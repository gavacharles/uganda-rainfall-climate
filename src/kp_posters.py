"""Kampala and Uganda posters and animations, in several map styles.

kp01  Greater Kampala in Sentinel-2 false colour (SWIR/NIR/red): built-up hills, wetlands, Lake Victoria
kp02  where Kampala floods in a 10-year storm: screening-model water depth on a greyscale Sentinel-2 base
kp03  Kampala's roads in an ordinary 2-year storm, silted vs clean channels (glowing network)
kp04  Inner Murchison Bay: true colour with satellite turbidity on the water
animations (GIF + MP4 + still):
ka01  Kampala spreads over its valleys, Landsat false colour 1986-2025
ka02  roads going under as the storm grows, 2- to 100-year (glowing network)
ka03  the flood rising, 2- to 100-year storm, on the Sentinel-2 base
Outputs: figures/kampala_posters/, figures/kampala_posters/animations/
"""
import io
import subprocess
import sys

import geopandas as gpd
import imageio_ffmpeg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib import patheffects as pe
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
from PIL import Image
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject

from common import FIG, PROC, ROOT

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_posters"
ANI = OUT / "animations"
OUT.mkdir(exist_ok=True); ANI.mkdir(exist_ok=True)
BOX = (32.45, 0.20, 32.72, 0.42)
TS = [2, 5, 10, 25, 50, 100]
BANNER, RIBBON, INK = "#0b3c73", "#ffc20e", "#0b2545"
TF, BF = "Avenir Next Condensed", "Avenir Next"
CREDIT = "Credit: Gava Charles"
PLACES = {"Kampala centre": (0.3136, 32.5811), "Bwaise": (0.3543, 32.5576), "Nakawa": (0.3290, 32.6150),
          "Kawempe": (0.3800, 32.5600), "Ntinda": (0.3530, 32.6170), "Kireka": (0.3480, 32.6500),
          "Ggaba": (0.2650, 32.6300), "Makindye": (0.2810, 32.5880), "Natete": (0.2990, 32.5350),
          "Kyebando": (0.3600, 32.5800), "Kira": (0.4000, 32.6400), "Munyonyo": (0.2440, 32.6230)}
DEPTH_EDGES = [0.1, 0.2, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 99]
DEPTH_COLS = ["#3ff3f2", "#33c5f5", "#4b8ef0", "#4f5fe3", "#4a2fd6", "#6a1fd0", "#a215d8", "#ff2fd5"]
DEPTH_LABS = ["0.1 – 0.2", "0.2 – 0.5", "0.5 – 1", "1 – 1.5", "1.5 – 2", "2 – 2.5", "2.5 – 3", "> 3"]


# ---------------------------------------------------------------- imagery
def to_grid(ds, bands, B, res, crs="EPSG:32636"):
    x, y = ds.x.values, ds.y.values
    dx = float(x[1] - x[0])
    src = from_origin(x[0] - dx / 2, y[0] + dx / 2, dx, dx)
    W, H = int(round((B[2] - B[0]) / res)), int(round((B[3] - B[1]) / res))
    dst = from_origin(B[0], B[3], res, res)
    out = []
    for b in bands:
        a = np.full((H, W), np.nan, "float32")
        reproject(ds[b].values.astype("float32"), a, src_transform=src, src_crs=crs, dst_transform=dst, dst_crs="EPSG:4326",
                  resampling=Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)
        out.append(a)
    return np.dstack(out), [B[0], B[0] + W * res, B[3] - H * res, B[3]]


def stretch(a, lo=1, hi=99.3, gamma=0.9):
    v = a[np.isfinite(a)]
    p0, p1 = np.percentile(v, [lo, hi])
    return np.clip((np.nan_to_num(a, nan=p0) - p0) / (p1 - p0), 0, 1) ** gamma


def s2(bands, B=BOX, res=0.00018):
    return to_grid(xr.open_dataset(KD / "sat_kampala_s2_2024_26.nc"), bands, B, res)


# ---------------------------------------------------------------- poster furniture
def banner(fig, title, ribbon, width=0.78):
    fig.patches.append(FancyBboxPatch((-0.02, 0.905), width, 0.058, boxstyle="round,pad=0,rounding_size=0.02",
                                      transform=fig.transFigure, fc=BANNER, ec="none", zorder=50))
    fig.text(0.035, 0.934, title.upper(), fontsize=27, fontweight="bold", color="white", va="center", family=TF, zorder=51)
    fig.patches.append(Rectangle((0, 0.872), 0.0075 * len(ribbon) + 0.03, 0.026, transform=fig.transFigure, fc=RIBBON,
                                 ec="none", zorder=50))
    fig.text(0.035, 0.885, ribbon.upper(), fontsize=15.5, fontweight="bold", color=INK, va="center", family=TF, zorder=51)


