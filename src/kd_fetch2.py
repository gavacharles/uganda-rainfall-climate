"""Downloads for the follow-on papers (no logins).

roads      OpenStreetMap drivable roads, Greater Kampala core            -> data/kd/osm_roads.geojson
services   hospitals, clinics, health centres, schools (OSM)             -> data/kd/osm_services.geojson
lst        Landsat 8/9 surface temperature (ST_B10, 30 m), dry-season    -> data/kd/sat_lst.nc
           medians 2014-2016 and 2023-2025, plus NDVI
cities     Jinja, Mbale, Gulu, Mbarara, Arua: Copernicus 30 m DEM tile, OSM waterways, Microsoft buildings,
           JRC GHSL built-up and population crops                          -> data/kd/cities/<city>_*
"""
import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import planetary_computer as pc
import pystac_client
import rasterio
import xarray as xr
from rasterio.windows import from_bounds

from common import ROOT
from kd_fetch import overpass, to_gdf, UA
import kd_fetch

KD = ROOT / "data" / "kd"
RAWK = ROOT / "data" / "raw" / "kampala"
BBOX = [32.45, 0.20, 32.72, 0.42]
CITIES = {  # centre lat, lon; half-width (deg); Copernicus tile
    "jinja": (0.445, 33.205, 0.09, "N00_00_E033_00"),
    "mbale": (1.080, 34.175, 0.08, "N01_00_E034_00"),
    "gulu": (2.780, 32.300, 0.08, "N02_00_E032_00"),
    "mbarara": (-0.607, 30.655, 0.08, "S01_00_E030_00"),
    "arua": (3.020, 30.910, 0.08, "N03_00_E030_00"),
}


def roads():
    f = KD / "osm_roads.geojson"
    if f.exists():
        return
    kd_fetch.BOX = (32.45, 0.20, 32.72, 0.42)
    q = 'way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|living_street|service)$"];'
    g = to_gdf(overpass(q), ["highway", "name", "bridge", "oneway"])
    g = g[g.geom_type == "LineString"]
    g.to_file(f, driver="GeoJSON")
    print("roads", len(g), flush=True)


def services():
    f = KD / "osm_services.geojson"
    if f.exists():
        return
    kd_fetch.BOX = (32.45, 0.20, 32.72, 0.42)
    q = 'nwr["amenity"~"^(hospital|clinic|doctors|school|college|university)$"];nwr["healthcare"~"^(hospital|clinic|centre)$"];'
    g = to_gdf(overpass(q), ["name", "amenity", "healthcare", "operator:type"])
    g["geometry"] = g.geometry.representative_point()
    g.to_file(f, driver="GeoJSON")
    print("services", len(g), g.amenity.value_counts().to_dict(), flush=True)


def lst():
    f = KD / "sat_lst.nc"
    if f.exists():
        return
    from odc.stac import load
    cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
    out = {}
    for tag, years in (("early", (2014, 2015, 2016)), ("late", (2023, 2024, 2025))):
        items = []
        for y in years:
            for months in (("01-01", "02-28"), ("06-15", "08-31")):  # the two dry seasons
                items += list(cat.search(collections=["landsat-c2-l2"], bbox=BBOX, datetime=f"{y}-{months[0]}/{y}-{months[1]}",
                                         query={"eo:cloud_cover": {"lt": 40}, "platform": {"in": ["landsat-8", "landsat-9"]}}).items())
        print(tag, "scenes", len(items), flush=True)
        ds = load(items, bands=["lwir11", "red", "nir08", "qa_pixel"], bbox=BBOX, crs="EPSG:32636", resolution=30,
                  groupby="solar_day", chunks={"x": 1024, "y": 1024})
        qa = ds.qa_pixel
        clear = ((qa & (1 << 3)) == 0) & ((qa & (1 << 4)) == 0) & ((qa & (1 << 1)) == 0) & (qa != 0)
        st = (ds.lwir11.where(clear & (ds.lwir11 > 0)) * 0.00341802 + 149.0 - 273.15)
        red = ds.red.where(clear) * 0.0000275 - 0.2
        nir = ds.nir08.where(clear) * 0.0000275 - 0.2
        out[f"lst_{tag}"] = st.median("time")
        out[f"ndvi_{tag}"] = ((nir - red) / (nir + red)).median("time")
    xr.Dataset(out).astype("float32").compute().to_netcdf(f)
    print("lst saved", flush=True)


