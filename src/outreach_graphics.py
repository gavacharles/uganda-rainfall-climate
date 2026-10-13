"""Social-media graphics and animations for the Substack article and X posts (outreach/).

g1_2026_vs_1997.png       Uganda rain since 1 August: 2026 vs 1997, 2023 and the normal range
g2_elnino_iod.png         El Nino strength vs October-December rain, coloured by the Indian Ocean Dipole
g3_season_swap.png        Vegetation drought in the first vs second season, 1982-2003 vs 2013-2025
g4_warm_nights.png        Warm nights per year, 1981-1995 vs 2011-2025
g5_concrete_vs_climate.png Urbanisation already done vs climate change to come, five cities
g6_kampala_rain_vs_paving.png Kampala: design storm change vs impervious cover change
a1_rain_race.gif          animation: 2026 vs 1997 cumulative rain, day by day
a2_kampala_growth.gif     animation: Greater Kampala built-up surface, 1975-2030
"""
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap

from common import BLUE, CAT, ORANGE, PROC, RES, ROOT, chirps, zone_mean, zones

OUT = ROOT / "outreach"
OUT.mkdir(exist_ok=True)
BG, INK, MUTE, GRIDC = "#fbfaf7", "#16201c", "#6f7a75", "#e3e5e0"
RED, BLU, GRN = "#d0461e", "#1d6a8a", "#2e8b57"
CREDIT = "Credit: Gava Charles"


def credit(fig, y=0.03):
    fig.text(0.97, y, CREDIT, ha="right", fontsize=11, color=INK, fontweight="bold", alpha=0.75)
matplotlib.rcParams.update({"font.size": 15, "axes.titlesize": 22, "axes.titleweight": "bold", "figure.facecolor": BG,
                            "axes.facecolor": BG, "savefig.facecolor": BG, "axes.spines.top": False,
                            "axes.spines.right": False, "axes.edgecolor": GRIDC, "axes.grid": True, "grid.color": GRIDC,
                            "text.color": INK, "axes.labelcolor": MUTE, "xtick.color": MUTE, "ytick.color": MUTE,
                            "axes.titlelocation": "left", "legend.frameon": False})
W, H = 12, 6.75  # 16:9 at 150 dpi -> 1800 x 1012


def frame(title, sub, source):
    fig, ax = plt.subplots(figsize=(W, H))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.80, bottom=0.14)
    fig.text(0.08, 0.93, title, fontsize=24, fontweight="bold", color=INK)
    fig.text(0.08, 0.865, sub, fontsize=15, color=MUTE)
    fig.text(0.08, 0.03, source, fontsize=10, color=MUTE)
    credit(fig)
    return fig, ax


def uganda_cumulative():
    pr = chirps()[0]
    u = zone_mean(pr.where(zones() >= 0)).sel(zone="Uganda").to_series()
    cur = {}
    for y in range(1981, 2027):
        s = u.loc[f"{y}-08-01":f"{y + 1}-01-31"].values
        cur[y] = np.cumsum(s)
    L = min(len(v) for k, v in cur.items() if k < 2026)
    H_ = np.array([cur[y][:L] for y in range(1981, 2025)])
    return cur, H_, L


def g1():
    cur, Hh, L = uganda_cumulative()
    fig, ax = frame("2026 is dry so far. So was 1997.", "Uganda average rain since 1 August (mm). 1997 was the great El Niño flood year.",
                    "Data: CHIRPS v2.0 (final to Aug 2026, preliminary to 5 Oct 2026).")
    d = np.arange(L)
    ax.fill_between(d, np.percentile(Hh, 10, 0), np.percentile(Hh, 90, 0), color=GRIDC, label="normal range (1981–2024)")
    ax.plot(d, np.median(Hh, 0), color=MUTE, lw=2, label="typical year")
    ax.plot(d, cur[1997][:L], color=RED, lw=3, label="1997 (El Niño floods)")
    n = len(cur[2026])
    ax.plot(np.arange(n), cur[2026], color=INK, lw=4.5, label="2026 so far")
    ax.scatter([n - 1], [cur[2026][-1]], color=INK, s=80, zorder=5)
    ax.annotate("5 Oct 2026", (n - 1, cur[2026][-1]), xytext=(8, -28), textcoords="offset points", fontsize=13)
    ticks = pd.date_range("2001-08-01", "2002-01-01", freq="MS")
    ax.set_xticks([(t - pd.Timestamp("2001-08-01")).days for t in ticks])
    ax.set_xticklabels([t.strftime("%b") for t in ticks])
    ax.set_ylim(0)
    ax.legend(loc="upper left", fontsize=13)
    fig.savefig(OUT / "g1_2026_vs_1997.png", dpi=150)
    plt.close(fig)


def g2():
    t = pd.read_csv(RES / "forecast_year_table.csv")
    fig, ax = frame("El Niño alone doesn't bring the rain. The Indian Ocean decides.",
                    "Each dot is a year. Strong El Niño + warm western Indian Ocean (blue) = wet Oct–Dec.",
                    "Rain: CHIRPS 1981–2025. El Niño: NOAA ONI (Oct–Dec). Indian Ocean Dipole: ERSST v5 (Sep–Nov).")
    c = np.clip(t.DMI_SON, -1, 1)
    sc = ax.scatter(t.ONI_OND, t.OND_pct_anom, c=c, cmap=LinearSegmentedColormap.from_list("d", [RED, "#eeeeee", BLU]),
                    vmin=-1, vmax=1, s=140, edgecolor=INK, lw=0.5, zorder=3)
    for _, r in t.iterrows():
        if r.year in (1997, 2015, 2023, 1982, 2019, 2009):
            off = {1982: (8, -14), 2023: (-12, 9)}.get(int(r.year), (7, 5))
            ax.annotate(int(r.year), (r.ONI_OND, r.OND_pct_anom), xytext=off, textcoords="offset points", fontsize=12,
                        ha="right" if int(r.year) == 2023 else "left")
    ax.axhline(0, color=MUTE, lw=1)
    ax.axvline(2.2, color=INK, ls="--", lw=1.5)
    ax.text(2.25, -30, "2026\n(record\nEl Niño)", fontsize=12)
    ax.set_xlabel("El Niño strength (°C)")
    ax.set_ylabel("Uganda Oct–Dec rain vs normal (%)")
    cb = fig.colorbar(sc, ax=ax, pad=0.01, fraction=0.03)
    cb.set_label("Indian Ocean Dipole")
    fig.savefig(OUT / "g2_elnino_iod.png", dpi=150)
    plt.close(fig)


def g3():
    fig, ax = frame("Uganda's first season is weakening. The second is improving.",
                    "Share of districts with crops in vegetation drought (satellite), outside the Lake Victoria crescent",
                    "Data: NOAA STAR Vegetation Health (VCI < 35, cropland), 1982–2025. First season Apr–Jul, second Oct–Dec.")
    x = np.arange(2)
    early, late = [11, 21], [23, 3]
    ax.bar(x - 0.2, early, 0.38, color="#b9c4bf", label="1982–2003")
    ax.bar(x + 0.2, late, 0.38, color=[RED, BLU], label="2013–2025")
    for i in range(2):
        ax.text(i - 0.2, early[i] + 0.6, f"{early[i]}%", ha="center", fontsize=18, color=MUTE)
        ax.text(i + 0.2, late[i] + 0.6, f"{late[i]}%", ha="center", fontsize=22, fontweight="bold", color=[RED, BLU][i])
    ax.set_xticks(x)
    ax.set_xticklabels(["First season (Mar–Jul)", "Second season (Sep–Dec)"], fontsize=16)
    ax.set_ylabel("districts in vegetation drought (%)")
    ax.set_ylim(0, 28)
    ax.legend(fontsize=13)
    fig.savefig(OUT / "g3_season_swap.png", dpi=150)
    plt.close(fig)


