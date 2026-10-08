"""Water scarcity now and in future: climatic water balance by grid cell and district.

Present (1991-2020): rainfall P (CHIRPS), reference evapotranspiration ET0 (FAO-56 Penman-Monteith, NASA POWER,
regridded to 0.25 deg), aridity index AI = P/ET0 (UNEP classes), annual water balance P-ET0, number of months with
P < 0.5 ET0 ('dry months'), and drought frequency: months with 12-month standardised water balance (SPEI-12 style,
empirical) below -1, 2011-2025 vs 1981-1995.

Future: CMIP6 (up to 16 models, r1i1p1f1) monthly change factors for 2041-2070 vs 1991-2020, SSP2-4.5 and SSP5-8.5:
P_future = P_obs x (1 + dP%), ET0_future = ET0_obs x (Tm + dT + 17.8)/(Tm + 17.8) (Hargreaves temperature
sensitivity, ~ +2.3 %/degC). Ensemble median and model agreement are reported.

Outputs: figures fig23-fig26, results/water_district.csv, results/cmip6_uganda_changes.csv,
         data/processed/water_balance.nc
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapely
import xarray as xr
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap

from common import (BASE, BLUE, CAT, CMAP_RAIN, CMAP_SEQ, CMAP_TEMP, INK, INK2, MUTED, ORANGE, PROC, RED, RES,
                    UG_EXTENT, Y0, Y1, chirps, draw_borders, grid_mask, save, zone_mean, zones)

AI_CLASSES = [0, 0.2, 0.5, 0.65, 0.8, 1.0, 5]
AI_NAMES = ["Arid", "Semi-arid", "Dry sub-humid", "Moist sub-humid", "Humid (0.8-1.0)", "Humid (>1.0)"]
AI_COLS = [ORANGE[5], ORANGE[3], ORANGE[1], BLUE[1], BLUE[3], BLUE[5]]
PERIOD = (2041, 2070)


def monthly_inputs():
    pr = chirps()[0].sel(time=slice(f"{Y0}", f"{Y1}")).resample(time="MS").sum()
    et = xr.open_dataset(PROC / "et0_monthly.nc")["et0"].load().sel(time=slice(f"{Y0}", f"{Y1}"))
    et = et.interp(lat=pr.lat, lon=pr.lon, method="linear").combine_first(
        et.interp(lat=pr.lat, lon=pr.lon, method="nearest", kwargs={"fill_value": "extrapolate"}))
    z = zones()
    return pr.where(z >= 0), et.where(z >= 0), z


def spei12(wb):
    """Empirical standardised 12-month water balance (rank -> normal quantile), per calendar month."""
    from scipy.stats import norm
    acc = wb.rolling(time=12).sum()
    out = xr.full_like(acc, np.nan)
    for m in range(1, 13):
        sel = acc.time.dt.month == m
        a = acc.where(sel, drop=True)
        r = a.rank("time") / (a.count("time") + 1)
        out.loc[dict(time=a.time)] = norm.ppf(r)
    return out


def districts():
    d = gpd.read_file(PROC / "uganda_adm2.geojson")
    d = d.to_crs(4326)
    return d


def district_means(fields, lat, lon):
    d = districts()
    lo, la = np.meshgrid(lon, lat)
    rows = []
    for _, r in d.iterrows():
        g = r.geometry
        m = shapely.contains_xy(g, lo, la)
        if not m.any():  # small district: nearest cell to centroid
            c = g.representative_point()
            i, j = np.abs(lat - c.y).argmin(), np.abs(lon - c.x).argmin()
            m = np.zeros_like(m)
            m[i, j] = True
        row = {"district": r.get("shapeName", r.iloc[0])}
        for k, f in fields.items():
            v = np.asarray(f)[m]
            row[k] = float(np.nanmean(v)) if np.isfinite(v).any() else np.nan
        rows.append(row)
    return d.assign(**pd.DataFrame(rows).drop(columns="district")), pd.DataFrame(rows)


def present():
    pr, et, z = monthly_inputs()
    base = slice(f"{BASE[0]}", f"{BASE[1]}")
    P = pr.sel(time=base).groupby("time.year").sum().mean("year")
    E = et.sel(time=base).groupby("time.year").sum().mean("year")
    Pm = pr.sel(time=base).groupby("time.month").mean()
    Em = et.sel(time=base).groupby("time.month").mean()
    dry = (Pm < 0.5 * Em).sum("month").where(z >= 0)
    ai = P / E
    wb = pr - et
    s = spei12(wb)
    d_early = (s.sel(time=slice("1981", "1995")) < -1).mean("time") * 100
    d_late = (s.sel(time=slice("2011", "2025")) < -1).mean("time") * 100
    ds = xr.Dataset({"P": P, "ET0": E, "AI": ai, "WB": P - E, "dry_months": dry, "drought_pct_1981_1995": d_early,
                     "drought_pct_2011_2025": d_late, "Pm": Pm, "Em": Em})
    ds.to_netcdf(PROC / "water_balance.nc")

    fig, axs = plt.subplots(2, 3, figsize=(13, 9))
    panels = [
        ("P", "a  Annual rainfall 1991-2020 (mm)", CMAP_SEQ, np.arange(600, 1801, 150)),
        ("ET0", "b  Evaporative demand ET0 (mm)", LinearSegmentedColormap.from_list("o", ["#fdf3ec"] + ORANGE), np.arange(1500, 2201, 100)),
        ("WB", "c  Water balance P - ET0 (mm)", CMAP_RAIN, np.arange(-1400, 1, 200)),
        ("AI", "d  Aridity index P/ET0 (UNEP class)", ListedColormap(AI_COLS), AI_CLASSES),
        ("dry_months", "e  Months with P < 0.5 x ET0", LinearSegmentedColormap.from_list("d", ["#f4f8fd"] + ORANGE), np.arange(-0.5, 8.6, 1)),
        ("dd", "f  Change in drought frequency\n(% of months SPEI-12 < -1, 2011-25 minus 1981-95)", CMAP_RAIN.reversed(),
         [-30, -20, -10, -5, 5, 10, 20, 30]),
    ]
    ds["dd"] = d_late - d_early
    for ax, (v, t, cmap, lev) in zip(axs.flat, panels):
        im = ax.pcolormesh(ds.lon, ds.lat, ds[v].where(z >= 0), cmap=cmap,
                           norm=BoundaryNorm(lev, cmap.N, extend="neither" if v in ("AI", "dry_months") else "both"),
                           shading="nearest")
        draw_borders(ax, UG_EXTENT)
        ax.set_title(t, fontsize=9)
        cb = fig.colorbar(im, ax=ax, shrink=0.75)
        if v == "AI":
            cb.set_ticks([(a + b) / 2 if b < 5 else 1.5 for a, b in zip(AI_CLASSES[:-1], AI_CLASSES[1:])])
            cb.set_ticklabels(AI_NAMES, fontsize=7)
            cb.ax.set_ylim(0, 2)
        if v == "dry_months":
            cb.set_ticks(range(0, 9))
    fig.suptitle("Where is Uganda water-scarce today? Climatic water balance, 1991-2020", x=0.01, ha="left",
                 fontweight="bold")
    save(fig, "fig23_water_balance_present.png")
    return ds


def cmip6_changes(ds_obs):
    f = PROC / "cmip6_ea_monthly.nc"
    cm = xr.open_dataset(f).load()
    base = cm.sel(time=slice(f"{BASE[0]}", f"{BASE[1]}")).groupby("time.month").mean()
    fut = cm.sel(time=slice(f"{PERIOD[0]}", f"{PERIOD[1]}")).groupby("time.month").mean()
    dP = (fut.pr / base.pr - 1).clip(-0.6, 1.5)  # model, scenario, month, lat, lon
    dT = fut.tas - base.tas
    # Uganda-mean series and table
    ug = grid_mask(cm.lat, cm.lon, exclude_lakes=False)
    w = np.cos(np.deg2rad(cm.lat))
    ann = cm.groupby("time.year").mean()
    ugs = ann.where(ug).weighted(w).mean(("lat", "lon"))
    rows = []
    for scen in cm.scenario.values:
        for per in ((2021, 2050), (2041, 2070), (2071, 2100)):
            for var in ("pr", "tas"):
                b = ugs[var].sel(scenario=scen, year=slice(*BASE)).mean("year")
                fv = ugs[var].sel(scenario=scen, year=slice(*per)).mean("year")
                ch = (100 * (fv / b - 1)) if var == "pr" else (fv - b)
                ch = ch.dropna("model")
                rows.append(dict(scenario=scen, period=f"{per[0]}-{per[1]}", variable=var,
                                 units="%" if var == "pr" else "°C", median=float(ch.median()),
                                 p10=float(ch.quantile(0.1)), p90=float(ch.quantile(0.9)), n_models=int(ch.size),
                                 share_models_wetter_or_warmer=float((ch > 0).mean())))
            for sname, months in (("MAM", [3, 4, 5]), ("OND", [10, 11, 12])):
                s = cm.pr.where(cm.time.dt.month.isin(months)).groupby("time.year").mean()
                s = s.where(ug).weighted(w).mean(("lat", "lon")).sel(scenario=scen)
                ch = 100 * (s.sel(year=slice(*PERIOD)).mean("year") / s.sel(year=slice(*BASE)).mean("year") - 1)
                ch = ch.dropna("model")
                rows.append(dict(scenario=scen, period=f"{PERIOD[0]}-{PERIOD[1]}", variable=f"pr_{sname}", units="%",
                                 median=float(ch.median()), p10=float(ch.quantile(0.1)), p90=float(ch.quantile(0.9)),
                                 n_models=int(ch.size), share_models_wetter_or_warmer=float((ch > 0).mean())))
    tab = pd.DataFrame(rows).drop_duplicates(["scenario", "period", "variable"])
    tab.round(2).to_csv(RES / "cmip6_uganda_changes.csv", index=False)

    # plume figure
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.3))
    obs_t = None
    for ax, var, lab in ((axs[0], "tas", "Temperature anomaly (°C)"), (axs[1], "pr", "Rainfall anomaly (%)")):
        for scen, c in (("ssp245", BLUE[4]), ("ssp585", RED[4])):
            s = ugs[var].sel(scenario=scen)
            b = s.sel(year=slice(*BASE)).mean("year")
            a = (s - b) if var == "tas" else 100 * (s / b - 1)
            a = a.rolling(year=11, center=True).mean()
            ax.fill_between(a.year, a.quantile(0.1, "model"), a.quantile(0.9, "model"), color=c, alpha=0.18, lw=0)
            ax.plot(a.year, a.median("model"), color=c, lw=2, label=f"CMIP6 {scen.upper()} median (10-90% shaded)")
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_ylabel(lab)
    # observed overlays
    pr, et, z = monthly_inputs()
    po = zone_mean(pr.groupby("time.year").sum()).sel(zone="Uganda")
    po = 100 * (po / po.sel(year=slice(*BASE)).mean() - 1)
    axs[1].plot(po.year, po.rolling(year=11, center=True).mean(), color=INK, lw=2, label="Observed CHIRPS (11-yr mean)")
    cpc = xr.open_dataset(PROC / "cpc_uganda_daily.nc")
    tmin = cpc.tmin.sel(time=slice(f"{Y0}", f"{Y1}")).groupby("time.year").mean()
    m = grid_mask(cpc.lat, cpc.lon, exclude_lakes=False)
    tmin = tmin.where(m).mean(("lat", "lon"))
    axs[0].plot(tmin.year, (tmin - tmin.sel(year=slice(*BASE)).mean()).rolling(year=11, center=True).mean(), color=INK,
                lw=2, label="Observed CPC Tmin (11-yr mean)")
    axs[0].legend(fontsize=7.5)
    axs[1].legend(fontsize=7.5)
    axs[0].set_title("a  Uganda temperature: observed and projected")
    axs[1].set_title("b  Uganda annual rainfall: observed and projected")
    save(fig, "fig26_cmip6_plumes.png")

    # map of projected changes (ensemble median), East Africa, SSP2-4.5
    fig, axs = plt.subplots(1, 4, figsize=(15, 4.3))
    for ax, (t, da, cmap, lev) in zip(axs, [
            ("Annual rainfall change (%)", 100 * (fut.pr.mean("month") / base.pr.mean("month") - 1), CMAP_RAIN, [-20, -10, -5, -2, 2, 5, 10, 20]),
            ("MAM rainfall change (%)", 100 * (fut.pr.sel(month=[3, 4, 5]).mean("month") / base.pr.sel(month=[3, 4, 5]).mean("month") - 1), CMAP_RAIN, [-20, -10, -5, -2, 2, 5, 10, 20]),
            ("OND rainfall change (%)", 100 * (fut.pr.sel(month=[10, 11, 12]).mean("month") / base.pr.sel(month=[10, 11, 12]).mean("month") - 1), CMAP_RAIN, [-20, -10, -5, -2, 2, 5, 10, 20]),
            ("Temperature change (°C)", dT.mean("month"), LinearSegmentedColormap.from_list("r", RED), [1, 1.25, 1.5, 1.75, 2, 2.25, 2.5])]):
        med = da.sel(scenario="ssp245").median("model")
        agree = (np.sign(da.sel(scenario="ssp245")) == np.sign(med)).mean("model")
        im = ax.pcolormesh(med.lon, med.lat, med, cmap=cmap, norm=BoundaryNorm(lev, cmap.N, extend="both"), shading="nearest")
        lo, la = np.meshgrid(med.lon, med.lat)
        hatch = (agree < 0.8).values
        ax.scatter(lo[hatch], la[hatch], marker="x", s=6, c=INK2, lw=0.5, zorder=7)
        from regional_global import outline
        outline(ax, (24, 43.5, -11.5, 11.5))
        ax.set_title(f"{t}\nSSP2-4.5, {PERIOD[0]}-{PERIOD[1]} vs 1991-2020", fontsize=8.5)
        fig.colorbar(im, ax=ax, shrink=0.7, orientation="horizontal", pad=0.03, ticks=lev[::2] if len(lev) > 6 else lev)
    fig.suptitle("CMIP6 ensemble-median projections (x = fewer than 80% of models agree on sign)", x=0.01, y=1.06,
                 ha="left", fontweight="bold")
    save(fig, "fig25_cmip6_change_maps.png")

    # save ensemble-median monthly change factors on the observation grid for other modules
    dd = xr.Dataset({"dP": dP.median("model"), "dT": dT.median("model"),
                     "dP_p10": dP.quantile(0.1, "model").drop_vars("quantile"), "dP_p90": dP.quantile(0.9, "model").drop_vars("quantile")})
    dd.interp(lat=ds_obs.lat, lon=ds_obs.lon, method="linear").to_netcdf(PROC / "cmip6_deltas_obsgrid.nc")
    # extreme-rain scaling: CMIP6 annual-max monthly rainfall is too coarse, so drainage uses Clausius-Clapeyron
    # (~7 %/degC) on the warming below; record the Uganda-mean warming per scenario/period
    # future water balance on obs grid
    out = {}
    for scen in cm.scenario.values:
        dPm = dP.sel(scenario=scen).median("model").interp(lat=ds_obs.lat, lon=ds_obs.lon, method="linear")
        dTm = dT.sel(scenario=scen).median("model").interp(lat=ds_obs.lat, lon=ds_obs.lon, method="linear")
        Tm = 22.0
        Pf = (ds_obs.Pm * (1 + dPm)).sum("month")
        Ef = (ds_obs.Em * (Tm + dTm + 17.8) / (Tm + 17.8)).sum("month")
        out[scen] = Pf / Ef
        out[scen + "_dP"] = 100 * (Pf / ds_obs.P - 1)
        out[scen + "_dE"] = 100 * (Ef / ds_obs.ET0 - 1)
        out[scen + "_dry_months"] = ((ds_obs.Pm * (1 + dPm)) < 0.5 * ds_obs.Em * (Tm + dTm + 17.8) / (Tm + 17.8)).sum("month")
    return tab, out


def district_maps(ds, fut):
    z = zones()
    fields = {"P_mm": ds.P.values, "ET0_mm": ds.ET0.values, "AI": ds.AI.values, "WB_mm": ds.WB.values,
              "dry_months": ds.dry_months.values, "drought_pct_1981_1995": ds.drought_pct_1981_1995.values,
              "drought_pct_2011_2025": ds.drought_pct_2011_2025.values}
    if fut:
        for s in ("ssp245", "ssp585"):
            fields[f"AI_{s}_2041_2070"] = fut[s].values
            fields[f"dP_pct_{s}"] = fut[s + "_dP"].values
            fields[f"dET0_pct_{s}"] = fut[s + "_dE"].values
            fields[f"dry_months_{s}"] = fut[s + "_dry_months"].values
    gdf, df = district_means({k: np.where(z.values >= 0, v, np.nan) for k, v in fields.items()},
                             ds.lat.values, ds.lon.values)
    cls = lambda a: pd.cut(a, AI_CLASSES, labels=AI_NAMES)
    df["AI_class_now"] = cls(df.AI)
    if fut:
        df["AI_class_ssp245"] = cls(df["AI_ssp245_2041_2070"])
        df["AI_class_ssp585"] = cls(df["AI_ssp585_2041_2070"])
    # simple scarcity score: 0-100 from AI (lower = scarcer), dry months and drought trend
    score = (100 * (1 - (df.AI.clip(0.3, 1.0) - 0.3) / 0.7) * 0.5 + 100 * df.dry_months.clip(0, 8) / 8 * 0.35 +
             np.clip((df.drought_pct_2011_2025 - df.drought_pct_1981_1995) * 2 + 50, 0, 100) * 0.15)
    df["scarcity_score_now"] = score
    gdf["scarcity_score_now"] = score.values
    df.sort_values("scarcity_score_now", ascending=False).round(3).to_csv(RES / "water_district.csv", index=False)

    ncol = 3 if fut else 1
    fig, axs = plt.subplots(1, ncol, figsize=(5 * ncol, 5.6))
    axs = np.atleast_1d(axs)
    gdf.plot(column="scarcity_score_now", ax=axs[0], cmap=ListedColormap(ORANGE), edgecolor="white", lw=0.25,
             vmin=10, vmax=80, legend=True, legend_kwds={"shrink": 0.6, "label": "score (higher = scarcer)"})
    axs[0].set_title("a  Climatic water-scarcity score by district,\npresent (aridity, dry months, drought trend)", fontsize=9)
    if fut:
        for ax, s, t in ((axs[1], "ssp245", "b"), (axs[2], "ssp585", "c")):
            gdf[f"dAI_{s}"] = 100 * (gdf[f"AI_{s}_2041_2070"] / gdf.AI - 1)
            gdf.plot(column=f"dAI_{s}", ax=ax, cmap=CMAP_RAIN, vmin=-15, vmax=15, edgecolor="white", lw=0.25, legend=True,
                     legend_kwds={"shrink": 0.6, "label": "% change in P/ET0 (red = drier)"})
            ax.set_title(f"{t}  Change in aridity index 2041-2070,\n{s.upper()} (CMIP6 median)", fontsize=9)
    for ax in axs:
        draw_borders(ax, UG_EXTENT)
    save(fig, "fig24_water_districts.png")
    return df


if __name__ == "__main__":
    ds = present()
    fut = None
    if (PROC / "cmip6_ea_monthly.nc").exists():
        tab, fut = cmip6_changes(ds)
        print(tab.to_string())
    df = district_maps(ds, fut)
    print(df.sort_values("scarcity_score_now", ascending=False).head(25).round(2).to_string())
    print(zone_mean(ds[["P", "ET0", "AI", "dry_months"]]).to_dataframe().round(2) if False else "")
