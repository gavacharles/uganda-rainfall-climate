"""Figures for Paper R (Silt, not storms):

kd50  attribution: from the 1990 baseline to today (silted) and the 2050s, Shapley contributions of paving,
      siltation, encroachment and climate to impassable road-km and to people cut off from the city centre; and the
      ordinary 2-year storm with clean vs silted channels
kd51  the crossings to desilt first: road-channel crossings ranked by the closures desilting avoids
kd52  sensitivity: siltation's share vs the share of channel depth lost (10-50%)
"""
import sys

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIG, PROC, RES, ROOT, save
from kd_roads_maps import extent, frame, relief, scalebar

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
UTM = 32636
COL = {"paving (land use)": "#8c6bb1", "channel siltation": "#a50026", "floodplain encroachment": "#f4a582",
       "climate change": "#4393c3"}
SRC = ("Roads: © OpenStreetMap contributors · terrain: Copernicus GLO-30 · built-up and population: JRC GHSL R2023A · "
       "buildings: Microsoft · storms: gauge-corrected CHIRPS IDF, CMIP6 SSP5-8.5 2041-70 · method: factorial "
       "scenarios with Shapley attribution (this study)")


def kd50():
    a = pd.read_csv(RES / "kd_roadsR_attribution.csv")
    sc = pd.read_csv(RES / "kd_roadsR_scenarios.csv")
    fig, axs = plt.subplots(1, 3, figsize=(17, 6.2), gridspec_kw=dict(width_ratios=[1.15, 1.15, 0.9], wspace=0.42))
    fig.subplots_adjust(left=0.06, right=0.98, top=0.8, bottom=0.2)
    for ax, (metric, lab, scale, unit) in zip(axs[:2], (("ea_km", "a  Road impassable in an average year", 1, "km"),
                                                        ("ea_cutoff_centre", "b  People cut off from the centre, average year",
                                                         1000, "thousand people"))):
        for row, hz in enumerate(("today", "2050s")):
            d = a[(a.metric == metric) & (a.horizon == hz)].set_index("factor")
            left = d.baseline.iloc[0] / scale
            ax.barh(row, left, color="#bbbbbb", height=0.55)
            for f in ["channel siltation", "paving (land use)", "floodplain encroachment", "climate change"]:
                if f in d.index:
                    v = d.loc[f, "contribution"] / scale
                    ax.barh(row, v, left=left, color=COL[f], height=0.55, edgecolor="white", lw=1)
                    if d.loc[f, "share_pct"] >= 8:
                        ax.text(left + v / 2, row, f"{d.loc[f, 'share_pct']:.0f}%", ha="center", va="center",
                                color="white", fontsize=10.5, fontweight="bold")
                    left += v
            ax.text(left * 1.02, row, f"{left:,.0f}", va="center", fontsize=11, fontweight="bold")
        ax.set_yticks([0, 1])
        ax.set_yticklabels(["today\n(channels silted)", "2050s\n(+ climate)"], fontsize=10.5)
        ax.invert_yaxis()
        ax.set_xlabel(unit)
        ax.set_xlim(0, left * 1.18)
        ax.set_title(lab, loc="left", fontsize=11.5)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", visible=False)
    # 2-year storm
    ax = axs[2]
    cl = sc[(sc.L == 1) & (sc.S == 0) & (sc.E == 1) & (sc.C == 0)].iloc[0]
    si = sc[(sc.L == 1) & (sc.S == 1) & (sc.E == 1) & (sc.C == 0)].iloc[0]
    x = np.arange(2)
    ax.bar(x - 0.2, [cl.km_T2, si.km_T2], 0.38, color="#f4a582", label="road under water (km)")
    ax2_vals = [cl.cutoff_centre_T2 / 1000, si.cutoff_centre_T2 / 1000]
    ax.bar(x + 0.2, ax2_vals, 0.38, color="#a50026", label="people cut off (thousands)")
    for i in range(2):
        ax.text(i - 0.2, [cl.km_T2, si.km_T2][i] + 4, f"{[cl.km_T2, si.km_T2][i]:,.0f}", ha="center", fontsize=10.5)
        ax.text(i + 0.2, ax2_vals[i] + 4, f"{ax2_vals[i]:,.0f}k", ha="center", fontsize=10.5)
    ax.set_xticks(x)
    ax.set_xticklabels(["channels clean", "channels silted"], fontsize=10.5)
    ax.set_ylim(0, max(si.km_T2, si.cutoff_centre_T2 / 1000) * 1.22)
    ax.set_yticks([])
    ax.legend(fontsize=9.5, loc="upper left", frameon=False)
    ax.set_title("c  An ordinary 2-year storm, today", loc="left", fontsize=11.5)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(False)
    from matplotlib.patches import Patch
    hand = [Patch(color="#bbbbbb", label="1990 baseline")] + [Patch(color=c, label=f) for f, c in COL.items()]
    fig.legend(handles=hand, loc="lower left", ncol=5, fontsize=10, frameon=False, bbox_to_anchor=(0.06, 0.03))
    fig.suptitle("Silt, not storms: what puts Kampala's roads under water", x=0.01, ha="left", fontweight="bold",
                 fontsize=16)
    fig.text(0.01, 0.885, "Contributions (Shapley values) of four changes since 1990 to road flooding and to people cut "
             "off, from 16 combined scenarios", fontsize=11, color="#555")
    save(fig, "kd50_roads_attribution.png", OUT, source=SRC)


