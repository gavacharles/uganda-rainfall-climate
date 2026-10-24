"""Flood x AMR paper 1, step 3: figures and structural sensitivity (reads results/am_stretches.csv; light on memory).

am01 sources and water points; am02 routed source load along the channels; am03 hotspot index; am04 concentration and
rank stability; am05 sampling frame for paper 2; am06 exposure by system and scenario.
Variants (results/am_variants.csv): overlap of the top 10% with the index (a) without treatment works, (b) health
facilities only, (c) sanitation only, (d) exposure counted as buildings, (e) clean channels.
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import LightSource, LogNorm
from matplotlib.lines import Line2D

from common import FIG, PROC, RES, ROOT, save

AM = ROOT / "data" / "kd" / "amr"
OUT = FIG / "kampala_amr"
BOX = (32.45, 0.20, 32.72, 0.42)
SRC = ("Sources: OpenStreetMap (© contributors) health facilities, markets, waste sites, treatment works, abattoir · water "
       "points: WPdx · population: JRC GHS-POP 2020 · terrain and channels: Copernicus GLO-30, Kampala Flood Watch · flood "
       "exposure: Kampala drainage screening model (indicative)")
COL = dict(wastewater="#6a3d9a", hospital="#e31a1c", abattoir="#8c510a", clinic="#fb9a99", market="#ff7f00", waste="#7f7f7f")
W0 = dict(wastewater=50, hospital=10, abattoir=5, clinic=2, market=1, waste=0.5, sanitation=1.0)


def base(ax, B=BOX):
    with rasterio.open(PROC / "kampala_dem.tif") as r:
        win = rasterio.windows.from_bounds(*B, r.transform)
        z = r.read(1, window=win, out_shape=(int(win.height // 2), int(win.width // 2))).astype("float32")
    hs = LightSource(azdeg=315, altdeg=40).hillshade(z, vert_exag=3, dx=60, dy=60)
    g = 0.86 + 0.13 * hs
    ax.imshow(np.dstack([g, g, g * 0.985]), extent=[B[0], B[2], B[1], B[3]], interpolation="bilinear", zorder=0)
    ax.set_xlim(B[0], B[2]); ax.set_ylim(B[1], B[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])


def lines(ax, s, mask=None, **kw):
    g = s if mask is None else s[mask]
    g.plot(ax=ax, **kw)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    from kf_export import segments
    s, h = segments()
    s = s.to_crs(4326)
    d = pd.read_csv(RES / "am_stretches.csv")
    src = gpd.read_file(AM / "sources.gpkg")
    wp = gpd.read_file(AM / "water_points.gpkg")
    n_top = int(np.ceil(0.1 * (d.eae_people > 0).sum()))
    top = set(d.nsmallest(n_top, "rank").seg)

    # variants
    ref = np.median(d.load[d.load > 0])
    def topset(load, e):
        v = load / ref * e
        return set(d.seg.values[np.argsort(-v.values)[:n_top]])
    up = lambda c: d["up_" + c]
    var = {"without treatment works": topset(d.load - W0["wastewater"] * up("wastewater"), d.eae_people),
           "health facilities only": topset(W0["hospital"] * up("hospital") + W0["clinic"] * up("clinic"), d.eae_people),
           "sanitation only": topset(up("sanitation"), d.eae_people),
           "exposure as buildings": topset(d.load, d.eae_buildings),
           "clean channels": topset(d.load, d.eae_people_clean)}
    v = pd.DataFrame([dict(variant=k, overlap_with_main_top10=round(len(top & x) / n_top, 3)) for k, x in var.items()])
    v.to_csv(RES / "am_variants.csv", index=False)
    print(v.to_string(), flush=True)

    # am01 sources
    fig, ax = plt.subplots(figsize=(12, 10.5)); fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.08)
    base(ax)
    lines(ax, s, color="#7fb3d5", lw=0.5, zorder=2)
    w_ = wp.cx[BOX[0]:BOX[2], BOX[1]:BOX[3]]
    ax.scatter(w_.geometry.x, w_.geometry.y, s=5, c="#1f78b4", marker="s", lw=0, alpha=0.6, zorder=3, label=f"water point ({len(w_):,})")
    for c in ("waste", "market", "clinic", "hospital", "abattoir", "wastewater"):
        g = src[src.cls == c].cx[BOX[0]:BOX[2], BOX[1]:BOX[3]]
        ms = {"wastewater": 160, "abattoir": 90, "hospital": 22, "clinic": 9, "market": 26, "waste": 6}[c]
        ax.scatter(g.geometry.x, g.geometry.y, s=ms, c=COL[c], marker="*" if c in ("wastewater", "abattoir") else "o",
                   edgecolor="white" if c in ("wastewater", "abattoir", "hospital") else "none", lw=0.6, zorder=5, label=f"{c} ({len(g):,})")
    for _, r in src[src.cls.isin(["wastewater", "abattoir"])].iterrows():
        ax.annotate(r["name"], (r.geometry.x, r.geometry.y), xytext=(7, 6), textcoords="offset points", fontsize=9.5,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85), zorder=6)
    ax.legend(loc="lower left", fontsize=9.5, framealpha=0.92, title="Mapped in OpenStreetMap / WPdx", title_fontsize=10)
    fig.suptitle("Where resistant bacteria can enter Kampala's channels", x=0.01, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.01, 0.925, "Health facilities, treatment works, the mapped abattoir, markets and waste sites, with the water points people "
             "draw from. On-site sanitation is carried by population (not shown).", fontsize=10.5, color="#555")
    save(fig, "am01_sources.png", OUT, SRC)

    # am02 routed load
    fig, ax = plt.subplots(figsize=(12, 10.5)); fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.08)
    base(ax)
    lv = d.load.values
    norm = LogNorm(max(np.percentile(lv[lv > 0], 5), 1e-3), np.percentile(lv, 99.5))
    s2 = s.assign(load=lv).sort_values("load")
    s2.plot(ax=ax, column="load", cmap="magma_r", norm=norm, linewidth=(0.6 + 2.6 * norm(s2.load.clip(norm.vmin, norm.vmax))), zorder=3)
    sm = plt.cm.ScalarMappable(norm=norm, cmap="magma_r"); cb = fig.colorbar(sm, ax=ax, shrink=0.55, pad=0.01)
    cb.set_label("Routed source load (weighted sources upstream; relative units, log scale)")
    fig.suptitle("Resistance sources accumulate downstream", x=0.01, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.01, 0.925, "Each stretch carries the weighted sum of sources in its catchment: treatment works, hospitals, clinics, the abattoir, "
             "markets, waste sites and on-site sanitation.", fontsize=10.5, color="#555")
    save(fig, "am02_routed_load.png", OUT, SRC)

    # am03 hotspot index
    fig, ax = plt.subplots(figsize=(12, 10.5)); fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.08)
    base(ax)
    lines(ax, s, color="#b8c7d4", lw=0.5, zorder=2)
    iv = d["index"].values
    msk = iv > 0
    nrm = LogNorm(np.percentile(iv[msk], 50), np.percentile(iv[msk], 99.7))
    s3 = s.assign(idx=iv)[msk].sort_values("idx")
    s3.plot(ax=ax, column="idx", cmap="YlOrRd", norm=nrm, linewidth=0.8 + 3 * nrm(s3.idx.clip(nrm.vmin, nrm.vmax)), zorder=3)
    s[d.seg.isin(top).values].plot(ax=ax, color="none", edgecolor="#67000d", lw=0.6, zorder=4)
    sm = plt.cm.ScalarMappable(norm=nrm, cmap="YlOrRd"); cb = fig.colorbar(sm, ax=ax, shrink=0.55, pad=0.01)
    cb.set_label("Hotspot index: routed load x expected annual people in floodwater (log scale)")
    tops = d.nsmallest(n_top, "rank").groupby("system")["index"].sum().sort_values(ascending=False)
    txt = "\n".join(f"{k if k != 'other / outside city catchments' else 'Mayanja and outside the city'}: {100 * v_ / d['index'].sum():.0f}%"
                    for k, v_ in tops.head(5).items())
    ax.text(0.015, 0.02, "Share of the index in the top 10% of stretches\n" + txt, transform=ax.transAxes, fontsize=10, va="bottom",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#ccc", alpha=0.92), zorder=6)
    fig.suptitle("Where floodwater meets resistance sources", x=0.01, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.01, 0.925, f"The {n_top} stretches in the top 10% hold {100 * d.nsmallest(n_top, 'rank')['index'].sum() / d['index'].sum():.0f}% "
             "of the index. Silted channels, 2020 city.", fontsize=10.5, color="#555")
    save(fig, "am03_hotspot_index.png", OUT, SRC)

    # am04 concentration and stability
    fig, axs = plt.subplots(1, 2, figsize=(13, 5)); fig.subplots_adjust(top=0.8, bottom=0.16, wspace=0.28, left=0.07, right=0.98)
    e = d[d.eae_people > 0].sort_values("index", ascending=False)
    cum = e["index"].cumsum() / e["index"].sum()
    axs[0].plot(np.arange(1, len(e) + 1) / len(e) * 100, cum * 100, color="#bd0026", lw=2.2)
    axs[0].axvline(10, color="#999", ls=":"); axs[0].set_xlabel("Stretches with flood exposure, ranked (%)"); axs[0].set_ylabel("Share of the index (%)")
    axs[0].set_title("a  The index is concentrated", loc="left", fontsize=11.5)
    r = e.head(600)
    axs[1].scatter(r["rank"], r.p_top10, s=8, color="#08519c")
    axs[1].axvline(n_top, color="#999", ls=":"); axs[1].set_xlabel("Rank (central weights)"); axs[1].set_ylabel("Share of 1,000 weight draws in the top 10%")
    axs[1].set_title("b  The ranking holds when the weights change", loc="left", fontsize=11.5)
    fig.suptitle("Concentration and robustness of the hotspot index", x=0.01, ha="left", fontweight="bold", fontsize=14)
    save(fig, "am04_concentration_stability.png", OUT, "Weights drawn log-uniformly within their ranges (see methods) · " + SRC)

    # am05 sampling frame
    f = pd.read_csv(RES / "am_sampling_frame.csv")
    fig, ax = plt.subplots(figsize=(12, 10.5)); fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.08)
    base(ax); lines(ax, s, color="#9fb3c8", lw=0.5, zorder=2)
    sty = {"high load, high exposure": ("#b10026", "o"), "high load, low exposure": ("#fd8d3c", "o"), "low load, high exposure": ("#2c7fb8", "o"),
           "low load, low exposure": ("#7fcdbb", "o"), "control, no flooding": ("#333333", "^")}
    for k, (c_, m_) in sty.items():
        g = f[f.stratum == k]
        ax.scatter(g.lon, g.lat, s=110, c=c_, marker=m_, edgecolor="white", lw=1.2, zorder=5, label=f"{k} ({len(g)})")
    for i, rr in f.reset_index(drop=True).iterrows():
        ax.annotate(str(i + 1), (rr.lon, rr.lat), xytext=(6, 5), textcoords="offset points", fontsize=8.5, zorder=6,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    ax.legend(loc="lower left", fontsize=10, framealpha=0.92, title="Stratum (sites at least 1 km apart)", title_fontsize=10)
    fig.suptitle("A sampling frame for measuring resistance after floods", x=0.01, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.01, 0.925, "Thirty channel sites for paper 2: six in each combination of high or low routed load and high or low flood "
             "exposure, and six upland controls.", fontsize=10.5, color="#555")
    save(fig, "am05_sampling_frame.png", OUT, SRC)

    # am06 exposure by scenario and system
    fig, axs = plt.subplots(1, 2, figsize=(13, 5)); fig.subplots_adjust(top=0.8, bottom=0.2, wspace=0.35, left=0.08, right=0.98)
    vals = [d.eae_people.sum(), d.eae_people_clean.sum()]
    axs[0].bar(["Today\n(silted channels)", "Clean channels"], vals, color=["#bd0026", "#41ab5d"])
    for i, x in enumerate(vals):
        axs[0].text(i, x * 1.02, f"{x:,.0f}", ha="center", fontsize=11, fontweight="bold")
    axs[0].set_ylabel("People in floodwater, expected per year"); axs[0].set_ylim(0, max(vals) * 1.18)
    axs[0].set_title("a  Desilting halves exposure", loc="left", fontsize=11.5)
    sy = d.groupby("system")["index"].sum().sort_values(ascending=True)
    sy.index = [x if x != "other / outside city catchments" else "Mayanja and outside" for x in sy.index]
    axs[1].barh(sy.index, sy.values / sy.sum() * 100, color="#fc4e2a")
    axs[1].set_xlabel("Share of the hotspot index (%)"); axs[1].set_title("b  Lubigi dominates", loc="left", fontsize=11.5)
    fig.suptitle("Exposure to floodwater from resistance sources", x=0.01, ha="left", fontweight="bold", fontsize=14)
    save(fig, "am06_scenarios_systems.png", OUT, SRC)


if __name__ == "__main__":
    main()
