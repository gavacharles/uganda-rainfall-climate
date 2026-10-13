"""Kampala drainage study, part 9: fly-through animations of each hotspot area -> figures/kampala_drainage/areas/flythrough/.

For each area (kd_areas.AREAS): start over the whole area, zoom in at the upstream end of the main traced channel,
fly downstream along it to the flooding point, then pull back out. Satellite imagery is fetched once per area
(Esri World Imagery, zoom 17) and cropped per frame. A heads-up panel shows the distance flown and the current
segment's priority, drivers, buildings in the 15 m reserve and culverts. Writes MP4 (H.264) and a smaller GIF.
"""
import sys

import contextily as ctx
import geopandas as gpd
import imageio_ffmpeg
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapely
import shapely.ops
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter
from shapely.geometry import LineString

from common import CREDIT
from kd_areas import AREAS
from kd_maps import CM, IMG, KD, OUT, load, trace

matplotlib.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
FLY = OUT / "areas" / "flythrough"
WM = 3857


def path_for(reach, gap=300.0):
    """Main stem upstream -> downstream: chain segments by increasing upstream area, each starting near the
    previous end (a gap of more than `gap` m ends the chain)."""
    stem = reach[reach.up_km2 >= reach.up_km2.max() * 0.12].sort_values("up_km2")
    rest = list(stem.index)
    first = rest.pop(0)
    pts = list(stem.loc[first].geometry.coords)
    tail = np.array(stem.loc[stem.index[-1]].geometry.coords[0])
    if np.hypot(*(np.array(pts[-1]) - tail)) > np.hypot(*(np.array(pts[0]) - tail)):
        pts = pts[::-1]
    while rest:
        end = np.array(pts[-1])
        best, bd, flip = None, gap, False
        for r in rest:
            c = stem.loc[r].geometry.coords
            for f_, q in ((False, c[0]), (True, c[-1])):
                d_ = np.hypot(*(np.array(q) - end))
                if d_ < bd:
                    best, bd, flip = r, d_, f_
        if best is None:
            break
        c = list(stem.loc[best].geometry.coords)
        pts += c[::-1] if flip else c
        rest.remove(best)
    return LineString(pts).simplify(10)