def kd51():
    from kd_roads_maps import load
    p, s = load()
    c = pd.read_csv(RES / "kd_roadsR_crossings.csv")
    c["label"] = c.name.fillna("unnamed " + c.cls)
    top = c.sort_values("avoided_by_desilting", ascending=False)
    top = top[top.avoided_by_desilting > 0].drop_duplicates("label").head(12).reset_index(drop=True)
    g = gpd.GeoSeries(gpd.points_from_xy(top.lon, top.lat), crs=4326).to_crs(UTM)
    allc = c[c.avoided_by_desilting > 0]
    ga = gpd.GeoSeries(gpd.points_from_xy(allc.lon, allc.lat), crs=4326).to_crs(UTM)
    x0, x1, y0, y1 = extent()
    fig = plt.figure(figsize=(17, 10.5))
    ax = fig.add_axes([0.005, 0.08, 0.64, 0.82])
    relief(ax, x0, x1, y0, y1, alpha=0.3)
    s[s.up_km2 >= 2].plot(ax=ax, color="#3d8fd1", lw=0.7, zorder=2)
    p[p.cls.isin(["highway", "main road", "local through road"])].plot(ax=ax, color="#8a817a", lw=0.6, zorder=3)
    sz = lambda v: 15 + 600 * (v / allc.avoided_by_desilting.max())
    ax.scatter(ga.x, ga.y, s=sz(allc.avoided_by_desilting.values), color="#f4a582", edgecolor="#7f2704", lw=0.4,
               alpha=0.7, zorder=4)
    ax.scatter(g.x, g.y, s=sz(top.avoided_by_desilting.values), color="#a50026", edgecolor="white", lw=1.2, zorder=5)
    from matplotlib import patheffects as pe
    placed = []
    dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1), (1.6, 0), (-1.6, 0), (0, 1.6), (0, -1.6)]
    for i, (x, y) in enumerate(zip(g.x, g.y)):
        best = None
        for rad in (700, 1100, 1500, 1900):
            for dx, dy in dirs:
                lx, ly = x + dx * rad, y + dy * rad
                if all(np.hypot(lx - px, ly - py) > 650 for px, py in placed) and \
                        all(np.hypot(lx - qx, ly - qy) > 350 for qx, qy in zip(g.x, g.y)):
                    best = (lx, ly)
                    break
            if best:
                break
        lx, ly = best or (x + 500, y + 500)
        placed.append((lx, ly))
        ax.plot([x, lx], [y, ly], color="#333", lw=0.7, zorder=5)
        ax.text(lx, ly, str(i + 1), fontsize=10, fontweight="bold", zorder=6, ha="center", va="center",
                path_effects=[pe.withStroke(linewidth=3, foreground="white")])
    frame(ax, x0, x1, y0, y1)
    scalebar(ax, x0 + 1500, y0 + 1200)
    ax.set_title("Road-channel crossings without a bridge, sized by the closures desilting would avoid", loc="left",
                 fontsize=12)
    tx = fig.add_axes([0.66, 0.08, 0.33, 0.82])
    tx.axis("off")
    tx.text(0, 1.0, "The crossings to clear first", fontsize=13, fontweight="bold", va="top")
    tx.text(0, 0.955, "closes every … years: silted → clean · people routed through", fontsize=9.5, color="#555", va="top")
    for i, r in top.iterrows():
        y = 0.9 - i * 0.068
        tc = "never in 100 yr" if np.isnan(r.T_close_clean) else f"{r.T_close_clean:.0f}"
        tx.text(0, y, f"{i + 1}", fontsize=11, fontweight="bold", color="#a50026", va="top")
        tx.text(0.06, y, f"{r.label} ({'minor catchment' if r.system.startswith('other') else r.system})", fontsize=10.5, va="top")
        tx.text(0.06, y - 0.03, f"every {r.T_close_silted:.0f} yr → {tc}  ·  {r.pop_through / 1000:,.0f}k people",
                fontsize=9.5, color="#555", va="top")
    fig.suptitle("Kampala: the culverts that keep the city moving", x=0.005, ha="left", fontweight="bold", fontsize=16)
    save(fig, "kd51_roads_crossings_priority.png", OUT, source=SRC)


