"""Kampala drainage study, part 8: analytic animations (+ still companions) -> figures/kampala_drainage/.

paving     channels coloured by how paved their upstream catchment is, 1975-2030 (JRC GHSL)  kd_a5 + kd19
drivers    cycles the eight pressures: map of each + hotspot-vs-other comparison              kd_a6 + kd20
landcover  valley-floor land cover 2017-2023 (Impact Observatory 10 m)                        kd_a7 + kd21
classes    current priority, emerging risk, then each work class in turn                      kd_a8 (still: kd12)
tour       slideshow of the nine hotspot-area pages                                           kd_a9
Every frame carries the credit and the data/map sources; text positions are fixed in layout slots so nothing
overlaps.
"""
import sys

import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap

from common import CREDIT, FIG, PROC, RES, ROOT, save
from kd_maps import CM, GRAY, LIGHT, SRC, UTM, load, place_labels
from kd_network import DRIVERS, KD

OUT = FIG / "kampala_drainage"
ANI = OUT / "animations"
INK, MUTE = "#1a1a1a", "#666"


def map_axes(fig, rect, s):
    ax = fig.add_axes(rect)
    f = s[s.up_km2 >= 0.25]
    x0, y0, x1, y1 = f.total_bounds
    ax.set_xlim(x0 - 500, x1 + 500)
    ax.set_ylim(y0 - 500, y1 + 500)
    ax.set_aspect("equal")
    ctx.add_basemap(ax, crs=f"EPSG:{UTM}", source=LIGHT, zoom=12, attribution=False)
    ax.set_axis_off()
    return ax


def footer(fig, source, y=0.012):
    fig.text(0.01, y, source, fontsize=7, color=MUTE, va="bottom", wrap=True)
    fig.text(0.99, y, CREDIT, fontsize=10, fontweight="bold", color="#333", ha="right", va="bottom")


# ---------------------------------------------------------------- paving upstream, 1975-2030
def paving_series():
    f = RES / "kd_segment_upstream_paving.csv"
    if f.exists():
        return pd.read_csv(f)
    import rasterio
    from pysheds.grid import Grid
    from pysheds.sview import Raster
    import kd_network as kn
    grid = Grid.from_raster(str(PROC / "kampala_dem.tif"))
    dem = grid.read_raster(str(PROC / "kampala_dem.tif"))
    inflated = grid.resolve_flats(grid.fill_depressions(grid.fill_pits(dem)))
    dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
    fdir = grid.flowdir(inflated, dirmap=dirmap)
    n = np.asarray(grid.accumulation(fdir, dirmap=dirmap), float)
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        cat, hand, acc = r.read(1), r.read(2), r.read(3)
        tr = r.transform
    H, W = acc.shape
    xs = tr.c + tr.a * (np.arange(W) + 0.5)
    ys = tr.f + tr.e * (np.arange(H) + 0.5)
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc")
    cell = (abs(float(np.diff(g.lon).mean())) * 111320 * np.cos(np.deg2rad(0.3))) * (abs(float(np.diff(g.lat).mean())) * 111320)
    s = kn.segments()
    z = np.zeros_like(acc)
    out = {"seg_id": s.seg_id.values}
    for e in (1975, 1985, 1995, 2005, 2015, 2020, 2025, 2030):
        b = np.clip(g.sel(epoch=e).sel(lat=ys, lon=xs, method="nearest").values / cell, 0, 1)
        up = np.asarray(grid.accumulation(fdir, weights=Raster(b.astype("float64"), viewfinder=fdir.viewfinder),
                                          dirmap=dirmap), float) / np.maximum(n, 1)
        R = dict(tr=tr, acc=acc, cat=cat, hand=hand, up={1990: up, 2020: up}, vb={1990: z, 2020: z}, wet=z, valley_share=z)
        out[f"up_built_{e}"] = kn.sample(s, R).u20.reindex(range(len(s))).values
        print("paving epoch", e, flush=True)
    df = pd.DataFrame(out)
    df.round(4).to_csv(f, index=False)
    return df


