"""Maps for the roads study (figures/kampala_drainage/):

kd45  every road in Kampala by class, over shaded relief, channels and lake (cartographic overview)
kd46  roads that go under in a 10-year storm: clean vs silted channels, with the reported road floods
kd47  over time: roads on the valley floors by when their ground urbanised; low-ground road km 1975-2020; impassable
      road-km per year by state (1990 city, 2020 clean, 2020 silted, 2050s)
kd48  satellite close-ups (Esri World Imagery) of four reported road floods with modelled depth and culvert crossings
kd49  today's roads drawn on the 1986 landscape (Landsat) vs today (Esri imagery) at Lubigi
"""
import sys

import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from matplotlib.colors import LightSource, ListedColormap
from matplotlib.lines import Line2D

from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
UTM = 32636
BOX = (32.45, 0.20, 32.72, 0.42)
IMG = ctx.providers.Esri.WorldImagery
ST = dict(highway=("#3b2f2f", 1.7), **{"main road": ("#5a4a42", 1.1), "local through road": ("#7d6f66", 0.6),
          "residential street": ("#a39a92", 0.25), "service lane": ("#c4bdb6", 0.18)})
DEPTH_BINS = [0.3, 0.5, 1.0, 9]
DEPTH_COL = ["#fdae61", "#f46d43", "#a50026"]
DEPTH_LAB = ["0.3–0.5 m (cars stall)", "0.5–1 m", "over 1 m"]
LABELS = {  # main roads only: name pattern -> label anchor (lat, lon) chosen on the road, away from other labels
    "Northern Bypass": (0.3640, 32.5900), "Jinja Road": (0.3240, 32.6050), "Entebbe Road": (0.2560, 32.5640),
    "Hoima Road": (0.3330, 32.5370), "Bombo Road": (0.3420, 32.5720), "Gayaza Road": (0.3700, 32.6060),
    "Masaka Road": (0.2960, 32.5300), "Entebbe Expressway": (0.2460, 32.5880)}
SRC = ("Roads, channels: © OpenStreetMap contributors · terrain: Copernicus GLO-30 DEM · built-up: JRC GHSL R2023A · "
       "flood depths: screening hydraulics, gauge-corrected CHIRPS design storms (this study)")


def load():
    p = gpd.read_parquet(KD / "road_pieces.parquet").to_crs(UTM)
    s = gpd.read_file(KD / "segments.gpkg").to_crs(UTM)
    return p, s


def extent():
    b = gpd.GeoSeries(gpd.points_from_xy([BOX[0], BOX[2]], [BOX[1], BOX[3]]), crs=4326).to_crs(UTM)
    return b.x.min(), b.x.max(), b.y.min(), b.y.max()


def relief(ax, x0, x1, y0, y1, alpha=0.55):
    """Light shaded relief from the Copernicus DEM, reprojected to UTM, plus Lake Victoria."""
    from rasterio.warp import Resampling, reproject
    W, H = 900, int(900 * (y1 - y0) / (x1 - x0))
    tr = rasterio.transform.from_bounds(x0, y0, x1, y1, W, H)
    dem = np.zeros((H, W), "float32")
    wc = np.zeros((H, W), "uint8")
    with rasterio.open(PROC / "kampala_dem.tif") as r:
        reproject(r.read(1), dem, src_transform=r.transform, src_crs=r.crs, dst_transform=tr, dst_crs=f"EPSG:{UTM}",
                  resampling=Resampling.bilinear)
    with rasterio.open(PROC / "kampala_worldcover.tif") as r:
        reproject(r.read(1), wc, src_transform=r.transform, src_crs=r.crs, dst_transform=tr, dst_crs=f"EPSG:{UTM}",
                  resampling=Resampling.mode)
    hs = LightSource(azdeg=315, altdeg=40).hillshade(dem, vert_exag=6, dx=(x1 - x0) / W, dy=(y1 - y0) / H)
    ax.imshow(hs, cmap="Greys_r", extent=[x0, x1, y0, y1], vmin=-0.3, vmax=1.3, alpha=alpha, zorder=0)
    lake = np.ma.masked_where(wc != 80, np.ones_like(wc, float))
    ax.imshow(lake, cmap=ListedColormap(["#bcd7ea"]), extent=[x0, x1, y0, y1], zorder=1)