def g4():
    e = pd.read_csv(RES / "temperature_extremes.csv").set_index("index")
    a, b = e.loc["Warm nights (TN90p, days/yr)", "mean_1981_1995"], e.loc["Warm nights (TN90p, days/yr)", "mean_2011_2025"]
    fig, ax = frame("Uganda's nights have got much hotter.", "Warm nights per year (warmer than 9 in 10 nights of 1991–2020 for that date)",
                    "Data: NOAA CPC daily minimum temperature, Uganda average. Daytime warming is real but its size is less certain.")
    ax.bar([0, 1], [a, b], 0.55, color=["#b9c4bf", RED])
    ax.text(0, a + 1.5, f"{a:.0f}", ha="center", fontsize=30, color=MUTE, fontweight="bold")
    ax.text(1, b + 1.5, f"{b:.0f}", ha="center", fontsize=36, color=RED, fontweight="bold")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["1981–1995", "2011–2025"], fontsize=17)
    ax.set_ylabel("warm nights per year")
    ax.set_ylim(0, b * 1.25)
    fig.savefig(OUT / "g4_warm_nights.png", dpi=150)
    plt.close(fig)


def g5():
    u = pd.read_csv(RES / "cities_urban_vs_climate.csv")
    fig, ax = frame("Concrete before climate.", "Rise in 10-year flood peaks: urban growth already done vs climate change still to come",
                    "Peak flows: SCS runoff model, 154 catchments. Paving: GHSL 1975–2020. Climate: CMIP6 median, 2041–2070.")
    x = np.arange(len(u))
    ax.bar(x - 0.2, u.urban_past_1975_2020_pct, 0.38, color=RED, label="paving & building, 1975–2020")
    ax.bar(x + 0.2, u.climate_ssp585_pct, 0.38, color=BLU, label="climate change by 2041–70 (high emissions)")
    for i, r in u.iterrows():
        ax.text(i - 0.2, r.urban_past_1975_2020_pct + 1, f"+{r.urban_past_1975_2020_pct:.0f}%", ha="center", fontsize=15, fontweight="bold", color=RED)
        ax.text(i + 0.2, r.climate_ssp585_pct + 1, f"+{r.climate_ssp585_pct:.0f}%", ha="center", fontsize=13, color=BLU)
    ax.set_xticks(x)
    ax.set_xticklabels(u.city, fontsize=15)
    ax.set_ylabel("increase in 10-year flood peak (%)")
    ax.set_ylim(0, 68)
    ax.legend(fontsize=13)
    fig.savefig(OUT / "g5_concrete_vs_climate.png", dpi=150)
    plt.close(fig)


def g6():
    rs = pd.read_csv(RES / "kampala_rain_stats.csv")
    r10 = rs[(rs["product"] == "CHIRPS") & (rs["T"] == 10)].iloc[0]
    at = pd.read_csv(RES / "kampala_attribution.csv")
    at = at[(at["product"] == "CHIRPS") & (at["T"] == 10)]
    w = at.area_km2 / at.area_km2.sum()
    i92, i14 = 100 * (at.imp_1992 * w).sum(), 100 * (at.imp_2014 * w).sum()
    fig, ax = frame("Kampala's storms haven't grown. Its concrete has.", "Storms: 1981–2003 vs 2004–2025.  Paved surface: 1992 vs 2014.",
                    "10-year 1-day storm: CHIRPS, gauge-calibrated. Impervious cover: GHSL + WorldCover, 10 Kampala catchments.")
    ax.axis("off")
    for y0, lab, a, b, unit, col in ((0.70, "10-year storm (1 day)", r10.rl_1981_2003_mm, r10.rl_2004_2025_mm, " mm", MUTE),
                                     (0.30, "Paved / built surface", i92, i14, "%", RED)):
        ax.text(0.0, y0, lab, fontsize=22, transform=ax.transAxes, color=MUTE, va="center")
        ax.text(0.60, y0, f"{a:.0f}{unit}", fontsize=36, transform=ax.transAxes, color="#9aa49f", fontweight="bold", va="center", ha="right")
        ax.text(0.665, y0, "→", fontsize=34, transform=ax.transAxes, color=MUTE, va="center", ha="center")
        ax.text(0.73, y0, f"{b:.0f}{unit}", fontsize=46, transform=ax.transAxes, color=col, fontweight="bold", va="center")
    ax.text(0.0, -0.02, "Paving alone raised Kampala's 10-year flood peaks by about 60% since 1975.", fontsize=17,
            transform=ax.transAxes, color=INK)
    fig.savefig(OUT / "g6_kampala_rain_vs_paving.png", dpi=150)
    plt.close(fig)


def a1():
    cur, Hh, L = uganda_cumulative()
    n26 = len(cur[2026])
    fig, ax = frame("2026 vs 1997: the race isn't over", "Uganda average rain since 1 August (mm)",
                    "Data: CHIRPS v2.0 (preliminary for Sep–Oct 2026).")
    d = np.arange(L)
    ax.fill_between(d, np.percentile(Hh, 10, 0), np.percentile(Hh, 90, 0), color=GRIDC)
    ax.plot(d, np.median(Hh, 0), color=MUTE, lw=2)
    ax.set_xlim(0, L)
    ax.set_ylim(0, max(cur[1997][:L].max(), np.percentile(Hh, 90, 0).max()) * 1.05)
    ticks = pd.date_range("2001-08-01", "2002-01-01", freq="MS")
    ax.set_xticks([(t - pd.Timestamp("2001-08-01")).days for t in ticks])
    ax.set_xticklabels([t.strftime("%b") for t in ticks])
    l97, = ax.plot([], [], color=RED, lw=3, label="1997")
    l26, = ax.plot([], [], color=INK, lw=4.5, label="2026")
    lab = ax.text(0.02, 0.9, "", transform=ax.transAxes, fontsize=18, fontweight="bold")
    note = ax.text(0.45, 0.25, "", transform=ax.transAxes, fontsize=16, color=INK)
    ax.legend(loc="upper left", bbox_to_anchor=(0, 0.85), fontsize=14)
    days = list(range(0, L, 3)) + [L - 1] * 15

    def step(i):
        k = days[i]
        l97.set_data(np.arange(k + 1), cur[1997][:k + 1])
        kk = min(k, n26 - 1)
        l26.set_data(np.arange(kk + 1), cur[2026][:kk + 1])
        lab.set_text((pd.Timestamp("2001-08-01") + pd.Timedelta(days=k)).strftime("%d %b"))
        note.set_text("2026: data end 5 Oct.\nThe El Niño rains, if they come,\nusually arrive late Oct–Nov." if k >= n26 else "")
        return l97, l26, lab, note
    anim = FuncAnimation(fig, step, frames=len(days), blit=False)
    anim.save(OUT / "a1_rain_race.gif", writer=PillowWriter(fps=12), dpi=80)
    plt.close(fig)


