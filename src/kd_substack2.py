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


if __name__ == "__main__":
    for f in sys.argv[1:] or ["x4", "x5", "x6", "x7", "x8"]:
        globals()[f]()
        print("done", f)
