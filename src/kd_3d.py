"""Kampala drainage study, part 10: cinematic 3D scenes (PyVista, off-screen) -> figures/kampala_drainage/3d/.

water    "Where the water goes": Copernicus 30 m terrain (3x vertical exaggeration) draped with Esri World Imagery;
         a water surface rises 0 -> 3 m above the nearest drain (HAND) through the Lubigi, Bwaise, Nakivubo and
         Lugogo valleys while the camera orbits; counter of buildings on the flooded ground. An illustration of
         which ground floods first - not a flood forecast or a hydraulic model.
people   population on low ground (GHS-POP, HAND < 2 m within 150 m of a channel) as 3D columns, 1975 -> 2030.
Each writes an MP4, a GIF and a four-panel still.
"""
import sys

import contextily as ctx
import geopandas as gpd
import imageio_ffmpeg
import numpy as np
import pyvista as pv
import rasterio
import xarray as xr
from rasterio.windows import from_bounds

from common import CREDIT, FIG, PROC, ROOT

pv.OFF_SCREEN = True
KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage" / "3d"
OUT.mkdir(parents=True, exist_ok=True)
BOX = (32.535, 0.300, 32.625, 0.375)  # lon0, lat0, lon1, lat1: Lubigi-Bwaise-Kalerwe-Nakivubo-Kitante-Lugogo
VEX = 3.0
SRC = ("Terrain: Copernicus GLO-30 DEM · imagery: Esri World Imagery (Esri, Maxar, Earthstar Geographics) · "
       "buildings: Microsoft · channels: © OpenStreetMap contributors")
LABELS = [("Bwaise", 0.352, 32.562), ("Kalerwe", 0.3545, 32.5785), ("Lubigi channel", 0.343, 32.545),
          ("Nakivubo channel", 0.316, 32.583), ("Kisenyi", 0.311, 32.570), ("Lugogo", 0.327, 32.604),
          ("Kololo hill", 0.333, 32.595), ("Makerere hill", 0.335, 32.567), ("Mulago", 0.340, 32.578)]


def terrain():
    with rasterio.open(PROC / "kampala_dem.tif") as r:
        w = from_bounds(*BOX, r.transform)
        dem = r.read(1, window=w).astype(float)
        tr = r.window_transform(w)
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand = r.read(2, window=from_bounds(*BOX, r.transform)).astype(float)
    H, W = dem.shape
    lon = tr.c + tr.a * (np.arange(W) + 0.5)
    lat = tr.f + tr.e * (np.arange(H) + 0.5)
    kx = 111320 * np.cos(np.deg2rad(lat.mean()))
    X, Y = np.meshgrid((lon - lon[0]) * kx, (lat - lat[-1]) * 110574)
    return dem, hand[:H, :W], lon, lat, X, Y, kx


def imagery(lon, lat):
    f = KD / "img_3d_box.npz"
    if f.exists():
        d = np.load(f)
        return d["img"], d["ext"]
    img, ext = ctx.bounds2img(lon.min(), lat.min(), lon.max(), lat.max(), zoom=16, source=ctx.providers.Esri.WorldImagery, ll=True)
    img, ext = ctx.warp_tiles(img, ext, t_crs="EPSG:4326")
    np.savez_compressed(f, img=img, ext=np.array(ext))
    return img, np.array(ext)


def surface(dem, X, Y, lon, lat):
    z = dem * VEX
    g = pv.StructuredGrid(X, Y, z)
    img, ext = imagery(lon, lat)
    LO, LA = np.meshgrid(lon, lat)
    u = (LO - ext[0]) / (ext[1] - ext[0])
    v = (LA - ext[2]) / (ext[3] - ext[2])
    g.active_texture_coordinates = np.c_[u.ravel(order="F"), v.ravel(order="F")]
    tex = pv.Texture(np.ascontiguousarray(img[:, :, :3]))
    return g, tex


def label_points(lon, lat, X, Y, dem, kx):
    pts, names = [], []
    for n, la, lo in LABELS:
        i = np.abs(lat - la).argmin()
        j = np.abs(lon - lo).argmin()
        pts.append([X[i, j], Y[i, j], dem[i, j] * VEX + 60])
        names.append(n)
    return np.array(pts), names


def font(sz, bold=False):
    from PIL import ImageFont
    import matplotlib
    d = matplotlib.get_data_path() + "/fonts/ttf/"
    return ImageFont.truetype(d + ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), sz)


