"""Download and subset all observational data used in the study.

Outputs (data/processed/):
  chirps_uganda_daily.nc     CHIRPS v2.0 daily rainfall, 0.25 deg, Uganda box, 1981-01-01 to latest
                             (final product, then CHIRPS preliminary for the most recent weeks)
  chirps_africa_monthly.nc   CHIRPS v2.0 monthly totals, 0.25 deg, Africa (land, 50S-50N)
  cpc_uganda_daily.nc        CPC global daily Tmax/Tmin, 0.5 deg, Uganda box, 1981 to latest
  ghcncams_monthly_1deg.nc   GHCN-CAMS monthly 2 m land air temperature, 1 deg, global, 1981 to latest
  gpcp_monthly.nc            GPCP v2.3 monthly precipitation, 2.5 deg, global, 1979 to latest
  ersst_monthly.nc           ERSST v5 monthly SST, 2 deg, global, 1950 to latest
  uganda_adm2.geojson        geoBoundaries Uganda ADM2
Raw yearly CHIRPS files are deleted after subsetting.
"""
import gzip
import io
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

UG = dict(lat=slice(-1.75, 4.5), lon=slice(29.25, 35.25))  # Uganda box with a small margin
AF = dict(lat=slice(-36.0, 38.0), lon=slice(-18.5, 52.0))
Y0, Y1 = 1981, 2026
CHC = "https://data.chc.ucsb.edu/products/CHIRPS-2.0"
PSL = "https://psl.noaa.gov/thredds/dodsC/Datasets"


def get(url, dest):
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)


def chirps_year(y):
    ug_f, af_f = RAW / f"chirps_ug_{y}.nc", RAW / f"chirps_af_{y}.nc"
    if ug_f.exists() and af_f.exists():
        return y
    tmp = RAW / f"chirps-v2.0.{y}.days_p25.nc"
    get(f"{CHC}/global_daily/netcdf/p25/{tmp.name}", tmp)
    with xr.open_dataset(tmp) as ds:
        pr = ds["precip"].rename(latitude="lat", longitude="lon") if "latitude" in ds.dims else ds["precip"]
        pr = pr.sortby("lat")
        pr.sel(**UG).astype("float32").load().to_netcdf(ug_f)
        pr.sel(**AF).resample(time="MS").sum(min_count=1).astype("float32").load().to_netcdf(af_f)
    tmp.unlink()
    print("chirps", y, flush=True)
    return y


def chirps_prelim(last_final):
    """Daily CHIRPS preliminary (0.05 deg GeoTIFF) after the final record, averaged to the 0.25 deg grid."""
    import rasterio
    days = pd.date_range(last_final + pd.Timedelta(days=1), pd.Timestamp.today().normalize(), freq="D")
    ref = xr.open_dataset(RAW / f"chirps_ug_{Y1}.nc")["precip"]
    out = []
    for d in days:
        url = f"{CHC}/prelim/global_daily/tifs/p05/{d.year}/chirps-v2.0.{d:%Y.%m.%d}.tif.gz"
        r = requests.get(url, timeout=300)
        if r.status_code == 404:
            continue
        r.raise_for_status()
        with rasterio.MemoryFile(gzip.decompress(r.content)) as mf, mf.open() as src:
            a = src.read(1).astype("float32")
            a[a < 0] = np.nan
            t = src.transform
            lon = t.c + t.a * (np.arange(src.width) + 0.5)
            lat = t.f + t.e * (np.arange(src.height) + 0.5)
        da = xr.DataArray(a, dims=("lat", "lon"), coords={"lat": lat, "lon": lon}).sortby("lat")
        da = da.sel(lat=slice(ref.lat.min() - 0.125, ref.lat.max() + 0.125),
                    lon=slice(ref.lon.min() - 0.125, ref.lon.max() + 0.125))
        da = da.coarsen(lat=5, lon=5, boundary="trim").mean()
        da = da.interp(lat=ref.lat, lon=ref.lon, method="nearest").expand_dims(time=[d])
        out.append(da)
        print("prelim", d.date(), flush=True)
    return xr.concat(out, "time").rename("precip") if out else None


