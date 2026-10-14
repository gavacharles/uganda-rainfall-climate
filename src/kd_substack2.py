"""Graphics for two Substack follow-ups (outreach/kampala_drainage/):

Flood log post
  x4_four_silent_years.png   events found per year by grade vs Kampala news indexed per year (two panels, one axis each)
  x5_flood_log_card.png      what a city flood log would record, with the 11 Oct 2026 flood as the example entry
The sponge we paved post
  x6_sponge_pools.png        17 million m3: storage lost + extra runoff for one 10-year storm, in Olympic pools
  x7_living_sponge.png       vegetated valley floor 1986 vs 2025, by channel system
  x8_bay_treatment.png       wetland draining to Murchison Bay, 1986-2025, and the treatment it no longer does
"""
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import RES, ROOT
from outreach_graphics import BG, BLU, GRIDC, INK, MUTE, RED, credit, frame

OUT = ROOT / "outreach" / "kampala_drainage"
GRADE = {"A": ("#b30000", "dated, 2+ outlets"), "B": ("#fc8d59", "dated, 1 report"), "C": ("#bdbdbd", "month only")}


def x4():
    c = pd.read_csv(RES / "kampala_flood_catalogue_2007_2026.csv")
    c["year"] = c.date.str[:4].astype(int)
    v = pd.read_csv(ROOT / "data" / "kd" / "gdelt_kampala_volume.csv", parse_dates=["date"]).set_index("date").n
    vy = v.resample("YS").sum()
    vy.index = vy.index.year
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 6.75), sharex=True, gridspec_kw=dict(height_ratios=[1.25, 1], hspace=0.35))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.80, bottom=0.14)
    fig.text(0.08, 0.93, "Kampala's flood record has a four-year hole", fontsize=24, fontweight="bold", color=INK)
    fig.text(0.08, 0.865, "Floods did not stop in 2021–2024. The reporting did.", fontsize=15, color=MUTE)
    fig.text(0.08, 0.03, "Data: Kampala flood catalogue 2007–2026 (news and ReliefWeb/FloodList reports); news volume: GDELT index.",
             fontsize=10, color=MUTE)
    credit(fig)
    yrs = np.arange(2007, 2027)
    bottom = np.zeros(len(yrs))
    for g in "ABC":
        n = c[c.grade == g].groupby("year").size().reindex(yrs, fill_value=0).values
        a1.bar(yrs, n, bottom=bottom, color=GRADE[g][0], width=0.7, label=GRADE[g][1], edgecolor=BG, lw=1.5)
        bottom += n
    for ax in (a1, a2):
        ax.axvspan(2020.6, 2024.4, color="#f1efe9", zorder=0, lw=0)
    a1.text(2022.5, 3.3, "the silent years", ha="center", fontsize=13, color=MUTE, style="italic")
    a1.set_ylim(0, 4.2)
    a1.set_yticks([0, 1, 2, 3, 4])
    a1.set_title("Floods on record per year", fontsize=14, color=INK, pad=6)
    a1.legend(loc="upper left", fontsize=11, ncol=3)
    a2.bar(vy.index, vy.values / 1000, color=BLU, width=0.7)
    a2.set_xlim(2006.4, 2026.6)
    a2.set_title("Kampala news stories indexed per year (thousands; index starts 2017)", fontsize=14, color=INK, pad=6)
    a2.set_xticks([2008, 2011, 2014, 2017, 2020, 2023, 2026])
    fig.savefig(OUT / "x4_four_silent_years.png", dpi=150)
    plt.close(fig)


def x5():
    fig = plt.figure(figsize=(12, 6.75))
    fig.text(0.06, 0.91, "What a Kampala flood log would record", fontsize=24, fontweight="bold", color=INK)
    fig.text(0.06, 0.845, "One line per flood, filled in by ward officers and residents, published every quarter.",
             fontsize=15, color=MUTE)
    fields = [("When", "date and time the water rose and fell"), ("Where", "GPS point, street, nearest channel"),
              ("How deep", "ankle, knee, waist, above head"), ("What closed", "roads, schools, clinics, markets"),
              ("Who", "homes flooded, displaced, hurt, dead"), ("Why", "blocked culvert, overtopped channel"),
              ("Proof", "photo, rain-gauge reading")]
    y = 0.72
    for k, v in fields:
        fig.text(0.06, y, k, fontsize=16, fontweight="bold", color=RED)
        fig.text(0.21, y, v, fontsize=14, color=INK)
        y -= 0.083
    ax = fig.add_axes([0.62, 0.17, 0.34, 0.6])
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color(GRIDC)
    ax.set_facecolor("#ffffff")
    ax.grid(False)
    ax.text(0.06, 0.92, "Example entry", fontsize=13, color=MUTE, transform=ax.transAxes)
    lines = [("When", "11 Oct 2026, ~3 a.m."), ("Where", "Hoima Rd at Lubigi channel"),
             ("How deep", "knee to waist on the road"), ("What closed", "Kampala–Hoima road"),
             ("Who", "2 dead (wall collapse)"), ("Why", "Lubigi overtopped"), ("Proof", "Daily Monitor, NTV")]
    yy = 0.80
    for k, v in lines:
        ax.text(0.06, yy, k, fontsize=12, fontweight="bold", color=INK, transform=ax.transAxes)
        ax.text(0.40, yy, v, fontsize=12, color=INK, transform=ax.transAxes)
        yy -= 0.11
    fig.text(0.06, 0.03, "Example from news reports of 11 Oct 2026 (Daily Monitor, NTV, KFM).", fontsize=10, color=MUTE)
    credit(fig)
    fig.savefig(OUT / "x5_flood_log_card.png", dpi=150)
    plt.close(fig)