def compose(img, title, sub, count, count_color, source=None):
    """Put the 3D render between a header band (title, subtitle, live counter) and a footer band (sources, credit)
    so no text ever sits on the scene."""
    from PIL import Image, ImageDraw
    import textwrap
    im = Image.fromarray(img)
    W_, H_ = im.size
    f = W_ / 1280
    head, foot = int(112 * f), int(46 * f)
    can = Image.new("RGB", (W_, H_ + head + foot), "#0f1419")
    can.paste(im, (0, head))
    d = ImageDraw.Draw(can)
    d.text((int(18 * f), int(10 * f)), title, font=font(int(26 * f), True), fill="white")
    d.text((int(18 * f), int(46 * f)), sub, font=font(int(15 * f)), fill="#b9c2c9")
    d.text((int(18 * f), int(72 * f)), count, font=font(int(20 * f), True), fill=count_color)
    cr = "Credit: Gava Charles"
    fc = font(int(17 * f), True)
    cw = d.textlength(cr, font=fc)
    d.text((W_ - cw - int(14 * f), H_ + head + int(12 * f)), cr, font=fc, fill="white")
    fs = font(max(9, int(12 * f)))
    src = source or SRC
    width = int((W_ - cw - int(50 * f)) / (6.6 * f * max(9, int(12 * f)) / 12))
    lines = textwrap.wrap(src, max(40, width))
    for i, ln in enumerate(lines[:2]):
        d.text((int(18 * f), H_ + head + int(6 * f) + i * int(16 * f)), ln, font=fs, fill="#9aa4ab")
    return can


def plotter(size=(1280, 760)):
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("#0f1419")
    p.enable_eye_dome_lighting() if False else None
    return p


def overlay_text(p, title, sub):
    W_, H_ = p.window_size
    f = H_ / 760
    p.add_text(title, position=(18, H_ - int(48 * f)), font_size=max(9, int(15 * f)), color="white", name="title")
    p.add_text(sub, position=(18, H_ - int(76 * f)), font_size=max(7, int(9 * f)), color="#b9c2c9", name="sub")
    p.add_text(SRC, position=(18, 10), font_size=7, color="#9aa4ab", name="src")
    p.add_text(CREDIT, position="lower_right", font_size=10, color="white", name="credit")


def orbit_camera(p, cx, cy, cz, r, ang, elev=0.55):
    p.camera.position = (cx + r * np.cos(ang), cy + r * np.sin(ang), cz + r * elev)
    p.camera.focal_point = (cx, cy, cz)
    p.camera.up = (0, 0, 1)