def locator(fig, lon, lat):
    cx, cy, r = 0.925, 0.89, 0.12
    fig.patches.append(Circle((cx, cy), r, transform=fig.transFigure, fc="#1b2a33", ec="none", alpha=0.62, zorder=50))
    ia = fig.add_axes([cx - 0.035, cy - 0.045, 0.07, 0.1], zorder=52)
    ug = gpd.read_file(PROC / "uganda_adm1.geojson").to_crs(4326).dissolve()
    ug.plot(ax=ia, color="white", lw=0)
    ia.plot(lon, lat, "s", color="#e4002b", ms=4.5)
    ia.set_aspect("equal"); ia.set_axis_off()
    fig.text(cx - 0.074, cy + 0.012, "Kampala\nFlood Watch", color="white", fontsize=10.5, family=TF, ha="center", va="center",
             fontweight="bold", zorder=53)
    d = lambda v, pos, neg: f"{int(abs(v))}° {int(abs(v) % 1 * 60):02d}' {abs(v) * 3600 % 60:02.0f}\" {pos if v >= 0 else neg}"
    fig.text(cx + 0.02, cy - 0.06, f"LATITUDE: {d(lat, 'N', 'S')}\nLONGITUDE: {d(lon, 'E', 'W')}", color="white", fontsize=10,
             family=TF, fontweight="bold", ha="center", va="top", zorder=53, linespacing=1.4)


def legend_box(fig, title, items, x=0.025, y=0.07, w=0.16):
    h = 0.06 + 0.03 * len(items)
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.004", transform=fig.transFigure,
                                      fc="#e9e9e9", ec="none", alpha=0.88, zorder=50))
    fig.text(x + 0.012, y + h - 0.03, title, fontsize=15, family=BF, color="#111", zorder=51, va="center")
    for i, (c, lab) in enumerate(items):
        yy = y + h - 0.07 - i * 0.03
        fig.patches.append(Rectangle((x + 0.014, yy - 0.009), 0.022, 0.018, transform=fig.transFigure, fc=c, ec="#777", lw=0.4,
                                     zorder=51))
        fig.text(x + 0.045, yy, lab, fontsize=13, family=BF, color="#111", va="center", zorder=51)


def scale_north(ax, B, km, colour="white"):
    dx, dy = B[2] - B[0], B[3] - B[1]
    deg = km / 111.32
    xs, ys = B[2] - 0.06 * dx - deg, B[1] + 0.045 * dy
    ax.plot([xs, xs + deg], [ys, ys], color=colour, lw=2.4, zorder=40, solid_capstyle="butt")
    ax.text(xs + deg / 2, ys + 0.01 * dy, f"{km:g} km", color=colour, fontsize=12, family=BF, ha="center", zorder=40)
    ax.annotate("", xy=(xs - 0.025 * dx, ys + 0.03 * dy), xytext=(xs - 0.025 * dx, ys), zorder=40,
                arrowprops=dict(arrowstyle="-|>", color=colour, lw=1.6))


def credit(fig, text, colour="white"):
    fig.text(0.025, 0.012, text, fontsize=10, family=BF, color=colour, zorder=60, va="bottom", linespacing=1.5)
    fig.text(0.975, 0.012, CREDIT, fontsize=12.5, family=BF, fontweight="bold", color=colour, ha="right", va="bottom", zorder=60)


def place(ax, lon, lat, name, colour="white", size=14):
    ax.plot(lon, lat, "o", color=colour, ms=3.5, zorder=30)
    ax.text(lon + 0.0018, lat, name, color=colour, fontsize=size, family=BF, va="center", zorder=30,
            path_effects=[pe.withStroke(linewidth=2.2, foreground="#000000aa")])


def frame(B, width=20):
    fig = plt.figure(figsize=(width, width * (B[3] - B[1]) / (B[2] - B[0])), dpi=110)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    return fig, ax


def save(fig, path, face="black"):
    with plt.rc_context({"savefig.bbox": "standard"}):
        fig.savefig(path, dpi=110, facecolor=face)
    plt.close(fig)
    print("saved", path.name, flush=True)


