"""Kampala drainage study, part 4: GIS maps, close-ups and satellite figures -> figures/kampala_drainage/.

kd04 overview: channel segments by current maintenance priority, reported hotspots, KCCA boundary
kd05 emerging risk: runoff growth and floodplain building since 1990
kd06 what sets reported hotspots apart (driver percentiles, hotspot vs other channels)
kd07 close-ups on satellite imagery at six hotspots (channels by priority, buildings in the 15 m reserve,
     waste points, culverts)
kd08 wetland loss: Landsat true colour 1986/1995 vs 2025 over Lubigi, Kinawataka and Nakivubo-Kansanga
kd09 valley-floor land cover 2017-2023 by channel system (Impact Observatory 10 m)
kd10 Sentinel-1 radar: newly wet ground on the latest pass vs the dry-season reference
kd11 channel-bed vegetation (Sentinel-2 NDVI) through time on the main channels
"""
import sys
import textwrap

import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

from common import CREDIT, FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
UTM = 32636
CM = LinearSegmentedColormap.from_list("risk", ["#4575b4", "#74add1", "#fee090", "#f46d43", "#a50026"])
IMG = ctx.providers.Esri.WorldImagery
SRC = ("Channels, waste points, places: © OpenStreetMap contributors · buildings: Microsoft Global ML Building Footprints · built-up: JRC GHSL R2023A · elevation: Copernicus GLO-30 DEM · wetland: ESA WorldCover 2021")
GRAY = " · basemap: Esri World Gray Canvas (Esri, HERE, Garmin, © OpenStreetMap contributors)"
LIGHT = ctx.providers.Esri.WorldGrayCanvas
CLOSE = [("Bwaise / Kalerwe (Lubigi, Nsooba)", 0.354, 32.570), ("Kyambogo-Banda (Kinawataka)", 0.335, 32.633),
         ("Downtown Nakivubo (Kisenyi, Clock Tower)", 0.311, 32.578), ("Nalukolongo-Ndeeba", 0.294, 32.552),
         ("Lubigi at Hoima Road", 0.341, 32.538), ("Kansanga-Soya (Gaba Road)", 0.277, 32.616)]


def load():
    s = gpd.read_file(KD / "segments.gpkg").to_crs(UTM)
    hs = pd.read_csv(KD / "flood_hotspots.csv")
    hp = gpd.GeoDataFrame(hs, geometry=gpd.points_from_xy(hs.lon, hs.lat), crs=4326).to_crs(UTM)
    d2 = gpd.read_file(PROC / "uganda_adm2.geojson")
    city = d2[d2.shapeName == "Kampala"].to_crs(UTM)
    return s, hp, city


def lw(s):
    return np.select([s.cls == "primary", s.cls == "secondary"], [2.2, 1.0], 0.35)


def place_labels(ax, kinds=("town", "suburb"), size=7.5, extra=None, halo="white", color="#222", frame=None,
                 pad=2.2, maxn=28, skip=()):
    """Neighbourhood names from OpenStreetMap, skipping any label that would overlap one already drawn."""
    import matplotlib.patheffects as pe
    pl = gpd.read_file(KD / "osm_places.geojson").to_crs(UTM)
    pl = pl[pl.place.isin(kinds)].dropna(subset=["name"]).drop_duplicates("name")
    order = {"town": 0, "suburb": 1, "neighbourhood": 2, "village": 3}
    pl = pl.assign(o=pl.place.map(order)).sort_values("o")
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    pl = pl.cx[x0:x1, y0:y1]
    rows = [(r.name, r.geometry.x, r.geometry.y, r.place == "town") for r in pl.itertuples()]
    if extra is not None:
        rows = [(n, x, y, True) for n, x, y in extra] + rows
    fig = ax.figure
    rend = fig.canvas.get_renderer()
    boxes = list(frame or [])
    for n, x, y, big in rows:
        if any(n.lower().startswith(k) for k in skip):
            continue
        t = ax.text(x, y, n, fontsize=size + (1.5 if big else 0), fontweight="bold" if big else "normal", color=color,
                    ha="center", va="center", zorder=12,
                    path_effects=[pe.withStroke(linewidth=2.5, foreground=halo)])
        bb = t.get_window_extent(rend).expanded(pad, pad * 1.6)
        if len(boxes) - len(frame or []) >= maxn or any(bb.overlaps(o) for o in boxes):
            t.remove()
        else:
            boxes.append(bb)
    return boxes


