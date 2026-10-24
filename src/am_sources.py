"""Flood x AMR paper 1, step 1: inventory of potential sources of antimicrobial resistance, and of receptors.

Sources (points, with a class):
  hospital      OSM amenity/healthcare = hospital                       (osm_services.geojson)
  clinic        OSM amenity/healthcare = clinic or doctors              (osm_services.geojson)
  wastewater    OSM man_made = wastewater_plant                          (Geofabrik Uganda extract)
  abattoir      OSM industrial/building = slaughterhouse, or name with abattoir/slaughter (OSM maps only Wambizzi; the
                City Abattoir is not mapped, a limitation stated in the paper)
                Treatment works mapped as many buildings (sludge tanks, trickling filters) are merged into one plant.
  market        OSM amenity = marketplace                                (osm_markets.geojson)
  waste         OSM amenity = waste_disposal / waste_transfer_station, landuse = landfill   (osm_waste.geojson)
  (on-site sanitation is carried by population, GHS-POP, in am_index.py)
Receptors: water points from the Water Point Data Exchange (WPdx), with source type and functional status.
Outputs: data/kd/amr/sources.gpkg, data/kd/amr/water_points.gpkg, results/am_sources_summary.csv
"""
import json
import os

import geopandas as gpd
import numpy as np
import pandas as pd

from common import RES, ROOT

KD = ROOT / "data" / "kd"
AM = KD / "amr"
VIEW = (32.38, 0.12, 32.80, 0.50)
PBF = ROOT / "data" / "raw" / "uganda-latest.osm.pbf"


def pt(g):
    g = g.to_crs(4326)
    g["geometry"] = g.geometry.representative_point()
    return g


def from_pbf():
    """Abattoirs and wastewater plants from the Uganda extract, read layer by layer within the view (non-interleaved:
    GDAL keeps its node index on disk, so memory stays near 400 MB)."""
    import pyogrio
    out = []
    for layer, where in (("points", "other_tags LIKE '%slaughterhouse%' OR man_made = 'wastewater_plant' OR other_tags LIKE '%abattoir%'"),
                         ("multipolygons", "man_made = 'wastewater_plant' OR other_tags LIKE '%slaughterhouse%' OR "
                                           "building = 'slaughterhouse' OR name LIKE '%abattoir%' OR name LIKE '%slaughter%' OR "
                                           "name LIKE '%sludge%' OR name LIKE '%trickling%' OR name LIKE '%trikling%' OR name LIKE '%sewage%'")):
        g = pyogrio.read_dataframe(PBF, layer=layer, bbox=VIEW, where=where)
        if len(g):
            tags = g.get("other_tags", pd.Series("", index=g.index)).fillna("")
            mm = g.get("man_made", pd.Series("", index=g.index)).fillna("")
            nm = g.get("name", pd.Series("", index=g.index)).fillna("").str.lower()
            g["cls"] = ["wastewater" if m == "wastewater_plant" or "wastewater_plant" in t or any(k in n for k in ("sludge", "trickling", "trikling", "sewage"))
                        else "abattoir" for m, t, n in zip(mm, tags, nm)]
            out.append(pt(g[["name", "cls", "geometry"]]))
    return pd.concat(out) if out else gpd.GeoDataFrame(columns=["name", "cls", "geometry"], crs=4326)


def main():
    AM.mkdir(exist_ok=True)
    sv = gpd.read_file(KD / "osm_services.geojson")
    am, hc = sv.amenity.fillna(""), sv.healthcare.fillna("")
    sv["cls"] = None
    sv.loc[(am == "hospital") | hc.str.contains("hospital"), "cls"] = "hospital"
    sv.loc[sv.cls.isna() & (am.isin(["clinic", "doctors"]) | hc.str.contains("clinic|doctor")), "cls"] = "clinic"
    health = pt(sv[sv.cls.notna()][["name", "cls", "geometry"]])
    mk = pt(gpd.read_file(KD / "osm_markets.geojson")[["name", "geometry"]].assign(cls="market"))
    ws = gpd.read_file(KD / "osm_waste.geojson")
    ws = ws[ws.amenity.isin(["waste_disposal", "waste_transfer_station"]) | (ws.landuse == "landfill")]
    ws = pt(ws[["name", "geometry"]].assign(cls="waste"))
    other = from_pbf()
    src = pd.concat([health, mk, ws, other], ignore_index=True)
    src = gpd.GeoDataFrame(src, geometry="geometry", crs=4326).cx[VIEW[0]:VIEW[2], VIEW[1]:VIEW[3]]
    # one record per facility: drop duplicates within 30 m of the same class (node and building of the same place)
    u = src.to_crs(32636)
    u["k"] = u.cls + "_" + (u.geometry.x // 30).astype(int).astype(str) + "_" + (u.geometry.y // 30).astype(int).astype(str)
    src = src.loc[~u.k.duplicated()].reset_index(drop=True)
    # a treatment works is mapped as many buildings (tanks, filters): merge wastewater features within 500 m into one plant
    w = src[src.cls == "wastewater"].to_crs(32636)
    if len(w) > 1:
        lab, k = -np.ones(len(w), int), 0
        xy = np.c_[w.geometry.x, w.geometry.y]
        for i in range(len(w)):
            if lab[i] < 0:
                lab[(lab < 0) & (np.hypot(*(xy - xy[i]).T) < 500)] = k; k += 1
        w["plant"] = lab
        keep = w.groupby("plant").first()
        keep["name"] = w.groupby("plant").name.agg(lambda v: next((x for x in v if x and ("plant" in x.lower() or "works" in x.lower())), "Wastewater treatment works (Bugolobi)"))
        keep = gpd.GeoDataFrame(keep.reset_index(drop=True), geometry=gpd.points_from_xy(w.groupby("plant").geometry.apply(lambda g: g.x.mean()),
                                w.groupby("plant").geometry.apply(lambda g: g.y.mean())), crs=32636).to_crs(4326)
        src = pd.concat([src[src.cls != "wastewater"], keep[["name", "cls", "geometry"]]], ignore_index=True)
    src.to_file(AM / "sources.gpkg", driver="GPKG")

    wp = pd.DataFrame(json.loads((AM / "wpdx.json").read_text()))
    wp = gpd.GeoDataFrame(wp[["water_source_clean", "status_id", "install_year"]].rename(columns={"water_source_clean": "source", "status_id": "functional"}),
                          geometry=gpd.points_from_xy(wp.lon_deg.astype(float), wp.lat_deg.astype(float)), crs=4326)
    wp["source"] = wp.source.fillna("Unknown")
    wp.to_file(AM / "water_points.gpkg", driver="GPKG")

    s = src.cls.value_counts().rename("sources").to_frame()
    s.loc["water points (WPdx)"] = len(wp)
    s.to_csv(RES / "am_sources_summary.csv")
    print(s.to_string())
    print(wp.source.value_counts().to_string())


if __name__ == "__main__":
    main()