def grab(fig, face="black"):
    buf = io.BytesIO()
    with plt.rc_context({"savefig.bbox": "standard"}):
        fig.savefig(buf, format="png", dpi=72, facecolor=face)
    plt.close(fig)
    return Image.open(buf).convert("RGB")


def write_anim(frames, name, durations):
    """GIF (≤ 1200 px wide, X-friendly) + MP4 + still of the last frame."""
    w = min(1200, frames[0].width)
    sm = [f.resize((w, round(f.height * w / f.width)), Image.LANCZOS) for f in frames]
    sm[0].save(ANI / f"{name}.gif", save_all=True, append_images=sm[1:], duration=durations, loop=0, optimize=True)
    W, H = sm[0].size
    W, H = W - W % 2, H - H % 2
    proc = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", "10", "-i", "-", "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "21",
                             "-movflags", "+faststart", str(ANI / f"{name}.mp4")], stdin=subprocess.PIPE)
    for f, d in zip(sm, durations):
        b = np.asarray(f.crop((0, 0, W, H))).tobytes()
        for _ in range(max(1, round(d / 100))):
            proc.stdin.write(b)
    proc.stdin.close(); proc.wait()
    frames[-1].save(ANI / f"{name}_still.png")
    print("animation", name, len(frames), "frames", flush=True)


# ---------------------------------------------------------------- road glow
NAVY, DIM, HOT = "#02121f", "#1f6f8b", "#ff3d7f"


def roads():
    p = gpd.read_parquet(KD / "road_pieces.parquet").to_crs(4326)
    lw = p.highway.map({"trunk": 1.4, "primary": 1.2, "secondary": 1.0, "tertiary": 0.8}).fillna(0.35).values
    return p, lw


def glow_panel(ax, p, lw, col, title=None, km_txt=True):
    wet = p[col].values >= 0.3
    p[~wet].plot(ax=ax, color=DIM, lw=lw[~wet], alpha=0.85)
    for w_, a_, c_ in ((7, 0.08, "#ff6fa3"), (4, 0.18, "#ff6fa3"), (2.2, 1.0, HOT)):
        p[wet].plot(ax=ax, color=c_, lw=w_, alpha=a_)
    ax.set_xlim(BOX[0], BOX[2]); ax.set_ylim(BOX[1], BOX[3]); ax.set_aspect("equal"); ax.set_axis_off()
    km = p.len_m.values[wet].sum() / 1000
    if title:
        ax.text(0.5, 1.02, title, transform=ax.transAxes, ha="center", color="#cfe9f2", fontsize=17)
    if km_txt:
        ax.text(0.5, -0.04, f"{km:.0f} km of road under water", transform=ax.transAxes, ha="center", color=HOT, fontsize=22,
                fontweight="bold")
    return km


def kp03():
    p, lw = roads()
    fig = plt.figure(figsize=(20, 10.6), facecolor=NAVY)
    for i, (col, lab) in enumerate((("d2_2020 silted", "Silted channels (as observed)"), ("d2_2020 clean", "Clean channels"))):
        ax = fig.add_axes([0.01 + i * 0.495, 0.08, 0.48, 0.79], facecolor=NAVY)
        glow_panel(ax, p, lw, col, lab)
    fig.text(0.5, 0.955, "Kampala's roads in an ordinary 2-year storm", ha="center", color="#e6f6fb", fontsize=28)
    fig.text(0.012, 0.015, "Roads: © OpenStreetMap contributors · flooding: Kampala drainage screening model (road under ≥ 0.3 m "
             "of water)", color="#7fa9b8", fontsize=10)
    fig.text(0.988, 0.015, CREDIT, ha="right", color="#cfe9f2", fontsize=12.5, fontweight="bold")
    save(fig, OUT / "kp03_kampala_roads_glow.png", NAVY)


