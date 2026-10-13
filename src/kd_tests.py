"""Kampala drainage study, part 13: hypothesis tests for papers A (hold-out), C (waste-culvert chain), D (exposure).

holdout   Does change measured 1975-2000 (upstream paving growth, valley-floor building) predict where valley floors
          were built over next (2000-2020)? Segment-level AUC/Spearman with 2 km block bootstrap.
waste     Are culverts with mapped dumping upstream nearby more often at reported flood hotspots, controlling for
          upstream area, paving and building density? Logistic model + block bootstrap; uncollected-waste load per
          channel system (GHS-POP x 0.55 kg/person/day x 50% uncollected, KCCA).
exposure  People on low ground beside channels 1975-2030: decomposition of growth into city growth (share constant)
          and a shift toward low ground; by channel system.
Outputs results/kd_test_*.csv and figures kd23-kd25.
"""
import sys

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import shapely
import xarray as xr
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
UTM = 32636
SRC = ("Channels, culverts, waste points: © OpenStreetMap contributors · built-up & population: JRC GHSL R2023A · "
       "DEM: Copernicus GLO-30 · hotspots: KCCA/NEMA lists, news & local reports (approx.)")


def blocks(geom, size=2000):
    c = geom.centroid
    return ((c.x // size).astype(int).astype(str) + "_" + (c.y // size).astype(int).astype(str)).values


def boot(y, score, blk, n=500, fn=roc_auc_score, seed=1):
    rng = np.random.default_rng(seed)
    ub = np.unique(blk)
    out = []
    for _ in range(n):
        idx = np.concatenate([np.flatnonzero(blk == b) for b in rng.choice(ub, len(ub))])
        try:
            out.append(fn(y[idx], score[idx]))
        except ValueError:
            pass
    return np.percentile(out, [2.5, 97.5])


# ------------------------------------------------------------------ A: temporal hold-out
def holdout():
    s = gpd.read_file(KD / "segments.gpkg").to_crs(UTM)
    pav = pd.read_csv(RES / "kd_segment_upstream_paving.csv").set_index("seg_id")
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc")
    cell = (abs(float(np.diff(g.lon).mean())) * 111320 * np.cos(np.deg2rad(0.3))) * (abs(float(np.diff(g.lat).mean())) * 111320)
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand = r.read(2)
        tr = r.transform
    from scipy import ndimage
    xs = tr.c + tr.a * (np.arange(hand.shape[1]) + 0.5)
    ys = tr.f + tr.e * (np.arange(hand.shape[0]) + 0.5)
    vf = (hand < 3).astype(float)
    vb = {}
    for e in (1975, 2000, 2020):
        b = np.clip(g.sel(epoch=e).sel(lat=ys, lon=xs, method="nearest").values / cell, 0, 1)
        vb[e] = ndimage.uniform_filter(vf * b, 17) / np.maximum(ndimage.uniform_filter(vf, 17), 1e-6)
    pts = s.to_crs(4326).geometry.interpolate(0.5, normalized=True)
    col = ((pts.x.values - tr.c) / tr.a).astype(int).clip(0, hand.shape[1] - 1)
    row = ((pts.y.values - tr.f) / tr.e).astype(int).clip(0, hand.shape[0] - 1)
    for e in vb:
        s[f"vb{e}"] = vb[e][row, col]
    s = s.join(pav[["up_built_1975", "up_built_1995", "up_built_2005", "up_built_2020"]], on="seg_id", rsuffix="_p")
    m = s[(s.up_km2 >= 0.25)].dropna(subset=["vb1975", "vb2000", "vb2020", "up_built_1975", "up_built_1995"]).copy()
    C = lambda b: 0.25 + 0.65 * b
    m["early_paving_growth"] = (C(m.up_built_1995) / C(m.up_built_1975)) - 1
    m["early_valley_change"] = m.vb2000 - m.vb1975
    m["early_score"] = m.early_paving_growth.rank(pct=True) * 0.5 + m.early_valley_change.rank(pct=True) * 0.5
    m["later_valley_change"] = m.vb2020 - m.vb2000
    room = m.vb2000 < 0.6  # only where there was still unbuilt valley floor in 2000
    m = m[room]
    top = (m.later_valley_change >= m.later_valley_change.quantile(0.75)).astype(int).values
    blk = blocks(m.geometry)
    auc = roc_auc_score(top, m.early_score)
    ci = boot(top, m.early_score.values, blk)
    rho, p = stats.spearmanr(m.early_score, m.later_valley_change)
    # naive alternative: "where it is already most built predicts what is built next"
    auc_naive = roc_auc_score(top, m.vb2000)
    res = dict(n_segments=len(m), auc_early_score=auc, ci_lo=ci[0], ci_hi=ci[1], spearman=rho, p=p,
               auc_already_built_2000=auc_naive)
    pd.DataFrame([res]).round(3).to_csv(RES / "kd_test_holdout.csv", index=False)
    print("HOLD-OUT", {k: round(v, 3) if isinstance(v, float) else v for k, v in res.items()})
    # figure
    fig, ax = plt.subplots(figsize=(8.5, 5))
    q = pd.qcut(m.early_score, 5, labels=["lowest", "2", "3", "4", "highest"])
    v = m.groupby(q, observed=True).later_valley_change.mean() * 100
    ax.bar(range(5), v.values, color=["#fee8c8", "#fdbb84", "#fc8d59", "#e34a33", "#b30000"])
    for i, x in enumerate(v.values):
        ax.text(i, x + 0.2, f"{x:.1f}", ha="center", fontsize=10)
    ax.set_xticks(range(5))
    ax.set_xticklabels([f"{l}" for l in v.index])
    ax.set_xlabel("emerging-risk score from 1975-2000 change (quintile of channel segments)")
    ax.set_ylabel("valley floor newly built over, 2000-2020 (percentage points)")
    ax.set_title(f"Early change predicts later encroachment (AUC {auc:.2f}, 95% CI {ci[0]:.2f}-{ci[1]:.2f})", loc="left")
    save(fig, "kd23_holdout_encroachment.png", OUT, source=SRC)


# ------------------------------------------------------------------ C: waste - culvert - flood chain
def waste():
    s = gpd.read_file(KD / "segments.gpkg").to_crs(UTM)
    cul = gpd.read_file(KD / "osm_waterways.geojson")
    cul = cul[cul.tunnel.isin(["culvert", "yes"])].to_crs(UTM)
    cul["geometry"] = cul.geometry.interpolate(0.5, normalized=True)
    w = gpd.read_file(KD / "osm_waste.geojson").to_crs(UTM)
    w["geometry"] = w.geometry.representative_point()
    hp = pd.read_csv(KD / "flood_hotspots.csv")
    hp = gpd.GeoSeries(gpd.points_from_xy(hp.lon, hp.lat), crs=4326).to_crs(UTM)
    fl = s[s.up_km2 >= 0.25]
    # attach each culvert to its nearest flowing segment
    j = shapely.STRtree(fl.geometry.values).nearest(cul.geometry.values)
    seg = fl.iloc[j].reset_index(drop=True)
    c = cul.reset_index(drop=True)[["geometry"]].join(seg[["seg_id", "up_km2", "up_built_2020", "bldg_reserve", "bldg_floodplain",
                                                         "system"]])
    c = c[c.distance(gpd.GeoSeries(seg.geometry.values, crs=UTM)) <= 30].copy()
    # dumping "upstream nearby": waste points within 250 m of the culvert whose nearest flowing segment has smaller
    # (or equal) upstream area - i.e. on the network above the culvert
    wj = shapely.STRtree(fl.geometry.values).nearest(w.geometry.values)
    w["up"] = fl.up_km2.values[wj]
    ii, jj = shapely.STRtree(w.geometry.values).query(c.geometry.values, predicate="dwithin", distance=250)
    up_ok = w.up.values[jj] <= c.up_km2.values[ii] * 1.01
    c["dump_up"] = np.bincount(ii[up_ok], minlength=len(c))
    c["dump_any"] = np.bincount(ii, minlength=len(c))
    hi, _ = shapely.STRtree(hp.values).query(c.geometry.values, predicate="dwithin", distance=400)
    c["hotspot"] = 0
    c.loc[c.index[np.unique(hi)], "hotspot"] = 1
    c["dumped"] = (c.dump_up > 0).astype(int)
    c = c.dropna(subset=["up_built_2020"])
    blk = blocks(c.geometry)
    X = pd.DataFrame({"dumped": c.dumped, "log_up": np.log(c.up_km2), "paved": c.up_built_2020,
                      "dens": np.log1p(c.bldg_reserve + c.bldg_floodplain)})
    Xs = (X - X.mean()) / X.std()
    lr = LogisticRegression(max_iter=1000).fit(Xs, c.hotspot)
    rng = np.random.default_rng(2)
    ub = np.unique(blk)
    coefs = []
    for _ in range(400):
        idx = np.concatenate([np.flatnonzero(blk == b) for b in rng.choice(ub, len(ub))])
        if c.hotspot.values[idx].sum() < 3:
            continue
        coefs.append(LogisticRegression(max_iter=1000).fit(Xs.values[idx], c.hotspot.values[idx]).coef_[0])
    coefs = np.array(coefs)
    raw = c.groupby("dumped").hotspot.mean()
    res = dict(n_culverts=len(c), n_with_upstream_dumping=int(c.dumped.sum()), hotspot_rate_dumped=raw.get(1, np.nan),
               hotspot_rate_clean=raw.get(0, np.nan),
               **{f"or_per_sd_{k}": float(np.exp(lr.coef_[0][i])) for i, k in enumerate(X.columns)},
               dumped_or_ci_lo=float(np.exp(np.percentile(coefs[:, 0], 2.5))),
               dumped_or_ci_hi=float(np.exp(np.percentile(coefs[:, 0], 97.5))))
    pd.DataFrame([res]).round(3).to_csv(RES / "kd_test_waste_culvert.csv", index=False)
    print("WASTE", {k: round(v, 3) if isinstance(v, float) else v for k, v in res.items()})
    # uncollected waste load per system
    pop = xr.open_dataarray(PROC / "kampala_ghs_pop.nc").sel(epoch=2020)
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        cat = r.read(1)
        tr = r.transform
    PLO, PLA = np.meshgrid(pop.lon.values, pop.lat.values)
    col = ((PLO - tr.c) / tr.a).astype(int).clip(0, cat.shape[1] - 1)
    row = ((PLA - tr.f) / tr.e).astype(int).clip(0, cat.shape[0] - 1)
    cid = cat[row, col]
    names = pd.read_csv(RES / "kampala_catchments.csv").set_index("id")
    rows = []
    for i_, r_ in names.iterrows():
        pp = float(np.nansum(pop.values[cid == i_]))
        rows.append(dict(system=r_["name"] if isinstance(r_["name"], str) else f"catchment {i_}", area_km2=r_.area_km2,
                         population_2020=pp, uncollected_t_per_year=pp * 0.55 * 0.5 * 365 / 1000))
    ld = pd.DataFrame(rows).sort_values("uncollected_t_per_year", ascending=False)
    ld["t_per_km2"] = ld.uncollected_t_per_year / ld.area_km2
    ld.round(1).to_csv(RES / "kd_test_waste_load.csv", index=False)
    print(ld.round(0).to_string())
    # figure
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8))
    rates = [res["hotspot_rate_clean"] * 100, res["hotspot_rate_dumped"] * 100]
    axs[0].bar([0, 1], rates, color=["#9ecae1", "#d95f0e"], width=0.55)
    for i, v in enumerate(rates):
        axs[0].text(i, v + 0.5, f"{v:.0f}%", ha="center", fontsize=11, fontweight="bold")
    axs[0].set_xticks([0, 1])
    axs[0].set_xticklabels([f"no mapped dumping upstream\n(n={len(c) - res['n_with_upstream_dumping']:,})",
                            f"dumping within 250 m upstream\n(n={res['n_with_upstream_dumping']:,})"])
    axs[0].set_ylabel("culverts within 400 m of a reported flood hotspot (%)")
    axs[0].set_ylim(0, max(rates) * 1.18)
    axs[0].set_title(f"Adjusted odds ratio {res['or_per_sd_dumped']:.2f} per SD "
                     f"(95% CI {res['dumped_or_ci_lo']:.2f}-{res['dumped_or_ci_hi']:.2f})", loc="left", fontsize=10)
    top = ld.dropna(subset=["system"]).head(8)
    axs[1].barh(top.system[::-1], top.uncollected_t_per_year[::-1] / 1000, color="#8c6d31")
    axs[1].set_xlabel("estimated uncollected waste, thousand tonnes per year (2020)")
    axs[1].set_title("Waste generated but not collected, by catchment", loc="left", fontsize=10)
    fig.suptitle("The waste - culvert - flood chain", x=0.01, ha="left", fontweight="bold")
    save(fig, "kd24_waste_culvert_chain.png", OUT, source=SRC + " · waste generation 0.55 kg/person/day, ~50% collected "
                                                           "(KCCA estimate)")