def frame(ax, x0, x1, y0, y1):
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_xticks([])
    ax.set_yticks([])
    for s_ in ax.spines.values():
        s_.set_color("#ccc")


def scalebar(ax, x0, y0, km=2, color="#333"):
    ax.plot([x0, x0 + km * 1000], [y0, y0], color=color, lw=3, solid_capstyle="butt", zorder=9)
    ax.text(x0 + km * 500, y0 + 250, f"{km} km", ha="center", fontsize=9, color=color, zorder=9)


def labels(ax, p, size=9):
    from matplotlib import patheffects as pe
    for nm, (la, lo) in LABELS.items():
        pt = gpd.GeoSeries(gpd.points_from_xy([lo], [la]), crs=4326).to_crs(UTM).iloc[0]
        cand = p[p.name.fillna("").str.contains(nm.replace("Entebbe Expressway", "Expressway"), case=False)]
        if len(cand):
            pt = cand.geometry.iloc[int(np.argmin(cand.distance(pt).values))].interpolate(0.5, normalized=True)
        ax.text(pt.x, pt.y, nm, fontsize=size, color="#222", fontweight="bold", ha="center", va="center", zorder=10,
                path_effects=[pe.withStroke(linewidth=3, foreground="white")])


def kd45(p, s):
    x0, x1, y0, y1 = extent()
    fig, ax = plt.subplots(figsize=(13, 11.2))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.11)
    relief(ax, x0, x1, y0, y1)
    s[s.up_km2 >= 2].plot(ax=ax, color="#3d8fd1", lw=0.9, zorder=2)
    for c in ["service lane", "residential street", "local through road", "main road", "highway"]:
        p[p.cls == c].plot(ax=ax, color=ST[c][0], lw=ST[c][1], zorder=3)
    labels(ax, p)
    frame(ax, x0, x1, y0, y1)
    scalebar(ax, x0 + 1500, y0 + 1200)
    km = p.groupby("cls").len_m.sum() / 1000
    hand = [Line2D([], [], color=ST[c][0], lw=max(ST[c][1] * 1.6, 1), label=f"{c} ({km.get(c, 0):,.0f} km)")
            for c in ["highway", "main road", "local through road", "residential street", "service lane"]]
    hand.append(Line2D([], [], color="#3d8fd1", lw=1.5, label="drainage channel"))
    fig.legend(handles=hand, loc="lower center", ncol=6, fontsize=9.5, frameon=False, bbox_to_anchor=(0.5, 0.055))
    fig.suptitle(f"Every road in Kampala: {p.len_m.sum() / 1000:,.0f} km", x=0.01, ha="left", fontweight="bold", fontsize=16)
    fig.text(0.01, 0.935, "OpenStreetMap drivable roads over shaded relief: the city's roads run along ridges and "
             "cross its valleys again and again", fontsize=11, color="#555")
    save(fig, "kd45_roads_all.png", OUT, source=SRC)


