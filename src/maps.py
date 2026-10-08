"""Satellite-image base maps and close-ups (Esri World Imagery tiles) with analysis results overlaid.

fig33 Uganda overview (zones on imagery) + satellite-rainfall (CHIRPS) climatology of East Africa
fig34 Greater Kampala, fig35 Mt Elgon - Mbale, fig36 Karamoja, fig37 South-west (Rwizi - Mbarara): each with two
result layers drawn as semi-transparent 0.25 deg cells labelled with their values, plus county (ADM2) boundaries.
"""
import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap

from common import (BASE, BLUE, CAT, CMAP_RAIN, CMAP_SEQ, INK, ORANGE, PROC, TOWNS, UG_EXTENT, Y0, Y1, chirps,
                    countries, lakes, save, season_total, trend_da, uganda, zone_names, zones)

IMG = ctx.providers.Esri.WorldImagery
WHITE = "#ffffff"


def base(ax, ext, zoom):
    ax.set_xlim(ext[0], ext[1])
    ax.set_ylim(ext[2], ext[3])
    ctx.add_basemap(ax, crs="EPSG:4326", source=IMG, zoom=zoom, attribution_size=5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)


def adm2(ax, ext):
    d = gpd.read_file(PROC / "uganda_adm2.geojson").cx[ext[0]:ext[1], ext[2]:ext[3]]
    d.boundary.plot(ax=ax, color=WHITE, lw=0.5, alpha=0.8, zorder=6)
    for _, r in d.iterrows():
        p = r.geometry.representative_point()
        if ext[0] < p.x < ext[1] and ext[2] < p.y < ext[3]:
            ax.text(p.x, p.y, r.shapeName, fontsize=5.5, color=WHITE, ha="center", va="center", zorder=7, alpha=0.9)
    gpd.GeoSeries([uganda()]).boundary.plot(ax=ax, color="#ffd400", lw=1.2, zorder=6)


def cells(ax, da, cmap, norm, fmt, alpha=0.55, label=True):
    im = ax.pcolormesh(da.lon, da.lat, da, cmap=cmap, norm=norm, shading="nearest", alpha=alpha, edgecolors=WHITE,
                       lw=0.3, zorder=4)
    if label:
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        for la in da.lat.values:
            for lo in da.lon.values:
                v = float(da.sel(lat=la, lon=lo))
                if np.isfinite(v) and x0 < lo < x1 and y0 < la < y1:
                    ax.text(lo, la, fmt.format(v), fontsize=6.5, ha="center", va="center", color=INK, zorder=8,
                            bbox=dict(fc=WHITE, ec="none", alpha=0.6, pad=0.6))
    return im


def towns(ax, ext):
    for t, (la, lo) in TOWNS.items():
        if ext[0] < lo < ext[1] and ext[2] < la < ext[3]:
            ax.plot(lo, la, "o", ms=4, color="#ffd400", mec=INK, mew=0.6, zorder=9)
            ax.annotate(t, (lo, la), xytext=(4, 4), textcoords="offset points", fontsize=8, color=WHITE, zorder=9,
                        fontweight="bold")


def layers():
    pr = chirps()[0].sel(time=slice(f"{Y0}", f"{Y1}"))
    z = zones()
    out = {}
    for name, months in (("MAM", (3, 4, 5)), ("SON", (9, 10, 11)), ("ANN", tuple(range(1, 13)))):
        tot = season_total(pr, months).sel(year=slice(Y0, Y1))
        s, p = trend_da(tot)
        out[name] = (100 * s / tot.sel(year=slice(*BASE)).mean("year")).where(z >= 0)
    rl = xr.open_dataset(PROC / "return_levels.nc")
    import pandas as pd
    cal = pd.read_csv(PROC.parent.parent / "results" / "drainage_gauge_calibration.csv")
    cf10 = cal.ratio_10yr.median()
    out["R10"] = (rl.rl_1981_2025.sel(T=10) * cf10).where(z >= 0)
    out["R10chg"] = (100 * (rl.rl_2004_2025.sel(T=10) / rl.rl_1981_2003.sel(T=10) - 1)).where(z >= 0)
    wb = xr.open_dataset(PROC / "water_balance.nc")
    out["AI"] = wb.AI
    out["dry"] = wb.dry_months
    s = xr.open_dataset(PROC / "seasons.nc")
    out["S1len_tr"], _ = trend_da(s.S1_length.where(s.S1_length.count("year") > 35))
    return out