def ka02():
    p, lw = roads()
    frames, dur = [], []
    for T in TS:
        fig = plt.figure(figsize=(12, 12.4), facecolor=NAVY)
        ax = fig.add_axes([0.02, 0.07, 0.96, 0.8], facecolor=NAVY)
        km = glow_panel(ax, p, lw, f"d{T}_2020 silted", km_txt=False)
        fig.text(0.5, 0.95, "Kampala's roads as the storm grows", ha="center", color="#e6f6fb", fontsize=24)
        fig.text(0.5, 0.905, "silted channels, as observed", ha="center", color="#7fa9b8", fontsize=14)
        fig.text(0.04, 0.83, f"{T}-year storm", color="#e6f6fb", fontsize=30, fontweight="bold")
        fig.text(0.04, 0.795, f"{km:.0f} km of road under water", color=HOT, fontsize=20, fontweight="bold")
        fig.text(0.02, 0.015, "Roads: © OpenStreetMap contributors · flooding: Kampala drainage screening model", color="#7fa9b8",
                 fontsize=10)
        fig.text(0.98, 0.015, CREDIT, ha="right", color="#cfe9f2", fontsize=12, fontweight="bold")
        frames.append(grab(fig, NAVY)); dur.append(1300 if T < 100 else 3500)
    write_anim(frames, "ka02_kampala_roads_storm", dur)


# ---------------------------------------------------------------- false colour
def kp01():
    B = (32.42, 0.17, 32.76, 0.44)
    fig, ax = frame(B)
    img, ext = s2(("B11", "B08", "B04"), B)
    ax.imshow(np.dstack([stretch(img[..., i]) for i in range(3)]), extent=ext, interpolation="bilinear")
    for n, (la, lo) in PLACES.items():
        place(ax, lo, la, n, size=15)
    ax.text(32.66, 0.235, "Lake Victoria", color="white", fontsize=18, style="italic",
            path_effects=[pe.withStroke(linewidth=2, foreground="#00000088")])
    ax.set_xlim(B[0], B[2]); ax.set_ylim(B[1], B[3]); ax.set_aspect("equal")
    banner(fig, "Kampala's hills built over, its valleys filling", "Copernicus Sentinel-2 false colour · dry seasons 2024–26", 0.74)
    locator(fig, 32.58, 0.31)
    legend_box(fig, "In this image", [("#b06ad6", "built-up"), ("#3fd36b", "vegetation, wetland"), ("#e6a9c3", "bare soil"),
                                      ("#14205a", "water")], y=0.06, w=0.15)
    scale_north(ax, B, 3)
    credit(fig, "Contains modified Copernicus Sentinel-2 data (2024–26), bands 11-8-4 · places: © OpenStreetMap contributors")
    save(fig, OUT / "kp01_kampala_false_colour.png")


ROY = dict(red=(0.0061, 0.9047), nir08=(0.0412, 0.8462), swir16=(0.0254, 0.8937))  # TM/ETM+ -> OLI (Roy et al. 2016)


def landsat_fc(yr, B):
    """Landsat false colour (SWIR, NIR, red) on a common scale for all years: TM/ETM+ harmonised to OLI, Landsat 7
    scan-line gaps (near-zero stripes) filled from the nearest valid pixel, one fixed stretch."""
    from scipy.ndimage import distance_transform_edt
    d = xr.open_dataset(KD / f"sat_landsat_{yr}.nc").load()
    if yr == 2005:  # Landsat 7 SLC-off: thin dark near-horizontal stripes; fill them on the native grid
        from scipy.ndimage import grey_closing
        br = sum(np.nan_to_num(d[b].values) for b in ("swir16", "nir08", "red"))
        cl = grey_closing(br, size=(9, 1))
        stripe = (cl - br) > 0.1 * np.maximum(cl, 1e-3)
        for b in ("swir16", "nir08", "red"):
            v = np.nan_to_num(d[b].values)
            d[b].values[:] = np.where(stripe, grey_closing(v, size=(9, 1)), v)
    img, ext = to_grid(d, ("swir16", "nir08", "red"), B, 0.00027)
    from scipy.ndimage import median_filter
    br = np.nan_to_num(img.sum(-1), nan=0.0)
    gap = ~np.isfinite(img).all(-1) | (img.max(-1) < 0.02) | ((br < 0.6 * median_filter(br, 9)) & (img[..., 1] < 0.12) & (yr == 2005))
    if yr < 2013:
        for i, b in enumerate(("swir16", "nir08", "red")):
            img[..., i] = ROY[b][0] + ROY[b][1] * img[..., i]
    if gap.any():
        idx = distance_transform_edt(gap, return_distances=False, return_indices=True)
        img = img[idx[0], idx[1]]
    lo, hi = np.array([0.04, 0.05, 0.02]), np.array([0.34, 0.42, 0.20])
    return np.clip((img - lo) / (hi - lo), 0, 1) ** 0.9, ext


