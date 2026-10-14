"""Paper R upgrades: spatially varying silt, independent validation, and the cost of disruption.

spatial   silt concentrated where dumping pressure is highest: depth lost = 0.10 + 0.40 x (waste-pressure percentile),
          Manning n = 0.030 + 0.015 x percentile (mean ~ the uniform 30% case); Shapley shares for today
validate  flood-prone road locations from KCCA's 2021 risk assessment (as listed in the Daily Monitor editorial
          "Let's watch out for flood prone roads", 2023) and the Observer's list of roads often cut off, plus the
          catalogue's road floods; geocoded with OpenStreetMap Nominatim. Main-road pieces within 300 m of a reported
          spot are positives, all other main-road pieces negatives; score = modelled depth (10-year storm).
          Reports AUC, hit rates, and the share of all main-road km the model flags (false-alarm proxy).
costs     annual value of lost access: people cut off x flood duration x share travelling x value of time, plus
          delay minutes for those still connected; ranges for every term; compared with avoided building damage
          (Paper 4) and KCCA's road-and-drainage maintenance allocation (UGX 10 bn)
Outputs: results/kd_roadsR_spatial.csv, kd_roadsR_validation*.csv, kd_roadsR_costs.csv
"""
import sys
import time

import geopandas as gpd
import numpy as np
import pandas as pd
import requests

import kd_roads_attrib as ra
import kd_roads_mc as mc
from common import RES, ROOT

KD = ROOT / "data" / "kd"
UTM = 32636

SPOTS = [  # (label, source, Nominatim query or (lat, lon), OSM road-name pattern)
    ("Jinja Road at Game–Shoprite (Lugogo)", "KCCA 2021", "Lugogo Mall, Kampala", "Jinja Road"),
    ("Jinja Road at Banda (Moil)", "KCCA 2021", (0.3380, 32.6400), "Jinja Road"),
    ("Jinja Road at Banda (Yoshino)", "KCCA 2021", (0.3400, 32.6460), "Jinja Road"),
    ("Lugogo Bypass (Cricket Oval)", "KCCA 2021", "Lugogo Cricket Oval, Kampala", "Lugogo"),
    ("Kyambogo Junction", "KCCA 2021", (0.3335, 32.6270), "Jinja Road"),
    ("Kibuli Road (Police Station)", "KCCA 2021", "Kibuli Police Station, Kampala", "Kibuli"),
    ("Mulago roundabout / flyover", "KCCA 2021", "Mulago roundabout, Kampala", ""),
    ("Queen's Way", "Observer", "Queens Way, Kampala", "Queen"),
    ("Ssebaana Kizito Road", "Observer", "Ssebaana Kizito Road, Kampala", "Kizito"),
    ("Kabuusu Junction", "Observer", "Kabuusu, Kampala", ""),
    ("Jinja Road roundabout", "Observer", "Jinja Road roundabout, Kampala", ""),
    ("Hoima Road at Lubigi", "catalogue", (0.3410, 32.5360), "Hoima Road"),
    ("Northern Bypass, Bwaise–Kalerwe", "catalogue", (0.3530, 32.5700), "Northern Bypass"),
    ("Bombo Road at Bwaise", "catalogue", (0.3520, 32.5620), "Bombo Road"),
    ("Entebbe Road, Namasuba", "catalogue", (0.2722, 32.5634), "Entebbe Road"),
    ("Mukwano Road", "catalogue", (0.3083, 32.5872), "Mukwano"),
    ("Kinawataka Road", "catalogue", (0.3351, 32.6432), "Kinawataka"),
]


def geocode(q):
    r = requests.get("https://nominatim.openstreetmap.org/search", params=dict(q=q, format="json", limit=1,
                     viewbox="32.45,0.42,32.72,0.20", bounded=1),
                     headers={"User-Agent": "kampala-roads-research/1.0 (research use)"}, timeout=30)
    time.sleep(1.1)
    j = r.json()
    return (float(j[0]["lat"]), float(j[0]["lon"])) if j else None


def spatial():
    ctx = mc.setup()
    seg = gpd.read_file(KD / "segments.gpkg")[["seg_id", "waste_pressure"]].set_index("seg_id")
    wp = seg.waste_pressure.reindex(ctx["h"].seg_id).fillna(0).values
    pct = pd.Series(wp).rank(pct=True).values
    rows = []
    for tag, sd, ns in (("uniform 30%", 0.30, 0.035),
                        ("dumping-weighted (mean 30%)", 0.10 + 0.40 * pct, 0.030 + 0.015 * pct)):
        P = dict(mc.CENTRAL, silt_depth=sd, n_silt=ns)
        out = mc.run(ctx, P)
        for m in ("ea_km", "ea_cut"):
            r = mc.shares(out, m)
            rows.append(dict(scenario=tag, metric=m, siltation=r[f"{m}_today_S"], paving=r[f"{m}_today_L"],
                             encroachment=r[f"{m}_today_E"], total_today=r[f"{m}_today_total"],
                             silt_2yr_km=out[(1, 1, 1, 0)]["km_T2"]))
    d = pd.DataFrame(rows)
    d.round(2).to_csv(RES / "kd_roadsR_spatial.csv", index=False)
    print(d.round(1).to_string())