def overview(s, hp, city):
    f = s[s.risk_pct.notna()].sort_values("risk_pct")
    fig, ax = plt.subplots(figsize=(11, 10))
    s[s.risk_pct.isna()].plot(ax=ax, color="#9aa0a6", lw=0.25, alpha=0.6)
    f.plot(ax=ax, column="risk_pct", cmap=CM, vmin=0, vmax=100, lw=lw(f), legend=True,
           legend_kwds=dict(shrink=0.5, label="current maintenance priority (percentile)"))
    city.boundary.plot(ax=ax, color="#333", lw=1, ls="--")
    hp.plot(ax=ax, marker="o", facecolor="none", edgecolor="k", markersize=60, lw=1.2, zorder=5)
    ctx.add_basemap(ax, crs=f"EPSG:{UTM}", source=LIGHT, zoom=13, attribution_size=5)
    ax.set_axis_off()
    place_labels(ax)
    ax.legend(handles=[Line2D([], [], marker="o", ls="", mfc="none", mec="k", label="reported flood hotspot (approx.)"),
                       Line2D([], [], color="#333", ls="--", label="Kampala city boundary (approx., geoBoundaries)"),
                       Line2D([], [], color="#9aa0a6", lw=0.6, label="minor drains (< 0.25 km² upstream)")],
              loc="upper left", fontsize=8, framealpha=0.9)
    ax.set_title("Greater Kampala drainage channels: current maintenance priority\n"
                 "equal-weight index of runoff load, culverts/bridges, waste & markets, buildings in the reserve, "
                 "floodplain homes, wetland left", fontsize=10, loc="left")
    save(fig, "kd04_priority_overview.png", OUT, source=SRC + GRAY)


def emerging(s, hp, city):
    f = s[s.emerging_pct.notna()].sort_values("emerging_pct")
    fig, ax = plt.subplots(figsize=(11, 10))
    f.plot(ax=ax, column="emerging_pct", cmap="magma_r", vmin=0, vmax=100, lw=lw(f), legend=True,
           legend_kwds=dict(shrink=0.5, label="emerging risk (percentile): runoff growth + floodplain built since 1990"))
    city.boundary.plot(ax=ax, color="#333", lw=1, ls="--")
    ctx.add_basemap(ax, crs=f"EPSG:{UTM}", source=LIGHT, zoom=13, attribution_size=5)
    ax.set_axis_off()
    place_labels(ax)
    ax.set_title("Where tomorrow's flood hotspots are forming: the fast-growing fringe", fontsize=11, loc="left")
    save(fig, "kd05_emerging_risk.png", OUT, source=SRC + GRAY)


def drivers():
    d = pd.read_csv(RES / "kd_drivers.csv")
    d = d.sort_values("hotspot_median_pct")
    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(d))
    same = (d.other_median_pct - d.hotspot_median_pct).abs().values < 0.02  # coinciding dots: offset vertically
    off = np.where(same, 0.14, 0.0)
    ax.hlines(y, d.other_median_pct * 100, d.hotspot_median_pct * 100, color="#bbb", lw=2)
    ax.scatter(d.other_median_pct * 100, y + off, color="#2c7bb6", s=60, label="other channels", zorder=3)
    ax.scatter(d.hotspot_median_pct * 100, y - off, color="#d7191c", s=60, label="near reported hotspots", zorder=3)
    for yy in y[same]:
        ax.text(d.hotspot_median_pct.values[list(y).index(yy)] * 100 + 2.5, yy, "no difference", va="center",
                fontsize=8.5, color="#666")
    ax.set_yticks(y)
    ax.set_yticklabels(d.label)
    ax.set_xlim(0, 100)
    ax.set_xlabel("median percentile rank among Kampala channel segments")
    ax.legend(loc="lower right")
    ax.set_title("What sets reported flood hotspots apart", loc="left")
    save(fig, "kd06_hotspot_drivers.png", OUT, source=SRC + " · hotspots: KCCA/NEMA lists and Ugandan news reports (approx. locations)")


