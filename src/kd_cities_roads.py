"""Paper 5 (The next Kampalas): roads on the valley floors of Uganda's regional cities, same rules as Kampala.

For Kampala (core box) and Jinja, Mbale, Gulu, Mbarara, Arua (Paper 7 boxes):
  roads      OpenStreetMap drivable roads (Overpass), cut into <= 100 m pieces
  terrain    Copernicus GLO-30, D8 channels draining >= 0.25 km2, HAND (kd_cities.terrain, identical everywhere)
  per piece  lowest HAND along it; distance to a terrain channel; crossing = piece passes over a channel cell and is
             not tagged bridge; urbanised = first GHSL epoch with built share >= 0.15 in its 100 m cell
  measures   road km on the valley floor (HAND < 3 m) and on low ground (HAND < 2 m, <= 150 m from a channel);
             share of road whose ground urbanised in each period that lies on low ground (is new road going into the
             valleys?); crossings per 100 km of road; low-ground road in the newest urban areas (2010-2030)
Outputs: data/kd/cities/<city>_roads.geojson, results/kd_cities_roads.csv, kd_cities_roads_epochs.csv, figure kd56.
"""
import sys
import time

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import xarray as xr

import kd_fetch
from common import FIG, RES, ROOT, save
from kd_cities import CITIES, city_inputs, terrain
from kd_fetch import overpass, to_gdf
from kd_roads import pieces

KD = ROOT / "data" / "kd"
CD = KD / "cities"
OUT = FIG / "kampala_drainage"
Q = ('way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|motorway_link|trunk_link|'
     'primary_link|secondary_link|tertiary_link|living_street|service)$"];')


def fetch():
    for c in CITIES:
        f = CD / f"{c}_roads.geojson"
        if f.exists() or c == "kampala":
            continue
        with rasterio.open(CD / f"{c}_dem.tif") as r:
            b = r.bounds
        kd_fetch.BOX = (b.left, b.bottom, b.right, b.top)
        for k in range(5):
            try:
                g = to_gdf(overpass(Q), ["highway", "name", "bridge"])
                break
            except Exception as e:
                print(c, "retry", e, flush=True)
                time.sleep(30)
        g = g[g.geom_type == "LineString"]
        g.to_file(f, driver="GeoJSON")
        print(c, "roads", len(g), flush=True)