def paving():
    s, hp, city = load()
    df = paving_series().set_index("seg_id")
    f = s[s.up_km2 >= 0.25].drop(columns=[c for c in df.columns if c in s.columns]).join(df, on="seg_id")
    epochs = [1975, 1985, 1995, 2005, 2015, 2020, 2025, 2030]
    km30 = [f.length_m[f[f"up_built_{e}"] >= 0.30].sum() / 1000 for e in epochs]
    cm = LinearSegmentedColormap.from_list("p", ["#fff5d6", "#fdb863", "#e66101", "#7f2704"])
    src = "Built-up: JRC GHSL R2023A (2025, 2030 projected) · flow routing: Copernicus GLO-30 DEM · channels: © OpenStreetMap contributors" + GRAY
    # still: four epochs
    fig = plt.figure(figsize=(16, 6.4))
    for k, e in enumerate((1975, 1995, 2015, 2030)):
        ax = map_axes(fig, [0.005 + k * 0.2, 0.08, 0.195, 0.78], s)
        ff = f.sort_values(f"up_built_{e}")
        ff.plot(ax=ax, column=f"up_built_{e}", cmap=cm, vmin=0, vmax=0.6, lw=np.where(ff.up_km2 >= 2, 1.6, 0.7))
        ax.set_title(f"{e}{' (projected)' if e > 2020 else ''}: {km30[epochs.index(e)]:.0f} km", fontsize=10.5, loc="left")
    bx = fig.add_axes([0.83, 0.2, 0.16, 0.6])
    bx.plot(epochs, km30, color="#e66101", lw=2.5, marker="o")
    bx.axvspan(2020, 2031, color="#eee", lw=0)
    bx.set_title("km of channel whose catchment\nis more than 30% paved", fontsize=9.5, loc="left")
    bx.spines[["top", "right"]].set_visible(False)
    fig.text(0.005, 0.95, "Paving creeps up Kampala's catchments: channels coloured by the built-up share upstream, "
             "1975-2030", fontsize=14, fontweight="bold")
    sm = plt.cm.ScalarMappable(cmap=cm, norm=plt.Normalize(0, 60))
    cb = fig.colorbar(sm, cax=fig.add_axes([0.25, 0.06, 0.3, 0.02]), orientation="horizontal")
    cb.set_label("upstream built-up share (%)", fontsize=9)
    save(fig, "kd19_paving_upstream.png", OUT, source=src)
    # animation
    fig = plt.figure(figsize=(11, 8))
    ax = map_axes(fig, [0.0, 0.08, 0.66, 0.8], s)
    place_labels(ax, maxn=14, pad=2.4)
    lines = ax.collections[-1] if ax.collections else None
    ff = f.copy()
    pc = ff.plot(ax=ax, column="up_built_1975", cmap=cm, vmin=0, vmax=0.6, lw=np.where(ff.up_km2 >= 2, 2.2, 0.9)).collections[-1]
    fig.text(0.02, 0.955, "Paving creeps up Kampala's catchments", fontsize=16, fontweight="bold", va="top")
    fig.text(0.02, 0.915, "Each channel coloured by how much of the land draining to it is built up.", fontsize=10.5,
             color=MUTE, va="top")
    yr = fig.text(0.97, 0.955, "", fontsize=28, fontweight="bold", color="#e66101", ha="right", va="top")
    bx = fig.add_axes([0.71, 0.42, 0.26, 0.36])
    bx.set_xlim(1972, 2033)
    bx.set_ylim(0, max(km30) * 1.2)
    bx.axvspan(2020, 2033, color="#eee", lw=0)
    bx.text(2026.5, max(km30) * 1.12, "projected", ha="center", fontsize=8, color=MUTE)
    bx.set_title("km of channel whose catchment\nis more than 30% paved", fontsize=10, loc="left")
    bx.spines[["top", "right"]].set_visible(False)
    ln, = bx.plot([], [], color="#e66101", lw=2.5, marker="o")
    cb = fig.colorbar(plt.cm.ScalarMappable(cmap=cm, norm=plt.Normalize(0, 60)),
                      cax=fig.add_axes([0.71, 0.27, 0.26, 0.025]), orientation="horizontal")
    cb.set_label("upstream built-up share (%)", fontsize=9)
    footer(fig, "Built-up: JRC GHSL R2023A · DEM: Copernicus GLO-30 · channels: © OpenStreetMap ·\nbasemap: Esri World Gray Canvas")
    seq = [k for k in range(len(epochs)) for _ in range(3)] + [len(epochs) - 1] * 6

    def step(i):
        k = seq[i]
        e = epochs[k]
        pc.set_array(ff[f"up_built_{e}"].values)
        yr.set_text(f"{e}{'*' if e > 2020 else ''}")
        ln.set_data(epochs[:k + 1], km30[:k + 1])
        return pc, yr, ln
    FuncAnimation(fig, step, frames=len(seq)).save(ANI / "kd_a5_paving_upstream.gif", writer=PillowWriter(fps=3), dpi=85)
    plt.close(fig)
    print("km channel >30% paved", dict(zip(epochs, np.round(km30))))


