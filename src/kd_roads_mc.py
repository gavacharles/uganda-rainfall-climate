"""Paper R uncertainty: Monte Carlo over the model's assumptions, and a machine-learning emulator to explain them.

Each draw (Latin hypercube, N = 150) re-runs all 16 factorial states (paving, siltation, encroachment, climate) for six
return periods, recomputes road depths and network access to the city centre, and the Shapley shares.
Uncertain parameters (uniform):
  design_T       return period the channels were built for, 1990 flows: 5-25 yr (log-uniform; main run 10)
  n_channel      Manning n of a clean channel: 0.020-0.030 (0.025)
  n_floodplain   floodplain n: 0.04-0.10 (0.06)
  silt_depth     share of channel depth lost when silted: 0.10-0.50 (0.30)
  n_silt         Manning n of a silted, vegetated channel: 0.030-0.045 (0.035)
  k_imperv       GHSL built share -> impervious factor: 1.8-2.7 (2.27)
  c_base         runoff coefficient of unpaved ground: 0.15-0.35 (0.25)
  idf_mult       design-storm intensity error: 0.85-1.15 (1.0)
  clim_mult      size of the SSP5-8.5 change factor: 0.5-1.5 (1.0)
  road_raise     road surface above the 30 m DEM ground: 0-0.3 m (0)
  block_mult     floodplain blocked per unit of footprint share (walls, fill): 1-3 (1)
  threshold      depth that stops cars: 0.2-0.4 m (0.3)
Fast implementation: rating curves vectorised over all stretches; network with scipy csgraph Dijkstra.
ML: gradient-boosting emulator of the siltation share and of the total disruption from the 12 parameters
(5-fold cross-validated R2), with permutation importance -> which assumptions the conclusion depends on.
Outputs: results/kd_roadsR_mc_draws.csv, kd_roadsR_mc_summary.csv, kd_roadsR_mc_importance.csv; figure kd53.
"""
import itertools
import math
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.stats import qmc

import kd_hydraulics as kh
import kd_roads_attrib as ra
from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
TS = ra.TS
FACT = ra.FACT
HGRID = np.arange(0.05, 6.01, 0.05)
PARAMS = dict(design_T=(np.log(5), np.log(25)), n_channel=(0.020, 0.030), n_floodplain=(0.04, 0.10),
              silt_depth=(0.10, 0.50), n_silt=(0.030, 0.045), k_imperv=(1.8, 2.7), c_base=(0.15, 0.35),
              idf_mult=(0.85, 1.15), clim_mult=(0.5, 1.5), road_raise=(0.0, 0.3), block_mult=(1.0, 3.0),
              threshold=(0.2, 0.4))
CENTRAL = dict(design_T=np.log(10), n_channel=0.025, n_floodplain=0.06, silt_depth=0.30, n_silt=0.035, k_imperv=2.27,
               c_base=0.25, idf_mult=1.0, clim_mult=1.0, road_raise=0.0, block_mult=1.0, threshold=0.3)


