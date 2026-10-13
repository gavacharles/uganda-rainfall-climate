"""Kampala drainage study, part 11: a 3D story film in chapters -> figures/kampala_drainage/3d/kd3d_story.mp4 (+ GIF, stills).

1  A city of hills and swamps     terrain of Greater Kampala rises out of the dark (Copernicus 30 m, 3x relief)
2  Where the rain goes            the drainage catchments light up one by one, named
3  The channels                   the drain network draws itself, coloured by maintenance priority
4  Concrete, 1975 -> 2030         built-up surface spreads over hills and valley floors (JRC GHSL)
5  Water finds the valleys        water rises 0 -> 3 m above the drains (illustration, not a forecast)
6  People in the water's path     residents on low ground as columns, 2030 (JRC GHS-POP)
7  Down into Bwaise               the camera dives to the Lubigi-Bwaise hotspot on satellite imagery
Every frame: header band (chapter, caption, live counter) and footer band (sources, credit) - no text on the scene.
"""
import contextily as ctx
import geopandas as gpd
import imageio.v2 as iio
import numpy as np
import pandas as pd
import pyvista as pv
import rasterio
import xarray as xr
from PIL import Image
from rasterio.windows import from_bounds

from common import PROC, RES, ROOT
from kd_3d import OUT, columns, compose

pv.OFF_SCREEN = True
KD = ROOT / "data" / "kd"
BOX = (32.47, 0.22, 32.70, 0.41)
VEX = 3.0
STEP = 2  # 60 m mesh
SRC = ("Terrain: Copernicus GLO-30 DEM · imagery: Esri World Imagery (Esri, Maxar, Earthstar Geographics) · built-up & "
       "population: JRC GHSL R2023A · channels: © OpenStreetMap contributors · catchments & priority: this study")
SYSTEMS = {"Lubigi": "#4fc3f7", "Nakivubo": "#ff8a65", "Kinawataka": "#ba68c8", "Kansanga": "#81c784",
           "Nalukolongo": "#ffd54f", "Walufumbe": "#f06292"}
PLACES = [("Bwaise", 0.352, 32.562), ("Kalerwe", 0.3545, 32.5785), ("Kololo", 0.333, 32.595), ("Makerere", 0.335, 32.567),
          ("Kisenyi", 0.311, 32.570), ("Lugogo", 0.327, 32.604), ("Nakawa", 0.329, 32.615), ("Ntinda", 0.354, 32.614),
          ("Rubaga", 0.303, 32.553), ("Katwe", 0.297, 32.576), ("Kireka", 0.347, 32.648), ("Nateete", 0.298, 32.532)]


def load():
    with rasterio.open(PROC / "kampala_dem.tif") as r:
        w = from_bounds(*BOX, r.transform)
        dem = r.read(1, window=w).astype(float)[::STEP, ::STEP]
        tr = r.window_transform(w)
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        w2 = from_bounds(*BOX, r.transform)
        cat = r.read(1, window=w2)[::STEP, ::STEP]
        hand = r.read(2, window=w2).astype(float)[::STEP, ::STEP]
    H, W = dem.shape
    cat, hand = cat[:H, :W], hand[:H, :W]
    lon = tr.c + tr.a * STEP * (np.arange(W) + 0.5)
    lat = tr.f + tr.e * STEP * (np.arange(H) + 0.5)
    kx = 111320 * np.cos(np.deg2rad(lat.mean()))
    X, Y = np.meshgrid((lon - lon[0]) * kx, (lat - lat[-1]) * 110574)
    return dict(dem=dem, cat=cat, hand=hand, lon=lon, lat=lat, X=X, Y=Y, kx=kx)


