"""Kampala drainage study, part 6: animations -> figures/kampala_drainage/animations/.

valley     built-up surface 1975-2030 (JRC GHSL), with the valley floors (HAND < 3 m: former wetlands and
           floodplains) highlighted; counter of the valley floor built over
people    residents on low ground (< 2 m above the nearest drain, within 150 m of a flowing channel), GHS-POP 1975-2030
timelapse Landsat dry-season true colour, Lubigi and Kinawataka wetlands, 1986-2025 (every ~5 years)
All frames carry "Credit: Gava Charles".
"""
import sys

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap

from common import FIG, PROC, ROOT

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage" / "animations"
OUT.mkdir(parents=True, exist_ok=True)
BOX = (32.45, 0.20, 32.72, 0.42)
BG, INK, MUTE = "#0f1419", "#f2f2f2", "#9aa4ab"
CREDIT = "Credit: Gava Charles"


def grid_hand(lat, lon):
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand, acc = r.read(2), r.read(3)
        tr = r.transform
    LO, LA = np.meshgrid(lon, lat)
    col = ((LO - tr.c) / tr.a).astype(int).clip(0, hand.shape[1] - 1)
    row = ((LA - tr.f) / tr.e).astype(int).clip(0, hand.shape[0] - 1)
    return hand[row, col], acc[row, col]


def overlays(ax):
    s = gpd.read_file(KD / "segments.gpkg")
    s[s.up_km2 >= 2].plot(ax=ax, color="#4fc3f7", lw=0.6, alpha=0.8, zorder=4)
    d2 = gpd.read_file(PROC / "uganda_adm2.geojson")
    d2[d2.shapeName == "Kampala"].boundary.plot(ax=ax, color="#bbbbbb", lw=0.7, ls="--", zorder=4)


def frame_text(fig, title, sub, source):
    fig.text(0.04, 0.95, title, fontsize=17, fontweight="bold", color=INK, va="top")
    fig.text(0.04, 0.905, sub, fontsize=10.5, color=MUTE, va="top")
    fig.text(0.04, 0.015, source, fontsize=8, color=MUTE)
    fig.text(0.97, 0.015, CREDIT, fontsize=10, color=INK, fontweight="bold", ha="right", alpha=0.85)


def valley():
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc").sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    cell = (abs(float(np.diff(g.lon).mean())) * 111320 * np.cos(np.deg2rad(0.3))) * (abs(float(np.diff(g.lat).mean())) * 111320)
    frac = np.clip(g.values / cell, 0, 1)
    hand, _ = grid_hand(g.lat.values, g.lon.values)
    vf = hand < 3
    epochs = list(g.epoch.values)
    share = [float((frac[k] * vf).sum() / vf.sum()) * 100 for k in range(len(epochs))]
    fig = plt.figure(figsize=(9, 9.6), facecolor=BG)
    ax = fig.add_axes([0.03, 0.12, 0.94, 0.74], facecolor=BG)
    ext = [float(g.lon.min()), float(g.lon.max()), float(g.lat.min()), float(g.lat.max())]
    ax.imshow(np.where(vf, 1, np.nan), cmap=LinearSegmentedColormap.from_list("v", ["#16323d", "#16323d"]), extent=ext,
              origin="lower", zorder=1)
    up = ax.imshow(np.where(~vf, frac[0], np.nan), cmap=LinearSegmentedColormap.from_list("u", ["#0f1419", "#b0b7bd"]),
                   vmin=0, vmax=0.8, extent=ext, origin="lower", zorder=2)
    vb = ax.imshow(np.where(vf, frac[0], np.nan), cmap=LinearSegmentedColormap.from_list("b", ["#16323d", "#ff5a36", "#ffd166"]),
                   vmin=0, vmax=0.8, extent=ext, origin="lower", zorder=3)
    s = gpd.read_file(KD / "segments.gpkg")
    s[s.up_km2 >= 2].plot(ax=ax, color="#4fc3f7", lw=0.5, alpha=0.7, zorder=4)
    ax.set_xlim(ext[:2])
    ax.set_ylim(ext[2:])
    ax.set_aspect("equal")
    ax.axis("off")
    frame_text(fig, "Kampala is building over its valley floors",
               "Teal: valley floors (former wetlands and floodplains, < 3 m above the nearest drain).\n"
               "Orange-yellow: buildings on them. Grey: buildings elsewhere. Blue lines: main channels.",
               "Data: JRC GHSL built-up surface 1975-2030 (2025, 2030 projected); Copernicus GLO-30 DEM; channels © OpenStreetMap contributors.")
    yr = fig.text(0.96, 0.95, "", fontsize=30, fontweight="bold", color="#ffd166", ha="right", va="top")
    cnt = fig.text(0.04, 0.085, "", fontsize=14, color=INK)
    seq = [k for k in range(len(epochs)) for _ in range(3)] + [len(epochs) - 1] * 8

    def step(i):
        k = seq[i]
        up.set_data(np.where(~vf, frac[k], np.nan))
        vb.set_data(np.where(vf, frac[k], np.nan))
        yr.set_text(f"{epochs[k]}{'*' if epochs[k] > 2020 else ''}")
        cnt.set_text(f"Valley floor built over: {share[k]:.0f}%" + ("   (* projected)" if epochs[k] > 2020 else ""))
        return up, vb, yr, cnt
    FuncAnimation(fig, step, frames=len(seq)).save(OUT / "kd_a1_valley_floors_built.gif", writer=PillowWriter(fps=4),
                                                    dpi=90, savefig_kwargs={"facecolor": BG})
    plt.close(fig)
    print("valley floor built %", dict(zip(epochs, np.round(share, 1))))


