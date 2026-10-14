"""Paper R: Silt, not storms - attributing flood disruption of Kampala's road network.

Four binary factors, full factorial (16 states):
  L  land use      upstream paving 1990 (off) vs 2020 (on): flows scaled by C1990/C2020 (rational method)
  S  maintenance   channels clean (off) vs 30% silted (on): capacity Qcap_clean vs Qcap_silted (kd_hydraulics.py)
  E  encroachment  floodplain open (off) vs blocked by today's buildings (on): each 30 m floodplain cell conveys
                   (1 - building footprint share) of its width in the HAND rating curve
  C  climate       today's design storms (off) vs 2041-70 SSP5-8.5 (on): IDF intensity ratio at each stretch's tc
For each state and return period (2-100 yr): stage per stretch -> depth on every road piece (stage - lowest HAND;
bridges and the post-DEM Entebbe Expressway never flood) -> impassable at >= 0.3 m.
Network (OSM drivable roads, class speeds as Paper 3): impassable pieces removed; population (GHS-POP 2020, 100 m) to
  (a) the city centre (Clock Tower) and (b) the nearest hospital: people cut off; population-weighted extra minutes.
Expected annual values: integral over annual exceedance probability (zero at T = 1).
Attribution: Shapley values of the four factors for (i) today (L, S, E from the 1990/clean/open baseline) and
  (ii) the 2050s (all four).
Crossings: road-channel crossings without a bridge, ranked by annual closure probability (today, silted) x
  population whose fastest route to the centre runs through them.
Outputs: results/kd_roadsR_*.csv, figures kd50-kd52.
"""
import itertools
import math

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import rasterio
import shapely
import xarray as xr

import kd_hydraulics as kh
from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
UTM = 32636
BOX = (32.45, 0.20, 32.72, 0.42)
TS = [2, 5, 10, 25, 50, 100]
IMP = 0.3
FACT = ["L", "S", "E", "C"]
NAMES = dict(L="paving (land use)", S="channel siltation", E="floodplain encroachment", C="climate change")
SPEED = {"motorway": 40, "trunk": 40, "primary": 30, "secondary": 25, "tertiary": 20}
CENTRE = (0.3136, 32.5811)  # Clock Tower / city centre


def floodplain_cells(su):
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand, trh = r.read(2), r.transform
    rows, cols = np.nonzero((hand < 6) & np.isfinite(hand))
    lon, lat = trh.c + trh.a * (cols + 0.5), trh.f + trh.e * (rows + 0.5)
    keep = (lon > BOX[0]) & (lon < BOX[2]) & (lat > BOX[1]) & (lat < BOX[3])
    rows, cols, lon, lat = rows[keep], cols[keep], lon[keep], lat[keep]
    # building footprint share of each 30 m cell (Microsoft footprints, by centroid)
    b = gpd.read_parquet(KD / "ms_buildings.parquet").cx[BOX[0]:BOX[2], BOX[1]:BOX[3]]
    area = b.to_crs(UTM).area.values
    c = b.geometry.centroid
    bc = ((c.x.values - trh.c) / trh.a).astype(int)
    br = ((c.y.values - trh.f) / trh.e).astype(int)
    occ = pd.Series(area).groupby(br * 100000 + bc).sum()
    cellarea = (abs(trh.a) * 111320 * math.cos(math.radians(0.3))) * (abs(trh.e) * 110574)
    bfrac = np.clip(occ.reindex(rows * 100000 + cols).fillna(0).values / cellarea, 0, 1)
    pts = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs=4326).to_crs(UTM).values
    tree = shapely.STRtree(su.geometry.values)
    pi, si = tree.query(pts, predicate="dwithin", distance=200)
    cell = pd.DataFrame({"p": pi, "s": si, "d": shapely.distance(pts[pi], su.geometry.values[si])}) \
        .sort_values("d").drop_duplicates("p")
    cell["h"] = hand[rows[cell.p.values], cols[cell.p.values]]
    cell["b"] = bfrac[cell.p.values]
    print("floodplain cells", len(cell), "mean building share", round(cell.b.mean(), 3), flush=True)
    return {k: (g.h.values, g.b.values) for k, g in cell.groupby("s")}