def kd52():
    o = pd.read_csv(RES / "kd_roadsR_sensitivity.csv")
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.4), gridspec_kw=dict(wspace=0.28))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.8, bottom=0.2)
    for ax, (m, lab) in zip(axs, (("ea_km", "a  Road impassable (average year)"),
                                  ("ea_cutoff_centre", "b  People cut off from the centre (average year)"))):
        d = o[o.metric == m]
        for f in ["channel siltation", "paving (land use)", "floodplain encroachment"]:
            q = d[d.factor == f]
            ax.plot(100 * q.silt_depth_lost, q.share_pct, "-o", color=COL[f], lw=2.2, label=f)
        ax.set_xlabel("channel depth lost to silt and vegetation (%)")
        ax.set_ylabel("share of the change since 1990 (%)")
        ax.set_ylim(0, 100)
        ax.set_xticks([10, 20, 30, 50])
        ax.axvline(30, color="#999", ls=":", lw=1)
        ax.set_title(lab, loc="left", fontsize=11.5)
        ax.spines[["top", "right"]].set_visible(False)
    axs[0].legend(fontsize=10, frameon=False, loc="center right")
    fig.suptitle("How much silt does it take? Attribution across siltation levels", x=0.01, ha="left",
                 fontweight="bold", fontsize=15)
    fig.text(0.01, 0.875, "Dotted line: the 30% used in the main results", fontsize=10.5, color="#555")
    save(fig, "kd52_roads_silt_sensitivity.png", OUT, source=SRC)




def kd54():
    """Validation: distance from reported road floods to modelled impassable main road vs random road locations."""
    import geopandas as gpd
    import shapely
    import kd_roads_attrib as ra
    p = gpd.read_parquet(KD / "road_pieces.parquet").to_crs(UTM).reset_index(drop=True)
    z = np.load(KD / "roadsR_depth.npz")
    v = pd.read_csv(RES / "kd_roadsR_validation_spots.csv")
    v = v[v.geocoded]
    main = p.cls.isin(["highway", "main road", "local through road"]).values & ~p.raised.values
    mid = p.geometry.interpolate(0.5, normalized=True).values
    rnd = mid[np.random.default_rng(0).choice(np.flatnonzero(main), 5000, replace=False)]
    pts = gpd.GeoSeries(gpd.points_from_xy(v.lon, v.lat), crs=4326).to_crs(UTM).values
    pr = pd.read_csv(RES / "kd_roadsR_validation_proximity.csv")
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.6), gridspec_kw=dict(wspace=0.25))
    fig.subplots_adjust(left=0.07, right=0.98, top=0.8, bottom=0.14)
    for ax, (tag, key, ttl) in zip(axs, (("clean", "1010", "a  Channels clean"), ("silted", "1110", "b  Channels silted"))):
        fl = main & (z[key][:, ra.TS.index(10)] >= 0.3)
        tree = shapely.STRtree(mid[fl])
        ds = np.sort(shapely.distance(pts, mid[fl][tree.nearest(pts)]))
        dr = np.sort(shapely.distance(rnd, mid[fl][tree.nearest(rnd)]))
        ax.plot(dr / 1000, np.arange(1, len(dr) + 1) / len(dr), color="#999", lw=2.2, label="random road locations")
        ax.step(ds / 1000, np.arange(1, len(ds) + 1) / len(ds), where="post", color="#a50026", lw=2.6,
                label=f"reported road floods (n = {len(ds)})")
        auc = pr[(pr.state == tag) & (pr["T"] == 10)].auc_proximity.iloc[0]
        ax.set_xlim(0, 3)
        ax.set_ylim(0, 1.02)
        ax.axvline(0.5, color="#ccc", ls=":", lw=1)
        ax.set_xlabel("distance to the nearest modelled impassable main road, 10-year storm (km)")
        ax.set_ylabel("share of locations")
        ax.set_title(f"{ttl}  ·  AUC = {auc:.2f}", loc="left", fontsize=11.5)
        ax.legend(fontsize=9.5, loc="lower right", frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Does the model put floods where people report them?", x=0.01, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.01, 0.875, "Flood-prone roads from KCCA's 2021 risk assessment, the Observer and the flood catalogue, "
             "against 5,000 random points on main roads", fontsize=10.5, color="#555")
    save(fig, "kd54_roads_validation.png", OUT,
         source="Reported roads: KCCA 2021 risk assessment (via Daily Monitor), The Observer, flood catalogue D0; "
                "geocoding: OpenStreetMap Nominatim · model: this study")