def kd46(p, s):
    x0, x1, y0, y1 = extent()
    ck = pd.read_csv(RES / "kd_roads_check.csv")
    rep = {"Hoima Road at Lubigi": (0.3410, 32.5360), "Jinja Road at Kyambogo": (0.3335, 32.6270),
           "Jinja Road at Banda": (0.3380, 32.6400), "Entebbe Road at Namasuba": (0.2722, 32.5634),
           "Bombo Road at Bwaise": (0.3520, 32.5620), "Mukwano Road": (0.3083, 32.5872),
           "Northern Bypass (Bwaise-Kalerwe)": (0.3530, 32.5700), "Kinawataka Road": (0.3351, 32.6432)}
    rp = gpd.GeoSeries(gpd.points_from_xy([v[1] for v in rep.values()], [v[0] for v in rep.values()]), crs=4326).to_crs(UTM)
    hz = pd.read_csv(RES / "kd_roads_hazard.csv").set_index("state")
    fig, axs = plt.subplots(1, 2, figsize=(17, 8.6))
    fig.subplots_adjust(left=0.005, right=0.995, top=0.85, bottom=0.14, wspace=0.02)
    for ax, (st, ttl) in zip(axs, (("2020 clean", "a  Channels clean"), ("2020 silted", "b  Channels 30% silted"))):
        relief(ax, x0, x1, y0, y1, alpha=0.35)
        s[s.up_km2 >= 2].plot(ax=ax, color="#3d8fd1", lw=0.7, zorder=2)
        p[p.cls.isin(["highway", "main road", "local through road"])].plot(ax=ax, color="#9a918a", lw=0.5, zorder=3)
        p[p.cls.isin(["residential street", "service lane"])].plot(ax=ax, color="#c9c2bb", lw=0.15, zorder=3)
        d = p[f"d10_{st}"]
        for k in range(3):
            sel = p[(d >= DEPTH_BINS[k]) & (d < DEPTH_BINS[k + 1])]
            sel.plot(ax=ax, color=DEPTH_COL[k], lw=1.6 + 0.6 * k, zorder=4 + k)
        ax.scatter(rp.x, rp.y, s=140, facecolor="none", edgecolor="#111", lw=1.6, zorder=8)
        for i, (x, y) in enumerate(zip(rp.x, rp.y)):
            ax.text(x + 380, y + 250, str(i + 1), fontsize=9, fontweight="bold", color="#111", zorder=9,
                    bbox=dict(facecolor="white", edgecolor="none", pad=0.6, alpha=0.85))
        frame(ax, x0, x1, y0, y1)
        ax.set_title(f"{ttl}: {hz.loc[st, 'impassable_km_T10']:,.0f} km of road impassable", loc="left", fontsize=12)
        scalebar(ax, x0 + 1500, y0 + 1200)
    hand = [Line2D([], [], color=c, lw=3, label=l) for c, l in zip(DEPTH_COL, DEPTH_LAB)]
    hand += [Line2D([], [], marker="o", ls="", mfc="none", mec="#111", ms=10, label="road flood in the news (numbered)")]
    fig.legend(handles=hand, loc="lower left", ncol=4, fontsize=10, frameon=False, bbox_to_anchor=(0.01, 0.075))
    key = "   ".join(f"{i + 1} {k}" for i, k in enumerate(rep))
    fig.text(0.01, 0.055, key, fontsize=8.5, color="#444")
    fig.suptitle("Kampala's roads that go under in a 10-year storm", x=0.01, ha="left", fontweight="bold", fontsize=16)
    fig.text(0.01, 0.905, "Water at least 0.3 m deep on the road, from the channel flood model. Every road named in a "
             "flood report floods in the silted case.", fontsize=11, color="#555")
    save(fig, "kd46_roads_flood_10yr.png", OUT, source=SRC)


def kd47(p, s):
    x0, x1, y0, y1 = extent()
    ex = pd.read_csv(RES / "kd_roads_exposure_by_epoch.csv")
    hz = pd.read_csv(RES / "kd_roads_hazard.csv").set_index("state")
    fig = plt.figure(figsize=(17, 8.4))
    ax = fig.add_axes([0.005, 0.14, 0.5, 0.74])
    relief(ax, x0, x1, y0, y1, alpha=0.3)
    s[s.up_km2 >= 2].plot(ax=ax, color="#3d8fd1", lw=0.6, zorder=2)
    p[p.hand_min >= 3].plot(ax=ax, color="#d9d3cc", lw=0.15, zorder=3)
    vf = p[p.hand_min < 3]
    bins = [(0, 1975, "by 1975", "#2c1b3d"), (1976, 1990, "1980–1990", "#7b3294"), (1991, 2005, "1995–2005", "#c2a5cf"),
            (2006, 2020, "2010–2020", "#f1a340"), (2021, 9999, "not yet urban", "#bbbbbb")]
    u = vf.urbanised.fillna(9999)
    for lo_, hi_, lab, col in bins[::-1]:
        vf[(u >= lo_) & (u <= hi_)].plot(ax=ax, color=col, lw=0.9, zorder=4)
    frame(ax, x0, x1, y0, y1)
    scalebar(ax, x0 + 1500, y0 + 1200)
    ax.set_title("a  Roads on the valley floors, by when their ground urbanised", loc="left", fontsize=12)
    fig.legend(handles=[Line2D([], [], color=c, lw=3, label=l) for _, _, l, c in bins], loc="lower left", ncol=5,
               fontsize=9.5, frameon=False, bbox_to_anchor=(0.005, 0.065))
    bx = fig.add_axes([0.56, 0.56, 0.42, 0.3])
    bx.plot(ex.epoch, ex.road_km_urban_low_ground, "-o", color="#7b3294", lw=2.2)
    for e in (1975, 2020):
        v = ex.set_index("epoch").road_km_urban_low_ground[e]
        bx.annotate(f"{v:,.0f} km", (e, v), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=10)
    bx.set_ylim(0, ex.road_km_urban_low_ground.max() * 1.25)
    bx.set_ylabel("urban road on low ground (km)")
    bx.set_title("b  Urban roads on low ground beside channels", loc="left", fontsize=12)
    bx.spines[["top", "right"]].set_visible(False)
    cx = fig.add_axes([0.56, 0.13, 0.42, 0.3])
    order = ["1990 city", "2020 clean", "2020 silted", "2050s"]
    labs = ["1990 city\n(modelled)", "today,\nclean channels", "today,\nsilted channels", "2050s,\nclean channels"]
    v = hz.loc[order, "expected_annual_impassable_km"].values
    cx.bar(range(4), v, color=["#bbbbbb", "#f46d43", "#a50026", "#7b3294"], width=0.6)
    for i, x in enumerate(v):
        cx.text(i, x + 3, f"{x:,.0f} km", ha="center", fontsize=11, fontweight="bold")
    cx.set_xticks(range(4))
    cx.set_xticklabels(labs, fontsize=9.5)
    cx.set_ylim(0, v.max() * 1.25)
    cx.set_ylabel("impassable road-km per year (expected)")
    cx.set_title("c  How much road goes under, on average, each year", loc="left", fontsize=12)
    cx.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Kampala's roads and its drainage, over time", x=0.005, ha="left", fontweight="bold", fontsize=16)
    save(fig, "kd47_roads_over_time.png", OUT, source=SRC)