def built_km2(yr, B):
    g = xr.open_dataset(PROC / "kampala_ghsl_built.nc").built_m2
    e = int(min(g.epoch.values, key=lambda x: abs(x - yr)))
    k = gpd.read_file(KD / "kcca_boundary.geojson").to_crs(4326).union_all()
    v = g.sel(epoch=e)
    LO, LA = np.meshgrid(v.lon.values, v.lat.values)
    import shapely
    m = shapely.contains_xy(k, LO, LA)
    return float(np.nansum(v.values[m]) / 1e6), e


def ka01():
    B = (32.47, 0.22, 32.72, 0.41)
    frames, dur = [], []
    for yr in (1986, 1995, 2005, 2015, 2025):
        fig, ax = frame(B, width=13)
        img, ext = landsat_fc(yr, B)
        ax.imshow(img, extent=ext, interpolation="bilinear")
        k = gpd.read_file(KD / "kcca_boundary.geojson").to_crs(4326)
        k.boundary.plot(ax=ax, color="white", lw=1.2, linestyle="--", alpha=0.8)
        ax.set_xlim(B[0], B[2]); ax.set_ylim(B[1], B[3]); ax.set_aspect("equal")
        for n in ("Kampala centre", "Bwaise", "Nakawa", "Ntinda", "Kireka", "Natete", "Ggaba"):
            la, lo = PLACES[n]
            place(ax, lo, la, n, size=11)
        km2, e = built_km2(yr, B)
        fig.patches.append(FancyBboxPatch((-0.02, 0.9), 0.82, 0.07, boxstyle="round,pad=0,rounding_size=0.02",
                                          transform=fig.transFigure, fc=BANNER, ec="none", zorder=50))
        fig.text(0.035, 0.935, "KAMPALA SPREADS ACROSS ITS HILLS", fontsize=22, fontweight="bold", color="white", va="center",
                 family=TF, zorder=51)
        fig.patches.append(Rectangle((0, 0.852), 0.46, 0.045, transform=fig.transFigure, fc=RIBBON, ec="none", zorder=50))
        fig.text(0.035, 0.875, f"{yr}   ·   {km2:.0f} km² built up in KCCA", fontsize=20, fontweight="bold", color=INK,
                 va="center", family=TF, zorder=51)
        fig.patches.append(FancyBboxPatch((0.015, 0.035), 0.3, 0.13, boxstyle="round,pad=0,rounding_size=0.004",
                                          transform=fig.transFigure, fc="#e9e9e9", ec="none", alpha=0.88, zorder=50))
        for i_, (c_, l_) in enumerate((("#c77ee0", "built-up"), ("#5fe05a", "vegetation, wetland"), ("#101826", "water"))):
            yy = 0.14 - i_ * 0.035
            fig.patches.append(Rectangle((0.028, yy - 0.011), 0.025, 0.022, transform=fig.transFigure, fc=c_, ec="#777", lw=0.4, zorder=51))
            fig.text(0.062, yy, l_, fontsize=12, family=BF, color="#111", va="center", zorder=51)
        fig.text(0.02, 0.012, f"Landsat 5/7/8/9 dry-season composites, false colour (SWIR, NIR, red), one colour scale · built-up: "
                 f"JRC GHSL {e} · dashed: KCCA boundary", fontsize=8.5, color="white", family=BF)
        fig.text(0.98, 0.012, CREDIT, fontsize=10.5, color="white", ha="right", family=BF, fontweight="bold")
        frames.append(grab(fig)); dur.append(1500 if yr < 2025 else 3500)
    write_anim(frames, "ka01_kampala_spreads", dur)