def cities():
    d = KD / "cities"
    d.mkdir(exist_ok=True)
    cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
    for city, (la, lo, h, tile) in CITIES.items():
        box = (lo - h, la - h, lo + h, la + h)
        # DEM
        fd = d / f"{city}_dem.tif"
        if not fd.exists():
            src = f"https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_{tile}_DEM/Copernicus_DSM_COG_10_{tile}_DEM.tif"
            with rasterio.open(src) as r:
                w = from_bounds(*box, r.transform)
                a = r.read(1, window=w)
                prof = r.profile | dict(height=a.shape[0], width=a.shape[1], transform=r.window_transform(w), compress="deflate")
                for k in ("blockxsize", "blockysize", "tiled"):
                    prof.pop(k, None)
            with rasterio.open(fd, "w", **prof) as o:
                o.write(a, 1)
        # GHSL built and population crops from the cached R9_C22 tiles
        for kind, pref, eps in (("built", "ghsl", [1975, 1985, 1995, 2005, 2015, 2020, 2025, 2030]),
                                ("pop", "ghspop", [1975, 1990, 2000, 2010, 2020, 2025, 2030])):
            fo = d / f"{city}_{kind}.nc"
            if fo.exists():
                continue
            layers = []
            for e in eps:
                z = RAWK / f"{pref}_{e}.zip"
                import zipfile
                n = [x for x in zipfile.ZipFile(z).namelist() if x.endswith(".tif")][0]
                with rasterio.open(f"zip://{z}!{n}") as r:
                    w = from_bounds(*box, r.transform)
                    a = r.read(1, window=w).astype("float32")
                    t = r.window_transform(w)
                a = np.where(a < 0, 0, a)
                lon = t.c + t.a * (np.arange(a.shape[1]) + 0.5)
                lat = t.f + t.e * (np.arange(a.shape[0]) + 0.5)
                layers.append(xr.DataArray(a, dims=("lat", "lon"), coords=dict(lat=lat, lon=lon)))
            da = xr.concat(layers, xr.DataArray(eps, dims="epoch", name="epoch")).rename(kind).sortby("lat")
            if kind == "pop" and abs(float(np.diff(da.lat).mean())) < 0.0005:
                k = int(round(0.000833 / abs(float(np.diff(da.lat).mean()))))
                da = da.coarsen(lat=k, lon=k, boundary="trim").sum().rename(kind)
            da.to_netcdf(fo)
        # OSM waterways
        fw = d / f"{city}_waterways.geojson"
        if not fw.exists():
            kd_fetch.BOX = box
            g = to_gdf(overpass('way["waterway"~"^(river|stream|canal|drain|ditch)$"];'), ["name", "waterway", "tunnel"])
            g = g[g.geom_type == "LineString"]
            g.to_file(fw, driver="GeoJSON")
            time.sleep(5)
        # Microsoft buildings
        fb = d / f"{city}_buildings.parquet"
        if not fb.exists():
            items = [i for i in cat.search(collections=["ms-buildings"], bbox=list(box)).items()
                     if i.properties.get("msbuildings:region") == "Uganda" or "Uganda" in i.id]
            items = [i for i in items if i.properties.get("msbuildings:quadkey")]
            parts = []
            for it in items:
                a = it.assets["data"]
                g = gpd.read_parquet(a.href, storage_options=a.extra_fields["table:storage_options"])
                parts.append(g.cx[box[0]:box[2], box[1]:box[3]])
            pd.concat(parts).to_parquet(fb) if parts else None
        print(city, "done", flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:] or ["roads", "services", "cities", "lst"]:
        globals()[s]()
