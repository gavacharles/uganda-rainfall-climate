"""Bulk water supply: source reliability (multi-year droughts) and climate drivers of demand and treatment.

Source side: standardised precipitation index at 12 and 24 months (SPI, gamma fit per calendar month, 1991-2020
base) by zone; worst 12-, 24- and 36-month rainfall totals as % of normal, and their dates; drought months
(SPI-24 < -1) per decade. Demand/treatment side: hottest-month Tmax and warm-night trends (CPC), peak-month ET0
(irrigation and garden demand proxy), days with >= 50 mm (gauge-calibrated ~ CHIRPS >= 26 mm) storms that drive
raw-water turbidity peaks, and the share of rain falling after >= 20 dry days ('first-flush' events).

Outputs: fig31 (SPI-24 by zone), fig32 (worst multi-year deficits), results/bulk_water_zone.csv
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from scipy import stats

from common import (BASE, BLUE, CAT, CMAP_RAIN, GRID, INK, INK2, MUTED, ORANGE, PROC, RED, RES, Y0, Y1, chirps,
                    save, series_trend, zone_mean, zones)


def spi(series, scale):
    """SPI for a monthly pandas Series (mm), gamma fit per calendar month on the base period."""
    acc = series.rolling(scale).sum()
    out = pd.Series(np.nan, index=series.index)
    for m in range(1, 13):
        s = acc[acc.index.month == m].dropna()
        b = s[(s.index.year >= BASE[0]) & (s.index.year <= BASE[1])]
        a, loc, sc = stats.gamma.fit(b[b > 0], floc=0)
        out.loc[s.index] = stats.norm.ppf(np.clip(stats.gamma.cdf(s, a, loc, sc), 1e-4, 1 - 1e-4))
    return out


def main():
    pr = chirps()[0]
    z = zones()
    zm_d = zone_mean(pr.where(z >= 0))
    mon = zm_d.resample(time="MS").sum().sel(time=slice(f"{Y0}", "2026-09"))
    rows = []
    fig, axs = plt.subplots(len(mon.zone), 1, figsize=(12, 1.6 * len(mon.zone)), sharex=True)
    worst = []
    for ax, n in zip(axs, mon.zone.values):
        s = mon.sel(zone=n).to_series()
        s24 = spi(s, 24)
        s12 = spi(s, 12)
        ax.fill_between(s24.index, 0, s24.clip(upper=0), color=ORANGE[3], lw=0)
        ax.fill_between(s24.index, 0, s24.clip(lower=0), color=BLUE[3], lw=0)
        ax.axhline(-1, color=INK2, lw=0.6, ls=":")
        ax.set_ylim(-3, 3)
        ax.set_ylabel("SPI-24", fontsize=7)
        ax.text(0.005, 0.92, n, transform=ax.transAxes, fontsize=8, va="top", fontweight="bold")
        mean = s[(s.index.year >= BASE[0]) & (s.index.year <= BASE[1])].mean()
        r = dict(zone=n)
        for w in (12, 24, 36):
            acc = s.rolling(w).sum().loc[:"2025-12"]
            lo = acc.idxmin()
            r[f"worst_{w}m_pct_of_normal"] = 100 * acc.min() / (mean * w)
            r[f"worst_{w}m_ending"] = lo.strftime("%Y-%m")
            worst.append(dict(zone=n, window=f"{w} months", pct=r[f"worst_{w}m_pct_of_normal"], end=lo.strftime("%b %Y")))
        for a, b in ((1981, 1995), (1996, 2010), (2011, 2025)):
            r[f"SPI24<-1 months/decade {a}-{b}"] = 10 * (s24[str(a):str(b)] < -1).sum() / (b - a + 1)
        r["SPI12 Sep 2026"] = float(s12.iloc[-1])
        r["SPI24 Sep 2026"] = float(s24.iloc[-1])
        rows.append(r)
    fig.suptitle("Multi-year rainfall surpluses and droughts by zone (SPI-24, CHIRPS; orange = drought)", x=0.01,
                 ha="left", fontweight="bold")
    save(fig, "fig31_spi24_zones.png")

    w = pd.DataFrame(worst)
    fig, ax = plt.subplots(figsize=(11, 4.6))
    zn = list(dict.fromkeys(w.zone))
    for k, (win, c) in enumerate(zip(["12 months", "24 months", "36 months"], [ORANGE[2], ORANGE[4], ORANGE[6]])):
        sub = w[w.window == win].set_index("zone").loc[zn]
        x = np.arange(len(zn)) + (k - 1) * 0.27
        ax.bar(x, sub.pct, width=0.25, color=c, label=win)
        for xi, (p, e) in zip(x, zip(sub.pct, sub.end)):
            ax.text(xi, p + 1, e, rotation=90, fontsize=6.5, ha="center", va="bottom", color=INK2)
    ax.set_xticks(range(len(zn)))
    ax.set_xticklabels([n.replace(" (", "\n(") for n in zn], fontsize=7.5)
    ax.set_ylim(0, 110)
    ax.axhline(100, color=MUTED, lw=0.8)
    ax.set_ylabel("lowest rainfall total, % of normal")
    ax.legend(fontsize=8, title="window", title_fontsize=8, loc="lower right")
    ax.set_title("Design droughts for water sources: driest 12/24/36-month spells 1981-2025 (label = end month)")
    save(fig, "fig32_worst_droughts.png")

    # demand / treatment drivers
    cpc = xr.open_dataset(PROC / "cpc_uganda_daily.nc").load().sel(time=slice(f"{Y0}", f"{Y1}"))
    from common import grid_mask
    m = grid_mask(cpc.lat, cpc.lon, exclude_lakes=False)
    tx = cpc.tmax.where(m).mean(("lat", "lon")).resample(time="MS").mean()
    hot = tx.groupby("time.year").max()
    s_hot, p_hot, _ = series_trend(hot.values)
    d = pr.sel(time=slice(f"{Y0}", f"{Y1}")).where(z >= 0)
    heavy = (d >= 26).groupby("time.year").sum()  # ~ 50 mm at a gauge (calibration factor ~1.9)
    dry = (d < 1).astype("int16")
    # first-flush: rain >= 10 mm falling after >= 20 consecutive dry days
    run = np.zeros(dry.shape[1:], int)
    ff = np.zeros(dry.shape[1:])
    ffy = []
    vals, dv = d.values, dry.values
    years = d.time.dt.year.values
    cur = years[0]
    for t in range(len(years)):
        if years[t] != cur:
            ffy.append(ff.copy())
            ff[:] = 0
            cur = years[t]
        ff += (vals[t] >= 10) & (run >= 20)
        run = np.where(dv[t] == 1, run + 1, 0)
    ffy.append(ff.copy())
    ffda = xr.DataArray(np.array(ffy), dims=("year", "lat", "lon"), coords={"year": np.unique(years), "lat": d.lat, "lon": d.lon})
    zh = zone_mean(heavy.where(z >= 0))
    zf = zone_mean(ffda.where(z >= 0))
    for r in rows:
        n = r["zone"]
        sh, ph, _ = series_trend(zh.sel(zone=n).values)
        r["heavy_days_per_yr_1991_2020"] = float(zh.sel(zone=n, year=slice(*BASE)).mean())
        r["heavy_days_trend_per_decade"] = sh
        r["heavy_days_p"] = ph
        r["first_flush_events_per_yr"] = float(zf.sel(zone=n).mean())
    out = pd.DataFrame(rows)
    out["hottest_month_Tmax_trend_C_per_decade_Uganda"] = s_hot
    out["hottest_month_Tmax_p"] = p_hot
    out.round(2).to_csv(RES / "bulk_water_zone.csv", index=False)
    return out


if __name__ == "__main__":
    print(main().round(2).T.to_string())
