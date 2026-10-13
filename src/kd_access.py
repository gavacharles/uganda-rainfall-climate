"""Paper 3: what floods cut off - access to hospitals and schools when Kampala's low roads flood.

Road graph: OpenStreetMap drivable roads (Greater Kampala core), nodes snapped at 1 m, edge travel time from
length and a class speed (motorway/trunk 40, primary 30, secondary 25, tertiary 20, other 15 km/h - congested urban
speeds). A road edge is FLOODED in a scenario when its midpoint lies on ground below the water level h above the
nearest drain (HAND < h; h = 0.5, 1, 2 m) AND within 300 m of a flowing channel (so lake-shore flats are excluded),
or within 400 m of a reported flood hotspot (hotspot scenario). Bridges (OSM bridge=yes) never flood.
Population: JRC GHS-POP 2020, 100 m cells, attached to the nearest road node.
Measures per scenario:
  isolated     residents with NO road route to any hospital
  delayed      residents whose fastest trip to a hospital becomes > 2x longer AND > 10 min longer
  >30 min      residents more than 30 minutes from a hospital
  facilities   hospitals and schools that sit on flooded ground (unreachable or under water)
  critical     road links whose flooding (single-link removal) adds the most person-minutes to hospital access
Outputs: results/kd_access_*.csv, figures kd32-kd34.
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import rasterio
import shapely
import xarray as xr

from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
UTM = 32636
BOX = (32.45, 0.20, 32.72, 0.42)
SPEED = {"motorway": 40, "trunk": 40, "primary": 30, "secondary": 25, "tertiary": 20}
SRC = ("Roads, hospitals, schools, channels: © OpenStreetMap contributors · population: JRC GHS-POP R2023A (2020) · "
       "terrain: Copernicus GLO-30 DEM · hotspots: KCCA/NEMA lists, news and local reports (approx.)")


def hand_at(lon, lat):
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand = r.read(2)
        tr = r.transform
    col = ((np.asarray(lon) - tr.c) / tr.a).astype(int).clip(0, hand.shape[1] - 1)
    row = ((np.asarray(lat) - tr.f) / tr.e).astype(int).clip(0, hand.shape[0] - 1)
    return hand[row, col]


def build_graph():
    r = gpd.read_file(KD / "osm_roads.geojson").cx[BOX[0]:BOX[2], BOX[1]:BOX[3]]
    r = r[r.geom_type == "LineString"].reset_index(drop=True)
    ru = r.to_crs(UTM)
    G = nx.Graph()
    rows = []
    key = lambda xy: (round(xy[0]), round(xy[1]))
    for i, (g, hw, br) in enumerate(zip(ru.geometry, r.highway, r.bridge)):
        cs = list(g.coords)
        base = (hw or "").replace("_link", "")
        v = SPEED.get(base, 15) / 3.6  # m/s
        for a, b in zip(cs[:-1], cs[1:]):
            L = float(np.hypot(b[0] - a[0], b[1] - a[1]))
            if L <= 0:
                continue
            u, w = key(a), key(b)
            G.add_edge(u, w, t=L / v / 60.0, L=L, way=i)
            rows.append((u, w, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, i, br == "yes", base))
    e = pd.DataFrame(rows, columns=["u", "v", "mx", "my", "way", "bridge", "hw"])
    # keep the largest connected component
    big = max(nx.connected_components(G), key=len)
    G = G.subgraph(big).copy()
    e = e[e.u.isin(big)].reset_index(drop=True)
    mid = gpd.GeoSeries(gpd.points_from_xy(e.mx, e.my), crs=UTM).to_crs(4326)
    e["hand"] = hand_at(mid.x.values, mid.y.values)
    s = gpd.read_file(KD / "segments.gpkg").to_crs(UTM)
    fl = s[s.up_km2 >= 0.25].geometry.values
    pts = gpd.points_from_xy(e.mx, e.my)
    near = np.zeros(len(e), bool)
    near[np.unique(shapely.STRtree(pts).query(fl, predicate="dwithin", distance=300)[1])] = True
    e["near_channel"] = near
    hs = pd.read_csv(KD / "flood_hotspots.csv")
    hp = gpd.GeoSeries(gpd.points_from_xy(hs.lon, hs.lat), crs=4326).to_crs(UTM).values
    nh = np.zeros(len(e), bool)
    nh[np.unique(shapely.STRtree(pts).query(hp, predicate="dwithin", distance=400)[1])] = True
    e["near_hotspot"] = nh
    print("graph nodes", G.number_of_nodes(), "edges", G.number_of_edges(), flush=True)
    return G, e


def attach(G, xs, ys):
    nodes = np.array(list(G.nodes))
    tree = shapely.STRtree(shapely.points(nodes))
    idx = tree.nearest(shapely.points(np.c_[xs, ys]))
    return [tuple(nodes[i]) for i in idx]


def candidates(G, xs, ys, k=8, r=250):
    """Up to k road nodes within r m of each point, nearest first (a resident can walk to any of them)."""
    nodes = np.array(list(G.nodes))
    tree = shapely.STRtree(shapely.points(nodes))
    pts = shapely.points(np.c_[xs, ys])
    ii, jj = tree.query(pts, predicate="dwithin", distance=r)
    d = shapely.distance(pts[ii], shapely.points(nodes[jj]))
    df = pd.DataFrame({"i": ii, "j": jj, "d": d}).sort_values(["i", "d"]).groupby("i").head(k)
    near = attach(G, xs, ys)
    out = [[n] for n in near]
    for i, grp in df.groupby("i"):
        out[i] = [tuple(nodes[j]) for j in grp.j] or out[i]
    return out


def best_time(tt, cand, H):
    """Fastest time from any reachable candidate node (walk to the nearest road that still connects)."""
    best = np.inf
    for n in cand:
        if H.has_node(n) and H.degree(n) > 0:
            v = tt.get(n, np.inf)
            if v < best:
                best = v
    return best


def times_from(G, sources, weight="t"):
    if not sources:
        return {}
    return nx.multi_source_dijkstra_path_length(G, set(sources), weight=weight)


def main():
    G, e = build_graph()
    sv = gpd.read_file(KD / "osm_services.geojson").cx[BOX[0]:BOX[2], BOX[1]:BOX[3]].to_crs(UTM)
    hosp = sv[sv.amenity.eq("hospital") | sv.healthcare.eq("hospital")]
    school = sv[sv.amenity.eq("school")]
    hosp_n, school_n = attach(G, hosp.geometry.x.values, hosp.geometry.y.values), attach(G, school.geometry.x.values, school.geometry.y.values)
    pop = xr.open_dataarray(PROC / "kampala_ghs_pop.nc").sel(epoch=2020).sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    LO, LA = np.meshgrid(pop.lon.values, pop.lat.values)
    pv = np.nan_to_num(pop.values.ravel())
    keep = pv > 1
    pp = gpd.GeoSeries(gpd.points_from_xy(LO.ravel()[keep], LA.ravel()[keep]), crs=4326).to_crs(UTM)
    pop_n = attach(G, pp.x.values, pp.y.values)
    pop_c = candidates(G, pp.x.values, pp.y.values)
    pw = pv[keep]
    hh = hand_at(LO.ravel()[keep], LA.ravel()[keep])
    base = times_from(G, hosp_n)
    t0 = np.array([best_time(base, c_, G) for c_ in pop_c])
    hand_h = hand_at(*gpd.GeoSeries(gpd.points_from_xy(hosp.geometry.x, hosp.geometry.y), crs=UTM).to_crs(4326).pipe(lambda g: (g.x.values, g.y.values)))
    hand_s = hand_at(*gpd.GeoSeries(gpd.points_from_xy(school.geometry.x, school.geometry.y), crs=UTM).to_crs(4326).pipe(lambda g: (g.x.values, g.y.values)))
    scen = {"water 0.5 m above drains": lambda d: (d.hand < 0.5) & d.near_channel & ~d.bridge,
            "water 1 m above drains": lambda d: (d.hand < 1.0) & d.near_channel & ~d.bridge,
            "water 2 m above drains": lambda d: (d.hand < 2.0) & d.near_channel & ~d.bridge,
            "reported hotspots flood": lambda d: d.near_hotspot & (d.hand < 2.0) & ~d.bridge}
    rows, store = [], {}
    for name, rule in scen.items():
        fl = e[rule(e)]
        H = G.copy()
        H.remove_edges_from(zip(fl.u, fl.v))
        hlev = {"water 0.5 m above drains": 0.5, "water 1 m above drains": 1, "water 2 m above drains": 2}.get(name, 1)
        ok_h = [n for n, h_ in zip(hosp_n, hand_h) if not (h_ < hlev)]
        ok_s = [n for n, h_ in zip(school_n, hand_s) if not (h_ < hlev)]
        tt = times_from(H, ok_h)
        t1 = np.array([best_time(tt, c_, H) for c_ in pop_c])
        wet_home = hh < hlev  # residents whose own cell floods are counted separately
        dry = ~wet_home
        iso = np.isinf(t1) & dry
        delayed = np.isfinite(t1) & (t1 > 2 * t0) & (t1 - t0 > 10) & dry
        far = (t1 > 30) & dry
        rows.append(dict(scenario=name, road_km_flooded=float(fl.assign(L=[G.edges[u, v]["L"] if G.has_edge(u, v) else 0
                                                                          for u, v in zip(fl.u, fl.v)]).L.sum() / 1000),
                         residents_on_flooded_ground=float(pw[wet_home].sum()),
                         residents_cut_off_from_hospitals=float(pw[iso].sum()),
                         residents_delayed_2x=float(pw[delayed].sum()),
                         residents_over_30min=float(pw[far].sum()),
                         residents_over_30min_normal=float(pw[(t0 > 30)].sum()),
                         hospitals_on_flooded_ground=int((hand_h < hlev).sum()), hospitals_total=len(hosp_n),
                         schools_on_flooded_ground=int((hand_s < hlev).sum()), schools_total=len(school_n),
                         median_extra_min=float(np.median((t1 - t0)[np.isfinite(t1) & dry])),
                         p90_extra_min=float(np.percentile((t1 - t0)[np.isfinite(t1) & dry], 90))))
        store[name] = (t1, fl)
        print(rows[-1], flush=True)
    res = pd.DataFrame(rows)
    res.round(1).to_csv(RES / "kd_access_scenarios.csv", index=False)
    crit = critical_links(G, e, hosp_n, pop_c, pw, base)
    figures(G, e, res, store, pp, pw, t0, hosp, crit)


def critical_links(G, e, hosp_n, pop_c, pw, base, top=12):
    """Single-link criticality: flood each low-lying road WAY (OSM way within 300 m of a channel, HAND < 1 m) on its
    own; extra person-minutes to the nearest hospital."""
    cand = e[(e.hand < 1.0) & e.near_channel & ~e.bridge & e.hw.isin(["motorway", "trunk", "primary", "secondary", "tertiary"])]
    ways = cand.groupby("way")
    r = gpd.read_file(KD / "osm_roads.geojson").cx[BOX[0]:BOX[2], BOX[1]:BOX[3]]
    r = r[r.geom_type == "LineString"].reset_index(drop=True)
    t0 = np.array([best_time(base, c_, G) for c_ in pop_c])
    out = []
    for w, grp in ways:
        H = G.copy()
        H.remove_edges_from(zip(grp.u, grp.v))
        tt = times_from(H, hosp_n)
        t1 = np.array([best_time(tt, c_, H) for c_ in pop_c])
        d = np.where(np.isfinite(t1), t1 - t0, 60.0)  # cut-off counted as +60 min
        pm = float((pw * np.clip(d, 0, None)).sum())
        aff = float(pw[d > 5].sum())
        nm_ = r.loc[w, "name"] if isinstance(r.loc[w, "name"], str) else ("A5 at Busega roundabout" if w == 5398 else f"unnamed {r.loc[w, 'highway']}")
        out.append(dict(way=w, name=nm_,
                        highway=r.loc[w, "highway"], person_minutes=pm, residents_delayed_5min=aff,
                        lon=float(r.loc[w].geometry.interpolate(0.5, normalized=True).x),
                        lat=float(r.loc[w].geometry.interpolate(0.5, normalized=True).y)))
    c = pd.DataFrame(out).sort_values("person_minutes", ascending=False).drop_duplicates("name")
    c.round(1).to_csv(RES / "kd_access_critical_links.csv", index=False)
    print(c.head(top).round(0).to_string(), flush=True)
    return c.head(top)


def figures(G, e, res, store, pp, pw, t0, hosp, crit):
    import contextily as ctx
    res = res.set_index("scenario")
    # kd32: scenario bars
    fig, axs = plt.subplots(1, 2, figsize=(14, 4.9), gridspec_kw=dict(wspace=0.5))
    sc = ["water 0.5 m above drains", "water 1 m above drains", "water 2 m above drains", "reported hotspots flood"]
    lab = ["0.5 m", "1 m", "2 m", "hotspots"]
    x = np.arange(len(sc))
    ax = axs[0]
    hom = res.loc[sc, "residents_on_flooded_ground"].values / 1000
    hom[-1] = np.nan  # hotspot scenario floods roads only
    ax.bar(x - 0.27, hom, 0.27, color="#3182bd", label="homes on flooded ground")
    ax.bar(x, res.loc[sc, "residents_delayed_2x"] / 1000, 0.27, color="#fd8d3c", label="trip to hospital doubles (+10 min)")
    ax.bar(x + 0.27, res.loc[sc, "residents_cut_off_from_hospitals"] / 1000, 0.27, color="#b30000", label="no road to any hospital")
    ax.set_xticks(x)
    ax.set_xticklabels(lab)
    ax.set_xlabel("flood scenario (water level above the drains)")
    ax.set_ylabel("residents (thousands)")
    ax.set_title("a  Who a flood cuts off from hospitals", loc="left")
    ax.set_ylim(0, np.nanmax(hom) * 1.45)
    ax.legend(fontsize=8.5, loc="upper left")
    ax = axs[1]
    c = crit.iloc[::-1]
    ax.barh(range(len(c)), c.person_minutes / 1e6, color="#b30000")
    ax.set_yticks(range(len(c)))
    ax.set_yticklabels([str(n)[:34] for n in c.name], fontsize=8.5)
    ax.set_xlabel("extra person-minutes to hospital if this road floods (millions)")
    ax.set_title("b  Most critical flood-prone roads", loc="left")
    save(fig, "kd32_access_scenarios.png", OUT, source=SRC)
    # kd33: map of extra travel time, 1 m scenario
    t1, fl = store["water 1 m above drains"]
    d = np.where(np.isfinite(t1), t1 - t0, 99)
    fig, ax = plt.subplots(figsize=(10, 9))
    flg = gpd.GeoSeries(gpd.points_from_xy(fl.mx, fl.my), crs=UTM)
    ax.scatter(pp.x, pp.y, c=np.clip(d, 0, 30), cmap="YlOrRd", s=3, vmin=0, vmax=30, alpha=0.8)
    flg.plot(ax=ax, color="#08519c", markersize=1.2)
    hosp.plot(ax=ax, marker="P", color="#2ca25f", markersize=55, edgecolor="white", lw=0.6, zorder=5)
    cg = gpd.GeoSeries(gpd.points_from_xy(crit.lon, crit.lat), crs=4326).to_crs(UTM)
    for (xx, yy), n in zip(zip(cg.x, cg.y), crit.name):
        ax.annotate("", (xx, yy))
    cg.plot(ax=ax, marker="o", facecolor="none", edgecolor="black", markersize=110, lw=1.6, zorder=6)
    ctx.add_basemap(ax, crs=f"EPSG:{UTM}", source=ctx.providers.Esri.WorldGrayCanvas, zoom=12, attribution=False)
    ax.set_axis_off()
    sm = plt.cm.ScalarMappable(cmap="YlOrRd", norm=plt.Normalize(0, 30))
    fig.colorbar(sm, ax=ax, shrink=0.55, label="extra minutes to the nearest hospital (30+ incl. cut off)")
    ax.set_title("When the low roads flood (water 1 m above the drains): extra time to hospital\n"
                 "blue: flooded road links · green crosses: hospitals · circles: the 12 most critical roads", loc="left", fontsize=11)
    save(fig, "kd33_access_map.png", OUT, source=SRC + " · basemap: Esri World Gray Canvas")


if __name__ == "__main__":
    main()