def x6():
    g = pd.read_csv(RES / "kd_sponge_gap.csv").set_index("region").loc["Greater Kampala core"]
    fig, ax = frame("The sponge we paved", "Kampala 1975–2020, one 10-year storm: water the valleys can no longer hold, plus extra runoff", "Data: Copernicus GLO-30 DEM, JRC GHSL 1975–2020, CHIRPS design storm. Pool = 2,500 m³.")
    ax.barh([0], [g.storage_lost_Mm3], color="#2e8b57", height=0.5, label="valley storage lost")
    ax.barh([0], [g.extra_runoff_T10_Mm3], left=[g.storage_lost_Mm3], color=RED, height=0.5, label="extra runoff from paving")
    ax.text(g.storage_lost_Mm3 / 2, 0, f"{g.storage_lost_Mm3:.1f} million m³\nstorage lost", ha="center", va="center",
            color="white", fontsize=15, fontweight="bold")
    ax.text(g.storage_lost_Mm3 + g.extra_runoff_T10_Mm3 / 2, 0, f"{g.extra_runoff_T10_Mm3:.1f} million m³\nextra runoff",
            ha="center", va="center", color="white", fontsize=15, fontweight="bold")
    ax.text(0, 0.62, f"{g.combined_gap_Mm3:.0f} million m³  ≈  {round(g.olympic_pools, -2):,.0f} Olympic swimming pools", fontsize=22,
            fontweight="bold", color=INK)
    ax.set_ylim(-0.6, 1.0)
    ax.set_xlim(0, g.combined_gap_Mm3 * 1.02)
    ax.set_yticks([])
    ax.set_xlabel("million m³")
    ax.grid(False)
    fig.savefig(OUT / "x6_sponge_pools.png", dpi=150)
    plt.close(fig)


def x7():
    d = pd.read_csv(RES / "kd_sponge_landsat.csv")
    d = d[d.region != "Greater Kampala core"].pivot(index="region", columns="year", values="valley_floor_vegetated_pct")
    d = d.sort_values(2025, ascending=False)
    fig, ax = frame("Kampala's valley wetlands, then and now", "Share of each channel system's valley floor still green "
                    "(papyrus, grass, crops) in the dry season", "Data: NASA/USGS Landsat 5 and 8/9 dry-season composites "
                    "(NDVI > 0.45), valley floor from Copernicus GLO-30 DEM.")
    y = np.arange(len(d))
    for i, (nm, r) in enumerate(d.iterrows()):
        ax.plot([r[2025], r[1986]], [i, i], color=GRIDC, lw=6, solid_capstyle="round", zorder=1)
        ax.scatter([r[1986]], [i], s=160, color="#2e8b57", zorder=3, edgecolor=BG, lw=2)
        ax.scatter([r[2025]], [i], s=160, color=RED, zorder=3, edgecolor=BG, lw=2)
        ax.text(r[2025] - 3, i, f"{r[2025]:.0f}%", ha="right", va="center", fontsize=13, color=INK)
        ax.text(r[1986] + 2.5, i, f"{r[1986]:.0f}%", ha="left", va="center", fontsize=13, color=MUTE)
    ax.set_yticks(y)
    ax.set_yticklabels(d.index, fontsize=15)
    ax.invert_yaxis()
    ax.set_xlim(-12, 112)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.scatter([], [], s=120, color="#2e8b57", label="1986")
    ax.scatter([], [], s=120, color=RED, label="2025")
    ax.set_ylim(len(d) - 0.4, -1.4)
    ax.legend(loc="upper left", fontsize=13, ncol=2)
    ax.grid(axis="y", visible=False)
    fig.savefig(OUT / "x7_living_sponge.png", dpi=150)
    plt.close(fig)