# ---------------------------------------------------------------- drivers
def drivers():
    s, hp, city = load()
    m = s[s.up_km2 >= 0.25].copy()
    X = pd.DataFrame({k: m[k].rank(pct=True) for k in DRIVERS})
    d = pd.read_csv(RES / "kd_drivers.csv").set_index("driver")
    order = list(d.sort_values("hotspot_median_pct").index)
    cm = LinearSegmentedColormap.from_list("d", ["#f7f7f7", "#9ecae1", "#3182bd", "#08306b"])
    # still: 2 x 4 small multiples
    fig = plt.figure(figsize=(16, 9.4))
    for k, key in enumerate(order[::-1]):
        r_, c_ = divmod(k, 4)
        ax = map_axes(fig, [0.005 + c_ * 0.249, 0.47 - r_ * 0.44, 0.244, 0.40], s)
        mm = m.assign(v=X[key]).sort_values("v")
        mm.plot(ax=ax, column="v", cmap=cm, vmin=0, vmax=1, lw=np.where(mm.up_km2 >= 2, 1.4, 0.6))
        hp.plot(ax=ax, marker="o", facecolor="none", edgecolor="#d7191c", markersize=14, lw=0.8)
        ax.set_title(DRIVERS[key], fontsize=10.5, loc="left")
    fig.text(0.005, 0.955, "The eight pressures on Kampala's channels (darker = higher percentile; red circles: reported "
             "flood hotspots)", fontsize=14, fontweight="bold")
    save(fig, "kd20_driver_maps.png", OUT, source=SRC + GRAY)
    # animation
    fig = plt.figure(figsize=(13, 7.6))
    ax = map_axes(fig, [0.0, 0.14, 0.55, 0.74], s)
    mm = m.copy()
    pc = mm.plot(ax=ax, column=X[order[0]].values, cmap=cm, vmin=0, vmax=1,
                 lw=np.where(mm.up_km2 >= 2, 1.9, 0.8)).collections[-1]
    hp.plot(ax=ax, marker="o", facecolor="none", edgecolor="#d7191c", markersize=30, lw=1.1, zorder=5)
    fig.text(0.02, 0.955, "What sets Kampala's flood hotspots apart?", fontsize=16, fontweight="bold", va="top")
    ttl = fig.text(0.02, 0.91, "", fontsize=12, color="#08306b", fontweight="bold", va="top")
    bx = fig.add_axes([0.80, 0.16, 0.18, 0.66])
    y = np.arange(len(order))
    labs = [DRIVERS[k] for k in order]
    bx.set_yticks(y)
    bx.set_yticklabels(labs, fontsize=8.5)
    bx.set_xlim(0, 100)
    bx.set_ylim(-0.6, len(order) - 0.4)
    bx.set_xlabel("median percentile", fontsize=8.5)
    bx.spines[["top", "right"]].set_visible(False)
    same = (d.loc[order].other_median_pct - d.loc[order].hotspot_median_pct).abs().values < 0.02
    off = np.where(same, 0.14, 0.0)
    segs = bx.hlines(y, d.loc[order].other_median_pct * 100, d.loc[order].hotspot_median_pct * 100, color="#ccc", lw=2)
    s1 = bx.scatter(d.loc[order].other_median_pct * 100, y + off, color="#2c7bb6", s=40, zorder=3, label="other channels")
    s2 = bx.scatter(d.loc[order].hotspot_median_pct * 100, y - off, color="#d7191c", s=40, zorder=3, label="near hotspots")
    bx.legend(loc="upper center", bbox_to_anchor=(0.3, -0.08), fontsize=8, ncol=1, frameon=False)
    hl = bx.axhspan(-0.5, 0.5, color="#fff3b0", zorder=0)
    cb = fig.colorbar(plt.cm.ScalarMappable(cmap=cm, norm=plt.Normalize(0, 100)),
                      cax=fig.add_axes([0.10, 0.085, 0.35, 0.016]), orientation="horizontal")
    cb.set_label("percentile among channel segments (red circles: reported hotspots)", fontsize=8.5)
    footer(fig, "Channels, waste, places: © OpenStreetMap · buildings: Microsoft · built-up: JRC GHSL · DEM: Copernicus · "
                "wetland: ESA WorldCover · hotspots: KCCA/NEMA & news (approx.) · basemap: Esri World Gray Canvas")
    seq = [k for k in range(len(order)) for _ in range(3)]

    def step(i):
        k = seq[i]
        key = order[::-1][k]
        pc.set_array(X[key].values)
        r = d.loc[key]
        ttl.set_text(f"{DRIVERS[key]}: hotspots {r.hotspot_median_pct * 100:.0f}th vs other channels "
                     f"{r.other_median_pct * 100:.0f}th percentile")
        yy = order.index(key)
        hl.set_y(yy - 0.5) if hasattr(hl, "set_y") else hl.set_xy([[0, yy - 0.5], [0, yy + 0.5], [1, yy + 0.5], [1, yy - 0.5]])
        return pc, ttl, hl
    FuncAnimation(fig, step, frames=len(seq)).save(ANI / "kd_a6_hotspot_drivers.gif", writer=PillowWriter(fps=1), dpi=80)
    plt.close(fig)


