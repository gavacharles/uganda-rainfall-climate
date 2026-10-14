"""Animations for the Murchison Bay Substack (outreach/kampala_drainage/gifs/), each with a still companion.

kd_a12_bay_swamps.gif      Landsat true colour of the swamps between Kampala and the bay, 1986 -> 2025, with wetland counter
                           (still: x11_bay_swamps_1986_2025.png)
kd_a13_bay_plumes.gif      Sentinel-2 turbidity of the bay over runs of clear passes in the short rains (Dec 2018-Jan 2019,
                           Nov-Dec 2020), with rain in the previous 3 days (still: kd42_bay_plumes.png)
kd_a14_bay_murkier.gif     the outlet-vs-lake gap building up period by period (still: x10_bay_murkier.png)
"""
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyproj
import xarray as xr
from PIL import Image

import kd_bay as kb
from common import RES, ROOT
from outreach_graphics import BG, INK, MUTE, RED

KD = ROOT / "data" / "kd"
OUT = ROOT / "outreach" / "kampala_drainage"
GIFS = OUT / "gifs"
CREDIT = "Credit: Gava Charles"


def grab(fig):
    fig.canvas.draw()
    im = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3])
    plt.close(fig)
    return im


def header(fig, title, sub, source):
    fig.patch.set_facecolor(BG)
    fig.text(0.03, 0.945, title, fontsize=25, fontweight="bold", color=INK)
    fig.text(0.03, 0.905, sub, fontsize=14.5, color=MUTE)
    fig.text(0.03, 0.022, source, fontsize=10, color=MUTE)
    fig.text(0.97, 0.022, CREDIT, fontsize=12, fontweight="bold", color=INK, ha="right", alpha=0.8)


def utm_box(lo0, la0, lo1, la1):
    tf = pyproj.Transformer.from_crs(4326, 32636, always_xy=True)
    x0, y0 = tf.transform(lo0, la0)
    x1, y1 = tf.transform(lo1, la1)
    return x0, x1, y0, y1


def a12():
    w = pd.read_csv(RES / "kd_bay_wetland.csv")
    wb = w[w.region == "Bay-draining catchments"].set_index("year").vegetated_ha
    x0, x1, y0, y1 = utm_box(32.585, 0.270, 32.700, 0.352)
    frames = []
    for yr in (1986, 1995, 2005, 2015, 2025):
        d = xr.open_dataset(KD / f"sat_landsat_{yr}.nc").sel(x=slice(x0, x1), y=slice(y1, y0))
        rgb = np.dstack([d.red, d.green, d.blue]).astype(float)
        rgb = np.clip((np.nan_to_num(rgb) / 0.16) ** 0.8, 0, 1)
        fig = plt.figure(figsize=(10.8, 10.8), dpi=100)
        header(fig, "The swamps between Kampala and the lake", "Nakivubo, Kinawataka and Luzira from space, dry season",
               "Imagery: NASA/USGS Landsat dry-season composites · terrain: Copernicus GLO-30")
        ax = fig.add_axes([0.03, 0.1, 0.94, 0.72])
        ax.imshow(rgb, extent=[float(d.x.min()), float(d.x.max()), float(d.y.min()), float(d.y.max())], aspect="auto")
        ax.set_xticks([])
        ax.set_yticks([])
        for nm, (la, lo), (dx, dy) in (("Nakivubo swamp", (0.305, 32.625), (-500, 900)),
                                       ("Kinawataka", (0.318, 32.660), (300, 900)),
                                       ("Murchison Bay", (0.282, 32.652), (0, 0))):
            ux, uy = pyproj.Transformer.from_crs(4326, 32636, always_xy=True).transform(lo, la)
            ax.text(ux + dx, uy + dy, nm, color="white", fontsize=14, fontweight="bold", ha="center",
                    bbox=dict(facecolor="black", alpha=0.35, edgecolor="none", pad=2))
        fig.text(0.97, 0.865, str(yr), fontsize=40, fontweight="bold", color=INK, ha="right", va="top")
        fig.text(0.03, 0.845, f"Green wetland draining to the bay: {wb[yr]:,.0f} ha", fontsize=17, fontweight="bold",
                 color="#2e8b57")
        if yr == 2025:
            fig.text(0.03, 0.065, f"−{100 * (1 - wb[2025] / wb[1986]):.0f}% since 1986", fontsize=16, fontweight="bold",
                     color=RED)
        frames.append(grab(fig))
    frames[0].save(GIFS / "kd_a12_bay_swamps.gif", save_all=True, append_images=frames[1:] + [frames[-1]] * 2,
                   duration=1700, loop=0)
    # still: 1986 and 2025 side by side
    w_, h_ = frames[0].size
    still = Image.new("RGB", (w_ * 2, h_), BG)
    still.paste(frames[0], (0, 0))
    still.paste(frames[-1], (w_, 0))
    still.save(OUT / "x11_bay_swamps_1986_2025.png")
    print("a12 done")