def setup():
    p = gpd.read_parquet(KD / "road_pieces.parquet").to_crs(ra.UTM).reset_index(drop=True)
    p["len_m"] = p.length
    s = gpd.read_file(KD / "segments.gpkg")
    h = pd.read_parquet(KD / "hydraulics.parquet")
    s = s[s.seg_id.isin(h.seg_id)].set_index("seg_id").loc[h.seg_id].reset_index()
    su = s.to_crs(ra.UTM)
    groups = ra.floodplain_cells(su)
    n = len(s)
    L = np.maximum(su.length.values, 30)
    Ncum = np.zeros((n, len(HGRID)))
    Bcum = np.zeros((n, len(HGRID)))
    for k in range(n):
        hk, bk = groups.get(k, (np.array([]), np.array([])))
        if len(hk):
            idx = np.searchsorted(HGRID, hk, side="right")  # cell counts for every h > HAND
            Ncum[k] = np.cumsum(np.bincount(idx, minlength=len(HGRID) + 1)[:len(HGRID)])
            Bcum[k] = np.cumsum(np.bincount(idx, weights=bk, minlength=len(HGRID) + 1)[:len(HGRID)])
    fi = kh.idf_intensity()
    f585 = kh.idf_intensity("intensity_ssp585_2041_2070")
    tc = h.tc_min.values
    ctx = dict(p=p, s=s, h=h, n=n, L=L, Ncum=Ncum, Bcum=Bcum,
               i_T=np.stack([fi(T, tc) for T in TS], 1),
               clim=np.stack([f585(T, tc) / fi(T, tc) for T in TS], 1),
               i_design=lambda T: fi_interp(fi, T, tc), built1990=s.up_built_1990.values,
               built2020=np.clip((h.C.values - 0.25) / 0.65 / 2.27, 0, 1))
    # road pieces -> stretch
    has = (p.stretch >= 0).values & ~p.bridge.values & ~p.raised.values & np.isfinite(p.hand_min.values)
    ctx.update(has=has, kk=p.stretch.clip(0).values, hand=p.hand_min.values, len_m=p.len_m.values)
    # network (csgraph)
    G = ra.graph(p)
    nodes = list(G.nodes)
    nid = {v: i for i, v in enumerate(nodes)}
    eu, ev, et, ep = [], [], [], []
    for u, w, d in G.edges(data=True):
        eu.append(nid[u]), ev.append(nid[w]), et.append(d["t"]), ep.append(d["piece"])
    ctx.update(eu=np.array(eu), ev=np.array(ev), et=np.array(et), ep=np.array(ep), nn=len(nodes))
    pop = xr.open_dataarray(PROC / "kampala_ghs_pop.nc").sel(epoch=2020).sel(lon=slice(ra.BOX[0], ra.BOX[2]),
                                                                            lat=slice(ra.BOX[1], ra.BOX[3]))
    LO, LA = np.meshgrid(pop.lon.values, pop.lat.values)
    pv = np.nan_to_num(pop.values.ravel())
    keep = pv > 1
    pp = gpd.GeoSeries(gpd.points_from_xy(LO.ravel()[keep], LA.ravel()[keep]), crs=4326).to_crs(ra.UTM)
    pn = np.array([nid[v] for v in ra.nodes_near(G, pp.x.values, pp.y.values)])
    cxy = gpd.GeoSeries(gpd.points_from_xy([ra.CENTRE[1]], [ra.CENTRE[0]]), crs=4326).to_crs(ra.UTM).iloc[0]
    na = np.array(nodes)
    src = np.flatnonzero(np.hypot(na[:, 0] - cxy.x, na[:, 1] - cxy.y) <= 1000)
    ctx.update(pn=pn, pw=pv[keep], src=src)
    base = access(ctx, np.zeros(len(ctx["eu"]), bool))
    ctx["ok"] = np.isfinite(base)
    print("setup done: stretches", n, "edges", len(eu), "population", round(ctx["pw"][ctx["ok"]].sum()), flush=True)
    return ctx


def fi_interp(fi, T, tc):
    """IDF intensity for a non-tabulated return period (log-linear in T between tabulated 2-100 yr)."""
    lo = max(t for t in TS if t <= T)
    hi = min(t for t in TS if t >= T)
    if lo == hi:
        return fi(lo, tc)
    w = (np.log(T) - np.log(lo)) / (np.log(hi) - np.log(lo))
    return np.exp((1 - w) * np.log(fi(lo, tc)) + w * np.log(fi(hi, tc)))


def access(ctx, flooded):
    keep = ~flooded
    u, v, t = ctx["eu"][keep], ctx["ev"][keep], ctx["et"][keep]
    M = csr_matrix((np.r_[t, t], (np.r_[u, v], np.r_[v, u])), shape=(ctx["nn"], ctx["nn"]))
    d = dijkstra(M, directed=False, indices=ctx["src"], min_only=True)
    return d[ctx["pn"]]


def run(ctx, P):
    h, n = ctx["h"], ctx["n"]
    T_design = float(np.exp(P["design_T"]))
    C90 = P["c_base"] + 0.65 * np.clip(P["k_imperv"] * ctx["built1990"], 0, 0.95)
    C20 = P["c_base"] + 0.65 * np.clip(P["k_imperv"] * ctx["built2020"], 0, 0.95)
    C = {0: C90, 1: C20}
    # flows: rational method relative to the stored 2020 flows
    Q20 = np.stack([h[f"Q{T}"].values for T in TS], 1) / h.C.values[:, None] * P["idf_mult"]
    # capacity: channel built for the 1990 design_T-year flow at n = 0.025, then actual n
    q_design = h.Qdesign.values / (0.25 + 0.65 * np.clip(2.27 * ctx["built1990"], 0, 0.95)) * C90 * P["idf_mult"] \
        * ctx["i_design"](T_design) / ctx["i_design"](10)
    cap_clean = q_design * 0.025 / P["n_channel"]
    D, S = h.D_design.values, h.S.values
    ratio = kh.manning_rect(3 * D, (1 - P["silt_depth"]) * D, S, P["n_silt"]) / kh.manning_rect(3 * D, D, S, P["n_channel"])
    cap = {0: cap_clean, 1: cap_clean * ratio}
    curves = {}
    for E in (0, 1):
        w = np.clip(ctx["Ncum"] - (P["block_mult"] * ctx["Bcum"] if E else 0), 0, None) * 900.0 / ctx["L"][:, None]
        w = np.maximum(w, h.W_design.values[:, None])
        A = np.cumsum(w * 0.05, 1)
        curves[E] = A * (A / w) ** (2 / 3) * np.sqrt(S)[:, None] / P["n_floodplain"]
    clim = 1 + (ctx["clim"] - 1) * P["clim_mult"]
    out = {}
    hand = ctx["hand"] + P["road_raise"]
    for st in itertools.product((0, 1), repeat=4):
        Lf, Sf, Ef, Cf = st
        q = Q20 * C[Lf][:, None] * (clim if Cf else 1.0)
        Qtot = cap[Sf][:, None] + curves[Ef]
        km, cut = [], []
        for j in range(len(TS)):
            over = q[:, j] > cap[Sf]
            idx = np.argmax(Qtot >= q[:, j][:, None], axis=1)
            idx = np.where((Qtot >= q[:, j][:, None]).any(1), idx, len(HGRID) - 1)
            stage = np.where(over, HGRID[idx], 0.0)
            sg = stage[ctx["kk"]]
            dep = np.where(ctx["has"] & (sg > 0), np.clip(sg - hand, 0, None), 0)
            imp = dep >= P["threshold"]
            km.append(ctx["len_m"][imp].sum() / 1000)
            a = access(ctx, imp[ctx["ep"]])
            cut.append(float(ctx["pw"][ctx["ok"] & ~np.isfinite(a)].sum()))
        out[st] = dict(ea_km=ra.ea(km), ea_cut=ra.ea(cut), km_T2=km[0], cut_T2=cut[0])
    return out


