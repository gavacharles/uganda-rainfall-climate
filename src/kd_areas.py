"""Kampala drainage study, part 5: one in-depth page per flood-hotspot area -> figures/kampala_drainage/areas/.

Each page: (1) satellite map of the channels draining to the area's reported flooding points, traced upstream
over the drain network, with only the culverts, waste points and buildings that bear on those channels;
(2) a high-zoom detail of the highest-priority segment; (3) location map; (4) key facts; (5) suggested
maintenance actions generated from the measured pressures; (6) a profile along the main traced channel.
Also writes results/kd_area_summary.csv and a combined PDF.
"""
import textwrap

import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapely
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D

from common import RES
from kd_maps import CM, IMG, KD, OUT, UTM, load, place_labels, trace

AREAS = [
    ("Bwaise–Kalerwe", "Lubigi and Nsooba channels",
     ["Bwaise", "Kalerwe", "Kanyanya", "Kyebando", "Nsooba Road", "Makerere Kavule", "Mulago roundabout"]),
    ("Kyambogo–Banda–Kinawataka", "Kinawataka channel at Jinja Road",
     ["Kyambogo junction (Jinja Road)", "Banda", "Kinawataka/Katogo-Mbuya", "Kireka", "Kasokoso bridge"]),
    ("Downtown Nakivubo", "Kisenyi, Old Taxi Park, Clock Tower, Katwe",
     ["Clock Tower", "Kisenyi", "Old Taxi Park", "Nakivubo Channel downtown", "Mukwano Road", "Katwe", "Queensway"]),
    ("Kitante–Lugogo", "Centenary Park, Lugogo Bypass, Lugogo lights by the mall and the Cricket Oval",
     ["Lugogo lights (Jinja Road by Lugogo Mall)", "Cricket Oval (Lugogo)", "Centenary Park", "Lugogo Bypass", "Seventh Street"]),
    ("Nalukolongo–Ndeeba", "Nalukolongo channel: Nateete, Kabuusu, Najjanankumbi",
     ["Nalukolongo", "Ndeeba", "Kabuusu", "Nateete", "Najjanankumbi"]),
    ("Lubigi wetland", "Hoima Road, Kasubi, Namungoona", ["Lubigi at Hoima Road", "Kasubi", "Namungoona"]),
    ("Kibuli–Kansanga–Gaba Road", "Kansanga and Kibuli-Kayunga channels",
     ["Kibuli", "Nsambya", "Gaba Road", "Soya-Bunga", "Munyonyo (Cape Road)"]),
    ("Lufuka–Masajja", "Lufuka channel: Kikajjo, Lubowa, Namasuba (2019 deaths)",
     ["Lufuka", "Kikajjo (Masajja)", "Lubowa (Masajja)", "Namasuba"]),
    ("Bukoto–Ntinda–Najjera", "upper Kinawataka and Nakivubo tributaries", ["Bukoto", "Ntinda (factory close)", "Najjera"]),
]


def wrap(t, w):
    return "\n".join(textwrap.wrap(t, w))


def actions(f):
    a = []
    if f["culverts"]:
        a.append(f"Inspect and desilt the {f['culverts']} culverts on these channels before each rainy season and "
                 "after big storms; check any that back water up for undersizing.")
    if f["waste"] >= 3:
        a.append(f"{f['waste']} mapped dump/waste points lie within 100 m of the channels: add skips and collection, "
                 "enforce no-dumping, and fit trash screens upstream of culverts.")
    if f["bldg15"] >= 10:
        a.append(f"{f['bldg15']:,} buildings stand within 15 m of the channels: enforce the drainage reserve, starting "
                 "with structures that narrow or cover the channel.")
    if f.get("pop2030", 0) > f.get("pop2020", 0) * 1.05:
        a.append(f"Population on the low ground here is projected to grow from {f['pop2020']:,.0f} (2020) to "
                 f"{f['pop2030']:,.0f} (2030): plan evacuation routes and keep the drainage reserve clear now.")
    if f["floodplain"] >= 100:
        a.append(f"{f['floodplain']:,} buildings sit on low ground (< 2 m above the drain) within 150 m: SMS early "
                 "warning on heavy-rain forecasts, raised floors and flood-proofing.")
    if f["wetland_pct"] < 10:
        w_ = "under 1" if f["wetland_pct"] < 1 else f"{f['wetland_pct']:.0f}"
        a.append(f"Only {w_}% of the land within 500 m is still wetland: protect what remains as flood "
                 "storage and stop further filling of the valley floor.")
    if f["emerging"] >= 60:
        a.append("Upstream paving is still growing fast: require on-site storm-water detention for new buildings upstream.")
    return a or ["No single pressure stands out: routine inspection and desilting."]