def validate():
    from sklearn.metrics import roc_auc_score
    p = gpd.read_parquet(KD / "road_pieces.parquet").to_crs(UTM).reset_index(drop=True)
    z = np.load(KD / "roadsR_depth.npz")
    d_clean, d_silt = z["1010"], z["1110"]
    j10 = ra.TS.index(10)
    j2 = ra.TS.index(2)
    main = p.cls.isin(["highway", "main road", "local through road"]).values & ~p.raised.values
    mid = p.geometry.interpolate(0.5, normalized=True)
    rows = []
    pos = np.zeros(len(p), bool)
    for lab, src, q, pat in SPOTS:
        ll = q if isinstance(q, tuple) else geocode(q)
        if ll is None:
            rows.append(dict(spot=lab, source=src, geocoded=False))
            continue
        pt = gpd.GeoSeries(gpd.points_from_xy([ll[1]], [ll[0]]), crs=4326).to_crs(UTM).iloc[0]
        near = main & (mid.distance(pt).values <= 300)
        if pat:
            named = near & p.name.fillna("").str.contains(pat, case=False).values
            near = named if named.any() else near
        pos |= near
        rows.append(dict(spot=lab, source=src, geocoded=True, lat=round(ll[0], 5), lon=round(ll[1], 5),
                         pieces=int(near.sum()),
                         max_depth_T10_clean=float(d_clean[near, j10].max()) if near.any() else np.nan,
                         max_depth_T10_silted=float(d_silt[near, j10].max()) if near.any() else np.nan,
                         max_depth_T2_silted=float(d_silt[near, j2].max()) if near.any() else np.nan))
    v = pd.DataFrame(rows)
    v.round(2).to_csv(RES / "kd_roadsR_validation_spots.csv", index=False)
    print(v.round(2).to_string())
    m = main
    y = pos[m]
    km = p.length.values / 1000
    out = []
    for tag, D in (("clean", d_clean), ("silted", d_silt)):
        for T, j in (("2-yr", j2), ("10-yr", j10)):
            s = D[m, j]
            g = v[v.geocoded & (v.pieces > 0)]
            hit = (g[f"max_depth_T{T.split('-')[0]}_{tag}"] >= ra.IMP).mean() if f"max_depth_T{T.split('-')[0]}_{tag}" in g \
                else np.nan
            out.append(dict(state=tag, storm=T, auc=roc_auc_score(y, s) if y.any() else np.nan,
                            spots_hit_pct=100 * hit if hit == hit else np.nan,
                            main_road_km_flagged_pct=100 * km[m][s >= ra.IMP].sum() / km[m].sum(),
                            positives=int(y.sum()), negatives=int((~y).sum())))
    o = pd.DataFrame(out)
    o.round(3).to_csv(RES / "kd_roadsR_validation.csv", index=False)
    print(o.round(3).to_string())


def costs():
    """Annual value of lost access from flooded roads, clean vs silted (today), with ranges."""
    sc = pd.read_csv(RES / "kd_roadsR_scenarios.csv")
    pick = lambda S: sc[(sc.L == 1) & (sc.S == S) & (sc.E == 1) & (sc.C == 0)].iloc[0]
    pop = 3.617e6
    rng = np.random.default_rng(1)
    n = 20000
    vot = rng.uniform(0.5, 1.8, n)          # US$ per hour (income-based to productivity-based)
    dur = rng.uniform(2, 8, n)              # hours a flooded crossing stays impassable (flash floods)
    trav = rng.uniform(0.3, 0.7, n)         # share of residents who need to travel during the event
    res = {}
    for tag, S in (("clean", 0), ("silted", 1)):
        r = pick(S)
        cut_h = r.ea_cutoff_centre * dur * trav            # person-hours of lost access per year
        delay_h = r.ea_extra_min_centre / 60 * pop * trav  # extra person-hours for those still connected
        res[tag] = (cut_h + delay_h) * vot
    diff = res["silted"] - res["clean"]
    q = lambda a: (np.median(a) / 1e6, np.percentile(a, 5) / 1e6, np.percentile(a, 95) / 1e6)
    rows = [dict(item="travel disruption, channels clean (US$ m/yr)", central=q(res["clean"])[0], p05=q(res["clean"])[1],
                 p95=q(res["clean"])[2]),
            dict(item="travel disruption, channels silted (US$ m/yr)", central=q(res["silted"])[0], p05=q(res["silted"])[1],
                 p95=q(res["silted"])[2]),
            dict(item="avoided by keeping channels clean: travel (US$ m/yr)", central=q(diff)[0], p05=q(diff)[1],
                 p95=q(diff)[2])]
    dm = pd.read_csv(RES / "kd_damage_totals.csv").set_index("value_case")
    bd = dm.maintenance_value_musd_per_yr
    rows.append(dict(item="avoided by keeping channels clean: building damage (US$ m/yr, Paper 4)", central=bd["central"],
                     p05=bd["low"], p95=bd["high"]))
    rows.append(dict(item="KCCA road and drainage maintenance allocation (US$ m/yr, UGX 10 bn)", central=10e9 / 3700 / 1e6,
                     p05=np.nan, p95=np.nan))
    tot = q(diff)[0] + bd["central"]
    rows.append(dict(item="total avoided (travel + buildings), central (US$ m/yr)", central=tot, p05=np.nan, p95=np.nan))
    rows.append(dict(item="ratio of avoided losses to the KCCA allocation", central=tot / (10e9 / 3700 / 1e6), p05=np.nan,
                     p95=np.nan))
    o = pd.DataFrame(rows)
    o.round(2).to_csv(RES / "kd_roadsR_costs.csv", index=False)
    print(o.round(2).to_string())


if __name__ == "__main__":
    for f in sys.argv[1:] or ["spatial", "validate", "costs"]:
        globals()[f]()