def a13():
    ch = kb.chirps_kla()
    runs = [["2018-12-16", "2018-12-26", "2018-12-31", "2019-01-05"],
            ["2020-11-30", "2020-12-05", "2020-12-10", "2020-12-15", "2020-12-20"]]
    comp = xr.open_dataset(KD / "sat_bay_s2_dry.nc")
    grey = np.clip(np.dstack([comp.B04, comp.B03, comp.B02]).mean(2) / 0.15, 0, 1)
    ext = [float(comp.x.min()), float(comp.x.max()), float(comp.y.min()), float(comp.y.max())]
    frames = []
    for run in runs:
        for dd in run:
            T = kb.scene_turb(dd)
            t = pd.Timestamp(dd)
            r3 = float(ch[t - pd.Timedelta(days=3):t - pd.Timedelta(days=1)].sum())
            fig = plt.figure(figsize=(10.8, 10.8), dpi=100)
            header(fig, "Kampala's water reaching the lake", "Murkiness of Murchison Bay on clear days in the short rains "
                   "(darker = murkier)", "Imagery: Copernicus Sentinel-2 (ESA) · turbidity: Dogliotti et al. 2015 · "
                   "rain: CHIRPS v2.0, Greater Kampala")
            ax = fig.add_axes([0.03, 0.1, 0.8, 0.74])
            ax.imshow(grey, cmap="Greys_r", extent=ext, vmin=0, vmax=1.4, alpha=0.55)
            im = ax.imshow(T.values, cmap="YlOrBr", vmin=4, vmax=24,
                           extent=[float(T.x.min()), float(T.x.max()), float(T.y.min()), float(T.y.max())])
            ax.set_xlim(456000, 465500)
            ax.set_ylim(22200, 34500)
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)
            ax.text(459000, 33500, "Kampala's channels\nenter here", color="white", fontsize=12, fontweight="bold",
                    ha="center", bbox=dict(facecolor="black", alpha=0.35, edgecolor="none", pad=2))
            cax = fig.add_axes([0.86, 0.3, 0.025, 0.4])
            cb = fig.colorbar(im, cax=cax)
            cb.set_label("turbidity (FNU)", fontsize=12)
            fig.text(0.97, 0.875, t.strftime("%-d %b %Y"), fontsize=30, fontweight="bold", color=INK, ha="right",
                     va="top")
            fig.text(0.97, 0.80, f"rain in previous\n3 days: {r3:.0f} mm", fontsize=15, color=INK, ha="right", va="top")
            bx = fig.add_axes([0.86, 0.73, 0.11, 0.025])
            bx.barh([0], [min(r3, 40)], color="#1d6a8a", height=1)
            bx.set_xlim(0, 40)
            bx.axis("off")
            frames.append(grab(fig))
    frames[0].save(GIFS / "kd_a13_bay_plumes.gif", save_all=True, append_images=frames[1:] + [frames[-1]],
                   duration=1400, loop=0)
    print("a13 done")


def a14():
    p = pd.read_csv(RES / "kd_bay_landsat_periods.csv")
    lab = ["1984–95", "1996–2005", "2006–15", "2016–26"]
    ex = 100 * (p.ratio_median - 1)
    frames = []
    for k in range(1, len(p) + 1):
        fig = plt.figure(figsize=(10.8, 10.8), dpi=100)
        header(fig, "As the swamps went, the bay got murkier", "How much murkier the water is where Kampala's channels "
               "enter, vs the open lake", "Data: NASA/USGS Landsat 1984–2026 (179 images) · wetland: Landsat on valley "
               "floors (Copernicus GLO-30)")
        ax = fig.add_axes([0.08, 0.14, 0.88, 0.62])
        ax.bar(range(k), ex[:k], color=[RED] * k, width=0.62)
        if k >= 1:
            ax.patches[0].set_alpha(0.45)
        for i in range(k):
            ax.text(i, ex[i] + 1.5, f"+{ex[i]:.0f}%", ha="center", fontsize=24, fontweight="bold", color=INK)
            ax.text(i, -11, f"{p.wetland_ha_mid[i]:,.0f} ha of swamp", ha="center", va="top", fontsize=13,
                    color="#2e8b57", fontweight="bold")
        ax.set_xlim(-0.6, len(p) - 0.4)
        ax.set_ylim(-20, ex.max() * 1.25)
        for i in range(len(p)):
            ax.text(i, -3, lab[i], ha="center", va="top", fontsize=16, color=INK if i < k else "#bbb")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.axhline(0, color="#ccc", lw=1)
        ax.text(0, ex[0] / 2, "few\nimages", ha="center", va="center", fontsize=11, color="white")
        frames.append(grab(fig))
    frames[0].save(GIFS / "kd_a14_bay_murkier.gif", save_all=True, append_images=frames[1:] + [frames[-1]] * 3,
                   duration=1300, loop=0)
    print("a14 done")


if __name__ == "__main__":
    for f in sys.argv[1:] or ["a12", "a13", "a14"]:
        globals()[f]()
