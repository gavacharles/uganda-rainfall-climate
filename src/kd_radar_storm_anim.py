"""Animated radar view of the 10-12 October 2026 storm weekend -> figures/kampala_drainage/animations/kd_a10_radar_storm.mp4/.gif

Dry-season reference -> Sun 11 Oct 19:04 -> Mon 12 Oct 06:35 (Sentinel-1 VV, 10 m), newly wet ground pulsing in cyan,
camera flying into Lubigi-Bwaise and Kinawataka-Banda and back out. Same detection rule as the still maps (kd10, kd10b).
"""
import geopandas as gpd
import imageio.v2 as iio
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyproj
import xarray as xr
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from scipy import ndimage

from common import CREDIT, FIG, ROOT

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage" / "animations"
BG = "#0f1419"
STEP = 2  # 20 m display grid


def prep(f):
    d = xr.open_dataset(KD / f).isel(x=slice(None, None, STEP), y=slice(None, None, STEP))
    full = xr.open_dataset(KD / f)
    share = float((((full.vv_now - full.vv_ref) < -3) & (full.vv_now < -15) & (full.vv_ref > -16)).mean()) * 100
    wet = ((d.vv_now - d.vv_ref) < -3) & (d.vv_now < -15) & (d.vv_ref > -16)
    wet = ndimage.binary_dilation(wet.values, iterations=1)  # enlarged for visibility only
    return d, wet, share


