"""Kampala drainage study, part 3: satellite layers (Microsoft Planetary Computer, no login).

landsat   dry-season median true-colour composites, 1995 (Landsat 5) and 2025 (Landsat 8/9), 30 m
s2        recent Sentinel-2 L2A median composite (2026 dry months), 10 m, for close-up maps
lulc      Impact Observatory annual 10 m land cover 2017-2023: built area and wetland ('flooded vegetation')
          inside the valley floor (HAND < 3 m) of each channel system
s1        Sentinel-1 RTC: VV backscatter on the latest pass vs the dry-season median -> newly wet/flooded areas
channels  Sentinel-2 monthly NDVI inside wide primary channels (2017-2026): vegetation choking the channel bed
Outputs in data/kd/sat_*.nc|tif and results/kd_lulc_*.csv, results/kd_channel_ndvi.csv
"""
import sys

import numpy as np
import pandas as pd
import planetary_computer as pc
import pystac_client
import xarray as xr
from odc.stac import load

from common import RES, ROOT

KD = ROOT / "data" / "kd"
BBOX = [32.45, 0.20, 32.72, 0.42]
CAT = None


def cat():
    global CAT
    if CAT is None:
        CAT = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
    return CAT


def landsat():
    for year, plats, months in ((1995, ["landsat-5"], "06-01/09-30"), (1986, ["landsat-5"], "06-01/09-30"),
                                (2025, ["landsat-8", "landsat-9"], "06-01/09-30")):
        f = KD / f"sat_landsat_{year}.nc"
        if f.exists():
            continue
        a, b = months.split("/")
        yrs = range(year - 1, year + 2)
        items = []
        for y in yrs:
            items += list(cat().search(collections=["landsat-c2-l2"], bbox=BBOX, datetime=f"{y}-{a}/{y}-{b}",
                                       query={"eo:cloud_cover": {"lt": 40}, "platform": {"in": plats}}).items())
        if not items:
            for y in yrs:  # widen to all months
                items += list(cat().search(collections=["landsat-c2-l2"], bbox=BBOX, datetime=f"{y}-01-01/{y}-12-31",
                                           query={"eo:cloud_cover": {"lt": 40}, "platform": {"in": plats}}).items())
        print(year, "landsat scenes", len(items), flush=True)
        ds = load(items, bands=["red", "green", "blue", "nir08", "swir16", "qa_pixel"], bbox=BBOX, crs="EPSG:32636",
                  resolution=30, groupby="solar_day", chunks={"x": 1024, "y": 1024})
        qa = ds.qa_pixel
        clear = ((qa & (1 << 3)) == 0) & ((qa & (1 << 4)) == 0) & ((qa & (1 << 1)) == 0) & (qa != 0)
        out = ds[["red", "green", "blue", "nir08", "swir16"]].where(clear).median("time")
        out = (out * 0.0000275 - 0.2).astype("float32").compute()
        out.attrs["n_scenes"] = len(items)
        out.to_netcdf(f)


def s2():
    f = KD / "sat_s2_2026.nc"
    if f.exists():
        return
    items = list(cat().search(collections=["sentinel-2-l2a"], bbox=BBOX, datetime="2025-12-01/2026-09-30",
                              query={"eo:cloud_cover": {"lt": 30}}).items())
    items = sorted(items, key=lambda i: i.properties["eo:cloud_cover"])[:24]
    print("s2 scenes", len(items), flush=True)
    ds = load(items, bands=["B02", "B03", "B04", "B08", "B11", "SCL"], bbox=BBOX, crs="EPSG:32636", resolution=10,
              groupby="solar_day", chunks={"x": 2048, "y": 2048})
    clear = ds.SCL.isin([4, 5, 6, 7])
    out = ds[["B02", "B03", "B04", "B08", "B11"]].where(clear).median("time")
    out = ((out - 1000) / 10000).astype("float32").compute()  # processing baseline >= 4.0 offset
    out.to_netcdf(f)