def x8():
    w = pd.read_csv(RES / "kd_bay_wetland.csv")
    t = pd.read_csv(RES / "kd_bay_treatment.csv", index_col=0).value
    s = w[w.region == "Bay-draining catchments"].set_index("year").vegetated_ha
    fig, ax = frame("The free treatment plant we built over", "Green wetland in the valleys that drain into Murchison Bay, "
                    "Lake Victoria (hectares)", "Data: NASA/USGS Landsat, Copernicus GLO-30 DEM; value US$1,500–2,900/ha/yr (Emerton et al. 1999).")
    ax.bar(s.index, s.values, width=6, color="#2e8b57", edgecolor=BG, lw=2)
    for yr, v in s.items():
        ax.text(yr, v + 25, f"{v:,.0f} ha", ha="center", fontsize=14, color=INK)
    ax.set_xticks(s.index)
    ax.set_ylim(0, s.max() * 1.5)
    ax.set_ylabel("hectares")
    ax.grid(axis="x", visible=False)
    ax.text(2007, s.max() * 1.33, f"−{t.lost_pct:.0f}% since 1986: about US${t.value_lost_lo_usd / 1e6:.1f}–"
            f"{t.value_lost_hi_usd / 1e6:.1f} million a year\nof water cleaning the city no longer gets for free",
            fontsize=15, color=INK, ha="center", fontweight="bold")
    fig.savefig(OUT / "x8_bay_treatment.png", dpi=150)
    plt.close(fig)


