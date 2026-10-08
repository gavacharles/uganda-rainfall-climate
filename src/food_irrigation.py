"""Food security and irrigation: growing period, season failure, dry spells and irrigation water requirement.

Length of growing period (LGP, FAO): days per year with rainfall (31-day running mean) above 0.5 x ET0.
Season failure: seasonal rainfall (onset-cessation total, from seasons.nc) below 70 % of the cell's 1991-2020 mean,
or no detectable season. Damaging in-season dry spell: longest run of days < 1 mm >= 10 days.
Irrigation: net irrigation requirement NIR = sum over months of max(0, Kc*ET0 - Peff), with Peff by USDA-SCS from
(a) mean and (b) 80 %-dependable (20th percentile) monthly rainfall; Kc = 1.0 (year-round crop, e.g. vegetables,
banana, pasture) and a dry-season-only crop (Dec-Feb + Jun-Aug). Design duty (l/s/ha) = peak-month gross requirement
at 65 % field efficiency, 24 h/day supply. Future: CMIP6 median change factors (water.py), 2041-2070.

Outputs: figures fig27 (food security), fig28 (irrigation), results/food_zone.csv, results/irrigation_zone.csv,
         results/irrigation_district.csv
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap

from common import (BASE, BLUE, CMAP_RAIN, CMAP_SEQ, ORANGE, PROC, RES, UG_EXTENT, Y0, Y1, chirps, draw_borders,
                    save, series_trend, stipple, trend_da, zone_mean, zones)
from water import district_means, monthly_inputs

EFF = 0.65
CMAP_DEM = LinearSegmentedColormap.from_list("dem", ["#fdf3ec"] + ORANGE)


def peff(p):
    return xr.where(p < 250, p * (125 - 0.2 * p) / 125, 125 + 0.1 * p)


def lgp():
    pr = chirps()[0].sel(time=slice(f"{Y0}", f"{Y1}"))
    z = zones()
    et = xr.open_dataset(PROC / "et0_monthly.nc")["et0"].load()
    et_d = (et / et.time.dt.days_in_month).interp(lat=pr.lat, lon=pr.lon, method="linear", kwargs={"fill_value": None})
    et_d = et_d.reindex(time=pr.time, method="ffill")
    sm = pr.rolling(time=31, center=True, min_periods=15).mean()
    g = (sm > 0.5 * et_d).groupby("time.year").sum().where(z >= 0)
    return g


def food():
    z = zones()
    s = xr.open_dataset(PROC / "seasons.nc").load()
    L = lgp()
    rows = []
    out = {}
    for key, name in (("S1", "First rains"), ("S2", "Second rains"), ("U", "Unimodal season")):
        tot = s[f"{key}_total"]
        valid = tot.count("year") > 35
        mean = tot.sel(year=slice(*BASE)).mean("year")
        fail = ((tot < 0.7 * mean) | tot.isnull()).where(valid)
        dry = (s[f"{key}_maxdry"] >= 10).where(valid & tot.notnull())
        out[key] = dict(fail_early=100 * fail.sel(year=slice(1981, 2003)).mean("year"),
                        fail_late=100 * fail.sel(year=slice(2004, 2025)).mean("year"),
                        dry=100 * dry.mean("year"))
        for metric, da in (("P(failed season) 1981-2003 %", out[key]["fail_early"]),
                           ("P(failed season) 2004-2025 %", out[key]["fail_late"]),
                           ("P(dry spell >= 10 d in season) %", out[key]["dry"])):
            zm = zone_mean(da)
            for n in zm.zone.values:
                rows.append(dict(season=name, metric=metric, zone=n, value=float(zm.sel(zone=n))))
    sl, p = trend_da(L)
    zl = zone_mean(L)
    for n in zl.zone.values:
        t, pp, _ = series_trend(zl.sel(zone=n).values)
        rows.append(dict(season="Year", metric="LGP days 1991-2020", zone=n, value=float(zl.sel(zone=n, year=slice(*BASE)).mean())))
        rows.append(dict(season="Year", metric="LGP trend days/decade", zone=n, value=t, p_value=pp))
        rows.append(dict(season="Year", metric="LGP CV %", zone=n, value=float(100 * zl.sel(zone=n).std() / zl.sel(zone=n).mean())))
    df = pd.DataFrame(rows)
    df.round(2).to_csv(RES / "food_zone.csv", index=False)

    fig, axs = plt.subplots(2, 4, figsize=(15, 8.4))
    Lm = L.sel(year=slice(*BASE)).mean("year")
    im = axs[0, 0].pcolormesh(Lm.lon, Lm.lat, Lm, cmap=CMAP_SEQ, vmin=120, vmax=330, shading="nearest")
    fig.colorbar(im, ax=axs[0, 0], shrink=0.7, label="days")
    axs[0, 0].set_title("a  Length of growing period\n(P > 0.5 ET0), 1991-2020", fontsize=9)
    im = axs[0, 1].pcolormesh(sl.lon, sl.lat, sl, cmap=CMAP_RAIN, norm=BoundaryNorm([-15, -10, -5, -2, 2, 5, 10, 15], 256, extend="both"),
                              shading="nearest")
    stipple(axs[0, 1], p.where(sl.notnull()), sl.lon, sl.lat, s=1.5)
    fig.colorbar(im, ax=axs[0, 1], shrink=0.7, label="days/decade")
    axs[0, 1].set_title("b  LGP trend 1981-2025", fontsize=9)
    cv = 100 * L.std("year") / L.mean("year")
    im = axs[0, 2].pcolormesh(cv.lon, cv.lat, cv, cmap=CMAP_DEM, vmin=5, vmax=35, shading="nearest")
    fig.colorbar(im, ax=axs[0, 2], shrink=0.7, label="%")
    axs[0, 2].set_title("c  Year-to-year variability of LGP\n(coefficient of variation)", fontsize=9)
    d = xr.concat([out[k]["dry"] for k in ("S1", "S2", "U")], "k").max("k")
    im = axs[0, 3].pcolormesh(d.lon, d.lat, d, cmap=CMAP_DEM, vmin=0, vmax=60, shading="nearest")
    fig.colorbar(im, ax=axs[0, 3], shrink=0.7, label="% of seasons")
    axs[0, 3].set_title("d  Chance of a >= 10-day dry spell\ninside the rainy season (worst season)", fontsize=9)
    for j, (k, name) in enumerate((("S1", "First rains"), ("S2", "Second rains"), ("U", "Unimodal season"))):
        ax = axs[1, j]
        fl = out[k]["fail_late"]
        im = ax.pcolormesh(fl.lon, fl.lat, fl, cmap=CMAP_DEM, vmin=0, vmax=40, shading="nearest")
        fig.colorbar(im, ax=ax, shrink=0.7, label="% of years")
        ax.set_title(f"{'efg'[j]}  {name}: chance of failed season\n(total < 70% of mean), 2004-2025", fontsize=9)
    ch = xr.concat([out[k]["fail_late"] - out[k]["fail_early"] for k in ("S1", "S2", "U")], "k").mean("k")
    im = axs[1, 3].pcolormesh(ch.lon, ch.lat, ch, cmap=CMAP_RAIN.reversed(), vmin=-20, vmax=20, shading="nearest")
    fig.colorbar(im, ax=axs[1, 3], shrink=0.7, label="percentage points")
    axs[1, 3].set_title("h  Change in failed-season risk\n2004-2025 minus 1981-2003 (red = riskier)", fontsize=9)
    for ax in axs.flat:
        draw_borders(ax, UG_EXTENT)
    fig.suptitle("Food security: how reliable are the growing seasons?", x=0.01, ha="left", fontweight="bold")
    save(fig, "fig27_food_security.png")
    return df


def irrigation():
    pr, et, z = monthly_inputs()
    base = slice(f"{BASE[0]}", f"{BASE[1]}")
    Pm = pr.sel(time=base).groupby("time.month").mean()
    P80 = pr.sel(time=base).groupby("time.month").quantile(0.2, "time")
    Em = et.sel(time=base).groupby("time.month").mean()
    dry_season = xr.DataArray([m in (12, 1, 2, 6, 7, 8) for m in range(1, 13)], dims="month", coords={"month": range(1, 13)})
    res = {}

    def nir(P, E):
        return (E * 1.0 - peff(P)).clip(min=0)

    fut = {}
    f = PROC / "cmip6_deltas_obsgrid.nc"
    if f.exists():
        dd = xr.open_dataset(f).load()
        for scen in dd.scenario.values:
            dP, dT = dd.dP.sel(scenario=scen, drop=True), dd.dT.sel(scenario=scen, drop=True)
            fut[scen] = (P80 * (1 + dP), Em * (22 + dT + 17.8) / (22 + 17.8))
    res["NIR mean rain, year-round (mm/yr)"] = nir(Pm, Em).sum("month")
    res["NIR 80% dependable rain, year-round (mm/yr)"] = nir(P80, Em).sum("month")
    res["NIR 80% dependable, dry-season crop (mm/season-pair)"] = nir(P80, Em).where(dry_season).sum("month")
    peak = nir(P80, Em).max("month")
    days = 30.4
    res["Design duty, peak month (l/s/ha)"] = peak / EFF / (days * 86400) * 10_000
    for scen, (Pf, Ef) in fut.items():
        res[f"NIR 80% dependable, year-round {scen} 2041-2070 (mm/yr)"] = nir(Pf, Ef).sum("month")
        res[f"Design duty {scen} 2041-2070 (l/s/ha)"] = nir(Pf, Ef).max("month") / EFF / (days * 86400) * 10_000
    ds = xr.Dataset({k: v.where(z >= 0) for k, v in res.items()})
    rows = []
    zm = zone_mean(ds)
    for n in zm.zone.values:
        r = {"zone": n}
        for k in ds.data_vars:
            r[k] = float(zm[k].sel(zone=n))
        rows.append(r)
    pd.DataFrame(rows).round(2).to_csv(RES / "irrigation_zone.csv", index=False)
    _, dist = district_means({k: ds[k].values for k in ds.data_vars}, ds.lat.values, ds.lon.values)
    dist.round(2).to_csv(RES / "irrigation_district.csv", index=False)

    n = 4 if fut else 3
    fig, axs = plt.subplots(1, n, figsize=(4 * n + 1, 4.6))
    panels = [("NIR 80% dependable rain, year-round (mm/yr)", "a  Net irrigation requirement\n(80% dependable rain, Kc = 1)", CMAP_DEM, (0, 1200), "mm/yr"),
              ("NIR 80% dependable, dry-season crop (mm/season-pair)", "b  Dry-season crop (Dec-Feb + Jun-Aug)\nnet requirement", CMAP_DEM, (0, 900), "mm"),
              ("Design duty, peak month (l/s/ha)", "c  Design duty, peak month\n(65% efficiency, 24 h supply)", CMAP_DEM, (0.3, 1.0), "l/s/ha")]
    if fut:
        k45 = "NIR 80% dependable, year-round ssp245 2041-2070 (mm/yr)"
        ds["dNIR"] = 100 * (ds[k45] / ds["NIR 80% dependable rain, year-round (mm/yr)"] - 1)
        panels.append(("dNIR", "d  Change in requirement 2041-2070\nSSP2-4.5 (CMIP6 median)", CMAP_RAIN.reversed(), (-20, 20), "%"))
    for ax, (k, t, cmap, (vmin, vmax), lab) in zip(axs, panels):
        im = ax.pcolormesh(ds.lon, ds.lat, ds[k], cmap=cmap, vmin=vmin, vmax=vmax, shading="nearest")
        draw_borders(ax, UG_EXTENT)
        ax.set_title(t, fontsize=9)
        fig.colorbar(im, ax=ax, shrink=0.7, label=lab)
    fig.suptitle("Irrigation water requirement", x=0.01, ha="left", fontweight="bold")
    save(fig, "fig28_irrigation.png")
    return pd.DataFrame(rows)


if __name__ == "__main__":
    f = food()
    print(f[f.zone == "Uganda"].to_string())
    print(f[f.metric.str.startswith("LGP")].round(1).to_string())
    print(irrigation().round(2).T.to_string())