def stages(s, h, silt=0.3, states=None):
    """Stage above bank [state, stretch, T] for all 16 states (or a subset); silt = share of channel depth lost."""
    su = s.to_crs(UTM)
    groups = floodplain_cells(su)
    hgrid = np.arange(0.05, 6.01, 0.05)
    L = su.length.values
    C1990 = 0.25 + 0.65 * np.clip(2.27 * s.up_built_1990.values, 0, 0.95)
    land = {0: C1990 / h.C.values, 1: np.ones(len(s))}
    fi, f585 = kh.idf_intensity(), kh.idf_intensity("intensity_ssp585_2041_2070")
    clim = {0: np.ones((len(s), len(TS))),
            1: np.stack([f585(T, h.tc_min.values) / fi(T, h.tc_min.values) for T in TS], 1)}
    D = h.D_design.values
    cap = {0: h.Qcap_clean.values, 1: kh.manning_rect(3 * D, (1 - silt) * D, h.S.values, 0.035)}
    Q = np.stack([h[f"Q{T}"].values for T in TS], 1)
    curves = {}  # (S, E) -> list of Qtot arrays per stretch
    for k in range(len(s)):
        hk, bk = groups.get(k, (np.array([]), np.array([])))
        for E in (0, 1):
            wgt = (1 - bk) if E else np.ones_like(hk)
            w = np.array([wgt[hk < x].sum() * 900.0 / max(L[k], 30) for x in hgrid])
            w = np.maximum(w, h.W_design.values[k])
            area = np.cumsum(w * 0.05)
            fp = area * (area / w) ** (2 / 3) * np.sqrt(h.S.values[k]) / 0.06
            for S in (0, 1):
                curves.setdefault((S, E), []).append(cap[S][k] + fp)
    out = {}
    for st in (states or list(itertools.product((0, 1), repeat=4))):
        Lf, Sf, Ef, Cf = st
        q = Q * land[Lf][:, None] * clim[Cf]
        H = np.zeros((len(s), len(TS)))
        cv = curves[(Sf, Ef)]
        for k in range(len(s)):
            over = q[k] > cap[Sf][k]
            if over.any():
                idx = np.minimum(np.searchsorted(cv[k], q[k]), len(hgrid) - 1)
                H[k] = np.where(over, hgrid[idx], 0.0)
        out[st] = H
    print("stages done", flush=True)
    return out


def graph(p):
    key = lambda xy: (round(xy[0]), round(xy[1]))
    G = nx.Graph()
    for i, (g, hw) in enumerate(zip(p.geometry.values, p.highway.values)):
        v = SPEED.get((hw or "").replace("_link", ""), 15) / 3.6
        cs = list(g.coords)
        for a, b in zip(cs[:-1], cs[1:]):  # every vertex, so junctions at shared OSM nodes connect
            u, w = key(a), key(b)
            if u == w:
                continue
            L_ = float(np.hypot(b[0] - a[0], b[1] - a[1]))
            if G.has_edge(u, w) and G[u][w]["t"] <= L_ / v / 60:
                continue
            G.add_edge(u, w, t=L_ / v / 60.0, piece=i)
    big = max(nx.connected_components(G), key=len)
    return G.subgraph(big).copy()


def nodes_near(G, xs, ys):
    nodes = np.array(list(G.nodes))
    tree = shapely.STRtree(shapely.points(nodes))
    return [tuple(nodes[i]) for i in tree.nearest(shapely.points(np.c_[xs, ys]))]


def ea(vals):
    v = np.array([0.0] + list(vals))
    pr = np.array([1.0] + [1 / T for T in TS])
    return float(-np.trapz(v, pr))