def shares(out, metric):
    res = {}
    for tag, fs in (("today", ["L", "S", "E"]), ("2050s", FACT)):
        val = lambda on: out[tuple(1 if f in on else 0 for f in FACT)][metric]
        phi = ra.shapley(val, fs)
        tot = val(set(fs)) - val(set())
        for f, v in phi.items():
            res[f"{metric}_{tag}_{f}"] = 100 * v / tot if tot else np.nan
        res[f"{metric}_{tag}_total"] = val(set(fs))
    return res


def main(N=150):
    ctx = setup()
    rows = []
    r0 = run(ctx, CENTRAL)
    rows.append(dict(draw="central", **CENTRAL, **shares(r0, "ea_km"), **shares(r0, "ea_cut"),
                     clean_today_km=r0[(1, 0, 1, 0)]["ea_km"], silted_today_km=r0[(1, 1, 1, 0)]["ea_km"]))
    print("central", {k: round(v, 1) for k, v in rows[0].items() if k.startswith("ea_km_today")}, flush=True)
    lhs = qmc.LatinHypercube(d=len(PARAMS), seed=42).random(N)
    keys = list(PARAMS)
    for i in range(N):
        P = {k: PARAMS[k][0] + lhs[i, j] * (PARAMS[k][1] - PARAMS[k][0]) for j, k in enumerate(keys)}
        r = run(ctx, P)
        rows.append(dict(draw=i, **P, **shares(r, "ea_km"), **shares(r, "ea_cut"),
                         clean_today_km=r[(1, 0, 1, 0)]["ea_km"], silted_today_km=r[(1, 1, 1, 0)]["ea_km"]))
        if i % 10 == 0:
            pd.DataFrame(rows).to_csv(RES / "kd_roadsR_mc_draws.csv", index=False)
            print(i, round(rows[-1]["ea_km_today_S"], 1), round(rows[-1]["ea_cut_today_S"], 1), flush=True)
    d = pd.DataFrame(rows)
    d["design_T"] = np.where(d.draw.astype(str) == "central", d.design_T, d.design_T)
    d.to_csv(RES / "kd_roadsR_mc_draws.csv", index=False)
    analyse()


def analyse():
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.inspection import permutation_importance
    from sklearn.model_selection import KFold, cross_val_predict
    from sklearn.metrics import r2_score
    d = pd.read_csv(RES / "kd_roadsR_mc_draws.csv")
    mc = d[d.draw.astype(str) != "central"].copy()
    mc["design_T_yr"] = np.exp(mc.design_T)
    summ = []
    for col in [c for c in d.columns if c.startswith(("ea_km_", "ea_cut_"))] + ["clean_today_km", "silted_today_km"]:
        v = mc[col].dropna()
        summ.append(dict(quantity=col, central=float(d[d.draw.astype(str) == "central"][col].iloc[0]),
                         median=v.median(), p05=v.quantile(0.05), p95=v.quantile(0.95),
                         share_draws_silt_largest=np.nan))
    s = pd.DataFrame(summ)
    for m in ("ea_km", "ea_cut"):
        largest = (mc[f"{m}_today_S"] > mc[[f"{m}_today_L", f"{m}_today_E"]].max(1)).mean() * 100
        s.loc[s.quantity == f"{m}_today_S", "share_draws_silt_largest"] = largest
    s.round(2).to_csv(RES / "kd_roadsR_mc_summary.csv", index=False)
    print(s.round(1).to_string(), flush=True)
    X = mc[list(PARAMS)].copy()
    X["design_T"] = np.exp(X.design_T)
    imp_rows = []
    for target in ("ea_km_today_S", "ea_cut_today_S", "silted_today_km"):
        y = mc[target].values
        gb = GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=0)
        pred = cross_val_predict(gb, X, y, cv=KFold(5, shuffle=True, random_state=0))
        r2 = r2_score(y, pred)
        gb.fit(X, y)
        pi = permutation_importance(gb, X, y, n_repeats=30, random_state=0)
        for k, m_, sd in zip(X.columns, pi.importances_mean, pi.importances_std):
            imp_rows.append(dict(target=target, parameter=k, importance=m_, sd=sd, emulator_cv_r2=r2))
        print(target, "emulator CV R2", round(r2, 3), flush=True)
    imp = pd.DataFrame(imp_rows)
    imp.round(4).to_csv(RES / "kd_roadsR_mc_importance.csv", index=False)
    print(imp.sort_values(["target", "importance"], ascending=[True, False]).groupby("target").head(5).round(3).to_string())
    figure(mc, imp)


