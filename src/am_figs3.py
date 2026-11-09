"""Flood x AMR paper 1, step 7: six further figures.

am12  real floods mapped: modelled hours in water of 10 cm or more for six catalogued floods, with the places named in
      reports marked as reproduced (water within 500 m) or missed
am13  routed load against exposure for every stretch: the four sampling strata and the top 10%, and the same as a
      bivariate map
am14  rank stability mapped: share of 1,000 weight draws in which each exposed stretch is in the top 10%
am15  the Ggaba intake through time: intake and outlet-plume turbidity over the open lake, scene by scene, with rain
am16  where the wetland filter was lost: vegetated valley floor on the channel paths in 1986 and 2025, and the
      wetland each stretch's load no longer passes
am17  the flood of 18 March 2026 hour by hour: animation (GIF, MP4) and still small multiples
The event runs repeat am_events (same rain, model and thresholds) but keep the hours per 30 m square;
they are cached in data/processed/am_event_cells.npz.
"""
import subprocess

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from PIL import Image

from am_figs import BOX, base
from common import CREDIT, FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_amr"
ANI = OUT / "animations"
CACHE = PROC / "am_event_cells.npz"
EVENTS = ["KLA-20160413", "KLA-20190526", "KLA-20250326", "KLA-20251031", "KLA-20260318", "KLA-20261010"]
HOURLY = "KLA-20260318"
MODEL = "Exposure: Kampala drainage screening model (indicative) · population: JRC GHS-POP 2020"
TERRAIN = "Terrain and channels: Copernicus GLO-30 · hillshade from GLO-30"
PLACES = [("Bwaise", 0.352, 32.562), ("Kalerwe", 0.3545, 32.5785), ("Kololo", 0.333, 32.595), ("Makerere", 0.335, 32.567),
          ("Kisenyi", 0.311, 32.570), ("Nakawa", 0.329, 32.615), ("Ntinda", 0.354, 32.614), ("Rubaga", 0.303, 32.553),
          ("Katwe", 0.297, 32.576), ("Kireka", 0.347, 32.648), ("Nateete", 0.298, 32.532), ("Kawempe", 0.378, 32.560),
          ("Namasuba", 0.272, 32.563), ("Ggaba", 0.255, 32.627), ("Bweyogerere", 0.358, 32.665), ("Nansana", 0.365, 32.525)]


def names(ax, size=8.5, keep=None):
    """Sparse neighbourhood names, skipping any that would overlap a name already drawn."""
    rend = ax.figure.canvas.get_renderer(); boxes = []
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    for n, la, lo in PLACES:
        if keep is not None and n not in keep or not (x0 < lo < x1 and y0 < la < y1):
            continue
        t = ax.text(lo, la, n, fontsize=size, color="#222", ha="center", va="center", zorder=12, style="italic",
                    path_effects=[pe.withStroke(linewidth=2.4, foreground="white")])
        bb = t.get_window_extent(rend).expanded(1.15, 1.4)
        if any(bb.overlaps(o) for o in boxes):
            t.remove()
        else:
            boxes.append(bb)


def solid(leg):
    """Legends on maps: opaque white frame above every map layer."""
    leg.set_frame_on(True); leg.get_frame().set_facecolor("white"); leg.get_frame().set_alpha(0.95)
    leg.get_frame().set_edgecolor("#cccccc"); leg.set_zorder(30)
    return leg


def cells():
    """Hours in water >= 10 cm per 30 m square for each event in EVENTS, and the hour-by-hour wet mask for HOURLY."""
    if CACHE.exists():
        z = np.load(CACHE)
        return {k: z[k] for k in z.files}
    from am_events import fetch, intensity
    from kf_export import rating, run, segments
    s, h = segments()
    C1990 = 0.25 + 0.65 * np.clip(2.27 * s.up_built_1990.values, 0, 0.95)
    FP = rating(s, h)
    cl = np.load(KD / "depth_cells.npz")
    out = {}
    for ev in EVENTS:
        r = fetch(ev, None, can_fetch=False)
        I = intensity(s, h, r)
        H = run(h, FP, I, mult=1.5, silt=0.3, paving="2020", C1990=C1990)
        wet = (H[cl["seg"]] - (np.round(cl["hand"] * 20) / 20)[:, None]) >= 0.0999
        out[ev.replace("-", "_")] = wet.sum(1).astype("int16")
        if ev == HOURLY:
            out["hourly"] = wet
            out["hourly_rain"] = r.sel(lat=slice(0.42, 0.20), lon=slice(32.45, 32.72)).mean(("lat", "lon")).fillna(0).values
            out["hourly_time"] = r.time.values.astype("datetime64[m]").astype("int64")
        print("cells", ev, int((out[ev.replace("-", "_")] > 0).sum()), flush=True)
    np.savez_compressed(CACHE, **out)
    return out


