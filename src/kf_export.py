"""Kampala Flood Replay, step 2: the event model and the data package for the browser.

The model replays the 10-11 October 2026 storm hour by hour on the Kampala drainage screening model (kd_hydraulics,
kd_roads.stage_states), with the same equations the browser runs, so settings can be changed and rerun in the page:
  rain       PERSIANN-CCS hourly (kf_rain.py), mean of the 3 x 3 cells (about 12 km) around each channel stretch
  intensity  over the stretch's time of concentration tc: for tc <= 60 min the hour's rain is spread within the hour like
             Kampala's 2-year design storm, i(tc) = R x i2(tc) / i2(60) (gauge-corrected IDF, as in kd_hydraulics); for
             longer tc, the mean over the last ceil(tc/60) hours
  flow       Q = 0.278 x C x i x A x ARF  (C: 2020 or 1990 paving; ARF = 1 - 0.04 A^0.5, floor 0.7)
  capacity   clean channel, or silted: cap = cap_clean x (cap_silted / cap_clean)^(silt / 0.3)  (cap_silted = 30% silt)
  stage      overbank level from each stretch's HAND rating curve: cap + floodplain flow(h) = Q
  depth      stage of the nearest stretch minus the cell's HAND (30 m cells within 200 m of a stretch)
Settings in the page: rain multiplier, silt in the channels, paving (2020 or 1990).

Outputs in tool_replay/data/ (public): seg.bin, rating.bin, rain_seg.bin (16-bit), cells.png, buildings.pmtiles, floodable.bin, roads.pmtiles, roads.bin,
meta.json, rain_grid.json, places.json. Validation: results/kf_validation.csv (reported places, default settings).
"""
import json
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
import xarray as xr
from PIL import Image

from common import PROC, RES, ROOT

KD = ROOT / "data" / "kd"
OUT = ROOT / "tool_replay" / "data"
BOX = (32.45, 0.20, 32.72, 0.42)
VIEW = (32.38, 0.12, 32.80, 0.50)                    # buildings shown on the map
HG = np.round(np.arange(0.1, 5.01, 0.1), 2)          # rating-curve levels (m)
DEFAULTS = dict(mult=1.5, silt=0.3, paving="2020")  # x1.5: see the page's "How good is it" tab


def segments():
    sys.path.insert(0, str(ROOT / "src"))
    s = gpd.read_file(KD / "segments.gpkg")
    h = pd.read_parquet(KD / "hydraulics.parquet")
    s = s[s.seg_id.isin(h.seg_id)].set_index("seg_id").loc[h.seg_id].reset_index()
    return s, h


def rating(s, h):
    """Floodplain flow (m3/s) at each level in HG, per stretch: as in kd_roads.stage_states."""
    su = s.to_crs(32636)
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand, trh = r.read(2), r.transform
    rows, cols = np.nonzero((hand < 6) & np.isfinite(hand))
    lon, lat = trh.c + trh.a * (cols + 0.5), trh.f + trh.e * (rows + 0.5)
    keep = (lon > BOX[0]) & (lon < BOX[2]) & (lat > BOX[1]) & (lat < BOX[3])
    pts = gpd.GeoSeries(gpd.points_from_xy(lon[keep], lat[keep]), crs=4326).to_crs(32636).values
    hv = hand[rows[keep], cols[keep]]
    pi, si = shapely.STRtree(su.geometry.values).query(pts, predicate="dwithin", distance=200)
    cell = pd.DataFrame({"p": pi, "s": si, "d": shapely.distance(pts[pi], su.geometry.values[si])}).sort_values("d") \
        .drop_duplicates("p")
    cell["h"] = hv[cell.p.values]
    groups = {k: g.h.values for k, g in cell.groupby("s")}
    L = su.length.values
    fine = np.arange(0.05, 5.01, 0.05)
    FP = np.zeros((len(s), len(HG)), "float32")
    for k in range(len(s)):
        hk = groups.get(k, np.array([]))
        wfp = np.maximum(np.array([(hk < x).sum() * 900.0 / max(L[k], 30) for x in fine]), h.W_design.values[k])
        area = np.cumsum(wfp * 0.05)
        fp = area * (area / wfp) ** (2 / 3) * np.sqrt(h.S.values[k]) / 0.06
        FP[k] = np.interp(HG, fine, fp)
    return FP


