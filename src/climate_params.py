"""Temperature, wind, humidity, radiation, soil moisture and evaporative demand: trends 1981-2025.

Sources: CPC daily Tmax/Tmin (0.5 deg, gauge-based), NASA POWER monthly (MERRA-2 based reanalysis, ~0.5 deg),
GHCN-CAMS monthly 2 m temperature (1 deg), CPC soil moisture (0.5 deg).
Reference evapotranspiration ET0 by FAO-56 Penman-Monteith from POWER monthly fields (solar radiation from 1984;
earlier months use the 1984-1993 monthly mean radiation).

Outputs: data/processed/power_clean.nc, data/processed/et0_monthly.nc,
         figures fig10 (temperature trend maps), fig11 (Uganda temperature series, 3 sources),
         fig12 (other parameters: Uganda series), fig13 (trend maps of wind, humidity, radiation, ET0, soil moisture)
         results/climate_params_trends.csv, results/temperature_extremes.csv
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import BoundaryNorm

from common import (BASE, BLUE, CAT, CMAP_RAIN, CMAP_TEMP, INK2, MUTED, PROC, RES, UG_EXTENT, Y0, Y1, draw_borders,
                    grid_mask, save, series_trend, stipple, trend_da, uganda)


def power():
    """Monthly means of daily POWER fields (+ wind extremes from daily maxima)."""
    f = PROC / "power_clean.nc"
    if f.exists():
        return xr.open_dataset(f).load()
    raw = xr.open_dataset(PROC / "power_daily.nc").load()
    # variables come on different native grids (MERRA-2 0.5x0.625; radiation 1x1): put all on one 0.5 deg grid
    lat, lon = np.arange(-1.5, 4.51, 0.5), np.arange(29.5, 35.01, 0.5)
    d = xr.Dataset()
    for v in raw.data_vars:
        a = raw[v].dropna("lat", how="all").dropna("lon", how="all")
        a = a.assign_coords(lat=np.round(a.lat.values, 4))
        d[v] = a.interp(lat=lat, lon=lon, method="linear", kwargs={"fill_value": None})
    ds = d.drop_vars("WS10M_MAX").resample(time="MS").mean()
    ds["WS10M_MAX"] = d.WS10M_MAX.resample(time="MS").mean()
    ds["WS10M_MAX_month"] = d.WS10M_MAX.resample(time="MS").max()
    p95 = d.WS10M_MAX.sel(time=slice(f"{BASE[0]}", f"{BASE[1]}")).quantile(0.95, "time")
    ds["windy_days"] = (d.WS10M_MAX > p95).resample(time="MS").sum()
    rs = ds["ALLSKY_SFC_SW_DWN"]
    clim = rs.sel(time=slice("1984", "1993")).groupby("time.month").mean()
    ds["ALLSKY_SFC_SW_DWN"] = rs.fillna(clim.sel(month=rs.time.dt.month).drop_vars("month"))
    ds["mask"] = grid_mask(ds.lat, ds.lon, exclude_lakes=True)
    ds.to_netcdf(f)
    return ds


def et0_pm(ds):
    """FAO-56 Penman-Monteith reference ET (mm/month) from monthly means."""
    tx, tn = ds.T2M_MAX, ds.T2M_MIN
    tm = (tx + tn) / 2
    u2 = ds.WS2M
    rs = ds.ALLSKY_SFC_SW_DWN  # MJ/m2/day in the POWER regional NetCDF
    P = ds.PS  # kPa
    es = lambda T: 0.6108 * np.exp(17.27 * T / (T + 237.3))
    esat = (es(tx) + es(tn)) / 2
    ea = es(ds.T2MDEW)
    delta = 4098 * es(tm) / (tm + 237.3) ** 2
    gamma = 0.000665 * P
    # extraterrestrial and clear-sky radiation
    lat = np.deg2rad(ds.lat)
    J = ds.time.dt.dayofyear + 14
    dr = 1 + 0.033 * np.cos(2 * np.pi / 365 * J)
    dec = 0.409 * np.sin(2 * np.pi / 365 * J - 1.39)
    ws = np.arccos(-np.tan(lat) * np.tan(dec))
    Ra = 24 * 60 / np.pi * 0.082 * dr * (ws * np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.sin(ws))
    z = 1100.0
    rso = (0.75 + 2e-5 * z) * Ra
    rns = 0.77 * rs
    sig = 4.903e-9
    rnl = sig * ((tx + 273.16) ** 4 + (tn + 273.16) ** 4) / 2 * (0.34 - 0.14 * np.sqrt(ea)) * (1.35 * (rs / rso).clip(max=1) - 0.35)
    rn = rns - rnl
    et0 = (0.408 * delta * rn + gamma * 900 / (tm + 273) * u2 * (esat - ea)) / (delta + gamma * (1 + 0.34 * u2))
    return (et0 * ds.time.dt.days_in_month).rename("et0"), (esat - ea).rename("vpd")


def annual(da, how="mean"):
    da = da.sel(time=slice(f"{Y0}", f"{Y1}"))
    g = da.groupby("time.year")
    return g.mean() if how == "mean" else g.sum(min_count=12)


def area_mean(da, mask):
    w = np.cos(np.deg2rad(da.lat)) * xr.ones_like(mask)
    return da.where(mask).weighted(w.where(mask, 0)).mean(("lat", "lon"))


def cpc():
    ds = xr.open_dataset(PROC / "cpc_uganda_daily.nc").load()
    ds = ds.sel(time=slice(f"{Y0}", f"{Y1}"))
    m = grid_mask(ds.lat, ds.lon, exclude_lakes=False)
    return ds, m


def temperature(pw):
    rows = []
    ds, m = cpc()
    pm = pw.mask.astype(bool)
    gc = xr.open_dataset(PROC / "ghcncams_monthly_1deg.nc")["tas"].sel(lat=slice(-5, 8), lon=slice(27, 38)).load()
    gm = grid_mask(gc.lat, gc.lon, exclude_lakes=False)
    fields = {
        "CPC Tmax": annual(ds.tmax).where(m), "CPC Tmin": annual(ds.tmin).where(m),
        "POWER Tmax": annual(pw.T2M_MAX).where(pm), "POWER Tmin": annual(pw.T2M_MIN).where(pm),
        "GHCN-CAMS Tmean": annual(gc).where(gm),
    }
    fig, axs = plt.subplots(1, 5, figsize=(14, 3.6))
    lev = [-0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5]
    for ax, (name, da) in zip(axs, fields.items()):
        s, p = trend_da(da)
        im = ax.pcolormesh(s.lon, s.lat, s, cmap=CMAP_TEMP, norm=BoundaryNorm(lev, 256, extend="both"), shading="nearest")
        stipple(ax, p.where(s.notnull()), s.lon, s.lat, s=3)
        draw_borders(ax, UG_EXTENT)
        ax.set_title(name, fontsize=9)
    fig.colorbar(im, ax=axs, orientation="horizontal", fraction=0.05, pad=0.04,
                 label="Trend 1981-2025, °C per decade (dots: p<0.05)")
    fig.suptitle("Is Uganda getting hotter? Temperature trends from three independent datasets", x=0.01, ha="left",
                 fontweight="bold")
    save(fig, "fig10_temperature_trend_maps.png")

    ser = {
        "CPC (gauge) Tmax": area_mean(fields["CPC Tmax"], m), "CPC (gauge) Tmin": area_mean(fields["CPC Tmin"], m),
        "POWER/MERRA-2 Tmax": area_mean(fields["POWER Tmax"], pm), "POWER/MERRA-2 Tmin": area_mean(fields["POWER Tmin"], pm),
        "GHCN-CAMS Tmean": area_mean(fields["GHCN-CAMS Tmean"], gm),
    }
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.2), sharey=True)
    for i, (name, y) in enumerate(ser.items()):
        a = y - y.sel(year=slice(*BASE)).mean()
        ax = axs[0] if ("Tmax" in name or "Tmean" in name) else axs[1]
        if "Tmean" in name:
            axs[1].plot(a.year, a, color=CAT[i], lw=1.6, label=name)
        ax.plot(a.year, a, color=CAT[i], lw=1.6, label=name)
        s, p, _ = series_trend(y.values)
        rows.append(dict(variable=name, source=name.split()[0], mean_1991_2020=float(y.sel(year=slice(*BASE)).mean()),
                         trend_per_decade=s, p_value=p, units="°C",
                         change_1981_95_to_2011_25=float(y.sel(year=slice(2011, 2025)).mean() - y.sel(year=slice(1981, 1995)).mean())))
    for ax, t in zip(axs, ("Daytime maximum (and mean)", "Night-time minimum (and mean)")):
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_title(t)
        ax.legend(fontsize=7.5)
    axs[0].set_ylabel("anomaly vs 1991-2020 (°C)")
    save(fig, "fig11_temperature_series.png")

    # daily extremes from CPC: hot days (Tmax > calendar-day p90 of 1991-2020), warm nights, DTR
    base = ds.sel(time=slice(f"{BASE[0]}", f"{BASE[1]}"))
    doy = lambda d: d.time.dt.dayofyear.clip(max=365)
    erows = []
    for var, lab in (("tmax", "Hot days (TX90p, days/yr)"), ("tmin", "Warm nights (TN90p, days/yr)")):
        q = base[var].groupby(doy(base)).quantile(0.9, "time")
        q = q.pad(dayofyear=7, mode="wrap").rolling(dayofyear=15, center=True).mean().isel(dayofyear=slice(7, -7))
        exc = (ds[var].groupby(doy(ds)) > q).groupby("time.year").sum()
        y = area_mean(exc.where(m), m)
        s, p, _ = series_trend(y.values)
        erows.append(dict(index=lab, mean_1981_1995=float(y.sel(year=slice(1981, 1995)).mean()),
                          mean_2011_2025=float(y.sel(year=slice(2011, 2025)).mean()), trend_per_decade=s, p_value=p))
    dtr = area_mean(annual(ds.tmax - ds.tmin).where(m), m)
    s, p, _ = series_trend(dtr.values)
    erows.append(dict(index="Diurnal temperature range (°C)", mean_1981_1995=float(dtr.sel(year=slice(1981, 1995)).mean()),
                      mean_2011_2025=float(dtr.sel(year=slice(2011, 2025)).mean()), trend_per_decade=s, p_value=p))
    pd.DataFrame(erows).round(3).to_csv(RES / "temperature_extremes.csv", index=False)
    return rows


def others(pw):
    pm = pw.mask.astype(bool)
    et0, vpd = et0_pm(pw)
    xr.Dataset({"et0": et0, "vpd": vpd}).astype("float32").to_netcdf(PROC / "et0_monthly.nc")
    soil = xr.open_dataset(PROC / "cpcsoil_monthly.nc")["soilw"].load()
    sm_mask = grid_mask(soil.lat, soil.lon, exclude_lakes=False)
    vars_ = {
        "Wind speed at 2 m (m/s)": (annual(pw.WS2M), pm),
        "Daily max wind at 10 m (m/s, annual mean)": (annual(pw.WS10M_MAX), pm),
        "Strongest wind of the year at 10 m (m/s)": (pw.WS10M_MAX_month.sel(time=slice(f"{Y0}", f"{Y1}")).groupby("time.year").max(), pm),
        "Windy days (daily max wind > 1991-2020 p95, days/yr)": (annual(pw.windy_days, "sum"), pm),
        "Relative humidity (%)": (annual(pw.RH2M), pm),
        "Dew point (°C)": (annual(pw.T2MDEW), pm),
        "Solar radiation (MJ/m²/day)": (annual(pw.ALLSKY_SFC_SW_DWN.where(pw.time.dt.year >= 1984)), pm),
        "Vapour pressure deficit (kPa)": (annual(vpd), pm),
        "Reference evapotranspiration ET0 (mm/yr)": (annual(et0, "sum"), pm),
        "Soil moisture (mm, 1.6 m column)": (annual(soil), sm_mask),
    }
    rows = []
    fig, axs = plt.subplots(4, 3, figsize=(13, 11.5), sharex=True)
    for ax, (name, (da, mk)) in zip(axs.flat, vars_.items()):
        y = area_mean(da.where(mk), mk)
        y = y.where(np.isfinite(y), drop=True)
        s, p, b = series_trend(y.values)
        ax.plot(y.year, y, color=BLUE[3], lw=1.6)
        ax.plot(y.year, b + s / 10 * (y.year - y.year[0]), color=CAT[1], lw=1.4)
        ax.set_title(name, fontsize=8.5)
        ax.text(0.01, 0.03, f"trend {s:+.3g} per decade (p={p:.2f})", transform=ax.transAxes, fontsize=7.5, color=INK2)
        rows.append(dict(variable=name, source="CPC soil" if "Soil" in name else "NASA POWER",
                         mean_1991_2020=float(y.sel(year=slice(*BASE)).mean()), trend_per_decade=s, p_value=p,
                         units=name.split("(")[-1].rstrip(")"),
                         change_1981_95_to_2011_25=float(y.sel(year=slice(2011, 2025)).mean() - y.sel(year=slice(1981, 1995)).mean())))
    fig.suptitle("Other climate parameters, Uganda average 1981-2025", x=0.01, ha="left", fontweight="bold")
    save(fig, "fig12_other_params_series.png")

    fig, axs = plt.subplots(1, 5, figsize=(14, 3.5))
    for ax, name in zip(axs, ["Wind speed at 2 m (m/s)", "Relative humidity (%)", "Solar radiation (MJ/m²/day)",
                              "Reference evapotranspiration ET0 (mm/yr)", "Soil moisture (mm, 1.6 m column)"]):
        da, mk = vars_[name]
        da = da.where(da.year >= (1984 if "Solar" in name else Y0), drop=True).where(mk)
        s, p = trend_da(da)
        rel = 100 * s / da.sel(year=slice(*BASE)).mean("year")
        cmap = CMAP_RAIN.reversed() if "ET0" in name else CMAP_RAIN
        im = ax.pcolormesh(rel.lon, rel.lat, rel, cmap=cmap, norm=BoundaryNorm([-6, -4, -2, -1, -0.5, 0.5, 1, 2, 4, 6], 256,
                                                                                extend="both"), shading="nearest")
        stipple(ax, p.where(rel.notnull()), rel.lon, rel.lat, s=3)
        draw_borders(ax, UG_EXTENT)
        ax.set_title(name.split("(")[0], fontsize=9)
    fig.colorbar(im, ax=axs, orientation="horizontal", fraction=0.05, pad=0.04,
                 label="Trend, % of 1991-2020 mean per decade (ET0: red = more evaporative demand)")
    save(fig, "fig13_other_params_maps.png")
    return rows


if __name__ == "__main__":
    pw = power()
    rows = others(pw) + temperature(pw)
    df = pd.DataFrame(rows)
    df.round(4).to_csv(RES / "climate_params_trends.csv", index=False)
    print(df.round(3).to_string())
    print(pd.read_csv(RES / "temperature_extremes.csv").to_string())
