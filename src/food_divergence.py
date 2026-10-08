"""Why does vegetation show a first-season decline that satellite rainfall barely shows?

Panel of 44 VHP districts (Lake Victoria crescent excluded) x years 1982-2025 x season (S1: weeks 17-28, ~late
Apr-mid Jul; S2: weeks 43-52, ~late Oct-Dec). For each district-season:
  VCI, TCI (NOAA VHP, cropland), rainfall over the season plus the preceding month (CHIRPS), number of rain days,
  longest dry spell, mean Tmax, vapour-pressure deficit and ET0 (NASA POWER daily, MERRA-2).
Analyses: (1) Sen trends of each variable per district, summarised by season; (2) fixed-effects panel regression
VCI ~ year + climate covariates (district dummies), comparing the year coefficient with and without climate
controls: the share of the VCI trend that climate explains.

Outputs: results/fp_divergence_trends.csv, results/fp_divergence_panel.csv, figures/fp04_divergence.png
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapely
import statsmodels.formula.api as smf
import xarray as xr

from common import BLUE, CAT, INK, INK2, MUTED, ORANGE, PROC, RES, ROOT, save, series_trend

LVC = ["Kampala", "Wakiso", "Mukono", "Jinja", "Mayuge", "Masaka", "Mpigi", "Iganga", "Bugiri", "Busia", "Kayunga"]
SEAS = {"S1": dict(weeks=(17, 28), months=(3, 4, 5, 6, 7)), "S2": dict(weeks=(43, 52), months=(9, 10, 11, 12))}


def district_cells(lat, lon):
    g = gpd.read_file(ROOT / "data" / "raw" / "gadm" / "gadm41_UGA_1.json")
    LO, LA = np.meshgrid(lon, lat)
    return {r.NAME_1: shapely.contains_xy(r.geometry, LO, LA) for r in g.itertuples()}


def panel():
    v = pd.read_csv(PROC / "vhi_uganda_weekly.csv")
    v["district"] = v.province_id.map(pd.read_csv(PROC / "vhp_provinces.csv").set_index("province_id").name)
    v = v[~v.district.str.startswith("Lake") & ~v.district.isin(LVC)]
    pr = xr.open_dataset(PROC / "chirps_uganda_daily.nc")["precip"].sel(time=slice("1982", "2025")).load()
    pw = xr.open_dataset(PROC / "power_daily.nc").load()
    # POWER variables to a common grid (as in climate_params)
    lat, lon = np.arange(-1.5, 4.51, 0.5), np.arange(29.5, 35.01, 0.5)
    met = xr.Dataset()
    for var in ("T2M_MAX", "T2M_MIN", "T2MDEW"):
        a = pw[var].dropna("lat", how="all").dropna("lon", how="all")
        a = a.assign_coords(lat=np.round(a.lat.values, 4))
        met[var] = a.interp(lat=lat, lon=lon, method="linear", kwargs={"fill_value": None})
    es = lambda T: 0.6108 * np.exp(17.27 * T / (T + 237.3))
    met["vpd"] = (es(met.T2M_MAX) + es(met.T2M_MIN)) / 2 - es(met.T2MDEW)
    et0 = xr.open_dataset(PROC / "et0_monthly.nc")["et0"].load()
    dc_p = district_cells(pr.lat.values, pr.lon.values)
    dc_m = district_cells(lat, lon)
    rows = []
    for s, cfg in SEAS.items():
        vv = v[(v.week >= cfg["weeks"][0]) & (v.week <= cfg["weeks"][1])].groupby(["district", "year"])[["VCI", "TCI"]].mean()
        mp = pr.where(pr.time.dt.month.isin(cfg["months"]), drop=True)
        mm = met.where(met.time.dt.month.isin(cfg["months"]), drop=True)
        me = et0.where(et0.time.dt.month.isin(cfg["months"]), drop=True)
        for d in vv.index.get_level_values(0).unique():
            if d not in dc_p or dc_p[d].sum() == 0:
                continue
            mk = xr.DataArray(dc_p[d], dims=("lat", "lon"))
            r = mp.where(mk).mean(("lat", "lon"))
            mkm = dc_m[d] if dc_m[d].sum() else None
            if mkm is None:  # small district: nearest met cell to its rain cells
                la0 = float(pr.lat.values[np.where(dc_p[d])[0]].mean())
                lo0 = float(pr.lon.values[np.where(dc_p[d])[1]].mean())
                mkm = np.zeros((len(lat), len(lon)), bool)
                mkm[np.abs(lat - la0).argmin(), np.abs(lon - lo0).argmin()] = True
            mkm = xr.DataArray(mkm, dims=("lat", "lon"), coords={"lat": lat, "lon": lon})
            mt = mm.where(mkm).mean(("lat", "lon"))
            ee = me.interp(lat=lat, lon=lon, method="nearest", kwargs={"fill_value": None}).where(mkm).mean(("lat", "lon"))
            for y in range(1982, 2026):
                ry = r.sel(time=str(y)).values if s == "S1" else r.sel(time=str(y)).values
                if ry.size < 60 or y not in vv.loc[d].index:
                    continue
                dry = (ry < 1).astype(int)
                run, best = 0, 0
                for x in dry:
                    run = run + 1 if x else 0
                    best = max(best, run)
                rows.append(dict(season=s, district=d, year=y, VCI=vv.loc[(d, y), "VCI"], TCI=vv.loc[(d, y), "TCI"],
                                 rain=float(np.nansum(ry)), raindays=int((ry >= 1).sum()), maxdry=best,
                                 tmax=float(mt.T2M_MAX.sel(time=str(y)).mean()), vpd=float(mt.vpd.sel(time=str(y)).mean()),
                                 et0=float(ee.sel(time=str(y)).sum())))
    df = pd.DataFrame(rows).dropna()
    df.to_csv(RES / "fp_divergence_panel.csv", index=False)
    return df


def analyse(df):
    trows, prows = [], []
    vars_ = ["VCI", "TCI", "rain", "raindays", "maxdry", "tmax", "vpd", "et0"]
    for s in ("S1", "S2"):
        d = df[df.season == s]
        for var in vars_:
            tr = []
            for dist, g in d.groupby("district"):
                g = g.sort_values("year")
                if len(g) > 25 and g[var].std() > 0:
                    t, p, _ = series_trend(g[var].values)
                    tr.append((t, p))
            tr = np.array(tr)
            mean = d[var].mean()
            trows.append(dict(season=s, variable=var, districts=len(tr), median_trend_per_decade=float(np.median(tr[:, 0])),
                              median_trend_pct_of_mean=float(100 * np.median(tr[:, 0]) / mean) if var not in ("tmax",) else np.nan,
                              share_sig_up=float(np.mean((tr[:, 1] < 0.05) & (tr[:, 0] > 0))),
                              share_sig_down=float(np.mean((tr[:, 1] < 0.05) & (tr[:, 0] < 0)))))
        z = d.copy()
        for c in ("rain", "raindays", "maxdry", "tmax", "vpd", "et0"):
            z[c] = (z[c] - z.groupby("district")[c].transform("mean")) / z[c].std()
        z["dec"] = (z.year - 2003.5) / 10
        m0 = smf.ols("VCI ~ dec + C(district)", z).fit(cov_type="cluster", cov_kwds={"groups": z.year})
        m1 = smf.ols("VCI ~ dec + rain + maxdry + raindays + C(district)", z).fit(cov_type="cluster", cov_kwds={"groups": z.year})
        m2 = smf.ols("VCI ~ dec + rain + maxdry + raindays + tmax + vpd + C(district)", z).fit(cov_type="cluster", cov_kwds={"groups": z.year})
        for name, m in (("trend only", m0), ("+ rainfall", m1), ("+ rainfall + heat", m2)):
            row = dict(season=s, model=name, trend_per_decade=m.params["dec"], trend_se=m.bse["dec"], trend_p=m.pvalues["dec"],
                       r2_within=m.rsquared, n=int(m.nobs))
            for c in ("rain", "maxdry", "raindays", "tmax", "vpd"):
                if c in m.params:
                    row[f"coef_{c}"] = m.params[c]
                    row[f"p_{c}"] = m.pvalues[c]
            prows.append(row)
    t = pd.DataFrame(trows)
    t.round(3).to_csv(RES / "fp_divergence_trends.csv", index=False)
    p = pd.DataFrame(prows)
    p.round(4).to_csv(RES / "fp_divergence_models.csv", index=False)
    return t, p


def figure(t, p):
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.6))
    ax = axs[0]
    show = [("rain", "rainfall"), ("raindays", "rain days"), ("maxdry", "longest dry spell"), ("vpd", "vapour-pressure deficit"),
            ("et0", "evaporative demand"), ("TCI", "thermal condition (TCI)"), ("VCI", "vegetation condition (VCI)")]
    y = np.arange(len(show))[::-1]
    for k, (s, c) in enumerate((("S1", ORANGE[4]), ("S2", BLUE[4]))):
        vals = [t[(t.season == s) & (t.variable == v)].median_trend_pct_of_mean.values[0] for v, _ in show]
        ax.barh(y + (0.18 if s == "S1" else -0.18), vals, 0.34, color=c, label="First season (Mar-Jul)" if s == "S1" else "Second season (Sep-Dec)")
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([l for _, l in show])
    ax.set_xlabel("median district trend, % of mean per decade")
    ax.set_title("a  What changed in each season, 1982-2025")
    ax.legend(fontsize=8, loc="lower right")
    ax = axs[1]
    models = ["trend only", "+ rainfall", "+ rainfall + heat"]
    for k, (s, c) in enumerate((("S1", ORANGE[4]), ("S2", BLUE[4]))):
        d = p[p.season == s].set_index("model").loc[models]
        x = np.arange(3) + (k - 0.5) * 0.3
        ax.errorbar(x, d.trend_per_decade, yerr=1.96 * d.trend_se, fmt="o", color=c, capsize=4, ms=7,
                    label="First season" if s == "S1" else "Second season")
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks(range(3))
    ax.set_xticklabels(models)
    ax.set_ylabel("VCI trend, points per decade (95% CI)")
    ax.set_title("b  Vegetation trend left after controlling for climate")
    ax.legend(fontsize=8)
    save(fig, "fp04_divergence.png")


if __name__ == "__main__":
    f = RES / "fp_divergence_panel.csv"
    df = pd.read_csv(f) if f.exists() else panel()
    t, p = analyse(df)
    figure(t, p)
    print(t.round(2).to_string())
    print(p.round(3).to_string())