def chirps():
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(chirps_year, range(Y0, Y1 + 1)))
    ug = xr.concat([xr.open_dataset(f)["precip"].load() for f in sorted(RAW.glob("chirps_ug_*.nc"))], "time")
    ug = ug.dropna("time", how="all")
    last = pd.Timestamp(ug.time.values[-1])
    pre = chirps_prelim(last)
    src = xr.full_like(ug.time, 0, dtype="int8")
    if pre is not None:
        ug = xr.concat([ug, pre], "time")
        src = xr.concat([src, xr.full_like(pre.time, 1, dtype="int8")], "time")
    ds = xr.Dataset({"precip": ug.astype("float32"), "is_prelim": src})
    ds.attrs.update(source="CHIRPS v2.0 daily p25 (final) + CHIRPS v2.0 prelim p05 averaged to 0.25 deg",
                    last_final=str(last.date()))
    ds.to_netcdf(OUT / "chirps_uganda_daily.nc")
    af = xr.concat([xr.open_dataset(f)["precip"].load() for f in sorted(RAW.glob("chirps_af_*.nc"))], "time")
    af.to_dataset().to_netcdf(OUT / "chirps_africa_monthly.nc")
    print("CHIRPS Uganda", ug.shape, "final to", last.date(), "prelim days", 0 if pre is None else pre.sizes["time"])


def cpc_temp():
    f = OUT / "cpc_uganda_daily.nc"
    if f.exists():
        return
    parts = []
    for y in range(Y0, Y1 + 1):
        v = {}
        for var in ("tmax", "tmin"):
            ds = xr.open_dataset(f"{PSL}/cpc_global_temp/{var}.{y}.nc")
            da = ds[var].sortby("lat")
            v[var] = da.sel(lat=UG["lat"], lon=UG["lon"]).load()
        parts.append(xr.Dataset(v))
        print("cpc", y, flush=True)
    xr.concat(parts, "time").astype("float32").to_netcdf(f)


PSLF = "https://psl.noaa.gov/thredds/fileServer/Datasets"


def psl_file(path):
    """Whole-file HTTP download (large OPeNDAP requests from PSL silently returned zeros)."""
    import subprocess
    dest = RAW / path.split("/")[-1]
    part = dest.with_suffix(".part")
    if not dest.exists():
        for _ in range(20):  # PSL drops long transfers; resume until complete
            if subprocess.run(["curl", "-sSf", "-C", "-", "--retry", "5", "-o", str(part), f"{PSLF}/{path}"]).returncode == 0:
                break
        part.rename(dest)
    return dest


def check(da, name):
    v = da.values
    assert np.isfinite(v).any() and np.nanstd(v) > 0, f"{name}: empty or constant data"


def ghcncams():
    f = OUT / "ghcncams_monthly_1deg.nc"
    if f.exists():
        return
    with xr.open_dataset(psl_file("ghcncams/air.mon.mean.nc")) as ds:
        da = ds["air"].sel(time=slice(f"{Y0}-01-01", None)).load()
    out = da.coarsen(lat=2, lon=2).mean().sortby("lat")
    out = out.assign_coords(lon=((out.lon + 180) % 360) - 180).sortby("lon")
    out = (out - 273.15 if float(out.mean()) > 100 else out).rename("tas").astype("float32")
    check(out, "ghcncams")
    out.to_netcdf(f)


def gpcp():
    f = OUT / "gpcp_monthly.nc"
    if f.exists():
        return
    with xr.open_dataset(psl_file("gpcp/precip.mon.mean.nc"), drop_variables=["time_bnds", "lat_bnds", "lon_bnds"]) as ds:
        da = ds["precip"].load().sortby("lat")
    da = da.assign_coords(lon=((da.lon + 180) % 360) - 180).sortby("lon")
    check(da, "gpcp")
    da.astype("float32").to_netcdf(f)  # mm/day


def ersst():
    f = OUT / "ersst_monthly.nc"
    if f.exists():
        return
    with xr.open_dataset(psl_file("noaa.ersst.v5/sst.mnmean.nc")) as ds:
        da = ds["sst"].sel(time=slice("1950-01-01", None)).load().sortby("lat")
    check(da, "ersst")
    da.astype("float32").to_netcdf(f)


def boundaries():
    f = OUT / "uganda_adm2.geojson"
    if f.exists():
        return
    meta = requests.get("https://www.geoboundaries.org/api/current/gbOpen/UGA/ADM2/", timeout=60).json()
    get(meta["gjDownloadURL"], f)


if __name__ == "__main__":
    steps = sys.argv[1:] or ["boundaries", "ersst", "gpcp", "ghcncams", "cpc_temp", "chirps"]
    for s in steps:
        globals()[s]()