def cell_lonlat():
    cl = np.load(KD / "depth_cells.npz")
    a, _, c0, _, e, f0 = cl["transform"]
    return c0 + a * (cl["cols"] + 0.5), f0 + e * (cl["rows"] + 0.5), cl["seg"]


def channels():
    from kf_export import segments
    return segments()[0].to_crs(4326)


HOURS_CMAP = ListedColormap(["#c6dbef", "#6baed6", "#2171b5", "#08306b"])
HOURS_NORM = BoundaryNorm([1, 2, 4, 7, 50], 4)


def am12(C, s):
    lon, lat, _ = cell_lonlat()
    e = pd.read_csv(RES / "am_events.csv").set_index("event")
    pl = pd.read_csv(RES / "kampala_flood_catalogue_places.csv")
    hit = pd.read_csv(RES / "am_event_places.csv")
    pl = pl.merge(hit, left_on=["event_id", "place"], right_on=["event", "place"])
    fig, axs = plt.subplots(2, 3, figsize=(15, 11.2))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.1, wspace=0.03, hspace=0.18)
    for ax, ev in zip(axs.flat, EVENTS):
        base(ax)
        s.plot(ax=ax, color="#9fb3c8", lw=0.35, zorder=2)
        hrs = C[ev.replace("-", "_")]; m = hrs > 0
        ax.scatter(lon[m], lat[m], s=1.6, c=hrs[m], cmap=HOURS_CMAP, norm=HOURS_NORM, marker="s", lw=0, zorder=3)
        g = pl[pl.event_id == ev]
        for ok, mk, col in ((True, "o", "#1a9850"), (False, "X", "#d73027")):
            gg = g[g.modelled_water_within_500m == ok]
            ax.scatter(gg.lon, gg.lat, s=90, marker=mk, c=col, edgecolor="white", lw=1.2, zorder=6)
        names(ax, size=8, keep={"Bwaise", "Kisenyi", "Ntinda", "Rubaga", "Katwe", "Kireka", "Namasuba", "Ggaba", "Nansana"})
        r = e.loc[ev]
        ax.set_title(f"{pd.Timestamp(r.date):%d %B %Y}", loc="left", fontsize=12, fontweight="bold", pad=20)
        ax.text(0, 1.012, f"{r.rain_42h_mm:.0f} mm  ·  {r.person_hours / 1000:,.0f}k person-hours  ·  "
                f"{int(g.modelled_water_within_500m.sum())} of {len(g)} named places reproduced", transform=ax.transAxes, fontsize=9.8, color="#444")
    hl = [Line2D([], [], ls="", marker="s", ms=8, color=c) for c in HOURS_CMAP.colors]
    hl += [Line2D([], [], ls="", marker="o", ms=9, color="#1a9850", mec="white"), Line2D([], [], ls="", marker="X", ms=9, color="#d73027", mec="white")]
    fig.legend(hl, ["1 hour in water ≥10 cm", "2–3 hours", "4–6 hours", "7 hours or more", "reported place, modelled water within 500 m",
                    "reported place, no modelled water"], loc="lower center", ncol=6, fontsize=9.5, frameon=False, bbox_to_anchor=(0.5, 0.045))
    fig.suptitle("Six real floods replayed: where the model puts water, and the places reporters named", x=0.01, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.01, 0.905, "Hourly PERSIANN-CCS rain (x1.5) over 42 hours, channels 30% silted. Under each date: city-average rain, person-hours "
             "in water of 10 cm or more, and named places with modelled water within 500 m.", fontsize=10.5, color="#555")
    save(fig, "am12_real_flood_maps.png", OUT, "Rain: PERSIANN-CCS hourly (CHRS, UC Irvine) · reports: Kampala flood catalogue (paper 0) · "
         + MODEL + " · " + TERRAIN)


STRATA = {"high load, high exposure": "#b10026", "high load, low exposure": "#fd8d3c", "low load, high exposure": "#2c7fb8",
          "low load, low exposure": "#7fcdbb"}