def closeups(s, hp):
    b = gpd.read_parquet(KD / "ms_buildings.parquet")
    waste = gpd.read_file(KD / "osm_waste.geojson").to_crs(UTM)
    waste["geometry"] = waste.geometry.representative_point()
    cul = gpd.read_file(KD / "osm_waterways.geojson")
    cul = cul[cul.tunnel.isin(["culvert", "yes"])].to_crs(UTM)
    cul["geometry"] = cul.geometry.interpolate(0.5, normalized=True)
    fig, axs = plt.subplots(2, 3, figsize=(16, 11))
    half = 650
    for ax, (title, la, lo) in zip(axs.flat, CLOSE):
        c = gpd.GeoSeries(gpd.points_from_xy([lo], [la]), crs=4326).to_crs(UTM).iloc[0]
        x0, x1, y0, y1 = c.x - half, c.x + half, c.y - half, c.y + half
        ss = s.cx[x0:x1, y0:y1]
        lon0, lat0, lon1, lat1 = gpd.GeoSeries(gpd.points_from_xy([x0, x1], [y0, y1]), crs=UTM).to_crs(4326).total_bounds
        bb = b.cx[lon0:lon1, lat0:lat1].to_crs(UTM)
        res = bb[bb.intersects(ss[ss.up_km2 >= 0.25].buffer(15).union_all())] if len(ss) else bb.iloc[:0]
        ss.plot(ax=ax, column="risk_pct", cmap=CM, vmin=0, vmax=100, lw=np.where(ss.up_km2 >= 2, 3.0, np.where(ss.up_km2 >= 0.25, 1.6, 0.6)),
                missing_kwds=dict(color="#bdbdbd"))
        res.plot(ax=ax, facecolor="none", edgecolor="#ff00ff", lw=0.8)
        waste.cx[x0:x1, y0:y1].plot(ax=ax, marker="^", color="#ffd400", edgecolor="k", markersize=40, lw=0.5, zorder=5)
        cul.cx[x0:x1, y0:y1].plot(ax=ax, marker="s", color="white", edgecolor="k", markersize=22, lw=0.6, zorder=4)
        hp.cx[x0:x1, y0:y1].plot(ax=ax, marker="o", facecolor="none", edgecolor="white", markersize=180, lw=1.5, zorder=6)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ctx.add_basemap(ax, crs=f"EPSG:{UTM}", source=IMG, zoom=17, attribution_size=4)
        ax.set_axis_off()
        ax.set_title(title, fontsize=10, loc="left")
        ax.plot([x0 + 60, x0 + 260], [y0 + 60, y0 + 60], color="white", lw=3)
        ax.text(x0 + 160, y0 + 85, "200 m", color="white", ha="center", fontsize=8, fontweight="bold")
        print(title, "buildings in 15 m reserve:", len(res), flush=True)
    handles = [Line2D([], [], color="#a50026", lw=3, label="channel, high priority"),
               Line2D([], [], color="#4575b4", lw=3, label="channel, low priority"),
               Line2D([], [], color="#bdbdbd", lw=1.5, label="minor drain"),
               Line2D([], [], marker="s", ls="", color="white", mec="k", label="culvert (OSM)"),
               Line2D([], [], color="#ff00ff", lw=1, label="building within 15 m of a channel"),
               Line2D([], [], marker="^", ls="", color="#ffd400", mec="k", label="mapped waste / dump point (OSM)"),
               Line2D([], [], marker="o", ls="", mfc="none", mec="k", label="reported flood hotspot")]
    fig.legend(handles=handles, loc="lower center", ncol=7, fontsize=9, frameon=False)
    fig.suptitle("Close-ups of Kampala's flood hotspots (imagery: Esri World Imagery; buildings: Microsoft 2023; "
                 "drains & waste: OpenStreetMap)", x=0.01, ha="left", fontweight="bold")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.06, wspace=0.03, hspace=0.1)
    save(fig, "kd07_hotspot_closeups.png", OUT)


def rgb(ds, gain=3.2):
    a = np.dstack([ds.red.values, ds.green.values, ds.blue.values]) if "red" in ds else \
        np.dstack([ds.B04.values, ds.B03.values, ds.B02.values])
    return np.clip(np.nan_to_num(a) * gain, 0, 1) ** 0.85


def wetland_loss():
    old = 1986 if (KD / "sat_landsat_1986.nc").exists() else 1995
    a = xr.open_dataset(KD / f"sat_landsat_{old}.nc")
    b = xr.open_dataset(KD / "sat_landsat_2025.nc")
    boxes = [("Lubigi wetland (north-west)", 0.335, 32.545), ("Kinawataka wetland (east)", 0.335, 32.640),
             ("Nakivubo-Kansanga wetlands (south-east)", 0.300, 32.615)]
    fig, axs = plt.subplots(3, 2, figsize=(11, 15))
    import pyproj
    tf = pyproj.Transformer.from_crs(4326, UTM, always_xy=True)
    for row, (t, la, lo) in zip(axs, boxes):
        x, y = tf.transform(lo, la)
        for ax, ds, yr in ((row[0], a, old), (row[1], b, 2025)):
            sub = ds.sel(x=slice(x - 2500, x + 2500), y=slice(y + 2500, y - 2500))
            ax.imshow(rgb(sub), extent=[float(sub.x.min()), float(sub.x.max()), float(sub.y.min()), float(sub.y.max())])
            ax.set_axis_off()
            ax.set_title(f"{t}: {yr}", fontsize=10, loc="left")
    fig.suptitle(f"Kampala's wetlands, {old} vs 2025 (Landsat dry-season median, true colour, 30 m)", x=0.01,
                 ha="left", fontweight="bold")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.01, wspace=0.03, hspace=0.08)
    save(fig, "kd08_wetland_loss_landsat.png", OUT, source="Imagery: NASA/USGS Landsat Collection 2 Level-2, via Microsoft Planetary Computer")


