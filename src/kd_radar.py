"""Kampala drainage study, part 7: Sentinel-1 radar time series (cloud-proof), 2017-2026.

Buildings return strong radar echoes (walls + ground = double bounce), so ground that turns persistently bright
between years is new construction. Comparing yearly medians on one orbit track:
  annual   yearly median VV/VH backscatter (gamma0, dB), 20 m, one relative orbit, <= 12 passes a year
  change   new-structure pixels: VV up >= 3 dB vs 2017-18 AND now > -6 dB; counted on valley floors (HAND < 3 m)
           and within 100 m of each channel segment -> results/kd_radar_new_structures.csv, data/kd/segments_radar.csv
  figures  kd17 change map, kd18 small-multiple still, kd_a4 animation (figures/kampala_drainage/)
"""
import os
import sys

os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "6")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "3")

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import planetary_computer as pc
import pystac_client
import rasterio
import shapely
import xarray as xr
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap
from odc.stac import load

from common import CREDIT, FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
BBOX = [32.45, 0.20, 32.72, 0.42]
SRC = ("Radar: ESA Copernicus Sentinel-1 RTC (Microsoft Planetary Computer) · channels: © OpenStreetMap contributors · "
       "valley floors: Copernicus GLO-30 DEM")


def annual():
    f = KD / "sat_s1_annual.nc"
    if f.exists():
        return
    cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
    allit = list(cat.search(collections=["sentinel-1-rtc"], bbox=BBOX, datetime="2017-01-01/2026-10-12").items())
    from shapely.geometry import box, shape
    aoi = box(*BBOX)
    full = [i for i in allit if shape(i.geometry).contains(aoi)]  # passes that cover the whole study area
    orb = pd.Series([i.properties.get("sat:relative_orbit") for i in full]).value_counts()
    print("full-coverage passes by track:", orb.to_dict(), flush=True)
    track = int(orb.index[0])
    its = [i for i in full if i.properties.get("sat:relative_orbit") == track]
    print("track", track, "passes", len(its), flush=True)
    years = []
    for y in range(2017, 2027):
        yi = sorted([i for i in its if i.datetime.year == y], key=lambda i: i.datetime)
        if len(yi) > 12:
            yi = [yi[k] for k in np.linspace(0, len(yi) - 1, 12).round().astype(int)]
        if not yi:
            continue
        yf = KD / f"sat_s1_{y}.nc"
        if yf.exists():
            years.append(xr.open_dataset(yf).load())
            print("radar", y, "cached", flush=True)
            continue
        good = []
        for it in yi:  # load scene by scene so one corrupt file cannot sink the year
            try:
                one = load([it], bands=["vv", "vh"], bbox=BBOX, crs="EPSG:32636", resolution=20, chunks={}).isel(time=0)
                good.append(one.where(one > 0))  # 0 = no data
            except Exception as e:  # noqa: BLE001 - skip unreadable scenes
                print("  skip scene", it.id, str(e)[:60], flush=True)
        m = xr.concat(good, "time").median("time")
        db = lambda v: 10 * np.log10(v.clip(min=1e-5))
        one_y = xr.Dataset({"vv": db(m.vv), "vh": db(m.vh)}).astype("float32").compute().expand_dims(year=[y])
        one_y.to_netcdf(yf)
        years.append(one_y)
        print("radar", y, len(good), "of", len(yi), flush=True)
    out = xr.concat(years, "year")
    out.attrs["relative_orbit"] = track
    out.to_netcdf(f)


def valley_mask(d):
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand = r.read(2)
        tr = r.transform
    import pyproj
    tf = pyproj.Transformer.from_crs(32636, 4326, always_xy=True)
    X, Y = np.meshgrid(d.x.values, d.y.values)
    lo, la = tf.transform(X, Y)
    col = ((lo - tr.c) / tr.a).astype(int).clip(0, hand.shape[1] - 1)
    row = ((la - tr.f) / tr.e).astype(int).clip(0, hand.shape[0] - 1)
    return hand[row, col] < 3