def fly(k, name, sub, places, s, hp, b, waste, cul):
    hp_area = hp[hp.place.isin(places)]
    fl = s[s.up_km2 >= 0.25]
    tree = shapely.STRtree(fl.geometry.values)
    h0 = hp_area.iloc[0]
    near = fl.iloc[tree.query(h0.geometry, predicate="dwithin", distance=700)]
    if near.empty:
        print("skip", name)
        return
    start = int((near.up_km2 / (1 + near.distance(h0.geometry) / 250)).idxmax())
    reach = trace(s, start, up_km=2500, down_km=600)
    others = []
    for _, h in hp_area.iloc[1:].iterrows():
        nn = fl.iloc[tree.query(h.geometry, predicate="dwithin", distance=700)]
        if len(nn):
            st = int((nn.up_km2 / (1 + nn.distance(h.geometry) / 250)).idxmax())
            others.append(trace(s, st, up_km=2500, down_km=600))
    R = pd.concat([reach] + others)
    R = R[~R.index.duplicated()]
    path = path_for(reach)
    # everything to Web Mercator for the imagery
    to = lambda g: g.to_crs(WM)
    Rw, sw, hpw = to(R), to(s), to(hp_area)
    pathw = gpd.GeoSeries([path], crs=s.crs).to_crs(WM).iloc[0]
    x0, y0, x1, y1 = Rw.total_bounds
    hx0, hy0, hx1, hy1 = hpw.total_bounds
    x0, y0, x1, y1 = min(x0, hx0) - 400, min(y0, hy0) - 400, max(x1, hx1) + 400, max(y1, hy1) + 400
    side = max(x1 - x0, y1 - y0, 2500)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    A = (cx - side / 2, cx + side / 2, cy - side / 2, cy + side / 2)
    import time
    for attempt in range(6):  # tile servers occasionally reset connections
        try:
            img, ext = ctx.bounds2img(A[0], A[2], A[1], A[3], zoom=17 if side < 6000 else 16, source=IMG)
            break
        except Exception as e:  # noqa: BLE001
            print("  tiles retry", attempt + 1, str(e)[:60], flush=True)
            time.sleep(10 * (attempt + 1))
    else:
        raise RuntimeError("imagery tiles unavailable")
    lon0, lat0, lon1, lat1 = gpd.GeoSeries(gpd.points_from_xy([A[0], A[1]], [A[2], A[3]]), crs=WM).to_crs(4326).total_bounds
    bb = b.cx[lon0:lon1, lat0:lat1].to_crs(s.crs)
    res = to(bb[bb.intersects(R.buffer(15).union_all())])
    w100 = to(waste[waste.intersects(R.buffer(100).union_all())])
    c25 = to(cul[cul.intersects(R.buffer(25).union_all())])

    fig = plt.figure(figsize=(12, 7.6))
    ax = fig.add_axes([0.0, 0.06, 0.66, 0.84])
    ax.imshow(img, extent=ext, interpolation="bilinear")
    sw.cx[A[0]:A[1], A[2]:A[3]].plot(ax=ax, color="#d0d0d0", lw=0.6, alpha=0.7)
    Rw.plot(ax=ax, color="white", lw=np.clip(2.5 + Rw.up_km2 ** 0.5, 3.5, 8.5), zorder=3)
    Rw.plot(ax=ax, column="risk_pct", cmap=CM, vmin=0, vmax=100, lw=np.clip(1.5 + Rw.up_km2 ** 0.5, 2.5, 7), zorder=4,
            missing_kwds=dict(color="#bdbdbd"))
    res.plot(ax=ax, facecolor="#ff00ff55", edgecolor="#ff00ff", lw=0.6, zorder=5)
    w100.plot(ax=ax, marker="^", color="#ffd400", edgecolor="k", markersize=55, lw=0.6, zorder=6)
    c25.plot(ax=ax, marker="s", color="white", edgecolor="k", markersize=30, lw=0.7, zorder=6)
    hpw.plot(ax=ax, marker="o", facecolor="none", edgecolor="white", markersize=420, lw=3, zorder=7)
    hpw.plot(ax=ax, marker="o", facecolor="none", edgecolor="#e8002a", markersize=420, lw=1.4, zorder=8)
    for _, h in hpw.iterrows():
        ax.annotate(h.place, (h.geometry.x, h.geometry.y), xytext=(0, 18), textcoords="offset points", ha="center",
                    fontsize=9, fontweight="bold", color="white", zorder=12, clip_on=True,
                    bbox=dict(facecolor="#b00020", edgecolor="none", pad=1.5, alpha=0.9))
    cam, = ax.plot([], [], marker="o", ms=11, mfc="none", mec="#00e5ff", mew=2.5, zorder=13)
    ax.set_axis_off()
    # side panel
    fig.text(0.02, 0.965, f"Fly-through: {name}", fontsize=16, fontweight="bold", va="top")
    fig.text(0.02, 0.925, f"{sub}. Following the main channel downstream to the flooding point.", fontsize=9.5,
             color="#555", va="top")
    lx = fig.add_axes([0.70, 0.60, 0.28, 0.30])
    lx.imshow(img, extent=ext)
    Rw.plot(ax=lx, color="#ff7043", lw=1.2)
    hpw.plot(ax=lx, marker="o", facecolor="none", edgecolor="#e8002a", markersize=30, lw=1)
    lx.plot(*pathw.xy, color="#00e5ff", lw=0.8, ls="--")
    box = plt.Rectangle((0, 0), 1, 1, fill=False, ec="#00e5ff", lw=1.8)
    lx.add_patch(box)
    lx.set_xlim(A[0], A[1])
    lx.set_ylim(A[2], A[3])
    lx.set_xticks([])
    lx.set_yticks([])
    lx.set_title("Where we are", fontsize=9.5, loc="left")
    hud = fig.text(0.70, 0.55, "", fontsize=10, va="top", linespacing=1.55, family="DejaVu Sans")
    from matplotlib.lines import Line2D
    fig.legend(handles=[Line2D([], [], color="#a50026", lw=3, label="channel, high priority"),
                        Line2D([], [], color="#4575b4", lw=3, label="channel, low priority"),
                        Line2D([], [], marker="s", ls="", color="white", mec="k", label="culvert"),
                        Line2D([], [], marker="s", ls="", color="#ff00ff55", mec="#ff00ff", label="building ≤ 15 m"),
                        Line2D([], [], marker="^", ls="", color="#ffd400", mec="k", label="waste/dump point"),
                        Line2D([], [], marker="o", ls="", mfc="none", mec="#e8002a", label="reported flooding")],
               loc="lower left", bbox_to_anchor=(0.695, 0.075), ncol=2, fontsize=8.5, frameon=False)
    fig.text(0.01, 0.012, "Imagery: Esri World Imagery (Esri, Maxar, Earthstar Geographics) · drains, waste: © OpenStreetMap "
             "contributors · buildings: Microsoft · DEM: Copernicus GLO-30", fontsize=7.5, color="#666")
    fig.text(0.99, 0.012, CREDIT, fontsize=10, fontweight="bold", color="#333", ha="right")

    # camera script: overview -> zoom in at upstream end -> fly -> pause at flooding point -> zoom out
    L = pathw.length
    W = 650.0
    n_fly = int(np.clip(L / 60, 35, 110))
    p0 = pathw.interpolate(0)
    hpt = hpw.iloc[0].geometry
    shots = []
    for t in np.linspace(0, 1, 10):  # zoom in
        e = 1 - (1 - t) ** 2
        w = side * (1 - e) + W * e
        shots.append((cx * (1 - e) + p0.x * e, cy * (1 - e) + p0.y * e, w, 0.0))
    for d in np.linspace(0, L, n_fly):
        p = pathw.interpolate(d)
        shots.append((p.x, p.y, W, d))
    for t in np.linspace(0, 1, 8):  # glide to the flooding point
        pe = pathw.interpolate(L)
        shots.append((pe.x * (1 - t) + hpt.x * t, pe.y * (1 - t) + hpt.y * t, W, L))
    shots += [shots[-1]] * 6
    for t in np.linspace(0, 1, 10):  # pull back
        e = t ** 2
        shots.append((hpt.x * (1 - e) + cx * e, hpt.y * (1 - e) + cy * e, W * (1 - e) + side * e, L))
    shots += [shots[-1]] * 6
    segw = Rw.reset_index()
    stree = shapely.STRtree(segw.geometry.values)

    def step(i):
        x, y, w, d = shots[i]
        ax.set_xlim(x - w / 2, x + w / 2)
        hh = w * (0.84 * 7.6) / (0.66 * 12)
        ax.set_ylim(y - hh / 2, y + hh / 2)
        cam.set_data([x], [y])
        box.set_bounds(x - w / 2, y - w / 2, w, w)
        j = stree.nearest(shapely.Point(x, y))
        r = segw.iloc[j]
        drv = (r.top_drivers or "-") if isinstance(r.top_drivers, str) else "-"
        drv = "\n   ".join(drv.split("; "))
        hud.set_text(f"Distance flown: {d / 1000:.1f} of {L / 1000:.1f} km\n"
                     f"Channel: {r['name'] if isinstance(r['name'], str) else 'unnamed drain'}\n"
                     f"Upstream area: {r.up_km2:.1f} km²\n"
                     f"Maintenance priority: {r.risk_pct:.0f}th percentile\n"
                     f"Buildings ≤ 15 m (this 200 m): {int(r.bldg_reserve)}\n"
                     f"Culverts nearby: {int(r.culverts)}   Waste points ≤ 100 m: {int(r.waste_100m)}\n"
                     f"Likely causes:\n   {drv}")
        return cam, box, hud
    anim = FuncAnimation(fig, step, frames=len(shots))
    FLY.mkdir(parents=True, exist_ok=True)
    slug = "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_")
    anim.save(FLY / f"kd_fly_{k:02d}_{slug}.mp4", writer=FFMpegWriter(fps=8, bitrate=2400), dpi=110)
    anim.save(FLY / f"kd_fly_{k:02d}_{slug}.gif", writer=PillowWriter(fps=8), dpi=48)
    plt.close(fig)
    print(k, name, f"path {L / 1000:.1f} km, {len(shots)} frames", flush=True)


