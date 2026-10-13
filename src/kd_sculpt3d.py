"""Kampala drainage study, part 12: "sculpted" 3D film in the style of data-relief maps -> figures/kampala_drainage/3d/.

Three acts on a matte, dark relief lit by a low sun (shadows on):
  1  The channels        Kampala's drainage network glows into place, biggest channels first
  2  Concrete             built-up surface rises as extruded blocks, 1975 -> 2030 (JRC GHSL; height = share built)
  3  The water rises      water fills the valleys 0 -> 3 m above the drains; blocks it reaches turn red, with a
                          live count of residents (JRC GHS-POP 2030) on the flooded ground. Illustration, not a forecast.
Outputs: kd3d_sculpt.mp4 (1280x720 + bands), kd3d_sculpt.gif (small), kd3d_sculpt_acts.png (stills).
"""
import geopandas as gpd
import imageio.v2 as iio
import numpy as np
import pyvista as pv
import rasterio
import xarray as xr
from PIL import Image
from rasterio.windows import from_bounds

from common import PROC, ROOT
from kd_3d import OUT, columns, compose

pv.OFF_SCREEN = True
KD = ROOT / "data" / "kd"
BOX = (32.50, 0.27, 32.66, 0.385)  # Lubigi - Bwaise - Kalerwe - centre - Nakivubo - Lugogo - Kinawataka
VEX = 4.0
SRC = ("Relief: Copernicus GLO-30 DEM · built-up and population: JRC GHSL R2023A (2025, 2030 projected) · channels: © "
       "OpenStreetMap contributors · valley floors: this study (height above nearest drainage)")
BG_TOP, BG_BOT = "#1a2233", "#05070b"
GROUND = "#3a3f47"
CONC_LOW, CONC_HIGH = "#d8cfc0", "#fff4e0"
WATER = "#3fa9ff"
HIT = "#ff3b30"


def grid():
    with rasterio.open(PROC / "kampala_dem.tif") as r:
        w = from_bounds(*BOX, r.transform)
        dem = r.read(1, window=w).astype(float)
        tr = r.window_transform(w)
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand = r.read(2, window=from_bounds(*BOX, r.transform)).astype(float)
    H, W = dem.shape
    hand = hand[:H, :W]
    lon = tr.c + tr.a * (np.arange(W) + 0.5)
    lat = tr.f + tr.e * (np.arange(H) + 0.5)
    kx = 111320 * np.cos(np.deg2rad(lat.mean()))
    X, Y = np.meshgrid((lon - lon[0]) * kx, (lat - lat[-1]) * 110574)
    return dict(dem=dem, hand=hand, lon=lon, lat=lat, X=X, Y=Y, kx=kx)


def at(G, lo, la):
    i = np.abs(G["lat"][:, None] - np.atleast_1d(la)[None, :]).argmin(0)
    j = np.abs(G["lon"][:, None] - np.atleast_1d(lo)[None, :]).argmin(0)
    return i, j


def ease(t):
    return t * t * (3 - 2 * t)