def a2():
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc")
    frac = (g / 8573.0).clip(0, 1)  # built m2 per ~92.6 m cell
    import geopandas as gpd
    d2 = gpd.read_file(PROC / "uganda_adm2.geojson")
    city = d2[d2.shapeName == "Kampala"]
    lake = gpd.read_file(Path.home() / "uganda-concrete-climate" / "data" / "raw" / "naturalearth" / "ne_10m_lakes.geojson")
    fig, ax = plt.subplots(figsize=(8, 8))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.11)
    fig.text(0.04, 0.94, "Greater Kampala, built up", fontsize=24, fontweight="bold")
    fig.text(0.04, 0.03, "Data: JRC Global Human Settlement Layer (GHS-BUILT-S R2023A); 2025–2030 are projections.", fontsize=10, color=MUTE)
    credit(fig, 0.065)
    cm = LinearSegmentedColormap.from_list("b", [BG, "#f0b9a4", RED, "#6e1f0b"])
    im = ax.pcolormesh(frac.lon, frac.lat, frac.isel(epoch=0), cmap=cm, vmin=0, vmax=0.6, shading="auto")
    lake.plot(ax=ax, color="#cfe3ec", zorder=2)
    city.boundary.plot(ax=ax, color=INK, lw=1.2, ls="--", zorder=3)
    ax.set_xlim(float(frac.lon.min()), float(frac.lon.max()))
    ax.set_ylim(float(frac.lat.min()), float(frac.lat.max()))
    ax.set_aspect("equal")
    ax.axis("off")
    yr = fig.text(0.72, 0.94, "", fontsize=30, fontweight="bold", color=RED)
    km = fig.text(0.04, 0.885, "", fontsize=16, color=MUTE)
    eps = list(frac.epoch.values)
    seq = [e for e in eps for _ in range(3)] + [eps[-1]] * 6

    def step(i):
        e = seq[i]
        im.set_array(frac.sel(epoch=e).values.ravel())
        yr.set_text(str(e))
        km.set_text(f"{float(g.sel(epoch=e).sum()) / 1e6:.0f} km² of buildings in the frame   (dashed: Kampala city)")
        return im, yr, km
    anim = FuncAnimation(fig, step, frames=len(seq), blit=False)
    anim.save(OUT / "a2_kampala_growth.gif", writer=PillowWriter(fps=4), dpi=90)
    plt.close(fig)


if __name__ == "__main__":
    for f in (g1, g2, g3, g4, g5, g6, a1, a2):
        f()
        print("done", f.__name__, flush=True)


CITIES = {
    "nairobi": dict(name="Nairobi", title="Nairobi's storms haven't grown. Its concrete has.", T=10, pct=False),
    "lagos": dict(name="Lagos", title="Lagos: flat storms, rising concrete.", T=10, pct=False),
    "dar_es_salaam": dict(name="Dar es Salaam", title="Dar es Salaam: heavier storms AND more concrete.", T=10, pct=True),
    "johannesburg": dict(name="Johannesburg", title="Johannesburg: heavier storms AND more concrete.", T=2, pct=False),
}


def city_card(city):
    cfg = CITIES[city]
    rs = pd.read_csv(RES / f"{city}_rain_stats.csv")
    r = rs[(rs["product"] == "CHIRPS") & (rs["T"] == cfg["T"])].iloc[0]
    at = pd.read_csv(RES / f"{city}_attribution.csv")
    at = at[(at["product"] == "CHIRPS") & (at["T"] == 10)].drop_duplicates("catchment")
    w = at.area_km2 / at.area_km2.sum()
    i92, i14 = 100 * (at.imp_1992 * w).sum(), 100 * (at.imp_2014 * w).sum()
    u = pd.read_csv(RES / "cities_urban_vs_climate.csv").set_index("city").loc[cfg["name"]]
    fig, ax = frame(cfg["title"], "Storms: 1981–2003 vs 2004–2025.  Paved surface: 1992 vs 2014.",
                    f"Storm: CHIRPS, gauge-calibrated. Paving: GHSL + WorldCover, {len(at)} catchments. Climate: CMIP6 2041–70.")
    ax.axis("off")
    storm_col = RED if r.change_pct > 5 else MUTE
    if cfg["pct"]:
        rows = ((0.70, f"{cfg['T']}-year storm (1 day)", "1981–2003", f"{r.change_pct:+.0f}%", storm_col, True),)
    else:
        rows = ((0.70, f"{cfg['T']}-year storm (1 day)", f"{r.rl_1981_2003_mm:.0f} mm", f"{r.rl_2004_2025_mm:.0f} mm", storm_col, False),)
    rows += ((0.30, "Paved / built surface", f"{i92:.0f}%", f"{i14:.0f}%", RED, False),)
    for y0, lab, a, b, col, single in rows:
        ax.text(0.0, y0, lab, fontsize=22, transform=ax.transAxes, color=MUTE, va="center")
        if single:
            ax.text(0.60, y0, "change", fontsize=26, transform=ax.transAxes, color="#9aa49f", va="center", ha="right")
        else:
            ax.text(0.60, y0, a, fontsize=36, transform=ax.transAxes, color="#9aa49f", fontweight="bold", va="center", ha="right")
            ax.text(0.665, y0, "→", fontsize=34, transform=ax.transAxes, color=MUTE, va="center", ha="center")
        ax.text(0.73, y0, b, fontsize=46, transform=ax.transAxes, color=col, fontweight="bold", va="center")
    ax.text(0.0, -0.02, f"Paving since 1975: +{u.urban_past_1975_2020_pct:.0f}% on 10-year flood peaks. "
            f"Climate change by 2050s: +{u.climate_ssp245_pct:.0f} to +{u.climate_ssp585_pct:.0f}%.", fontsize=17,
            transform=ax.transAxes, color=INK)
    fig.savefig(OUT / f"g7_{city}_card.png", dpi=150)
    plt.close(fig)


