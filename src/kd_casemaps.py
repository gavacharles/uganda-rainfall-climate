"""Case-study maps and supporting figures for the five Kampala papers and the data paper.

cm0  P0  where Kampala's reported floods happened (catalogue places by grade, KCCA/NEMA hotspot list)
cm1  P1  study area: six channel systems, channels, 45 reported hotspots, KCCA boundary, Makerere gauge
cm2  P2  valley floors today (machine-learning land cover), bay-draining catchments, Murchison Bay zones, Ggaba intake
cm3  P3  people on low ground in 2020, inner valleys vs the fringe beyond the KCCA boundary
cm4  P4  road network, 636 bridge-less channel crossings, hospitals, city centre, validation spots
cm5  P5  Uganda's six cities, with each city's valley floors and roads on low ground at the same scale
fw1  P1  study design: two explanations and the tests applied to each
fw4  P4  factorial attribution design: four switches, 16 scenarios, model chain, Shapley values
lc2  P2  Nakivubo-Kinawataka from Landsat, 1986 vs 2025, valley floor outlined
bg3  P3  building grain: a low-ground rental neighbourhood (Bwaise) vs a hillside (Rubaga), footprints by size
All figures: figures/kampala_drainage/cm*.png (Credit: Gava Charles; sources on each figure)
"""
import sys

import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from matplotlib import patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch, Rectangle
from rasterio.features import shapes

from common import FIG, PROC, RES, ROOT, lakes, save, uganda
from kd_roads_maps import extent, frame, relief, scalebar

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
UTM = 32636
SYS = {10: "Lubigi", 15: "Nakivubo", 40: "Kinawataka", 41: "Kansanga", 66: "Nalukolongo", 129: "Walufumbe"}
SYSCOL = {"Lubigi": "#80b1d3", "Nakivubo": "#fb8072", "Kinawataka": "#b3de69", "Kansanga": "#fdb462",
          "Nalukolongo": "#bc80bd", "Walufumbe": "#8dd3c7"}
HALO = [pe.withStroke(linewidth=3, foreground="white")]
OSM = "© OpenStreetMap contributors"


def utm(lon, lat):
    g = gpd.GeoSeries(gpd.points_from_xy(np.atleast_1d(lon), np.atleast_1d(lat)), crs=4326).to_crs(UTM)
    return g.x.values, g.y.values


def catchments(ids=SYS):
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        a, tr = r.read(1), r.transform
    m = np.isin(a, list(ids))
    rows = [(int(v), shp) for shp, v in shapes(a.astype("int32"), mask=m, transform=tr)]
    g = gpd.GeoDataFrame(dict(cid=[v for v, _ in rows]), geometry=[__import__("shapely.geometry", fromlist=["shape"]).shape(s)
                                                                   for _, s in rows], crs=4326)
    g = g.dissolve("cid").reset_index()
    g["name"] = g.cid.map(ids)
    return g.to_crs(UTM)


def north(ax, x=0.955, y=0.9):
    ax.annotate("N", xy=(x, y), xytext=(x, y - 0.08), xycoords="axes fraction", ha="center", va="center", fontsize=12,
                fontweight="bold", arrowprops=dict(arrowstyle="-|>", color="#222", lw=1.6), zorder=20)


def inset_uganda(fig, rect, mark=None, cities=None):
    ax = fig.add_axes(rect)
    ug = gpd.GeoSeries([uganda()], crs=4326)
    ug.plot(ax=ax, color="#f2efe9", edgecolor="#555", lw=0.8)
    lk = lakes().cx[29:35.5, -2:5]
    lk.plot(ax=ax, color="#bcd7ea", lw=0)
    if mark:
        x0, y0, x1, y1 = mark
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor="#c0392b", lw=1.8))
    if cities:
        for nm, (la, lo) in cities.items():
            ax.plot(lo, la, "o", color="#c0392b", ms=4)
    ax.set_xlim(29.4, 35.2)
    ax.set_ylim(-1.6, 4.4)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("white")
    for s_ in ax.spines.values():
        s_.set_color("#999")
    ax.text(0.5, 0.03, "Uganda", transform=ax.transAxes, ha="center", fontsize=8, color="#555")
    return ax


def label(ax, x, y, t, size=9, color="#222", weight="normal", ha="center", style="normal"):
    ax.text(x, y, t, fontsize=size, color=color, fontweight=weight, ha=ha, va="center", style=style, zorder=15,
            path_effects=HALO)


def base(figsize=(13, 11.4)):
    x0, x1, y0, y1 = extent()
    fig = plt.figure(figsize=figsize)
    ax = fig.add_axes([0.01, 0.1, 0.98, 0.8])
    relief(ax, x0, x1, y0, y1, alpha=0.45)
    return fig, ax, (x0, x1, y0, y1)


def kcca(ax):
    b = gpd.read_file(KD / "kcca_boundary.geojson").to_crs(UTM)
    b.boundary.plot(ax=ax, color="#333", lw=1.4, ls="--", zorder=6)
    return b


def channels(ax, s, minA=2, lw=0.8, color="#2b7bba"):
    s[s.up_km2 >= minA].plot(ax=ax, color=color, lw=lw, zorder=4)


def segs():
    return gpd.read_file(KD / "segments.gpkg").to_crs(UTM)