def people():
    import shapely
    pop = xr.open_dataarray(PROC / "kampala_ghs_pop.nc").sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    hand, _ = grid_hand(pop.lat.values, pop.lon.values)
    s = gpd.read_file(KD / "segments.gpkg").to_crs(32636)
    fl = s[s.up_km2 >= 0.25]
    LO, LA = np.meshgrid(pop.lon.values, pop.lat.values)
    pts = gpd.GeoSeries(gpd.points_from_xy(LO.ravel(), LA.ravel()), crs=4326).to_crs(32636).values
    idx = np.unique(shapely.STRtree(pts).query(fl.geometry.values, predicate="dwithin", distance=150)[1])
    risk = np.zeros(LO.size, bool)
    risk[idx] = True
    risk = risk.reshape(LO.shape) & (hand < 2)
    epochs = list(pop.epoch.values)
    tot = [float(pop.sel(epoch=e).values[risk].sum()) for e in epochs]
    allp = [float(pop.sel(epoch=e).values.sum()) for e in epochs]
    pd.DataFrame({"epoch": epochs, "pop_low_ground": tot, "pop_box": allp}).round(0).to_csv(
        ROOT / "results" / "kd_population_low_ground.csv", index=False)
    fig = plt.figure(figsize=(9, 10), facecolor=BG)
    ax = fig.add_axes([0.03, 0.25, 0.94, 0.62], facecolor=BG)
    ext = [float(pop.lon.min()), float(pop.lon.max()), float(pop.lat.min()), float(pop.lat.max())]
    base = ax.imshow(np.log10(1 + pop.sel(epoch=epochs[0]).values), cmap=LinearSegmentedColormap.from_list("g", [BG, "#55606a"]),
                     vmin=0, vmax=2.6, extent=ext, origin="lower", zorder=1)
    hot = ax.imshow(np.where(risk, np.log10(1 + pop.sel(epoch=epochs[0]).values), np.nan),
                    cmap=LinearSegmentedColormap.from_list("h", ["#3b0f2e", "#d6336c", "#ffb703", "#fff3b0"]),
                    vmin=0, vmax=2.6, extent=ext, origin="lower", zorder=3)
    s[s.up_km2 >= 2].to_crs(4326).plot(ax=ax, color="#4fc3f7", lw=0.5, alpha=0.6, zorder=4)
    ax.set_xlim(ext[:2])
    ax.set_ylim(ext[2:])
    ax.set_aspect("equal")
    ax.axis("off")
    frame_text(fig, "More people are living where the water goes",
               "Bright: residents on low ground (< 2 m above the drain, within 150 m of a channel).\n"
               "Grey: everyone else. Blue lines: main channels.",
               "Data: JRC GHS-POP R2023A, 100 m (2025, 2030 projected); Copernicus DEM; OpenStreetMap drains.")
    yr = fig.text(0.96, 0.95, "", fontsize=30, fontweight="bold", color="#ffb703", ha="right", va="top")
    sp = fig.add_axes([0.10, 0.08, 0.84, 0.13], facecolor=BG)
    sp.set_xlim(epochs[0] - 1, epochs[-1] + 1)
    sp.set_ylim(0, max(tot) * 1.25)
    for side in sp.spines.values():
        side.set_visible(False)
    sp.tick_params(colors=MUTE, labelsize=9)
    sp.grid(False)
    sp.set_yticks([])
    line, = sp.plot([], [], color="#ffb703", lw=2.4)
    dot, = sp.plot([], [], "o", color="#fff3b0", ms=7)
    lab = sp.text(0, 0, "", color=INK, fontsize=12, fontweight="bold")
    seq = [k for k in range(len(epochs)) for _ in range(3)] + [len(epochs) - 1] * 8

    def step(i):
        k = seq[i]
        p = pop.sel(epoch=epochs[k]).values
        base.set_data(np.log10(1 + p))
        hot.set_data(np.where(risk, np.log10(1 + p), np.nan))
        yr.set_text(f"{epochs[k]}{'*' if epochs[k] > 2020 else ''}")
        line.set_data(epochs[:k + 1], tot[:k + 1])
        dot.set_data([epochs[k]], [tot[k]])
        lab.set_position((epochs[k] - 1, tot[k] + max(tot) * 0.08))
        lab.set_ha("right" if k > len(epochs) / 2 else "left")
        lab.set_text(f"{tot[k] / 1000:,.0f}k people on low ground")
        return base, hot, yr, line, dot, lab
    FuncAnimation(fig, step, frames=len(seq)).save(OUT / "kd_a2_people_on_low_ground.gif", writer=PillowWriter(fps=4),
                                                    dpi=90, savefig_kwargs={"facecolor": BG})
    plt.close(fig)
    print("people on low ground", dict(zip(epochs, np.round(tot, -2))))


