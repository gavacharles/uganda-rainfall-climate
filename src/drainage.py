"""Design rainfall for urban / road drainage: return levels, non-stationarity and IDF curves.

Annual maximum 1-day rainfall (CHIRPS 0.25 deg, areal ~770 km2) -> GEV fitted by L-moments (Hosking 1990) per cell
for 1981-2025, 1981-2003 and 2004-2025. CHIRPS smooths point extremes, so return levels are converted to
gauge-equivalent point depths with a factor CF(T) = median over 7 GHCN-Daily Uganda gauges (Gulu, Masindi, Kasese,
Jinja, Tororo, Mbarara, Kabale; 19-57 complete years, 1926-1986) of gauge GEV return level / CHIRPS GEV return level
at the same cell. Final designs should still use UNMA's full gauge archive; relative changes are the robust result.
Sub-daily depths: TRRL East African ratio R_t = R_24 * (t/24) * ((24 + b)/(t + b))**n with b = 0.33 h, n = 0.96
(Fiddes, Forsgate & Grigg 1974, TRRL LR 623; as adopted for Uganda road drainage design).
Future: Clausius-Clapeyron scaling of 7 % per degC applied to CMIP6 median Uganda warming.

Outputs: figures fig29 (return-level maps & change), fig30 (town IDF + AMS); results/drainage_towns.csv,
         results/drainage_idf_kampala.csv
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap

from common import (ROOT, BLUE, CAT, CMAP_RAIN, CMAP_SEQ, INK, INK2, MUTED, PROC, RED, RES, TOWNS, UG_EXTENT, Y0, Y1,
                    draw_borders, save, series_trend, zones)

T = np.array([2, 5, 10, 25, 50, 100])
CC = 0.07
DUR_H = np.array([10 / 60, 0.25, 0.5, 1, 2, 3, 6, 12, 24])


def lmom_gev(x):
    """GEV parameters (xi, alpha, k; Hosking convention) from sample L-moments."""
    x = np.sort(x[np.isfinite(x)])
    n = len(x)
    if n < 15:
        return np.nan, np.nan, np.nan
    j = np.arange(n)
    b0 = x.mean()
    b1 = np.sum(j / (n - 1) * x) / n
    b2 = np.sum(j * (j - 1) / ((n - 1) * (n - 2)) * x) / n
    l1, l2, l3 = b0, 2 * b1 - b0, 6 * b2 - 6 * b1 + b0
    t3 = l3 / l2
    c = 2 / (3 + t3) - np.log(2) / np.log(3)
    k = 7.8590 * c + 2.9554 * c ** 2
    from math import gamma
    alpha = l2 * k / ((1 - 2 ** (-k)) * gamma(1 + k))
    xi = l1 - alpha * (1 - gamma(1 + k)) / k
    return xi, alpha, k


def gev_q(params, T):
    xi, a, k = params
    F = 1 - 1 / np.asarray(T, float)
    return xi + a / k * (1 - (-np.log(F)) ** k)


def return_levels(ams, years):
    sub = ams.sel(year=slice(*years))
    out = np.full((len(T),) + sub.shape[1:], np.nan)
    for i in range(sub.shape[1]):
        for j in range(sub.shape[2]):
            p = lmom_gev(sub.values[:, i, j])
            if np.isfinite(p[0]):
                out[:, i, j] = gev_q(p, T)
    return xr.DataArray(out, dims=("T", "lat", "lon"), coords={"T": T, "lat": ams.lat, "lon": ams.lon})


def gauge_calibration(ams):
    """CF(T) = gauge / CHIRPS return-level ratio, median over GHCN-Daily stations."""
    st = pd.read_fwf(ROOT / "data" / "raw" / "ghcnd" / "stations_ug.txt", header=None,
                     colspecs=[(0, 11), (12, 20), (21, 30), (31, 37), (41, 71)], names=["id", "lat", "lon", "elev", "name"])
    rows = []
    for r in st.itertuples():
        d = pd.read_csv(ROOT / "data" / "raw" / "ghcnd" / f"{r.id}.csv.gz", header=None, usecols=[1, 2, 3, 5],
                        names=["date", "el", "v", "q"])
        d = d[(d.el == "PRCP") & d.q.isna()]
        d["year"] = d.date // 10000
        g = d.groupby("year").v.agg(["count", "max"])
        g = g[g["count"] >= 330]["max"] / 10
        if len(g) < 15:
            continue
        qg = gev_q(lmom_gev(g.values), T)
        qc = gev_q(lmom_gev(ams.sel(lat=r.lat, lon=r.lon, method="nearest").values), T)
        row = dict(station=r.name.strip().title(), lat=r.lat, lon=r.lon, years=len(g), first=int(g.index.min()),
                   last=int(g.index.max()))
        for Tv, a, b in zip(T, qg, qc):
            row[f"gauge_{Tv}yr"], row[f"chirps_{Tv}yr"], row[f"ratio_{Tv}yr"] = a, b, a / b
        rows.append(row)
    df = pd.DataFrame(rows)
    df.round(2).to_csv(RES / "drainage_gauge_calibration.csv", index=False)
    return xr.DataArray([df[f"ratio_{Tv}yr"].median() for Tv in T], dims="T", coords={"T": T}), df


def trrl(r24, t_h, b=0.33, n=0.96):
    return r24 * (t_h / 24) * ((24 + b) / (t_h + b)) ** n


def warming():
    f = RES / "cmip6_uganda_changes.csv"
    if not f.exists():
        return {}
    c = pd.read_csv(f)
    c = c[c.variable == "tas"]
    return {(r.scenario, r.period): r.median for r in c.itertuples()}


def main():
    z = zones()
    ams = xr.open_dataarray(PROC / "rx1day_annual.nc").load()
    ams = ams.rename(group="year") if "group" in ams.dims else ams
    rl_all = return_levels(ams, (Y0, Y1))
    rl_a = return_levels(ams, (1981, 2003))
    rl_b = return_levels(ams, (2004, 2025))
    xr.Dataset({"rl_1981_2025": rl_all, "rl_1981_2003": rl_a, "rl_2004_2025": rl_b}).to_netcdf(PROC / "return_levels.nc")
    dw = warming()
    CF, cal = gauge_calibration(ams)
    print(cal.round(2).to_string())
    print("calibration factors", CF.values.round(2))

    fig, axs = plt.subplots(1, 4, figsize=(15, 4.5))
    cm = LinearSegmentedColormap.from_list("b", ["#f4f8fd"] + BLUE)
    for ax, Tv, lab in ((axs[0], 10, "a"), (axs[1], 50, "b")):
        v = rl_all.sel(T=Tv).where(z >= 0) * CF.sel(T=Tv)
        im = ax.pcolormesh(v.lon, v.lat, v, cmap=cm, vmin=60, vmax=110 if Tv == 10 else 150, shading="nearest")
        fig.colorbar(im, ax=ax, shrink=0.7, label="mm in 1 day (gauge-calibrated)")
        ax.set_title(f"{lab}  {Tv}-year 1-day rainfall, 1981-2025", fontsize=9)
    for ax, Tv, lab in ((axs[2], 10, "c"), (axs[3], 50, "d")):
        r = 100 * (rl_b.sel(T=Tv) / rl_a.sel(T=Tv) - 1)
        im = ax.pcolormesh(r.lon, r.lat, r.where(z >= 0), cmap=CMAP_RAIN,
                           norm=BoundaryNorm([-30, -20, -10, -5, 5, 10, 20, 30], 256, extend="both"), shading="nearest")
        fig.colorbar(im, ax=ax, shrink=0.7, label="%")
        ax.set_title(f"{lab}  Change in {Tv}-year 1-day rainfall\n2004-2025 vs 1981-2003 (blue = heavier)", fontsize=9)
    for ax in axs:
        draw_borders(ax, UG_EXTENT)
        for t, (la, lo) in TOWNS.items():
            if t in ("Kampala", "Gulu", "Mbarara", "Arua", "Mbale", "Fort Portal", "Moroto"):
                ax.plot(lo, la, "o", ms=2.5, color=INK, zorder=8)
    fig.suptitle("Design storms: how big is the 1-day storm, and is it changing?", x=0.01, ha="left", fontweight="bold")
    save(fig, "fig29_design_rain_maps.png")

    rows = []
    for t, (la, lo) in TOWNS.items():
        cell = dict(lat=la, lon=lo, method="nearest")
        s = ams.sel(**cell)
        tr, p, _ = series_trend(s.values)
        r = dict(town=t, ams_mean_mm=float(s.mean()), ams_trend_pct_per_decade=100 * tr / float(s.mean()), ams_trend_p=p)
        for Tv in (2, 10, 25, 50, 100):
            r[f"R24_{Tv}yr_areal"] = float(rl_all.sel(T=Tv, **cell))
            r[f"R24_{Tv}yr_point"] = float(rl_all.sel(T=Tv, **cell) * CF.sel(T=Tv))
            r[f"I_1h_{Tv}yr_mm_per_h"] = trrl(r[f"R24_{Tv}yr_point"], 1.0)
        r["change_10yr_pct_2004_25_vs_1981_03"] = float(100 * (rl_b.sel(T=10, **cell) / rl_a.sel(T=10, **cell) - 1))
        r["change_50yr_pct_2004_25_vs_1981_03"] = float(100 * (rl_b.sel(T=50, **cell) / rl_a.sel(T=50, **cell) - 1))
        for (sc, per), d in dw.items():
            if per == "2041-2070":
                r[f"uplift_{sc}_2041_2070_pct"] = 100 * ((1 + CC) ** d - 1)
        rows.append(r)
    towns = pd.DataFrame(rows)
    towns.round(2).to_csv(RES / "drainage_towns.csv", index=False)

    # IDF for Kampala (present and 2041-2070)
    k = towns.set_index("town").loc["Kampala"]
    idf = []
    for Tv in (2, 5, 10, 25, 50, 100):
        r24 = float(rl_all.sel(T=Tv, lat=TOWNS["Kampala"][0], lon=TOWNS["Kampala"][1], method="nearest") * CF.sel(T=Tv))
        for d in DUR_H:
            row = dict(T=Tv, duration_min=d * 60, depth_mm=trrl(r24, d), intensity_mm_h=trrl(r24, d) / d)
            for (sc, per), w in dw.items():
                if per == "2041-2070":
                    row[f"intensity_{sc}_2041_2070"] = row["intensity_mm_h"] * (1 + CC) ** w
            idf.append(row)
    idf = pd.DataFrame(idf)
    idf.round(1).to_csv(RES / "drainage_idf_kampala.csv", index=False)

    fig, axs = plt.subplots(1, 2, figsize=(13, 4.6))
    ax = axs[0]
    cols = [BLUE[1], BLUE[2], BLUE[3], BLUE[4], BLUE[5], BLUE[6]]
    for c, Tv in zip(cols, (2, 5, 10, 25, 50, 100)):
        s = idf[idf["T"] == Tv]
        ax.plot(s.duration_min, s.intensity_mm_h, color=c, lw=1.8, label=f"{Tv}-yr")
        if "intensity_ssp585_2041_2070" in s and Tv in (10, 50):
            ax.plot(s.duration_min, s.intensity_ssp585_2041_2070, color=c, lw=1.4, ls="--")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks([10, 15, 30, 60, 120, 360, 720, 1440])
    ax.set_xticklabels(["10m", "15m", "30m", "1h", "2h", "6h", "12h", "24h"])
    ax.set_ylabel("intensity (mm/h)")
    ax.legend(fontsize=7.5, title="return period", title_fontsize=7.5)
    ax.set_title("a  Indicative IDF curves, Kampala (dashed: 10-/50-yr, SSP5-8.5 2041-2070)")
    ax = axs[1]
    for i, t in enumerate(["Kampala", "Mbale", "Gulu", "Mbarara"]):
        s = ams.sel(lat=TOWNS[t][0], lon=TOWNS[t][1], method="nearest")
        ax.plot(s.year, s, color=CAT[i], lw=1.4, label=t)
    ax.set_ylabel("annual maximum 1-day rainfall, areal (mm)")
    ax.legend(fontsize=8)
    ax.set_title("b  Annual maximum daily rainfall (CHIRPS cell), 1981-2025")
    save(fig, "fig30_idf_kampala.png")
    return towns, idf


if __name__ == "__main__":
    towns, idf = main()
    print(towns.round(1).to_string())
    print(idf[idf["T"].isin([10, 50])].round(1).to_string())