def main():
    d1, w1, sh1 = prep("sat_s1.nc")
    d2, w2, sh2 = prep("sat_s1_20261012.nc")
    ext = [float(d1.x.min()), float(d1.x.max()), float(d1.y.min()), float(d1.y.max())]
    org = "upper" if float(d1.y[0]) > float(d1.y[-1]) else "lower"
    ref = np.nan_to_num(d1.vv_ref.values, nan=-25)
    v1 = np.nan_to_num(d1.vv_now.values, nan=-25)
    v2 = np.nan_to_num(d2.vv_now.values, nan=-25)
    if v2.shape != v1.shape:  # same bbox/crs/resolution; trim any one-pixel mismatch
        h, w = min(v1.shape[0], v2.shape[0]), min(v1.shape[1], v2.shape[1])
        ref, v1, v2, w1, w2 = ref[:h, :w], v1[:h, :w], v2[:h, :w], w1[:h, :w], w2[:h, :w]
    s = gpd.read_file(KD / "segments.gpkg").to_crs(32636)
    fl = s[s.up_km2 >= 2]
    hs = pd.read_csv(KD / "flood_hotspots.csv")
    hp = gpd.GeoSeries(gpd.points_from_xy(hs.lon, hs.lat), crs=4326).to_crs(32636)
    tf = pyproj.Transformer.from_crs(4326, 32636, always_xy=True)
    Z = {"city": ((ext[0] + ext[1]) / 2, (ext[2] + ext[3]) / 2, ext[1] - ext[0]),
         "lubigi": (*tf.transform(32.562, 0.350), 5200), "kina": (*tf.transform(32.632, 0.336), 5200)}

    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor=BG)
    ax = fig.add_axes([0, 0.075, 1, 0.80])
    ax.set_facecolor(BG)
    cm = LinearSegmentedColormap.from_list("rb", ["#000000", "#2b3440", "#9fb0bf", "#ffffff"])
    im = ax.imshow(ref, cmap=cm, vmin=-24, vmax=0, extent=ext, origin=org, interpolation="bilinear")
    wl = ax.imshow(np.full(ref.shape, np.nan), cmap=LinearSegmentedColormap.from_list("c", ["#00e5ff", "#00e5ff"]), vmin=0, vmax=1,
                   extent=ext, origin=org, interpolation="nearest", alpha=0.0)
    fl.plot(ax=ax, color="#ff9f1c", lw=0.9, zorder=4)
    hp.plot(ax=ax, marker="o", facecolor="none", edgecolor="#ffe600", markersize=60, lw=1.4, zorder=5)
    ax.set_axis_off()
    asp = (0.80 * 7.2) / 12.8
    fig.text(0.015, 0.965, "Kampala's storm weekend, seen by radar", fontsize=19, fontweight="bold", color="white", va="top")
    sub = fig.text(0.015, 0.915, "", fontsize=12, color="#b9c2c9", va="top")
    stamp = fig.text(0.985, 0.965, "", fontsize=19, fontweight="bold", color="#00e5ff", va="top", ha="right")
    note = fig.text(0.985, 0.915, "", fontsize=11, color="#ffffff", va="top", ha="right")
    fig.text(0.015, 0.03, "Orange: main channels · yellow circles: reported flood hotspots · cyan: ground newly water-dark vs the "
             "dry season", fontsize=9.5, color="#b9c2c9")
    fig.text(0.015, 0.008, "Radar: ESA Copernicus Sentinel-1 RTC (Microsoft Planetary Computer) · channels: © OpenStreetMap "
             "contributors · hotspots: KCCA/NEMA lists, news and local reports", fontsize=7.5, color="#8a959c")
    fig.text(0.985, 0.012, CREDIT, fontsize=11, fontweight="bold", color="white", ha="right")

    frames = []
    W = iio.get_writer(str(OUT / "kd_a10_radar_storm.mp4"), fps=15, quality=8, macro_block_size=8)

    def cam(a, b, t):
        t = t * t * (3 - 2 * t)
        x, y, w = [p + (q - p) * t for p, q in zip(Z[a], Z[b])]
        ax.set_xlim(x - w / 2, x + w / 2)
        ax.set_ylim(y - w * asp / 2, y + w * asp / 2)

    def shot():
        fig.canvas.draw()
        fr = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
        W.append_data(fr)
        frames.append(fr)

    def scene(n, img=None, wet=None, alpha=0.0, za="city", zb="city", s_=None, st=None, nt=None, pulse=False, blend=None):
        for k in range(n):
            t = k / max(n - 1, 1)
            if blend is not None:
                a_, b_ = blend
                im.set_data(a_ * (1 - t) + b_ * t)
            elif img is not None:
                im.set_data(img)
            if wet is not None:
                wl.set_data(np.where(wet, 1.0, np.nan))
                wl.set_alpha(alpha * (0.55 + 0.45 * abs(np.sin(k / 4))) if pulse else alpha * t if alpha else 0)
            cam(za, zb, t)
            if s_ is not None: sub.set_text(s_)
            if st is not None: stamp.set_text(st)
            if nt is not None: note.set_text(nt)
            shot()

    SUN, MON = "Sun 11 Oct · 19:04", "Mon 12 Oct · 06:35"
    scene(30, img=ref, s_="Dry season (June-September median): what radar normally sees", st="Dry season", nt="")
    scene(25, blend=(ref, v1), s_="Sunday's storm hit before dawn: Lubigi, Kinawataka and Banda flooded", st=SUN)
    scene(20, img=v1, wet=w1, alpha=1.0, nt=f"newly wet: {sh1:.2f}% of the area")
    scene(40, img=v1, wet=w1, alpha=1.0, za="city", zb="lubigi", pulse=True, s_="Lubigi - Bwaise - Kalerwe, about 13 hours later")
    scene(30, img=v1, wet=w1, alpha=1.0, za="lubigi", zb="lubigi", pulse=True,
          nt="no standing water left along the channel")
    scene(40, img=v1, wet=w1, alpha=1.0, za="lubigi", zb="kina", pulse=True, s_="Kinawataka - Banda - Kyambogo")
    scene(25, blend=(v1, v2), za="kina", zb="kina", st=MON, s_="Monday at dawn, a second satellite pass", nt="")
    scene(30, img=v2, wet=w2, alpha=1.0, za="kina", zb="kina", pulse=True, nt=f"newly wet: {sh2:.2f}% of the area")
    scene(40, img=v2, wet=w2, alpha=1.0, za="kina", zb="city", pulse=True,
          s_="The floods had come and gone within hours: too fast for any satellite to catch", nt="")
    scene(35, img=v2, wet=w2, alpha=1.0, za="city", zb="city", pulse=True,
          s_="To track Kampala's floods: rain gauges, sensors on key culverts, and reports from residents")
    W.close()
    plt.close(fig)
    gif = [Image.fromarray(f).resize((720, 405), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE) for f in frames[::2]]
    gif[0].save(OUT / "kd_a10_radar_storm.gif", save_all=True, append_images=gif[1:], duration=133, loop=0)
    print("frames", len(frames), "seconds", round(len(frames) / 15, 1))


if __name__ == "__main__":
    main()