# ---------------------------------------------------------------- flood depth
def depth_cells():
    """Water depth per 30 m cell for each storm: stage of the nearest channel stretch (silted, as observed) minus HAND."""
    f = KD / "depth_cells.npz"
    if f.exists():
        return dict(np.load(f))
    import rasterio
    import shapely
    sys.path.insert(0, str(ROOT / "src"))
    from kd_roads import stage_states
    s = gpd.read_file(KD / "segments.gpkg")
    h = pd.read_parquet(KD / "hydraulics.parquet")
    s = s[s.seg_id.isin(h.seg_id)].set_index("seg_id").loc[h.seg_id].reset_index()
    H = stage_states(s, h)["2020 silted"]
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand, t = r.read(2), r.transform
    rows, cols = np.nonzero((hand < 8) & np.isfinite(hand))
    lon, lat = t.c + t.a * (cols + 0.5), t.f + t.e * (rows + 0.5)
    k = (lon > BOX[0]) & (lon < BOX[2]) & (lat > BOX[1]) & (lat < BOX[3])
    rows, cols, lon, lat = rows[k], cols[k], lon[k], lat[k]
    su = s.to_crs(32636)
    pts = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs=4326).to_crs(32636).values
    pi, si = shapely.STRtree(su.geometry.values).query(pts, predicate="dwithin", distance=200)
    c = pd.DataFrame({"p": pi, "s": si, "d": shapely.distance(pts[pi], su.geometry.values[si])}).sort_values("d").drop_duplicates("p")
    out = dict(rows=rows[c.p.values], cols=cols[c.p.values], seg=c.s.values, hand=hand[rows[c.p.values], cols[c.p.values]],
               H=H, shape=np.array(hand.shape), transform=np.array(t)[:6])
    np.savez_compressed(f, **out)
    return out


def depth_grid(cl, T):
    j = TS.index(T)
    st = cl["H"][cl["seg"], j]
    d = st - cl["hand"]
    g = np.full(tuple(cl["shape"]), np.nan, "float32")
    g[cl["rows"], cl["cols"]] = np.where((st > 0) & (d >= 0.1), d, np.nan)
    a, b, c, dd, e, f = cl["transform"]
    H_, W_ = cl["shape"]
    return g, [c, c + a * W_, f + e * H_, f]


def depth_map(fig, ax, cl, T, B, grey):
    img, ext = grey
    ax.imshow(img, extent=ext, interpolation="bilinear")
    g, gext = depth_grid(cl, T)
    ax.imshow(g, extent=gext, cmap=ListedColormap(DEPTH_COLS), norm=BoundaryNorm(DEPTH_EDGES, 8), interpolation="nearest", alpha=0.92)
    k = gpd.read_file(KD / "kcca_boundary.geojson").to_crs(4326)
    k.boundary.plot(ax=ax, color="white", lw=1.3, linestyle="--", alpha=0.85)
    ax.set_xlim(B[0], B[2]); ax.set_ylim(B[1], B[3]); ax.set_aspect("equal")


def grey_base(B):
    img, ext = s2(("B04", "B03", "B02"), B)
    g = stretch(img.mean(-1), 1, 99.5, 1.0)
    return np.dstack([g, g, g]), ext


def kp02():
    B = (32.47, 0.21, 32.71, 0.42)
    cl = depth_cells()
    grey = grey_base(B)
    fig, ax = frame(B)
    depth_map(fig, ax, cl, 10, B, grey)
    for n, (la, lo) in PLACES.items():
        if B[0] < lo < B[2] and B[1] < la < B[3]:
            place(ax, lo, la, n, size=15)
    banner(fig, "Where Kampala floods in a 10-year storm", "Maximum water depth · today's city, silted channels", 0.8)
    locator(fig, 32.58, 0.31)
    legend_box(fig, "Maximum water depth (m)", list(zip(DEPTH_COLS, DEPTH_LABS)), y=0.065, w=0.18)
    scale_north(ax, B, 2)
    credit(fig, "Flood depth: Kampala drainage screening model (rational method, HAND rating curves, Copernicus GLO-30); "
                "indicative, not for design\nBasemap: contains modified Copernicus Sentinel-2 data (2024–26) · boundary: KCCA · "
                "places: © OpenStreetMap contributors")
    save(fig, OUT / "kp02_kampala_flood_depth_10yr.png")