def change():
    d = xr.open_dataset(KD / "sat_s1_annual.nc")
    base = d.vv.sel(year=[2017, 2018]).mean("year")
    years = list(d.year.values)
    vf = valley_mask(d)
    # candidate new structure on previously open land: dark at baseline (< -9 dB), now building-bright (> -7 dB),
    # up >= 4 dB, persisting two years. Checked against Impact Observatory land cover 2017->2023: ~30% of candidates
    # are confirmed new built-up, but radar finds only ~1% of all new built-up (most new homes are too small/low).
    new = {y: (base < -9) & ((d.vv.sel(year=y) - base) >= 4) & (d.vv.sel(year=y) > -7) for y in years}
    # persistent: also new in the following year (or the last year itself), to drop one-off speckle/events
    pers = {}
    for k, y in enumerate(years):
        # persistent change: also present the following year (for the last year, also present the year before)
        other = years[k + 1] if k + 1 < len(years) else years[k - 1]
        pers[y] = (new[y] & new[other]).values
    px_ha = 0.04  # 20 m x 20 m
    rows = []
    s = gpd.read_file(KD / "segments.gpkg").to_crs(32636)
    for y in years:
        rows.append(dict(year=y, new_structures_ha=pers[y].sum() * px_ha, on_valley_floor_ha=(pers[y] & vf).sum() * px_ha))
    df = pd.DataFrame(rows)
    df.round(1).to_csv(RES / "kd_radar_new_structures.csv", index=False)
    print(df.round(1).to_string())
    # per segment: new-structure hectares within 100 m (2026 vs 2017-18)
    last = pers[years[-1]]
    yy, xx = np.nonzero(last)
    pts = shapely.points(d.x.values[xx], d.y.values[yy])
    i, j = shapely.STRtree(pts).query(s.geometry.values, predicate="dwithin", distance=100)
    s["radar_new_ha_100m"] = np.bincount(i, minlength=len(s)) * px_ha
    s[["seg_id", "radar_new_ha_100m"]].to_csv(KD / "segments_radar.csv", index=False)
    by = s[s.up_km2 >= 0.25].groupby("system").radar_new_ha_100m.sum().sort_values(ascending=False)
    print(by.round(1))
    return d, base, pers, vf, s, df


def grow(mask, it=2):
    """Thicken detections (20 m pixels) to ~60-100 m blobs so they read at city scale."""
    from scipy import ndimage
    return ndimage.binary_dilation(np.asarray(mask), iterations=it)


def solid(mask, it=4):
    return np.where(grow(mask, it), 1.0, np.nan)


def halo(mask, it=4):
    """Dark outline ring around the enlarged detections so they stand out from the radar texture."""
    g = grow(mask, it)
    return np.where(grow(mask, it + 2) & ~g, 1.0, np.nan)


