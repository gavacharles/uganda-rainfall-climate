"""Rainy-season onset, cessation, length and in-season dry spells, every year 1981-2025, every CHIRPS cell.

Method (after Liebmann et al. 2012 and Dunning et al. 2016): each cell is classed as bimodal (two rainy seasons)
or unimodal from the ratio of the 2nd to 1st annual harmonic of its 1991-2020 daily climatology (ratio > 1 =
bimodal). Within a search window the cumulative daily anomaly A(d) = sum(R - Rbar), with Rbar the cell's
climatological mean daily rain, is computed; onset is the day after the minimum of A and cessation the day of
the maximum of A after onset. Windows: bimodal season 1 = 1 Feb-31 Jul, season 2 = 1 Aug-31 Jan (next year);
unimodal = 1 Jan-31 Dec. Rainy-season totals, rain days and the longest dry spell (<1 mm) between onset and
cessation are recorded.

Outputs: data/processed/seasons.nc, results/season_trend_zone.csv, results/season_epochs_zone.csv,
         figures fig07 (climatology + trend maps), fig08 (zone series), fig09 (regime map).
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import BoundaryNorm, ListedColormap

from common import (BASE, BLUE, CAT, CMAP_RAIN, CMAP_SEQ, EPOCHS, MUTED, PROC, RES, UG_EXTENT, Y0, Y1, chirps,
                    draw_borders, save, series_trend, stipple, trend_da, zone_mean, zones)

DOY0 = pd.Timestamp("2001-01-01")


def harmonic_ratio(clim):
    t = np.arange(clim.shape[0])
    f = np.fft.rfft(clim - clim.mean(0), axis=0)
    return np.abs(f[2]) / np.abs(f[1])


def season_metrics(r, rbar):
    """r: daily rain in the search window (1-D). Returns onset idx, cessation idx, total, rain days, max dry spell."""
    if np.isnan(r).mean() > 0.05:
        return [np.nan] * 5
    a = np.nancumsum(r - rbar)
    ce = int(np.argmax(a))  # cessation first, then onset = minimum before it (avoids a spurious late minimum)
    on = int(np.argmin(a[:ce + 1])) + 1 if ce > 0 else 0
    if ce - on < 15:
        return [np.nan] * 5
    seg = r[on:ce + 1]
    dry, best = 0, 0
    for v in seg:
        dry = dry + 1 if v < 1 else 0
        best = max(best, dry)
    return [on, ce, np.nansum(seg), int((seg >= 1).sum()), best]


def compute():
    pr = chirps()[0].sel(time=slice(f"{Y0}-01-01", f"{Y1 + 1}-01-31"))
    z = zones()
    base = pr.sel(time=slice(f"{BASE[0]}", f"{BASE[1]}"))
    clim = base.groupby(base.time.dt.dayofyear.clip(max=365)).mean().values  # 365, lat, lon
    hr = harmonic_ratio(clim)
    rbar = clim.mean(0)
    P = pr.values
    t = pd.DatetimeIndex(pr.time.values)
    nlat, nlon = len(pr.lat), len(pr.lon)
    years = np.arange(Y0, Y1 + 1)
    names = ["onset", "cessation", "total", "raindays", "maxdry"]
    out = {s: np.full((5, len(years), nlat, nlon), np.nan) for s in ("S1", "S2", "U")}
    win = {}
    for k, y in enumerate(years):
        win[("S1", y)] = (t >= f"{y}-02-01") & (t <= f"{y}-07-31")
        win[("S2", y)] = (t >= f"{y}-08-01") & (t <= f"{y + 1}-01-31")
        win[("U", y)] = (t >= f"{y}-01-01") & (t <= f"{y}-12-31")
    for i in range(nlat):
        for j in range(nlon):
            if z.values[i, j] < 0:
                continue
            seas = ("S1", "S2") if hr[i, j] > 1 else ("U",)
            for k, y in enumerate(years):
                for s in seas:
                    w = win[(s, y)]
                    if w.sum() < 150:
                        continue
                    m = season_metrics(P[w, i, j], rbar[i, j])
                    if np.isfinite(m[0]):
                        d0 = t[w][0]
                        # store onset / cessation as day-of-year relative to 1 Jan of the season's start year
                        m[0] = (t[w][int(m[0])] - pd.Timestamp(f"{y}-01-01")).days + 1
                        m[1] = (t[w][int(m[1])] - pd.Timestamp(f"{y}-01-01")).days + 1
                    out[s][:, k, i, j] = m
    ds = xr.Dataset()
    for s in out:
        for n, name in enumerate(names):
            ds[f"{s}_{name}"] = (("year", "lat", "lon"), out[s][n].astype("float32"))
        ds[f"{s}_length"] = ds[f"{s}_cessation"] - ds[f"{s}_onset"] + 1
    ds = ds.assign_coords(year=years, lat=pr.lat, lon=pr.lon)
    ds["harmonic_ratio"] = (("lat", "lon"), hr.astype("float32"))
    ds["bimodal"] = (("lat", "lon"), ((hr > 1) & (z.values >= 0)).astype("int8"))
    ds.to_netcdf(PROC / "seasons.nc")
    return ds


def doy_label(d):
    return (DOY0 + pd.Timedelta(days=float(d) - 1)).strftime("%d %b") if np.isfinite(d) else "-"


def figures(ds):
    z = zones()
    bim = ds.bimodal
    # regime map
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    reg = xr.where(z >= 0, bim, np.nan)
    ax.pcolormesh(reg.lon, reg.lat, reg, cmap=ListedColormap([CAT[3], CAT[0]]), shading="nearest", vmin=0, vmax=1)
    draw_borders(ax, UG_EXTENT)
    ax.set_title("Rainfall regime (harmonic ratio)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=CAT[0], label="Bimodal: two rainy seasons"),
                       Patch(color=CAT[3], label="Unimodal: one long season")], loc="lower left", fontsize=7)
    save(fig, "fig09_regime_map.png")

    # climatology + trend maps
    panels = [("S1", "onset", "First rains onset"), ("S1", "cessation", "First rains cessation"),
              ("S1", "length", "First rains length"), ("S2", "onset", "Second rains onset"),
              ("S2", "cessation", "Second rains cessation"), ("S2", "length", "Second rains length"),
              ("U", "onset", "Unimodal onset"), ("U", "cessation", "Unimodal cessation"),
              ("U", "length", "Unimodal length")]
    fig, axs = plt.subplots(3, 6, figsize=(16, 9.6))
    for k, (s, v, title) in enumerate(panels):
        da = ds[f"{s}_{v}"]
        clim = da.sel(year=slice(*BASE)).mean("year")
        slope, p = trend_da(da.where(da.count("year") > 35))
        r, c = k // 3, (k % 3) * 2
        ax = axs[r, c]
        if v == "length":
            im = ax.pcolormesh(clim.lon, clim.lat, clim, cmap=CMAP_SEQ, shading="nearest", vmin=40, vmax=260)
            fig.colorbar(im, ax=ax, shrink=0.7, label="days")
        else:
            im = ax.pcolormesh(clim.lon, clim.lat, clim, cmap="viridis", shading="nearest",
                               vmin=float(clim.quantile(0.03)), vmax=float(clim.quantile(0.97)))
            cb = fig.colorbar(im, ax=ax, shrink=0.7)
            cb.set_ticks(cb.get_ticks())
            cb.set_ticklabels([doy_label(x) for x in cb.get_ticks()])
        draw_borders(ax, UG_EXTENT)
        ax.set_title(f"{title}\n1991-2020 mean", fontsize=8)
        ax = axs[r, c + 1]
        lev = [-15, -10, -6, -3, -1, 1, 3, 6, 10, 15]
        cmap = CMAP_RAIN.reversed() if v == "onset" else CMAP_RAIN
        im = ax.pcolormesh(slope.lon, slope.lat, slope, cmap=cmap, norm=BoundaryNorm(lev, 256, extend="both"),
                           shading="nearest")
        stipple(ax, p.where(slope.notnull()), slope.lon, slope.lat, s=1.5)
        draw_borders(ax, UG_EXTENT)
        fig.colorbar(im, ax=ax, shrink=0.7, label="days/decade")
        ax.set_title(f"{title}\ntrend 1981-2025", fontsize=8)
    fig.suptitle("Rainy-season timing: climatology and trend (onset: red = later; cessation/length: red = earlier/shorter)",
                 x=0.01, ha="left", fontweight="bold")
    save(fig, "fig07_season_timing_maps.png")

    # zone series and tables
    rows, erows = [], []
    for s in ("S1", "S2", "U"):
        for v in ("onset", "cessation", "length", "total", "maxdry", "raindays"):
            zm = zone_mean(ds[f"{s}_{v}"].where(ds[f"{s}_{v}"].count("year") > 35))
            for n in zm.zone.values:
                y = zm.sel(zone=n).values
                if np.isfinite(y).sum() < 35:
                    continue
                sl, p, _ = series_trend(y)
                rows.append(dict(season=s, metric=v, zone=n, mean_1991_2020=float(np.nanmean(zm.sel(zone=n, year=slice(*BASE)))),
                                 sen_per_decade=sl, p_value=p, sd=float(np.nanstd(y))))
                for a, b in EPOCHS:
                    erows.append(dict(season=s, metric=v, zone=n, epoch=f"{a}-{b}",
                                      mean=float(np.nanmean(zm.sel(zone=n, year=slice(a, b))))))
    tr = pd.DataFrame(rows)
    tr.round(3).to_csv(RES / "season_trend_zone.csv", index=False)
    pd.DataFrame(erows).round(1).to_csv(RES / "season_epochs_zone.csv", index=False)

    zn = [n for n in tr.zone.unique()]
    fig, axs = plt.subplots(1, 2, figsize=(13, 5.2), sharey=True)
    for ax, s, title in zip(axs, ("S1", "S2"), ("First rains (Feb-Jul window)", "Second rains (Aug-Jan window)")):
        on = zone_mean(ds[f"{s}_onset"].where(ds[f"{s}_onset"].count("year") > 35))
        ce = zone_mean(ds[f"{s}_cessation"].where(ds[f"{s}_cessation"].count("year") > 35))
        names = [n for n in on.zone.values if np.isfinite(on.sel(zone=n)).sum() > 35]
        for i, n in enumerate(names):
            y0 = i
            yrs = on.year.values
            o, c = on.sel(zone=n).values, ce.sel(zone=n).values
            ax.hlines(y0 + (yrs - Y0) / (Y1 - Y0) * 0.8 - 0.4, o, c, color=BLUE[3] if n != "Uganda" else CAT[1], lw=1.2)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=8)
        ax.invert_yaxis()
        ticks = pd.date_range("2001-01-01", "2002-02-01", freq="MS")
        ax.set_xticks([(d - DOY0).days + 1 for d in ticks])
        ax.set_xticklabels([d.strftime("%b") for d in ticks], fontsize=7)
        ax.set_xlim((pd.Timestamp("2001-02-01") - DOY0).days if s == "S1" else (pd.Timestamp("2001-07-15") - DOY0).days,
                    (pd.Timestamp("2001-08-01") - DOY0).days if s == "S1" else (pd.Timestamp("2002-02-01") - DOY0).days)
        ax.set_title(f"{title}: each line is one year, 1981 (top) to 2025 (bottom)")
    save(fig, "fig08_season_bars_zone.png")
    return tr


if __name__ == "__main__":
    f = PROC / "seasons.nc"
    ds = xr.open_dataset(f).load() if f.exists() else compute()
    tr = figures(ds)
    print(tr[tr.zone == "Uganda"].to_string())
    print(tr[tr.p_value < 0.05].to_string())