LAB = dict(design_T="design standard (return period)", n_channel="channel roughness", n_floodplain="floodplain roughness",
           silt_depth="silt depth", n_silt="silted-channel roughness", k_imperv="paving calibration",
           c_base="runoff of unpaved ground", idf_mult="design-storm error", clim_mult="climate signal size",
           road_raise="road height above DEM", block_mult="floodplain blocking per building", threshold="depth that stops cars")


def figure(mc, imp):
    import matplotlib.pyplot as plt
    COL = {"L": "#8c6bb1", "S": "#a50026", "E": "#f4a582", "C": "#4393c3"}
    NM = {"L": "paving", "S": "siltation", "E": "encroachment", "C": "climate"}
    fig, axs = plt.subplots(1, 3, figsize=(17, 5.8), gridspec_kw=dict(width_ratios=[1, 1, 1.25], wspace=0.35))
    fig.subplots_adjust(left=0.05, right=0.98, top=0.8, bottom=0.14)
    for ax, (m, lab) in zip(axs[:2], (("ea_km", "a  Road impassable"), ("ea_cut", "b  People cut off from the centre"))):
        data, cols, labs = [], [], []
        for tag in ("today", "2050s"):
            for f in (["S", "L", "E"] if tag == "today" else ["S", "L", "E", "C"]):
                data.append(mc[f"{m}_{tag}_{f}"].dropna().values)
                cols.append(COL[f])
                labs.append(dict(S="silt", L="paving", E="encr.", C="climate")[f])
        bp = ax.boxplot(data, widths=0.6, patch_artist=True, showfliers=False, whis=(5, 95), medianprops=dict(color="white", lw=2))
        for b, c in zip(bp["boxes"], cols):
            b.set_facecolor(c)
            b.set_edgecolor(c)
        ax.set_xticks(range(1, len(labs) + 1))
        ax.set_xticklabels(labs, fontsize=9)
        ax.axvline(3.5, color="#999", lw=1, ls=":")
        ax.text(2, 97, "today", ha="center", fontsize=10.5, fontweight="bold", color="#444")
        ax.text(5.5, 97, "2050s", ha="center", fontsize=10.5, fontweight="bold", color="#444")
        ax.set_ylim(-5, 104)
        ax.set_ylabel("share of the change since 1990 (%)")
        ax.set_title(lab, loc="left", fontsize=11.5)
        ax.spines[["top", "right"]].set_visible(False)
    ax = axs[2]
    q = imp[imp.target == "ea_km_today_S"].sort_values("importance")
    ax.barh([LAB[k] for k in q.parameter], q.importance, xerr=q.sd, color="#a50026", alpha=0.85)
    ax.set_xlabel("importance for the siltation share (permutation, emulator)")
    ax.set_title(f"c  Which assumptions matter (emulator R² = {q.emulator_cv_r2.iloc[0]:.2f})", loc="left", fontsize=11.5)
    ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"Silt, not storms, across {len(mc)} versions of the model", x=0.01, ha="left", fontweight="bold",
                 fontsize=15)
    fig.text(0.01, 0.875, "Monte Carlo over 12 uncertain assumptions (boxes: 25-75%, whiskers: 5-95%); a gradient-boosting "
             "emulator ranks the assumptions by influence. encr. = floodplain encroachment", fontsize=10.5, color="#555")
    save(fig, "kd53_roads_uncertainty.png", OUT,
         source="Monte Carlo (Latin hypercube) of the factorial road-flood model; emulator: scikit-learn gradient boosting "
                "with permutation importance (this study)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "analyse":
        analyse()
    else:
        main(int(sys.argv[1]) if len(sys.argv) > 1 else 150)