def channels_px(ax, d, lw=1.1):
    """Draw today's main channels (>= 0.25 km2 upstream) in the pixel coordinates of raster d (EPSG:32636)."""
    s = gpd.read_file(KD / "segments.gpkg").to_crs(32636)
    s = s[s.up_km2 >= 0.25]
    x0, dx = float(d.x[0]), float(d.x[1] - d.x[0])
    y0, dy = float(d.y[0]), float(d.y[1] - d.y[0])
    for g, a in zip(s.geometry, s.up_km2):
        xy = np.asarray(g.coords)
        big = a >= 2
        ax.plot((xy[:, 0] - x0) / dx, (xy[:, 1] - y0) / dy, color="#4fc3f7" if big else "#b3e5fc",
                lw=lw * (0.9 if big else 0.35), alpha=0.85 if big else 0.5, solid_capstyle="round")
    ax.set_xlim(-0.5, d.sizes["x"] - 0.5)
    ax.set_ylim(d.sizes["y"] - 0.5, -0.5)


def timelapse():
    import pystac_client
    import planetary_computer as pc
    from odc.stac import load
    bbox = [32.50, 0.305, 32.665, 0.375]  # Lubigi (west) to Kinawataka (east)
    f = KD / "sat_landsat_timelapse.nc"
    if not f.exists():
        cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
        frames = []
        for y, plats in ((1986, ["landsat-5"]), (1990, ["landsat-5"]), (1995, ["landsat-5"]), (2000, ["landsat-5", "landsat-7"]),
                         (2005, ["landsat-5"]), (2010, ["landsat-5"]), (2015, ["landsat-8"]), (2020, ["landsat-8"]),
                         (2025, ["landsat-8", "landsat-9"])):
            items = []
            for yy in (y - 1, y, y + 1):
                items += list(cat.search(collections=["landsat-c2-l2"], bbox=bbox, datetime=f"{yy}-01-01/{yy}-12-31",
                                         query={"eo:cloud_cover": {"lt": 50}, "platform": {"in": plats}}).items())
            if not items:
                print("no scenes", y)
                continue
            ds = load(items, bands=["red", "green", "blue", "qa_pixel"], bbox=bbox, crs="EPSG:32636", resolution=30,
                      groupby="solar_day", chunks={})
            qa = ds.qa_pixel
            clear = ((qa & (1 << 3)) == 0) & ((qa & (1 << 4)) == 0) & ((qa & (1 << 1)) == 0) & (qa != 0)
            m = ds[["red", "green", "blue"]].where(clear).median("time")
            m = (m * 0.0000275 - 0.2).astype("float32").compute().expand_dims(year=[y])
            frames.append(m)
            print("timelapse", y, len(items), flush=True)
        xr.concat(frames, "year").to_netcdf(f)
    d = xr.open_dataset(f)
    rgb = lambda k: np.clip(np.nan_to_num(np.dstack([d.red.isel(year=k), d.green.isel(year=k), d.blue.isel(year=k)])) * 3.4,
                            0, 1) ** 0.85
    fig = plt.figure(figsize=(12, 7.2), facecolor=BG)
    ax = fig.add_axes([0.01, 0.07, 0.98, 0.78])
    im = ax.imshow(rgb(0))
    ax.axis("off")
    channels_px(ax, d)
    import pyproj
    tf = pyproj.Transformer.from_crs(4326, 32636, always_xy=True)
    xs, ys = d.x.values, d.y.values
    for name, lo, la in (("Lubigi wetland", 32.545, 0.345), ("Kinawataka wetland", 32.645, 0.335),
                         ("Bwaise", 32.562, 0.352), ("Nakawa", 32.615, 0.329)):
        x, y = tf.transform(lo, la)
        ax.text(np.abs(xs - x).argmin(), np.abs(ys - y).argmin(), name, color="white", fontsize=10, fontweight="bold",
                ha="center", bbox=dict(facecolor="#00000088", edgecolor="none", pad=2))
    frame_text(fig, "Kampala's wetlands from space, 1986-2025",
               "Landsat median, true colour, 30 m: dark green valley floors (wetland) give way to buildings.\n"
               "Blue lines: today's drainage channels.",
               "Imagery: NASA/USGS Landsat 5, 7, 8, 9 Collection 2 (Microsoft Planetary Computer) · channels: © OpenStreetMap contributors.")
    yr = fig.text(0.96, 0.95, "", fontsize=30, fontweight="bold", color="#ffd166", ha="right", va="top")
    years = list(d.year.values)
    seq = [k for k in range(len(years)) for _ in range(4)] + [len(years) - 1] * 6

    def step(i):
        im.set_data(rgb(seq[i]))
        yr.set_text(str(years[seq[i]]))
        return im, yr
    FuncAnimation(fig, step, frames=len(seq)).save(OUT / "kd_a3_wetlands_timelapse.gif", writer=PillowWriter(fps=3),
                                                    dpi=90, savefig_kwargs={"facecolor": BG})
    plt.close(fig)