def city_growth(city, name):
    import rasterio
    g = xr.open_dataarray(PROC / f"{city}_ghsl_built.nc")
    clat = np.cos(np.deg2rad(float(g.lat.mean())))
    cell = abs(float(np.diff(g.lon)[0])) * 111320 * clat * abs(float(np.diff(g.lat)[0])) * 111320
    frac = (g / cell).clip(0, 1)
    with rasterio.open(PROC / f"{city}_worldcover.tif") as r:
        wc = r.read(1, out_shape=(r.height // 10, r.width // 10))
        b = r.bounds
    water = np.where(wc == 80, 1.0, np.nan)
    import geopandas as gpd
    fig, ax = plt.subplots(figsize=(8, 8))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.11)
    fig.text(0.04, 0.94, f"{name}, built up", fontsize=24, fontweight="bold")
    fig.text(0.04, 0.03, "Data: JRC Global Human Settlement Layer (GHS-BUILT-S R2023A); 2025–2030 are projections.", fontsize=10, color=MUTE)
    credit(fig, 0.065)
    cm = LinearSegmentedColormap.from_list("b", [BG, "#f0b9a4", RED, "#6e1f0b"])
    im = ax.pcolormesh(frac.lon, frac.lat, frac.isel(epoch=0), cmap=cm, vmin=0, vmax=0.6, shading="auto")
    ax.imshow(water, extent=(b.left, b.right, b.bottom, b.top), cmap=LinearSegmentedColormap.from_list("w", ["#cfe3ec", "#cfe3ec"]),
              zorder=2, interpolation="nearest")
    bd = PROC / ("uganda_adm2.geojson" if city == "kampala" else f"{city}_boundary.geojson")
    gpd.read_file(bd).boundary.plot(ax=ax, color=INK, lw=1.2, ls="--", zorder=3)
    ax.set_xlim(float(frac.lon.min()), float(frac.lon.max()))
    ax.set_ylim(float(frac.lat.min()), float(frac.lat.max()))
    ax.set_aspect("equal")
    ax.axis("off")
    yr = fig.text(0.74, 0.94, "", fontsize=30, fontweight="bold", color=RED)
    km = fig.text(0.04, 0.885, "", fontsize=16, color=MUTE)
    eps = list(frac.epoch.values)
    seq = [e for e in eps for _ in range(3)] + [eps[-1]] * 6

    def step(i):
        e = seq[i]
        im.set_array(frac.sel(epoch=e).values.ravel())
        yr.set_text(str(e))
        km.set_text(f"{float(g.sel(epoch=e).sum()) / 1e6:.0f} km² of buildings in the frame   (dashed: city boundary)")
        return im, yr, km
    FuncAnimation(fig, step, frames=len(seq), blit=False).save(OUT / f"a3_{city}_growth.gif", writer=PillowWriter(fps=4), dpi=80)
    plt.close(fig)


def cities():
    for c, cfg in CITIES.items():
        city_card(c)
        city_growth(c, cfg["name"])
        print("city", c, flush=True)


def g8():
    z = pd.read_csv(RES / "irrigation_zone.csv").set_index("zone").drop("Uganda")
    short = {"Karamoja (NE, semi-arid)": "Karamoja", "North (Acholi-Kitgum)": "Acholi", "West Nile-Lango-Teso-Elgon belt": "West Nile–Lango–Teso",
             "Mid-west & Kyoga (Bunyoro-Kyoga)": "Bunyoro–Kyoga", "Lake Victoria crescent (Central-Busoga)": "Central–Busoga",
             "South-west (Ankole-Kigezi)": "Ankole–Kigezi"}
    d = z["Design duty, peak month (l/s/ha)"].rename(index=short).sort_values()
    nir = z["NIR 80% dependable rain, year-round (mm/yr)"].rename(index=short).reindex(d.index)
    fig, ax = frame("How much water does a hectare of irrigation need?",
                    "Peak-month design flow per hectare, by region (4 years in 5 rainfall, 65% field efficiency)",
                    "Data: CHIRPS rainfall, NASA POWER evaporation (FAO-56). Annual net need in brackets.")
    ax.barh(d.index, d.values, color=[RED if v > 1.0 else BLU for v in d.values], height=0.6)
    for i, (v, n) in enumerate(zip(d.values, nir.values)):
        ax.text(v + 0.02, i, f"{v:.2f} l/s/ha   ({n:,.0f} mm/yr)", va="center", fontsize=14)
    ax.set_xlim(0, 1.75)
    ax.set_xlabel("litres per second per hectare (peak month)")
    ax.grid(axis="y")
    fig.savefig(OUT / "g8_irrigation_need.png", dpi=150)
    plt.close(fig)


def g9():
    import geopandas as gpd
    d = gpd.read_file(PROC / "uganda_adm2.geojson")
    w = pd.read_csv(RES / "water_district.csv").drop_duplicates("district").set_index("district")
    d["AI"] = d.shapeName.map(w.AI)
    d["dry"] = d.shapeName.map(w.dry_months)
    fig, ax = plt.subplots(figsize=(W, H))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.82, bottom=0.08)
    fig.text(0.04, 0.93, "Where Uganda is short of water", fontsize=24, fontweight="bold")
    fig.text(0.04, 0.865, "Rain compared with evaporation, 1991–2020, by county. Darker = drier.", fontsize=15, color=MUTE)
    fig.text(0.04, 0.03, "Aridity index = rainfall / reference evaporation (CHIRPS, NASA POWER). Counties: geoBoundaries ADM2.", fontsize=10, color=MUTE)
    credit(fig)
    bins = [0, 0.5, 0.65, 0.8, 1.0, 5]
    cols = ["#7a2a10", RED, "#f0b9a4", "#cfe3ec", BLU]
    labs = ["semi-arid", "dry sub-humid", "moist sub-humid", "humid", "very humid"]
    d["cls"] = pd.cut(d.AI, bins, labels=False)
    for k, c in enumerate(cols):
        d[d.cls == k].plot(ax=ax, color=c, edgecolor="white", lw=0.3)
    d[d.cls.isna()].plot(ax=ax, color="#e8e8e4", edgecolor="white", lw=0.3)
    ax.set_axis_off()
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label=l) for c, l in zip(cols, labs)], loc="lower left", fontsize=13,
              bbox_to_anchor=(1.0, 0.05))
    notes = [("Karamoja: semi-arid,\nup to 8 dry months", (34.4, 2.9), (35.4, 3.6)),
             ("Acholi–Lango–Teso:\ndry sub-humid, 4–5 dry months", (33.3, 2.0), (35.4, 1.4)),
             ("Ankole rangelands:\n4–5 dry months", (30.9, -0.5), (28.3, -1.3))]
    for t, xy, xt in notes:
        ax.annotate(t, xy, xytext=xt, fontsize=12, arrowprops=dict(arrowstyle="-", color=MUTE, lw=1), color=INK)
    ax.set_xlim(27.6, 37.2)
    fig.savefig(OUT / "g9_water_scarce_map.png", dpi=150)
    plt.close(fig)


def g10():
    t = pd.read_csv(RES / "fp_ipc_karamoja.csv", parse_dates=["date"])
    t = t[t.dataset == "CHIRPS"]
    ipc = (t.groupby(t.date.dt.year).share_phase3plus.mean() * 100).loc[2011:2024]
    s = xr.open_dataset(PROC / "wrsi_chirps.nc")
    mk = s.zone.values == 0  # Karamoja
    w = pd.Series(np.nanmean(s["S1_maize_A"].values[:, mk], 1), index=s.year.values).loc[2011:2024]
    fig = plt.figure(figsize=(W, H))
    fig.text(0.08, 0.93, "Rain alone doesn't explain Karamoja's growing hunger", fontsize=24, fontweight="bold")
    fig.text(0.08, 0.865, "Food crisis rose in good rainy seasons (2019–20) as well as poor ones (2021–23)", fontsize=15, color=MUTE)
    fig.text(0.08, 0.03, "Data: FEWS NET IPC classifications (Karamoja units); season quality = maize water-satisfaction index (WRSI) from CHIRPS.", fontsize=10, color=MUTE)
    credit(fig)
    a1 = fig.add_axes([0.08, 0.50, 0.88, 0.30])
    a2 = fig.add_axes([0.08, 0.13, 0.88, 0.30], sharex=a1)
    a1.bar(ipc.index, ipc.values, color=RED, width=0.7)
    a1.set_ylabel("% of areas\nin crisis+")
    a1.set_title("Food crisis (IPC Phase 3+)", fontsize=15, loc="left")
    a2.bar(w.index, w.values, color=[BLU if v >= 80 else "#9aa49f" for v in w.values], width=0.7)
    a2.axhline(80, color=INK, lw=1, ls="--")
    a2.text(2021.55, 84, "good season", fontsize=12, color=INK)
    a2.set_ylim(0, 105)
    a2.set_ylabel("season quality\n(0–100)")
    a2.set_title("Rainy-season quality for crops", fontsize=15, loc="left")
    plt.setp(a1.get_xticklabels(), visible=False)
    fig.savefig(OUT / "g10_karamoja_hunger_vs_rain.png", dpi=150)
    plt.close(fig)


def g11():
    fig, ax = frame("Design numbers for NDP IV", "What Uganda's engineers should plan with, from 45 years of data",
                    "Screening values from CHIRPS (gauge-calibrated), GHSL, CMIP6, FAO-56. Use UNMA gauges for final design.")
    ax.axis("off")
    items = [("79 mm", "Kampala 10-year 1-day design storm\n(add +9–13% for the 2050s)", BLU),
             ("0.6–1.3", "litres/s per hectare: peak irrigation\ndemand, wettest to driest region", GRN),
             ("65–74%", "of normal rain in the driest 12 months\n(2008–10): the drought to design for", RED),
             ("26–116 m³", "per hectare of on-site storage cancels\nKampala's extra runoff since 1992", "#7a5c00")]
    for k, (big, small, c) in enumerate(items):
        x, y = (0.0 if k % 2 == 0 else 0.52), (0.62 if k < 2 else 0.12)
        ax.text(x, y + 0.2, big, fontsize=44, fontweight="bold", color=c, transform=ax.transAxes)
        ax.text(x, y, small, fontsize=15, color=INK, transform=ax.transAxes, va="bottom")
    fig.savefig(OUT / "g11_design_numbers.png", dpi=150)
    plt.close(fig)