def shapley(val, factors):
    n = len(factors)
    phi = {}
    for i, f in enumerate(factors):
        tot = 0.0
        others = [g for g in factors if g != f]
        for r in range(n):
            for sub in itertools.combinations(others, r):
                w = math.factorial(r) * math.factorial(n - r - 1) / math.factorial(n)
                on = set(sub)
                tot += w * (val(on | {f}) - val(on))
        phi[f] = tot
    return phi


def net_setup(p):
    G = graph(p)
    edges = [(u, w, d["piece"]) for u, w, d in G.edges(data=True)]
    epiece = np.array([e[2] for e in edges])
    pop = xr.open_dataarray(PROC / "kampala_ghs_pop.nc").sel(epoch=2020).sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    LO, LA = np.meshgrid(pop.lon.values, pop.lat.values)
    pv = np.nan_to_num(pop.values.ravel())
    keep = pv > 1
    pp = gpd.GeoSeries(gpd.points_from_xy(LO.ravel()[keep], LA.ravel()[keep]), crs=4326).to_crs(UTM)
    pw = pv[keep]
    pn = nodes_near(G, pp.x.values, pp.y.values)
    cxy = gpd.GeoSeries(gpd.points_from_xy([CENTRE[1]], [CENTRE[0]]), crs=4326).to_crs(UTM).iloc[0]
    nodes_arr = np.array(list(G.nodes))
    cset = {tuple(n) for n in nodes_arr[np.hypot(nodes_arr[:, 0] - cxy.x, nodes_arr[:, 1] - cxy.y) <= 1000]}
    sv = gpd.read_file(KD / "osm_services.geojson").cx[BOX[0]:BOX[2], BOX[1]:BOX[3]].to_crs(UTM)
    hosp = sv[sv.amenity.eq("hospital") | sv.healthcare.eq("hospital")]
    hn = set(nodes_near(G, hosp.geometry.x.values, hosp.geometry.y.values))
    base_c = nx.multi_source_dijkstra_path_length(G, cset, weight="t")
    base_h = nx.multi_source_dijkstra_path_length(G, hn, weight="t")
    bc = np.array([base_c.get(n, np.nan) for n in pn])
    bh = np.array([base_h.get(n, np.nan) for n in pn])
    ok = np.isfinite(bc) & np.isfinite(bh)
    print("population on network", round(pw[ok].sum()), flush=True)

    def network(dep):
        """people cut off and pop-weighted extra minutes, to centre and to hospital."""
        flooded = dep[epiece] >= IMP
        Hg = G.copy()
        Hg.remove_edges_from([(e[0], e[1]) for e, f in zip(edges, flooded) if f])
        tc = nx.multi_source_dijkstra_path_length(Hg, cset, weight="t")
        th = nx.multi_source_dijkstra_path_length(Hg, hn, weight="t")
        ac = np.array([tc.get(n, np.inf) for n in pn])
        ah = np.array([th.get(n, np.inf) for n in pn])
        r = {}
        for nm, a, b in (("centre", ac, bc), ("hospital", ah, bh)):
            cut = ok & ~np.isfinite(a)
            reach = ok & np.isfinite(a)
            r[f"cutoff_{nm}"] = float(pw[cut].sum())
            r[f"extra_min_{nm}"] = float((pw[reach] * (a[reach] - b[reach])).sum() / pw[ok].sum())
        return r

    return network, G, pn, pw, ok, cset