def ka03():
    B = (32.50, 0.26, 32.66, 0.40)
    cl = depth_cells()
    grey = grey_base(B)
    frames, dur = [], []
    for T in TS:
        fig, ax = frame(B, width=13)
        depth_map(fig, ax, cl, T, B, grey)
        for n in ("Kampala centre", "Bwaise", "Nakawa", "Kawempe", "Ntinda", "Kyebando"):
            la, lo = PLACES[n]
            place(ax, lo, la, n, size=12)
        fig.patches.append(FancyBboxPatch((-0.02, 0.9), 0.84, 0.07, boxstyle="round,pad=0,rounding_size=0.02",
                                          transform=fig.transFigure, fc=BANNER, ec="none", zorder=50))
        fig.text(0.035, 0.935, "KAMPALA: THE FLOOD RISING WITH THE STORM", fontsize=21, fontweight="bold", color="white",
                 va="center", family=TF, zorder=51)
        fig.patches.append(Rectangle((0, 0.855), 0.3, 0.04, transform=fig.transFigure, fc=RIBBON, ec="none", zorder=50))
        fig.text(0.035, 0.875, f"{T}-YEAR STORM", fontsize=22, fontweight="bold", color=INK, va="center", family=TF, zorder=51)
        legend_box(fig, "Water depth (m)", list(zip(DEPTH_COLS, DEPTH_LABS)), y=0.06, w=0.2)
        fig.text(0.02, 0.012, "Screening model, silted channels (indicative) · basemap: contains modified Copernicus Sentinel-2 "
                 "data", fontsize=8.5, color="white", family=BF)
        fig.text(0.98, 0.012, CREDIT, fontsize=10.5, color="white", ha="right", family=BF, fontweight="bold")
        frames.append(grab(fig)); dur.append(1300 if T < 100 else 3500)
    write_anim(frames, "ka03_kampala_flood_rising", dur)


# ---------------------------------------------------------------- Murchison Bay
def kp04(date=None):
    import glob
    d = xr.open_dataset(KD / "sat_bay_s2_dry.nc")
    x, y = d.x.values, d.y.values
    t0 = xr.open_dataset(KD / "bay_turb_2020-12-10.nc")
    ext = [max(float(x.min()), float(t0.x.min())), min(float(x.max()), float(t0.x.max())),
           max(float(y.min()), float(t0.y.min())), min(float(y.max()), float(t0.y.max()))]
    from pyproj import Transformer
    tr = Transformer.from_crs(32636, 4326, always_xy=True)
    lo0, la0 = tr.transform(ext[0], ext[2]); lo1, la1 = tr.transform(ext[1], ext[3])
    B = (lo0, la0, lo1, la1)
    rgb, gext = to_grid(d, ("B04", "B03", "B02"), B, 0.00009)
    rgb = np.dstack([stretch(rgb[..., i], 1, 99.5, 0.85) for i in range(3)])
    files = sorted(glob.glob(str(KD / "bay_turb_*.nc")))
    best, bv = None, -1
    for f in files:
        v = xr.open_dataset(f)
        var = list(v.data_vars)[0]
        m = float(np.nanpercentile(v[var].values, 90))
        if m > bv:
            best, bv = f, m
    f = date and str(KD / f"bay_turb_{date}.nc") or best
    t = xr.open_dataset(f)
    var = list(t.data_vars)[0]
    tg, text_ = to_grid(t, (var,), B, 0.00009)
    fig, ax = frame(B, width=15)
    ax.imshow(rgb, extent=gext, interpolation="bilinear")
    from matplotlib.colors import LogNorm
    v = tg[..., 0][np.isfinite(tg[..., 0])]
    lo_, hi_ = np.percentile(v, [5, 99])
    im = ax.imshow(tg[..., 0], extent=text_, cmap="inferno", norm=LogNorm(max(lo_, 1), hi_), interpolation="bilinear", alpha=0.9)
    for n, (la, lo) in {"Ggaba": (0.2650, 32.6300), "Munyonyo": (0.2440, 32.6230), "Port Bell": (0.2880, 32.6530)}.items():
        if B[0] < lo < B[2] and B[1] < la < B[3]:
            place(ax, lo, la, n, size=15)
    ax.set_xlim(B[0], B[2]); ax.set_ylim(B[1], B[3]); ax.set_aspect("equal")
    day = f.split("bay_turb_")[1][:10]
    banner(fig, "Inner Murchison Bay: where the water is muddiest", f"Copernicus Sentinel-2 · satellite turbidity on {day}", 0.74)
    locator(fig, 32.62, 0.28)
    fig.patches.append(FancyBboxPatch((0.025, 0.06), 0.27, 0.085, boxstyle="round,pad=0,rounding_size=0.004",
                                      transform=fig.transFigure, fc="#e9e9e9", ec="none", alpha=0.9, zorder=50))
    ca = fig.add_axes([0.04, 0.09, 0.24, 0.018], zorder=52)
    cb = fig.colorbar(im, cax=ca, orientation="horizontal")
    tk = [x for x in (10, 15, 20, 30, 50, 100, 200) if lo_ <= x <= hi_]
    cb.set_ticks(tk); cb.set_ticklabels([str(x) for x in tk]); cb.ax.minorticks_off()
    cb.ax.tick_params(colors="#111", labelsize=11)
    fig.text(0.04, 0.122, "Satellite turbidity (FNU)", fontsize=14, family=BF, color="#111", zorder=53)
    scale_north(ax, B, 1)
    credit(fig, "Contains modified Copernicus Sentinel-2 data · turbidity: Dogliotti et al. (2015) algorithm · places: © "
                "OpenStreetMap contributors")
    save(fig, OUT / "kp04_murchison_bay_plume.png")