def a4_hot_nights():
    """Playful night-sky animation: warm nights per year across Uganda, 1981-2025 (CPC Tmin, TN90p, 3-yr mean)."""
    import geopandas as gpd
    import shapely
    from matplotlib.patches import Circle
    from common import grid_mask, uganda
    cpc = xr.open_dataset(PROC / "cpc_uganda_daily.nc")["tmin"].sel(time=slice("1981", "2025")).load()
    base = cpc.sel(time=slice("1991", "2020"))
    doy = lambda d: d.time.dt.dayofyear.clip(max=365)
    q = base.groupby(doy(base)).quantile(0.9, "time")
    q = q.pad(dayofyear=7, mode="wrap").rolling(dayofyear=15, center=True).mean().isel(dayofyear=slice(7, -7))
    tn90 = (cpc.groupby(doy(cpc)) > q).groupby("time.year").sum()
    tn90 = tn90.rolling(year=3, center=True, min_periods=1).mean()
    # smooth to a fine grid and clip to Uganda
    lat = np.arange(-1.55, 4.3, 0.04)
    lon = np.arange(29.5, 35.1, 0.04)
    fine = tn90.interp(lat=lat, lon=lon, method="linear", kwargs={"fill_value": None})
    LO, LA = np.meshgrid(lon, lat)
    ug = uganda()
    shapely.prepare(ug)
    inside = shapely.contains_xy(ug, LO, LA)
    m = grid_mask(cpc.lat, cpc.lon, exclude_lakes=False)
    nat = tn90.where(m).mean(("lat", "lon")).to_series()
    years = list(tn90.year.values)
    NIGHT, STAR = "#0b1430", "#f4f1d6"
    cm = LinearSegmentedColormap.from_list("night", ["#1d3c78", "#4b5fb0", "#9a5fb5", "#e0705a", "#ffb347", "#fff1a8"])
    fig = plt.figure(figsize=(7, 7.6), facecolor=NIGHT)
    ax = fig.add_axes([0.04, 0.17, 0.92, 0.66], facecolor=NIGHT)
    rng = np.random.default_rng(3)
    sx, sy = rng.uniform(29.3, 35.3, 160), rng.uniform(-1.8, 4.6, 160)
    sx_out = ~shapely.contains_xy(ug, sx, sy)
    sx, sy = sx[sx_out], sy[sx_out]
    stars = ax.scatter(sx, sy, s=rng.uniform(1, 9, sx.size), c=STAR, alpha=0.8, lw=0)
    im = ax.pcolormesh(lon, lat, np.where(inside, fine.isel(year=0), np.nan), cmap=cm, vmin=0, vmax=120, shading="auto")
    lakes = gpd.read_file(Path.home() / "uganda-concrete-climate" / "data" / "raw" / "naturalearth" / "ne_10m_lakes.geojson")
    lakes = lakes.cx[29.3:35.3, -1.8:4.6]
    lakes.plot(ax=ax, color=NIGHT, zorder=3)
    gpd.GeoSeries([ug]).boundary.plot(ax=ax, color="#cfd6ff", lw=0.8, zorder=4)
    ax.set_xlim(29.3, 35.3)
    ax.set_ylim(-1.8, 4.6)
    ax.set_aspect("equal")
    ax.axis("off")
    moon = Circle((34.55, -1.05), 0.42, color="#e8e8f0", zorder=5)
    ax.add_patch(moon)
    fig.text(0.05, 0.93, "Uganda's nights are heating up", fontsize=18, fontweight="bold", color="white")
    fig.text(0.05, 0.885, "Warm nights per year (warmer than 9 in 10 nights of 1991–2020)", fontsize=11.5, color="#b9c2e6")
    yr = fig.text(0.95, 0.93, "", fontsize=26, fontweight="bold", color="#ffb347", ha="right")
    cnt = fig.text(0.05, 0.835, "", fontsize=15, color="white")
    sp = fig.add_axes([0.08, 0.075, 0.84, 0.085], facecolor=NIGHT)
    sp.set_xlim(years[0], years[-1])
    sp.set_ylim(0, max(nat.max() * 1.15, 10))
    for side in sp.spines.values():
        side.set_visible(False)
    sp.tick_params(colors="#b9c2e6", labelsize=9)
    sp.set_yticks([])
    sp.grid(False)
    line, = sp.plot([], [], color="#ffb347", lw=2.2)
    dot, = sp.plot([], [], "o", color="#fff1a8", ms=6)
    fig.text(0.05, 0.015, "Data: NOAA CPC daily minimum temperature, 3-year running mean.", fontsize=8.5, color="#8d96bd")
    fig.text(0.95, 0.015, CREDIT, fontsize=10, color="white", fontweight="bold", ha="right", alpha=0.85)
    mcol = LinearSegmentedColormap.from_list("moon", ["#e8e8f0", "#ffd27a", "#ff7a3d", "#d8402a"])
    seq = [y for y in years for _ in range(2)] + [years[-1]] * 14

    def step(i):
        y = seq[i]
        im.set_array(np.where(inside, fine.sel(year=y).values, np.nan).ravel())
        v = float(nat.loc[y])
        yr.set_text(str(y))
        cnt.set_text(f"Uganda average: {v:.0f} warm nights a year")
        moon.set_color(mcol(np.clip((v - 15) / 70, 0, 1)))
        stars.set_alpha(0.25 + 0.6 * abs(np.sin(i * 0.7)) * (1 - np.clip(v / 90, 0, 0.6)))
        hist = nat.loc[:y]
        line.set_data(hist.index, hist.values)
        dot.set_data([y], [v])
        return im, yr, cnt, moon, stars, line, dot
    FuncAnimation(fig, step, frames=len(seq), blit=False).save(OUT / "a4_hot_nights.gif", writer=PillowWriter(fps=8),
                                                            dpi=100, savefig_kwargs={"facecolor": NIGHT})
    plt.close(fig)
    print("national warm nights", nat.loc[[1982, 2000, 2024]].round(0).to_dict())


def cover():
    """Substack cover (1456x1048) and social preview (1200x630): headline + map of 2026 rain as % of normal."""
    import geopandas as gpd
    import shapely
    from common import uganda
    pr = chirps()[0]
    last = pd.Timestamp(pr.time.values[-1])
    win = lambda y: pr.sel(time=slice(f"{y}-09-01", f"{y}-{last:%m-%d}")).sum("time")
    clim = xr.concat([win(y) for y in range(1991, 2021)], "year").mean("year")
    pct = 100 * win(2026) / clim
    lat = np.arange(-1.55, 4.3, 0.02)
    lon = np.arange(29.5, 35.1, 0.02)
    fine = pct.interp(lat=lat, lon=lon, method="linear", kwargs={"fill_value": None})
    LO, LA = np.meshgrid(lon, lat)
    ug = uganda()
    shapely.prepare(ug)
    inside = shapely.contains_xy(ug, LO, LA)
    lakes = gpd.read_file(Path.home() / "uganda-concrete-climate" / "data" / "raw" / "naturalearth" / "ne_10m_lakes.geojson").cx[29.3:35.3, -1.8:4.6]
    cm = LinearSegmentedColormap.from_list("dry", ["#6e1f0b", RED, "#f0a07f", "#f6e3d6", "#cfe3ec", BLU])
    u = zone_mean(pr.where(zones() >= 0)).sel(zone="Uganda").to_series()
    tot = lambda y: u.loc[f"{y}-09-01":f"{y}-{last:%m-%d}"].sum()
    nat = 100 * tot(2026) / np.mean([tot(y) for y in range(1991, 2021)])

    def make(w_in, h_in, fname, big):
        fig = plt.figure(figsize=(w_in, h_in), facecolor=BG)
        mx = fig.add_axes([0.50, 0.16, 0.48, 0.78], facecolor=BG)
        im = mx.pcolormesh(lon, lat, np.where(inside, fine, np.nan), cmap=cm, vmin=20, vmax=140, shading="auto")
        lakes.plot(ax=mx, color="#cfe3ec", zorder=2)
        gpd.GeoSeries([ug]).boundary.plot(ax=mx, color=INK, lw=1.0, zorder=3)
        mx.set_xlim(29.4, 35.2)
        mx.set_ylim(-1.7, 4.45)
        mx.set_aspect("equal")
        mx.axis("off")
        cax = fig.add_axes([0.62, 0.075, 0.30, 0.022])
        cb = fig.colorbar(im, cax=cax, orientation="horizontal", ticks=[20, 50, 80, 110, 140])
        cb.ax.tick_params(labelsize=big * 0.42, colors=MUTE, length=0)
        cb.outline.set_visible(False)
        cb.set_label(f"rain, 1 Sep–{last:%-d %b} 2026, % of normal", fontsize=big * 0.45, color=MUTE)
        fig.text(0.06, 0.86, "Where is the\nEl Niño rain?", fontsize=big * 1.55, fontweight="bold", color=INK, va="top",
                 linespacing=1.0)
        fig.text(0.06, 0.50, f"{nat:.0f}%", fontsize=big * 2.3, fontweight="bold", color=RED, va="center")
        fig.text(0.06, 0.37, f"of normal rain since 1 September.\nIn 1997, the year of the El Niño\nfloods, it looked just the same.",
                 fontsize=big * 0.62, color=INK, va="top", linespacing=1.3)
        fig.text(0.06, 0.10, "Uganda's forecast, seasons and floods:\n45 years of data", fontsize=big * 0.42, color=MUTE, va="bottom")
        fig.text(0.06, 0.045, CREDIT, fontsize=big * 0.42, color=INK, fontweight="bold", alpha=0.8)
        with matplotlib.rc_context({"savefig.bbox": "standard"}):
            fig.savefig(OUT / fname, dpi=100, facecolor=BG)
        from PIL import Image
        im_ = Image.open(OUT / fname)
        target = (round(w_in * 100), round(h_in * 100))
        if im_.size != target:
            im_.resize(target, Image.LANCZOS).save(OUT / fname)
        plt.close(fig)
    make(14.56, 10.48, "cover_substack_1456x1048.png", 40)
    make(12.0, 6.30, "cover_social_1200x630.png", 30)
    print("national % of normal", round(nat))