def main():
    p = gpd.read_parquet(KD / "road_pieces.parquet").to_crs(UTM).reset_index(drop=True)
    p["len_m"] = p.length
    s = gpd.read_file(KD / "segments.gpkg")
    h = pd.read_parquet(KD / "hydraulics.parquet")
    s = s[s.seg_id.isin(h.seg_id)].set_index("seg_id").loc[h.seg_id].reset_index()
    cache = KD / "roadsR_depth.npz"
    if cache.exists():
        z = np.load(cache)
        depth = {tuple(int(c) for c in k_): z[k_] for k_ in z.files}
    else:
        H = stages(s, h)
        has = (p.stretch >= 0).values & ~p.bridge.values & ~p.raised.values & np.isfinite(p.hand_min.values)
        k = p.stretch.clip(0).values
        depth = {st: np.where(has[:, None], np.clip(Hs[k] - p.hand_min.values[:, None], 0, None) * (Hs[k] > 0), 0)
                 .astype("float32") for st, Hs in H.items()}
        np.savez_compressed(cache, **{"".join(map(str, st)): d for st, d in depth.items()})
    network, G, pn, pw, ok, cset = net_setup(p)
    rows = []
    for st, D in depth.items():
        r = dict(zip(FACT, st))
        km = [p.len_m.values[D[:, j] >= IMP].sum() / 1000 for j in range(len(TS))]
        for j, T in enumerate(TS):
            r[f"km_T{T}"] = km[j]
        r["ea_km"] = ea(km)
        nets = [network(D[:, j]) for j in range(len(TS))]
        for key_ in nets[0]:
            for j, T in enumerate(TS):
                r[f"{key_}_T{T}"] = nets[j][key_]
            r[f"ea_{key_}"] = ea([n_[key_] for n_ in nets])
        rows.append(r)
        print(st, round(r["ea_km"], 1), round(r["ea_cutoff_centre"]), round(r["ea_extra_min_centre"], 2), flush=True)
    sc = pd.DataFrame(rows)
    sc.round(3).to_csv(RES / "kd_roadsR_scenarios.csv", index=False)
    # attribution
    look = {tuple(r[f] for f in FACT): r for r in rows}
    att = []
    for metric in ("ea_km", "ea_cutoff_centre", "ea_extra_min_centre", "ea_cutoff_hospital", "ea_extra_min_hospital"):
        for tag, fs in (("today", ["L", "S", "E"]), ("2050s", FACT)):
            def val(on, metric=metric):
                return look[tuple(1 if f in on else 0 for f in FACT)][metric]
            phi = shapley(val, fs)
            base, end = val(set()), val(set(fs))
            for f, v in phi.items():
                att.append(dict(metric=metric, horizon=tag, factor=NAMES[f], baseline=base, endpoint=end,
                                contribution=v, share_pct=100 * v / (end - base) if end != base else np.nan))
    att = pd.DataFrame(att)
    att.round(3).to_csv(RES / "kd_roadsR_attribution.csv", index=False)
    print(att[att.metric.isin(["ea_km", "ea_extra_min_centre"])].round(2).to_string(), flush=True)
    crossings(p, G, pn, pw, ok, cset, depth)


