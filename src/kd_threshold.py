"""Paper A core test: has the rainfall needed to flood Kampala fallen, 2017-2026?

Unit: every day 2017-01-01 .. 2026-10-05 (CHIRPS end). Outcome: a reported flood day (GDELT catalogue, >= 2 outlets,
plus verified manual events). Predictors: same-day and 3-day antecedent rain (CHIRPS Greater-Kampala mean; NASA POWER
hourly peak as sensitivity), a linear time trend (per year), and news coverage (GDELT monthly count of all English
articles mentioning Kampala, log) so that growth in reporting is not read as falling thresholds.
  trend > 0 at fixed rain and coverage  =>  the same rain floods more often  =>  falling threshold (drainage decline)
Also: rain percentile on flood days by year (Kendall tau), and a placebo with dry days (< 1 mm).
Outputs results/kd_threshold_*.csv, figure kd26.
"""
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm
import xarray as xr
from scipy import stats

from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
BOX = dict(lat=slice(0.15, 0.50), lon=slice(32.40, 32.80))


def coverage():
    f = KD / "gdelt_kampala_volume.csv"
    if f.exists():
        return pd.read_csv(f, parse_dates=["date"]).set_index("date").n
    params = dict(query="Kampala sourcelang:english", mode="timelinevolraw", format="json",
                  startdatetime="20170101000000", enddatetime="20261013000000")
    for _ in range(8):
        r = requests.get("https://api.gdeltproject.org/api/v2/doc/doc", params=params, timeout=180)
        if r.status_code == 429:
            time.sleep(60)
            continue
        break
    tl = r.json()["timeline"][0]["data"]
    s = pd.Series({pd.to_datetime(d["date"][:8]): d["value"] for d in tl}, name="n")
    s.index.name = "date"
    s.to_frame().to_csv(f)
    return s


def events():
    g = pd.read_csv(KD / "flood_catalogue_gdelt.csv", parse_dates=["start", "end"])
    m = pd.read_csv(KD / "flood_events.csv", parse_dates=["date"])
    days = set()
    for r in g.itertuples():
        for d in pd.date_range(r.start, r.end):
            days.add(d.normalize())
    for d in m.date:
        days.add(d.normalize())
    return sorted(days)