def ka04():
    """Murchison Bay through the years: every usable Sentinel-2 turbidity scene (at least a quarter of the bay seen), on
    one fixed colour scale so the frames compare, over the dry-season true-colour base."""
    import glob
    from matplotlib.colors import LogNorm
    d = xr.open_dataset(KD / "sat_bay_s2_dry.nc")
    t0 = xr.open_dataset(KD / "bay_turb_2020-12-10.nc")
    ext = [max(float(d.x.min()), float(t0.x.min())), min(float(d.x.max()), float(t0.x.max())),
           max(float(d.y.min()), float(t0.y.min())), min(float(d.y.max()), float(t0.y.max()))]
    from pyproj import Transformer
    tr = Transformer.from_crs(32636, 4326, always_xy=True)
    lo0, la0 = tr.transform(ext[0], ext[2]); lo1, la1 = tr.transform(ext[1], ext[3])
    B = (lo0, la0, lo1, la1)
    rgb, gext = to_grid(d, ("B04", "B03", "B02"), B, 0.00009)
    rgb = np.dstack([stretch(rgb[..., i], 1, 99.5, 0.85) for i in range(3)])
    norm = LogNorm(4, 20)
    frames, dur = [], []
    for f in sorted(glob.glob(str(KD / "bay_turb_*.nc"))):
        t = xr.open_dataset(f)
        var = list(t.data_vars)[0]
        if np.isfinite(t[var].values).mean() < 0.25:  # mostly cloud
            continue
        tg, text_ = to_grid(t, (var,), B, 0.00009)
        day = pd.Timestamp(f.split("bay_turb_")[1][:10])
        med = float(np.nanmedian(tg[..., 0]))
        fig, ax = frame(B, width=13)
        ax.imshow(rgb, extent=gext, interpolation="bilinear")
        im = ax.imshow(tg[..., 0], extent=text_, cmap="inferno", norm=norm, interpolation="bilinear", alpha=0.9)
        for n, (la, lo) in {"Ggaba": (0.2650, 32.6300), "Munyonyo": (0.2440, 32.6230), "Port Bell": (0.2880, 32.6530)}.items():
            if B[0] < lo < B[2] and B[1] < la < B[3]:
                place(ax, lo, la, n, size=13)
        ax.set_xlim(B[0], B[2]); ax.set_ylim(B[1], B[3]); ax.set_aspect("equal")
        banner(fig, "Murchison Bay, scene by scene", f"{day:%d %B %Y}  ·  median turbidity {med:.0f} FNU", 0.86)
        locator(fig, 32.62, 0.28)
        fig.patches.append(FancyBboxPatch((0.025, 0.06), 0.39, 0.1, boxstyle="round,pad=0,rounding_size=0.004",
                                          transform=fig.transFigure, fc="#e9e9e9", ec="none", alpha=0.9, zorder=50))
        ca = fig.add_axes([0.04, 0.085, 0.29, 0.02], zorder=52)
        cb = fig.colorbar(im, cax=ca, orientation="horizontal")
        cb.set_ticks([4, 6, 10, 15, 20]); cb.set_ticklabels(["4", "6", "10", "15", "20+"]); cb.ax.minorticks_off()
        cb.ax.tick_params(colors="#111", labelsize=11)
        fig.text(0.04, 0.128, "Satellite turbidity (FNU), one scale for every frame", fontsize=12, family=BF, color="#111", zorder=53)
        scale_north(ax, B, 1)
        credit(fig, "Contains modified Copernicus Sentinel-2 data · turbidity: Dogliotti et al. (2015) · base: dry-season "
                    "composite · cloud and land masked")
        frames.append(grab(fig)); dur.append(1400)
    dur[-1] = 3000
    write_anim(frames, "ka04_murchison_bay_scenes", dur)


if __name__ == "__main__":
    for fn in sys.argv[1:]:
        globals()[fn]()
