"""Data for the Kampala flooding and food-security papers.

Outputs (data/processed/):
  kampala_ghsl_built.nc   GHSL GHS-BUILT-S R2023A built-up surface (m2 per ~90 m cell), epochs 1975-2030
                          (2025 and 2030 are GHSL projections), Greater Kampala box
  kampala_worldcover.tif  ESA WorldCover 2021 v200 (10 m), same box
  kampala_dem.tif         Copernicus GLO-30 DEM (30 m), same box
  arc2_uganda_daily.nc    NOAA CPC ARC2 daily rainfall (0.1 deg), Uganda box, 1983-2025 (IRI Data Library)
"""
import io
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio
import xarray as xr
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw" / "kampala", ROOT / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
BOX = (32.30, 0.00, 32.95, 0.60)  # lon0, lat0, lon1, lat1 - Greater Kampala
EPOCHS = list(range(1975, 2031, 5))
GHSL = ("https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A/"
        "GHS_BUILT_S_E{y}_GLOBE_R2023A_4326_3ss/V1-0/tiles/GHS_BUILT_S_E{y}_GLOBE_R2023A_4326_3ss_V1_0_R9_C22.zip")


def curl(url, dest):
    for _ in range(10):
        if subprocess.run(["curl", "-sSfL", "-C", "-", "--retry", "5", "-o", str(dest), url]).returncode == 0:
            return dest
    raise RuntimeError(url)


def crop(src_path, dst_path=None):
    with rasterio.open(src_path) as r:
        w = from_bounds(*BOX, r.transform)
        a = r.read(1, window=w)
        t = r.window_transform(w)
        prof = r.profile | dict(height=a.shape[0], width=a.shape[1], transform=t, compress="deflate")
    if dst_path:
        prof.pop("blockxsize", None), prof.pop("blockysize", None), prof.pop("tiled", None)
        with rasterio.open(dst_path, "w", **prof) as d:
            d.write(a, 1)
    return a, t


def ghsl():
    f = OUT / "kampala_ghsl_built.nc"
    if f.exists():
        return
    layers = []
    for y in EPOCHS:
        z = RAW / f"ghsl_{y}.zip"
        if not z.exists():
            curl(GHSL.format(y=y), z)
        with zipfile.ZipFile(z) as zz:
            name = [n for n in zz.namelist() if n.endswith(".tif")][0]
            tif = RAW / name
            if not tif.exists():
                zz.extract(name, RAW)
        a, t = crop(tif)
        tif.unlink()
        lon = t.c + t.a * (np.arange(a.shape[1]) + 0.5)
        lat = t.f + t.e * (np.arange(a.shape[0]) + 0.5)
        layers.append(xr.DataArray(a.astype("float32"), dims=("lat", "lon"), coords={"lat": lat, "lon": lon}))
        print("ghsl", y, float(a.sum()) / 1e6, "km2 built", flush=True)
    da = xr.concat(layers, xr.DataArray(EPOCHS, dims="epoch", name="epoch")).rename("built_m2")
    da.sortby("lat").to_netcdf(f)


def worldcover():
    f = OUT / "kampala_worldcover.tif"
    if not f.exists():
        src = curl("https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N00E030_Map.tif",
                   RAW / "worldcover_N00E030.tif")
        crop(src, f)


def dem():
    f = OUT / "kampala_dem.tif"
    if not f.exists():
        src = curl("https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N00_00_E032_00_DEM/"
                   "Copernicus_DSM_COG_10_N00_00_E032_00_DEM.tif", RAW / "cop30_N00E032.tif")
        crop(src, f)


def arc2():
    f = OUT / "arc2_uganda_daily.nc"
    if f.exists():
        return
    parts = []
    for y in range(1983, 2026):
        p = RAW / f"arc2_{y}.nc"
        url = ("http://iridl.ldeo.columbia.edu/SOURCES/.NOAA/.NCEP/.CPC/.FEWS/.Africa/.DAILY/.ARC2/.daily/.est_prcp/"
               f"X/29.25/35.25/RANGEEDGES/Y/-1.75/4.5/RANGEEDGES/T/(1%20Jan%20{y})/(31%20Dec%20{y})/RANGEEDGES/data.nc")
        if not p.exists():
            curl(url, p)
        ds = xr.open_dataset(p, decode_times=False)
        v = ds["est_prcp"]
        t0 = np.datetime64(f"{y}-01-01")
        v = v.assign_coords(T=t0 + np.arange(v.sizes["T"]).astype("timedelta64[D]"))
        parts.append(v.rename(T="time", X="lon", Y="lat").load())
        print("arc2", y, flush=True)
    da = xr.concat(parts, "time").sortby("lat").rename("precip")
    da = da.where(da >= 0)
    da.astype("float32").to_netcdf(f)


if __name__ == "__main__":
    for s in sys.argv[1:] or ["dem", "worldcover", "ghsl", "arc2"]:
        globals()[s]()


GHSPOP = ("https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/"
          "GHS_POP_E{y}_GLOBE_R2023A_4326_3ss/V1-0/tiles/GHS_POP_E{y}_GLOBE_R2023A_4326_3ss_V1_0_R9_C22.zip")


POP_EPOCHS = [1975, 1980, 1985, 1990, 2000, 2010, 2020, 2025, 2030]  # slow server: skip 1995/2005/2015


def ghs_pop():
    """GHS-POP R2023A residential population (people per ~100 m cell), 1975-2030 (2025/2030 projected)."""
    f = OUT / "kampala_ghs_pop.nc"
    if f.exists():
        return
    layers = []
    for y in POP_EPOCHS:
        z = RAW / f"ghspop_{y}.zip"
        if not z.exists():
            curl(GHSPOP.format(y=y), z)
        with zipfile.ZipFile(z) as zz:
            name = [n for n in zz.namelist() if n.endswith(".tif")][0]
            tif = RAW / name
            if not tif.exists():
                zz.extract(name, RAW)
        a, t = crop(tif)
        tif.unlink()
        a = np.where(a < 0, 0, a)
        lon = t.c + t.a * (np.arange(a.shape[1]) + 0.5)
        lat = t.f + t.e * (np.arange(a.shape[0]) + 0.5)
        layers.append(xr.DataArray(a.astype("float32"), dims=("lat", "lon"), coords={"lat": lat, "lon": lon}))
        print("ghs-pop", y, round(float(a.sum()) / 1e6, 2), "million people in box", flush=True)
    da = xr.concat(layers, xr.DataArray(POP_EPOCHS, dims="epoch", name="epoch")).rename("pop")
    step = abs(float(np.diff(da.lat.values).mean()))
    if step < 0.0005:  # crop window was oversampled (~1 arcsec): back to the native 3 arcsec grid, preserving sums
        k = int(round(0.000833 / step))
        da = da.fillna(0).coarsen(lat=k, lon=k, boundary="trim").sum().rename("pop")
    da.sortby("lat").to_netcdf(f)
