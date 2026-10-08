"""Rainfall trends 1981-2025 (CHIRPS): totals by season, extremes (ETCCDI-style), shifts in the annual cycle.

Figures: fig02 seasonal trend maps, fig03 zone series, fig04 extremes trend maps, fig05 annual cycle by epoch,
         fig06 year x month anomaly heat map.
Tables:  results/rain_trend_zone.csv, results/rain_extremes_zone.csv, results/rain_annual_cycle_epochs.csv
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import BoundaryNorm

from common import (BASE, BLUE, CAT, CMAP_RAIN, EPOCHS, INK2, MUTED, PROC, RES, UG_EXTENT, Y0, Y1, chirps,
                    draw_borders, save, season_total, series_trend, stipple, trend_da, zone_mean, zone_names,
                    zones)

SEAS = {"Annual": tuple(range(1, 13)), "MAM (first rains)": (3, 4, 5), "JJA": (6, 7, 8),
        "SON (second rains)": (9, 10, 11), "DJF": (12, 1, 2)}


def daily():
    pr = chirps()[0].sel(time=slice(f"{Y0}-01-01", f"{Y1}-12-31"))
    z = zones()
    return pr.where(z >= 0), z


def map_panel(ax, da, p, title, levels, cmap=CMAP_RAIN, label="% per decade"):
    norm = BoundaryNorm(levels, cmap.N, extend="both")
    im = ax.pcolormesh(da.lon, da.lat, da, cmap=cmap, norm=norm, shading="nearest")
    if p is not None:
        stipple(ax, p.where(da.notnull()), da.lon, da.lat, s=1.5)
    draw_borders(ax, UG_EXTENT)
    ax.set_title(title, fontsize=9)
    return im


def seasonal(pr, z):
    rows, maps = [], {}
    base_mask = lambda s: s.sel(year=slice(*BASE)).mean("year")
    for name, months in SEAS.items():
        tot = season_total(pr, months).sel(year=slice(Y0 + (1 if 1 in months and 12 in months and len(months) < 12 else 0), Y1))
        tot = tot.where(z >= 0)
        slope, p = trend_da(tot)
        rel = 100 * slope / base_mask(tot)
        maps[name] = (rel, p)
        zm = zone_mean(tot)
        for zn in zm.zone.values:
            y = zm.sel(zone=zn).values
            s, pp, _ = series_trend(y)
            rows.append(dict(season=name, zone=zn, mean_1991_2020=float(zm.sel(zone=zn, year=slice(*BASE)).mean()),
                             sen_mm_per_decade=s, pct_per_decade=100 * s / float(zm.sel(zone=zn, year=slice(*BASE)).mean()),
                             p_value=pp, cv_pct=100 * np.std(y) / np.mean(y),
                             mean_1981_2003=float(zm.sel(zone=zn, year=slice(1981, 2003)).mean()),
                             mean_2004_2025=float(zm.sel(zone=zn, year=slice(2004, 2025)).mean())))
        maps[name + "_zm"] = zm
    df = pd.DataFrame(rows)
    df.round(3).to_csv(RES / "rain_trend_zone.csv", index=False)

    fig, axs = plt.subplots(1, 5, figsize=(13, 3.6))
    levels = [-15, -10, -6, -3, -1, 1, 3, 6, 10, 15]
    for ax, name in zip(axs, SEAS):
        im = map_panel(ax, maps[name][0], maps[name][1], name, levels)
    cb = fig.colorbar(im, ax=axs, orientation="horizontal", fraction=0.05, pad=0.04, aspect=50)
    cb.set_label("Rainfall trend 1981-2025, % of 1991-2020 mean per decade (dots: significant, p<0.05)")
    fig.suptitle("Rainfall trends by season (CHIRPS v2.0)", x=0.01, ha="left", fontweight="bold")
    save(fig, "fig02_rain_trend_maps.png")

    # zone series, MAM and SON, with Sen trend
    zn = [zone_names()[k] for k in sorted(zone_names())] + ["Uganda"]
    fig, axs = plt.subplots(len(zn), 3, figsize=(12, 1.55 * len(zn)), sharex=True)
    for j, name in enumerate(["Annual", "MAM (first rains)", "SON (second rains)"]):
        zm = maps[name + "_zm"]
        for i, n in enumerate(zn):
            ax = axs[i, j]
            y = zm.sel(zone=n)
            yrs = y.year.values
            ax.bar(yrs, y, color=BLUE[2], width=0.8)
            s, p, b = series_trend(y.values)
            ax.plot(yrs, b + s / 10 * (yrs - yrs[0]), color=CAT[1], lw=1.6)
            ax.set_ylim(0, float(y.max()) * 1.15)
            ax.text(0.01, 0.97, f"{n}: {s:+.0f} mm/dec (p={p:.2f})", transform=ax.transAxes, va="top", fontsize=7)
            if j == 0:
                ax.set_ylabel("mm", fontsize=7)
            if i == 0:
                ax.set_title(name)
    save(fig, "fig03_rain_zone_series.png")
    return df


def extremes(pr, z):
    wet = pr >= 1
    base = pr.sel(time=slice(f"{BASE[0]}", f"{BASE[1]}"))
    p95 = base.where(base >= 1).quantile(0.95, "time")
    yr = pr.time.dt.year
    idx = {
        "Rx1day (mm)": pr.groupby(yr).max(),
        "Rx5day (mm)": pr.rolling(time=5).sum().groupby(yr).max(),
        "R20mm (days)": (pr >= 20).groupby(yr).sum(),
        "R95pTOT (mm)": pr.where(pr > p95).groupby(yr).sum(),
        "Wet days >=1mm": wet.groupby(yr).sum(),
        "SDII (mm/wet day)": pr.where(wet).groupby(yr).mean(),
    }
    # longest dry spell (<1 mm) per year, counted within the calendar year
    dry = (~wet).astype("int16").values
    run = np.zeros_like(dry)
    for t in range(dry.shape[0]):
        run[t] = (run[t - 1] + 1) * dry[t] if t else dry[t]
    idx["CDD (days)"] = xr.DataArray(run, dims=pr.dims, coords=pr.coords).groupby(yr).max()
    rows = []
    fig, axs = plt.subplots(1, len(idx), figsize=(15, 3.4))
    for ax, (name, da) in zip(axs, idx.items()):
        da = da.rename(group="year") if "group" in da.dims else da
        da = da.where(z >= 0)
        slope, p = trend_da(da)
        rel = 100 * slope / da.sel(year=slice(*BASE)).mean("year")
        cmap = CMAP_RAIN if not name.startswith("CDD") else CMAP_RAIN.reversed()
        im = map_panel(ax, rel, p, name, [-20, -12, -6, -3, -1, 1, 3, 6, 12, 20], cmap=cmap)
        zm = zone_mean(da)
        for n in zm.zone.values:
            s, pp, _ = series_trend(zm.sel(zone=n).values)
            m = float(zm.sel(zone=n, year=slice(*BASE)).mean())
            rows.append(dict(index=name, zone=n, mean_1991_2020=m, sen_per_decade=s, pct_per_decade=100 * s / m,
                             p_value=pp))
        if name.startswith("Rx1day"):
            da.to_netcdf(PROC / "rx1day_annual.nc")
    cb = fig.colorbar(im, ax=axs, orientation="horizontal", fraction=0.05, pad=0.04, aspect=60)
    cb.set_label("Trend 1981-2025, % of 1991-2020 mean per decade (blue = wetter / more; for CDD blue = shorter dry spells)")
    fig.suptitle("Trends in rainfall extremes (CHIRPS, 0.25°)", x=0.01, ha="left", fontweight="bold")
    save(fig, "fig04_rain_extremes_trends.png")
    df = pd.DataFrame(rows)
    df.round(3).to_csv(RES / "rain_extremes_zone.csv", index=False)
    return df


def annual_cycle(pr, z):
    zm = zone_mean(pr)
    rows = []
    zn = list(zm.zone.values)
    fig, axs = plt.subplots(2, (len(zn) + 1) // 2, figsize=(14, 6), sharex=True)
    cols = [MUTED, BLUE[3], CAT[1]]
    for ax, n in zip(axs.flat, zn):
        for (a, b), c in zip(EPOCHS, cols):
            s = zm.sel(zone=n, time=slice(f"{a}", f"{b}"))
            mon = s.groupby("time.month").mean() * xr.DataArray([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
                                                                  dims="month", coords={"month": range(1, 13)})
            ax.plot(mon.month, mon, color=c, lw=2, marker="o", ms=3, label=f"{a}-{b}")
            for m, v in zip(mon.month.values, mon.values):
                rows.append(dict(zone=n, epoch=f"{a}-{b}", month=int(m), mm=float(v)))
        ax.set_title(n, fontsize=9)
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(list("JFMAMJJASOND"))
        ax.set_ylim(0)
    for ax in axs.flat[len(zn):]:
        ax.axis("off")
    axs.flat[0].legend(fontsize=8)
    axs[0, 0].set_ylabel("mm/month")
    axs[1, 0].set_ylabel("mm/month")
    fig.suptitle("Mean monthly rainfall by 15-year epoch: has the shape of the seasons changed?", x=0.01, ha="left",
                 fontweight="bold")
    save(fig, "fig05_annual_cycle_epochs.png")
    pd.DataFrame(rows).round(1).to_csv(RES / "rain_annual_cycle_epochs.csv", index=False)

    # year x month anomaly (% of 1991-2020 monthly mean), Uganda
    u = zm.sel(zone="Uganda").resample(time="MS").sum()
    clim = u.sel(time=slice(f"{BASE[0]}", f"{BASE[1]}")).groupby("time.month").mean()
    an = 100 * (u.groupby("time.month") / clim - 1)
    tab = an.to_series()
    tab = pd.DataFrame({"year": tab.index.year, "month": tab.index.month, "v": tab.values}).pivot(
        index="year", columns="month", values="v")
    fig, ax = plt.subplots(figsize=(6.5, 8.5))
    im = ax.pcolormesh(np.arange(0.5, 13), np.arange(tab.index[0] - 0.5, tab.index[-1] + 1), tab.values,
                       cmap=CMAP_RAIN, vmin=-80, vmax=80, shading="flat")
    ax.invert_yaxis()
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(list("JFMAMJJASOND"))
    ax.grid(False)
    fig.colorbar(im, ax=ax, label="% anomaly vs 1991-2020", shrink=0.6)
    ax.set_title("Uganda monthly rainfall anomaly, 1981-2025")
    save(fig, "fig06_rain_month_year_anomaly.png")


def main():
    pr, z = daily()
    print(seasonal(pr, z).query("zone=='Uganda'"))
    print(extremes(pr, z).query("zone=='Uganda'"))
    annual_cycle(pr, z)


if __name__ == "__main__":
    main()