def am13(s):
    d = pd.read_csv(RES / "am_stretches.csv")
    f = pd.read_csv(RES / "am_sampling_frame.csv")
    ex = d[(d.eae_people > 0) & (d.load > 0)].copy()
    ml, me = ex.load.median(), ex.eae_people.median()
    ex["stratum"] = np.where(ex.load >= ml, "high load, ", "low load, ") + np.where(ex.eae_people >= me, "high exposure", "low exposure")
    n_top = int(np.ceil(0.1 * (d.eae_people > 0).sum()))
    top = ex["rank"] <= n_top
    fig = plt.figure(figsize=(15.5, 7.6))
    a = fig.add_axes([0.06, 0.13, 0.36, 0.74]); b = fig.add_axes([0.45, 0.08, 0.42, 0.82]); k = fig.add_axes([0.885, 0.55, 0.1, 0.19])
    for st, c in STRATA.items():
        g = ex[(ex.stratum == st) & ~top]
        a.scatter(g.load, g.eae_people, s=5, c=c, alpha=0.45, lw=0, label=st)
    a.scatter(ex.load[top], ex.eae_people[top], s=11, facecolor="none", edgecolor="#4d0012", lw=0.7, label=f"top 10% of the index ({n_top})")
    g = f[f.stratum != "control, no flooding"]
    if len(g):
        a.scatter(g.load, g.eae_people, s=70, marker="*", c="black", edgecolor="white", lw=0.6, zorder=5, label="sampling site (paper 7)")
    a.axvline(ml, color="#666", ls="--", lw=0.9); a.axhline(me, color="#666", ls="--", lw=0.9)
    a.set_xscale("log"); a.set_yscale("log")
    a.set_xlim(ex.load.quantile(0.002), ex.load.max() * 1.5); a.set_ylim(ex.eae_people.quantile(0.002), ex.eae_people.max() * 1.5)
    a.set_xlabel("Routed source load (relative units, log)"); a.set_ylabel("People in floodwater, expected per year (log)")
    a.legend(fontsize=8.5, loc="lower left", markerscale=1.6, framealpha=0.92)
    a.set_title("a  Every exposed stretch: the medians define the four strata", loc="left", fontsize=11.5)
    # bivariate map, terciles of load and exposure
    BIV = np.array([["#e8e8e8", "#ace4e4", "#5ac8c8"], ["#dfb0d6", "#a5add3", "#5698b9"], ["#be64ac", "#8c62aa", "#3b4994"]])
    ql = pd.qcut(ex.load.rank(method="first"), 3, labels=False).values
    qe = pd.qcut(ex.eae_people.rank(method="first"), 3, labels=False).values
    ex["col"] = BIV[ql, qe]
    base(b); s.plot(ax=b, color="#c9d3dc", lw=0.35, zorder=2)
    g = s.loc[ex.seg.values].assign(col=ex.col.values, o=ql + qe).sort_values("o")
    g.plot(ax=b, color=g.col, linewidth=0.8 + 0.7 * g.o.values, zorder=3)
    names(b, size=8.5)
    b.set_title("b  The same on the map (terciles of load and exposure)", loc="left", fontsize=11.5)
    for i in range(3):
        for j in range(3):
            k.add_patch(plt.Rectangle((j, i), 1, 1, color=BIV[i, j]))
    k.set_xlim(0, 3); k.set_ylim(0, 3); k.set_xticks([]); k.set_yticks([]); k.set_aspect("equal")
    k.set_xlabel("exposure →", fontsize=9.5); k.set_ylabel("load →", fontsize=9.5)
    for sp in k.spines.values():
        sp.set_visible(False)
    fig.suptitle("Why the index is concentrated: few stretches carry both a large load and many people", x=0.01, ha="left", fontweight="bold", fontsize=14.5)
    save(fig, "am13_load_vs_exposure.png", OUT, "Sources: OpenStreetMap (© contributors) · " + MODEL + " · " + TERRAIN)