def kd55():
    """Valley floors today at 10 m (Sentinel-2) and the agreement of three methods."""
    import rasterio
    import xarray as xr
    from matplotlib.colors import ListedColormap
    from kd_roads_maps import extent, frame, relief, scalebar
    from rasterio.warp import Resampling, reproject
    nd = xr.open_dataarray(KD / "s2_ndvi_2024_2026_median.nc")
    x0, x1, y0, y1 = extent()
    H, W = nd.shape
    tr = rasterio.transform.from_origin(float(nd.x[0]) - 5, float(nd.y[0]) + 5, 10, 10)
    hand = np.zeros((H, W), "float32")
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        reproject(r.read(2).astype("float32"), hand, src_transform=r.transform, src_crs=r.crs, dst_transform=tr,
                  dst_crs="EPSG:32636", resampling=Resampling.nearest)
    wc = np.zeros((H, W), "uint8")
    with rasterio.open(PROC / "kampala_worldcover.tif") as r:
        reproject(r.read(1), wc, src_transform=r.transform, src_crs=r.crs, dst_transform=tr, dst_crs="EPSG:32636",
                  resampling=Resampling.nearest)
    v = nd.values
    vf = (hand < 3) & np.isfinite(v) & (v > 0) & (wc != 80)  # open water (incl. algae-rich bay) excluded
    cls = np.where(vf, np.where(v > 0.45, 1, 0), np.nan)
    c = pd.read_csv(RES / "kd_valley_s2_check.csv")
    fig = plt.figure(figsize=(17, 8.6))
    ax = fig.add_axes([0.005, 0.1, 0.6, 0.78])
    relief(ax, x0, x1, y0, y1, alpha=0.3)
    ext = [float(nd.x.min()) - 5, float(nd.x.max()) + 5, float(nd.y.min()) - 5, float(nd.y.max()) + 5]
    ax.imshow(cls, cmap=ListedColormap(["#d6604d", "#1b7837"]), vmin=0, vmax=1, extent=ext, interpolation="nearest",
              zorder=3)
    frame(ax, x0, x1, y0, y1)
    scalebar(ax, x0 + 1500, y0 + 1200)
    ax.set_title("a  Valley floors (< 3 m above the drains) today: green or not, 10 m", loc="left", fontsize=12)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color="#1b7837", label="green (NDVI > 0.45)"), Patch(color="#d6604d", label="built, bare or paved")],
              loc="lower right", fontsize=10, frameon=True)
    bx = fig.add_axes([0.66, 0.16, 0.32, 0.7])
    order = ["Kansanga", "Walufumbe", "Nakivubo", "Lubigi", "Kinawataka", "Nalukolongo"]
    d = c.set_index("region").loc[order]
    y = np.arange(len(order))
    bx.barh(y - 0.27, d.s2_vegetated_pct, 0.26, color="#1b7837", label="Sentinel-2 10 m, 2024–26")
    bx.barh(y, d.landsat_2025_pct, 0.26, color="#7fbc41", label="Landsat 30 m, 2025")
    bx.barh(y + 0.27, d.ml_2025_natural_pct, 0.26, color="#c2a5cf", label="machine learning: wetland + trees only")
    bx.set_yticks(y)
    bx.set_yticklabels(order, fontsize=11)
    bx.invert_yaxis()
    bx.set_xlim(0, 75)
    bx.set_xlabel("valley floor still green (%)")
    bx.legend(fontsize=9.5, loc="lower right", frameon=False)
    bx.set_title("b  Three methods, one picture", loc="left", fontsize=12)
    bx.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Kampala's valley floors today, seen at 10 m", x=0.005, ha="left", fontweight="bold", fontsize=16)
    save(fig, "kd55_valley_vegetation_10m.png", OUT,
         source="Imagery: Copernicus Sentinel-2 L2A (ESA), dry-season medians 2024–26; NASA/USGS Landsat; terrain: "
                "Copernicus GLO-30 · machine-learning land cover: this study")


if __name__ == "__main__":
    for f in sys.argv[1:] or ["kd50", "kd51", "kd52"]:
        globals()[f]()