def _panels(n, title, sub, source, w=16, h=7.6):
    fig = plt.figure(figsize=(w, h), facecolor="white")
    fig.text(0.01, 0.97, title, fontsize=17, fontweight="bold", va="top")
    fig.text(0.01, 0.925, sub, fontsize=10.5, color="#555", va="top")
    fig.text(0.01, 0.012, source, fontsize=8, color="#666")
    fig.text(0.99, 0.012, CREDIT, fontsize=10, fontweight="bold", ha="right", color="#333")
    return fig


def valley_still():
    """Still companion to kd_a1: valley floors in five epochs + share built over time."""
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc").sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    cell = (abs(float(np.diff(g.lon).mean())) * 111320 * np.cos(np.deg2rad(0.3))) * (abs(float(np.diff(g.lat).mean())) * 111320)
    frac = np.clip(g.values / cell, 0, 1)
    hand, _ = grid_hand(g.lat.values, g.lon.values)
    vf = hand < 3
    epochs = list(g.epoch.values)
    share = [float((frac[k] * vf).sum() / vf.sum()) * 100 for k in range(len(epochs))]
    show = [1975, 1990, 2005, 2020, 2030]
    fig = _panels(len(show), "Kampala is building over its valley floors, 1975-2030",
                  "Teal: valley floors (former wetlands and floodplains, < 3 m above the nearest drain). Red-yellow: "
                  "buildings on them. Grey: buildings elsewhere. 2030 is a projection.",
                  "Data: JRC GHSL built-up surface R2023A (100 m); Copernicus GLO-30 DEM.", h=5.4)
    ext = [float(g.lon.min()), float(g.lon.max()), float(g.lat.min()), float(g.lat.max())]
    cv = LinearSegmentedColormap.from_list("b", ["#cfe8e6", "#e8553a", "#7a1500"])
    cu = LinearSegmentedColormap.from_list("u", ["#ffffff", "#7d7d7d"])
    for j, e in enumerate(show):
        k = epochs.index(e)
        ax = fig.add_axes([0.005 + j * 0.152, 0.22, 0.148, 0.62])
        ax.imshow(np.where(~vf, frac[k], np.nan), cmap=cu, vmin=0, vmax=0.8, extent=ext, origin="lower")
        ax.imshow(np.where(vf, frac[k], np.nan), cmap=cv, vmin=0, vmax=0.8, extent=ext, origin="lower")
        ax.set_axis_off()
        ax.set_title(f"{e}{' (projected)' if e > 2020 else ''}: {share[k]:.0f}% built", fontsize=11, loc="left")
    bx = fig.add_axes([0.80, 0.24, 0.19, 0.58])
    bx.plot(epochs, share, color="#e8553a", lw=2.5, marker="o")
    bx.axvspan(2020, 2031, color="#eee")
    bx.text(2025.5, min(share) + 1, "projected", ha="center", fontsize=8, color="#777")
    bx.set_title("Valley floor built over (%)", fontsize=11, loc="left")
    bx.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.09, f"In 1975 buildings covered {share[0]:.0f}% of Greater Kampala's valley floors; by 2020, "
             f"{share[epochs.index(2020)]:.0f}%; by 2030 (projected) {share[-1]:.0f}%. Every hectare built on the valley "
             "floor is flood storage lost and a home placed in the water's path.", fontsize=11, wrap=True)
    fig.savefig(OUT.parent / "kd14_valley_floors_built.png", dpi=150)
    plt.close(fig)


