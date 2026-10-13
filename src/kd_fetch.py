"""Kampala drainage & wetlands study: open-data downloads (no logins).

osm      OpenStreetMap via Overpass: all waterways (drain/ditch/canal/stream/river, with culvert/covered tags),
         wetlands, landfills/dumps/waste points, markets, bridges over waterways  -> data/kd/osm_*.geojson
power    NASA POWER hourly point series for central Kampala (precip, T2M, dew point), 2001-present
         -> data/kd/power_hourly_kampala.csv
"""
import json
import sys
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "kd"
OUT.mkdir(parents=True, exist_ok=True)
BOX = (32.40, 0.15, 32.80, 0.50)  # Greater Kampala Metropolitan core (lon0, lat0, lon1, lat1)
HOSTS = ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
         "https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass.private.coffee/api/interpreter")
UA = {"User-Agent": "uganda-rainfall-climate research (python-requests)"}


def overpass(body):
    lon0, lat0, lon1, lat1 = BOX
    q = f"[out:json][timeout:300][bbox:{lat0},{lon0},{lat1},{lon1}];({body});out geom;"
    for host in HOSTS:
        try:
            r = requests.post(host, data={"data": q}, timeout=400, headers=UA)
            if r.ok:
                return r.json()["elements"]
        except requests.RequestException:
            pass
        time.sleep(5)
    raise RuntimeError("all Overpass mirrors failed")


def to_gdf(elements, keep):
    rows = []
    for e in elements:
        t = e.get("tags", {})
        geom = None
        if e["type"] == "node":
            geom = Point(e["lon"], e["lat"])
        elif e["type"] == "way" and len(e.get("geometry", [])) > 1:
            pts = [(p["lon"], p["lat"]) for p in e["geometry"]]
            closed = pts[0] == pts[-1] and len(pts) > 3
            area = closed and (t.get("natural") == "wetland" or "landuse" in t or "amenity" in t)
            geom = Polygon(pts) if area else LineString(pts)
        elif e["type"] == "relation":
            lines = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]]) for m in e.get("members", [])
                     if m.get("role") in ("outer", "") and len(m.get("geometry", []) or []) > 1]
            polys = list(polygonize(unary_union(lines))) if lines else []
            geom = unary_union(polys) if polys else None
        if geom is None or geom.is_empty:
            continue
        rows.append({"osm_id": f'{e["type"][0]}{e["id"]}', **{k: t.get(k) for k in keep}, "geometry": geom})
    return gpd.GeoDataFrame(rows, crs=4326)


def osm():
    jobs = {
        "waterways": ('way["waterway"~"^(river|stream|canal|drain|ditch)$"];',
                      ["name", "waterway", "tunnel", "culvert", "covered", "width", "intermittent", "layer"]),
        "wetlands": ('way["natural"="wetland"];relation["natural"="wetland"];way["landuse"="basin"];',
                     ["name", "natural", "wetland", "landuse"]),
        "waste": ('nwr["landuse"="landfill"];nwr["amenity"~"^(waste_disposal|waste_transfer_station|recycling)$"];'
                  'nwr["dump"];nwr["illegal_dumping"];',
                  ["name", "landuse", "amenity", "recycling_type"]),
        "markets": ('nwr["amenity"="marketplace"];', ["name", "amenity"]),
        "bridges": ('way["highway"]["bridge"="yes"];', ["name", "highway", "bridge"]),
    }
    for name, (q, keep) in jobs.items():
        f = OUT / f"osm_{name}.geojson"
        if f.exists():
            continue
        g = to_gdf(overpass(q), keep)
        g.to_file(f, driver="GeoJSON")
        print(name, len(g), flush=True)


def power():
    f = OUT / "power_hourly_kampala.csv"
    if f.exists():
        return
    frames = []
    for y in range(2001, 2027):
        end = f"{y}1231" if y < 2026 else pd.Timestamp.today().strftime("%Y%m%d")
        url = ("https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=PRECTOTCORR,T2M,T2MDEW"
               f"&community=RE&longitude=32.58&latitude=0.32&start={y}0101&end={end}&format=JSON&time-standard=LST")
        for attempt in range(4):
            try:
                r = requests.get(url, timeout=300, headers=UA)
                r.raise_for_status()
                p = r.json()["properties"]["parameter"]
                break
            except (requests.RequestException, KeyError, json.JSONDecodeError):
                time.sleep(10 * (attempt + 1))
        else:
            raise RuntimeError(f"POWER failed for {y}")
        df = pd.DataFrame(p)
        df.index = pd.to_datetime(df.index, format="%Y%m%d%H")
        frames.append(df)
        print("power", y, len(df), flush=True)
    out = pd.concat(frames).replace(-999, float("nan"))
    out.to_csv(f)


if __name__ == "__main__":
    for s in sys.argv[1:] or ["osm", "power"]:
        globals()[s]()
