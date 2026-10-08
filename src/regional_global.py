"""Uganda in regional and global context, 1981-2025.

Temperature: GHCN-CAMS land 2 m temperature (1 deg) - trends for Uganda, East Africa (12S-12N, 28-42E land),
Africa land and global land (60S-75N). Rainfall: CHIRPS monthly (Africa, 0.25 deg) for East Africa seasonal trend
maps; GPCP v2.3 (2.5 deg) for global context.

Figures fig20 (global/Africa temperature trend maps), fig21 (East Africa MAM/OND rainfall trend maps),
        fig22 (series: Uganda vs East Africa vs Africa vs world). Table results/regional_global_trends.csv
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import BoundaryNorm

from common import (BASE, CAT, CMAP_RAIN, CMAP_TEMP, INK, MUTED, PROC, RES, Y0, Y1, countries, grid_mask, lakes,
                    save, series_trend, stipple, trend_da, uganda)
import geopandas as gpd

EA_BOX = dict(lat=slice(-12, 12), lon=slice(28, 42))


def wmean(da, mask=None):
    w = np.cos(np.deg2rad(da.lat))
    if mask is not None:
        da = da.where(mask)
    return da.weighted(w).mean(("lat", "lon"))


def africa_geom():
    c = countries()
    return c[c.CONTINENT == "Africa"].geometry.unary_union


def outline(ax, extent, lw=0.4):
    countries().boundary.plot(ax=ax, color=INK, lw=lw, zorder=5)
    gpd.GeoSeries([uganda()]).boundary.plot(ax=ax, color=INK, lw=1.4, zorder=6)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_aspect("equal")
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])


def main():
    rows = []
    tas = xr.open_dataset(PROC / "ghcncams_monthly_1deg.nc")["tas"].load()
    ann = tas.sel(time=slice(f"{Y0}", f"{Y1}")).groupby("time.year").mean()
    # require complete coverage
    ann = ann.where(tas.sel(time=slice(f"{Y0}", f"{Y1}")).groupby("time.year").count() >= 10)
    slope, p = trend_da(ann.where(ann.count("year") > 40))

    fig = plt.figure(figsize=(14, 5.4))
    ax = fig.add_axes([0.0, 0.08, 0.6, 0.85])
    lev = np.arange(-0.6, 0.61, 0.1)
    im = ax.pcolormesh(slope.lon, slope.lat, slope, cmap=CMAP_TEMP, norm=BoundaryNorm(lev, 256, extend="both"),
                       shading="nearest")
    outline(ax, (-180, 180, -60, 80), lw=0.2)
    ax.set_title("a  Land temperature trend 1981-2025 (GHCN-CAMS), °C per decade")
    ax2 = fig.add_axes([0.6, 0.08, 0.32, 0.85])
    sub = slope.sel(lat=slice(-36, 38), lon=slice(-20, 53))
    ax2.pcolormesh(sub.lon, sub.lat, sub, cmap=CMAP_TEMP, norm=BoundaryNorm(lev, 256, extend="both"), shading="nearest")
    stipple(ax2, p.sel(lat=slice(-36, 38), lon=slice(-20, 53)).where(sub.notnull()), sub.lon, sub.lat, s=1, step=2)
    outline(ax2, (-20, 53, -36, 38))
    ax2.set_title("b  Africa (dots: p<0.05)")
    fig.colorbar(im, ax=[ax, ax2], orientation="horizontal", fraction=0.04, pad=0.03, aspect=60, label="°C per decade")
    save(fig, "fig20_global_temperature_trends.png")

    # region series
    ug = grid_mask(ann.lat.sel(lat=slice(-2, 5)), ann.lon.sel(lon=slice(29, 36)), exclude_lakes=False)
    sub = ann.sel(lat=slice(-36, 38), lon=slice(-20, 53))
    af = grid_mask(sub.lat, sub.lon, geom=africa_geom(), exclude_lakes=False)
    ea = af.sel(**EA_BOX)
    series = {
        "Uganda": wmean(ann.sel(lat=slice(-2, 5), lon=slice(29, 36)), ug),
        "East Africa": wmean(sub.sel(**EA_BOX), ea),
        "Africa": wmean(sub, af),
        "Global land": wmean(ann.sel(lat=slice(-60, 75))),
    }
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.2))
    for i, (n, y) in enumerate(series.items()):
        a = y - y.sel(year=slice(*BASE)).mean()
        axs[0].plot(a.year, a, color=CAT[i], lw=2 if n == "Uganda" else 1.4, label=n)
        s, pp, _ = series_trend(y.values)
        rows.append(dict(variable="Temperature (GHCN-CAMS)", region=n, trend_per_decade=s, units="°C", p_value=pp,
                         change_1981_95_to_2011_25=float(y.sel(year=slice(2011, 2025)).mean() - y.sel(year=slice(1981, 1995)).mean())))
    axs[0].axhline(0, color=MUTED, lw=0.8)
    axs[0].set_ylabel("°C anomaly vs 1991-2020")
    axs[0].set_title("a  Annual land temperature")
    axs[0].legend(fontsize=8)

    # rainfall: CHIRPS Africa for Uganda / East Africa / Africa, GPCP for global land
    ch = xr.open_dataset(PROC / "chirps_africa_monthly.nc")["precip"].load()
    ch = ch.sel(time=slice(f"{Y0}", f"{Y1}"))
    chs = ch.coarsen(lat=4, lon=4, boundary="trim").mean()  # 1 deg for masking speed
    afm = grid_mask(chs.lat, chs.lon, geom=africa_geom(), exclude_lakes=True)
    ugm = grid_mask(chs.lat.sel(lat=slice(-2, 5)), chs.lon.sel(lon=slice(29, 36)), exclude_lakes=True)
    annp = chs.groupby("time.year").sum(min_count=12)
    gp = xr.open_dataset(PROC / "gpcp_monthly.nc")["precip"].load().sel(time=slice(f"{Y0}", f"{Y1}"))
    gp = (gp * gp.time.dt.days_in_month).groupby("time.year").sum()
    land = grid_mask(gp.lat, gp.lon, geom=countries().geometry.unary_union, exclude_lakes=False)
    rseries = {
        "Uganda": wmean(annp.sel(lat=slice(-2, 5), lon=slice(29, 36)), ugm),
        "East Africa": wmean(annp.sel(**EA_BOX), afm.sel(**EA_BOX)),
        "Africa": wmean(annp, afm),
        "Global land (GPCP)": wmean(gp.sel(lat=slice(-60, 75)), land.sel(lat=slice(-60, 75))),
    }
    for i, (n, y) in enumerate(rseries.items()):
        a = 100 * (y / y.sel(year=slice(*BASE)).mean() - 1)
        axs[1].plot(a.year, a.rolling(year=5, center=True).mean(), color=CAT[i], lw=2 if n == "Uganda" else 1.4, label=n)
        s, pp, _ = series_trend(y.values)
        rows.append(dict(variable="Annual rainfall", region=n, trend_per_decade=s, units="mm",
                         pct_per_decade=100 * s / float(y.sel(year=slice(*BASE)).mean()), p_value=pp,
                         change_1981_95_to_2011_25=float(y.sel(year=slice(2011, 2025)).mean() - y.sel(year=slice(1981, 1995)).mean())))
    axs[1].axhline(0, color=MUTED, lw=0.8)
    axs[1].set_ylabel("% anomaly vs 1991-2020 (5-yr running mean)")
    axs[1].set_title("b  Annual rainfall")
    axs[1].legend(fontsize=8)
    save(fig, "fig22_regional_global_series.png")

    # East Africa seasonal rainfall trend maps (CHIRPS 0.25)
    eab = ch.sel(lat=slice(-12, 16), lon=slice(22, 52))
    fig, axs = plt.subplots(1, 3, figsize=(14, 5.2))
    lev = [-15, -10, -6, -3, -1, 1, 3, 6, 10, 15]
    for ax, (name, months) in zip(axs, [("Annual", range(1, 13)), ("MAM long rains", (3, 4, 5)),
                                         ("OND short rains", (10, 11, 12))]):
        tot = eab.where(eab.time.dt.month.isin(list(months)), drop=True).groupby("time.year").sum(min_count=len(list(months)))
        s, pp = trend_da(tot)
        rel = 100 * s / tot.sel(year=slice(*BASE)).mean("year")
        rel = rel.where(tot.sel(year=slice(*BASE)).mean("year") > (50 if len(list(months)) < 12 else 200))
        im = ax.pcolormesh(rel.lon, rel.lat, rel, cmap=CMAP_RAIN, norm=BoundaryNorm(lev, 256, extend="both"),
                           shading="nearest", rasterized=True)
        stipple(ax, pp.where(rel.notnull()), rel.lon, rel.lat, s=0.4, step=3)
        lakes()[lambda d: d.geometry.area > 0.05].plot(ax=ax, color="#dfe9f3", edgecolor=INK, lw=0.3, zorder=4)
        outline(ax, (22, 52, -12, 16))
        ax.set_title(f"{name}: trend 1981-2025")
        reg = rel.sel(**EA_BOX)
        rows.append(dict(variable=f"{name} rainfall (CHIRPS)", region="East Africa box mean of % trends",
                         pct_per_decade=float(reg.mean()), units="%"))
    fig.colorbar(im, ax=axs, orientation="horizontal", fraction=0.05, pad=0.04, aspect=60,
                 label="% of 1991-2020 mean per decade (dots: p<0.05; areas with little seasonal rain masked)")
    fig.suptitle("East Africa: the 'East African paradox' - long rains drying in the Horn, short rains wetting",
                 x=0.01, ha="left", fontweight="bold")
    save(fig, "fig21_east_africa_rain_trends.png")
    df = pd.DataFrame(rows)
    df.round(3).to_csv(RES / "regional_global_trends.csv", index=False)
    print(df.round(3).to_string())


if __name__ == "__main__":
    main()