# ---------------------------------------------------------------- valley land cover
def landcover():
    import rasterio
    from rasterio.warp import Resampling, reproject
    lc = xr.open_dataarray(KD / "sat_iolulc.nc")
    lc = lc.isel(x=slice(None, None, 2), y=slice(None, None, 2))  # 20 m for speed
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand = r.read(2)
        src_tr = r.transform
    from affine import Affine
    tr = Affine(float(lc.x[1] - lc.x[0]), 0, float(lc.x[0]) - float(lc.x[1] - lc.x[0]) / 2, 0,
                float(lc.y[1] - lc.y[0]), float(lc.y[0]) - float(lc.y[1] - lc.y[0]) / 2)
    hv = np.full(lc.shape[1:], np.nan, np.float32)
    reproject(hand, hv, src_transform=src_tr, src_crs="EPSG:4326", dst_transform=tr, dst_crs="EPSG:32636",
              resampling=Resampling.nearest)
    vf = hv < 3
    classes = {7: ("built-up", "#d7301f"), 2: ("trees", "#238b45"), 5: ("crops", "#fec44f"), 11: ("rangeland/grass", "#c7a26b"),
               4: ("wetland (flooded vegetation)", "#41b6c4"), 1: ("water", "#2171b5"), 8: ("bare ground", "#969696")}
    years = [int(v) for v in lc.time.values]
    codes = list(classes)
    cmap = LinearSegmentedColormap.from_list("lc", [classes[c][1] for c in codes], N=len(codes))

    def img(y):
        a = lc.sel(time=y).values
        out = np.full(a.shape, np.nan)
        for k, c in enumerate(codes):
            out[(a == c) & vf] = k
        return out
    shares = pd.DataFrame({classes[c][0]: [((lc.sel(time=y).values == c) & vf).sum() / vf.sum() * 100 for y in years]
                           for c in codes}, index=years)
    shares.round(2).to_csv(RES / "kd_valley_landcover_core.csv")
    ext = [float(lc.x.min()), float(lc.x.max()), float(lc.y.min()), float(lc.y.max())]
    src = ("Land cover: Impact Observatory / Esri 10 m annual (io-lulc v02, Microsoft Planetary Computer) · valley floors: "
           "Copernicus GLO-30 DEM (HAND < 3 m)")
    # still: 2017 vs 2023
    fig = plt.figure(figsize=(15, 7.2))
    for k, y in enumerate((years[0], years[-1])):
        ax = fig.add_axes([0.005 + k * 0.33, 0.06, 0.32, 0.82])
        ax.imshow(np.where(vf, np.nan, 1), cmap=LinearSegmentedColormap.from_list("g", ["#eeeeee", "#eeeeee"]), extent=ext)
        ax.imshow(img(y), cmap=cmap, vmin=-0.5, vmax=len(codes) - 0.5, extent=ext, interpolation="nearest")
        ax.set_axis_off()
        ax.set_title(f"{y}: built-up {shares.loc[y, 'built-up']:.0f}% of the valley floor", fontsize=11, loc="left")
    lx = fig.add_axes([0.68, 0.45, 0.31, 0.42])
    for c in codes[:5]:
        lx.plot(years, shares[classes[c][0]], color=classes[c][1], lw=2.2, marker="o", label=classes[c][0])
    lx.set_title("Share of valley floor (%)", fontsize=10.5, loc="left")
    lx.legend(fontsize=8.5, loc="center left", bbox_to_anchor=(0.0, -0.45), ncol=2, frameon=False)
    lx.spines[["top", "right"]].set_visible(False)
    fig.text(0.005, 0.955, "What covers Kampala's valley floors (former wetlands and floodplains), 2017 vs 2023",
             fontsize=14, fontweight="bold")
    save(fig, "kd21_valley_landcover_maps.png", OUT, source=src)
    # animation
    fig = plt.figure(figsize=(12, 7.4))
    ax = fig.add_axes([0.0, 0.07, 0.6, 0.82])
    ax.imshow(np.where(vf, np.nan, 1), cmap=LinearSegmentedColormap.from_list("g", ["#eeeeee", "#eeeeee"]), extent=ext)
    im = ax.imshow(img(years[0]), cmap=cmap, vmin=-0.5, vmax=len(codes) - 0.5, extent=ext, interpolation="nearest")
    ax.set_axis_off()
    fig.text(0.02, 0.955, "Kampala's valley floors, year by year", fontsize=16, fontweight="bold", va="top")
    fig.text(0.02, 0.915, "Only land < 3 m above the nearest drain is coloured (former wetlands and floodplains).",
             fontsize=10.5, color=MUTE, va="top")
    yr = fig.text(0.97, 0.955, "", fontsize=28, fontweight="bold", color="#d7301f", ha="right", va="top")
    lx = fig.add_axes([0.66, 0.50, 0.31, 0.34])
    lx.set_xlim(years[0] - 0.5, years[-1] + 0.5)
    lx.set_ylim(0, max(shares.max()) * 1.15)
    lx.set_title("Share of valley floor (%)", fontsize=10, loc="left")
    lx.spines[["top", "right"]].set_visible(False)
    lns = {c: lx.plot([], [], color=classes[c][1], lw=2.2, marker="o")[0] for c in codes[:5]}
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=classes[c][1], label=classes[c][0]) for c in codes], loc="upper left",
               bbox_to_anchor=(0.66, 0.40), fontsize=8.5, frameon=False, ncol=2)
    footer(fig, "Land cover: Impact Observatory/Esri 10 m annual (io-lulc v02) · valley floors: Copernicus GLO-30 DEM")
    seq = [k for k in range(len(years)) for _ in range(2)] + [len(years) - 1] * 4

    def step(i):
        k = seq[i]
        im.set_data(img(years[k]))
        yr.set_text(str(years[k]))
        for c, l_ in lns.items():
            l_.set_data(years[:k + 1], shares[classes[c][0]].values[:k + 1])
        return [im, yr] + list(lns.values())
    FuncAnimation(fig, step, frames=len(seq)).save(ANI / "kd_a7_valley_landcover.gif", writer=PillowWriter(fps=2), dpi=80)
    plt.close(fig)
    print(shares.round(1).to_string())