def g12_erratic_months():
    """fig06 for social: Uganda monthly rain anomaly, years across, months down; extreme-month counts per epoch."""
    from common import CMAP_RAIN
    pr = chirps()[0]
    u = zone_mean(pr.where(zones() >= 0)).sel(zone="Uganda").to_series()
    m = u.resample("MS").sum()[:"2025-12"]
    clim = m["1991":"2020"].groupby(m["1991":"2020"].index.month).mean()
    an = 100 * (m / clim.reindex(m.index.month).values - 1)
    t = pd.DataFrame({"y": an.index.year, "m": an.index.month, "v": an.values}).pivot(index="y", columns="m", values="v")
    eps = [(1981, 1995), (1996, 2010), (2011, 2025)]
    n = [int((t.loc[a:b].abs() > 40).sum().sum()) for a, b in eps]
    fig = plt.figure(figsize=(W, H))
    fig.text(0.05, 0.93, "Uganda's rain has become more erratic", fontsize=24, fontweight="bold", color=INK)
    fig.text(0.05, 0.865, "Each square is one month: rain above (blue) or below (orange) the 1991–2020 normal",
             fontsize=15, color=MUTE)
    ax = fig.add_axes([0.07, 0.33, 0.80, 0.48])
    im = ax.pcolormesh(np.arange(1980.5, 2026), np.arange(0.5, 13), t.values.T, cmap=CMAP_RAIN, vmin=-80, vmax=80,
                       shading="flat", edgecolors=BG, linewidth=0.6)
    ax.set_ylim(12.5, 0.5)
    ax.set_yticks(range(1, 13))
    ax.set_yticklabels(list("JFMAMJJASOND"), fontsize=11)
    ax.set_xticks([1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025])
    ax.tick_params(length=0, labelsize=12)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    cax = fig.add_axes([0.895, 0.36, 0.014, 0.42])
    cb = fig.colorbar(im, cax=cax, ticks=[-80, -40, 0, 40, 80], extend="both")
    cb.ax.set_yticklabels(["−80%", "−40%", "0", "+40%", "+80%"], fontsize=11)
    cb.ax.tick_params(length=0, colors=MUTE)
    cb.outline.set_visible(False)
    # epoch brackets and counts under the heat map
    tr = ax.get_xaxis_transform()
    for (a, b), k, c in zip(eps, n, (MUTE, "#b0613e", RED)):
        ax.plot([a - 0.4, b + 0.4], [-0.16, -0.16], color=c, lw=3, transform=tr, clip_on=False, solid_capstyle="butt")
        ax.text((a + b) / 2, -0.24, f"{a}–{b}", ha="center", va="top", fontsize=13, color=MUTE, transform=tr)
        ax.text((a + b) / 2, -0.36, f"{k} extreme months", ha="center", va="top", fontsize=18, fontweight="bold",
                color=c, transform=tr)
    fig.text(0.05, 0.075, "Extreme month = rain more than 40% above or below normal.", fontsize=11.5, color=MUTE)
    fig.text(0.05, 0.03, "Data: CHIRPS v2.0, Uganda average, 1981–2025.", fontsize=10, color=MUTE)
    credit(fig)
    fig.savefig(OUT / "g12_erratic_months.png", dpi=150)
    plt.close(fig)
    print("extreme months per epoch", n)


def _season_lines():
    from seasons import DOY0
    ds = xr.open_dataset(PROC / "seasons.nc")
    out = {}
    for s in ("S1", "S2"):
        on = zone_mean(ds[f"{s}_onset"].where(ds[f"{s}_onset"].count("year") > 35)).sel(zone="Uganda").to_series()
        ce = zone_mean(ds[f"{s}_cessation"].where(ds[f"{s}_cessation"].count("year") > 35)).sel(zone="Uganda").to_series()
        out[s] = pd.DataFrame({"on": on, "ce": ce})
    return out, DOY0


def _season_figure():
    """Uganda first and second rains, one line per year; returns fig and a draw(upto_year) function."""
    data, DOY0 = _season_lines()
    eps = [(1981, 1995), (1996, 2010), (2011, 2025)]
    cols = {1981: "#9aa5a0", 1996: "#5a8fb0", 2011: RED}
    fig = plt.figure(figsize=(W, H))
    fig.text(0.05, 0.93, "Uganda's second rains now last nearly two weeks longer", fontsize=24, fontweight="bold", color=INK)
    fig.text(0.05, 0.865, "Each line is one rainy season, from first to last rains. Boxes: 15-year averages.",
             fontsize=15, color=MUTE)
    fig.text(0.05, 0.03, "Data: CHIRPS v2.0, Uganda average; onset and end by the anomalous-accumulation method.",
             fontsize=10, color=MUTE)
    credit(fig)
    axs = [fig.add_axes([0.10, 0.17, 0.36, 0.61]), fig.add_axes([0.57, 0.17, 0.36, 0.61])]
    lims = {"S1": ("2001-02-01", "2001-08-01"), "S2": ("2001-08-01", "2002-02-01")}
    names = {"S1": "First rains (Mar–May)", "S2": "Second rains (Sep–Nov)"}
    doy = lambda d: (pd.Timestamp(d) - DOY0).days + 1
    lines, boxes = {}, {}
    for ax, s in zip(axs, ("S1", "S2")):
        ax.set_xlim(doy(lims[s][0]), doy(lims[s][1]))
        ax.set_ylim(2026, 1980)
        ticks = pd.date_range(lims[s][0], lims[s][1], freq="MS")
        ax.set_xticks([doy(d) for d in ticks])
        ax.set_xticklabels([d.strftime("%b") for d in ticks], fontsize=12)
        ax.set_yticks([1985, 1995, 2005, 2015, 2025])
        ax.tick_params(labelsize=12, length=0)
        ax.grid(axis="y", visible=False)
        ax.set_title(names[s], fontsize=17, pad=10)
        df = data[s]
        for y, r in df.iterrows():
            c = cols[max(k for k in cols if k <= y)]
            ln, = ax.plot([r.on, r.ce], [y, y], color=c, lw=3.2, solid_capstyle="round", visible=False)
            lines[(s, y)] = ln
        for a, b in eps:
            e = df.loc[a:b]
            o, c_ = e.on.mean(), e.ce.mean()
            col = cols[a]
            rect = plt.Rectangle((o, a - 0.6), c_ - o, b - a + 1.2, fill=False, ec=col, lw=2.2, ls="-", visible=False,
                                 zorder=4)
            ax.add_patch(rect)
            txt = ax.text(doy("2001-06-24" if s == "S1" else "2002-01-04"), (a + b) / 2, f"{c_ - o:.0f} days",
                          va="center", fontsize=15, fontweight="bold", color=col, visible=False)
            boxes[(s, b)] = (rect, txt)

    def draw(upto):
        for (s, y), ln in lines.items():
            ln.set_visible(y <= upto)
        for (s, b), (rect, txt) in boxes.items():
            rect.set_visible(b <= upto)
            txt.set_visible(b <= upto)
        return list(lines.values())
    return fig, draw, data