def lulc_trends():
    d = pd.read_csv(RES / "kd_lulc_valley.csv")
    d = d[d.system != "All Greater Kampala core"]
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8), sharex=True)
    for nm, g in d.groupby("system"):
        axs[0].plot(g.year, g.built * 100, marker="o", label=nm)
        axs[1].plot(g.year, g.wetland * 100, marker="o", label=nm)
    axs[0].set_title("Built-up share of the valley floor (%)", loc="left")
    axs[1].set_title("Wetland ('flooded vegetation') share of the valley floor (%)", loc="left")
    axs[0].legend(fontsize=8)
    fig.suptitle("Former wetlands and floodplains (HAND < 3 m), 2017-2023, Impact Observatory 10 m land cover",
                 x=0.01, ha="left", fontweight="bold")
    save(fig, "kd09_valley_landcover.png", OUT, source="Data: Impact Observatory/Esri 10 m annual land cover (io-lulc v02); Copernicus GLO-30 DEM")


def radar(src="sat_s1.nc", out="kd10_sentinel1_after_storm.png", title=None, finding=None):
    """Sentinel-1 after a storm (default: 11 Oct 2026 afternoon pass), with zooms on two hotspot valleys."""
    from scipy import ndimage
    d = xr.open_dataset(KD / src)
    s, hp, city = load()
    diff = (d.vv_now - d.vv_ref)
    wet = ((diff < -3) & (d.vv_now < -15) & (d.vv_ref > -16)).values  # exclude water already open in the dry season
    share = float(wet.mean()) * 100
    big = ndimage.binary_dilation(wet, iterations=2)
    ring = ndimage.binary_dilation(wet, iterations=4) & ~big
    ext = [float(d.x.min()), float(d.x.max()), float(d.y.min()), float(d.y.max())]
    org = "upper" if float(d.y[0]) > float(d.y[-1]) else "lower"
    base = LinearSegmentedColormap.from_list("rb", ["#000000", "#2b3440", "#9fb0bf", "#ffffff"])
    cyan = LinearSegmentedColormap.from_list("c", ["#00e5ff", "#00e5ff"])
    blk = LinearSegmentedColormap.from_list("k", ["#000000", "#000000"])
    fl = s[s.up_km2 >= 2]

    def panel(ax, x0, x1, y0, y1, lw=0.7, ms=60):
        ax.imshow(d.vv_now, cmap=base, vmin=-24, vmax=0, extent=ext, origin=org)
        ax.imshow(np.where(ring, 1.0, np.nan), cmap=blk, extent=ext, origin=org, interpolation="nearest", alpha=0.9)
        ax.imshow(np.where(big, 1.0, np.nan), cmap=cyan, extent=ext, origin=org, interpolation="nearest")
        fl.plot(ax=ax, color="#ff9f1c", lw=lw, zorder=4)
        hp.plot(ax=ax, marker="o", facecolor="none", edgecolor="#ffe600", markersize=ms, lw=1.6, zorder=5)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_xticks([])
        ax.set_yticks([])
    fig = plt.figure(figsize=(16, 10.5), facecolor="#0f1419")
    ax = fig.add_axes([0.005, 0.05, 0.6, 0.86])
    panel(ax, *ext)
    zooms = [("Lubigi - Bwaise - Kalerwe", 0.352, 32.565), ("Kinawataka - Banda - Kyambogo", 0.336, 32.632)]
    import pyproj
    tf = pyproj.Transformer.from_crs(4326, 32636, always_xy=True)
    for k, (nm, la, lo) in enumerate(zooms):
        x, y = tf.transform(lo, la)
        h = 1300
        zx = fig.add_axes([0.615, 0.49 - k * 0.43, 0.2, 0.40])
        panel(zx, x - h, x + h, y - h, y + h, lw=1.4, ms=200)
        for sp in zx.spines.values():
            sp.set_edgecolor("#00e5ff")
            sp.set_linewidth(1.5)
        zx.set_title(nm, color="white", fontsize=11, loc="left")
        ax.add_patch(plt.Rectangle((x - h, y - h), 2 * h, 2 * h, fill=False, ec="#00e5ff", lw=1.6, zorder=6))
        ax.text(x - h, y + h + 150, str(k + 1), color="#00e5ff", fontsize=12, fontweight="bold", zorder=6)
        zx.text(0.02, 0.97, str(k + 1), color="#00e5ff", fontsize=12, fontweight="bold", transform=zx.transAxes, va="top")
    fig.text(0.005, 0.965, title or f"Kampala by radar, {d.attrs['date_now'][:10]}, about 13 hours after the early-morning storm",
             fontsize=17, fontweight="bold", color="white", va="top")
    fig.text(0.005, 0.93, "Sentinel-1 radar sees through cloud: dark = smooth (water, tarmac, open ground), bright = buildings. "
             "Cyan: ground that turned water-dark since the dry season.", fontsize=11, color="#b9c2c9", va="top")
    txt = (f"What the radar shows\n\nCyan patches (enlarged for visibility): {share:.2f}% of the area looks newly wet "
           f"compared with {d.attrs['n_ref']} dry-season passes - mostly small ponds and waterlogged plots, not "
           "flooded channels.\n\n" + (finding or "No extensive standing water remained along the channels (orange) or at the "
           "reported hotspots (yellow circles). Kampala's floods are flash floods: they rise and drain within hours, and the "
           "satellite passes only every 6-12 days.") + "\n\nSo radar maps where water CAN go and tracks slow change, but the "
           "city's flood detector has to be rain gauges, water-level sensors at key culverts and reports from residents "
           "and KCCA crews.")
    fig.text(0.825, 0.88, "\n".join(textwrap.fill(p_, 30) if p_ else "" for p_ in txt.split("\n")), fontsize=10,
             color="white", va="top")
    fig.text(0.005, 0.015, "Radar: ESA Copernicus Sentinel-1 RTC (Microsoft Planetary Computer) · channels: © OpenStreetMap "
             "contributors · hotspots: KCCA/NEMA lists, news and local reports (approx.)", fontsize=8, color="#9aa4ab")
    fig.text(0.995, 0.015, CREDIT, fontsize=11, fontweight="bold", color="white", ha="right")
    fig.savefig(OUT / out, dpi=170, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("s1 wet-looking share %", round(share, 3))
    return share


def radar_pair():
    """11 Oct afternoon vs 12 Oct morning, plus a stand-alone 12 Oct map."""
    a = radar()
    b = radar("sat_s1_20261012.nc", "kd10b_sentinel1_12oct_morning.png",
              "Kampala by radar, 12 October 2026, 06:35, the morning after the storm weekend",
              "This descending pass compares the morning of 12 October with dry-season passes from the same orbit. "
              "As on Sunday afternoon, the channels (orange) and reported hotspots (yellow circles) show no extensive "
              "standing water: the floodwater had drained away.")
    print("newly wet share: 11 Oct", round(a, 3), "| 12 Oct", round(b, 3))

def channel_ndvi():
    d = pd.read_csv(RES / "kd_channel_ndvi.csv", parse_dates=["month"])
    fig, ax = plt.subplots(figsize=(12, 5))
    for nm, g in d.groupby("system"):
        m = g.groupby("month").ndvi.median()
        ax.plot(m.index, m.rolling(3, min_periods=1).mean(), label=nm, lw=1.6)
    ax.set_ylabel("NDVI in the channel bed (median of 20 m samples)")
    ax.set_title("Vegetation choking Kampala's main channels: Sentinel-2, 2017-2026 (higher = greener/more blocked)",
                 loc="left")
    ax.legend(fontsize=8)
    save(fig, "kd11_channel_vegetation.png", OUT, source="Data: ESA Copernicus Sentinel-2 L2A via Microsoft Planetary Computer; channels © OpenStreetMap contributors")


def overlay():
    """Current priority x emerging risk (terciles each): where the work is now, and where it is coming."""
    s, hp, city = load()
    f = s[s.risk_pct.notna()].copy()
    f["now"] = pd.cut(f.risk_pct, [-1, 100 / 3, 200 / 3, 101], labels=[0, 1, 2]).astype(int)
    f["fut"] = pd.cut(f.emerging_pct, [-1, 100 / 3, 200 / 3, 101], labels=[0, 1, 2]).astype(int)
    grid = [["#e8e8e8", "#e4acac", "#c85a5a"],   # rows: emerging low->high; cols: current low->high
            ["#b0d5df", "#ad9ea5", "#985356"],
            ["#64acbe", "#627f8c", "#574249"]]
    f["col"] = [grid[b][a] for a, b in zip(f.now, f.fut)]
    fig = plt.figure(figsize=(15, 10.5))
    ax = fig.add_axes([0.0, 0.0, 0.68, 0.94])
    s[s.risk_pct.isna()].plot(ax=ax, color="#c8c8c8", lw=0.2)
    f = f.sort_values(["now", "fut"])
    f.plot(ax=ax, color=f.col, lw=lw(f) * 1.2)
    city.boundary.plot(ax=ax, color="#333", lw=0.9, ls="--")
    ctx.add_basemap(ax, crs=f"EPSG:{UTM}", source=LIGHT, zoom=13, attribution_size=5)
    ax.set_axis_off()
    place_labels(ax)
    fig.text(0.01, 0.965, "How much work is waiting: channels that need attention now, and those heading there",
             fontsize=15, fontweight="bold")
    lg = fig.add_axes([0.72, 0.62, 0.17, 0.24])
    for a in range(3):
        for b in range(3):
            lg.add_patch(plt.Rectangle((a, b), 1, 1, color=grid[b][a]))
    lg.set_xlim(0, 3)
    lg.set_ylim(0, 3)
    lg.set_xticks([0.5, 1.5, 2.5])
    lg.set_xticklabels(["low", "mid", "high"])
    lg.set_yticks([0.5, 1.5, 2.5])
    lg.set_yticklabels(["low", "mid", "high"])
    lg.set_xlabel("current maintenance priority →")
    lg.set_ylabel("emerging risk →")
    lg.set_aspect("equal")
    lg.grid(False)
    km = f.assign(km=f.length_m / 1000)
    cls = {"Urgent: high now AND still worsening": (km.now == 2) & (km.fut >= 1),
           "Fix now: high priority, stable": (km.now == 2) & (km.fut == 0),
           "Coming: rising risk, not yet high": (km.now <= 1) & (km.fut == 2),
           "Watch: moderate on both": (km.now == 1) & (km.fut == 1),
           "Low on both": (km.now == 0) & (km.fut <= 1)}
    tot = km.km.sum()
    rows = [(k, km.km[m].sum()) for k, m in cls.items()]
    other = tot - sum(v for _, v in rows)
    bx = fig.add_axes([0.72, 0.16, 0.26, 0.36])
    cols = ["#574249", "#c85a5a", "#64acbe", "#ad9ea5", "#e8e8e8"]
    y = np.arange(len(rows))[::-1]
    bx.barh(y, [v for _, v in rows], color=cols, edgecolor="#555", lw=0.5, height=0.45)
    for yy, (k, v) in zip(y, rows):
        bx.text(0, yy + 0.33, k, va="bottom", fontsize=9.5, fontweight="bold", color="#333")
        bx.text(v + tot * 0.01, yy, f"{v:.0f} km ({100 * v / tot:.0f}%)", va="center", fontsize=9)
    bx.set_yticks([])
    bx.set_ylim(-0.5, len(rows) - 0.1)
    bx.set_xlim(0, max(v for _, v in rows) * 1.45)
    bx.set_xlabel("km of channel (segments with >= 0.25 km² upstream)")
    bx.set_title(f"{tot:.0f} km of flowing channel assessed", fontsize=10, loc="left")
    fig.text(0.72, 0.09, "Current priority: runoff load, culverts/bridges, waste & markets, buildings in the reserve,\n"
             "floodplain homes, wetland left. Emerging risk: growth since 1990 in upstream paving and in\n"
             "building on the valley floor. Terciles among Greater Kampala channel segments.", fontsize=8, color="#555")
    save(fig, "kd12_priority_vs_emerging.png", OUT, source=SRC + GRAY)
    pd.DataFrame(rows + [("Other combinations", other)], columns=["class", "km"]).round(1).to_csv(RES / "kd_work_classes.csv", index=False)
    print(rows, round(tot))


PAGES = [  # (title, lat, lon) of the flooding point; the channel feeding it is traced from here
    ("Bwaise (Lubigi channel)", 0.352, 32.562), ("Kalerwe (Nsooba channel)", 0.3545, 32.5785),
    ("Kyambogo-Banda, Jinja Road (Kinawataka)", 0.3335, 32.627), ("Kinawataka / Katogo-Mbuya", 0.331, 32.636),
    ("Downtown Nakivubo: Kisenyi, Clock Tower", 0.3105, 32.5785), ("Centenary Park / Lugogo (Kitante channel)", 0.3181, 32.5939),
    ("Nalukolongo-Ndeeba", 0.2946, 32.5413), ("Najjanankumbi", 0.2798, 32.5666),
    ("Lubigi at Hoima Road", 0.341, 32.536), ("Kansanga-Soya, Gaba Road", 0.2773, 32.6193),
    ("Lufuka-Kikajjo (2019 deaths)", 0.2792, 32.5537),
]


def trace(s, start, up_km=4000, down_km=800):
    """Upstream/downstream walk over touching segments, using upstream area to tell direction."""
    import shapely
    geoms = s.geometry.values
    ends = np.array([[g.coords[0], g.coords[-1]] for g in geoms]).reshape(len(s), 4)
    pts = shapely.points(np.vstack([ends[:, :2], ends[:, 2:]]))
    owner = np.r_[np.arange(len(s)), np.arange(len(s))]
    gtree = shapely.STRtree(geoms)
    ptree = shapely.STRtree(pts)
    up = s.up_km2.values
    L = s.length_m.values

    def nbrs(i):
        """segments touching i: their line within 15 m of i's ends, or their ends within 15 m of i's line
        (catches tributaries that join mid-segment and small gaps in the mapping)"""
        a = gtree.query(pts[[i, i + len(s)]], predicate="dwithin", distance=15)[1]
        b = owner[ptree.query(geoms[i], predicate="dwithin", distance=15)]
        return set(a) | set(b) - {i}
    a0 = up[start]
    keep, dist = {start: 0.0}, {start: 0.0}
    frontier = [start]
    while frontier:  # upstream: smaller area, still a sizeable tributary
        i = frontier.pop()
        for j in nbrs(i):
            if j in keep or up[j] > up[i] * 1.05 or up[j] < max(0.15 * a0, 0.1):
                continue
            d = dist[i] + L[j]
            if d <= up_km:
                keep[j], dist[j] = d, d
                frontier.append(j)
    i, d = start, 0.0
    while d < down_km:  # downstream: follow the largest-area neighbour
        cand = [j for j in nbrs(i) if up[j] >= up[i] * 0.98 and j not in keep]
        if not cand:
            break
        i = max(cand, key=lambda j: up[j])
        d += L[i]
        keep[i] = -d
    return s.iloc[list(keep)].assign(along=list(keep.values()))


def closeup_pages():
    import shapely
    from matplotlib.backends.backend_pdf import PdfPages
    s, hp, city = load()
    s = s.reset_index(drop=True)
    b = gpd.read_parquet(KD / "ms_buildings.parquet")
    waste = gpd.read_file(KD / "osm_waste.geojson").to_crs(UTM)
    waste["geometry"] = waste.geometry.representative_point()
    cul = gpd.read_file(KD / "osm_waterways.geojson")
    cul = cul[cul.tunnel.isin(["culvert", "yes"])].to_crs(UTM)
    cul["geometry"] = cul.geometry.interpolate(0.5, normalized=True)
    pages = OUT / "closeups"
    pages.mkdir(parents=True, exist_ok=True)
    flowing = s[s.up_km2 >= 0.25]
    tree = shapely.STRtree(flowing.geometry.values)
    rows = []
    with PdfPages(OUT / "kd07_hotspot_closeups.pdf") as pdf:
        for k, (title, la, lo) in enumerate(PAGES, start=1):
            p = gpd.GeoSeries(gpd.points_from_xy([lo], [la]), crs=4326).to_crs(UTM).iloc[0]
            near = flowing.iloc[tree.query(p, predicate="dwithin", distance=700)]
            if near.empty:
                print("no channel near", title)
                continue
            start = int((near.up_km2 / (1 + near.distance(p) / 250)).idxmax())
            reach = trace(s, start)
            x0, y0, x1, y1 = reach.total_bounds
            pad = 250
            x0, y0, x1, y1 = min(x0, p.x) - pad, min(y0, p.y) - pad, max(x1, p.x) + pad, max(y1, p.y) + pad
            w, h = x1 - x0, y1 - y0
            side = max(w, h, 1500)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            x0, x1, y0, y1 = cx - side / 2, cx + side / 2, cy - side / 2, cy + side / 2
            ctxs = s.cx[x0:x1, y0:y1]
            lon0, lat0, lon1, lat1 = gpd.GeoSeries(gpd.points_from_xy([x0, x1], [y0, y1]), crs=UTM).to_crs(4326).total_bounds
            bb = b.cx[lon0:lon1, lat0:lat1].to_crs(UTM)
            rb = reach.buffer(15).union_all()
            res = bb[bb.intersects(rb)]
            ws = waste.cx[x0:x1, y0:y1]
            cu = cul.cx[x0:x1, y0:y1]
            n_waste = int(ws.intersects(reach.buffer(100).union_all()).sum())
            n_cul = int(cu.intersects(reach.buffer(25).union_all()).sum())
            fig = plt.figure(figsize=(16, 11.3))
            ax = fig.add_axes([0.01, 0.06, 0.66, 0.86])
            ctxs[ctxs.up_km2 < 0.25].plot(ax=ax, color="#bdbdbd", lw=0.6)
            fl = ctxs[ctxs.up_km2 >= 0.25]
            fl.plot(ax=ax, color="#9e9e9e", lw=1.2)
            reach.buffer(18).plot(ax=ax, color="#00e5ff", alpha=0.35, zorder=3)
            reach.plot(ax=ax, column="risk_pct", cmap=CM, vmin=0, vmax=100, lw=np.clip(1.5 + reach.up_km2 ** 0.5, 2, 6), zorder=4,
                       missing_kwds=dict(color="#bdbdbd"))
            res.plot(ax=ax, facecolor="none", edgecolor="#ff00ff", lw=0.7, zorder=5)
            ws.plot(ax=ax, marker="^", color="#ffd400", edgecolor="k", markersize=45, lw=0.5, zorder=6)
            cu.plot(ax=ax, marker="s", color="white", edgecolor="k", markersize=24, lw=0.6, zorder=6)
            ax.scatter([p.x], [p.y], s=420, facecolor="none", edgecolor="white", lw=2.5, zorder=7)
            ax.scatter([p.x], [p.y], s=420, facecolor="none", edgecolor="#d7191c", lw=1.2, zorder=8)
            ax.annotate("reported flooding", (p.x, p.y), xytext=(14, 14), textcoords="offset points", color="white",
                        fontsize=10, fontweight="bold", zorder=9,
                        bbox=dict(facecolor="#00000099", edgecolor="none", pad=2))
            # flow direction arrows at the reach's upstream ends
            ax.set_xlim(x0, x1)
            ax.set_ylim(y0, y1)
            zoom = 17 if side < 2500 else 16
            ctx.add_basemap(ax, crs=f"EPSG:{UTM}", source=IMG, zoom=zoom, attribution_size=5)
            ax.set_axis_off()
            sb = 500 if side > 2500 else 200
            ax.plot([x0 + 0.04 * side, x0 + 0.04 * side + sb], [y0 + 0.04 * side] * 2, color="white", lw=4)
            ax.text(x0 + 0.04 * side + sb / 2, y0 + 0.055 * side, f"{sb} m", color="white", ha="center",
                    fontsize=10, fontweight="bold")
            fig.text(0.01, 0.955, f"{k}. {title}", fontsize=18, fontweight="bold")
            fig.text(0.01, 0.93, "Highlighted (cyan): the channel reach draining to the flooding point, traced upstream "
                     "over the drain network", fontsize=10.5, color="#555")
            # side panel
            loc = fig.add_axes([0.69, 0.60, 0.29, 0.32])
            s[s.up_km2 >= 2].plot(ax=loc, color="#4575b4", lw=0.6)
            city.boundary.plot(ax=loc, color="#555", lw=0.6, ls="--")
            loc.add_patch(plt.Rectangle((x0, y0), side, side, fill=False, ec="#d7191c", lw=1.5))
            loc.set_xlim(*city.total_bounds[[0, 2]] + np.array([-3000, 3000]))
            loc.set_ylim(*city.total_bounds[[1, 3]] + np.array([-3000, 3000]))
            loc.set_aspect("equal")
            loc.set_xticks([])
            loc.set_yticks([])
            loc.set_title("location in Greater Kampala", fontsize=9)
            up_area = float(reach.up_km2.max())
            hd = pd.read_csv(KD / "flood_hotspots.csv")
            ev = hd.iloc[((hd.lat - la) ** 2 + (hd.lon - lo) ** 2).idxmin()].evidence
            top = reach.loc[reach.risk_pct.idxmax()] if reach.risk_pct.notna().any() else None
            txt = [("Reach traced", f"{reach.length_m.sum() / 1000:.1f} km of channel"),
                   ("Upstream area at the bottom", f"{up_area:.1f} km²"),
                   ("Upstream built-up, 1990 → 2020", f"{100 * reach.loc[reach.up_km2.idxmax()].up_built_1990:.0f}% → "
                                                     f"{100 * reach.loc[reach.up_km2.idxmax()].up_built_2020:.0f}%"),
                   ("Buildings within 15 m of channel", f"{len(res):,}"),
                   ("Mapped waste/dump points ≤100 m", f"{n_waste}"),
                   ("Culverts on the reach", f"{n_cul}"),
                   ("Median maintenance priority", f"{reach.risk_pct.median():.0f}th percentile"),
                   ("Highest-priority segment's drivers", top.top_drivers if top is not None else "-"),
                   ("Flood evidence", ev)]
            yy = 0.55
            for a_, b_ in txt:
                fig.text(0.69, yy, a_, fontsize=9, color="#666")
                fig.text(0.69, yy - 0.022, b_, fontsize=11, fontweight="bold", wrap=True)
                yy -= 0.052 if len(b_) < 45 else 0.075
            handles = [Line2D([], [], color="#a50026", lw=3, label="channel, high priority"),
                       Line2D([], [], color="#4575b4", lw=3, label="channel, low priority"),
                       Line2D([], [], color="#9e9e9e", lw=1.5, label="other drains"),
                       Line2D([], [], marker="s", ls="", color="white", mec="k", label="culvert"),
                       Line2D([], [], color="#ff00ff", lw=1, label="building ≤15 m from reach"),
                       Line2D([], [], marker="^", ls="", color="#ffd400", mec="k", label="waste / dump point")]
            fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.01, 0.005), ncol=6, fontsize=9, frameon=False)
            fig.text(0.99, 0.012, "Imagery: Esri World Imagery · drains & waste: OpenStreetMap · buildings: Microsoft (2023) · "
                     "DEM: Copernicus GLO-30", ha="right", fontsize=7.5, color="#666")
            slug = "".join(c if c.isalnum() else "_" for c in title.split(":")[0].split("(")[0].strip().lower()).strip("_")
            fig.savefig(pages / f"kd07_{k:02d}_{slug}.png", dpi=150)
            pdf.savefig(fig, dpi=150)
            plt.close(fig)
            rows.append(dict(page=k, place=title, reach_km=reach.length_m.sum() / 1000, upstream_km2=up_area,
                             bldg_15m=len(res), waste_100m=n_waste, culverts=n_cul,
                             priority_median=reach.risk_pct.median()))
            print(k, title, f"reach {reach.length_m.sum() / 1000:.1f} km, bldg {len(res)}, waste {n_waste}, culv {n_cul}", flush=True)
    pd.DataFrame(rows).round(2).to_csv(RES / "kd_closeup_reaches.csv", index=False)


if __name__ == "__main__":
    s, hp, city = load()
    steps = sys.argv[1:] or ["overview", "emerging", "drivers", "closeups"]
    for st in steps:
        f = globals()[st]
        f(*{"overview": (s, hp, city), "emerging": (s, hp, city), "closeups": (s, hp)}.get(st, ()))