def lulc():
    f = KD / "sat_iolulc.nc"
    if not f.exists():
        items = list(cat().search(collections=["io-lulc-annual-v02"], bbox=BBOX).items())
        print("io-lulc items", len(items), flush=True)
        ds = load(items, bands=["data"], bbox=BBOX, crs="EPSG:32636", resolution=10, groupby="start_datetime",
                  chunks={"x": 2048, "y": 2048})
        ds["time"] = pd.to_datetime(ds.time.values).year
        ds.data.astype("uint8").compute().to_netcdf(f)
    lc = xr.open_dataarray(f)
    # classes: 1 water, 2 trees, 4 flooded vegetation, 5 crops, 7 built, 8 bare, 11 rangeland
    import rasterio
    from rasterio.warp import Resampling, reproject
    with rasterio.open(ROOT / "data" / "processed" / "kampala_catchments.tif") as r:
        cat_, hand = r.read(1), r.read(2)
        src_tr = r.transform
    dst = np.zeros(lc.shape[1:], np.float32)
    dst_tr = lc.odc.geobox.transform if hasattr(lc, "odc") else None
    hv = np.full(lc.shape[1:], np.nan, np.float32)
    cv = np.zeros(lc.shape[1:], np.float32)
    reproject(hand, hv, src_transform=src_tr, src_crs="EPSG:4326", dst_transform=dst_tr, dst_crs="EPSG:32636",
              resampling=Resampling.nearest)
    reproject(cat_.astype("float32"), cv, src_transform=src_tr, src_crs="EPSG:4326", dst_transform=dst_tr,
              dst_crs="EPSG:32636", resampling=Resampling.nearest)
    names = pd.read_csv(RES / "kampala_catchments.csv").set_index("id").name.dropna()
    valley = hv < 3
    rows = []
    for yr in lc.time.values:
        a = lc.sel(time=yr).values
        for cid, nm in list(names.items()) + [(None, "All Greater Kampala core")]:
            m = valley & ((cv == cid) if cid else np.isfinite(hv))
            n = m.sum()
            rows.append(dict(year=int(yr), system=nm, valley_km2=n * 1e-4,
                             built=(a[m] == 7).mean(), wetland=(a[m] == 4).mean(), trees=(a[m] == 2).mean(),
                             crops=(a[m] == 5).mean(), rangeland=(a[m] == 11).mean(), water=(a[m] == 1).mean()))
    df = pd.DataFrame(rows)
    df.round(4).to_csv(RES / "kd_lulc_valley.csv", index=False)
    print(df[df.year.isin([2017, 2023])].round(3).to_string())


def s1():
    f = KD / "sat_s1.nc"
    if f.exists():
        return
    recent = list(cat().search(collections=["sentinel-1-rtc"], bbox=BBOX, datetime="2026-10-01/2026-10-12").items())
    recent = sorted(recent, key=lambda i: i.datetime)
    print("recent s1", [(i.datetime.strftime("%Y-%m-%d %H:%M"), i.properties.get("sat:orbit_state"),
                         i.properties.get("sat:relative_orbit")) for i in recent], flush=True)
    last = recent[-1]
    orbit = last.properties.get("sat:relative_orbit")
    ref = [i for i in cat().search(collections=["sentinel-1-rtc"], bbox=BBOX, datetime="2026-06-15/2026-09-10").items()
           if i.properties.get("sat:relative_orbit") == orbit]
    print("reference passes, same orbit", len(ref), flush=True)
    kw = dict(bands=["vv", "vh"], bbox=BBOX, crs="EPSG:32636", resolution=10, chunks={"x": 2048, "y": 2048})
    now = load([i for i in recent if i.datetime.date() == last.datetime.date()], groupby="solar_day", **kw).isel(time=0)
    base = load(ref, groupby="solar_day", **kw).median("time")
    db = lambda v: 10 * np.log10(v.clip(min=1e-5))
    out = xr.Dataset({"vv_now": db(now.vv), "vv_ref": db(base.vv), "vh_now": db(now.vh), "vh_ref": db(base.vh)}).astype("float32").compute()
    out.attrs["date_now"] = str(last.datetime)
    out.attrs["n_ref"] = len(ref)
    out.to_netcdf(f)