# ---------------------------------------------------------------------------------------------------------------- P1
def cm1():
    s = segs()
    fig, ax, (x0, x1, y0, y1) = base()
    c = catchments()
    for r in c.itertuples():
        gpd.GeoSeries([r.geometry], crs=UTM).plot(ax=ax, color=SYSCOL[r.name], alpha=0.38, edgecolor=SYSCOL[r.name], lw=1.2, zorder=2)
    channels(ax, s, 2, 0.9)
    kcca(ax)
    hs = pd.read_csv(KD / "flood_hotspots.csv")
    hx, hy = utm(hs.lon.values, hs.lat.values)
    ax.scatter(hx, hy, s=55, facecolor="#d7301f", edgecolor="white", lw=1, zorder=8)
    gx, gy = utm(32.568, 0.335)
    ax.scatter(gx, gy, marker="*", s=260, color="#ffd400", edgecolor="#222", lw=0.9, zorder=9)
    label(ax, gx[0] + 400, gy[0] + 500, "Makerere gauge", 8.5, ha="left")
    pos = {"Lubigi": (32.505, 0.355), "Nakivubo": (32.605, 0.300), "Kinawataka": (32.655, 0.352), "Kansanga": (32.625, 0.272),
           "Nalukolongo": (32.525, 0.288), "Walufumbe": (32.620, 0.392)}
    for nm, (lo, la) in pos.items():
        x, y = utm(lo, la)
        label(ax, x[0], y[0], nm, 11, "#222", "bold")
    lx, ly = utm(32.66, 0.235)
    label(ax, lx[0], ly[0], "Lake Victoria\n(Murchison Bay)", 9.5, "#2c5f8a", style="italic")
    frame(ax, x0, x1, y0, y1)
    scalebar(ax, x0 + 1500, y0 + 1200)
    north(ax)
    inset_uganda(fig, [0.80, 0.11, 0.17, 0.2], mark=(32.45, 0.20, 32.72, 0.42))
    hand = [Patch(color=SYSCOL[n], alpha=0.6, label=f"{n} system") for n in SYSCOL]
    hand += [Line2D([], [], color="#2b7bba", lw=1.5, label="channel (≥ 2 km² upstream)"),
             Line2D([], [], color="#333", lw=1.4, ls="--", label="KCCA boundary"),
             Line2D([], [], marker="o", ls="", mfc="#d7301f", mec="white", ms=8, label="reported flood hotspot (45)"),
             Line2D([], [], marker="*", ls="", mfc="#ffd400", mec="#222", ms=13, label="rain gauge")]
    fig.legend(handles=hand, loc="lower center", ncol=5, fontsize=9.5, frameon=False, bbox_to_anchor=(0.5, 0.035))
    fig.suptitle("Study area: Greater Kampala's six channel systems and reported flood hotspots", x=0.01, ha="left",
                 fontweight="bold", fontsize=15)
    fig.text(0.01, 0.925, "Analysis box 32.45–32.72° E, 0.20–0.42° N; 6,914 channel stretches (469 km) draining ≥ 0.25 km²",
             fontsize=10.5, color="#555")
    save(fig, "cm1_case_rainfall_or_drainage.png", OUT,
         source=f"Channels: {OSM} · catchments and relief: Copernicus GLO-30 DEM (D8 routing, this study) · KCCA boundary: "
                f"{OSM} · hotspots: KCCA/NEMA lists and news reports (approx. ±500 m)")


def fw1():
    fig = plt.figure(figsize=(14, 7.2))
    ax = fig.add_axes([0, 0, 1, 0.9])
    ax.axis("off")
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7.2)

    def box(x, y, w, h, txt, fc, size=10.5, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.15", fc=fc, ec="#555", lw=1))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=size, fontweight="bold" if bold else "normal",
                wrap=True)

    def arrow(a, b):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=14, color="#555", lw=1.2))
    box(5.0, 6.15, 4.0, 0.8, "Why does Kampala flood?", "#f0f0f0", 13, True)
    box(0.4, 4.6, 5.6, 0.95, "Explanation 1: heavier rain\n(climate)", "#deebf7", 11.5, True)
    box(8.0, 4.6, 5.6, 0.95, "Explanation 2: how the city was built\n(drainage, encroachment, capacity)", "#fde0dd", 11.5, True)
    arrow((6.2, 6.15), (3.6, 5.6))
    arrow((7.8, 6.15), (10.6, 5.6))
    left = [("Trend in rainfall extremes, 1981–2025\n(Mann–Kendall, Sen)", "§4.1: no trend"),
            ("Rain on 18 dated flood days\n(percentile of wet days)", "§4.2: median 74th"),
            ("Falling-threshold test, 2017–26\n(logistic, coverage control)", "§4.2: not detectable")]
    right = [("Hotspot index: six drainage pressures\nvs 45 reported hotspots", "§4.3: AUC 0.73"),
             ("Design-basis drift: 1990-sized channels\nvs 2020–2070 flows", "§4.4: median +17%"),
             ("Hold-out: 1975–2000 change predicts\n2000–2020 valley building", "§4.5: AUC 0.79")]
    for i, (t, r) in enumerate(left):
        y = 3.35 - i * 1.25
        box(0.4, y, 3.9, 0.95, t, "white", 9.5)
        box(4.45, y + 0.15, 1.55, 0.65, r, "#deebf7", 9, True)
        arrow((3.2, 4.6 if i == 0 else y + 2.2), (3.2, y + 0.95)) if i == 0 else None
    for i, (t, r) in enumerate(right):
        y = 3.35 - i * 1.25
        box(8.0, y, 3.9, 0.95, t, "white", 9.5)
        box(12.05, y + 0.15, 1.55, 0.65, r, "#fde0dd", 9, True)
        arrow((9.9, 4.6), (9.9, 4.3)) if i == 0 else None
    ax.plot([2.35, 2.35], [0.85, 4.6], color="#9ecae1", lw=3, zorder=0)
    ax.plot([9.95, 9.95], [0.85, 4.6], color="#fcbba1", lw=3, zorder=0)
    box(4.9, 0.08, 4.2, 0.62, "Verdict: the levers are on the ground", "#fff7bc", 11.5, True)
    arrow((6.0, 0.85), (6.4, 0.72))
    arrow((10.6, 0.85), (8.4, 0.72))
    fig.suptitle("Study design: two explanations, six tests", x=0.01, ha="left", fontweight="bold", fontsize=15)
    save(fig, "fw1_study_design_rainfall_or_drainage.png", OUT,
         source="Data: CHIRPS v2.0, NASA POWER, flood catalogue 2007–2026, OpenStreetMap, JRC GHSL, Copernicus GLO-30 (this study)")