def analyse():
    rows, ep_rows = [], []
    for c in CITIES:
        f, built, pop, b = city_inputs(c)
        hand, dist, tr, cell = terrain(f)
        with rasterio.open(f) as r:
            bnd = r.bounds
        if c == "kampala":
            roads = gpd.read_file(KD / "osm_roads.geojson").cx[bnd.left:bnd.right, bnd.bottom:bnd.top]
        else:
            roads = gpd.read_file(CD / f"{c}_roads.geojson")
        roads = roads[roads.geom_type == "LineString"].copy()
        if "osm_id" not in roads:
            roads["osm_id"] = np.arange(len(roads))
        for col in ("name", "bridge"):
            if col not in roads:
                roads[col] = None
        p = pieces(roads.to_crs(32636)).to_crs(4326)
        p["len_m"] = p.to_crs(32636).length
        H, W = hand.shape
        stream = dist == 0
        hmin, dmin, cross = [], [], []
        for g, Lm in zip(p.geometry.values, p.len_m.values):
            L = g.length
            pts = [g.interpolate(x) for x in np.linspace(0, L, max(2, int(Lm // 15) + 2))]
            col = np.clip(((np.array([q.x for q in pts]) - tr.c) / tr.a).astype(int), 0, W - 1)
            row = np.clip(((np.array([q.y for q in pts]) - tr.f) / tr.e).astype(int), 0, H - 1)
            hv = hand[row, col]
            hmin.append(np.nanmin(hv) if np.isfinite(hv).any() else np.nan)
            dmin.append(dist[row, col].min())
            cross.append(bool(stream[row, col].any()))
        p["hand_min"], p["dist_m"], p["cross"] = hmin, dmin, cross
        p["cross"] &= ~p.bridge.fillna("").isin(["yes", "viaduct"])
        mid = p.geometry.interpolate(0.5, normalized=True)
        gcell = (abs(float(np.diff(built.lon).mean())) * 111320 * np.cos(np.deg2rad(float(built.lat.mean())))) * \
                (abs(float(np.diff(built.lat).mean())) * 110574)
        first = np.full(len(p), np.nan)
        for e in sorted((int(v) for v in built.epoch.values), reverse=True):
            bs = built.sel(epoch=e).sel(lat=xr.DataArray(mid.y.values), lon=xr.DataArray(mid.x.values), method="nearest").values / gcell
            first = np.where(bs >= 0.15, e, first)
        p["urbanised"] = first
        km = lambda m: float(p.len_m[m].sum() / 1000)
        low = (p.hand_min < 2) & (p.dist_m <= 150)
        vf = p.hand_min < 3
        r = dict(city=c, road_km=km(p.len_m > 0), valley_floor_km=km(vf), low_ground_km=km(low),
                 valley_floor_pct=100 * km(vf) / km(p.len_m > 0), low_ground_pct=100 * km(low) / km(p.len_m > 0),
                 crossings=int(p.cross.sum()), crossings_per_100km=100 * p.cross.sum() / km(p.len_m > 0))
        for lab, lo, hi in (("by 1990", 0, 1990), ("1995-2005", 1991, 2005), ("2010-2020", 2006, 2020),
                            ("2025-2030 (proj.)", 2021, 2030)):
            m = (p.urbanised >= lo) & (p.urbanised <= hi)
            ep_rows.append(dict(city=c, period=lab, road_km=km(m), low_ground_pct=100 * km(m & low) / max(km(m), 1e-9),
                                valley_floor_pct=100 * km(m & vf) / max(km(m), 1e-9)))
        r["low_ground_pct_not_yet_urban"] = 100 * km(p.urbanised.isna() & low) / max(km(p.urbanised.isna()), 1e-9)
        rows.append(r)
        p[["highway", "len_m", "hand_min", "dist_m", "cross", "urbanised", "geometry"]].to_file(CD / f"{c}_road_pieces.gpkg")
        print(c, {k: round(v, 1) if isinstance(v, float) else v for k, v in r.items()}, flush=True)
    t = pd.DataFrame(rows)
    t.round(2).to_csv(RES / "kd_cities_roads.csv", index=False)
    e = pd.DataFrame(ep_rows)
    e.round(2).to_csv(RES / "kd_cities_roads_epochs.csv", index=False)
    print(t.round(1).to_string())
    print(e.pivot(index="city", columns="period", values="low_ground_pct").round(1).to_string())
    figure(t, e)


def figure(t, e):
    names = {c: c.capitalize() for c in CITIES}
    cols = {"kampala": "#333333", "jinja": "#1b9e77", "mbale": "#d95f02", "gulu": "#7570b3", "mbarara": "#e7298a", "arua": "#66a61e"}
    fig, axs = plt.subplots(1, 2, figsize=(15, 5.6), gridspec_kw=dict(wspace=0.28))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.8, bottom=0.2)
    order = ["by 1990", "1995-2005", "2010-2020"]  # 2025-30 projection omitted: < 30 km of road per city
    for c in CITIES:
        d = e[e.city == c].set_index("period").reindex(order)
        axs[0].plot(range(3), d.low_ground_pct, "-o", color=cols[c], lw=2.8 if c == "kampala" else 1.8, label=names[c])
    axs[0].set_xticks(range(3))
    axs[0].set_xticklabels(order, fontsize=9.5)
    axs[0].set_ylabel("road on low ground beside channels (%)")
    axs[0].set_xlabel("when the ground under the road became urban")
    axs[0].set_title("a  Are new roads going into the valleys?", loc="left", fontsize=11.5)
    axs[0].legend(fontsize=9, ncol=2, frameon=False)
    axs[0].spines[["top", "right"]].set_visible(False)
    tt = t.set_index("city").reindex(list(CITIES))
    x = np.arange(len(tt))
    axs[1].bar(x, tt.low_ground_pct, 0.6, color="#d6604d")
    for i, (v, cr) in enumerate(zip(tt.low_ground_pct, tt.crossings_per_100km)):
        axs[1].text(i, v + 0.3, f"{v:.0f}%", ha="center", fontsize=11, fontweight="bold")
        axs[1].text(i, -1.9, f"{cr:.0f}", ha="center", fontsize=10, color="#2166ac")
    axs[1].text(-0.6, -2.9, "channel crossings per 100 km of road", fontsize=9.5, color="#2166ac")
    axs[1].set_ylim(-3.4, 14)
    axs[1].xaxis.set_ticks_position("top")
    axs[1].tick_params(axis="x", labeltop=False, labelbottom=False)
    for i, c_ in enumerate(tt.index):
        axs[1].text(i, -0.9, names[c_], ha="center", fontsize=10.5)
    axs[1].set_xticks(x)
    axs[1].set_xticklabels([names[c] for c in tt.index])
    axs[1].tick_params(axis="x", pad=4, length=0)
    axs[1].set_yticks([0, 4, 8, 12])
    axs[1].spines[["bottom"]].set_visible(False)
    axs[1].set_ylabel("road on low ground beside channels (%)")
    axs[1].set_title("b  Road exposure today", loc="left", fontsize=11.5)
    axs[1].spines[["top", "right"]].set_visible(False)
    fig.suptitle("Roads and valley floors in Uganda's growing cities", x=0.01, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.01, 0.875, "Identical open-data rules everywhere: OpenStreetMap roads, Copernicus terrain channels, JRC GHSL "
             "urbanisation dates", fontsize=10.5, color="#555")
    save(fig, "kd56_cities_roads.png", OUT,
         source="Roads: © OpenStreetMap contributors · terrain: Copernicus GLO-30 DEM · built-up: JRC GHSL R2023A "
                "(2025, 2030 projected) · method: this study")


if __name__ == "__main__":
    for f_ in sys.argv[1:] or ["fetch", "analyse"]:
        globals()[f_]()