def density(mask, k=5):
    """Share of each k x k block (20 m pixels -> 200 m) flagged, repeated back to pixel size for display."""
    H, W = mask.shape
    m = mask[: H // k * k, : W // k * k].reshape(H // k, k, W // k, k).mean((1, 3))
    out = np.full(mask.shape, np.nan)
    out[: H // k * k, : W // k * k] = np.repeat(np.repeat(m, k, 0), k, 1)
    return np.where(out >= 0.04, out, np.nan)


def figures():
    d, base, pers, vf, s, df = change()
    years = list(d.year.values)
    last = years[-1]
    ext = [float(d.x.min()), float(d.x.max()), float(d.y.min()), float(d.y.max())]
    fl = s[s.up_km2 >= 2]
    gray = dict(cmap=LinearSegmentedColormap.from_list("dk", ["#000000", "#5a5a5a"]), vmin=-22, vmax=2, extent=ext,
                origin="upper" if float(d.y[0]) > float(d.y[-1]) else "lower")
    red = LinearSegmentedColormap.from_list("r", ["#ff2d95", "#ff2d95"])
    yel = LinearSegmentedColormap.from_list("y", ["#ffe600", "#ffe600"])
    sk = dict(vmin=0, vmax=1, extent=ext, interpolation="nearest")
    dk = dict(vmin=0.04, vmax=0.3, extent=ext, origin=gray["origin"], interpolation="nearest")
    # kd17 change map
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_axes([0.01, 0.02, 0.68, 0.9])
    ax.imshow(d.vv.sel(year=last), **gray)
    blk = LinearSegmentedColormap.from_list("k", ["#000000", "#000000"])
    ax.imshow(halo(pers[last]), cmap=blk, origin=gray["origin"], **sk)
    ax.imshow(solid(pers[last] & ~vf), cmap=yel, origin=gray["origin"], **sk)
    ax.imshow(solid(pers[last] & vf), cmap=red, origin=gray["origin"], **sk)
    fl.plot(ax=ax, color="#2a9df4", lw=0.7, alpha=0.8)
    ax.set_xlim(ext[:2])
    ax.set_ylim(ext[2:])
    ax.set_axis_off()
    fig.text(0.01, 0.955, f"Candidate new structures on open land seen by radar, 2017-18 to {last} (exploratory)",
             fontsize=15, fontweight="bold")
    tot, vfa = df.iloc[-1].new_structures_ha, df.iloc[-1].on_valley_floor_ha
    by = s[s.up_km2 >= 0.25].groupby("system").radar_new_ha_100m.sum().sort_values(ascending=True)
    by = by[by.index != "other / outside city catchments"]
    fig.text(0.71, 0.88, "\n".join([
        "Grey: Sentinel-1 radar echo (bright = buildings).",
        "Candidates: ground that was dark (open) in 2017-18 and",
        "is now persistently building-bright. Yellow: higher",
        "ground; pink: valley floors (former wetland/floodplain,",
        "< 3 m above the drain). Marks enlarged for visibility.",
        "Blue: main drainage channels.", "",
        f"Candidates: {tot:,.0f} ha, of which {vfa:,.0f} ha on valley floors.", "",
        "How reliable? Against 10 m land-cover maps",
        "(2017 -> 2023) about 30% of candidates are confirmed",
        "new building - and radar catches only ~1% of all",
        "new building: most new homes are too small and low",
        "for yearly 20 m radar. Treat as leads for inspection,",
        "not a count of encroachment."]), fontsize=10.5, va="top")
    bx = fig.add_axes([0.80, 0.12, 0.17, 0.36])
    bx.barh(by.index, by.values, color="#ff2d55")
    bx.tick_params(axis="y", pad=10, length=0)
    bx.set_title("Candidates within 100 m of\nchannels, by system (ha)", fontsize=10, loc="left")
    bx.spines[["top", "right"]].set_visible(False)
    save(fig, "kd17_radar_new_construction.png", OUT, source=SRC)
    # kd18 small multiples
    show = [y for y in (2017, 2020, 2023, last) if y in years]
    fig = plt.figure(figsize=(16, 4.9))
    for k, y in enumerate(show):
        a = fig.add_axes([0.005 + k * 0.249, 0.03, 0.245, 0.84])
        a.imshow(d.vv.sel(year=y), **gray)
        cum = pers[y]
        a.imshow(halo(cum), cmap=LinearSegmentedColormap.from_list("k", ["#000000", "#000000"]), origin=gray["origin"], **sk)
        a.imshow(solid(cum & ~vf), cmap=yel, origin=gray["origin"], **sk)
        a.imshow(solid(cum & vf), cmap=red, origin=gray["origin"], **sk)
        fl.plot(ax=a, color="#2a9df4", lw=0.4, alpha=0.8)
        a.set_xlim(ext[:2])
        a.set_ylim(ext[2:])
        a.set_axis_off()
        r = df.set_index("year").loc[y]
        a.set_title(f"{y}: {r.new_structures_ha:,.0f} ha candidates ({r.on_valley_floor_ha:,.0f} ha on valley floors)",
                    fontsize=10, loc="left")
    fig.text(0.005, 0.95, "Kampala through radar eyes: candidate new structures on open land since 2017-18 (yellow; pink on "
             "valley floors). Exploratory: ~30% confirmed by land-cover maps.", fontsize=12.5, fontweight="bold")
    save(fig, "kd18_radar_panels.png", OUT, source=SRC)
    # animation
    BG = "#0f1419"
    fig = plt.figure(figsize=(9, 8.6), facecolor=BG)
    ax = fig.add_axes([0.02, 0.08, 0.96, 0.8])
    im = ax.imshow(d.vv.sel(year=years[0]), **gray)
    blank = np.full(vf.shape, np.nan)
    ov1 = ax.imshow(blank, cmap=yel, origin=gray["origin"], **sk)
    ov2 = ax.imshow(blank, cmap=red, origin=gray["origin"], **sk)
    flash = ax.imshow(blank, cmap=LinearSegmentedColormap.from_list("w", ["#ffffff", "#ffffff"]), origin=gray["origin"], **sk)
    fl.plot(ax=ax, color="#2a9df4", lw=0.5, alpha=0.8)
    ax.set_xlim(ext[:2])
    ax.set_ylim(ext[2:])
    ax.set_axis_off()
    fig.text(0.03, 0.965, "Kampala through radar eyes, 2017-2026", fontsize=16, fontweight="bold", color="white", va="top")
    fig.text(0.03, 0.925, "Sentinel-1 yearly radar (bright = buildings). Yellow/pink: candidate new structures on open land "
             "(pink: valley floors; white flash: new this year).\nExploratory - about 30% confirmed by land-cover maps. Blue: main channels.",
             fontsize=9.5, color="#9aa4ab", va="top")
    yr = fig.text(0.97, 0.965, "", fontsize=28, fontweight="bold", color="#ffd60a", ha="right", va="top")
    cnt = fig.text(0.03, 0.045, "", fontsize=12, color="white")
    fig.text(0.03, 0.012, "Radar: ESA Copernicus Sentinel-1 RTC (Microsoft Planetary Computer) · channels: © OpenStreetMap",
             fontsize=7.5, color="#9aa4ab")
    fig.text(0.97, 0.012, CREDIT, fontsize=10, color="white", fontweight="bold", ha="right")
    seq = [k for k in range(len(years)) for _ in range(3)] + [len(years) - 1] * 6

    def step(i):
        y = years[seq[i]]
        im.set_data(d.vv.sel(year=y))
        ov1.set_data(solid(pers[y] & ~vf))
        ov2.set_data(solid(pers[y] & vf))
        k_ = years.index(y)
        prev = pers[years[k_ - 1]] if k_ > 0 else np.zeros_like(pers[y])
        flash.set_data(solid(pers[y] & ~prev) if i % 3 == 0 else blank)  # this year's new ones blink
        r = df.set_index("year").loc[y]
        yr.set_text(str(y) + ("*" if y == 2026 else ""))
        cnt.set_text(f"Candidates: {r.new_structures_ha:,.0f} ha   on valley floors: {r.on_valley_floor_ha:,.0f} ha"
                     + ("   (*2026 to 12 Oct)" if y == 2026 else ""))
        return im, ov1, ov2, flash, yr, cnt
    FuncAnimation(fig, step, frames=len(seq)).save(OUT / "animations" / "kd_a4_radar_new_construction.gif",
                                                    writer=PillowWriter(fps=3), dpi=90, savefig_kwargs={"facecolor": BG})
    plt.close(fig)
    zooms(d, base, pers, vf, last, gray, ext)


def zooms(d, base, pers, vf, last, gray, ext):
    """The four largest clusters of candidates: radar before, radar after, and today's imagery."""
    import contextily as ctx
    from scipy import ndimage
    g = grow(pers[last], 3)
    lab, n = ndimage.label(g)
    sizes = ndimage.sum(pers[last], lab, range(1, n + 1))
    xs_, ys_ = d.x.values, d.y.values
    cen = ndimage.center_of_mass(pers[last], lab, range(1, n + 1))
    top, used = [], []
    for li in np.argsort(sizes)[::-1]:
        cy_, cx_ = cen[li]
        X_, Y_ = xs_[int(cx_)], ys_[int(cy_)]
        if all(np.hypot(X_ - u, Y_ - v) > 3000 for u, v in used):
            top.append(li + 1)
            used.append((X_, Y_))
        if len(top) == 4:
            break
    fig = plt.figure(figsize=(14, 19.5))
    xs, ys = d.x.values, d.y.values
    for r_, lid in enumerate(top):
        yy, xx = np.nonzero(lab == lid)
        cx, cy = xs[int(xx.mean())], ys[int(yy.mean())]
        h = 600
        win = dict(x=slice(cx - h, cx + h), y=slice(cy + h, cy - h) if ys[0] > ys[-1] else slice(cy - h, cy + h))
        import pyproj
        lo, la = pyproj.Transformer.from_crs(32636, 4326, always_xy=True).transform(cx, cy)
        on_vf = vf[yy, xx].mean() > 0.5
        for c_, (ttl, arr) in enumerate((("Radar 2017-18", base), (f"Radar {last}", d.vv.sel(year=last)))):
            a = fig.add_axes([0.005 + c_ * 0.333, 0.72 - r_ * 0.235, 0.325, 0.2])
            sub = arr.sel(**win)
            a.imshow(sub, cmap="gray", vmin=-22, vmax=2,
                     extent=[float(sub.x.min()), float(sub.x.max()), float(sub.y.min()), float(sub.y.max())],
                     origin="upper" if float(sub.y[0]) > float(sub.y[-1]) else "lower")
            if c_ == 1:
                m = xr.DataArray(pers[last], coords=dict(y=d.y, x=d.x), dims=("y", "x")).sel(**win)
                a.contour(m.x, m.y, m.values.astype(float), levels=[0.5], colors=["#ff2d95" if on_vf else "#ffe600"],
                          linewidths=1.6)
            a.set_aspect("equal")
            a.set_axis_off()
            a.set_title(f"{r_ + 1}. {ttl}", fontsize=10.5, loc="left")
        a = fig.add_axes([0.671, 0.72 - r_ * 0.235, 0.325, 0.2])
        a.set_xlim(cx - h, cx + h)
        a.set_ylim(cy - h, cy + h)
        try:
            ctx.add_basemap(a, crs="EPSG:32636", source=ctx.providers.Esri.WorldImagery, zoom=16, attribution=False)
        except Exception:  # noqa: BLE001
            pass
        a.set_axis_off()
        a.set_aspect("equal")
        a.set_title(f"{r_ + 1}. Imagery today ({la:.3f}°N, {lo:.3f}°E)" + ("\n    mostly on a valley floor" if on_vf else ""),
                    fontsize=10.5, loc="left")
    fig.text(0.005, 0.975, "The largest clusters of candidate new structures (at least 3 km apart)", fontsize=15,
             fontweight="bold", va="top")
    fig.text(0.005, 0.955, "Radar before (2017-18) and after, with candidate outlines, and today's imagery. 1.2 km squares; "
             "yellow outline: higher ground, pink: valley floor.", fontsize=10.5, color="#555", va="top")
    save(fig, "kd22_radar_cluster_zooms.png", OUT,
         source=SRC + " · imagery: Esri World Imagery (Esri, Maxar, Earthstar Geographics). Outlines: candidate new structures.")


if __name__ == "__main__":
    for st in sys.argv[1:] or ["annual", "figures"]:
        globals()[st]()
        print("done", st, flush=True)