# ---------------------------------------------------------------------------------------------------------------- P2
def cm2():
    import kd_bay as kb
    from matplotlib.colors import ListedColormap
    import kd_landcover as lc
    s = segs()
    x0, x1, y0, y1 = extent()
    _, by0 = utm(32.6, 0.13)
    y0b = by0[0]
    fig = plt.figure(figsize=(13, 13.6))
    ax = fig.add_axes([0.01, 0.09, 0.98, 0.83])
    relief(ax, x0, x1, y0b, y1, alpha=0.45)
    x, y, tr = lc.grid()
    hand, cat, lo, la = lc.terrain(x, y)
    cls = xr.open_dataset(KD / "landcover_2025.nc").cls.values
    from rasterio.warp import Resampling, reproject
    wc = np.zeros(hand.shape, "uint8")
    with rasterio.open(PROC / "kampala_worldcover.tif") as r:
        reproject(r.read(1), wc, src_transform=r.transform, src_crs=r.crs, dst_transform=tr, dst_crs="EPSG:32636",
                  resampling=Resampling.mode)
    vf = (hand < 3) & (cls >= 0) & (wc != 80) & (cls != 4)  # open water (incl. algae-green bay) excluded
    grp = np.where(vf, np.select([np.isin(cls, [0, 1]), cls == 2, cls == 3], [0, 1, 2], -1), -1).astype(float)
    grp[grp < 0] = np.nan
    ax.imshow(grp, cmap=ListedColormap(["#1b7837", "#d9ef8b", "#d6604d"]), vmin=-0.5, vmax=2.5, interpolation="nearest",
              extent=[x.min() - 15, x.max() + 15, y.min() - 15, y.max() + 15], zorder=3)
    c = catchments({15: "Nakivubo", 40: "Kinawataka", 41: "Kansanga", 112: "Munyonyo shore"})
    c.boundary.plot(ax=ax, color="#08306b", lw=1.8, zorder=6)
    channels(ax, s, 5, 0.7, "#2b7bba")
    m = kb.watermask()
    z = kb.zones(m.x.values, m.y.values, m.values.astype(bool)).astype(float)
    z[z == 0] = np.nan
    zc = ListedColormap(["#08519c", "#4292c6", "#9ecae1", "#deebf7"])
    ax.imshow(z, cmap=zc, vmin=0.5, vmax=4.5, alpha=0.75, extent=[float(m.x.min()), float(m.x.max()), float(m.y.min()),
                                                                     float(m.y.max())], zorder=2)
    gx, gy = utm(32.6385, 0.2585)
    ax.scatter(gx, gy, marker="^", s=150, color="#ffd400", edgecolor="#222", zorder=10)
    label(ax, gx[0] + 350, gy[0] - 550, "Ggaba waterworks\nintake (approx.)", 9, ha="left")
    ax.axhline(y.min(), color="#555", lw=0.8, ls=":", zorder=5)
    label(ax, x0 + 600, y.min() - 450, "land cover mapped north of this line", 8.5, "#555", ha="left", style="italic")
    for nm, (lo_, la_) in {"Nakivubo": (32.618, 0.312), "Kinawataka": (32.665, 0.345), "Kansanga": (32.608, 0.262)}.items():
        xx, yy = utm(lo_, la_)
        label(ax, xx[0], yy[0], nm, 11, "#08306b", "bold")
    for nm, (lo_, la_) in {"Inner\nMurchison Bay": (32.655, 0.275), "Outer bay": (32.665, 0.205),
                          "Open lake (reference)": (32.665, 0.150)}.items():
        xx, yy = utm(lo_, la_)
        label(ax, xx[0], yy[0], nm, 9.5, "#08306b", style="italic")
    frame(ax, x0, x1, y0b, y1)
    scalebar(ax, x0 + 1500, y0b + 1200)
    north(ax)
    inset_uganda(fig, [0.80, 0.10, 0.17, 0.18], mark=(32.45, 0.13, 32.72, 0.42))
    hand = [Patch(color="#1b7837", label="valley floor: wetland, trees"), Patch(color="#d9ef8b", label="valley floor: crops, grass"),
            Patch(color="#d6604d", label="valley floor: built, bare"),
            Line2D([], [], color="#08306b", lw=2, label="catchments draining to the bay"),
            Patch(color="#08519c", alpha=0.75, label="outlet zone (≤ 1.2 km)"), Patch(color="#4292c6", alpha=0.75, label="inner bay"),
            Patch(color="#9ecae1", alpha=0.75, label="outer bay"), Patch(color="#deebf7", label="open-lake reference")]
    fig.legend(handles=hand, loc="lower center", ncol=4, fontsize=9.5, frameon=False, bbox_to_anchor=(0.5, 0.02))
    fig.suptitle("Study area: Kampala's valley floors today and the bay they drain to", x=0.01, ha="left", fontweight="bold",
                 fontsize=15)
    fig.text(0.01, 0.94, "Valley floor = less than 3 m above the nearest drain; land cover 2025 from the machine-learning map; "
             "bay zones used for the satellite water analysis", fontsize=10.5, color="#555")
    save(fig, "cm2_case_double_loss.png", OUT,
         source=f"Land cover: Landsat machine-learning map (this study) · bay: Copernicus Sentinel-2 water mask · terrain: "
                f"Copernicus GLO-30 · channels: {OSM} · intake position approximate")


