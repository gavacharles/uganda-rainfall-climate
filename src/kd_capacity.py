"""Paper 6: design-basis drift - how far Kampala's channels have fallen behind the flows they now receive.

Uses data/kd/hydraulics.parquet (kd_hydraulics.py). Each channel stretch is assumed sized to carry the 10-year
storm under 1990 land cover (rectangular, width 3 x depth, n = 0.025). Overload ratio = design-storm peak flow under a
scenario / that capacity. Scenarios: 2020 land; 2020 + 30% siltation; 2030 land; 2030 land + 2041-70 rainfall
(SSP2-4.5, SSP5-8.5; CMIP6 Clausius-Clapeyron uplift). Validation: overload vs reported flood hotspots (AUC,
2 km block bootstrap). Outputs: results/kd_cap_*.csv, figures kd37-kd38.
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import contextily as ctx
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap
from sklearn.metrics import roc_auc_score

from common import FIG, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
SRC = ("Design storms: gauge-corrected CHIRPS IDF with CMIP6 uplift (this study) · paving: JRC GHSL R2023A · terrain: "
       "Copernicus GLO-30 DEM · channels: © OpenStreetMap contributors · basemap: Esri World Gray Canvas")
SYSTEMS = ["Lubigi", "Nakivubo", "Kinawataka", "Kansanga", "Nalukolongo", "Walufumbe"]


def main():
    h = pd.read_parquet(KD / "hydraulics.parquet")
    s = gpd.read_file(KD / "segments.gpkg").to_crs(32636)
    s = s.merge(h, on="seg_id")
    s["km"] = s.length_m / 1000
    sc = {"ratio_2020": "2020 land", "ratio_2020_silted": "2020 + silted", "ratio_2030land": "2030 land",
          "ratio_2050_245": "2030 land + 2041-70 SSP2-4.5", "ratio_2050_585": "2030 land + 2041-70 SSP5-8.5"}
    rows = []
    for c, lab in sc.items():
        for sys_ in SYSTEMS + ["all"]:
            m = s.system.eq(sys_) if sys_ != "all" else np.ones(len(s), bool)
            r = s[m]
            rows.append(dict(scenario=lab, system=sys_, km=r.km.sum(), median_ratio=r[c].median(),
                             km_over_1_2=r.km[r[c] > 1.2].sum(), km_over_1_5=r.km[r[c] > 1.5].sum(),
                             pct_km_over_1_2=100 * r.km[r[c] > 1.2].sum() / max(r.km.sum(), 1e-9)))
    tab = pd.DataFrame(rows)
    tab.round(2).to_csv(RES / "kd_cap_by_system.csv", index=False)
    print(tab[tab.system == "all"].round(2).to_string())
    print(tab[tab.scenario == "2020 land"].round(2).to_string())
    # what the channel can carry now (clean)
    capT = s.groupby("capT_clean").km.sum()
    print("km by return period carried today (clean):", capT.round(1).to_dict())
    # validation against hotspots
    blk = ((s.geometry.centroid.x // 2000).astype(int).astype(str) + "_" + (s.geometry.centroid.y // 2000).astype(int).astype(str)).values
    y = s.hotspot.values
    auc = {c: roc_auc_score(y, s[c]) for c in ("ratio_2020", "risk_pct")}
    rng = np.random.default_rng(3)
    ub = np.unique(blk)
    boot = []
    for _ in range(400):
        idx = np.concatenate([np.flatnonzero(blk == b) for b in rng.choice(ub, len(ub))])
        if 0 < y[idx].sum() < len(idx):
            boot.append(roc_auc_score(y[idx], s.ratio_2020.values[idx]))
    val = dict(auc_overload=auc["ratio_2020"], ci_lo=np.percentile(boot, 2.5), ci_hi=np.percentile(boot, 97.5),
               auc_priority_index=auc["risk_pct"])
    pd.DataFrame([val]).round(3).to_csv(RES / "kd_cap_validation.csv", index=False)
    print("validation", {k: round(v, 3) for k, v in val.items()})
    top = s.sort_values("ratio_2020", ascending=False)
    top = top[top.up_km2 >= 2].drop_duplicates("name").head(15)[["name", "system", "up_km2", "Qdesign", "Q10", "ratio_2020", "ratio_2050_585"]]
    top.round(2).to_csv(RES / "kd_cap_top_overloaded.csv", index=False)
    print(top.round(2).to_string())
    figures(s, tab)


def figures(s, tab):
    # kd37: distribution of overload by scenario + km over 1.2 by system
    fig, axs = plt.subplots(1, 2, figsize=(14.5, 5), gridspec_kw=dict(wspace=0.32))
    ax = axs[0]
    cols = ["ratio_2020", "ratio_2030land", "ratio_2050_245", "ratio_2050_585", "ratio_2020_silted"]
    labs = ["2020\nland", "2030\nland", "+2041-70\nSSP2-4.5", "+2041-70\nSSP5-8.5", "2020 +\nsilted"]
    bp = ax.boxplot([s[c] for c in cols], labels=labs, showfliers=False, patch_artist=True, widths=0.55)
    for b, c in zip(bp["boxes"], ["#fdd0a2", "#fdae6b", "#f16913", "#a63603", "#6a51a3"]):
        b.set_facecolor(c)
    ax.axhline(1, color="#333", lw=1.2, ls="--")
    ax.text(5.45, 1.02, "design capacity", fontsize=8.5, ha="right", va="bottom")
    ax.set_ylabel("10-year peak flow ÷ channel capacity")
    ax.set_title("a  How far channels have fallen behind their design flow", loc="left", fontsize=11)
    ax = axs[1]
    t = tab[tab.system.isin(SYSTEMS)].pivot(index="system", columns="scenario", values="pct_km_over_1_2").reindex(SYSTEMS[::-1])
    order = ["2020 land", "2030 land", "2030 land + 2041-70 SSP5-8.5"]
    yy = np.arange(len(t))
    for i, (c, col) in enumerate(zip(order, ["#fdae6b", "#f16913", "#a63603"])):
        ax.barh(yy + (i - 1) * 0.27, t[c], 0.27, color=col, label=c)
    ax.set_yticks(yy)
    ax.set_yticklabels(t.index)
    ax.set_xlim(0, 105)
    ax.set_xlabel("% of channel length overloaded by more than 20%")
    ax.set_title("b  Overloaded channel length, by system", loc="left", fontsize=11)
    ax.legend(fontsize=8.5, loc="upper center", bbox_to_anchor=(0.45, -0.13), ncol=3, frameon=False)
    save(fig, "kd37_design_drift.png", OUT, source=SRC)
    # kd38 map
    fig, ax = plt.subplots(figsize=(10, 9))
    cm = LinearSegmentedColormap.from_list("ov", ["#2c7bb6", "#ffffbf", "#fdae61", "#d7191c", "#67001f"])
    bounds = [0.5, 0.9, 1.1, 1.3, 1.6, 2.5]
    ss = s.sort_values("ratio_2020")
    ss.plot(ax=ax, column="ratio_2020", cmap=cm, norm=BoundaryNorm(bounds, cm.N), lw=np.where(ss.up_km2 >= 2, 2.0, 0.8))
    ctx.add_basemap(ax, crs="EPSG:32636", source=ctx.providers.Esri.WorldGrayCanvas, zoom=12, attribution=False)
    ax.set_axis_off()
    sm = plt.cm.ScalarMappable(cmap=cm, norm=BoundaryNorm(bounds, cm.N))
    fig.colorbar(sm, ax=ax, shrink=0.55, label="2020 10-year flow ÷ capacity sized for 1990 land cover")
    ax.set_title("Kampala channels sized for 1990 now carry more than they were built for", loc="left", fontsize=12)
    save(fig, "kd38_overload_map.png", OUT, source=SRC)


if __name__ == "__main__":
    main()