def x10():
    p = pd.read_csv(RES / "kd_bay_landsat_periods.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 6.75), gridspec_kw=dict(wspace=0.28))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.76, bottom=0.17)
    fig.text(0.08, 0.93, "As the swamps went, the bay got murkier", fontsize=24, fontweight="bold", color=INK)
    fig.text(0.08, 0.865, "Where Kampala's channels enter Murchison Bay, compared with the open lake on the same day",
             fontsize=15, color=MUTE)
    fig.text(0.08, 0.03, "Data: NASA/USGS Landsat 1984–2026 (179 images); valley floors from Copernicus GLO-30 DEM.", fontsize=10, color=MUTE)
    credit(fig)
    x = np.arange(len(p))
    lab = ["1984–95", "1996–2005", "2006–15", "2016–26"]
    a1.bar(x, p.wetland_ha_mid, color="#2e8b57", width=0.65)
    for i, v in enumerate(p.wetland_ha_mid):
        a1.text(i, v + 25, f"{v:,.0f} ha", ha="center", fontsize=13, color=INK)
    a1.set_title("Wetland draining to the bay", fontsize=15, color=INK, pad=8)
    a1.set_ylim(0, p.wetland_ha_mid.max() * 1.2)
    ex = 100 * (p.ratio_median - 1)
    cols = [RED] * len(p)
    a2.bar(x, ex, color=cols, width=0.65, alpha=1)
    a2.patches[0].set_alpha(0.45)
    for i, v in enumerate(ex):
        a2.text(i, v + 1.2, f"+{v:.0f}%", ha="center", fontsize=15, fontweight="bold", color=INK)
    a2.text(0, ex[0] / 2, "few\nimages", ha="center", va="center", fontsize=10, color="white")
    a2.set_title("Outlets: how much murkier than the lake", fontsize=15, color=INK, pad=8)
    a2.set_ylim(0, ex.max() * 1.25)
    for ax in (a1, a2):
        ax.set_xticks(x)
        ax.set_xticklabels(lab, fontsize=12)
        ax.set_yticks([])
        ax.grid(False)
        ax.spines["left"].set_visible(False)
    fig.savefig(OUT / "x10_bay_murkier.png", dpi=150)
    plt.close(fig)




def _cover(fname, kicker, l1, l2, sub, draw, source):
    """Substack cover 1456 x 1048, same layout as cover_substack_1456x1048.png."""
    import matplotlib
    from PIL import Image
    D, KICK, R2 = BG, "#1d6a8a", RED
    fig = plt.figure(figsize=(14.56, 10.48), dpi=100, facecolor=D)
    ax = fig.add_axes([0.48, 0.045, 0.52, 0.955], facecolor=D)
    draw(ax)
    ax.axis("off")
    g = fig.add_axes([0.48, 0.045, 0.14, 0.955])
    grad = np.zeros((2, 256, 4))
    grad[..., :3] = matplotlib.colors.to_rgb(D)
    grad[..., 3] = np.linspace(1, 0, 256)
    g.imshow(grad, aspect="auto", extent=[0, 1, 0, 1])
    g.axis("off")
    fig.text(0.055, 0.80, kicker, fontsize=17, fontweight="bold", color=KICK)
    fig.text(0.055, 0.745, l1, fontsize=50, fontweight="bold", color=INK, va="top", linespacing=1.05)
    n1 = l1.count("\n") + 1
    fig.text(0.055, 0.745 - 0.083 * n1, l2, fontsize=50, fontweight="bold", color=R2, va="top", linespacing=1.05)
    n2 = l2.count("\n") + 1
    fig.text(0.055, 0.745 - 0.083 * (n1 + n2) - 0.03, sub, fontsize=20, color=MUTE, va="top", linespacing=1.45)
    fig.text(0.055, 0.075, "Credit: Gava Charles", fontsize=18, fontweight="bold", color=INK)
    fig.add_artist(plt.Rectangle((0, 0), 1, 0.045, transform=fig.transFigure, color="#f1efe9", zorder=5))
    fig.text(0.055, 0.017, source, fontsize=10.5, color=MUTE, zorder=6)
    fig.savefig(OUT / fname, dpi=100, facecolor=D)
    plt.close(fig)
    im = Image.open(OUT / fname)
    if im.size != (1456, 1048):
        im.resize((1456, 1048), Image.LANCZOS).save(OUT / fname)


def covers():
    import xarray as xr
    from matplotlib.colors import ListedColormap
    import kd_landcover as lc
    import kd_bay as kb
    KD = ROOT / "data" / "kd"
    x, y, tr = lc.grid()
    hand, cat, lo, la = lc.terrain(x, y)

    def sponge(ax):
        cm = ListedColormap(lc.COLORS)
        r0, r1, c0, c1 = 120, 640, 60, 840
        for k, yr in enumerate((1986, 2025)):
            cls = xr.open_dataset(KD / f"landcover_{yr}.nc").cls.values[r0:r1, c0:c1]
            h = hand[r0:r1, c0:c1]
            top = 1 - k * 0.5
            sub = ax.inset_axes([0.0, top - 0.49, 1.0, 0.47])
            sub.imshow(np.where(np.isfinite(h), 1, np.nan), cmap=ListedColormap(["#e9e6df"]), aspect="auto")
            sub.imshow(np.where((h < 3) & (cls >= 0), cls, np.nan).astype(float), cmap=cm, vmin=-0.5,
                       vmax=len(lc.CLASSES) - 0.5, interpolation="nearest", aspect="auto")
            sub.axis("off")
            sub.text(0.97, 0.06, str(yr), transform=sub.transAxes, fontsize=34, fontweight="bold", color=INK,
                     ha="right", bbox=dict(facecolor=BG, alpha=0.85, edgecolor="none", pad=4))

    def bay(ax):
        comp = xr.open_dataset(KD / "sat_bay_s2_dry.nc")
        grey = np.clip(np.dstack([comp.B04, comp.B03, comp.B02]).mean(2) / 0.15, 0, 1)
        ext = [float(comp.x.min()), float(comp.x.max()), float(comp.y.min()), float(comp.y.max())]
        T = kb.scene_turb("2019-11-21")
        ax.imshow(grey, cmap="Greys_r", extent=ext, vmin=-0.6, vmax=1.3, alpha=0.75)
        ax.imshow(T.values, cmap="YlOrBr", vmin=4, vmax=24,
                  extent=[float(T.x.min()), float(T.x.max()), float(T.y.min()), float(T.y.max())])
        ax.set_xlim(455600, 466000)
        ax.set_ylim(22200, 35800)
        ax.set_aspect("auto")
        ax.text(0.97, 0.015, "Murchison Bay after rain, 21 Nov 2019 · darker orange = murkier", transform=ax.transAxes,
                fontsize=11, color=INK, ha="right", bbox=dict(facecolor=BG, alpha=0.85, edgecolor="none", pad=4))

    _cover("cover_sponge_1456x1048.png", "KAMPALA FLOODS · 40 YEARS FROM SPACE",
           "Kampala paved\nits sponge.", "Now the rain\ncomes indoors.",
           "Half the valley wetlands that held storm\nwater are gone. 17 million m³ of water\nnow has nowhere to go.\n\nMaps: valley floors in green (wetland, trees)\nturning red (built, bare).",
           sponge, "Imagery: NASA/USGS Landsat · land cover: machine learning (LightGBM) on WorldCover/Impact Observatory "
                   "labels · terrain: Copernicus GLO-30")
    _cover("cover_bay_1456x1048.png", "KAMPALA'S WATER · LAKE VICTORIA",
           "We built over", "Kampala's\nkidneys.",
           "The swamps that cleaned the city's water\nbefore it reached the lake are half gone.\n"
           "From space, the bay is getting murkier.",
           bay, "Imagery: Copernicus Sentinel-2 (ESA) · turbidity: Dogliotti et al. 2015 · wetland: NASA/USGS Landsat")
    print("covers done")


if __name__ == "__main__":
    for f in sys.argv[1:] or ["x4", "x5", "x6", "x7", "x8"]:
        globals()[f]()
        print("done", f)