def lc2():
    xs, ys = utm(np.array([32.585, 32.700]), np.array([0.270, 0.352]))
    x0, y0 = xs, ys
    import kd_landcover as lc
    x, y, tr = lc.grid()
    hand, *_ = lc.terrain(x, y)
    fig, axs = plt.subplots(1, 2, figsize=(16, 6.4))
    fig.subplots_adjust(left=0.005, right=0.995, top=0.82, bottom=0.08, wspace=0.02)
    for ax, yr in zip(axs, (1986, 2025)):
        d = xr.open_dataset(KD / f"sat_landsat_{yr}.nc").sel(x=slice(x0[0], x0[1]), y=slice(y0[1], y0[0]))
        rgb = np.clip((np.nan_to_num(np.dstack([d.red, d.green, d.blue]).astype(float)) / 0.16) ** 0.8, 0, 1)
        ax.imshow(rgb, extent=[float(d.x.min()), float(d.x.max()), float(d.y.min()), float(d.y.max())])
        ax.contour(x, y, np.where(np.isfinite(hand), hand, 99), levels=[3], colors="#ffd400", linewidths=0.6)
        ax.set_xlim(x0[0], x0[1])
        ax.set_ylim(y0[0], y0[1])
        ax.set_axis_off()
        ax.set_title(f"{'ab'[yr == 2025]}  {yr}, Landsat dry-season composite", loc="left", fontsize=12)
        ax.plot([x0[0] + 400, x0[0] + 2400], [y0[0] + 500, y0[0] + 500], color="white", lw=3)
        ax.text(x0[0] + 1400, y0[0] + 800, "2 km", color="white", ha="center", fontsize=9, fontweight="bold")
    fig.suptitle("Nakivubo and Kinawataka: the treatment wetland, then and now", x=0.005, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.005, 0.895, "Yellow line: edge of the valley floor (3 m above the nearest drain). Dark green in 1986 is papyrus; "
             "by 2025 most of it is roofs, industry and gardens.", fontsize=10.5, color="#555")
    save(fig, "lc2_nakivubo_then_now.png", OUT,
         source="Imagery: NASA/USGS Landsat 5 (1986) and 8/9 (2025), dry-season median composites · valley floor: Copernicus GLO-30 (HAND)")


