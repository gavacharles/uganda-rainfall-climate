"""Why the 2026 'El Nino = heavy rains' forecast has not (yet) verified, and how to forecast better.

1. 2026 so far: rainfall anomalies (MAM, JJA, 1 Sep-latest) and cumulative second-season curves vs analogue years.
2. Teleconnections 1981-2025: OND rainfall vs Nino3.4, DMI and the two Indian Ocean poles (correlation maps,
   partial correlations, El Nino-year table).
3. Hindcast skill of statistical forecasts of OND zone rainfall, issued mid-Aug (July SST) and early Oct (Sep SST
   + Sep rain), leave-one-out cross-validated: climatology, ENSO only, ENSO+DMI, ENSO+IO poles, ridge, LightGBM.
4. 2026 OND outlook from the best model, with tercile probabilities by zone.

Figures fig14-fig18; tables results/forecast_*.csv
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import BoundaryNorm
from scipy import stats
from sklearn.linear_model import LinearRegression, RidgeCV

from common import (BASE, BLUE, CAT, CMAP_RAIN, GRID, INK, INK2, MUTED, RED, RES, UG_EXTENT, Y0, Y1, chirps,
                    draw_borders, indices, oni, save, zone_mean, zones)

pr_all, prelim, last_final = chirps()
z = zones()
pr_all = pr_all.where(z >= 0)
LAST = pd.Timestamp(pr_all.time.values[-1])
YEARS = np.arange(Y0, Y1 + 1)


def window_total(da, y, m0, d0, m1, d1):
    return da.sel(time=slice(f"{y}-{m0:02d}-{d0:02d}", f"{y}-{m1:02d}-{d1:02d}")).sum("time", min_count=1)


# ---------------------------------------------------------------- 1. 2026 so far
def status_2026():
    wins = [("1 Mar-31 May 2026 (first rains)", 3, 1, 5, 31), ("1 Jun-31 Aug 2026", 6, 1, 8, 31),
            (f"1 Sep-{LAST:%d %b} 2026 (second rains so far)", 9, 1, LAST.month, LAST.day)]
    fig, axs = plt.subplots(2, 3, figsize=(12, 8.2))
    rows = []
    for k, (name, m0, d0, m1, d1) in enumerate(wins):
        hist = xr.concat([window_total(pr_all, y, m0, d0, m1, d1) for y in YEARS], pd.Index(YEARS, name="year"))
        now = window_total(pr_all, 2026, m0, d0, m1, d1)
        pct = 100 * now / hist.sel(year=slice(*BASE)).mean("year")
        rank = (hist < now).sum("year") / hist.count("year") * 100
        ax = axs[0, k]
        im = ax.pcolormesh(pct.lon, pct.lat, pct.where(z >= 0), cmap=CMAP_RAIN,
                           norm=BoundaryNorm([25, 50, 70, 85, 95, 105, 115, 130, 150, 200], 256, extend="both"),
                           shading="nearest")
        draw_borders(ax, UG_EXTENT)
        ax.set_title(f"{name}\n% of 1991-2020 average", fontsize=9)
        fig.colorbar(im, ax=ax, shrink=0.75, label="%")
        ax = axs[1, k]
        im2 = ax.pcolormesh(rank.lon, rank.lat, rank.where(z >= 0), cmap=CMAP_RAIN,
                            norm=BoundaryNorm([0, 10, 20, 33, 67, 80, 90, 100], 256), shading="nearest")
        draw_borders(ax, UG_EXTENT)
        ax.set_title("Percentile rank among 1981-2025", fontsize=9)
        fig.colorbar(im2, ax=ax, shrink=0.75, label="percentile (<33 = below normal)")
        zm_now, zm_h = zone_mean(now), zone_mean(hist)
        for n in zm_now.zone.values:
            h = zm_h.sel(zone=n)
            rows.append(dict(window=name, zone=n, mm_2026=float(zm_now.sel(zone=n)),
                             mean_1991_2020=float(h.sel(year=slice(*BASE)).mean()),
                             pct_of_normal=float(100 * zm_now.sel(zone=n) / h.sel(year=slice(*BASE)).mean()),
                             percentile=float((h < zm_now.sel(zone=n)).mean() * 100)))
    fig.suptitle(f"How wet has 2026 been? CHIRPS (final to {last_final}, preliminary to {LAST:%d %b %Y})",
                 x=0.01, ha="left", fontweight="bold")
    save(fig, "fig14_2026_status_maps.png")
    df = pd.DataFrame(rows)
    df.round(1).to_csv(RES / "forecast_2026_status.csv", index=False)

    # cumulative second-season curves, 1 Aug - 31 Jan
    zm = zone_mean(pr_all)
    show = ["Uganda", "Lake Victoria crescent (Central-Busoga)", "West Nile-Lango-Teso-Elgon belt",
            "Karamoja (NE, semi-arid)"]
    analog = {1997: CAT[1], 2023: CAT[4], 2015: CAT[2], 2006: CAT[6]}
    fig, axs = plt.subplots(1, 4, figsize=(15, 4.2), sharex=True)
    for ax, n in zip(axs, show):
        curves = {}
        for y in list(YEARS[:-1]) + [2026]:
            s = zm.sel(zone=n, time=slice(f"{y}-08-01", f"{y + 1}-01-31")).values
            curves[y] = np.nancumsum(s)
        L = min(len(v) for k, v in curves.items() if k != 2026)
        H = np.array([curves[y][:L] for y in YEARS[:-1]])
        d = np.arange(L)
        ax.fill_between(d, np.percentile(H, 10, 0), np.percentile(H, 90, 0), color=GRID, label="1981-2024 10-90%")
        ax.plot(d, np.median(H, 0), color=MUTED, lw=1.5, label="median")
        for y, c in analog.items():
            ax.plot(d, curves[y][:L], color=c, lw=1.3, label=str(y))
        ax.plot(np.arange(len(curves[2026])), curves[2026], color=INK, lw=2.6, label="2026")
        ticks = pd.date_range("2001-08-01", "2002-01-01", freq="MS")
        ax.set_xticks([(t - pd.Timestamp("2001-08-01")).days for t in ticks])
        ax.set_xticklabels([t.strftime("%b") for t in ticks])
        ax.set_title(n, fontsize=8.5)
        ax.set_ylim(0)
    axs[0].set_ylabel("cumulative mm since 1 Aug")
    axs[0].legend(fontsize=7)
    fig.suptitle("Second-season rainfall accumulation: 2026 against climatology and El Nino analogue years",
                 x=0.01, ha="left", fontweight="bold")
    save(fig, "fig15_2026_cumulative.png")
    return df


# ---------------------------------------------------------------- 2. teleconnections
def ond_by_zone():
    mon = pr_all.resample(time="MS").sum(min_count=1)
    ond = mon.where(mon.time.dt.month.isin([10, 11, 12]), drop=True).groupby("time.year").sum(min_count=1)
    return ond.sel(year=YEARS), zone_mean(ond.sel(year=YEARS))


def idx_season(months, years=YEARS):
    d = indices()
    d = d[d.index.month.isin(months)]
    return d.groupby(d.index.year).mean().loc[years]


def teleconnections():
    ond, zm = ond_by_zone()
    son = idx_season([9, 10, 11])
    fig, axs = plt.subplots(1, 4, figsize=(13, 3.8))
    for ax, (col, title) in zip(axs, [("nino34", "Nino-3.4"), ("dmi", "Indian Ocean Dipole (DMI)"),
                                      ("wio", "West Indian Ocean pole"), ("eio", "East Indian Ocean pole")]):
        x = xr.DataArray(son[col].values, dims="year", coords={"year": YEARS})
        r = xr.corr(ond, x, "year")
        im = ax.pcolormesh(r.lon, r.lat, r.where(z >= 0), cmap=CMAP_RAIN, vmin=-0.8, vmax=0.8, shading="nearest")
        draw_borders(ax, UG_EXTENT)
        ax.set_title(f"OND rain vs SON {title}", fontsize=9)
    fig.colorbar(im, ax=axs, orientation="horizontal", fraction=0.05, pad=0.04, label="correlation 1981-2025 (|r|>0.29 significant)")
    save(fig, "fig16_teleconnection_maps.png")

    u = zm.sel(zone="Uganda").values
    an = 100 * (u / zm.sel(zone="Uganda", year=slice(*BASE)).mean().values - 1)
    rows = []
    for n in zm.zone.values:
        y = zm.sel(zone=n).values
        r_n = stats.pearsonr(son.nino34, y)[0]
        r_d = stats.pearsonr(son.dmi, y)[0]
        r_nd = stats.pearsonr(son.nino34, son.dmi)[0]
        partial_n = (r_n - r_d * r_nd) / np.sqrt((1 - r_d ** 2) * (1 - r_nd ** 2))
        partial_d = (r_d - r_n * r_nd) / np.sqrt((1 - r_n ** 2) * (1 - r_nd ** 2))
        rows.append(dict(zone=n, r_nino34=r_n, r_dmi=r_d, r_wio=stats.pearsonr(son.wio, y)[0],
                         r_eio=stats.pearsonr(son.eio, y)[0], partial_nino_given_dmi=partial_n,
                         partial_dmi_given_nino=partial_d))
    tc = pd.DataFrame(rows)
    tc.round(2).to_csv(RES / "forecast_teleconnections.csv", index=False)

    # scatter Uganda OND anomaly vs Nino3.4, colour by DMI
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    sc = ax.scatter(son.nino34, an, c=son.dmi, cmap=CMAP_RAIN, vmin=-1.2, vmax=1.2, s=55, edgecolor=INK, lw=0.4, zorder=3)
    for yy, xv, yv in zip(YEARS, son.nino34, an):
        if abs(xv) > 0.9 or abs(yv) > 30:
            ax.annotate(str(yy), (xv, yv), xytext=(4, 3), textcoords="offset points", fontsize=7.5)
    s26 = indices().loc["2026-09"]
    ax.axvline(float(s26.nino34.iloc[0]), color=INK2, ls="--", lw=1)
    ax.text(float(s26.nino34.iloc[0]) - 0.05, ax.get_ylim()[1] * 0.92, "Sep 2026\nNino-3.4", fontsize=7.5, color=INK2,
            ha="right")
    ax.axhline(0, color=MUTED, lw=0.8)
    fig.colorbar(sc, ax=ax, label="SON Indian Ocean Dipole index (°C)")
    ax.set_xlabel("SON Nino-3.4 anomaly (°C)")
    ax.set_ylabel("Uganda OND rainfall, % anomaly vs 1991-2020")
    ax.set_title("El Nino alone does not guarantee wet short rains: the Indian Ocean decides")
    save(fig, "fig17_enso_iod_scatter.png")

    # El Nino year table
    o = oni()
    ond_oni = o[o.index.month.isin([10, 11, 12])].groupby(o[o.index.month.isin([10, 11, 12])].index.year).mean()
    sept = xr.concat([window_total(zone_mean(pr_all).sel(zone="Uganda"), y, 9, 1, LAST.month, LAST.day)
                      for y in YEARS], pd.Index(YEARS, name="year"))
    sept_pct = 100 * sept / sept.sel(year=slice(*BASE)).mean()
    tab = pd.DataFrame({"ONI_OND": ond_oni.reindex(YEARS).values, "DMI_SON": son.dmi.values, "EIO_SON": son.eio.values,
                        "OND_pct_anom": an, f"Sep1-{LAST:%b%d}_pct_of_normal": sept_pct.values}, index=YEARS)
    tab.index.name = "year"
    tab.round(2).to_csv(RES / "forecast_year_table.csv")

    # forecasts of opportunity: outcome by event class
    q1, q2 = np.percentile(an[(YEARS >= BASE[0]) & (YEARS <= BASE[1])], [100 / 3, 200 / 3])
    cls = np.select([son.nino34.values >= 1.5, (son.dmi.values >= 0.6) & (son.nino34.values < 1.5),
                     (son.nino34.values >= 0.5) & (son.dmi.values < 0.6), son.nino34.values <= -0.5],
                    ["Strong El Nino (SON Nino3.4 >= 1.5)", "Positive IOD (DMI >= 0.6), not strong El Nino",
                     "Weak/moderate El Nino, no strong +IOD", "La Nina (Nino3.4 <= -0.5)"], "Neutral")
    opp = pd.DataFrame({"cls": cls, "an": an, "year": YEARS}).groupby("cls").agg(
        n=("an", "size"), mean_OND_anom_pct=("an", "mean"), min_pct=("an", "min"), max_pct=("an", "max"),
        share_upper_tercile=("an", lambda v: np.mean(v > q2)), share_lower_tercile=("an", lambda v: np.mean(v < q1)),
        years=("year", lambda v: " ".join(map(str, v))))
    opp.round(2).to_csv(RES / "forecast_opportunity.csv")
    print(opp.round(2).to_string())
    return tc, tab


# ---------------------------------------------------------------- 3. hindcast skill
def gauss_terciles(mu, sd, lo, hi):
    pb = stats.norm.cdf(lo, mu, sd)
    pa = 1 - stats.norm.cdf(hi, mu, sd)
    return np.column_stack([pb, 1 - pb - pa, pa])


def rpss(prob, obs_cat):
    o = np.eye(3)[obs_cat]
    rps = np.mean(np.sum((np.cumsum(prob, 1) - np.cumsum(o, 1)) ** 2, 1))
    clim = np.full_like(prob, 1 / 3)
    rps_c = np.mean(np.sum((np.cumsum(clim, 1) - np.cumsum(o, 1)) ** 2, 1))
    return 1 - rps / rps_c


def predictors(issue):
    d = indices()
    if issue == "mid-Aug (July SST)":
        X = d[d.index.month == 7].groupby(d[d.index.month == 7].index.year).mean()
        X = X.loc[list(YEARS) + [2026]]
        X = X.assign(rain_sep=np.nan)
    else:
        X = d[d.index.month == 9].groupby(d[d.index.month == 9].index.year).mean().loc[list(YEARS) + [2026]]
        sep = pr_all.where(pr_all.time.dt.month == 9, drop=True).groupby("time.year").sum(min_count=1)
        sep = zone_mean(sep)
        X = X.assign(rain_sep=np.nan)
        X.attrs["sep"] = sep
    return X


MODELS = {
    "ENSO only": ["nino34"],
    "ENSO + IOD (DMI)": ["nino34", "dmi"],
    "ENSO + IO poles": ["rnino34", "wio", "eio"],
    "Ridge (all SST + Sep rain)": ["nino34", "rnino34", "dmi", "wio", "eio", "trop", "rain_sep"],
    "LightGBM (all)": ["nino34", "rnino34", "dmi", "wio", "eio", "trop", "rain_sep"],
}


def fit_predict(name, Xtr, ytr, Xte):
    if name.startswith("Ridge"):
        m = RidgeCV(alphas=np.logspace(-2, 3, 30)).fit(Xtr, ytr)
    elif name.startswith("LightGBM"):
        import lightgbm as lgb
        m = lgb.LGBMRegressor(n_estimators=150, learning_rate=0.05, num_leaves=4, min_child_samples=5,
                              subsample=0.8, subsample_freq=1, verbose=-1, random_state=0).fit(Xtr, ytr)
    else:
        m = LinearRegression().fit(Xtr, ytr)
    return m.predict(Xte), m


def hindcast():
    ond, zm = ond_by_zone()
    rows, fc26 = [], []
    for issue in ("mid-Aug (July SST)", "early Oct (Sep SST + Sep rain)"):
        X = predictors(issue)
        for n in zm.zone.values:
            y = zm.sel(zone=n).values
            ym, ys = y[(YEARS >= BASE[0]) & (YEARS <= BASE[1])].mean(), y[(YEARS >= BASE[0]) & (YEARS <= BASE[1])].std()
            yz = (y - ym) / ys
            lo, hi = np.percentile(yz[(YEARS >= BASE[0]) & (YEARS <= BASE[1])], [100 / 3, 200 / 3])
            obs_cat = np.digitize(yz, [lo, hi])
            Xn = X.copy()
            if "Sep" in issue:
                sep = X.attrs["sep"].sel(zone=n)
                v = sep.sel(year=list(YEARS) + [2026]).values
                Xn["rain_sep"] = (v - v[:-1].mean()) / v[:-1].std()
            res = {"Climatology": (np.zeros_like(yz), None)}
            for mname, cols in MODELS.items():
                cols = [c for c in cols if Xn[c].notna().all()]
                pred = np.zeros_like(yz)
                for i in range(len(YEARS)):
                    tr = np.abs(np.arange(len(YEARS)) - i) > 1  # leave out year and neighbours
                    Xa = Xn.iloc[:-1][cols].values
                    pred[i] = fit_predict(mname, Xa[tr], yz[tr], Xa[i:i + 1])[0][0]
                p26, _ = fit_predict(mname, Xn.iloc[:-1][cols].values, yz, Xn.iloc[-1:][cols].values)
                res[mname] = (pred, p26[0])
            for mname, (pred, p26) in res.items():
                resid_sd = np.sqrt(np.mean((yz - pred) ** 2))
                prob = gauss_terciles(pred, resid_sd, lo, hi)
                r = stats.pearsonr(pred, yz)[0] if np.std(pred) > 0 else 0.0
                rows.append(dict(issue=issue, zone=n, model=mname, r=r, msess=1 - np.mean((yz - pred) ** 2) / np.mean(yz ** 2),
                                 rpss=rpss(prob, obs_cat), hit_rate=np.mean(prob.argmax(1) == obs_cat)))
                if p26 is not None:
                    pp = gauss_terciles(np.array([p26]), resid_sd, lo, hi)[0]
                    fc26.append(dict(issue=issue, zone=n, model=mname, z_2026=p26, mm_2026=ym + p26 * ys,
                                     pct_of_normal=100 * (ym + p26 * ys) / ym, p_below=pp[0], p_normal=pp[1],
                                     p_above=pp[2]))
    sk = pd.DataFrame(rows)
    sk.round(3).to_csv(RES / "forecast_skill.csv", index=False)
    fc = pd.DataFrame(fc26)
    fc.round(3).to_csv(RES / "forecast_2026_ond.csv", index=False)

    # skill figure (RPSS by model and issue time, zones as dots, Uganda as bar)
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.3), sharey=True)
    names = ["Climatology"] + list(MODELS)
    for ax, issue in zip(axs, sk.issue.unique()):
        s = sk[sk.issue == issue]
        for i, m in enumerate(names):
            u = s[(s.model == m) & (s.zone == "Uganda")].rpss.values[0]
            ax.bar(i, u, color=BLUE[3] if u > 0 else RED[2], width=0.6)
            zz = s[(s.model == m) & (s.zone != "Uganda")].rpss.values
            ax.scatter(np.full(len(zz), i) + np.linspace(-0.2, 0.2, len(zz)), zz, s=12, color=INK2, zorder=3)
        ax.axhline(0, color=INK, lw=0.8)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=25, ha="right", fontsize=8)
        ax.set_title(f"Issued {issue}")
    axs[0].set_ylabel("RPSS vs climatology (cross-validated)\nbar = Uganda, dots = zones")
    fig.suptitle("Hindcast skill of OND tercile forecasts, 1981-2025", x=0.01, ha="left", fontweight="bold")
    save(fig, "fig18_forecast_skill.png")
    return sk, fc


def outlook_map(fc):
    best = fc[(fc.issue.str.startswith("early")) & (fc.model == "ENSO + IO poles")].set_index("zone")
    fig, ax = plt.subplots(figsize=(6, 6))
    zz = z.where(z >= 0)
    from common import zone_names
    nm = zone_names()
    val = xr.full_like(zz, np.nan)
    for k, n in nm.items():
        val = xr.where(z == k, best.loc[n, "p_above"] - best.loc[n, "p_below"], val)
    im = ax.pcolormesh(val.lon, val.lat, val, cmap=CMAP_RAIN, vmin=-0.5, vmax=0.5, shading="nearest")
    draw_borders(ax, UG_EXTENT)
    for k, n in nm.items():
        la = float(z.lat.where(z == k).mean())
        lo = float(z.lon.where(z == k).mean())
        r = best.loc[n]
        ax.text(lo, la, f"B {r.p_below:.0%}\nN {r.p_normal:.0%}\nA {r.p_above:.0%}", fontsize=7, ha="center",
                va="center", zorder=8, bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.5))
    fig.colorbar(im, ax=ax, shrink=0.7, label="P(above) - P(below)")
    ax.set_title("Statistical OND 2026 outlook (issued early Oct)\nENSO + Indian Ocean poles model", fontsize=9)
    save(fig, "fig19_ond2026_outlook.png")


if __name__ == "__main__":
    st = status_2026()
    print(st.round(1).to_string())
    tc, tab = teleconnections()
    print(tc.round(2).to_string())
    print(tab[tab.ONI_OND >= 0.8].round(2).to_string())
    sk, fc = hindcast()
    print(sk[sk.zone == "Uganda"].round(2).to_string())
    print(fc[fc.zone == "Uganda"].round(2).to_string())
    outlook_map(fc)