def main():
    ch = xr.open_dataset(PROC / "chirps_uganda_daily.nc")["precip"].sel(**BOX).mean(("lat", "lon")).to_series()
    ch = ch["2017-01-01":"2026-10-05"]
    pw = pd.read_csv(KD / "power_hourly_kampala.csv", index_col=0, parse_dates=True).PRECTOTCORR
    pw = pw.where(pw < 150)
    pmax = pw.resample("D").max()
    cov = coverage()
    covm = cov.resample("MS").sum()
    fl = set(events())
    df = pd.DataFrame({"r1": ch, "r3": ch.rolling(3).sum(), "pmax": pmax.reindex(ch.index)})
    df["flood"] = [int(d in fl) for d in df.index]
    df["t"] = (df.index - pd.Timestamp("2017-01-01")).days / 365.25
    df["cov"] = np.log(covm.reindex(df.index.to_period("M").to_timestamp()).values + 1)
    df = df.dropna(subset=["r1", "r3", "cov"])
    print("flood days:", int(df.flood.sum()), "of", len(df))
    rows = []
    wet = df[df.r1 >= 1].copy()
    for name, d, cols in (("CHIRPS wet days", wet, ["lr1", "lr3", "t", "cov"]),
                          ("CHIRPS wet days, no coverage control", wet, ["lr1", "lr3", "t"]),
                          ("POWER peak-hour, wet days", wet.dropna(subset=["pmax"]), ["lpmax", "lr3", "t", "cov"])):
        d = d.assign(lr1=np.log1p(d.r1), lr3=np.log1p(d.r3), lpmax=np.log1p(d.pmax))
        X = sm.add_constant(d[cols])
        m = sm.Logit(d.flood, X).fit(disp=0, cov_type="HAC", cov_kwds={"maxlags": 7})
        rows.append(dict(model=name, n=len(d), floods=int(d.flood.sum()),
                         trend_or_per_year=float(np.exp(m.params["t"])),
                         ci_lo=float(np.exp(m.conf_int().loc["t", 0])), ci_hi=float(np.exp(m.conf_int().loc["t", 1])),
                         p_trend=float(m.pvalues["t"]),
                         rain_or_per_log=float(np.exp(m.params[cols[0]])), p_rain=float(m.pvalues[cols[0]])))
    # placebo: dry days should show no rain-driven "floods"; flood reports on dry days measure reporting noise
    dry = df[df.r1 < 1]
    rows.append(dict(model="placebo: share of flood days that were dry (<1 mm)", n=len(dry), floods=int(dry.flood.sum()),
                     trend_or_per_year=np.nan, ci_lo=np.nan, ci_hi=np.nan, p_trend=np.nan,
                     rain_or_per_log=np.nan, p_rain=np.nan))
    res = pd.DataFrame(rows)
    res.round(4).to_csv(RES / "kd_threshold_models.csv", index=False)
    print(res.round(3).to_string())
    # rain percentile on flood days, by year
    clim = ch[ch >= 1]
    fd = df[df.flood == 1].copy()
    fd["pct3"] = [(clim.rolling(3).sum().dropna() < v).mean() * 100 for v in fd.r3]
    fd["pct1"] = [(clim < v).mean() * 100 for v in fd.r1]
    fd["year"] = fd.index.year
    tau, p = stats.kendalltau(fd.t, fd.pct3)
    fd[["r1", "r3", "pct1", "pct3", "pmax", "year"]].round(1).to_csv(RES / "kd_threshold_flood_days.csv")
    print("Kendall tau (3-day rain percentile on flood days vs time):", round(tau, 3), "p =", round(p, 3))
    # figure
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8))
    yrs = fd.groupby("year")
    axs[0].scatter(fd.index, fd.r3, s=24, color="#b30000", alpha=0.75, label="reported flood days")
    q50 = df.r3.rolling(365, min_periods=200).quantile(0.9)
    axs[0].plot(q50.index, q50, color="#555", lw=1.2, label="90th percentile of 3-day rain (rolling year)")
    if len(fd) > 5:
        z = np.polyfit(fd.t, fd.r3, 1)
        tt = np.array([fd.t.min(), fd.t.max()])
        axs[0].plot(pd.Timestamp("2017-01-01") + pd.to_timedelta(tt * 365.25, unit="D"), np.polyval(z, tt), "--", color="#b30000",
                    lw=1.5, label=f"trend in rain on flood days ({z[0]:+.1f} mm/yr)")
    axs[0].set_ylabel("3-day rain ending on the day (mm, CHIRPS)")
    axs[0].legend(fontsize=8.5, loc="upper left")
    axs[0].set_title("Rain on reported flood days", loc="left")
    r0 = res.iloc[0]
    axs[1].errorbar([0, 1, 2], res.trend_or_per_year[:3], yerr=[res.trend_or_per_year[:3] - res.ci_lo[:3], res.ci_hi[:3] - res.trend_or_per_year[:3]],
                    fmt="o", color="#08519c", capsize=5, ms=8)
    axs[1].axhline(1, color="#888", lw=1)
    axs[1].set_xticks([0, 1, 2])
    axs[1].set_xticklabels(["daily rain +\ncoverage control", "daily rain,\nno control", "peak-hour rain +\ncoverage control"], fontsize=9)
    axs[1].set_ylabel("odds of a reported flood per year, at the same rain")
    axs[1].set_title("Has the same rain become more likely to flood?", loc="left")
    fig.suptitle("Falling flood thresholds? Kampala 2017-2026", x=0.01, ha="left", fontweight="bold")
    save(fig, "kd26_flood_threshold_trend.png", OUT,
         source="Rain: CHIRPS v2.0 (UCSB CHC), NASA POWER hourly (MERRA-2) · flood days: GDELT news index (>= 2 outlets) and "
                "verified reports · coverage control: GDELT volume of Kampala news")


if __name__ == "__main__":
    main()