# ---------------------------------------------------------------------------------------------------------------- P3
def cm3():
    s = segs()
    fig, ax, (x0, x1, y0, y1) = base()
    channels(ax, s, 2, 0.7, "#6baed6")
    k = kcca(ax)
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand, trh = r.read(2), r.transform
    pop = xr.open_dataarray(PROC / "kampala_ghs_pop.nc").sel(epoch=2020).sel(lon=slice(32.45, 32.72), lat=slice(0.20, 0.42))
    LO, LA = np.meshgrid(pop.lon.values, pop.lat.values)
    col = ((LO - trh.c) / trh.a).astype(int).clip(0, hand.shape[1] - 1)
    row = ((LA - trh.f) / trh.e).astype(int).clip(0, hand.shape[0] - 1)
    hh = hand[row, col]
    pts = gpd.GeoSeries(gpd.points_from_xy(LO.ravel(), LA.ravel()), crs=4326).to_crs(UTM)
    import shapely
    ch = s[s.up_km2 >= 0.25]
    tree = shapely.STRtree(ch.geometry.values)
    near = np.zeros(len(pts), bool)
    near[np.unique(tree.query(pts.values, predicate="dwithin", distance=150)[0])] = True
    v = np.nan_to_num(pop.values.ravel())
    low = (hh.ravel() < 2) & near & (v > 5)
    inside = pts.within(k.geometry.iloc[0]).values
    px, py = pts.x.values[low], pts.y.values[low]
    sz = np.clip(v[low] / 25, 2, 60)
    ax.scatter(px[inside[low]], py[inside[low]], s=sz[inside[low]], color="#cb181d", alpha=0.55, lw=0, zorder=7)
    ax.scatter(px[~inside[low]], py[~inside[low]], s=sz[~inside[low]], color="#fd8d3c", alpha=0.65, lw=0, zorder=7)
    for nm, (lo_, la_) in {"Bwaise": (32.562, 0.352), "Kisenyi": (32.570, 0.306), "Kalerwe": (32.579, 0.360),
                          "Kira": (32.639, 0.398), "Nansana": (32.528, 0.372), "Namugongo": (32.655, 0.385),
                          "Kyaliwajjala": (32.668, 0.372)}.items():
        xx, yy = utm(lo_, la_)
        label(ax, xx[0], yy[0] + 450, nm, 9.5, "#222", "bold")
    frame(ax, x0, x1, y0, y1)
    scalebar(ax, x0 + 1500, y0 + 1200)
    north(ax)
    inset_uganda(fig, [0.80, 0.11, 0.17, 0.2], mark=(32.45, 0.20, 32.72, 0.42))
    pin, pout = v[low & inside].sum(), v[low & ~inside].sum()
    hand = [Line2D([], [], marker="o", ls="", mfc="#cb181d", mec="none", alpha=0.7, ms=9,
                   label=f"on low ground, inside KCCA ({pin / 1000:,.0f}k people)"),
            Line2D([], [], marker="o", ls="", mfc="#fd8d3c", mec="none", ms=9,
                   label=f"on low ground, outside KCCA, Wakiso fringe ({pout / 1000:,.0f}k)"),
            Line2D([], [], color="#333", lw=1.4, ls="--", label="KCCA boundary"),
            Line2D([], [], color="#6baed6", lw=1.5, label="channel")]
    fig.legend(handles=hand, loc="lower center", ncol=2, fontsize=10, frameon=False, bbox_to_anchor=(0.45, 0.025))
    fig.suptitle("Study area: who lives in the water's path, 2020", x=0.01, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.01, 0.925, "Residents of 100 m cells less than 2 m above the nearest drain and within 150 m of a channel; "
             "dot size = residents", fontsize=10.5, color="#555")
    save(fig, "cm3_case_waters_path.png", OUT,
         source=f"Population: JRC GHS-POP R2023A (2020) · terrain: Copernicus GLO-30 (HAND) · channels and KCCA boundary: {OSM}")
    pd.Series(dict(low_inside_kcca=pin, low_outside_kcca=pout)).round(0).to_csv(RES / "cm3_low_ground_kcca_split.csv")


def bg3():
    b = gpd.read_parquet(KD / "ms_buildings.parquet")
    fig, axs = plt.subplots(1, 3, figsize=(17, 6.6), gridspec_kw=dict(width_ratios=[1, 1, 0.8], wspace=0.06))
    fig.subplots_adjust(left=0.005, right=0.98, top=0.84, bottom=0.12)
    sites = [("a  Low ground: Bwaise, beside the Nsooba–Lubigi channel", 32.5615, 0.3525),
             ("b  Hillside: Kawempe hill, 2 km north", 32.5600, 0.3740)]
    areas = []
    for ax, (ttl, lo, la) in zip(axs[:2], sites):
        cx, cy = utm(lo, la)
        h = 220
        x0, x1, y0, y1 = cx[0] - h, cx[0] + h, cy[0] - h, cy[0] + h
        bb = b.cx[lo - 0.003:lo + 0.003, la - 0.003:la + 0.003].to_crs(UTM)
        bb = bb.cx[x0:x1, y0:y1]
        a = bb.area.values
        areas.append(a)
        cols = np.where(a < 40, "#d7301f", np.where(a < 100, "#fdae61", "#4575b4"))
        bb.plot(ax=ax, facecolor=cols, edgecolor="white", lw=0.4, alpha=0.85, zorder=3)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ctx.add_basemap(ax, crs=f"EPSG:{UTM}", source=ctx.providers.Esri.WorldImagery, zoom=18, attribution=False)
        ax.set_axis_off()
        ax.set_title(ttl, loc="left", fontsize=11)
        ax.plot([x0 + 20, x0 + 120], [y0 + 25, y0 + 25], color="white", lw=3)
        ax.text(x0 + 70, y0 + 40, "100 m", color="white", ha="center", fontsize=9, fontweight="bold")
        ax.text(0.98, 0.97, f"{len(a)} buildings · median {np.median(a):.0f} m² · {100 * (a < 40).mean():.0f}% under 40 m²",
                transform=ax.transAxes, ha="right", va="top", fontsize=9.5,
                bbox=dict(facecolor="white", alpha=0.9, edgecolor="none", pad=3))
    ax = axs[2]
    bins = np.arange(0, 305, 15)
    for a, c, l in zip(areas, ("#d7301f", "#4575b4"), ("Bwaise (low ground)", "Kawempe hill")):
        ax.hist(np.clip(a, 0, 300), bins=bins, density=True, histtype="step", lw=2.2, color=c, label=l)
    ax.axvline(40, color="#555", ls=":", lw=1)
    ax.text(42, ax.get_ylim()[1] * 0.92, "40 m²: a single room", fontsize=9, color="#555")
    ax.set_xlabel("building footprint (m²; > 300 grouped)")
    ax.set_yticks([])
    ax.legend(fontsize=9.5, frameon=False, loc="center right")
    ax.set_title("c  Footprint sizes in the two windows", loc="left", fontsize=11)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.legend(handles=[Patch(color="#d7301f", label="< 40 m² (room-sized)"), Patch(color="#fdae61", label="40–100 m²"),
                        Patch(color="#4575b4", label="> 100 m²")], loc="lower left", ncol=3, fontsize=10, frameon=False,
               bbox_to_anchor=(0.005, 0.02))
    fig.suptitle("The grain of building in the water's path", x=0.005, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.005, 0.895, "Two neighbouring 440 m windows at the same scale; single windows vary, so the evidence is the city-wide "
             "comparison: median 66 m² on low ground vs 82 m² on the hills (Section 3.3).", fontsize=10.5, color="#555")
    save(fig, "bg3_building_grain.png", OUT,
         source="Imagery: Esri World Imagery (Esri, Maxar, Earthstar Geographics) · buildings: Microsoft Global ML Building Footprints (2023)")


