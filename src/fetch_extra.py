"""Additional climate parameters and future projections.

Outputs (data/processed/):
  power_monthly.nc        NASA POWER (MERRA-2 based) monthly grids over Uganda, 1981-2025: 2 m and 10 m wind
                          speed, 2 m relative humidity, all-sky surface solar radiation, 2 m dew point,
                          surface pressure, Tmax/Tmin  (~0.5 x 0.625 deg)
  cpcsoil_monthly.nc      CPC soil moisture (leaky-bucket model, mm in 1.6 m column), 0.5 deg, 1981 to latest
  cmip6_ea_monthly.nc     CMIP6 monthly pr (mm/day) and tas (deg C), r1i1p1f1, historical + SSP2-4.5 + SSP5-8.5,
                          regridded to a common 1 deg East Africa grid (12S-12N, 24E-44E), 1981-2100
"""
import io
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"
PSL = "https://psl.noaa.gov/thredds/dodsC/Datasets"

POWER_PARAMS = ["WS2M", "WS10M", "WS2M_MAX", "RH2M", "ALLSKY_SFC_SW_DWN", "T2MDEW", "PS", "T2M_MAX", "T2M_MIN"]
CMIP6_MODELS = ["ACCESS-CM2", "BCC-CSM2-MR", "CMCC-ESM2", "CanESM5", "EC-Earth3", "FGOALS-g3", "GFDL-ESM4",
                "INM-CM5-0", "IPSL-CM6A-LR", "KACE-1-0-G", "MIROC6", "MPI-ESM1-2-LR", "MRI-ESM2-0", "NESM3",
                "NorESM2-MM", "TaiESM1"]
EA = dict(lat=np.arange(-11.5, 12, 1.0), lon=np.arange(24.5, 44, 1.0))


def power():
    f = OUT / "power_monthly.nc"
    if f.exists():
        return
    parts = []
    for p in POWER_PARAMS:
        for y0, y1 in ((1981, 2002), (2003, 2025)):
            url = ("https://power.larc.nasa.gov/api/temporal/monthly/regional"
                   f"?parameters={p}&community=AG&latitude-min=-1.5&latitude-max=4.5&longitude-min=29.5"
                   f"&longitude-max=35.0&start={y0}&end={y1}&format=NETCDF")
            for attempt in range(4):
                r = requests.get(url, timeout=600)
                if r.ok:
                    break
                time.sleep(20)
            r.raise_for_status()
            ds = xr.open_dataset(io.BytesIO(r.content), engine="h5netcdf").load()
            parts.append(ds[[p]])
            print("power", p, y0, y1, flush=True)
    ds = xr.merge([xr.concat([a for a in parts if p in a], "time") for p in POWER_PARAMS])
    ds = ds.where(ds > -900)
    ds.to_netcdf(f)


POWER_DAILY = ["T2M_MAX", "T2M_MIN", "T2MDEW", "WS2M", "WS10M_MAX", "ALLSKY_SFC_SW_DWN", "PS", "RH2M"]


def power_daily():
    """NASA POWER daily grids (monthly POWER Tmax/Tmin are monthly extremes, not means of daily values)."""
    f = OUT / "power_daily.nc"
    if f.exists():
        return
    out = {}
    for p in POWER_DAILY:
        parts = []
        for y0 in range(1984 if p.startswith("ALLSKY") else 1981, 2026):  # no POWER radiation before 1984
            y1 = y0
            url = ("https://power.larc.nasa.gov/api/temporal/daily/regional"
                   f"?parameters={p}&community=AG&latitude-min=-1.5&latitude-max=4.5&longitude-min=29.5"
                   f"&longitude-max=35.0&start={y0}0101&end={y1}1231&format=NETCDF")
            cache = ROOT / "data" / "raw" / "power" / f"{p}_{y0}.nc"
            cache.parent.mkdir(parents=True, exist_ok=True)
            if not cache.exists():
                for attempt in range(6):
                    try:
                        r = requests.get(url, timeout=900)
                        if r.ok:
                            break
                        print("retry", p, y0, r.status_code, r.text[:200], flush=True)
                    except requests.RequestException as e:
                        print("retry", p, y0, e, flush=True)
                    time.sleep(30)
                r.raise_for_status()
                cache.write_bytes(r.content)
            parts.append(xr.open_dataset(cache, engine="h5netcdf")[p].load())
            print("power daily", p, y0, flush=True)
        da = xr.concat(parts, "time")
        out[p] = da.where(da > -900).astype("float32")
    xr.Dataset(out).to_netcdf(f)


def cpcsoil():
    f = OUT / "cpcsoil_monthly.nc"
    if f.exists():
        return
    ds = xr.open_dataset(f"{PSL}/cpcsoil/soilw.mon.mean.v2.nc")
    da = ds["soilw"].sortby("lat")
    lon = da.lon
    da = da.sel(lat=slice(-2, 5), lon=slice(29, 35.5) if float(lon.min()) < 0 else slice(29, 35.5))
    da.sel(time=slice("1981-01-01", None)).load().astype("float32").to_netcdf(f)