def imagery(lon, lat, zoom=15, name="img_story.npz"):
    f = KD / name
    if f.exists():
        d = np.load(f)
        return d["img"], d["ext"]
    img, ext = ctx.bounds2img(lon.min(), lat.min(), lon.max(), lat.max(), zoom=zoom,
                              source=ctx.providers.Esri.WorldImagery, ll=True)
    img, ext = ctx.warp_tiles(img, ext, t_crs="EPSG:4326")
    np.savez_compressed(f, img=img, ext=np.array(ext))
    return img, np.array(ext)


def textured(G, z):
    g = pv.StructuredGrid(G["X"], G["Y"], z)
    img, ext = imagery(G["lon"], G["lat"])
    LO, LA = np.meshgrid(G["lon"], G["lat"])
    g.active_texture_coordinates = np.c_[((LO - ext[0]) / (ext[1] - ext[0])).ravel(order="F"),
                                         ((LA - ext[2]) / (ext[3] - ext[2])).ravel(order="F")]
    return g, pv.Texture(np.ascontiguousarray(img[:, :, :3]))


def xyz(G, lo, la, dz=0.0):
    i = np.abs(G["lat"][:, None] - np.atleast_1d(la)[None, :]).argmin(0)
    j = np.abs(G["lon"][:, None] - np.atleast_1d(lo)[None, :]).argmin(0)
    return np.c_[(np.atleast_1d(lo) - G["lon"][0]) * G["kx"], (np.atleast_1d(la) - G["lat"][-1]) * 110574,
                 G["dem"][i, j] * VEX + dz]


def ease(t):
    return t * t * (3 - 2 * t)