def am14(s):
    d = pd.read_csv(RES / "am_stretches.csv")
    ex = d[d.eae_people > 0]
    fig, ax = plt.subplots(figsize=(12, 10.5)); fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.08)
    base(ax); s.plot(ax=ax, color="#c9d3dc", lw=0.35, zorder=2)
    cmap = ListedColormap(["#fee8c8", "#fdbb84", "#e34a33", "#7f0000"]); norm = BoundaryNorm([0.01, 0.2, 0.5, 0.8, 1.0001], 4)
    g = ex[ex.p_top10 >= 0.01]
    sg = s.loc[g.seg.values].assign(p=g.p_top10.values).sort_values("p")
    sg.plot(ax=ax, column="p", cmap=cmap, norm=norm, linewidth=1.0 + 2.6 * sg.p.values, zorder=3)
    names(ax, size=9.5)
    n80 = int((ex.p_top10 >= 0.8).sum())
    hl = [Line2D([], [], color=c, lw=3) for c in cmap.colors]
    solid(ax.legend(hl, ["1–20% of draws", "20–50%", "50–80%", "80% or more"], loc="lower left", fontsize=10, framealpha=0.92,
              title="In the top 10% in this share\nof 1,000 random weightings", title_fontsize=10))
    fig.suptitle("Hotspots that do not depend on the weights", x=0.01, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.01, 0.925, f"{n80} stretches stay in the top 10% in at least 80% of weightings: the Lubigi and its tributaries, the "
             "Mayanja below it, the Nakivubo, and the southern channels to the bay.", fontsize=10.5, color="#555")
    save(fig, "am14_rank_stability_map.png", OUT, "Weights drawn log-uniformly within literature ranges · sources: OpenStreetMap (© contributors) · "
         + MODEL + " · " + TERRAIN)


def am15():
    q = pd.read_csv(RES / "am_intake.csv", parse_dates=["date"]).sort_values("date")
    fig, (a, b) = plt.subplots(2, 1, figsize=(14, 7.4), sharex=True, gridspec_kw=dict(height_ratios=[2.4, 1]))
    fig.subplots_adjust(top=0.84, bottom=0.12, left=0.07, right=0.98, hspace=0.08)
    a.axhline(1, color="#888", ls=":", lw=1); a.text(q.date.min(), 1.02, "open lake", fontsize=9, color="#666")
    a.plot(q.date, q.outlets_ratio, "-o", color="#d6604d", ms=5, lw=1.3, label="five highest-load channel outlets")
    a.plot(q.date, q.intake_ratio, "-o", color="#2166ac", ms=5, lw=1.3, label="within 1 km of the Ggaba intake")
    a.set_ylabel("Turbidity / open lake, same scene"); a.legend(fontsize=10, loc="upper left")
    for dt, v in zip(q.date, q.intake_ratio):
        if v > 1.55:
            a.annotate(f"{dt:%d %b %Y}", (dt, v), xytext=(6, 4), textcoords="offset points", fontsize=8.5, color="#2166ac")
    b.bar(q.date, q.r3, width=25, color=np.where(q.r3 >= 25, "#08519c", "#9ecae1"))
    b.axhline(25, color="#888", ls=":", lw=1); b.set_ylabel("Rain, 3 days\nbefore (mm)")
    a.set_title("Each point is one clear Sentinel-2 scene (35 scenes, 2017–2026)", loc="left", fontsize=11.5)
    fig.suptitle("The intake follows the outlet plume, scene after scene", x=0.01, ha="left", fontweight="bold", fontsize=14)
    save(fig, "am15_intake_timeline.png", OUT, "Turbidity: Copernicus Sentinel-2 L2A, Dogliotti et al. (2015) · intake: Ggaba waterworks "
         "(OpenStreetMap) · rain: CHIRPS")