def g13_season_lengths():
    fig, draw, data = _season_figure()
    draw(2025)
    fig.savefig(OUT / "g13_second_rains_longer.png", dpi=150)
    plt.close(fig)
    for s, df in data.items():
        a, b = df.loc[1981:1995], df.loc[2011:2025]
        print(s, "length", round((a.ce - a.on).mean(), 1), "->", round((b.ce - b.on).mean(), 1),
              "onset", round(a.on.mean(), 1), "->", round(b.on.mean(), 1), "end", round(a.ce.mean(), 1), "->", round(b.ce.mean(), 1))


def a5_seasons():
    fig, draw, _ = _season_figure()
    yr = fig.text(0.95, 0.858, "", fontsize=26, fontweight="bold", color=RED, ha="right")
    seq = [y for y in range(1981, 2026) for _ in range(2)] + [2025] * 20

    def step(i):
        draw(seq[i])
        yr.set_text(str(seq[i]))
        return []
    FuncAnimation(fig, step, frames=len(seq), blit=False).save(OUT / "a5_seasons.gif", writer=PillowWriter(fps=10), dpi=80)
    plt.close(fig)


def g14_east_africa():
    """fig21 for social: East Africa long-rains vs short-rains trend maps."""
    from matplotlib.colors import BoundaryNorm
    from common import BASE, CMAP_RAIN, trend_da
    from regional_global import outline
    from common import lakes
    ch = xr.open_dataset(PROC / "chirps_africa_monthly.nc")["precip"].load().sel(time=slice("1981", "2025"))
    eab = ch.sel(lat=slice(-12, 16), lon=slice(22, 52))
    fig = plt.figure(figsize=(W, H))
    fig.text(0.05, 0.93, "East Africa's short rains are getting wetter", fontsize=24, fontweight="bold", color=INK)
    fig.text(0.05, 0.865, "Rainfall trend 1981–2025, % per decade. Blue = wetter, orange = drier. Uganda outlined.",
             fontsize=15, color=MUTE)
    lev = [-15, -10, -6, -3, -1, 1, 3, 6, 10, 15]
    axs = [fig.add_axes([0.04, 0.17, 0.44, 0.62]), fig.add_axes([0.52, 0.17, 0.44, 0.62])]
    for ax, (name, months) in zip(axs, [("March–May (long rains)", (3, 4, 5)), ("October–December (short rains)", (10, 11, 12))]):
        tot = eab.where(eab.time.dt.month.isin(list(months)), drop=True).groupby("time.year").sum(min_count=3)
        s, _ = trend_da(tot)
        mean = tot.sel(year=slice(*BASE)).mean("year")
        rel = (100 * s / mean).where(mean > 50)
        im = ax.pcolormesh(rel.lon, rel.lat, rel, cmap=CMAP_RAIN, norm=BoundaryNorm(lev, 256, extend="both"),
                           shading="nearest", rasterized=True)
        lakes()[lambda d: d.geometry.area > 0.05].plot(ax=ax, color="#dfe9f3", edgecolor=INK, lw=0.3, zorder=4)
        outline(ax, (22, 52, -12, 16))
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title(name, fontsize=17, pad=8)
    axs[0].annotate("Horn: long rains\ndrying", (44.0, 3.5), xytext=(47.0, -5.0), fontsize=12.5, fontweight="bold",
                    color=RED, ha="center", arrowprops=dict(arrowstyle="-", color=RED, lw=1.2), zorder=7)
    cax = fig.add_axes([0.30, 0.115, 0.40, 0.022])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal", ticks=lev)
    cb.ax.tick_params(labelsize=10.5, length=0, colors=MUTE)
    cb.outline.set_visible(False)
    fig.text(0.05, 0.03, "Data: CHIRPS v2.0 monthly, Sen's slope. Areas with little seasonal rain left blank.",
             fontsize=10, color=MUTE)
    credit(fig)
    fig.savefig(OUT / "g14_east_africa_rains.png", dpi=150)
    plt.close(fig)


def _warming_series():
    from common import BASE, grid_mask
    tas = xr.open_dataset(PROC / "ghcncams_monthly_1deg.nc")["tas"].load().sel(time=slice("1981", "2025"))
    ann = tas.groupby("time.year").mean().where(tas.groupby("time.year").count() >= 10)
    w = lambda d: np.cos(np.deg2rad(d.lat))
    ug = grid_mask(ann.lat.sel(lat=slice(-2, 5)), ann.lon.sel(lon=slice(29, 36)), exclude_lakes=False)
    sub = ann.sel(lat=slice(-2, 5), lon=slice(29, 36)).where(ug)
    u = sub.weighted(w(sub)).mean(("lat", "lon")).to_series()
    g = ann.sel(lat=slice(-60, 75))
    g = g.weighted(w(g)).mean(("lat", "lon")).to_series()
    u, g = u - u.loc[BASE[0]:BASE[1]].mean(), g - g.loc[BASE[0]:BASE[1]].mean()
    tr = pd.read_csv(RES / "regional_global_trends.csv").set_index(["variable", "region"])
    tu = tr.loc[("Temperature (GHCN-CAMS)", "Uganda"), "trend_per_decade"]
    tg = tr.loc[("Temperature (GHCN-CAMS)", "Global land"), "trend_per_decade"]
    return u, g, tu, tg


def g15_warming_faster():
    """fig22 for social: Uganda vs global land temperature anomaly."""
    u, g, tu, tg = _warming_series()
    fig, ax = frame("Uganda is warming faster than the world",
                    "Annual land temperature, °C above or below the 1991–2020 average",
                    "Data: NOAA GHCN-CAMS land temperature, 1981–2025.")
    fig.subplots_adjust(right=0.80)
    ax.axhline(0, color=MUTE, lw=1)
    ax.plot(g.index, g.values, color=MUTE, lw=2.2)
    ax.plot(u.index, u.values, color=RED, lw=3.6)
    ax.text(2026, u.iloc[-1] + 0.05, f"Uganda\n+{tu:.2f} °C/decade", color=RED, fontsize=14, fontweight="bold",
            va="center", clip_on=False)
    ax.text(2026, g.iloc[-1] - 0.25, f"Global land\n+{tg:.2f} °C/decade", color=MUTE, fontsize=14, fontweight="bold",
            va="center", clip_on=False)
    ax.set_xlim(1980, 2025.5)
    ax.set_yticks([-1, -0.5, 0, 0.5, 1, 1.5])
    ax.set_yticklabels(["−1.0", "−0.5", "0", "+0.5", "+1.0", "+1.5"])
    fig.savefig(OUT / "g15_warming_faster.png", dpi=150)
    plt.close(fig)
    print("Uganda", u.iloc[-3:].round(2).to_dict(), "global", g.iloc[-3:].round(2).to_dict())