def channels():
    """Monthly NDVI in the bed of wide primary channels (>= 8 m wide in OSM, or the named main channels)."""
    import geopandas as gpd
    f = RES / "kd_channel_ndvi.csv"
    if f.exists():
        return
    seg = gpd.read_file(KD / "segments.gpkg")
    w = pd.to_numeric(seg.width if "width" in seg else pd.Series(np.nan, index=seg.index), errors="coerce")
    named = seg.name.fillna("").str.contains("Nakivubo Channel|Lubigi Channel|Kinawataka|Nalukolongo|Kansanga|Kitante|Lubigi$", regex=True)
    main = seg[(named | (w >= 8)) & (seg.up_km2 >= 2)].to_crs(32636)
    print("channel segments monitored", len(main), flush=True)
    pts = []
    for _, r in main.iterrows():
        for d in np.arange(10, r.geometry.length, 20):
            p = r.geometry.interpolate(d)
            pts.append((r.seg_id, r["name"], r.system, p.x, p.y))
    pts = pd.DataFrame(pts, columns=["seg_id", "name", "system", "x", "y"])
    items = list(cat().search(collections=["sentinel-2-l2a"], bbox=BBOX, datetime="2017-01-01/2026-10-12",
                              query={"eo:cloud_cover": {"lt": 60}}).items())
    print("s2 scenes for channel monitoring", len(items), flush=True)
    x0, x1, y0, y1 = pts.x.min() - 50, pts.x.max() + 50, pts.y.min() - 50, pts.y.max() + 50
    import pyproj
    tf = pyproj.Transformer.from_crs(32636, 4326, always_xy=True)
    lo0, la0 = tf.transform(x0, y0)
    lo1, la1 = tf.transform(x1, y1)
    ds = load(items, bands=["B04", "B08", "SCL"], bbox=[lo0, la0, lo1, la1], crs="EPSG:32636", resolution=10,
              groupby="solar_day", chunks={"x": 1024, "y": 1024, "time": 8})
    X = xr.DataArray(pts.x.values, dims="p")
    Y = xr.DataArray(pts.y.values, dims="p")
    sub = ds.sel(x=X, y=Y, method="nearest")
    clear = sub.SCL.isin([4, 5, 6, 7])
    nd = ((sub.B08 - sub.B04) / (sub.B08 + sub.B04).where(lambda v: v > 0)).where(clear)
    nd = nd.compute()
    df = nd.to_pandas().T
    df.index = pts.index
    long = df.stack().rename("ndvi").reset_index()
    long.columns = ["p", "time", "ndvi"]
    long = long.join(pts[["seg_id", "name", "system"]], on="p")
    long["month"] = pd.to_datetime(long.time).dt.to_period("M").dt.to_timestamp()
    out = long.groupby(["seg_id", "name", "system", "month"]).ndvi.median().reset_index()
    out.round(4).to_csv(f, index=False)
    print(out.groupby("month").ndvi.median().tail(12))


if __name__ == "__main__":
    for s in sys.argv[1:] or ["landsat", "s2", "lulc", "s1", "channels"]:
        globals()[s]()
        print("done", s, flush=True)


def s1_pass(day="2026-10-12", out_name="sat_s1_20261012.nc"):
    """One Sentinel-1 pass vs the dry-season median on the same relative orbit."""
    f = KD / out_name
    if f.exists():
        return
    items = [i for i in cat().search(collections=["sentinel-1-rtc"], bbox=BBOX, datetime=f"{day}/{day}").items()]
    last = sorted(items, key=lambda i: i.datetime)[-1]
    orbit = last.properties.get("sat:relative_orbit")
    ref = [i for i in cat().search(collections=["sentinel-1-rtc"], bbox=BBOX, datetime="2026-06-15/2026-09-10").items()
           if i.properties.get("sat:relative_orbit") == orbit]
    print("pass", last.datetime, "orbit", orbit, "reference passes", len(ref), flush=True)
    kw = dict(bands=["vv", "vh"], bbox=BBOX, crs="EPSG:32636", resolution=10, chunks={"x": 2048, "y": 2048})
    now = load([last], **kw).isel(time=0)
    base = load(ref, groupby="solar_day", **kw)
    base = base.where(base > 0).median("time")
    db = lambda v: 10 * np.log10(v.where(v > 0).clip(min=1e-5))
    out = xr.Dataset({"vv_now": db(now.vv), "vv_ref": db(base.vv), "vh_now": db(now.vh), "vh_ref": db(base.vh)}).astype("float32").compute()
    out.attrs["date_now"] = str(last.datetime)
    out.attrs["n_ref"] = len(ref)
    out.to_netcdf(f)