# ---------------------------------------------------------------------------------------------------------------- P4
def cm4():
    s = segs()
    p = gpd.read_parquet(KD / "road_pieces.parquet").to_crs(UTM)
    fig, ax, (x0, x1, y0, y1) = base()
    channels(ax, s, 2, 0.7, "#6baed6")
    p[p.cls.isin(["residential street", "service lane"])].plot(ax=ax, color="#c9c2bb", lw=0.15, zorder=3)
    p[p.cls.isin(["local through road"])].plot(ax=ax, color="#8a817a", lw=0.5, zorder=3)
    p[p.cls.isin(["highway", "main road"])].plot(ax=ax, color="#3b2f2f", lw=1.3, zorder=4)
    cr = p[p.crosses_channel & ~p.bridge & ~p.raised].drop_duplicates("osm_id")
    m = cr.geometry.interpolate(0.5, normalized=True)
    ax.scatter(m.x, m.y, marker="s", s=9, color="#f16913", edgecolor="#7f2704", lw=0.3, zorder=6)
    sv = gpd.read_file(KD / "osm_services.geojson").cx[32.45:32.72, 0.20:0.42].to_crs(UTM)
    hosp = sv[sv.amenity.eq("hospital") | sv.healthcare.eq("hospital")]
    ax.scatter(hosp.geometry.x, hosp.geometry.y, marker="P", s=40, color="#cb181d", edgecolor="white", lw=0.5, zorder=7)
    v = pd.read_csv(RES / "kd_roadsR_validation_spots.csv")
    v = v[v.geocoded]
    vx, vy = utm(v.lon.values, v.lat.values)
    ax.scatter(vx, vy, marker="^", s=110, facecolor="#ffd400", edgecolor="#222", lw=1, zorder=9)
    cx, cy = utm(32.5811, 0.3136)
    ax.add_patch(plt.Circle((cx[0], cy[0]), 1000, fill=False, edgecolor="#222", lw=1.6, ls="--", zorder=8))
    frame(ax, x0, x1, y0, y1)
    scalebar(ax, x0 + 1500, y0 + 1200)
    north(ax)
    inset_uganda(fig, [0.80, 0.11, 0.17, 0.2], mark=(32.45, 0.20, 32.72, 0.42))
    hand = [Line2D([], [], color="#3b2f2f", lw=2, label="highway / main road"),
            Line2D([], [], color="#8a817a", lw=1, label="local through road"),
            Line2D([], [], color="#c9c2bb", lw=1, label="street / lane"),
            Line2D([], [], color="#6baed6", lw=1.5, label="channel"),
            Line2D([], [], marker="s", ls="", mfc="#f16913", mec="#7f2704", ms=6, label=f"road–channel crossing without a bridge ({len(cr)})"),
            Line2D([], [], marker="P", ls="", mfc="#cb181d", mec="white", ms=9, label=f"hospital ({len(hosp)})"),
            Line2D([], [], marker="^", ls="", mfc="#ffd400", mec="#222", ms=10, label="reported flood-prone road (validation)"),
            Line2D([], [], marker="o", ls="", mfc="none", mec="#222", ms=12, mew=1.4, label="city centre (1 km of Clock Tower)")]
    fig.legend(handles=hand, loc="lower center", ncol=4, fontsize=9.5, frameon=False, bbox_to_anchor=(0.45, 0.025))
    fig.suptitle("Study area: Kampala's road network where it meets the channels", x=0.01, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.01, 0.925, "6,725 km of OpenStreetMap drivable road in 88,056 pieces; 3.6 million residents routed to the "
             "city centre and to hospitals", fontsize=10.5, color="#555")
    save(fig, "cm4_case_silt_not_storms.png", OUT,
         source=f"Roads, channels, hospitals: {OSM} · relief: Copernicus GLO-30 · validation: KCCA 2021 risk list (via Daily "
                f"Monitor), The Observer, flood catalogue")