# ------------------------------------------------------------------ D: exposure decomposition
def exposure():
    df = pd.read_csv(RES / "kd_population_low_ground.csv").set_index("epoch")
    df["share"] = df.pop_low_ground / df.pop_box
    rows = []
    for a, b in ((1975, 2000), (2000, 2020), (2020, 2030), (1975, 2020)):
        d_total = df.pop_low_ground[b] - df.pop_low_ground[a]
        growth = df.share[a] * (df.pop_box[b] - df.pop_box[a])  # city growth at constant share
        shift = d_total - growth  # toward (or away from) low ground
        rows.append(dict(period=f"{a}-{b}", change=d_total, from_city_growth=growth, from_shift_to_low_ground=shift,
                         share_start=df.share[a] * 100, share_end=df.share[b] * 100))
    out = pd.DataFrame(rows)
    out.round(1).to_csv(RES / "kd_test_exposure_decomposition.csv", index=False)
    print(out.round(1).to_string())
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8))
    axs[0].plot(df.index, df.share * 100, marker="o", color="#d6336c", lw=2.5)
    axs[0].axvspan(2020, 2031, color="#eee", lw=0)
    axs[0].set_ylabel("% of the area's residents living on low ground by channels")
    axs[0].set_title("Share of people in the water's path", loc="left")
    x = np.arange(len(out) - 1)
    o = out.iloc[:3]
    axs[1].bar(x - 0.18, o.from_city_growth / 1000, 0.36, color="#9ecae1", label="city growth (same share)")
    axs[1].bar(x + 0.18, o.from_shift_to_low_ground / 1000, 0.36, color="#d6336c", label="shift toward low ground")
    axs[1].axhline(0, color="#555", lw=0.8)
    axs[1].set_xticks(x)
    axs[1].set_xticklabels(o.period)
    axs[1].set_ylabel("change in people on low ground (thousands)")
    axs[1].legend(fontsize=9, loc="lower left")
    axs[1].set_title("Why exposure grew", loc="left")
    fig.suptitle("Moving into the water's path, 1975-2030 (2025-2030 projected)", x=0.01, ha="left", fontweight="bold")
    save(fig, "kd25_exposure_decomposition.png", OUT,
         source="Population: JRC GHS-POP R2023A · low ground: < 2 m above the nearest drain (Copernicus GLO-30), within 150 m "
                "of a channel (© OpenStreetMap contributors)")


if __name__ == "__main__":
    for st in sys.argv[1:] or ["holdout", "waste", "exposure"]:
        globals()[st]()
