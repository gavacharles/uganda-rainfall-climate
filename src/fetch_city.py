"""City data for the urban-flooding paper (Johannesburg here; Kampala via fetch_kampala.py).

Outputs (data/processed/), <city> = johannesburg:
  <city>_ghsl_built.nc, <city>_worldcover.tif, <city>_dem.tif (mosaic), <city>_boundary.geojson,
  <city>_chirps_daily.nc, <city>_arc2_daily.nc, <city>_waterways.geojson (named OSM waterways, for catchment names)
Also writes kampala_waterways.geojson.
"""
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import requests
import xarray as xr
from rasterio.merge import merge
from shapely.geometry import LineString

from fetch_kampala import EPOCHS, GHSL, curl, crop

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"
CITY = {
    "johannesburg": dict(box=(27.60, -26.65, 28.40, -25.80), ghsl="R12_C21",
                         dem=["S26_00_E027_00", "S26_00_E028_00", "S27_00_E027_00", "S27_00_E028_00"],
                         wc="S27E027", iso="ZAF", adm="ADM2", name="City of Johannesburg"),
    "kampala": dict(box=(32.30, 0.00, 32.95, 0.60)),
    "nairobi": dict(box=(36.60, -1.47, 37.15, -1.13), ghsl="R10_C22", dem=["S02_00_E036_00", "S02_00_E037_00"],
                    wc="S03E036"),
    "dar_es_salaam": dict(box=(39.00, -7.20, 39.45, -6.60), ghsl="R10_C22", dem=["S07_00_E039_00", "S08_00_E039_00"],
                          wc="S09E039"),
    "lagos": dict(box=(3.00, 6.38, 3.80, 6.75), ghsl="R9_C19", dem=["N06_00_E003_00"], wc="N06E003"),
}
IRI = "http://iridl.ldeo.columbia.edu/SOURCES"


def raw(city):
    p = ROOT / "data" / "raw" / city
    p.mkdir(parents=True, exist_ok=True)
    return p


def crop_to(src, box, dst=None):
    import fetch_kampala as fk
    old = fk.BOX
    fk.BOX = box
    try:
        return crop(src, dst)
    finally:
        fk.BOX = old


def ghsl(city):
    c = CITY[city]
    f = OUT / f"{city}_ghsl_built.nc"
    if f.exists():
        return
    layers = []
    for y in EPOCHS:
        z = raw(city) / f"ghsl_{y}.zip"
        if not z.exists():
            curl(GHSL.format(y=y).replace("R9_C22", c["ghsl"]), z)
        with zipfile.ZipFile(z) as zz:
            name = [n for n in zz.namelist() if n.endswith(".tif")][0]
            tif = raw(city) / name
            if not tif.exists():
                zz.extract(name, raw(city))
        a, t = crop_to(tif, c["box"])
        tif.unlink()
        lon = t.c + t.a * (np.arange(a.shape[1]) + 0.5)
        lat = t.f + t.e * (np.arange(a.shape[0]) + 0.5)
        layers.append(xr.DataArray(a.astype("float32"), dims=("lat", "lon"), coords={"lat": lat, "lon": lon}))
        print(city, "ghsl", y, round(float(a.sum()) / 1e6, 1), "km2", flush=True)
    da = xr.concat(layers, xr.DataArray(EPOCHS, dims="epoch", name="epoch")).rename("built_m2")
    da.sortby("lat").to_netcdf(f)


def dem(city):
    c = CITY[city]
    f = OUT / f"{city}_dem.tif"
    if f.exists():
        return
    srcs = []
    for tname in c["dem"]:
        p = raw(city) / f"cop30_{tname}.tif"
        if not p.exists():
            curl(f"https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{tname}_DEM/Copernicus_DSM_COG_10_{tname}_DEM.tif", p)
        srcs.append(rasterio.open(p))
    lon0, lat0, lon1, lat1 = c["box"]
    mos, tr = merge(srcs, bounds=(lon0, lat0, lon1, lat1))
    prof = srcs[0].profile | dict(height=mos.shape[1], width=mos.shape[2], transform=tr, compress="deflate", count=1)
    for k in ("blockxsize", "blockysize", "tiled"):
        prof.pop(k, None)
    with rasterio.open(f, "w", **prof) as d:
        d.write(mos[0], 1)