def am16(s):
    import rasterio
    import xarray as xr
    from pyproj import Transformer
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand, acc, tr = r.read(2), r.read(3), r.transform
    H, W = hand.shape
    xs = tr.c + tr.a * (np.arange(W) + 0.5); ys = tr.f + tr.e * (np.arange(H) + 0.5)
    rr, cc = np.nonzero((acc >= 0.05) & (hand < 3))
    lo, la = xs[cc], ys[rr]
    inb = (lo > BOX[0]) & (lo < BOX[2]) & (la > BOX[1]) & (la < BOX[3])
    lo, la, rr, cc = lo[inb], la[inb], rr[inb], cc[inb]
    X, Y = Transformer.from_crs(4326, 32636, always_xy=True).transform(lo, la)
    veg = {}
    for yr in (1986, 2025):
        L = xr.open_dataset(KD / f"sat_landsat_{yr}.nc")
        v = ((L.nir08 - L.red) / (L.nir08 + L.red)).sel(x=xr.DataArray(X), y=xr.DataArray(Y), method="nearest").values
        veg[yr] = np.nan_to_num(v) > 0.45
    w = pd.read_csv(RES / "am_wetland_path.csv")
    w["lost"] = (w.wet_km_1986 - w.wet_km_2025).clip(lower=0)
    fig, axs = plt.subplots(1, 2, figsize=(16, 8.4)); fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.11, wspace=0.03)
    a, b = axs
    base(a)
    kept, lost, new = veg[1986] & veg[2025], veg[1986] & ~veg[2025], ~veg[1986] & veg[2025]
    for m, c in ((kept, "#1a9850"), (lost, "#d73027"), (new, "#a6d96a")):
        a.scatter(lo[m], la[m], s=1.1, c=c, marker="s", lw=0, zorder=3)
    names(a, size=8.5)
    a.set_title(f"a  Vegetated valley floor on the channel paths: {lost.sum() / max(veg[1986].sum(), 1) * 100:.0f}% of 1986 lost by 2025",
                loc="left", fontsize=11.5)
    solid(a.legend([Line2D([], [], ls="", marker="s", ms=8, color=c) for c in ("#1a9850", "#d73027", "#a6d96a")],
             ["vegetated in 1986 and 2025", "vegetated in 1986, not in 2025", "vegetated only in 2025"], loc="lower left", fontsize=9.5))
    base(b); s.plot(ax=b, color="#c9d3dc", lw=0.35, zorder=2)
    cmap = ListedColormap(["#fee0d2", "#fc9272", "#de2d26", "#67000d"]); norm = BoundaryNorm([0.25, 1, 2, 4, 50], 4)
    g = w[(w.load > 0) & (w.lost >= 0.25)]
    sg = s.loc[g.seg.values].assign(l=g.lost.values, lw=np.log10(g.load.values + 1)).sort_values("l")
    sg.plot(ax=b, column="l", cmap=cmap, norm=norm, linewidth=0.5 + 0.6 * sg.lw.clip(0, 4), zorder=3)
    names(b, size=8.5)
    solid(b.legend([Line2D([], [], color=c, lw=3) for c in cmap.colors], ["0.25–1 km", "1–2 km", "2–4 km", "more than 4 km"], loc="lower left",
             fontsize=9.5, framealpha=0.92, title="Wetland the stretch's load no longer\npasses downstream (1986 → 2025)", title_fontsize=9.5))
    b.set_title("b  The filter lost, stretch by stretch (line width: routed load)", loc="left", fontsize=11.5)
    fig.suptitle("Where the wetland filter was lost", x=0.01, ha="left", fontweight="bold", fontsize=15)
    save(fig, "am16_wetland_loss_map.png", OUT, "Vegetation: Landsat 5 TM (1986) and Landsat 8/9 OLI (2025) dry-season NDVI > 0.45, USGS · valley "
         "floor: HAND < 3 m (paper 2) · " + TERRAIN)