def main():
    G = grid()
    dem, X, Y, hand = G["dem"], G["X"], G["Y"], G["hand"]
    zmin = np.nanmin(dem)
    Z = (dem - zmin) * VEX
    terrain = pv.StructuredGrid(X, Y, Z).compute_normals() if hasattr(pv.StructuredGrid, "compute_normals") else pv.StructuredGrid(X, Y, Z)
    terrain = terrain.extract_surface().compute_normals(cell_normals=False, auto_orient_normals=True)
    # skirt (base slab) for the sculpted look
    base = pv.Box(bounds=(X.min(), X.max(), Y.min(), Y.max(), -120, 0))
    # channels
    s = gpd.read_file(KD / "segments.gpkg").cx[BOX[0]:BOX[2], BOX[1]:BOX[3]]
    s = s[s.up_km2 >= 0.3].sort_values("up_km2", ascending=False)
    tubes, glows, lengths = [], [], []
    for gm, up in zip(s.geometry, s.up_km2):
        xy = np.asarray(gm.coords)
        i, j = at(G, xy[:, 0], xy[:, 1])
        P = np.c_[(xy[:, 0] - G["lon"][0]) * G["kx"], (xy[:, 1] - G["lat"][-1]) * 110574, Z[i, j] + 6]
        if len(P) < 2:
            continue
        line = pv.lines_from_points(P)
        r = float(np.clip(6 + 4 * np.sqrt(up), 7, 32))
        tubes.append(line.tube(radius=r, n_sides=8))
        glows.append(line.tube(radius=r * 2.6, n_sides=8))
        lengths.append(up)
    # concrete blocks: GHSL 100 m cells
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc").sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    cell = (abs(float(np.diff(g.lon).mean())) * 111320 * np.cos(np.deg2rad(0.33))) * (abs(float(np.diff(g.lat).mean())) * 111320)
    GLO, GLA = np.meshgrid(g.lon.values, g.lat.values)
    gi, gj = at(G, GLO.ravel(), GLA.ravel())
    gbase = np.c_[(GLO.ravel() - G["lon"][0]) * G["kx"], (GLA.ravel() - G["lat"][-1]) * 110574, Z[gi, gj]]
    ghand = hand[gi, gj]
    gdrain = dem[gi, gj] - ghand
    epochs = [1975, 1985, 1995, 2005, 2015, 2020, 2025, 2030]
    frac = {e: np.clip(g.sel(epoch=e).values.ravel() / cell, 0, 1) for e in epochs}
    keep = frac[2030] > 0.08
    gbase, ghand, gdrain = gbase[keep], ghand[keep], gdrain[keep]
    frac = {e: v[keep] for e, v in frac.items()}
    # year each cell first passed 20% built (for colouring by age)
    first = np.full(keep.sum(), 2035.0)
    for e in epochs[::-1]:
        first[frac[e] >= 0.2] = e
    pop = xr.open_dataarray(PROC / "kampala_ghs_pop.nc").sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    PLO, PLA = np.meshgrid(pop.lon.values, pop.lat.values)
    pi, pj = at(G, PLO.ravel(), PLA.ravel())
    phand = hand[pi, pj]
    p30 = np.nan_to_num(pop.sel(epoch=2030).values.ravel())
    H_PER = 160.0  # block height (m, before exaggeration) for a fully built cell

    # plotter -----------------------------------------------------------------------------------------------
    p = pv.Plotter(off_screen=True, window_size=(1280, 720))
    p.set_background(BG_BOT, top=BG_TOP)
    p.remove_all_lights()
    sun = pv.Light(position=(X.max() * 1.6, -Y.max() * 0.6, 2600), focal_point=(X.mean(), Y.mean(), 0), intensity=1.15,
                   light_type="scene light")
    fill = pv.Light(position=(-X.max(), Y.max() * 2, 3000), focal_point=(X.mean(), Y.mean(), 0), intensity=0.25,
                    light_type="scene light")
    p.add_light(sun)
    p.add_light(fill)
    p.enable_shadows()
    p.add_mesh(terrain, color=GROUND, ambient=0.25, diffuse=0.9, specular=0.0, smooth_shading=True, name="terrain")
    p.add_mesh(base, color="#14171c", ambient=0.4, name="base")
    cx, cy = X.mean(), Y.mean()
    span = max(X.max(), Y.max())
    cz = float(np.nanmean(Z))

    def cam(az, el, dist, fx=cx, fy=cy):
        a, e = np.deg2rad(az), np.deg2rad(el)
        p.camera.focal_point = (fx, fy, cz)
        p.camera.position = (fx + dist * np.cos(e) * np.cos(a), fy + dist * np.cos(e) * np.sin(a), cz + dist * np.sin(e))
        p.camera.up = (0, 0, 1)
        p.camera.view_angle = 28

    mp4 = iio.get_writer(str(OUT / "kd3d_sculpt.mp4"), fps=15, quality=8, macro_block_size=8)
    gif, stills = [], {}
    nfr = {"n": 0}

    def shoot(title, sub, count, color, still=None):
        can = compose(p.screenshot(return_img=True), title, sub, count, color, SRC)
        mp4.append_data(np.asarray(can))
        if nfr["n"] % 5 == 0:
            gif.append(can.resize((560, int(can.height * 560 / can.width)), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE))
        if still:
            stills[still] = can
        nfr["n"] += 1

    # Act 1: channels -------------------------------------------------------------------------------------------
    T1, S1 = "The channels", "Kampala's drainage network, from the big trunk channels to the smallest mapped drains."
    n = len(tubes)
    for k in range(75):
        t = ease(k / 74)
        upto = max(1, int(n * t))
        pass  # translucent glow is dropped by the shadow pass
        p.add_mesh(pv.merge(tubes[:upto]), color="#7fe3ff", ambient=0.9, diffuse=0.3, specular=0.6, name="chan")
        cam(-135 + 25 * t, 40 - 8 * t, span * (1.45 - 0.25 * t))
        shoot(T1, S1, f"{upto:,} channel segments", "#7fe3ff", still="1" if k == 74 else None)
    # Act 2: concrete -------------------------------------------------------------------------------------------
    T2, S2 = "Concrete, 1975 to 2030", ("Blocks: 100 m cells, height = share covered by roofs and paving. Pale: built by 1995; "
                                       "amber: 1995-2015; orange: since 2015.")
    for k in range(110):
        ef = ease(k / 109) * (len(epochs) - 1)
        e0 = int(np.floor(ef))
        e1 = min(e0 + 1, len(epochs) - 1)
        f = frac[epochs[e0]] * (1 - (ef - e0)) + frac[epochs[e1]] * (ef - e0)
        m = f > 0.05
        blk = columns(gbase[m], (f[m] ** 1.3) * H_PER * VEX / 3, half=36)
        blk["age"] = np.repeat(np.where(first[m] <= 1995, 0.0, np.where(first[m] <= 2015, 0.5, 1.0)), 8)
        p.add_mesh(blk, scalars="age", cmap=["#e9e4da", "#ffb74d", "#ff7043"], clim=(0, 1), show_scalar_bar=False,
                   ambient=0.22, diffuse=0.9, specular=0.15, name="blocks")
        yr = epochs[e0] + (epochs[e1] - epochs[e0]) * (ef - e0)
        vf = ghand < 3
        share = float((f * vf).sum() / max(vf.sum(), 1) * 100)
        cam(-110 + 40 * k / 109, 32 + 4 * np.sin(np.pi * k / 109), span * 1.2)
        shoot(T2, S2, f"{yr:.0f}{' (projected)' if yr > 2020 else ''}  ·  valley floors built over: {share:.0f}%", "#ffe0b2",
              still="2" if k == 109 else None)
    # Act 3: water ----------------------------------------------------------------------------------------------
    T3, S3 = "The water rises", ("Water filling the valleys 0-3 m above the drains; red roofs mark buildings it reaches. "
                                 "Illustration of which ground floods first - not a forecast.")
    f = frac[2030]
    m = f > 0.05
    fb, fh = f[m], ghand[m]
    for k in range(120):
        h = 3.0 * ease(min(k / 100, 1))
        wz = np.where(hand < h, (dem - hand + h - zmin) * VEX + 1.5, Z - 6)
        wg = pv.StructuredGrid(X, Y, wz)
        wg["wet"] = (hand < h).ravel(order="F").astype(float)
        wet = wg.threshold(0.5, scalars="wet", all_scalars=True)
        if wet.n_cells:
            p.add_mesh(wet, color="#2e9bff", opacity=1.0, ambient=0.45, diffuse=0.6, specular=1.0, specular_power=60,
                       smooth_shading=True, name="water")
        hit = fh < h
        shrink = 1 - 0.55 * ease(min(k / 25, 1))  # lower the city so the water shows
        hb = (fb ** 1.3) * H_PER * VEX / 3 * shrink
        hb = np.where(hit, (h - fh) * VEX + 5.0, hb)  # flooded buildings: red roofs just breaking the water surface
        blk = columns(gbase[m], hb, half=36)
        blk["c"] = np.repeat(np.where(hit, 1.0, 0.0), 8)
        p.add_mesh(blk, scalars="c", cmap=["#cfc8bb", HIT], clim=(0, 1), show_scalar_bar=False, ambient=0.35, diffuse=0.9,
                   name="blocks")
        people = float(p30[phand < h].sum())
        cam(-70 + 70 * k / 119, 30 + 6 * k / 119, span * (1.2 - 0.25 * k / 119))
        shoot(T3, S3, f"water {h:.1f} m above the drains  ·  {int(hit.sum()):,} built cells reached  ·  "
                      f"{people:,.0f} residents (2030) on flooded ground", "#ff8a80", still="3" if k == 105 else None)
    mp4.close()
    p.close()
    gif[0].save(OUT / "kd3d_sculpt.gif", save_all=True, append_images=gif[1:], duration=330, loop=0)
    ks = sorted(stills)
    W_, H_ = stills[ks[0]].size
    sheet = Image.new("RGB", (W_, H_ * len(ks)), "#0f1419")
    for i_, k in enumerate(ks):
        sheet.paste(stills[k], (0, i_ * H_))
    sheet.save(OUT / "kd3d_sculpt_acts.png")
    print("frames", nfr["n"])


if __name__ == "__main__":
    main()
