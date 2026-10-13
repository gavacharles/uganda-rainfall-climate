"""Kampala drainage study, part 1: how has Kampala's rain changed, what rain floods the channels, and does
temperature matter?

Inputs: CHIRPS v2.0 daily (0.25 deg cells over Greater Kampala), ARC2 daily (0.1 deg), NOAA CPC Tmax/Tmin,
NASA POWER hourly (MERRA-2: precipitation, 2 m temperature and dew point at central Kampala), and the dated
flood catalogue data/kd/flood_events.csv compiled from news reports.

Outputs (results/kd_*):
  kd_rain_annual.csv       annual totals, heavy-rain days, max 1-day / 3-day rain, wet-season totals
  kd_rain_trends.csv       Sen slope + Mann-Kendall for each index
  kd_flood_event_rain.csv  rain on each flood date (1-day, 3-day, 7-day antecedent) and its percentile
  kd_temp_scaling.csv      hourly-extreme rain vs dew point (Clausius-Clapeyron test)
Figures (figures/kd01..kd04).
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from common import BLUE, CAT, FIG, ORANGE, PROC, RES, ROOT, save, series_trend

KD = ROOT / "data" / "kd"
KDFIG = FIG / "kampala_drainage"  # all figures for the Kampala drainage study
BOX = dict(lat=slice(0.15, 0.50), lon=slice(32.40, 32.80))


def kampala_daily():
    ch = xr.open_dataset(PROC / "chirps_uganda_daily.nc")["precip"].sel(**BOX).mean(("lat", "lon")).to_series()
    ar = xr.open_dataset(PROC / "arc2_uganda_daily.nc")["precip"].sel(**BOX).mean(("lat", "lon")).to_series()
    cpc = xr.open_dataset(PROC / "cpc_uganda_daily.nc").sel(lat=slice(0.0, 0.75), lon=slice(32.25, 33.0)).mean(("lat", "lon"))
    pw = pd.read_csv(KD / "power_hourly_kampala.csv", index_col=0, parse_dates=True)
    pw.loc[pw.PRECTOTCORR > 150, "PRECTOTCORR"] = np.nan  # fill values
    return ch, ar, cpc.tmax.to_series(), cpc.tmin.to_series(), pw


def indices(s, name):
    s = s[: "2025-12-31"]
    y = s.groupby(s.index.year)
    r3 = s.rolling(3).sum()
    out = pd.DataFrame({
        f"{name}_total": y.sum(),
        f"{name}_days_ge20": y.apply(lambda v: (v >= 20).sum()),
        f"{name}_days_ge30": y.apply(lambda v: (v >= 30).sum()),
        f"{name}_max1d": y.max(),
        f"{name}_max3d": r3.groupby(r3.index.year).max(),
        f"{name}_mam": s[s.index.month.isin([3, 4, 5])].groupby(lambda d: d.year).sum(),
        f"{name}_son": s[s.index.month.isin([9, 10, 11])].groupby(lambda d: d.year).sum(),
    })
    return out


def main():
    ch, ar, tx, tn, pw = kampala_daily()
    ann = indices(ch, "chirps").join(indices(ar, "arc2"), how="outer")
    hourly = pw.PRECTOTCORR
    hy = hourly[:"2025-12-31"].groupby(hourly[:"2025-12-31"].index.year)
    ann["power_max1h"] = hy.max()
    ann["power_hours_ge5"] = hy.apply(lambda v: (v >= 5).sum())
    ann["tmax_mean"] = tx[:"2025"].groupby(tx[:"2025"].index.year).mean()
    ann["tmin_mean"] = tn[:"2025"].groupby(tn[:"2025"].index.year).mean()
    ann.index.name = "year"
    ann.round(2).to_csv(RES / "kd_rain_annual.csv")

    rows = []
    for c in ann.columns:
        v = ann[c].dropna()
        v = v[v.index >= (1983 if c.startswith("arc2") else 1981)]
        if len(v) < 15:
            continue
        sl, p, _ = series_trend(v.values)
        early, late = v.loc[:v.index[0] + 14].mean(), v.loc[v.index[-1] - 14:].mean()
        rows.append(dict(index=c, first_year=int(v.index[0]), last_year=int(v.index[-1]), sen_per_decade=sl,
                         p_value=p, mean_first15=early, mean_last15=late, change_pct=100 * (late / early - 1)))
    tr = pd.DataFrame(rows)
    tr.round(3).to_csv(RES / "kd_rain_trends.csv", index=False)
    print(tr.round(2).to_string())

    # --- rain on flood dates
    ev = pd.read_csv(KD / "flood_events.csv", parse_dates=["date"])
    src = ch.copy()
    hd = hourly.resample("D").sum(min_count=20)
    clim = src["1991":"2020"]
    wet = clim[clim >= 1]
    erows = []
    for _, e in ev.iterrows():
        d = e.date
        r1 = src.get(d, np.nan)
        r3 = src[d - pd.Timedelta(days=2): d].sum() if d in src.index else np.nan
        r7 = src[d - pd.Timedelta(days=6): d].sum() if d in src.index else np.nan
        p1 = hd.get(d, np.nan)
        p3 = hd[d - pd.Timedelta(days=2): d].sum() if d in hd.index else np.nan
        mx = hourly[d: d + pd.Timedelta(hours=23)].max() if d in hd.index else np.nan
        erows.append(dict(date=d.date(), places=e.places, chirps_1d=r1, chirps_3d=r3, chirps_7d=r7,
                          chirps_1d_pctile_wetdays=(wet < r1).mean() * 100 if np.isfinite(r1) else np.nan,
                          power_1d=p1, power_3d=p3, power_max1h=mx))
    er = pd.DataFrame(erows)
    er.round(1).to_csv(RES / "kd_flood_event_rain.csv", index=False)
    print(er.round(1).to_string())

    # --- temperature: hourly extremes vs dew point (binned scaling) and hot-day storms
    df = pw.dropna()
    daily = df.resample("D").agg({"PRECTOTCORR": "max", "T2MDEW": "mean", "T2M": "max"}).dropna()
    daily = daily[daily.PRECTOTCORR >= 0.5]
    bins = np.arange(np.floor(daily.T2MDEW.quantile(0.02)), np.ceil(daily.T2MDEW.quantile(0.98)) + 0.5, 0.5)
    daily["bin"] = pd.cut(daily.T2MDEW, bins)
    sc = daily.groupby("bin", observed=True).PRECTOTCORR.agg(n="size", p50="median", p90=lambda v: v.quantile(0.9),
                                                            p99=lambda v: v.quantile(0.99))
    sc["dew_mid"] = [b.mid for b in sc.index]
    sc = sc[sc.n >= 50]
    sc.reset_index(drop=True).round(3).to_csv(RES / "kd_temp_scaling.csv", index=False)
    rate = {}
    for q in ("p90", "p99"):
        k = np.polyfit(sc.dew_mid, np.log(sc[q]), 1)[0]
        rate[q] = 100 * (np.exp(k) - 1)
    print("hourly-extreme scaling with dew point, %/degC:", {k: round(v, 1) for k, v in rate.items()})
    # CPC: heavy-rain days (CHIRPS>=20) vs Tmax anomaly on the day before
    t_anom = (tx - tx.groupby(tx.index.dayofyear).transform("mean"))
    j = pd.DataFrame({"r": ch, "ta_prev": t_anom.shift(1)}).dropna()
    heavy = j[j.r >= 20].ta_prev.mean()
    other = j[(j.r >= 1) & (j.r < 20)].ta_prev.mean()
    print(f"Tmax anomaly the day before heavy (>=20mm) days: {heavy:+.2f} C vs other wet days {other:+.2f} C")
    pd.Series({"scaling_p90_pct_per_C": rate["p90"], "scaling_p99_pct_per_C": rate["p99"],
               "tmax_anom_before_heavy": heavy, "tmax_anom_before_other_wet": other}).round(3).to_csv(
        RES / "kd_temp_summary.csv", header=["value"])

    figures(ann, tr, er, sc, rate, ch, hourly)


def figures(ann, tr, er, sc, rate, ch, hourly):
    # kd01: annual indices
    fig, axs = plt.subplots(2, 2, figsize=(13, 7.5))
    spec = [("chirps_total", "arc2_total", "Annual rainfall (mm)"),
            ("chirps_days_ge20", "arc2_days_ge20", "Days with 20 mm or more"),
            ("chirps_max1d", "arc2_max1d", "Wettest day of the year (mm)"),
            ("chirps_max3d", "arc2_max3d", "Wettest 3 days of the year (mm)")]
    for ax, (a, b, t) in zip(axs.flat, spec):
        for c, col, lab in ((a, BLUE[3], "CHIRPS"), (b, ORANGE[3], "ARC2")):
            v = ann[c].dropna()
            ax.plot(v.index, v, color=col, lw=1.2, alpha=0.6, label=lab)
            ax.plot(v.index, v.rolling(9, center=True, min_periods=5).mean(), color=col, lw=2.4)
            r = tr.set_index("index").loc[c]
            ax.text(0.01, 0.95 - 0.08 * (col == ORANGE[3]), f"{lab}: {r.sen_per_decade:+.1f}/decade (p={r.p_value:.2f})",
                    transform=ax.transAxes, fontsize=8, color=col, va="top")
        ax.set_title(t)
    axs[0, 0].legend(loc="lower right", fontsize=8)
    for ax in axs.flat:
        ax.axvspan(2019.5, 2025.5, color="#f4a582", alpha=0.12, lw=0)
    axs[0, 1].text(0.99, 0.62, "ARC2 jumps after 2019 with no\nmatching rise in CHIRPS: likely a\nchange in ARC2's inputs, not real rain",
                   transform=axs[0, 1].transAxes, ha="right", fontsize=7.5, color=ORANGE[4])
    fig.suptitle("Greater Kampala rainfall, 1981-2025 (thin: yearly; thick: 9-year mean)", x=0.01, ha="left",
                 fontweight="bold")
    save(fig, "kd01_kampala_rain_indices.png", KDFIG, source="Data: CHIRPS v2.0 (UCSB Climate Hazards Center); ARC2 (NOAA Climate Prediction Center). Greater Kampala area average.")

    # kd02: flood dates against the rainfall distribution (numbered lines + key: no label overlaps)
    fig = plt.figure(figsize=(12, 5))
    ax = fig.add_axes([0.06, 0.12, 0.62, 0.74])
    wet = ch["1991":"2020"]
    wet = wet[wet >= 1]
    ax.hist(wet, bins=np.arange(0, 50, 2), color="#cfd8dc", label="all wet days 1991-2020")
    ev = er[np.isfinite(er.chirps_1d)].sort_values("chirps_1d").reset_index(drop=True)
    top = ax.get_ylim()[1]
    ax.set_ylim(0, top * 1.25)
    key = []
    xs = []
    for k, r in ev.iterrows():
        ax.axvline(r.chirps_1d, color=ORANGE[4], lw=1.5, ymax=0.78)
        x = r.chirps_1d if not xs else max(r.chirps_1d, xs[-1] + 1.3)  # keep numbers at least 1.3 mm apart
        xs.append(x)
        ax.annotate(str(k + 1), (r.chirps_1d, top * 1.25 * 0.78), xytext=(x, top * 1.25 * 0.86), ha="center",
                    va="bottom", fontsize=9, fontweight="bold", color=ORANGE[4],
                    arrowprops=dict(arrowstyle="-", color=ORANGE[4], lw=0.6))
        key.append(f"{k + 1}.  {pd.Timestamp(r.date):%d %b %Y}:  {r.chirps_1d:.1f} mm  ({r.chirps_1d_pctile_wetdays:.0f}th pct)")
    ax.set_xlabel("CHIRPS daily rain over Greater Kampala (mm, area average)")
    ax.set_ylabel("days")
    ax.legend(loc="center right", fontsize=8.5)
    fig.text(0.06, 0.95, "Reported Kampala flood days are often NOT extreme rain days", fontsize=12, fontweight="bold")
    fig.text(0.71, 0.84, "Reported flood days (satellite rain\nthat day, percentile among wet days)", fontsize=9,
             fontweight="bold", va="top")
    fig.text(0.71, 0.74, "\n".join(key), fontsize=8.8, va="top", linespacing=1.6, color="#333")
    fig.text(0.71, 0.30, "Satellite rain is an area average and\nsmooths local downpours: on 29-31 Oct\n2025 the Makerere "
             "gauge recorded 63 mm\nvs 21 mm from CHIRPS.", fontsize=8.5, va="top", color="#555")
    save(fig, "kd02_flood_days_rain.png", KDFIG, source="Data: CHIRPS v2.0 (UCSB Climate Hazards Center). Flood dates: Daily Monitor, New Vision, NTV Uganda, The Observer, 93.3 KFM, ReliefWeb and FloodList reports.")

    # kd03: scaling
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.semilogy(sc.dew_mid, sc.p99, "o-", color=ORANGE[4], label=f"99th pct ({rate['p99']:+.0f}%/°C)")
    ax.semilogy(sc.dew_mid, sc.p90, "o-", color=BLUE[3], label=f"90th pct ({rate['p90']:+.0f}%/°C)")
    x = np.array([sc.dew_mid.min(), sc.dew_mid.max()])
    for q, col in (("p99", ORANGE[4]), ("p90", BLUE[3])):
        y0 = sc[q].iloc[len(sc) // 2]
        x0 = sc.dew_mid.iloc[len(sc) // 2]
        ax.semilogy(x, y0 * 1.07 ** (x - x0), "--", color=col, lw=0.8)
    ax.text(0.02, 0.03, "dashed: 7%/°C Clausius-Clapeyron", transform=ax.transAxes, fontsize=8)
    ax.set_xlabel("daily mean dew point (°C)")
    ax.set_ylabel("peak hourly rain on wet days (mm/h)")
    ax.set_title("Hourly rain intensity vs humidity, Kampala 2001-2026 (NASA POWER/MERRA-2)")
    ax.legend()
    save(fig, "kd03_intensity_dewpoint.png", KDFIG, source="Data: NASA POWER hourly (MERRA-2 reanalysis), central Kampala, 2001-2026.")


if __name__ == "__main__":
    main()