def water():
    dem, hand, lon, lat, X, Y, kx = terrain()
    g, tex = surface(dem, X, Y, lon, lat)
    drain = dem - hand  # elevation of the nearest drainage line
    b = gpd.read_parquet(KD / "ms_buildings.parquet").cx[BOX[0]:BOX[2], BOX[1]:BOX[3]]
    c = b.geometry.centroid
    bi = np.abs(lat[:, None] - c.y.values[None, :]).argmin(0)
    bj = np.abs(lon[:, None] - c.x.values[None, :]).argmin(0)
    bh = hand[bi, bj]
    levels = np.r_[np.linspace(0.05, 3.0, 48), [3.0] * 14]
    s = gpd.read_file(KD / "segments.gpkg").cx[BOX[0]:BOX[2], BOX[1]:BOX[3]]
    s = s[s.up_km2 >= 2]
    lines = []
    for geom in s.geometry:
        xy = np.asarray(geom.coords)
        jj = np.abs(lon[:, None] - xy[:, 0][None, :]).argmin(0)
        ii = np.abs(lat[:, None] - xy[:, 1][None, :]).argmin(0)
        pts = np.c_[(xy[:, 0] - lon[0]) * kx, (xy[:, 1] - lat[-1]) * 110574, dem[ii, jj] * VEX + 4]
        lines.append(pv.lines_from_points(pts))
    chan = lines[0].merge(lines[1:]) if len(lines) > 1 else lines[0]
    lp, ln = label_points(lon, lat, X, Y, dem, kx)
    cx, cy, cz = X.mean(), Y.mean(), np.nanmean(dem) * VEX
    rad = max(X.max(), Y.max()) * 0.95

    def frame(p, h, ang):
        wz = np.where(hand < h, (drain + h) * VEX + 0.5, dem * VEX - 0.5)  # dry vertices hug the ground: no walls
        wg = pv.StructuredGrid(X, Y, wz)
        wg["wet"] = (hand < h).ravel(order="F").astype(float)
        wet = wg.threshold(0.5, scalars="wet", all_scalars=True)
        p.add_mesh(g, texture=tex, name="terrain", smooth_shading=True)
        if wet.n_cells:
            p.add_mesh(wet, color="#2f9bff", opacity=0.72, name="water", smooth_shading=True, specular=0.6)
        p.add_mesh(chan, color="#7fdcff", line_width=2, name="chan")
        p.add_point_labels(lp, ln, font_size=max(9, int(12 * p.window_size[1] / 640)), text_color="white",
                           shape="rounded_rect", shape_color="#0f1419", shape_opacity=0.65, show_points=False,
                           always_visible=True, name="labels")
        n = int((bh < h).sum())
        orbit_camera(p, cx, cy, cz, rad, ang)
        return n

    import imageio.v2 as iio
    from PIL import Image
    T = "Where the water goes: Kampala's valleys filling up"
    S = "Land below each water level above the nearest drain - which ground floods first. Illustration, not a flood forecast. Terrain 3x."
    p = plotter((1280, 640))
    mp4 = iio.get_writer(str(OUT / "kd3d_water_rising.mp4"), fps=10, quality=7, macro_block_size=8)
    gif = []
    for k, h in enumerate(levels):
        n = frame(p, h, -2.2 + 0.9 * k / len(levels))
        can = compose(p.screenshot(return_img=True), T, S, f"Water {h:.1f} m above the drains  ·  {n:,} buildings on flooded ground", "#7fdcff")
        mp4.append_data(np.asarray(can))
        if k % 2 == 0:
            gif.append(can.resize((800, int(can.height * 800 / can.width)), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE))
    mp4.close()
    p.close()
    gif[0].save(OUT / "kd3d_water_rising.gif", save_all=True, append_images=gif[1:], duration=125, loop=0)
    shots = []
    p = plotter((960, 480))
    for h in (0.5, 1.0, 2.0, 3.0):
        n = frame(p, h, -1.75)
        shots.append(compose(p.screenshot(return_img=True), f"Water {h:.1f} m above the drains",
                             "Illustration of which ground floods first - not a flood forecast",
                             f"{n:,} buildings on flooded ground", "#7fdcff"))
    p.close()
    W_, H_ = shots[0].size
    sheet = Image.new("RGB", (W_ * 2, H_ * 2))
    for i_, im in enumerate(shots):
        sheet.paste(im, ((i_ % 2) * W_, (i_ // 2) * H_))
    sheet.save(OUT / "kd3d_water_rising_panels.png")
    print("buildings on flooded ground at 0.5/1/2/3 m:",
          [int((bh < h).sum()) for h in (0.5, 1.0, 2.0, 3.0)], "of", len(bh))


def columns(base, heights, half=38.0):
    """Square columns (one per cell) as a single mesh: 8 corners and 6 quads each."""
    n = len(base)
    cx = np.array([-1, 1, 1, -1, -1, 1, 1, -1]) * half
    cy = np.array([-1, -1, 1, 1, -1, -1, 1, 1]) * half
    cz = np.array([0, 0, 0, 0, 1, 1, 1, 1], float)
    pts = np.empty((n, 8, 3))
    pts[:, :, 0] = base[:, [0]] + cx
    pts[:, :, 1] = base[:, [1]] + cy
    pts[:, :, 2] = base[:, [2]] + cz[None, :] * np.maximum(heights, 0.5)[:, None]
    quads = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
    off = (np.arange(n) * 8)[:, None, None]
    faces = np.concatenate([np.full((n, 6, 1), 4), quads[None] + off], axis=2).ravel()
    return pv.PolyData(pts.reshape(-1, 3), faces)


def people():
    import shapely
    dem, hand, lon, lat, X, Y, kx = terrain()
    g, tex = surface(dem, X, Y, lon, lat)
    pop = xr.open_dataarray(PROC / "kampala_ghs_pop.nc").sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    PLO, PLA = np.meshgrid(pop.lon.values, pop.lat.values)
    ii = np.abs(lat[:, None] - PLA.ravel()[None, :]).argmin(0)
    jj = np.abs(lon[:, None] - PLO.ravel()[None, :]).argmin(0)
    ph = hand[ii, jj]
    s = gpd.read_file(KD / "segments.gpkg").to_crs(32636)
    fl = s[s.up_km2 >= 0.25]
    pts = gpd.GeoSeries(gpd.points_from_xy(PLO.ravel(), PLA.ravel()), crs=4326).to_crs(32636).values
    near = np.zeros(len(pts), bool)
    near[np.unique(shapely.STRtree(pts).query(fl.geometry.values, predicate="dwithin", distance=150)[1])] = True
    sel = near & (ph < 2)
    base = np.c_[(PLO.ravel() - lon[0]) * kx, (PLA.ravel() - lat[-1]) * 110574, dem[ii, jj] * VEX][sel]
    epochs = [int(e) for e in pop.epoch.values]
    vals = np.nan_to_num(pop.values.reshape(len(epochs), -1)[:, sel])
    lp, ln = label_points(lon, lat, X, Y, dem, kx)
    cx, cy, cz = X.mean(), Y.mean(), np.nanmean(dem) * VEX
    rad = max(X.max(), Y.max()) * 0.95
    scale = 4.0  # metres of column per resident (100 m cell)

    def frame(p, k_float, ang):
        k0 = int(np.floor(k_float))
        k1 = min(k0 + 1, len(epochs) - 1)
        t = k_float - k0
        v = vals[k0] * (1 - t) + vals[k1] * t
        glyphs = columns(base, v * scale)
        glyphs["residents"] = np.repeat(v, 8)
        p.add_mesh(g, texture=tex, name="terrain", smooth_shading=True)
        p.add_mesh(glyphs, scalars="residents", cmap="plasma", clim=(0, 400), name="cols", show_scalar_bar=False)
        p.add_point_labels(lp, ln, font_size=max(9, int(12 * p.window_size[1] / 640)), text_color="white",
                           shape="rounded_rect", shape_color="#0f1419", shape_opacity=0.65, show_points=False,
                           always_visible=True, name="labels")
        yr = epochs[k0] + (epochs[k1] - epochs[k0]) * t
        orbit_camera(p, cx, cy, cz, rad, ang, elev=0.6)
        return yr, float(v.sum())

    import imageio.v2 as iio
    from PIL import Image
    T = "People living where the water goes, 1975-2030"
    S = "Columns: residents per 100 m cell on low ground (< 2 m above the drain, within 150 m of a channel). 2025-2030 projected."
    src = "Population: JRC GHS-POP R2023A · terrain: Copernicus GLO-30 DEM · imagery: Esri World Imagery (Esri, Maxar, Earthstar Geographics) · channels: © OpenStreetMap contributors"
    p = plotter((1280, 640))
    mp4 = iio.get_writer(str(OUT / "kd3d_people_low_ground.mp4"), fps=10, quality=7, macro_block_size=8)
    gif = []
    nf = 70
    for k in range(nf + 12):
        kf = min(k / nf * (len(epochs) - 1), len(epochs) - 1)
        yr, tot = frame(p, kf, -2.0 + 0.8 * min(k, nf) / nf)
        can = compose(p.screenshot(return_img=True), T, S,
                      f"{yr:.0f}{' (projected)' if yr > 2020 else ''}  ·  {tot:,.0f} people on low ground in this view",
                      "#ffb703", src)
        mp4.append_data(np.asarray(can))
        if k % 2 == 0:
            gif.append(can.resize((800, int(can.height * 800 / can.width)), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE))
    mp4.close()
    p.close()
    gif[0].save(OUT / "kd3d_people_low_ground.gif", save_all=True, append_images=gif[1:], duration=125, loop=0)
    shots = []
    p = plotter((960, 480))
    for e in (1975, 1990, 2010, 2030):
        yr, tot = frame(p, epochs.index(e), -1.6)
        shots.append(compose(p.screenshot(return_img=True), f"People on low ground, {e}{' (projected)' if e > 2020 else ''}",
                             "Residents per 100 m cell < 2 m above the drain, within 150 m of a channel",
                             f"{tot:,.0f} people in this view", "#ffb703", src))
    p.close()
    W_, H_ = shots[0].size
    sheet = Image.new("RGB", (W_ * 2, H_ * 2))
    for i_, im in enumerate(shots):
        sheet.paste(im, ((i_ % 2) * W_, (i_ // 2) * H_))
    sheet.save(OUT / "kd3d_people_low_ground_panels.png")


if __name__ == "__main__":
    for st in sys.argv[1:] or ["water", "people"]:
        globals()[st]()
        print("done", st, flush=True)