def seg_rain(s, h):
    """Hourly intensity over each stretch's tc (mm/h) for the event, before the rain multiplier."""
    from kd_hydraulics import idf_intensity
    r = xr.open_dataset(PROC / "kf_rain_persiann.nc").rain.fillna(0)
    c = s.to_crs(32636).geometry.centroid.to_crs(4326)
    R = np.zeros((len(s), r.sizes["time"]), "float32")
    la, lo = r.lat.values, r.lon.values
    for k, (x, y) in enumerate(zip(c.x.values, c.y.values)):
        i, j = np.abs(la - y).argmin(), np.abs(lo - x).argmin()
        R[k] = r.values[:, max(i - 1, 0):i + 2, max(j - 1, 0):j + 2].mean((1, 2))
    fi = idf_intensity()
    tc = h.tc_min.values
    peak = fi(2, np.minimum(tc, 60)) / fi(2, np.full(len(tc), 60.0))
    I = np.zeros_like(R)
    for k in range(len(s)):
        if tc[k] <= 60:
            I[k] = R[k] * peak[k]
        else:
            n = int(np.ceil(tc[k] / 60))
            I[k] = np.convolve(R[k], np.ones(n) / n)[:R.shape[1]]
    return I, [pd.Timestamp(t) for t in r.time.values]