CLOSE = [("Hoima Road and Northern Bypass at Lubigi", 0.3450, 32.5470),
         ("Bombo Road at Bwaise", 0.3520, 32.5640),
         ("Jinja Road, Kyambogo to Banda", 0.3370, 32.6330),
         ("Entebbe Road at Kibuye–Namasuba", 0.2650, 32.5660)]


def kd48(p, s):
    fig, axs = plt.subplots(2, 2, figsize=(15, 15))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.095, wspace=0.03, hspace=0.08)
    half = 900
    for ax, (ttl, la, lo) in zip(axs.flat, CLOSE):
        c = gpd.GeoSeries(gpd.points_from_xy([lo], [la]), crs=4326).to_crs(UTM).iloc[0]
        x0, x1, y0, y1 = c.x - half, c.x + half, c.y - half, c.y + half
        pp = p.cx[x0:x1, y0:y1]
        ss = s.cx[x0:x1, y0:y1]
        ss[ss.up_km2 >= 0.25].plot(ax=ax, color="#4fc3f7", lw=np.where(ss[ss.up_km2 >= 0.25].up_km2 >= 2, 3, 1.4), zorder=3)
        pp[pp.cls.isin(["highway", "main road", "local through road"])].plot(ax=ax, color="white", lw=1.4, alpha=0.8, zorder=4)
        d = pp["d10_2020 silted"]
        for k in range(3):
            pp[(d >= DEPTH_BINS[k]) & (d < DEPTH_BINS[k + 1])].plot(ax=ax, color=DEPTH_COL[k], lw=3.2 + k, zorder=5 + k)
        cr = pp[pp.crosses_channel & ~pp.bridge]
        if len(cr):
            m = cr.geometry.interpolate(0.5, normalized=True)
            ax.scatter(m.x, m.y, marker="s", s=36, color="white", edgecolor="k", lw=0.7, zorder=9)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ctx.add_basemap(ax, crs=f"EPSG:{UTM}", source=IMG, zoom=16, attribution=False)
        ax.set_axis_off()
        imp = pp.len_m[pp["d10_2020 silted"] >= 0.3].sum()
        ax.set_title(f"{ttl}  ·  {imp / 1000:.1f} km under water", loc="left", fontsize=11.5)
        ax.plot([x0 + 80, x0 + 580], [y0 + 90, y0 + 90], color="white", lw=3)
        ax.text(x0 + 330, y0 + 130, "500 m", color="white", ha="center", fontsize=9, fontweight="bold")
    hand = [Line2D([], [], color=c, lw=4, label=l) for c, l in zip(DEPTH_COL, DEPTH_LAB)]
    hand += [Line2D([], [], color="#4fc3f7", lw=3, label="drainage channel"),
             Line2D([], [], marker="s", ls="", mfc="white", mec="k", ms=7, label="road crosses channel without a bridge")]
    fig.legend(handles=hand, loc="lower center", ncol=5, fontsize=10, frameon=False, bbox_to_anchor=(0.5, 0.045))
    fig.suptitle("Where Kampala's roads meet its channels: 10-year storm, channels silted", x=0.01, ha="left",
                 fontweight="bold", fontsize=16)
    save(fig, "kd48_roads_satellite_closeups.png", OUT,
         source="Imagery: Esri World Imagery (Esri, Maxar, Earthstar Geographics) · roads, channels: © OpenStreetMap "
                "contributors · depths: screening flood model (this study)")