_POP = None


def pop_at_risk(R, dist=150, hand_max=2.0):
    """GHS-POP residents in ~100 m cells within `dist` m of the channels R and < hand_max m above the nearest drain."""
    global _POP
    if _POP is None:
        import rasterio
        import xarray as xr
        from common import PROC
        pop = xr.open_dataarray(PROC / "kampala_ghs_pop.nc")
        LO, LA = np.meshgrid(pop.lon.values, pop.lat.values)
        with rasterio.open(PROC / "kampala_catchments.tif") as r:
            hand = r.read(2)
            tr = r.transform
        col = ((LO - tr.c) / tr.a).astype(int).clip(0, hand.shape[1] - 1)
        row = ((LA - tr.f) / tr.e).astype(int).clip(0, hand.shape[0] - 1)
        h = hand[row, col].ravel()
        pts = gpd.GeoSeries(gpd.points_from_xy(LO.ravel(), LA.ravel()), crs=4326).to_crs(UTM).values
        _POP = dict(pop=pop.values.reshape(len(pop.epoch), -1), epochs=list(pop.epoch.values), hand=h,
                    tree=shapely.STRtree(pts))
    idx = np.unique(_POP["tree"].query(R.geometry.values, predicate="dwithin", distance=dist)[1])
    idx = idx[_POP["hand"][idx] < hand_max]
    return {int(e): float(_POP["pop"][k, idx].sum()) for k, e in enumerate(_POP["epochs"])}