def fw4():
    fig = plt.figure(figsize=(15, 6.6))
    ax = fig.add_axes([0, 0, 1, 0.88])
    ax.axis("off")
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 6.6)

    def box(x, y, w, h, txt, fc, size=10, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.12", fc=fc, ec="#555", lw=1))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=size, fontweight="bold" if bold else "normal")

    def arrow(a, b):
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=14, color="#555", lw=1.2))
    sw = [("L  paving", "1990 → 2020 cover", "#8c6bb1"), ("S  siltation", "clean → 30% depth lost", "#a50026"),
          ("E  encroachment", "open → footprint-blocked", "#f4a582"), ("C  climate", "today → 2041–70 SSP5-8.5", "#4393c3")]
    ax.text(1.6, 6.15, "Four switches", ha="center", fontsize=12, fontweight="bold")
    for i, (a, b_, c) in enumerate(sw):
        y = 4.9 - i * 1.15
        ax.add_patch(FancyBboxPatch((0.2, y), 2.8, 0.85, boxstyle="round,pad=0.05,rounding_size=0.12", fc=c, ec="none", alpha=0.85))
        ax.text(1.6, y + 0.55, a, ha="center", fontsize=11, fontweight="bold", color="white")
        ax.text(1.6, y + 0.22, b_, ha="center", fontsize=9, color="white")
    box(3.6, 2.6, 1.8, 1.4, "2⁴ = 16\nscenarios\n× 6 storms", "#f0f0f0", 11, True)
    for i in range(4):
        arrow((3.05, 5.32 - i * 1.15), (3.6, 3.3))
    chain = [("Channel capacity\n& flows (6,914\nstretches)", "#deebf7"), ("Stage on HAND\nrating curves", "#deebf7"),
             ("Depth on 88,056\nroad pieces\n(≥ 0.3 m = closed)", "#fee0d2"), ("Network: 3.6 m people\nto centre & hospitals", "#fee0d2")]
    for i, (t, fc) in enumerate(chain):
        x = 6.0 + i * 2.1
        box(x, 2.55, 1.85, 1.5, t, fc, 9.5)
        if i:
            arrow((x - 0.25, 3.3), (x, 3.3))
    arrow((5.45, 3.3), (6.0, 3.3))
    box(6.0, 0.35, 7.95, 1.25, "Shapley values: each switch's average marginal effect over all orders\n"
        "→ shares that add up exactly to the change since 1990", "#fff7bc", 10.5, True)
    arrow((10.9, 2.55), (10.9, 1.6))
    box(6.0, 4.65, 7.95, 1.1, "Uncertainty: 400 Monte Carlo runs over 12 assumptions → gradient-boosting emulator ranks them",
        "#f0f0f0", 10)
    arrow((10.0, 4.65), (10.0, 4.05))
    fig.suptitle("Attribution design: switching each driver on and off", x=0.01, ha="left", fontweight="bold", fontsize=15)
    save(fig, "fw4_attribution_design.png", OUT, source="Method: this study (Paper 4)")


# ---------------------------------------------------------------------------------------------------------------- P5
CITYLL = {"kampala": (0.31, 32.585), "jinja": (0.445, 33.205), "mbale": (1.08, 34.175), "gulu": (2.78, 32.30),
          "mbarara": (-0.607, 30.655), "arua": (3.02, 30.91)}


def cm5():
    from kd_cities import terrain
    fig = plt.figure(figsize=(17, 11))
    ax = fig.add_axes([0.005, 0.08, 0.33, 0.82])
    ug = gpd.GeoSeries([uganda()], crs=4326)
    ug.plot(ax=ax, color="#f2efe9", edgecolor="#555", lw=1)
    lakes().cx[29:35.5, -2:5].plot(ax=ax, color="#bcd7ea", lw=0)
    for c, (la, lo) in CITYLL.items():
        ax.plot(lo, la, "o", color="#c0392b" if c != "kampala" else "#222", ms=10 if c == "kampala" else 8, mec="white")
        dx, dy = {"jinja": (0.2, -0.28), "kampala": (-0.15, 0.25)}.get(c, (0.18, 0.15))
        label(ax, lo + dx, la + dy, c.capitalize(), 11, "#222", "bold", ha="right" if c == "kampala" else "left")
    ax.set_xlim(29.4, 35.2)
    ax.set_ylim(-1.6, 4.4)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title("a  Kampala and the five regional cities", loc="left", fontsize=12)
    t = pd.read_csv(RES / "kd_cities_roads.csv").set_index("city")
    order = ["kampala", "jinja", "mbale", "gulu", "mbarara", "arua"]
    for i, c in enumerate(order):
        r_, k_ = divmod(i, 3)
        sub = fig.add_axes([0.35 + k_ * 0.215, 0.5 - r_ * 0.4, 0.205, 0.36])
        f = (ROOT / "data" / "kd" / "cities" / f"{c}_dem.tif")
        hand, dist, tr, cell = terrain(f)
        with rasterio.open(f) as rr:
            b = rr.bounds
        vf = np.where((hand < 3) & np.isfinite(hand), 1.0, np.nan)
        sub.imshow(np.ones_like(hand), cmap="Greys", vmin=0, vmax=12, extent=[b.left, b.right, b.bottom, b.top])
        sub.imshow(vf, cmap=plt.matplotlib.colors.ListedColormap(["#a6dba0"]), extent=[b.left, b.right, b.bottom, b.top],
                   interpolation="nearest")
        rp = gpd.read_file(ROOT / "data" / "kd" / "cities" / f"{c}_road_pieces.gpkg")
        low = (rp.hand_min < 2) & (rp.dist_m <= 150)
        rp[~low].plot(ax=sub, color="#777", lw=0.25)
        rp[low].plot(ax=sub, color="#d7301f", lw=0.8)
        cy = (b.bottom + b.top) / 2
        half = 0.08
        cxm = (b.left + b.right) / 2
        sub.set_xlim(cxm - half / np.cos(np.deg2rad(0)), cxm + half)
        sub.set_ylim(cy - half, cy + half)
        sub.set_aspect("equal")
        sub.set_xticks([])
        sub.set_yticks([])
        for s_ in sub.spines.values():
            s_.set_color("#bbb")
        sub.set_title(f"{'bcdefg'[i]}  {c.capitalize()}: {t.loc[c, 'low_ground_pct']:.0f}% of road on low ground",
                      loc="left", fontsize=10.5)
        km = 2 / 111.32
        sub.plot([cxm - half + 0.01, cxm - half + 0.01 + km], [cy - half + 0.01] * 2, color="#222", lw=2.5)
        sub.text(cxm - half + 0.01 + km / 2, cy - half + 0.016, "2 km", ha="center", fontsize=8)
    fig.legend(handles=[Patch(color="#a6dba0", label="valley floor (< 3 m above a terrain channel)"),
                        Line2D([], [], color="#d7301f", lw=2, label="road on low ground beside a channel"),
                        Line2D([], [], color="#777", lw=1, label="other road")], loc="lower center", ncol=3, fontsize=10.5,
               frameon=False, bbox_to_anchor=(0.62, 0.02))
    fig.suptitle("Study area: six Ugandan cities at the same scale and under the same rules", x=0.005, ha="left",
                 fontweight="bold", fontsize=15)
    fig.text(0.005, 0.935, "Each panel: the central 18 × 18 km (Kampala cropped to the same size). Channels from the "
             "Copernicus terrain model, roads from OpenStreetMap.", fontsize=10.5, color="#555")
    save(fig, "cm5_case_next_kampalas.png", OUT,
         source=f"Terrain: Copernicus GLO-30 (D8 channels, HAND; this study) · roads: {OSM} · boundaries and lakes: Natural Earth")