def worldcover(city):
    c = CITY[city]
    f = OUT / f"{city}_worldcover.tif"
    if not f.exists():
        src = curl(f"https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{c['wc']}_Map.tif",
                   raw(city) / f"worldcover_{c['wc']}.tif")
        crop_to(src, c["box"], f)


def boundary(city):
    c = CITY[city]
    f = OUT / f"{city}_boundary.geojson"
    if f.exists():
        return
    meta = requests.get(f"https://www.geoboundaries.org/api/current/gbOpen/{c['iso']}/{c['adm']}/", timeout=60).json()
    g = gpd.read_file(meta["gjDownloadURL"])
    g = g[g.shapeName.str.contains("Johannesburg")]
    print(g.shapeName.tolist())
    g.to_file(f, driver="GeoJSON")


def rain(city, pad=1.4):
    """Daily CHIRPS and ARC2 for the city box plus `pad` degrees (room for the calibration gauges)."""
    from concurrent.futures import ThreadPoolExecutor
    c = CITY[city]
    lon0, lat0, lon1, lat1 = c["box"]
    for prod, path, var, y0 in (("chirps", ".UCSB/.CHIRPS/.v2p0/.daily-improved/.global/.0p25/.prcp", "prcp", 1981),
                                ("arc2", ".NOAA/.NCEP/.CPC/.FEWS/.Africa/.DAILY/.ARC2/.daily/.est_prcp", "est_prcp", 1983)):
        f = OUT / f"{city}_{prod}_daily.nc"
        if f.exists():
            continue

        def one(y):
            p = raw(city) / f"{prod}_{y}.nc"
            if not p.exists():
                curl(f"{IRI}/{path}/X/{lon0 - pad}/{lon1 + pad}/RANGEEDGES/Y/{lat0 - pad}/{lat1 + pad}/RANGEEDGES/"
                     f"T/(1%20Jan%20{y})/(31%20Dec%20{y})/RANGEEDGES/data.nc", p)
            print(city, prod, y, flush=True)
            return p

        with ThreadPoolExecutor(6) as ex:
            files = list(ex.map(one, range(y0, 2026)))
        parts = []
        for y, p in zip(range(y0, 2026), files):
            v = xr.open_dataset(p, decode_times=False)[var]
            v = v.assign_coords(T=np.datetime64(f"{y}-01-01") + np.arange(v.sizes["T"]).astype("timedelta64[D]"))
            parts.append(v.rename(T="time", X="lon", Y="lat").load())
        da = xr.concat(parts, "time").sortby("lat").rename("precip")
        da.where(da >= 0).astype("float32").to_netcdf(f)
        print(city, prod, dict(da.sizes), flush=True)


def waterways(city):
    f = OUT / f"{city}_waterways.geojson"
    if f.exists():
        return
    lon0, lat0, lon1, lat1 = CITY[city]["box"]
    q = (f'[out:json][timeout:180];way["waterway"~"river|stream|canal|drain"]["name"]'
         f'({lat0},{lon0},{lat1},{lon1});out geom;')
    r = None
    for host in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
                 "https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass.private.coffee/api/interpreter"):
        try:
            r = requests.post(host, data={"data": q}, timeout=300,
                              headers={"User-Agent": "uganda-rainfall-climate research (python-requests)"})
            if r.ok:
                break
        except requests.RequestException:
            continue
    r.raise_for_status()
    feats = [dict(name=e["tags"]["name"], kind=e["tags"].get("waterway"),
                  geometry=LineString([(p["lon"], p["lat"]) for p in e["geometry"]]))
             for e in r.json()["elements"] if len(e.get("geometry", [])) > 1]
    gpd.GeoDataFrame(feats, crs=4326).to_file(f, driver="GeoJSON")
    print(city, "waterways", len(feats))


if __name__ == "__main__":
    city = sys.argv[1]
    steps = sys.argv[2:] or (["waterways"] if city == "kampala" else ["boundary", "waterways", "dem", "worldcover", "ghsl", "rain"])
    if city not in ("kampala", "johannesburg"):
        steps = [x for x in steps if x != "boundary"]  # boundaries saved from geoBoundaries ADM1 beforehand
    for s in steps:
        globals()[s](city)