def crossings(p, G, pn, pw, ok, cset, depth):
    """Rank road-channel crossings without a bridge: annual closure probability x population routed through."""
    G2 = G.copy()
    hub = ("centre",)
    G2.add_edges_from((hub, n, dict(t=0.0, piece=-1)) for n in cset)
    pred, dist = nx.dijkstra_predecessor_and_distance(G2, hub, weight="t")
    G, centre = G2, hub
    load = pd.Series(0.0, index=pd.Index(list(G.nodes), tupleize_cols=False))
    w = pd.Series(pw[ok]).groupby(pd.Index([pn[i] for i in np.flatnonzero(ok)], tupleize_cols=False)).sum()
    load.loc[w.index] += w.values
    order = sorted(dist, key=dist.get, reverse=True)
    through = {}
    for n in order:  # push population up the shortest-path tree toward the centre
        if n == centre or not pred.get(n):
            continue
        par = pred[n][0]
        load[par] += load[n]
        through[G[n][par]["piece"]] = load[n]
    p["pop_through"] = p.index.map(through).fillna(0.0)
    today_silted, today_clean = depth[(1, 1, 1, 0)], depth[(1, 0, 1, 0)]
    first = lambda D: np.array([next((T for j, T in enumerate(TS) if D[i, j] >= IMP), np.nan) for i in range(len(D))])
    cr = p[p.crosses_channel & ~p.bridge & ~p.raised].copy()
    idx = cr.index.values
    cr["T_close_silted"] = first(today_silted[idx])
    cr["T_close_clean"] = first(today_clean[idx])
    cr["p_close_silted"] = 1 / cr.T_close_silted
    cr["p_close_clean"] = (1 / cr.T_close_clean).fillna(0)
    cr["people_x_p_silted"] = cr.p_close_silted.fillna(0) * cr.pop_through
    cr["avoided_by_desilting"] = (cr.p_close_silted.fillna(0) - cr.p_close_clean) * cr.pop_through
    mid = cr.geometry.interpolate(0.5, normalized=True).to_crs(4326)
    cr["lat"], cr["lon"] = mid.y.round(5), mid.x.round(5)
    keep = ["osm_id", "name", "cls", "system", "lat", "lon", "T_close_clean", "T_close_silted", "pop_through",
            "people_x_p_silted", "avoided_by_desilting"]
    cr = cr.sort_values("avoided_by_desilting", ascending=False)
    cr = cr.drop_duplicates(["osm_id", "system"])
    cr[keep].round(3).to_csv(RES / "kd_roadsR_crossings.csv", index=False)
    print(cr[keep].head(20).round(2).to_string(), flush=True)


def sensitivity():
    """Silt share of channel depth lost (10-50%): Shapley shares for today's L, S, E."""
    p = gpd.read_parquet(KD / "road_pieces.parquet").to_crs(UTM).reset_index(drop=True)
    p["len_m"] = p.length
    s = gpd.read_file(KD / "segments.gpkg")
    h = pd.read_parquet(KD / "hydraulics.parquet")
    s = s[s.seg_id.isin(h.seg_id)].set_index("seg_id").loc[h.seg_id].reset_index()
    network, *_ = net_setup(p)
    has = (p.stretch >= 0).values & ~p.bridge.values & ~p.raised.values & np.isfinite(p.hand_min.values)
    k = p.stretch.clip(0).values
    sts = [st for st in itertools.product((0, 1), repeat=4) if st[3] == 0]
    out = []
    for silt in (0.1, 0.2, 0.3, 0.5):
        H = stages(s, h, silt=silt, states=sts)
        look = {}
        for st, Hs in H.items():
            D = np.where(has[:, None], np.clip(Hs[k] - p.hand_min.values[:, None], 0, None) * (Hs[k] > 0), 0)
            km = [p.len_m.values[D[:, j] >= IMP].sum() / 1000 for j in range(len(TS))]
            cut = [network(D[:, j])["cutoff_centre"] for j in range(len(TS))]
            look[st] = dict(ea_km=ea(km), ea_cutoff_centre=ea(cut), km_T2=km[0])
        for metric in ("ea_km", "ea_cutoff_centre"):
            val = lambda on, m=metric: look[tuple(1 if f in on else 0 for f in FACT)][m]
            phi = shapley(val, ["L", "S", "E"])
            tot = val({"L", "S", "E"}) - val(set())
            for f_, v in phi.items():
                out.append(dict(silt_depth_lost=silt, metric=metric, factor=NAMES[f_], share_pct=100 * v / tot,
                                endpoint=val({"L", "S", "E"}), clean_today=val({"L", "E"})))
        print(silt, {m: round(look[(1, 1, 1, 0)][m], 1) for m in ("ea_km", "ea_cutoff_centre", "km_T2")}, flush=True)
    o = pd.DataFrame(out)
    o.round(2).to_csv(RES / "kd_roadsR_sensitivity.csv", index=False)
    print(o.round(1).to_string(), flush=True)


if __name__ == "__main__":
    import sys
    globals()[sys.argv[1] if len(sys.argv) > 1 else "main"]()