def am17(C, s):
    lon, lat, seg = cell_lonlat()
    wet = C["hourly"]; rain = C["hourly_rain"]
    t = pd.to_datetime(C["hourly_time"].astype("datetime64[m]"))
    import xarray as xr
    pop = np.nan_to_num(xr.open_dataset(PROC / "kampala_ghs_pop.nc").pop.sel(epoch=2020)
                        .sel(lat=xr.DataArray(lat), lon=xr.DataArray(lon), method="nearest").values) / 9.0
    people = (wet * pop[:, None]).sum(0)
    i0 = max(int(np.argmax(rain > 0.5)) - 2, 0); i1 = min(int(np.nonzero(people > 0)[0].max()) + 3, len(t))
    frames = list(range(i0, i1))
    src = ("Rain: PERSIANN-CCS hourly (CHRS, UC Irvine), x1.5 · " + MODEL + " · " + TERRAIN)

    def draw(fig, ax, k, small=False):
        base(ax); s.plot(ax=ax, color="#9fb3c8", lw=0.3 if small else 0.45, zorder=2)
        m = wet[:, k]
        ax.scatter(lon[m], lat[m], s=1.2 if small else 2.4, c="#08519c", marker="s", lw=0, zorder=3)
        if not small:
            names(ax, size=9)

    # animation
    ANI.mkdir(parents=True, exist_ok=True)
    imgs = []
    for k in frames:
        fig = plt.figure(figsize=(10, 9.6), dpi=100)
        ax = fig.add_axes([0.01, 0.2, 0.98, 0.7]); sp = fig.add_axes([0.08, 0.085, 0.82, 0.1])
        draw(fig, ax, k)
        sp.bar(range(len(frames)), rain[frames], color="#9ecae1", width=0.9)
        sp2 = sp.twinx(); sp2.plot(range(len(frames)), people[frames] / 1000, color="#b2182b", lw=1.8)
        sp2.scatter([k - i0], [people[k] / 1000], color="#b2182b", s=30, zorder=5)
        sp.axvline(k - i0, color="#444", lw=0.8)
        sp.set_ylabel("rain mm/h", fontsize=8.5, color="#3182bd"); sp2.set_ylabel("people (k)", fontsize=8.5, color="#b2182b")
        tk = list(range(0, len(frames), 4)); sp.set_xticks(tk); sp.set_xticklabels([f"{t[frames[j]]:%H:%M}" for j in tk])
        sp.tick_params(labelsize=8); sp2.tick_params(labelsize=8)
        fig.text(0.01, 0.965, "The flood of 18 March 2026, hour by hour", fontsize=15, fontweight="bold")
        fig.text(0.01, 0.93, f"{t[k]:%a %d %b, %H:%M} Kampala time  ·  rain {rain[k]:.1f} mm/h  ·  {people[k]:,.0f} people in water ≥10 cm",
                 fontsize=11, color="#333")
        fig.text(0.01, 0.012, src, fontsize=6.6, color="#555", wrap=True)
        fig.text(0.99, 0.035, CREDIT, fontsize=9.5, fontweight="bold", ha="right", color="#333")
        fig.canvas.draw()
        imgs.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()))
        plt.close(fig)
    pal = [im.convert("P", palette=Image.ADAPTIVE, colors=128) for im in imgs]
    pal[0].save(ANI / "am17_flood_20260318.gif", save_all=True, append_images=pal[1:], duration=[700] * (len(pal) - 1) + [2500], loop=0, optimize=True)
    import imageio_ffmpeg
    w_, h_ = imgs[0].size; w_ -= w_ % 2; h_ -= h_ % 2
    p = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w_}x{h_}",
                          "-r", "2", "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(ANI / "am17_flood_20260318.mp4")],
                         stdin=subprocess.PIPE)
    for im in imgs + [imgs[-1]] * 4:
        p.stdin.write(np.asarray(im.crop((0, 0, w_, h_))).tobytes())
    p.stdin.close(); p.wait()
    # still: six hours spread over the rise and recession
    pk = int(np.argmax(people))
    pick = sorted(set(int(x) for x in np.clip([pk - 3, pk - 2, pk - 1, pk, pk + 2, pk + 4], i0, i1 - 1)))
    fig, axs = plt.subplots(2, 3, figsize=(15, 11)); fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.08, wspace=0.03, hspace=0.1)
    for ax, k in zip(axs.flat, pick):
        draw(fig, ax, k, small=True)
        names(ax, size=8, keep={"Bwaise", "Kisenyi", "Ntinda", "Rubaga", "Kireka", "Namasuba", "Nansana"})
        ax.set_title(f"{t[k]:%d %b %H:%M}  ·  rain {rain[k]:.1f} mm/h  ·  {people[k] / 1000:,.0f}k people", loc="left", fontsize=11)
    for ax in list(axs.flat)[len(pick):]:
        ax.axis("off")
    fig.suptitle("The flood of 18 March 2026, hour by hour (still of the animation)", x=0.01, ha="left", fontweight="bold", fontsize=15)
    fig.text(0.01, 0.905, "Blue: 30 m squares in water of 10 cm or more. Hourly satellite rain x1.5, channels 30% silted.", fontsize=10.5, color="#555")
    save(fig, "am17_flood_20260318_still.png", ANI, src)
    print("animation frames", len(frames), "peak", t[pk], int(people[pk]), flush=True)


if __name__ == "__main__":
    import sys
    which = sys.argv[1:] or ["12", "13", "14", "15", "16", "17"]
    s = channels()
    C = cells() if {"12", "17"} & set(which) else None
    for k in which:
        {"12": lambda: am12(C, s), "13": lambda: am13(s), "14": lambda: am14(s), "15": am15, "16": lambda: am16(s), "17": lambda: am17(C, s)}[k]()