def overview(L):
    z = zones()
    fig = plt.figure(figsize=(14, 6.6))
    ax = fig.add_axes([0.0, 0.03, 0.5, 0.92])
    base(ax, UG_EXTENT, 8)
    zz = z.where(z >= 0)
    ax.pcolormesh(z.lon, z.lat, zz, cmap=ListedColormap(CAT[:6]), vmin=-0.5, vmax=5.5, shading="nearest", alpha=0.35, zorder=3)
    ax.contour(z.lon, z.lat, zz, levels=np.arange(0.5, 5.6, 1), colors=WHITE, linewidths=0.8, zorder=4)
    gpd.GeoSeries([uganda()]).boundary.plot(ax=ax, color="#ffd400", lw=1.3, zorder=6)
    towns(ax, UG_EXTENT)
    for k, n in zone_names().items():
        la, lo = float(z.lat.where(z == k).mean()), float(z.lon.where(z == k).mean())
        ax.text(lo, la - 0.25, n.split(" (")[0], fontsize=7.5, color=WHITE, ha="center", fontweight="bold", zorder=9,
                bbox=dict(fc=CAT[k], ec="none", alpha=0.8, pad=1.5))
    ax.set_title("a  Uganda from space (Esri World Imagery) with rainfall-regime zones")
    ax2 = fig.add_axes([0.53, 0.08, 0.45, 0.85])
    af = xr.open_dataset(PROC / "chirps_africa_monthly.nc")["precip"].sel(time=slice(f"{BASE[0]}", f"{BASE[1]}"),
                                                                          lat=slice(-12, 16), lon=slice(22, 52))
    ann = af.groupby("time.year").sum(min_count=12).mean("year")
    cm = LinearSegmentedColormap.from_list("r", ["#fdf3ec", ORANGE[1]] + BLUE)
    im = ax2.pcolormesh(ann.lon, ann.lat, ann, cmap=cm, norm=BoundaryNorm([0, 200, 400, 600, 800, 1000, 1200, 1400, 1700, 2000, 3000], 256),
                        shading="nearest", rasterized=True)
    countries().boundary.plot(ax=ax2, color=INK, lw=0.4)
    lakes()[lambda d: d.geometry.area > 0.05].plot(ax=ax2, color="#dfe9f3", edgecolor=INK, lw=0.3)
    gpd.GeoSeries([uganda()]).boundary.plot(ax=ax2, color=INK, lw=1.4)
    ax2.set_xlim(22, 52)
    ax2.set_ylim(-12, 16)
    ax2.set_aspect("equal")
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.grid(False)
    fig.colorbar(im, ax=ax2, shrink=0.75, label="mm/yr")
    ax2.set_title("b  Satellite-gauge rainfall (CHIRPS), mean annual 1991-2020")
    save(fig, "fig33_satellite_overview.png")


def closeup(fname, title, ext, zoom, panels):
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.6 * (ext[3] - ext[2]) / (ext[1] - ext[0]) + 0.9))
    for ax, (key, sub, cmap, norm, fmt, cblab) in zip(axs, panels):
        base(ax, ext, zoom)
        im = cells(ax, L[key], cmap, norm, fmt)
        adm2(ax, ext)
        towns(ax, ext)
        ax.set_title(sub, fontsize=9.5)
        fig.colorbar(im, ax=ax, shrink=0.7, label=cblab)
    fig.suptitle(title, x=0.01, ha="left", fontweight="bold")
    save(fig, fname)


if __name__ == "__main__":
    L = layers()
    overview(L)
    pct = BoundaryNorm([-15, -10, -6, -3, -1, 1, 3, 6, 10, 15], 256, extend="both")
    chg = BoundaryNorm([-30, -20, -10, -5, 5, 10, 20, 30], 256, extend="both")
    r10 = BoundaryNorm(np.arange(60, 131, 10), 256, extend="both")
    cm10 = LinearSegmentedColormap.from_list("b", ["#f4f8fd"] + BLUE)
    aicm = LinearSegmentedColormap.from_list("ai", [ORANGE[5], ORANGE[3], ORANGE[1], BLUE[1], BLUE[3], BLUE[5]])
    ain = BoundaryNorm([0.2, 0.3, 0.4, 0.5, 0.65, 0.8, 1.0, 1.2], 256, extend="both")
    drn = BoundaryNorm(np.arange(-0.5, 9, 1), 256)
    dcm = LinearSegmentedColormap.from_list("d", ["#f4f8fd"] + ORANGE)
    closeup("fig34_closeup_kampala.png", "Greater Kampala: design storm and second-season trend",
            (32.25, 33.0, -0.05, 0.62), 11,
            [("R10", "a  10-year 1-day rainfall, gauge-calibrated (mm)", cm10, r10, "{:.0f}", "mm"),
             ("R10chg", "b  Change in 10-yr storm, 2004-25 vs 1981-2003 (%)", CMAP_RAIN, chg, "{:+.0f}", "%")])
    closeup("fig35_closeup_elgon.png", "Mt Elgon - Mbale - Tororo: wetter second rains, landslide and flash-flood country",
            (33.75, 34.75, 0.45, 1.6), 10,
            [("SON", "a  SON rainfall trend 1981-2025 (% per decade)", CMAP_RAIN, pct, "{:+.0f}", "%/decade"),
             ("R10", "b  10-year 1-day rainfall, gauge-calibrated (mm)", cm10, r10, "{:.0f}", "mm")])
    closeup("fig36_closeup_karamoja.png", "Karamoja: Uganda's water-scarce frontier",
            (33.5, 35.05, 1.5, 4.3), 9,
            [("AI", "a  Aridity index P/ET0 (<0.5 semi-arid)", aicm, ain, "{:.2f}", "P/ET0"),
             ("dry", "b  Dry months per year (P < 0.5 ET0)", dcm, drn, "{:.0f}", "months")])
    closeup("fig37_closeup_southwest.png", "South-west (Rwizi catchment, Mbarara - Kabale): first-rains trend and dry months",
            (29.55, 31.1, -1.5, -0.1), 9,
            [("MAM", "a  MAM rainfall trend 1981-2025 (% per decade)", CMAP_RAIN, pct, "{:+.0f}", "%/decade"),
             ("dry", "b  Dry months per year (P < 0.5 ET0)", dcm, drn, "{:.0f}", "months")])