class Cam:
    """Keyframed orbit camera: (azimuth deg, elevation deg, distance m, focal x, focal y)."""

    def __init__(self, G):
        self.cz = np.nanmean(G["dem"]) * VEX

    def set(self, p, az, el, dist, fx, fy):
        a, e = np.deg2rad(az), np.deg2rad(el)
        p.camera.focal_point = (fx, fy, self.cz)
        p.camera.position = (fx + dist * np.cos(e) * np.cos(a), fy + dist * np.cos(e) * np.sin(a), self.cz + dist * np.sin(e))
        p.camera.up = (0, 0, 1)
        p.camera.view_angle = 30


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def main():
    G = load()
    dem, X, Y = G["dem"], G["X"], G["Y"]
    cxm, cym = X.mean(), Y.mean()
    span = max(X.max(), Y.max())
    cam = Cam(G)
    # layers -------------------------------------------------------------------------------------------------
    names = pd.read_csv(RES / "kampala_catchments.csv").set_index("id").name.dropna()
    s = gpd.read_file(KD / "segments.gpkg").cx[BOX[0]:BOX[2], BOX[1]:BOX[3]]
    s = s[s.up_km2 >= 0.5].copy()
    seg_lines, seg_val, seg_order = [], [], []
    for gm, rp, up in zip(s.geometry, s.risk_pct.fillna(30), s.up_km2):
        xy = np.asarray(gm.coords)
        P = xyz(G, xy[:, 0], xy[:, 1], dz=6)
        seg_lines.append(pv.lines_from_points(P))
        seg_val.append(rp)
        seg_order.append(-up)  # draw big channels first
    order = np.argsort(seg_order)
    for k, ln in enumerate(seg_lines):
        ln["priority"] = np.full(ln.n_points, seg_val[k])
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc")
    cell = (abs(float(np.diff(g.lon).mean())) * 111320 * np.cos(np.deg2rad(0.3))) * (abs(float(np.diff(g.lat).mean())) * 111320)
    epochs = [1975, 1985, 1995, 2005, 2015, 2020, 2025, 2030]
    built = {e: np.clip(g.sel(epoch=e).sel(lat=G["lat"], lon=G["lon"], method="nearest").values / cell, 0, 1) for e in epochs}
    pop = xr.open_dataarray(PROC / "kampala_ghs_pop.nc").sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    PLO, PLA = np.meshgrid(pop.lon.values, pop.lat.values)
    ii = np.abs(G["lat"][:, None] - PLA.ravel()[None, :]).argmin(0)
    jj = np.abs(G["lon"][:, None] - PLO.ravel()[None, :]).argmin(0)
    low = G["hand"][ii, jj] < 2
    p30 = np.nan_to_num(pop.sel(epoch=2030).values.ravel())
    sel = low & (p30 > 20)
    pbase = xyz(G, PLO.ravel()[sel], PLA.ravel()[sel])
    pv30 = p30[sel]
    drain = dem - G["hand"]
    lab_pts = xyz(G, [p[2] for p in PLACES], [p[1] for p in PLACES], dz=90)
    lab_names = [p[0] for p in PLACES]
    cat_pts, cat_names, cat_cols = [], [], []
    for cid, nm in names.items():
        if nm not in SYSTEMS:
            continue
        m = G["cat"] == cid
        if m.sum() < 50:
            continue
        yy, xx = np.nonzero(m)
        k = len(yy) // 2
        cat_pts.append([X[yy[k], xx[k]], Y[yy[k], xx[k]], dem[yy[k], xx[k]] * VEX + 140])
        cat_names.append(nm)
        cat_cols.append(SYSTEMS[nm])
    flat = pv.StructuredGrid(X, Y, dem * VEX)
    tex_mesh, tex = textured(G, dem * VEX)

    p = pv.Plotter(off_screen=True, window_size=(1280, 640))
    p.set_background("#05070c", top="#1c2a44")
    p.add_light(pv.Light(position=(cxm - span, cym - span, 9000), focal_point=(cxm, cym, 0), intensity=0.6))
    mp4 = iio.get_writer(str(OUT / "kd3d_story.mp4"), fps=12, quality=7, macro_block_size=8)
    gif, stills = [], {}
    F = {"n": 0}

    def shoot(title, sub, count, color="#7fdcff", still=None):
        can = compose(p.screenshot(return_img=True), title, sub, count, color, SRC)
        mp4.append_data(np.asarray(can))
        if F["n"] % 4 == 0:
            gif.append(can.resize((600, int(can.height * 720 / can.width)), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE))
        if still:
            stills[still] = can
        F["n"] += 1

    def labels(pts, nms, size=13, color="white", name="labels", bg="#0f1419"):
        p.add_point_labels(pts, nms, font_size=size, text_color=color, shape="rounded_rect", shape_color=bg,
                           shape_opacity=0.7, show_points=False, always_visible=True, name=name)

    def clear(*names_):
        for n_ in names_:
            p.remove_actor(n_)

    # 1 terrain rises ---------------------------------------------------------------------------------------
    T1 = "1  A city of hills and swamps"
    for k in range(36):
        t = ease(k / 35)
        z = dem * VEX * t + np.nanmin(dem) * VEX * (1 - t)
        m = pv.StructuredGrid(X, Y, z)
        m["elev"] = dem.ravel(order="F")
        p.add_mesh(m, scalars="elev", cmap="gist_earth", clim=(1130, 1330), show_scalar_bar=False, name="terrain",
                   smooth_shading=True)
        cam.set(p, *lerp((-120, 55, span * 1.6, cxm, cym), (-110, 32, span * 1.15, cxm, cym), t))
        shoot(T1, "Kampala grew on a ring of hills; the rain drains into swampy valley floors between them. Relief 3x.",
              "Copernicus 30 m terrain", "#c8e6c9", still="1" if k == 35 else None)
    labels(lab_pts, lab_names)
    for k in range(14):
        cam.set(p, -110 + 6 * k / 13, 32, span * 1.15, cxm, cym)
        shoot(T1, "Kampala grew on a ring of hills; the rain drains into swampy valley floors between them. Relief 3x.",
              "Copernicus 30 m terrain", "#c8e6c9")
    # 2 catchments ------------------------------------------------------------------------------------------
    T2 = "2  Where the rain goes: the drainage catchments"
    shown = []
    for i_, (cid, nm) in enumerate([(c, n) for c, n in names.items() if n in SYSTEMS]):
        shown.append(cid)
        cm = np.isin(G["cat"], shown).astype(float)
        col = np.zeros(G["cat"].shape)
        for k_, c_ in enumerate(shown):
            col[G["cat"] == c_] = k_ + 1
        ov = pv.StructuredGrid(X, Y, dem * VEX + 4)
        ov["c"] = np.where(cm > 0, col, np.nan).ravel(order="F")
        ov = ov.threshold(0.5, scalars="c")
        cols = [SYSTEMS[names[c_]] for c_ in shown]
        from matplotlib.colors import ListedColormap
        p.add_mesh(ov, scalars="c", cmap=ListedColormap(cols), clim=(0.5, len(cols) + 0.5), opacity=0.55,
                   show_scalar_bar=False, name="catch")
        idx = [cat_names.index(names[c_]) for c_ in shown if names[c_] in cat_names]
        clear("labels")
        labels(np.array([cat_pts[j] for j in idx]), [cat_names[j] for j in idx], size=15, name="catlab")
        for k in range(10):
            cam.set(p, -104 + 2.2 * (i_ * 10 + k) / 10, 34, span * 1.12, cxm, cym)
            shoot(T2, "Each colour is the land that drains to one of Kampala's main channels.",
                  f"{len(shown)} of {len(SYSTEMS)} channel catchments", "#ffd54f", still="2" if i_ == len(SYSTEMS) - 1 and k == 9 else None)
    # 3 channels ----------------------------------------------------------------------------------------------
    T3 = "3  The channels, coloured by maintenance priority"
    clear("catch", "catlab")
    p.add_mesh(tex_mesh, texture=tex, name="terrain", smooth_shading=True)
    n_all = len(order)
    for k in range(40):
        upto = int(n_all * ease((k + 1) / 40))
        if upto:
            net = pv.merge([seg_lines[j] for j in order[:upto]])
            p.add_mesh(net, scalars="priority", cmap="RdYlBu_r", clim=(0, 100), line_width=3, show_scalar_bar=False,
                       name="net", render_lines_as_tubes=True)
        cam.set(p, *lerp((-90, 34, span * 1.1, cxm, cym), (-60, 40, span * 0.95, cxm, cym), ease(k / 39)))
        shoot(T3, "Drawn from the biggest channels to the smallest drains. Red = highest current maintenance priority.",
              f"{sum(s.length_m.values[order[:upto]]) / 1000:,.0f} km of channel", "#ff8a65", still="3" if k == 39 else None)
    # 4 concrete --------------------------------------------------------------------------------------------
    T4 = "4  Concrete, 1975 to 2030"
    vf = G["hand"] < 3
    for k in range(48):
        ef = ease(k / 47) * (len(epochs) - 1)
        e0, e1 = int(np.floor(ef)), min(int(np.floor(ef)) + 1, len(epochs) - 1)
        b = built[epochs[e0]] * (1 - (ef - e0)) + built[epochs[e1]] * (ef - e0)
        ov = pv.StructuredGrid(X, Y, dem * VEX + 3)
        ov["b"] = np.where(b > 0.35, b, np.nan).ravel(order="F")
        ov["v"] = np.where(vf, 1.0, 0.0).ravel(order="F")
        th = ov.threshold(0.35, scalars="b")
        if th.n_cells:
            p.add_mesh(th, scalars="b", cmap="YlOrRd", clim=(0.35, 0.8), opacity=0.75, show_scalar_bar=False, name="built")
        yr = epochs[e0] + (epochs[e1] - epochs[e0]) * (ef - e0)
        share = float((b * vf).sum() / vf.sum() * 100)
        cam.set(p, -60 + 30 * k / 47, 40, span * 0.95, cxm, cym)
        shoot(T4, "Yellow-red: densely built land, over 35% roofs and paving (JRC GHSL; 2025 and 2030 projected). Every roof and road sheds rain straight "
                  "into the channels.", f"{yr:.0f}  ·  valley floors built over: {share:.0f}%", "#ffb74d",
              still="4" if k == 47 else None)
    # 5 water -----------------------------------------------------------------------------------------------
    T5 = "5  Water finds the valleys"
    clear("built")
    for k in range(44):
        h = 0.1 + 2.9 * ease(k / 43)
        wz = np.where(G["hand"] < h, (drain + h) * VEX + 1.0, dem * VEX - 1.0)
        wg = pv.StructuredGrid(X, Y, wz)
        wg["wet"] = (G["hand"] < h).ravel(order="F").astype(float)
        wet = wg.threshold(0.5, scalars="wet", all_scalars=True)
        if wet.n_cells:
            p.add_mesh(wet, color="#2f9bff", opacity=0.75, name="water", smooth_shading=True, specular=0.7)
        cam.set(p, -30 + 25 * k / 43, 36, span * 0.9, cxm, cym)
        shoot(T5, "Land below each level above the nearest drain: the ground that floods first. Illustration, not a "
                  "flood forecast.", f"water {h:.1f} m above the drains", "#7fdcff", still="5" if k == 43 else None)
    # 6 people ----------------------------------------------------------------------------------------------
    T6 = "6  People in the water's path (2030)"
    for k in range(40):
        t = ease(k / 39)
        cols_mesh = columns(pbase, pv30 * 1.3 * t, half=45)
        cols_mesh["r"] = np.repeat(pv30, 8)
        p.add_mesh(cols_mesh, scalars="r", cmap="plasma", clim=(0, 400), show_scalar_bar=False, name="people")
        cam.set(p, -5 + 20 * k / 39, 34 + 6 * t, span * 0.85, cxm, cym)
        shoot(T6, "Columns: residents per 100 m cell on low ground (< 2 m above the drain), 2030 projection (JRC GHS-POP).",
              f"{pv30.sum() * t:,.0f} people on low ground in this view", "#ffb703", still="6" if k == 39 else None)
    # 7 dive to Bwaise ---------------------------------------------------------------------------------------
    T7 = "7  Down into Bwaise"
    clear("labels")
    bw = xyz(G, [32.562], [0.352])[0]
    labels(np.array([bw + [0, 0, 160]]), ["Bwaise"], size=16, name="bw", bg="#b00020")
    for k in range(46):
        t = ease(k / 45)
        cam.set(p, *lerp((15, 40, span * 0.85, cxm, cym), (60, 30, 1500, bw[0], bw[1]), t))
        if k == 20:
            clear("people")
        shoot(T7, "The Lubigi channel meets one of Kampala's most flood-prone neighbourhoods.",
              "Bwaise-Kalerwe: 1,039 buildings within 15 m of the channels", "#ff5252", still="7" if k == 45 else None)
    for k in range(24):
        cam.set(p, 60 + 40 * k / 23, 30, 1500, bw[0], bw[1])
        shoot(T7, "The Lubigi channel meets one of Kampala's most flood-prone neighbourhoods.",
              "Bwaise-Kalerwe: 1,039 buildings within 15 m of the channels", "#ff5252")
    mp4.close()
    p.close()
    gif[0].save(OUT / "kd3d_story.gif", save_all=True, append_images=gif[1:], duration=330, loop=0)
    ks = sorted(stills)
    W_, H_ = stills[ks[0]].size
    sheet = Image.new("RGB", (W_ * 2, H_ * ((len(ks) + 1) // 2)), "#0f1419")
    for i_, k in enumerate(ks):
        sheet.paste(stills[k], ((i_ % 2) * W_, (i_ // 2) * H_))
    sheet.save(OUT / "kd3d_story_chapters.png")
    print("frames", F["n"], "people low ground 2030 in view", round(pv30.sum()))


if __name__ == "__main__":
    main()