def run(h, FP, I, mult=1.0, silt=0.3, paving="2020", C1990=None):
    """Stage (m above the channel's overbank level) per stretch and hour: the browser's model, in numpy."""
    A = h.A_km2.values
    ARF = np.clip(1 - 0.04 * np.sqrt(A), 0.7, 1)
    C = h.C.values if paving == "2020" else C1990
    cap = h.Qcap_clean.values * (h.Qcap_silted.values / h.Qcap_clean.values) ** (silt / 0.3)
    Q = 0.278 * (C * A * ARF)[:, None] * I * mult
    H = np.zeros_like(Q)
    for k in range(len(h)):
        over = Q[k] - cap[k]
        idx = np.searchsorted(FP[k], over)
        H[k] = np.where(over > 0, HG[np.minimum(idx, len(HG) - 1)], 0)
    return H


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s, h = segments()
    C1990 = 0.25 + 0.65 * np.clip(2.27 * s.up_built_1990.values, 0, 0.95)
    FP = rating(s, h)
    I, times = seg_rain(s, h)
    n, T = len(s), len(times)
    print("stretches", n, "hours", T, flush=True)

    # stretch table: A, ARF folded in, C 2020, C 1990, cap clean, cap silted (float32 x 6)
    A = h.A_km2.values
    ARF = np.clip(1 - 0.04 * np.sqrt(A), 0.7, 1)
    np.stack([0.278 * A * ARF, h.C.values, C1990, h.Qcap_clean.values, h.Qcap_silted.values], 1).astype("<f4") \
        .tofile(OUT / "seg.bin")
    # 16-bit encodings keep the download small: rating = log1p(Q) x 5000, rain = mm/h x 1000
    np.round(np.log1p(FP) * 5000).astype("<u2").tofile(OUT / "rating.bin")
    np.round(I * 1000).astype("<u2").tofile(OUT / "rain_seg.bin")

    # cells: R,G = stretch index (65535: none), B = HAND x 20 (0.05 m steps)
    cl = np.load(KD / "depth_cells.npz")
    a, _, c0, _, e, f0 = cl["transform"]
    c_lo, c_hi = int((BOX[0] - c0) / a), int(np.ceil((BOX[2] - c0) / a))
    r_lo, r_hi = int((BOX[3] - f0) / e), int(np.ceil((BOX[1] - f0) / e))
    W, Hh = c_hi - c_lo, r_hi - r_lo
    img = np.zeros((Hh, W, 4), "uint8"); img[..., 3] = 255
    img[..., 0] = img[..., 1] = 255
    rr, cc = cl["rows"] - r_lo, cl["cols"] - c_lo
    ok = (rr >= 0) & (rr < Hh) & (cc >= 0) & (cc < W) & (cl["hand"] < 12.7)
    sg = cl["seg"][ok].astype("uint16")
    img[rr[ok], cc[ok], 0], img[rr[ok], cc[ok], 1] = sg >> 8, sg & 255
    img[rr[ok], cc[ok], 2] = np.round(cl["hand"][ok] * 20).astype("uint8")
    Image.fromarray(img, "RGBA").save(OUT / "cells.png", optimize=True)
    bounds = [c0 + a * c_lo, f0 + e * r_hi, c0 + a * c_hi, f0 + e * r_lo]  # W, S, E, N
    print("cells", int(ok.sum()), "grid", W, "x", Hh, flush=True)

    def lookup(lon, lat):
        col = ((lon - bounds[0]) / a).astype(int); row = ((bounds[3] - lat) / -e).astype(int)
        inside = (col >= 0) & (col < W) & (row >= 0) & (row < Hh)
        sgv = np.full(len(lon), 65535); hv = np.full(len(lon), np.nan)
        px = img[row[inside], col[inside]]
        sgv[inside] = px[:, 0].astype(int) * 256 + px[:, 1]
        hv[inside] = px[:, 2] / 20
        return sgv, hv

    # all buildings as vector tiles (grey, 3D, with height), and the ones that can flood as a compact list:
    # floodable.bin = int32 building id, then uint16 stretch index, uint16 HAND (cm), per building that can flood
    b = gpd.read_parquet(KD / "ms_buildings.parquet").cx[VIEW[0]:VIEW[2], VIEW[1]:VIEW[3]].reset_index(drop=True)
    b["gid"] = np.arange(len(b), dtype="int32")
    b["ht"] = b.meanHeight.fillna(4).clip(3, 40).round(1)
    cen = b.geometry.centroid
    sgv, hv = lookup(cen.x.values, cen.y.values)
    m = (sgv != 65535) & (hv <= 5)
    np.concatenate([b.gid.values[m].astype("<i4").view("<u2").reshape(-1, 2),
                    np.stack([sgv[m], np.round(hv[m] * 100)], 1).astype("<u2")], 1).tofile(OUT / "floodable.bin")
    f = OUT / "buildings.pmtiles"
    f.unlink(missing_ok=True)
    import pyogrio
    pyogrio.write_dataframe(b[["gid", "ht", "geometry"]], f, driver="PMTiles", layer="b",
                            dataset_options=dict(MINZOOM=13, MAXZOOM=15, NAME="Kampala buildings"))
    print("buildings", len(b), "can flood", int(m.sum()), "pmtiles MB", round(f.stat().st_size / 1e6, 1), flush=True)

    # roads that can flood: pieces near a stretch, with the stretch index and lowest HAND
    p = gpd.read_parquet(KD / "road_pieces.parquet")
    p = gpd.GeoDataFrame(p, geometry="geometry", crs=4326) if not isinstance(p, gpd.GeoDataFrame) else p
    idx = pd.Series(np.arange(n), index=h.seg_id.values)
    p = p[p.seg_id.isin(idx.index) & (p.hand_min <= 5)].copy()
    p["s"] = idx.loc[p.seg_id].values
    p["h"] = np.round(p.hand_min * 100).astype(int)
    p["n"] = p["name"].fillna("")
    p = p.to_crs(4326) if p.crs and p.crs.to_epsg() != 4326 else p
    # roads that can flood: vector tiles for the map (rid), and roads.bin for the counters: uint16 stretch, uint16 HAND (cm),
    # float32 length (m), per road piece in rid order
    p = p.reset_index(drop=True)
    p["rid"] = np.arange(len(p), dtype="int32")
    np.concatenate([np.stack([p.s.values, p.h.values], 1).astype("<u2"),
                    p.len_m.values.astype("<f4").view("<u2").reshape(-1, 2)], 1).tofile(OUT / "roads.bin")
    f = OUT / "roads.pmtiles"
    f.unlink(missing_ok=True)
    import pyogrio
    pyogrio.write_dataframe(p[["rid", "geometry"]], f, driver="PMTiles", layer="r",
                            dataset_options=dict(MINZOOM=10, MAXZOOM=15, NAME="Kampala roads that can flood"))
    print("road pieces", len(p), flush=True)
    import gzip
    for f in ("seg.bin", "rating.bin", "rain_seg.bin", "floodable.bin", "roads.bin"):  # Pages does not compress binary
        (OUT / (f + ".gz")).write_bytes(gzip.compress((OUT / f).read_bytes(), 9, mtime=0))

    # stretch names, rain grid, places
    nm = s["name"].fillna("").values
    meta = dict(n_seg=n, hours=[t.strftime("%Y-%m-%dT%H:%M") for t in times], hg=HG.tolist(), cells_bounds=bounds,
                cells_size=[W, Hh], seg_name=[x for x in nm], systems=sorted(s["system"].fillna("").unique().tolist()),
                defaults=DEFAULTS)
    meta["seg_system"] = [meta["systems"].index(x) for x in s["system"].fillna("")]
    (OUT / "meta.json").write_text(json.dumps(meta, separators=(",", ":")))
    r = xr.open_dataset(PROC / "kf_rain_persiann.nc").rain
    (OUT / "rain_grid.json").write_text(json.dumps(dict(
        lat=[round(float(x), 3) for x in r.lat.values], lon=[round(float(x), 3) for x in r.lon.values],
        rain=np.round(np.nan_to_num(r.values), 1).tolist()), separators=(",", ":")))
    pl = pd.read_csv(RES / "kampala_flood_catalogue_places.csv")
    ev = pl[pl.event_id == "KLA-20261010"].drop_duplicates(["lat", "lon"])
    hs = pd.read_csv(KD / "hotspots_geocoded.csv")
    places = dict(event=[dict(name=r_.place, lat=r_.lat, lon=r_.lon) for r_ in ev.itertuples()],
                  hotspots=[dict(name=str(r_[1]), lat=float(r_.lat), lon=float(r_.lon)) for r_ in hs.itertuples()
                            if np.isfinite(r_.lat) and np.isfinite(r_.lon)])
    (OUT / "places.json").write_text(json.dumps(places, separators=(",", ":")))

    # validation at the places reported flooded in this storm, default settings and doubled rain
    rows = []
    for mult in (1.0, 1.5, 2.0):
        H = run(h, FP, I, mult=mult, C1990=C1990)
        for r_ in ev.itertuples():
            d = np.hypot((cl["cols"] * a + c0 - r_.lon) * 111320, (f0 + e * cl["rows"] - r_.lat) * 110570)
            near = d <= 500
            depth = (H[cl["seg"][near]] - (np.round(cl["hand"][near] * 20) / 20)[:, None])  # HAND in 5 cm steps, as in the page
            pk = depth.max(1)
            rows.append(dict(mult=mult, place=r_.place, cells_500m=int(near.sum()),
                             flooded_cells=int((pk >= 0.0999).sum()), max_depth_m=round(float(pk.max()), 2) if near.any() else None,
                             peak_hour=times[int(np.unravel_index(depth.argmax(), depth.shape)[1])].strftime("%d %b %H:%M")
                             if near.any() else None))
        tot = (H[cl["seg"]] - (np.round(cl["hand"] * 20) / 20)[:, None] >= 0.0999).sum(0)
        print(f"mult {mult}: peak flooded area {tot.max() * 900 / 1e6:.1f} km2 at {times[int(tot.argmax())]:%d %b %H:%M}",
              flush=True)
    v = pd.DataFrame(rows)
    v.to_csv(RES / "kf_validation.csv", index=False)
    print(v.to_string(), flush=True)


if __name__ == "__main__":
    main()