# ---------------------------------------------------------------- priority vs emerging, revealed
def classes():
    s, hp, city = load()
    f = s[s.risk_pct.notna()].copy()
    f["now"] = pd.cut(f.risk_pct, [-1, 100 / 3, 200 / 3, 101], labels=[0, 1, 2]).astype(int)
    f["fut"] = pd.cut(f.emerging_pct, [-1, 100 / 3, 200 / 3, 101], labels=[0, 1, 2]).astype(int)
    grid = [["#e8e8e8", "#e4acac", "#c85a5a"], ["#b0d5df", "#ad9ea5", "#985356"], ["#64acbe", "#627f8c", "#574249"]]
    f["col"] = [grid[b][a] for a, b in zip(f.now, f.fut)]
    cls = [("Urgent: high now AND still worsening", (f.now == 2) & (f.fut >= 1), "#574249"),
           ("Fix now: high priority, stable", (f.now == 2) & (f.fut == 0), "#c85a5a"),
           ("Coming: rising risk, not yet high", (f.now <= 1) & (f.fut == 2), "#64acbe"),
           ("Watch: moderate on both", (f.now == 1) & (f.fut == 1), "#ad9ea5"),
           ("Low on both", (f.now == 0) & (f.fut <= 1), "#bdbdbd")]
    km = [f.length_m[m_].sum() / 1000 for _, m_, _ in cls]
    tot = f.length_m.sum() / 1000
    fig = plt.figure(figsize=(13, 7.6))
    ax = map_axes(fig, [0.0, 0.08, 0.58, 0.8], s)
    lw = np.where(f.up_km2 >= 2, 2.0, 0.9)
    pc = f.plot(ax=ax, color=f.col, lw=lw).collections[-1]
    place_labels(ax, maxn=12, pad=2.4)
    fig.text(0.02, 0.955, "How much drainage work is waiting?", fontsize=16, fontweight="bold", va="top")
    ttl = fig.text(0.02, 0.91, "", fontsize=12, fontweight="bold", va="top")
    bx = fig.add_axes([0.62, 0.18, 0.35, 0.62])
    y = np.arange(len(cls))[::-1]
    bars = bx.barh(y, km, color=[c for _, _, c in cls], height=0.45, edgecolor="#555", lw=0.5)
    for yy, (n_, _, _), v in zip(y, cls, km):
        bx.text(0, yy + 0.32, n_, fontsize=9.5, fontweight="bold", va="bottom", color="#333")
        bx.text(v + tot * 0.01, yy, f"{v:.0f} km ({100 * v / tot:.0f}%)", va="center", fontsize=9)
    bx.set_yticks([])
    bx.set_ylim(-0.6, len(cls) - 0.1)
    bx.set_xlim(0, max(km) * 1.5)
    bx.set_xlabel(f"km of channel (of {tot:.0f} km with >= 0.25 km² upstream)", fontsize=9)
    bx.spines[["top", "right", "left"]].set_visible(False)
    footer(fig, "Channels, waste, places: © OpenStreetMap · buildings: Microsoft · built-up: JRC GHSL · DEM: Copernicus · "
                "wetland: ESA WorldCover · basemap: Esri World Gray Canvas")
    risk_c = [CM(v / 100) for v in f.risk_pct]
    emer_c = [plt.cm.magma_r(v / 100) for v in f.emerging_pct]
    frames = [("Step 1. Current maintenance priority (red = high)", risk_c, None),
              ("Step 2. Emerging risk: growth since 1990 (dark = high)", emer_c, None),
              ("Step 3. Both together", list(f.col), None)] + \
             [(f"{n_}: {v:.0f} km", [c if m_.loc[i_] else "#e6e6e6" for i_, c in zip(f.index, f.col)], k)
              for k, ((n_, m_, _), v) in enumerate(zip(cls, km))] + [("All classes", list(f.col), None)]
    seq = [k for k in range(len(frames)) for _ in range(3)]

    def step(i):
        t, cols, hk = frames[seq[i]]
        pc.set_color(cols)
        ttl.set_text(t)
        for k, b in enumerate(bars):
            b.set_alpha(1.0 if hk is None or hk == k else 0.25)
        return pc, ttl
    FuncAnimation(fig, step, frames=len(seq)).save(ANI / "kd_a8_priority_vs_emerging.gif", writer=PillowWriter(fps=1), dpi=80)
    plt.close(fig)


# ---------------------------------------------------------------- tour of area pages
def tour():
    from PIL import Image
    pages = sorted((OUT / "areas").glob("kd13_*.png"))
    frames = []
    for p in pages:
        im = Image.open(p).convert("RGB")
        w = 1400
        frames.append(im.resize((w, int(im.height * w / im.width)), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE))
    frames[0].save(ANI / "kd_a9_hotspot_area_tour.gif", save_all=True, append_images=frames[1:], duration=4000, loop=0)


if __name__ == "__main__":
    for st in sys.argv[1:] or ["drivers", "landcover", "classes", "paving"]:
        globals()[st]()
        print("done", st, flush=True)