def kd49(p, s):
    la, lo = 0.3480, 32.5560
    c = gpd.GeoSeries(gpd.points_from_xy([lo], [la]), crs=4326).to_crs(UTM).iloc[0]
    half = 1600
    x0, x1, y0, y1 = c.x - half, c.x + half, c.y - half, c.y + half
    pp = p.cx[x0:x1, y0:y1]
    d = xr.open_dataset(KD / "sat_landsat_1986.nc").sel(x=slice(x0, x1), y=slice(y1, y0))
    rgb = np.clip((np.nan_to_num(np.dstack([d.red, d.green, d.blue]).astype(float)) / 0.16) ** 0.8, 0, 1)
    fig, axs = plt.subplots(1, 2, figsize=(16, 8.6))
    fig.subplots_adjust(left=0.005, right=0.995, top=0.84, bottom=0.12, wspace=0.02)
    axs[0].imshow(rgb, extent=[float(d.x.min()) - 15, float(d.x.max()) + 15, float(d.y.min()) - 15, float(d.y.max()) + 15])
    axs[1].set_xlim(x0, x1)
    axs[1].set_ylim(y0, y1)
    ctx.add_basemap(axs[1], crs=f"EPSG:{UTM}", source=IMG, zoom=16, attribution=False)
    for ax, ttl in zip(axs, ("a  1986 (Landsat), with today's roads drawn on", "b  Today (Esri imagery)")):
        main = pp[pp.cls.isin(["highway", "main road", "local through road"])]
        minor = pp[pp.cls.isin(["residential street", "service lane"])]
        minor.plot(ax=ax, color="#ffe082", lw=0.5, alpha=0.8, zorder=4)
        main.plot(ax=ax, color="#ffb300", lw=2.0, zorder=5)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_axis_off()
        ax.set_title(ttl, loc="left", fontsize=12)
        ax.plot([x0 + 120, x0 + 1120], [y0 + 140, y0 + 140], color="white", lw=3)
        ax.text(x0 + 620, y0 + 220, "1 km", color="white", ha="center", fontsize=9, fontweight="bold")
    wet = pp[(pp.hand_min < 3) & pp.lc1986.isin([0, 1])].len_m.sum() / 1000
    fig.suptitle("Lubigi: the roads were built across the wetland", x=0.005, ha="left", fontweight="bold", fontsize=16)
    fig.text(0.005, 0.895, f"In this 3 km square, {wet:.0f} km of today's road sits on valley floor that was wetland or "
             "bush in 1986. Northern Bypass crosses the valley in the centre.", fontsize=11, color="#555")
    fig.legend(handles=[Line2D([], [], color="#ffb300", lw=3, label="main road today"),
                        Line2D([], [], color="#ffe082", lw=1.5, label="street or lane today")],
               loc="lower left", ncol=2, fontsize=10, frameon=False, bbox_to_anchor=(0.005, 0.06))
    save(fig, "kd49_roads_lubigi_then_now.png", OUT,
         source="Imagery: NASA/USGS Landsat 5 (1986 dry season), Esri World Imagery (today) · roads: © OpenStreetMap "
                "contributors · land cover 1986: machine-learning map (this study)")


if __name__ == "__main__":
    p, s = load()
    for f in sys.argv[1:] or ["kd45", "kd46", "kd47", "kd48", "kd49"]:
        globals()[f](p, s)