# ---------------------------------------------------------------------------------------------------------------- P0
def cm0():
    s = segs()
    fig, ax, (x0, x1, y0, y1) = base()
    channels(ax, s, 2, 0.7, "#6baed6")
    kcca(ax)
    hs = pd.read_csv(KD / "flood_hotspots.csv")
    hx, hy = utm(hs.lon.values, hs.lat.values)
    ax.scatter(hx, hy, s=30, facecolor="none", edgecolor="#555", lw=1, zorder=6)
    c = pd.read_csv(RES / "kampala_flood_catalogue_2007_2026.csv")[["event_id", "grade"]]
    p = pd.read_csv(RES / "kampala_flood_catalogue_places.csv").merge(c, on="event_id")
    g = p.groupby(["place", "lat", "lon"]).agg(n=("event_id", "nunique"), best=("grade", "min")).reset_index()
    gx, gy = utm(g.lon.values, g.lat.values)
    col = g.best.map({"A": "#b30000", "B": "#fc8d59", "C": "#bdbdbd"})
    ax.scatter(gx, gy, s=60 + 90 * (g.n - 1), color=col, edgecolor="white", lw=1, alpha=0.9, zorder=8)
    top = g.sort_values("n", ascending=False).head(8)
    tx, ty = utm(top.lon.values, top.lat.values)
    off = {"Bwaise": (-1400, 600), "Kalerwe": (900, 700), "Banda": (900, 500), "Kyambogo": (-300, -900),
           "Namasuba": (900, -300), "Kinawataka": (-1200, -700), "Clock Tower": (-1300, -200), "Kyebando": (600, 900),
           "Ndeeba": (-1200, -400), "Katwe": (900, -500)}
    for (nm, n), x, y in zip(top[["place", "n"]].values, tx, ty):
        dx, dy = off.get(nm.split(" (")[0], (700, 500))
        ax.annotate(f"{nm} ({n})", (x, y), xytext=(x + dx, y + dy), fontsize=9.5, fontweight="bold", zorder=12,
                    path_effects=HALO, arrowprops=dict(arrowstyle="-", color="#444", lw=0.8))
    frame(ax, x0, x1, y0, y1)
    scalebar(ax, x0 + 1500, y0 + 1200)
    north(ax)
    inset_uganda(fig, [0.80, 0.11, 0.17, 0.2], mark=(32.45, 0.20, 32.72, 0.42))
    hand = [Line2D([], [], marker="o", ls="", mfc=c_, mec="white", ms=10, label=l) for c_, l in
            (("#b30000", "best record: dated, 2+ outlets"), ("#fc8d59", "best record: dated, 1 report"),
             ("#bdbdbd", "best record: month only"))]
    hand += [Line2D([], [], marker="o", ls="", mfc="none", mec="#555", ms=7, label="KCCA/NEMA and press hotspot list (45)"),
             Line2D([], [], color="#333", lw=1.4, ls="--", label="KCCA boundary")]
    fig.legend(handles=hand, loc="lower center", ncol=3, fontsize=9.5, frameon=False, bbox_to_anchor=(0.45, 0.025))
    fig.suptitle("Where Kampala's reported floods happened, 2007–2026", x=0.01, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.01, 0.925, "Places named in the 22 catalogued events (circle size: number of events; ±500 m), "
             "with the independent hotspot list for comparison", fontsize=10.5, color="#555")
    save(fig, "cm0_case_flood_catalogue.png", OUT,
         source=f"Flood reports: Daily Monitor, New Vision, NTV, URN, KFM, ReliefWeb, FloodList, GDELT · channels, boundary: {OSM} "
                f"· relief: Copernicus GLO-30")


if __name__ == "__main__":
    for f_ in sys.argv[1:] or ["cm0", "cm1", "fw1", "cm2", "lc2", "cm3", "bg3", "cm4", "fw4", "cm5"]:
        globals()[f_]()
        print("done", f_, flush=True)