def people_still():
    df = pd.read_csv(ROOT / "results" / "kd_population_low_ground.csv")
    pop = xr.open_dataarray(PROC / "kampala_ghs_pop.nc").sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    fig = _panels(4, "More people are living where the water goes",
                  "Residents on low ground (< 2 m above the nearest drain, within 150 m of a flowing channel), "
                  "Greater Kampala core. 2025 and 2030 are projections.",
                  "Data: JRC GHS-POP R2023A (100 m); Copernicus GLO-30 DEM; OpenStreetMap drains.")
    show = [1990, 2010, 2030]
    cm = LinearSegmentedColormap.from_list("h", ["#ffffff", "#fcbba1", "#ef3b2c", "#67000d"])
    ext = [float(pop.lon.min()), float(pop.lon.max()), float(pop.lat.min()), float(pop.lat.max())]
    for j, e in enumerate(show):
        ax = fig.add_axes([0.005 + j * 0.2, 0.12, 0.195, 0.76])
        ax.imshow(np.log10(1 + pop.sel(epoch=e).values), cmap=cm, vmin=0, vmax=2.6, extent=ext, origin="lower")
        ax.set_axis_off()
        v = float(df.set_index("epoch").pop_low_ground[e])
        ax.set_title(f"{e}{' (projected)' if e > 2020 else ''}: {v / 1000:,.0f}k on low ground", fontsize=11, loc="left")
    bx = fig.add_axes([0.64, 0.2, 0.34, 0.6])
    bx.bar(df.epoch, df.pop_low_ground / 1000, width=3.6, color=["#ef3b2c" if e <= 2020 else "#fcbba1" for e in df.epoch])
    for e, v in zip(df.epoch, df.pop_low_ground):
        bx.text(e, v / 1000, f"{v / 1000:,.0f}k", ha="center", va="bottom", fontsize=8)
    share = 100 * df.pop_low_ground / df.pop_box
    bx.set_title("People on low ground by channels (thousands); light = projected", fontsize=11, loc="left")
    bx.spines[["top", "right"]].set_visible(False)
    fig.text(0.64, 0.12, f"Share of the area's population on this low ground: {share.iloc[0]:.0f}% (1975) -> "
             f"{share[df.epoch == 2020].iloc[0]:.0f}% (2020) -> {share.iloc[-1]:.0f}% (2030)", fontsize=10)
    fig.savefig(OUT.parent / "kd15_people_on_low_ground.png", dpi=150)
    plt.close(fig)


def timelapse_still():
    d = xr.open_dataset(KD / "sat_landsat_timelapse.nc")
    years = list(d.year.values)
    show = [y for y in (1986, 1995, 2000, 2010, 2015, 2025) if y in years]
    fig = _panels(len(show), "Kampala's wetlands from space: Lubigi (west) to Kinawataka (east)",
                  "Landsat median, true colour, 30 m. Dark green valley floors are wetland; they shrink as buildings "
                  "(brown/grey) fill in. Blue: today's drainage channels (OpenStreetMap).", "Imagery: NASA/USGS Landsat Collection 2 (Microsoft Planetary Computer) · channels: © OpenStreetMap contributors.",
                  w=16, h=6.0)
    n = len(show)
    cols = 3
    for j, y in enumerate(show):
        k = years.index(y)
        r, c = divmod(j, cols)
        ax = fig.add_axes([0.005 + c * 0.333, 0.455 - r * 0.415, 0.325, 0.37])
        ax.imshow(np.clip(np.nan_to_num(np.dstack([d.red.isel(year=k), d.green.isel(year=k), d.blue.isel(year=k)])) * 3.4,
                          0, 1) ** 0.85)
        ax.set_axis_off()
        channels_px(ax, d, lw=0.8)
        ax.set_title(str(y), fontsize=12, loc="left", fontweight="bold")
    fig.savefig(OUT.parent / "kd16_wetlands_timelapse_panels.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    for st in sys.argv[1:] or ["valley", "timelapse", "people"]:
        globals()[st]()
        print("done", st, flush=True)