def a6_warming():
    """g15 as an animation: Uganda vs global land temperature, drawn year by year."""
    u, g, tu, tg = _warming_series()
    fig, ax = frame("Uganda is warming faster than the world",
                    "Annual land temperature, °C above or below the 1991–2020 average",
                    "Data: NOAA GHCN-CAMS land temperature, 1981–2025.")
    fig.subplots_adjust(right=0.80)
    ax.axhline(0, color=MUTE, lw=1)
    ax.set_xlim(1980, 2025.5)
    ax.set_ylim(-1.4, 1.75)
    ax.set_yticks([-1, -0.5, 0, 0.5, 1, 1.5])
    ax.set_yticklabels(["−1.0", "−0.5", "0", "+0.5", "+1.0", "+1.5"])
    lg, = ax.plot([], [], color=MUTE, lw=2.2)
    lu, = ax.plot([], [], color=RED, lw=3.6)
    du, = ax.plot([], [], "o", color=RED, ms=9)
    dg, = ax.plot([], [], "o", color=MUTE, ms=7)
    tu_ = ax.text(0, 0, "", color=RED, fontsize=14, fontweight="bold", va="center", clip_on=False, zorder=6,
                  bbox=dict(facecolor=BG, edgecolor="none", pad=1.5))
    tg_ = ax.text(0, 0, "", color=MUTE, fontsize=14, fontweight="bold", va="center", clip_on=False, zorder=6,
                  bbox=dict(facecolor=BG, edgecolor="none", pad=1.5))
    yr = fig.text(0.95, 0.858, "", fontsize=26, fontweight="bold", color=RED, ha="right")
    years = list(u.index)
    seq = [y for y in years for _ in range(2)] + [years[-1]] * 24

    def step(i):
        y = seq[i]
        uu, gg = u.loc[:y], g.loc[:y]
        lu.set_data(uu.index, uu.values)
        lg.set_data(gg.index, gg.values)
        du.set_data([y], [uu.iloc[-1]])
        dg.set_data([y], [gg.iloc[-1]])
        yr.set_text(str(y))
        done = i >= len(years) * 2
        if done:  # final hold: right-margin labels with the trends
            tu_.set_position((2026, u.iloc[-1] + 0.05))
            tu_.set_text(f"Uganda\n+{tu:.2f} °C/decade")
            tg_.set_position((2026, g.iloc[-1] - 0.25))
            tg_.set_text(f"Global land\n+{tg:.2f} °C/decade")
        else:  # labels ride with the line ends, kept apart vertically
            yu, yg = uu.iloc[-1], gg.iloc[-1]
            if abs(yu - yg) < 0.22:
                mid = (yu + yg) / 2
                yu, yg = (mid + 0.11, mid - 0.11) if u.loc[y] >= g.loc[y] else (mid - 0.11, mid + 0.11)
            tu_.set_position((y + 0.8, yu))
            fmt = lambda v: "0.0" if round(v, 1) == 0 else f"{v:+.1f}"
            tu_.set_text(f"Uganda {fmt(u.loc[y])} °C")
            tg_.set_position((y + 0.8, yg))
            tg_.set_text(f"Global land {fmt(g.loc[y])} °C")
        return lu, lg, du, dg, tu_, tg_, yr
    FuncAnimation(fig, step, frames=len(seq), blit=False).save(OUT / "a6_warming.gif", writer=PillowWriter(fps=10), dpi=80)
    plt.close(fig)


# ---------------------------------------------------------------- Kampala drainage study: social cards
KDO = OUT / "kampala_drainage"


def kd_cards():
    KDO.mkdir(parents=True, exist_ok=True)
    # 1: floods on ordinary rain
    ev = pd.read_csv(RES / "kd_flood_event_rain.csv", parse_dates=["date"]).dropna(subset=["chirps_1d"]).sort_values("chirps_1d_pctile_wetdays")
    fig, ax = frame("Kampala floods on ordinary rain", "Rain on reported flood days, as a percentile of all wet days (1991–2020)",
                    "Data: CHIRPS v2.0 satellite rain, Greater Kampala average; flood dates from Daily Monitor, New Vision, NTV, ReliefWeb.")
    y = np.arange(len(ev))
    cols = [RED if v >= 90 else "#e9a23b" if v >= 50 else BLU for v in ev.chirps_1d_pctile_wetdays]
    ax.barh(y, ev.chirps_1d_pctile_wetdays, color=cols, height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels([d.strftime("%-d %b %Y") for d in ev.date], fontsize=13)
    for yy, v, mm in zip(y, ev.chirps_1d_pctile_wetdays, ev.chirps_1d):
        ax.text(max(v + 1.5, 91.5) if v < 90 and v > 84 else v + 1.5, yy, f"{v:.0f}th  ({mm:.0f} mm)", va="center", fontsize=12)
    ax.axvline(90, color=MUTE, ls="--", lw=1.2)
    ax.text(90.8, len(ev) - 0.45, "a truly heavy day", fontsize=11, color=MUTE, va="bottom")
    ax.set_xlim(0, 118)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.grid(axis="y", visible=False)
    fig.savefig(KDO / "x1_floods_ordinary_rain.png", dpi=150)
    plt.close(fig)
    # 2: next hotspots (hold-out)
    ho = pd.read_csv(RES / "kd_test_holdout.csv").iloc[0]
    fig, ax = frame("We can see the next flood hotspots coming", "Valley floor built over 2000–2020, by a risk score built only from 1975–2000 change",
                    "Data: JRC GHSL built-up, Copernicus DEM, OpenStreetMap channels. Analysis of 6,902 channel stretches.")
    vals = [1.6, 1.8, 2.9, 3.8, 6.5]
    ax.bar(range(5), vals, color=["#fde0c5", "#facba6", "#f8a07e", "#ce6693", "#a63a8a"], width=0.62)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.15, f"{v:.1f}", ha="center", fontsize=16, fontweight="bold")
    ax.set_xticks(range(5))
    ax.set_xticklabels(["lowest\nrisk score", "", "", "", "highest\nrisk score"], fontsize=13)
    ax.set_ylabel("percentage points of valley floor built over")
    ax.set_ylim(0, 8)
    ax.text(0.02, 0.92, f"4x more encroachment where the early-warning score was highest\n(prediction accuracy AUC {ho.auc_early_score:.2f})",
            transform=ax.transAxes, fontsize=13.5, va="top")
    ax.grid(axis="x", visible=False)
    fig.savefig(KDO / "x2_next_hotspots.png", dpi=150)
    plt.close(fig)
    # 3: people in the water's path
    pop = pd.read_csv(RES / "kd_population_low_ground.csv")
    fig, ax = frame("More people now live where Kampala's water goes",
                    "Residents on low ground (< 2 m above the drain) within 150 m of a channel",
                    "Data: JRC GHS-POP (2025, 2030 projected), Copernicus DEM, OpenStreetMap channels.")
    ax.fill_between(pop.epoch, pop.pop_low_ground / 1000, color="#f4c7d6")
    ax.plot(pop.epoch, pop.pop_low_ground / 1000, color="#c2185b", lw=3.5)
    for e in (1975, 1990, 2020, 2030):
        v = float(pop.set_index("epoch").pop_low_ground[e]) / 1000
        ax.scatter([e], [v], color="#c2185b", s=70, zorder=5)
        ax.annotate(f"{v:,.0f}k", (e, v), xytext=(0, 12), textcoords="offset points", ha="center", fontsize=15, fontweight="bold")
    ax.axvspan(2020, 2031, color=GRIDC, alpha=0.6, lw=0)
    ax.text(2025.5, 15, "projected", ha="center", fontsize=11, color=MUTE)
    ax.set_xlim(1972, 2033)
    ax.set_ylim(0, 290)
    ax.set_ylabel("thousand people")
    fig.savefig(KDO / "x3_people_low_ground.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__" and "kd_cards" in __import__("sys").argv:
    kd_cards()