def page(k, name, sub, places, s, hp, city, b, waste, cul, hs_all, events, pdf):
    hp_area = hp[hp.place.isin(places)]
    flowing = s[s.up_km2 >= 0.25]
    tree = shapely.STRtree(flowing.geometry.values)
    reaches = []
    for _, h in hp_area.iterrows():
        near = flowing.iloc[tree.query(h.geometry, predicate="dwithin", distance=700)]
        if near.empty:
            continue
        start = int((near.up_km2 / (1 + near.distance(h.geometry) / 250)).idxmax())
        reaches.append(trace(s, start, up_km=2500, down_km=600).assign(hotspot=h.place))
    if not reaches:
        print("no channels for", name)
        return None
    R = pd.concat(reaches)
    main = reaches[0]
    R = R[~R.index.duplicated()]
    # frame: hotspots plus the traced channels, capped
    hx, hy = hp_area.geometry.x, hp_area.geometry.y
    cx, cy = hx.mean(), hy.mean()
    rx0, ry0, rx1, ry1 = R.total_bounds
    span = max(hx.max() - hx.min(), hy.max() - hy.min()) + 900
    side = float(np.clip(max(span, min(max(rx1 - rx0, ry1 - ry0) + 400, 4200)), 1800, 6500))
    x0, x1, y0, y1 = cx - side / 2, cx + side / 2, cy - side / 2, cy + side / 2
    R = R.cx[x0:x1, y0:y1]
    main = main.cx[x0:x1, y0:y1]
    lon0, lat0, lon1, lat1 = gpd.GeoSeries(gpd.points_from_xy([x0, x1], [y0, y1]), crs=UTM).to_crs(4326).total_bounds
    bb = b.cx[lon0:lon1, lat0:lat1].to_crs(UTM)
    res = bb[bb.intersects(R.buffer(15).union_all())]
    w100 = waste[waste.intersects(R.buffer(100).union_all())]
    c25 = cul[cul.intersects(R.buffer(25).union_all())]
    f = dict(km=R.length_m.sum() / 1000, up=R.up_km2.max(), bldg15=len(res), waste=len(w100), culverts=len(c25),
             floodplain=int(R.bldg_floodplain.sum()), wetland_pct=100 * R.wetland_500m.mean(),
             built90=100 * R.loc[R.up_km2.idxmax()].up_built_1990, built20=100 * R.loc[R.up_km2.idxmax()].up_built_2020,
             valley90=100 * R.valley_built_1990.mean(), valley20=100 * R.valley_built_2020.mean(),
             priority=R.risk_pct.median(), emerging=R.emerging_pct.median())

    fig = plt.figure(figsize=(16.5, 11))
    fig.text(0.01, 0.972, f"{k}. {name}", fontsize=20, fontweight="bold", va="top")
    fig.text(0.01, 0.935, wrap(f"{sub}. Coloured lines: channels draining to the reported flooding points (circles), "
                               "traced upstream over the drain network.", 150), fontsize=9.5, color="#555", va="top")
    ax = fig.add_axes([0.01, 0.07, 0.56, 0.83])
    oth = s.cx[x0:x1, y0:y1]
    oth.plot(ax=ax, color="#d0d0d0", lw=np.where(oth.up_km2 >= 0.25, 0.9, 0.4), alpha=0.8)
    R.plot(ax=ax, color="white", lw=np.clip(2.5 + R.up_km2 ** 0.5, 3.5, 8.5), zorder=3)
    R.plot(ax=ax, column="risk_pct", cmap=CM, vmin=0, vmax=100, lw=np.clip(1.5 + R.up_km2 ** 0.5, 2.5, 7), zorder=4,
           missing_kwds=dict(color="#bdbdbd"))
    res.plot(ax=ax, facecolor="#ff00ff55", edgecolor="#ff00ff", lw=0.6, zorder=5)
    w100.plot(ax=ax, marker="^", color="#ffd400", edgecolor="k", markersize=55, lw=0.6, zorder=6)
    c25.plot(ax=ax, marker="s", color="white", edgecolor="k", markersize=30, lw=0.7, zorder=6)
    hp_area.plot(ax=ax, marker="o", facecolor="none", edgecolor="white", markersize=500, lw=3, zorder=7)
    hp_area.plot(ax=ax, marker="o", facecolor="none", edgecolor="#e8002a", markersize=500, lw=1.4, zorder=8)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ctx.add_basemap(ax, crs=f"EPSG:{UTM}", source=IMG, zoom=17 if side <= 3000 else 16, attribution_size=5)
    ax.set_axis_off()
    import matplotlib.patheffects as pe
    # detail of the highest-priority segment near a flooding point
    near_h = R[R.distance(hp_area.union_all()) <= 700]
    tgt = (near_h if len(near_h) else R).risk_pct.idxmax()
    c = R.loc[tgt].geometry.interpolate(0.5, normalized=True)
    d = 230
    rend = fig.canvas.get_renderer()
    from matplotlib.transforms import Bbox
    rad = (500 ** 0.5) / 2 * fig.dpi / 72 + 3  # circle radius in pixels (+ margin)
    circles = []
    for _, h in hp_area.iterrows():
        cxp, cyp = ax.transData.transform((h.geometry.x, h.geometry.y))
        circles.append(Bbox([[cxp - rad, cyp - rad], [cxp + rad, cyp + rad]]))
    boxes = list(circles)
    (bx0, by0), (bx1, by1) = ax.transData.transform([(c.x - d, c.y - d), (c.x + d, c.y + d)])
    for e_ in (Bbox([[bx0 - 2, by0 - 2], [bx1 + 2, by0 + 2]]), Bbox([[bx0 - 2, by1 - 2], [bx1 + 2, by1 + 2]]),
               Bbox([[bx0 - 2, by0], [bx0 + 2, by1]]), Bbox([[bx1 - 2, by0], [bx1 + 2, by1]])):
        boxes.append(e_)  # the four edges of the detail box
    cands = [(0, 22, "center"), (0, -36, "center"), (24, -6, "left"), (-24, -6, "right"), (0, 44, "center"),
             (0, -58, "center"), (30, 18, "left"), (-30, 18, "right"), (30, -30, "left"), (-30, -30, "right")]
    for _, h in hp_area.iterrows():
        for dx_, dy_, ha_ in cands:
            t = ax.annotate(h.place, (h.geometry.x, h.geometry.y), xytext=(dx_, dy_), textcoords="offset points",
                            ha=ha_, fontsize=10, fontweight="bold", color="white", zorder=12,
                            bbox=dict(facecolor="#b00020", edgecolor="none", pad=2, alpha=0.9))
            bb_ = t.get_window_extent(rend).expanded(1.06, 1.25)
            if not any(bb_.overlaps(o) for o in boxes):
                break
            t.remove()
        else:
            t = ax.annotate(h.place, (h.geometry.x, h.geometry.y), xytext=cands[0][:2], textcoords="offset points",
                            ha="center", fontsize=9, fontweight="bold", color="white", zorder=12,
                            bbox=dict(facecolor="#b00020", edgecolor="none", pad=2, alpha=0.9))
            bb_ = t.get_window_extent(rend)
        boxes.append(bb_)
    place_labels(ax, kinds=("suburb", "neighbourhood"), size=8.5, halo="black", color="white", frame=boxes, pad=2.0, maxn=10,
                 skip=[p_.split(" ")[0].split("/")[0].lower()[:6] for p_ in places])
    sb = 500 if side > 2500 else 200
    ax.plot([x0 + 0.04 * side, x0 + 0.04 * side + sb], [y0 + 0.04 * side] * 2, color="white", lw=4)
    ax.text(x0 + 0.04 * side + sb / 2, y0 + 0.058 * side, f"{sb} m", color="white", ha="center", fontsize=10,
            fontweight="bold", zorder=13, bbox=dict(facecolor="#000000aa", edgecolor="none", pad=1.5))

    dx = fig.add_axes([0.585, 0.53, 0.2, 0.33])
    dd = s.cx[c.x - d:c.x + d, c.y - d:c.y + d]
    dd.plot(ax=dx, column="risk_pct", cmap=CM, vmin=0, vmax=100, lw=4, missing_kwds=dict(color="#bdbdbd"), zorder=3)
    res.cx[c.x - d:c.x + d, c.y - d:c.y + d].plot(ax=dx, facecolor="#ff00ff55", edgecolor="#ff00ff", lw=1, zorder=4)
    w100.cx[c.x - d:c.x + d, c.y - d:c.y + d].plot(ax=dx, marker="^", color="#ffd400", edgecolor="k", markersize=80, zorder=5)
    c25.cx[c.x - d:c.x + d, c.y - d:c.y + d].plot(ax=dx, marker="s", color="white", edgecolor="k", markersize=45, zorder=5)
    dx.set_xlim(c.x - d, c.x + d)
    dx.set_ylim(c.y - d, c.y + d)
    ctx.add_basemap(dx, crs=f"EPSG:{UTM}", source=IMG, zoom=18, attribution=False)
    dx.set_xticks([])
    dx.set_yticks([])
    r = R.loc[tgt]
    dx.set_title(wrap(f"Detail: highest-priority segment ({r.risk_pct:.0f}th pct). Drivers: {r.top_drivers}", 46),
                 fontsize=8, loc="left")
    dx.plot([c.x - d + 25, c.x - d + 125], [c.y - d + 25] * 2, color="white", lw=3)
    dx.text(c.x - d + 75, c.y - d + 40, "100 m", color="white", ha="center", fontsize=8, fontweight="bold",
            path_effects=[pe.withStroke(linewidth=2, foreground="black")])
    ax.add_patch(plt.Rectangle((c.x - d, c.y - d), 2 * d, 2 * d, fill=False, ec="#00e5ff", lw=1.8, zorder=11))

    lx = fig.add_axes([0.80, 0.68, 0.19, 0.19])
    s[s.up_km2 >= 2].plot(ax=lx, color="#4575b4", lw=0.5)
    city.boundary.plot(ax=lx, color="#555", lw=0.6, ls="--")
    lx.add_patch(plt.Rectangle((x0, y0), side, side, fill=False, ec="#e8002a", lw=1.8))
    lx.set_xlim(*city.total_bounds[[0, 2]] + np.array([-4000, 4000]))
    lx.set_ylim(*city.total_bounds[[1, 3]] + np.array([-4000, 4000]))
    lx.set_aspect("equal")
    lx.set_xticks([])
    lx.set_yticks([])
    lx.set_title("Location in Greater Kampala", fontsize=9, loc="left")

    # key facts
    evs = {e.replace(" (deaths)", "") for p_ in places for e in str(hs_all.set_index("place").evidence.get(p_, "")).split("; ")
           if e.startswith("news") or e.startswith("local report")}
    dead = {e.replace(" (deaths)", "") for p_ in places for e in str(hs_all.set_index("place").evidence.get(p_, "")).split("; ")
            if e.endswith("(deaths)")}
    ev = "; ".join(e + (" (deaths)" if e in dead else "") for e in sorted(evs))
    facts = [("Channels traced", f"{f['km']:.1f} km"), ("Largest upstream area", f"{f['up']:.1f} km²"),
             ("Upstream built-up 1990 → 2020", f"{f['built90']:.0f}% → {f['built20']:.0f}%"),
             ("Valley floor built-up 1990 → 2020", f"{f['valley90']:.0f}% → {f['valley20']:.0f}%"),
             ("Buildings ≤ 15 m from channel", f"{f['bldg15']:,}"), ("Waste points ≤ 100 m", f"{f['waste']}"),
             ("Culverts", f"{f['culverts']}"), ("Low-lying buildings ≤ 150 m", f"{f['floodplain']:,}"),
             ("Priority / emerging (median pct)", f"{f['priority']:.0f} / {f['emerging']:.0f}")]
    fx = fig.add_axes([0.80, 0.375, 0.19, 0.30])
    fx.axis("off")
    yy = 1.0
    for a_, b_ in facts:
        fx.text(0, yy, a_, fontsize=8.5, color="#666", va="top", transform=fx.transAxes)
        fx.text(0, yy - 0.04, b_, fontsize=10.5, fontweight="bold", va="top", transform=fx.transAxes)
        yy -= 0.108
    ax2 = fig.add_axes([0.585, 0.355, 0.2, 0.15])
    ax2.axis("off")
    ax2.text(0, 1, "Reported flooding", fontsize=10, fontweight="bold", va="top", transform=ax2.transAxes)
    ax2.text(0, 0.80, wrap(ev.replace("news ", "").replace("editorial", "news commentary") or "KCCA/NEMA hotspot lists", 46), fontsize=8.5, va="top",
             transform=ax2.transAxes, color="#333")
    from common import PROC
    if (PROC / "kampala_ghs_pop.nc").exists():
        pr = pop_at_risk(R)
        f.update({f"pop{y}": v for y, v in pr.items()})
        ax2.text(0, 0.45, "People on low ground by these channels", fontsize=10, fontweight="bold", va="top",
                 transform=ax2.transAxes)
        ax2.text(0, 0.27, f"1990: {pr[1990]:,.0f}   2020: {pr[2020]:,.0f}\n2030 (projected): {pr[2030]:,.0f}",
                 fontsize=10, va="top", transform=ax2.transAxes, color="#b00020", fontweight="bold")
    # actions
    acts = actions(f)
    ax3 = fig.add_axes([0.585, 0.05, 0.41, 0.28])
    ax3.axis("off")
    ax3.text(0, 1, "Suggested maintenance actions (from the measured pressures)", fontsize=11, fontweight="bold",
             va="top", transform=ax3.transAxes)
    yy = 0.89
    for a_ in acts[:6]:
        t = wrap(a_, 105)
        ax3.text(0, yy, "• " + t.replace("\n", "\n   "), fontsize=8.8, va="top", transform=ax3.transAxes)
        yy -= 0.068 * (t.count("\n") + 1) + 0.035
    handles = [Line2D([], [], color="#a50026", lw=3, label="channel, high priority"),
               Line2D([], [], color="#4575b4", lw=3, label="channel, low priority"),
               Line2D([], [], color="#d0d0d0", lw=1.5, label="other drains"),
               Line2D([], [], marker="s", ls="", color="white", mec="k", label="culvert"),
               Line2D([], [], marker="s", ls="", color="#ff00ff55", mec="#ff00ff", label="building ≤ 15 m"),
               Line2D([], [], marker="^", ls="", color="#ffd400", mec="k", label="waste/dump point"),
               Line2D([], [], marker="o", ls="", mfc="none", mec="#e8002a", label="reported flooding")]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.01, 0.025), ncol=4, fontsize=9, frameon=False)
    fig.text(0.01, 0.008, "Imagery: Esri World Imagery (Esri, Maxar, Earthstar Geographics) · drains, waste, places: OpenStreetMap · buildings: Microsoft (2023) · "
             "elevation: Copernicus GLO-30 · built-up: JRC GHSL. Hotspot positions approximate (±500 m).",
             fontsize=7.5, color="#666")
    fig.text(0.99, 0.008, "Credit: Gava Charles", fontsize=10, fontweight="bold", color="#333", ha="right")
    fig.canvas.draw()
    rr = fig.canvas.get_renderer()
    texts = [t for t in fig.findobj(plt.Text) if t.get_text().strip() and t.get_visible() and t.axes is not ax
             and t.axes is not dx and t.axes is not lx]
    bbs = [(t.get_text()[:30], t.get_window_extent(rr)) for t in texts]
    clash = [(a[0], b[0]) for i_, a in enumerate(bbs) for b in bbs[i_ + 1:] if a[1].overlaps(b[1])]
    if clash:
        print("  TEXT OVERLAP on", name, clash[:6], flush=True)
    slug = "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_")
    fig.savefig(OUT / "areas" / f"kd13_{k:02d}_{slug}.png", dpi=150)
    pdf.savefig(fig, dpi=150)
    plt.close(fig)
    print(k, name, {kk: (round(v, 1) if isinstance(v, float) else v) for kk, v in f.items()}, flush=True)
    return dict(area=name, **f, actions=" | ".join(acts))


def main():
    s, hp, city = load()
    s = s.reset_index(drop=True)
    b = gpd.read_parquet(KD / "ms_buildings.parquet")
    waste = gpd.read_file(KD / "osm_waste.geojson").to_crs(UTM)
    waste["geometry"] = waste.geometry.representative_point()
    cul = gpd.read_file(KD / "osm_waterways.geojson")
    cul = cul[cul.tunnel.isin(["culvert", "yes"])].to_crs(UTM)
    cul["geometry"] = cul.geometry.interpolate(0.5, normalized=True)
    hs_all = pd.read_csv(KD / "flood_hotspots.csv")
    events = pd.read_csv(KD / "flood_events.csv")
    (OUT / "areas").mkdir(parents=True, exist_ok=True)
    rows = []
    with PdfPages(OUT / "kd13_hotspot_areas.pdf") as pdf:
        for k, (name, sub, places) in enumerate(AREAS, start=1):
            r = page(k, name, sub, places, s, hp, city, b, waste, cul, hs_all, events, pdf)
            if r:
                rows.append(r)
    pd.DataFrame(rows).round(2).to_csv(RES / "kd_area_summary.csv", index=False)


if __name__ == "__main__":
    main()