def cmip6_model(m):
    """Download one model (historical + SSP2-4.5 + SSP5-8.5, pr and tas) to data/raw/cmip6/<model>.nc."""
    import fsspec
    f = ROOT / "data" / "raw" / "cmip6" / f"{m}.nc"
    f.parent.mkdir(parents=True, exist_ok=True)
    if f.exists():
        return
    cat = pd.read_csv("https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv")
    cat = cat[(cat.table_id == "Amon") & (cat.member_id == "r1i1p1f1") & cat.variable_id.isin(["pr", "tas"])]
    runs = {}
    for var in ("pr", "tas"):
        for exp in ("historical", "ssp245", "ssp585"):
            row = cat[(cat.source_id == m) & (cat.variable_id == var) & (cat.experiment_id == exp)]
            ds = xr.open_zarr(fsspec.get_mapper(row.zstore.values[-1], token="anon"), consolidated=True)
            da = ds[var]
            da = da.assign_coords(lon=((da.lon + 180) % 360) - 180).sortby("lon").sortby("lat")
            da = da.sel(lat=slice(-14, 14), lon=slice(22, 46))
            da = da.sortby("time")  # some stores have unsorted / duplicated time steps
            da = da.isel(time=~da.indexes["time"].duplicated())
            da = da.sel(time=slice("1981", "2014") if exp == "historical" else slice("2015", "2100"))
            da = da.load().interp(lat=EA["lat"], lon=EA["lon"])
            t = pd.to_datetime([f"{d.year}-{d.month:02d}-01" for d in da.indexes["time"]])
            da = da.assign_coords(time=t)
            da = da * 86400 if var == "pr" else da - 273.15
            runs[(var, exp)] = da.drop_vars([c for c in da.coords if c not in ("time", "lat", "lon")])
    out = []
    for scen in ("ssp245", "ssp585"):
        ds = xr.Dataset({v: xr.concat([runs[(v, "historical")], runs[(v, scen)]], "time") for v in ("pr", "tas")})
        out.append(ds.expand_dims(model=[m], scenario=[scen]))
    xr.combine_by_coords(out).astype("float32").to_netcdf(f)
    print("cmip6", m, flush=True)


def cmip6():
    """Combine the per-model files (run cmip6_model for each model first, e.g. in parallel)."""
    files = sorted((ROOT / "data" / "raw" / "cmip6").glob("*.nc"))
    ds = xr.combine_by_coords([xr.open_dataset(f).load() for f in files])
    ds.to_netcdf(OUT / "cmip6_ea_monthly.nc")
    print("combined", ds.sizes["model"], "models")


def cmip6_tas_point(m, lat=-26.2, lon=28.05, tag="jhb"):
    """Annual-mean 2 m temperature at one point (bilinear), historical + SSP2-4.5 + SSP5-8.5, one model."""
    import fsspec
    f = ROOT / "data" / "raw" / f"cmip6_{tag}" / f"{m}.nc"
    f.parent.mkdir(parents=True, exist_ok=True)
    if f.exists():
        return
    cat = pd.read_csv("https://storage.googleapis.com/cmip6/cmip6-zarr-consolidated-stores.csv")
    cat = cat[(cat.table_id == "Amon") & (cat.member_id == "r1i1p1f1") & (cat.variable_id == "tas")]
    out = {}
    for exp in ("historical", "ssp245", "ssp585"):
        row = cat[(cat.source_id == m) & (cat.experiment_id == exp)]
        da = xr.open_zarr(fsspec.get_mapper(row.zstore.values[-1], token="anon"), consolidated=True)["tas"]
        da = da.assign_coords(lon=((da.lon + 180) % 360) - 180).sortby("lon").sortby("lat").sortby("time")
        da = da.isel(time=~da.indexes["time"].duplicated())
        da = da.sel(lat=slice(lat - 4, lat + 4), lon=slice(lon - 4, lon + 4))
        da = da.sel(time=slice("1981", "2014") if exp == "historical" else slice("2015", "2100")).load()
        da = da.interp(lat=lat, lon=lon) - 273.15
        yrs = np.array([d.year for d in da.indexes["time"]])
        out[exp] = pd.Series(da.values, index=yrs).groupby(level=0).mean()
    pd.DataFrame({"historical": out["historical"], "ssp245": out["ssp245"], "ssp585": out["ssp585"]}).to_xarray() \
        .rename(index="year").to_netcdf(f)
    print("cmip6 point", m, flush=True)


if __name__ == "__main__":
    if sys.argv[1:2] == ["cmip6_model"]:
        cmip6_model(sys.argv[2])
    elif sys.argv[1:2] == ["cmip6_tas_point"]:
        if len(sys.argv) > 3:  # model lat lon tag
            cmip6_tas_point(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5])
        else:
            cmip6_tas_point(sys.argv[2])
    else:
        for s in sys.argv[1:] or ["cpcsoil", "power", "power_daily", "cmip6"]:
            globals()[s]()
