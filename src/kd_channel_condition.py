"""Observed channel condition for Paper R: how green (vegetated, choked) is each channel bed today?

composites  Sentinel-2 L2A dry-season median NDVI, 10 m, Greater Kampala core: Jun-Aug 2024, Dec 2024-Feb 2025,
            Jun-Aug 2025, Dec 2025-Feb 2026, Jun-Aug 2026 (cloud < 30%, SCL clear classes only)
condition   for every stretch draining >= 3 km2 (primary channels, ~5-20 m wide): median NDVI on the centreline
            (points every 10 m, all seasons) and of the land 30-60 m either side (surroundings)
            score c = clip((NDVI_bed - 0.20) / (0.55 - 0.20), 0, 1): 0 = clear bed (concrete, water, bare silt
            surface), 1 = fully vegetated bed
            silted state from c: depth lost = 0.10 + 0.40 c; Manning n = 0.030 + 0.015 c
            smaller drains (< 3 km2, too narrow for 10 m imagery): median c of their system's primary channels
Outputs: data/kd/s2_ndvi_<season>.nc, results/kd_channel_condition.csv
"""
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr

from common import RES, ROOT

KD = ROOT / "data" / "kd"
BBOX = [32.45, 0.20, 32.72, 0.42]
SEASONS = {"2024_JJA": ("2024-06-01", "2024-08-31"), "2025_DJF": ("2024-12-01", "2025-02-28"),
           "2025_JJA": ("2025-06-01", "2025-08-31"), "2026_DJF": ("2025-12-01", "2026-02-28"),
           "2026_JJA": ("2026-06-01", "2026-08-31")}
LO, HI = 0.20, 0.55


def composites():
    import planetary_computer as pc
    import pystac_client
    from odc.stac import load
    cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
    for tag, (a, b) in SEASONS.items():
        f = KD / f"s2_ndvi_{tag}.nc"
        if f.exists():
            continue
        items = list(cat.search(collections=["sentinel-2-l2a"], bbox=BBOX, datetime=f"{a}/{b}",
                                query={"eo:cloud_cover": {"lt": 30}}).items())
        print(tag, "scenes", len(items), flush=True)
        ds = load(items, bands=["B04", "B08", "SCL"], bbox=BBOX, crs="EPSG:32636", resolution=10,
                  groupby="solar_day", chunks={"x": 1024, "y": 1024, "time": 1})
        clear = ds.SCL.isin([4, 5, 6, 7])
        r, n = (ds.B04.astype("float32") - 1000) / 10000, (ds.B08.astype("float32") - 1000) / 10000
        ndvi = ((n - r) / (n + r)).where(clear & (n + r > 0)).median("time").astype("float32").compute()
        ndvi.rename("ndvi").to_netcdf(f)
        print(tag, "done", flush=True)


def condition():
    seg = gpd.read_file(KD / "segments.gpkg").to_crs(32636)
    rasters = [xr.open_dataarray(KD / f"s2_ndvi_{t}.nc") for t in SEASONS if (KD / f"s2_ndvi_{t}.nc").exists()]
    print("seasons", len(rasters), flush=True)
    big = seg[seg.up_km2 >= 3]
    rows = []
    for r in big.itertuples():
        g = r.geometry
        d = np.arange(0, g.length, 10.0)
        pts = [g.interpolate(x) for x in d]
        X = xr.DataArray([p.x for p in pts], dims="p")
        Y = xr.DataArray([p.y for p in pts], dims="p")
        ring = g.buffer(60).difference(g.buffer(30))
        rp = ring.representative_point()
        bx, by = ring.bounds[0::2], ring.bounds[1::2]
        sx = np.linspace(ring.bounds[0], ring.bounds[2], 12)
        sy = np.linspace(ring.bounds[1], ring.bounds[3], 12)
        SX, SY = np.meshgrid(sx, sy)
        import shapely
        inside = shapely.contains_xy(ring, SX.ravel(), SY.ravel())
        RX = xr.DataArray(SX.ravel()[inside], dims="q")
        RY = xr.DataArray(SY.ravel()[inside], dims="q")
        bed = np.concatenate([ra.sel(x=X, y=Y, method="nearest").values for ra in rasters])
        sur = np.concatenate([ra.sel(x=RX, y=RY, method="nearest").values for ra in rasters]) if inside.any() else np.array([np.nan])
        rows.append(dict(seg_id=r.seg_id, system=r.system, up_km2=r.up_km2, ndvi_bed=np.nanmedian(bed),
                         ndvi_surround=np.nanmedian(sur), n_obs=int(np.isfinite(bed).sum())))
    c = pd.DataFrame(rows)
    c["score"] = ((c.ndvi_bed - LO) / (HI - LO)).clip(0, 1)
    c["observed"] = True
    sysmed = c.groupby("system").score.median()
    small = seg[seg.up_km2 < 3][["seg_id", "system", "up_km2"]].copy()
    small["score"] = small.system.map(sysmed).fillna(c.score.median())
    small["observed"] = False
    out = pd.concat([c, small], ignore_index=True)
    out["silt_depth"] = 0.10 + 0.40 * out.score
    out["n_silt"] = 0.030 + 0.015 * out.score
    out.round(4).to_csv(RES / "kd_channel_condition.csv", index=False)
    print(c[["ndvi_bed", "ndvi_surround", "score"]].describe().round(3).to_string())
    print(c.groupby("system")[["ndvi_bed", "score"]].median().round(3).to_string())
    print("correlation bed vs surroundings:", round(c[["ndvi_bed", "ndvi_surround"]].corr().iloc[0, 1], 3))


if __name__ == "__main__":
    for f in sys.argv[1:] or ["composites", "condition"]:
        globals()[f]()