def main(which=None):
    s, hp, city = load()
    s = s.reset_index(drop=True)
    b = gpd.read_parquet(KD / "ms_buildings.parquet")
    waste = gpd.read_file(KD / "osm_waste.geojson").to_crs(s.crs)
    waste["geometry"] = waste.geometry.representative_point()
    cul = gpd.read_file(KD / "osm_waterways.geojson")
    cul = cul[cul.tunnel.isin(["culvert", "yes"])].to_crs(s.crs)
    cul["geometry"] = cul.geometry.interpolate(0.5, normalized=True)
    for k, (name, sub, places) in enumerate(AREAS, start=1):
        if which and k not in which:
            continue
        fly(k, name, sub, places, s, hp, b, waste, cul)




# ---------------------------------------------------------------- social-media fly-along (vertical 4:5)
def fly_social(k, name, sub, places, s, hp, b, waste, cul, step_m=6.0, half=170.0):
    """Smooth vertical walk-through along the channel feeding the area's flooding point (no pop-ups): smoothed
    camera path, eased constant speed, 24 fps; quiet overlays of buildings in the 15 m reserve, culverts and dump sites."""
    import textwrap
    import time
    import imageio.v2 as iio
    from matplotlib.patches import FancyBboxPatch
    hp_area = hp[hp.place.isin(places)]
    fl = s[s.up_km2 >= 0.25]
    tree = shapely.STRtree(fl.geometry.values)
    START = {"Kibuli–Kansanga–Gaba Road": "Soya-Bunga"}  # avoid repeating the Nakivubo trunk walked for Kitante–Lugogo
    h0 = hp_area[hp_area.place == START[name]].iloc[0] if name in START else hp_area.iloc[0]
    near = fl.iloc[tree.query(h0.geometry, predicate="dwithin", distance=700)]
    if near.empty:
        print("skip", name)
        return
    start = int((near.up_km2 / (1 + near.distance(h0.geometry) / 250)).idxmax())
    reach = trace(s, start, up_km=3000, down_km=500)
    path = path_for(reach)
    if path.length > 3600:  # keep films under ~1 minute: last 3.6 km before the flooding point
        path = shapely.ops.substring(path, path.length - 3600, path.length)
    L = path.length
    corridor = path.buffer(15)
    # features near the channel
    lon0, lat0, lon1, lat1 = gpd.GeoSeries([path.buffer(400)], crs=s.crs).to_crs(4326).total_bounds
    bb = b.cx[lon0:lon1, lat0:lat1].to_crs(s.crs)
    res = bb[bb.intersects(corridor)].copy()
    res["d"] = [path.project(g.centroid) for g in res.geometry]
    cu = cul[cul.distance(path) <= 25].copy()
    cu["d"] = [path.project(g) for g in cu.geometry]
    ws = waste[waste.distance(path) <= 100].copy()
    ws["d"] = [path.project(g) for g in ws.geometry]
    ws["off"] = ws.distance(path)
    hs = hp[hp.distance(path) <= 400].copy()
    hs["d"] = [path.project(g) for g in hs.geometry]
    segs = s[s.distance(path) <= 5].copy()
    segs["d"] = [path.project(g.interpolate(0.5, normalized=True)) for g in segs.geometry]
    hsd = pd.read_csv(KD / "flood_hotspots.csv").set_index("place").evidence
    events = [(r.d, "culvert", "Culvert", "A pinch point: silt and rubbish lodge here and back water up.", r.geometry)
              for r in cu.itertuples()]
    events += [(r.d, "waste", "Dump site", f"Waste {r.off:.0f} m from the channel: rubbish washes in when it rains.", r.geometry)
               for r in ws.itertuples()]
    for r in hs.itertuples():
        ev = str(hsd.get(r.place, "")).replace("news ", "")
        events.append((r.d, "flood", f"Reported flooding: {r.place}", textwrap.shorten(ev, 70), r.geometry))
    events.sort(key=lambda e: e[0])
    # imagery (Web Mercator)
    to = lambda gdf: gdf.to_crs(WM)
    pathw = gpd.GeoSeries([path], crs=s.crs).to_crs(WM).iloc[0]
    X0, Y0, X1, Y1 = gpd.GeoSeries([path.buffer(half * 1.6)], crs=s.crs).to_crs(WM).total_bounds
    for attempt in range(6):
        try:
            img, ext = ctx.bounds2img(X0, Y0, X1, Y1, zoom=18, source=IMG)
            break
        except Exception as e:  # noqa: BLE001
            print("  tiles retry", attempt + 1, str(e)[:60], flush=True)
            time.sleep(10 * (attempt + 1))
    else:
        raise RuntimeError("imagery tiles unavailable")
    fig = plt.figure(figsize=(7.2, 9.0), facecolor="#0f1419")
    ax = fig.add_axes([0.0, 0.27, 1.0, 0.63])
    ax.imshow(img, extent=ext, interpolation="bilinear")
    sw = to(s.cx[path.bounds[0] - 600:path.bounds[2] + 600, path.bounds[1] - 600:path.bounds[3] + 600])
    sw.plot(ax=ax, color="#9e9e9e", lw=1.2, alpha=0.7)
    to(gpd.GeoDataFrame(geometry=[corridor], crs=s.crs)).plot(ax=ax, facecolor="#00e5ff22", edgecolor="#00e5ff", lw=0.8,
                                                              ls="--", zorder=3)
    segw = to(segs)
    segw.plot(ax=ax, column="risk_pct", cmap=CM, vmin=0, vmax=100, lw=6, zorder=4, missing_kwds=dict(color="#bdbdbd"))
    if len(res):
        to(res).plot(ax=ax, facecolor="#ff00ff66", edgecolor="#ff00ff", lw=1.0, zorder=5)
    if len(ws):
        to(ws).plot(ax=ax, marker="^", color="#ffd400", edgecolor="k", markersize=70, lw=0.6, zorder=6)
    if len(cu):
        to(cu).plot(ax=ax, marker="s", color="white", edgecolor="k", markersize=50, lw=0.6, zorder=6)
    if len(hs):
        to(hs).plot(ax=ax, marker="o", facecolor="none", edgecolor="#ff1744", markersize=900, lw=2.5, zorder=7)
    ax.set_axis_off()
    # map fills the frame; slim header and footer only
    ax.set_position([0.0, 0.085, 1.0, 0.83])
    fig.text(0.04, 0.975, name, fontsize=17, fontweight="bold", color="white", va="top")
    fig.text(0.04, 0.95, "A walk along the channel to where it floods", fontsize=10, color="#b9c2c9", va="top")
    prog = fig.add_axes([0.04, 0.921, 0.92, 0.005])
    prog.set_xlim(0, 1)
    prog.set_ylim(0, 1)
    prog.axis("off")
    prog.barh(0.5, 1, height=1, color="#2b3440")
    bar = prog.barh(0.5, 0, height=1, color="#00e5ff")[0]
    dist = fig.text(0.96, 0.975, "", fontsize=12, color="#00e5ff", ha="right", va="top", fontweight="bold")
    fig.text(0.04, 0.058, "Channel colour: maintenance priority (red = high) · pink: buildings within 15 m · "
             "squares: culverts · triangles: dump sites", fontsize=7.2, color="#b9c2c9")
    fig.text(0.04, 0.035, "Imagery: Esri World Imagery (Esri, Maxar, Earthstar Geographics) · drains, waste: © OpenStreetMap "
             "contributors · buildings: Microsoft", fontsize=6.3, color="#9aa4ab")
    fig.text(0.96, 0.008, CREDIT, fontsize=10, fontweight="bold", color="white", ha="right")
    # smooth camera: heavily smoothed path, eased constant-speed motion, 24 fps
    from scipy.ndimage import gaussian_filter1d
    raw = np.array([pathw.interpolate(x).coords[0] for x in np.linspace(0, pathw.length, max(50, int(pathw.length / 5)))])
    sm = np.c_[gaussian_filter1d(raw[:, 0], 12, mode="nearest"), gaussian_filter1d(raw[:, 1], 12, mode="nearest")]
    seg_len = np.r_[0, np.cumsum(np.hypot(*np.diff(sm, axis=0).T))]
    Ls = seg_len[-1]
    fps, speed = 24, 70.0  # metres per second of video
    nfr = max(48, int(Ls / speed * fps))
    tt = np.linspace(0, 1, nfr)
    ease = np.where(tt < 0.08, 0.5 * (tt / 0.08) ** 2 * 0.16, np.where(tt > 0.92, 1 - 0.5 * ((1 - tt) / 0.08) ** 2 * 0.16,
                    0.08 + (tt - 0.08) * (0.84 / 0.84)))
    ease = (ease - ease.min()) / (ease.max() - ease.min())
    xs = np.interp(ease * Ls, seg_len, sm[:, 0])
    ys = np.interp(ease * Ls, seg_len, sm[:, 1])
    hold = fps * 2
    FLY.mkdir(parents=True, exist_ok=True)
    slug = "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_")
    out = FLY / f"kd_fly_{k:02d}_{slug}_social.mp4"
    W = iio.get_writer(str(out), fps=fps, quality=8, macro_block_size=8)
    aspect = (0.83 * 9.0) / (1.0 * 7.2)
    for i in range(nfr + hold):
        q = min(i, nfr - 1)
        x, y = xs[q], ys[q]
        ax.set_xlim(x - half, x + half)
        ax.set_ylim(y - half * aspect, y + half * aspect)
        bar.set_width(ease[q])
        dist.set_text(f"{ease[q] * L / 1000:.1f} km")
        fig.canvas.draw()
        W.append_data(np.asarray(fig.canvas.buffer_rgba())[:, :, :3])
    W.close()
    plt.close(fig)
    print(k, name, f"social: {L / 1000:.1f} km, {nfr + hold} frames ({(nfr + hold) / fps:.0f} s), {len(res)} bldg, {len(cu)} culv, "
                   f"{len(ws)} waste, {len(hs)} hotspots", flush=True)


def main_social(which=None):
    s, hp, city = load()
    s = s.reset_index(drop=True)
    b = gpd.read_parquet(KD / "ms_buildings.parquet")
    waste = gpd.read_file(KD / "osm_waste.geojson").to_crs(s.crs)
    waste["geometry"] = waste.geometry.representative_point()
    cul = gpd.read_file(KD / "osm_waterways.geojson")
    cul = cul[cul.tunnel.isin(["culvert", "yes"])].to_crs(s.crs)
    cul["geometry"] = cul.geometry.interpolate(0.5, normalized=True)
    for k, (name, sub, places) in enumerate(AREAS, start=1):
        if which and k not in which:
            continue
        fly_social(k, name, sub, places, s, hp, b, waste, cul)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "social":
        main_social([int(a) for a in args[1:]] or None)
    else:
        main([int(a) for a in args] or None)
