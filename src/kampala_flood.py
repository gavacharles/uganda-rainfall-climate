"""Rain or concrete? Attribution of the change in design runoff in Kampala's drainage catchments.

Rainfall: annual maximum 1-day rainfall (AMS) over Kampala from CHIRPS v2.0 (0.25 deg cell 0.25-0.5N,
32.5-32.75E) and ARC2 (0.1 deg cells over the city, mean of cell maxima), converted to gauge-equivalent point depths
with gauge/product GEV ratios CF(T) from 7 GHCN-Daily Ugandan gauges. Change tests: Mann-Kendall + Sen on AMS;
GEV (L-moments) return levels for 1981-2003 vs 2004-2025 with bootstrap intervals; non-stationary GEV with a
linear trend in location (likelihood-ratio test).
Land: impervious fraction per catchment and epoch (kampala_catchments.py).
Runoff: SCS curve number. CN = imp x 98 + (1 - imp) x CN_perv (open space, fair: HSG B 69 / C 79 / D 84).
Design storm of critical duration t_c (TRRL East African ratio from the 24-h depth). Lag by the SCS lag equation
(CN dependent, so paving also speeds runoff), t_c = lag / 0.6. Peak by the SCS triangular unit hydrograph,
q_p = 0.208 A Q / T_p, T_p = D/2 + lag, D = t_c.
Attribution: Shapley decomposition of the change in peak flow and runoff depth between
(rain 1981-2003, land 1992) and (rain 2004-2025, land 2014): land effect, rainfall effect (sum = total).
Uncertainty: 4000 Monte Carlo draws over AMS bootstrap, gauge calibration factor, soil group and impervious factor.

Outputs: results/kampala_rain_stats.csv, results/kampala_attribution.csv, results/kampala_attribution_mc.csv,
         figures/kp0*.png (Kampala), jb0*.png (Johannesburg). Run: python kampala_flood.py [kampala|johannesburg]
"""
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from scipy import optimize, stats

from common import BLUE, CAT, CMAP_RAIN, GRID, INK, INK2, MUTED, ORANGE, PROC, RED, RES, save, series_trend
from drainage import gev_q, lmom_gev, trrl

RNG = np.random.default_rng(42)
T = np.array([2, 10, 50])
EP1, EP2 = (1981, 2003), (2004, 2025)
LAND1, LAND2 = 1992, 2014  # mid-points of the rainfall epochs
CN_PERV = {"B": 69, "C": 79, "D": 84}
HSG_P = {"B": 0.2, "C": 0.5, "D": 0.3}
CITY = sys.argv[1] if len(sys.argv) > 1 and __name__ == "__main__" else "kampala"
CFG = {
    "kampala": dict(prefix="kp", chirps=("chirps_uganda_daily.nc", 0.375, 32.625),
                    arc2=("arc2_uganda_daily.nc", (0.2, 0.45), (32.5, 32.7)), zoom=13),
    "johannesburg": dict(prefix="jb", chirps=("johannesburg_chirps_daily.nc", -26.125, 28.125),
                         arc2=("johannesburg_arc2_daily.nc", (-26.3, -26.0), (27.9, 28.2)), zoom=11),
    "nairobi": dict(prefix="nb", chirps=("nairobi_chirps_daily.nc", -1.375, 36.875), centre=(-1.29, 36.82),
                    arc2=("nairobi_arc2_daily.nc", (-1.42, -1.17), (36.7, 36.95)), zoom=12),
    "dar_es_salaam": dict(prefix="ds", chirps=("dar_es_salaam_chirps_daily.nc", -6.875, 39.125), centre=(-6.80, 39.28),
                          arc2=("dar_es_salaam_arc2_daily.nc", (-6.95, -6.7), (39.1, 39.3)), zoom=12),
    "lagos": dict(prefix="lg", chirps=("lagos_chirps_daily.nc", 6.625, 3.375), centre=(6.45, 3.40),
                  arc2=("lagos_arc2_daily.nc", (6.45, 6.7), (3.25, 3.5)), zoom=12),
}[CITY]
NAMES = {62: "North (Kawempe)", 86: "West (Lungujja)", 111: "North-east (Kyanja)", 112: "South (Munyonyo)"} if CITY == "kampala" else {}


def labels(cats):
    if CITY == "kampala":
        return [n if isinstance(n, str) else NAMES.get(i, f"Catchment {i}") for i, n in zip(cats.id, cats.name)]
    out, seen = [], {}
    for i, n in zip(cats.id, cats.osm_name):
        n = n if isinstance(n, str) else f"Catchment {i}"
        seen[n] = seen.get(n, 0) + 1
        out.append(n if seen[n] == 1 else f"{n} ({seen[n]})")
    return out


# ------------------------------------------------------------------ rainfall
def ams_series():
    f, la, lo = CFG["chirps"]
    ch = xr.open_dataset(PROC / f)["precip"].sel(time=slice("1981", "2025"))
    c = ch.sel(lat=la, lon=lo, method="nearest")
    f2, (a, b), (c0, c1) = CFG["arc2"]
    a2 = xr.open_dataset(PROC / f2)["precip"].sel(time=slice("1983", "2025"), lat=slice(a, b), lon=slice(c0, c1))
    return {"CHIRPS": c.groupby("time.year").max().to_series(),
            "ARC2": a2.groupby("time.year").max().mean(("lat", "lon")).to_series()}


def gauge_ams(path):
    d = pd.read_csv(path, header=None, usecols=[1, 2, 3, 5], names=["date", "el", "v", "q"])
    d = d[(d.el == "PRCP") & d.q.isna()]
    d["year"] = d.date // 10000
    g = d.groupby("year").v.agg(["count", "max"])
    return g[g["count"] >= 330]["max"] / 10


def stations():
    from drainage import ROOT
    if CITY == "kampala":
        st = pd.read_fwf(ROOT / "data" / "raw" / "ghcnd" / "stations_ug.txt", header=None,
                         colspecs=[(0, 11), (12, 20), (21, 30), (31, 37), (41, 71)], names=["id", "lat", "lon", "elev", "name"])
        return st, ROOT / "data" / "raw" / "ghcnd"
    inv = pd.read_fwf(ROOT / "data" / "raw" / "ghcnd_za" / "inventory.txt", header=None, names=["id", "lat", "lon", "el", "y0", "y1"],
                      colspecs=[(0, 11), (12, 20), (21, 30), (31, 35), (36, 40), (41, 45)])
    if CITY == "johannesburg":
        sel = pd.read_csv(ROOT / "data" / "raw" / "ghcnd_za" / "sel.txt", header=None, names=["id"])
        return inv[inv.id.isin(sel.id)], ROOT / "data" / "raw" / "ghcnd_za"
    # other cities: GHCN-Daily gauges within 200 km with >= 20 years of record
    import subprocess
    inv = pd.read_csv(ROOT / "data" / "raw" / "ghcnd_prcp_inventory.csv")
    la, lo = CFG["centre"]
    d = np.hypot(inv.lat - la, (inv.lon - lo) * np.cos(np.deg2rad(la))) * 111
    st = inv[(d < 200) & (inv.y1 - inv.y0 >= 20)]
    folder = ROOT / "data" / "raw" / f"ghcnd_{CITY}"
    folder.mkdir(exist_ok=True)
    for i in st.id:
        f = folder / f"{i}.csv.gz"
        if not f.exists():
            subprocess.run(["curl", "-sSf", "-o", str(f), f"https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/{i}.csv.gz"])
    return st, folder


def calibration(product_ams_by_station, product_years=None, tag=""):
    """Gauge/product GEV return-level ratios. Kampala: long gauge records (1926-86) vs product 1981-2025.
    Johannesburg: same-year ratios for gauges with >= 15 complete years inside the product period (public South
    African GHCN-Daily records mostly end in 1997, so the overlap is 1981/83-1997)."""
    st, folder = stations()
    out, rows = [], []
    for r in st.itertuples():
        g = gauge_ams(folder / f"{r.id}.csv.gz")
        p = product_ams_by_station(r.lat, r.lon)
        if CITY != "kampala":
            p = pd.Series(p, index=product_years)
            j = g.index.intersection(p.index[np.isfinite(p.values)])
            if len(j) < 15:
                continue
            ratio = gev_q(lmom_gev(g[j].values), T) / gev_q(lmom_gev(p[j].values), T)
            rows.append(dict(id=r.id, lat=r.lat, lon=r.lon, years=len(j), r_ams=float(np.corrcoef(g[j], p[j])[0, 1]),
                             **{f"ratio_{t}": v for t, v in zip(T, ratio)}))
        else:
            if len(g) < 15:
                continue
            ratio = gev_q(lmom_gev(g.values), T) / gev_q(lmom_gev(p), T)
        out.append(ratio)
    if rows:
        pd.DataFrame(rows).round(3).to_csv(RES / f"{CITY}_gauge_calibration_{tag}.csv", index=False)
    if CITY not in ("kampala", "johannesburg") and len(out) < 3:
        # too few local gauges: pool the Ugandan and South African station ratios for this product
        pooled = []
        for c in ("kampala", "johannesburg"):
            f = RES / f"{c}_gauge_ratios_{tag}.npy"
            if f.exists():
                pooled.append(np.load(f))
        print(CITY, tag, "local gauges", len(out), "-> pooled calibration", flush=True)
        return np.vstack(pooled + ([np.array(out)] if len(out) else []))
    np.save(RES / f"{CITY}_gauge_ratios_{tag}.npy", np.array(out))
    return np.array(out)  # stations x T


def ns_gev_test(x, years):
    """Likelihood-ratio test: GEV with location mu0 + mu1*t vs stationary."""
    t = (years - years.mean()) / 10.0

    def nll(p, trend):
        mu = p[0] + (p[3] * t if trend else 0)
        sc, sh = np.exp(p[1]), p[2]
        return -stats.genextreme.logpdf(x, sh, loc=mu, scale=sc).sum()
    x0 = [np.mean(x), np.log(np.std(x)), 0.0, 0.0]
    r0 = optimize.minimize(nll, x0, args=(False,), method="Nelder-Mead", options={"maxiter": 4000})
    r1 = optimize.minimize(nll, r0.x, args=(True,), method="Nelder-Mead", options={"maxiter": 4000})
    lr = 2 * (r0.fun - r1.fun)
    return r1.x[3], stats.chi2.sf(max(lr, 0), 1)


def rain():
    ams = ams_series()
    ch_all = xr.open_dataset(PROC / CFG["chirps"][0])["precip"].sel(time=slice("1981", "2025")).groupby("time.year").max()
    a2_all = xr.open_dataset(PROC / CFG["arc2"][0])["precip"].sel(time=slice("1983", "2025")).groupby("time.year").max()
    cf = {"CHIRPS": calibration(lambda la, lo: ch_all.sel(lat=la, lon=lo, method="nearest").values, ch_all.year.values, "chirps"),
          "ARC2": calibration(lambda la, lo: a2_all.sel(lat=la, lon=lo, method="nearest").values, a2_all.year.values, "arc2")}
    rows, boot = [], {}
    for prod, s in ams.items():
        y = s.index.values
        sl, p, _ = series_trend(s.values)
        mu1, p_ns = ns_gev_test(s.values, y)
        CF = np.median(cf[prod], 0)
        e1, e2 = s[(y >= EP1[0]) & (y <= EP1[1])].values, s[(y >= EP2[0]) & (y <= EP2[1])].values
        rl1, rl2 = gev_q(lmom_gev(e1), T) * CF, gev_q(lmom_gev(e2), T) * CF
        b1 = np.array([gev_q(lmom_gev(RNG.choice(e1, len(e1))), T) for _ in range(4000)])
        b2 = np.array([gev_q(lmom_gev(RNG.choice(e2, len(e2))), T) for _ in range(4000)])
        boot[prod] = (b1, b2, cf[prod])
        ch = 100 * (b2 / b1 - 1)
        for k, Tv in enumerate(T):
            rows.append(dict(product=prod, T=Tv, years=f"{y.min()}-{y.max()}", ams_mean_mm=s.mean(),
                             ams_sen_pct_per_decade=100 * sl / s.mean(), ams_mk_p=p,
                             nsgev_mu_trend_mm_per_decade=mu1, nsgev_lr_p=p_ns, cf_median=CF[k],
                             cf_min=cf[prod][:, k].min(), cf_max=cf[prod][:, k].max(),
                             rl_1981_2003_mm=rl1[k], rl_2004_2025_mm=rl2[k],
                             change_pct=100 * (rl2[k] / rl1[k] - 1),
                             change_pct_p05=np.nanpercentile(ch[:, k], 5), change_pct_p95=np.nanpercentile(ch[:, k], 95),
                             p_increase=float(np.mean(ch[:, k] > 0))))
    df = pd.DataFrame(rows)
    df.round(3).to_csv(RES / f"{CITY}_rain_stats.csv", index=False)

    fig, axs = plt.subplots(1, 2, figsize=(13, 4.4))
    for (prod, s), c in zip(ams.items(), [BLUE[4], CAT[1]]):
        CF = np.median(cf[prod][:, 1])
        axs[0].plot(s.index, s.values * CF, color=c, lw=1.6, marker="o", ms=3, label=f"{prod} (x{CF:.2f} gauge factor)")
        sl, p, b = series_trend(s.values)
        axs[0].plot(s.index, (b + sl / 10 * (s.index - s.index[0])) * CF, color=c, lw=1, ls="--")
    axs[0].set_ylabel("annual maximum 1-day rain, gauge-equivalent (mm)")
    axs[0].set_title(f"a  {CITY.title()} annual maximum daily rainfall")
    axs[0].legend(fontsize=8)
    ax = axs[1]
    for k, (prod, c) in enumerate(zip(ams, [BLUE[4], CAT[1]])):
        d = df[df["product"] == prod]
        x = np.arange(len(T)) + (k - 0.5) * 0.3
        ax.errorbar(x, d.change_pct, yerr=[d.change_pct - d.change_pct_p05, d.change_pct_p95 - d.change_pct], fmt="o",
                    color=c, capsize=4, label=prod)
    ax.axhline(0, color=INK, lw=0.8)
    ax.set_xticks(range(len(T)))
    ax.set_xticklabels([f"{t}-year" for t in T])
    ax.set_ylabel("% change, 2004-2025 vs 1981-2003")
    ax.set_title("b  Change in design 1-day rainfall (90% bootstrap interval)")
    ax.legend(fontsize=8)
    save(fig, f"{CFG['prefix']}01_{CITY}_rain_extremes.png")
    return df, boot


# ------------------------------------------------------------------ runoff
def scs_Q(P, CN):
    S = 25400 / CN - 254
    return np.where(P > 0.2 * S, (P - 0.2 * S) ** 2 / (P + 0.8 * S), 0.0)


def lag_h(L_m, slope_pct, CN):
    l_ft = L_m * 3.281
    S_in = 1000 / CN - 10
    return l_ft ** 0.8 * (S_in + 1) ** 0.7 / (1900 * np.sqrt(np.maximum(slope_pct, 0.5)))  # 0.5 % floor for flat terrain


def peak(P24, imp, cnp, cat):
    CN = imp * 98 + (1 - imp) * cnp
    lag = lag_h(cat.flow_length_m, cat.mean_slope_pct, CN)
    tc = lag / 0.6
    P = trrl(P24, tc)
    Q = scs_Q(P, CN)
    Tp = tc / 2 + lag
    return 0.208 * cat.area_km2 * Q / Tp, scs_Q(P24, CN), tc


def imp_at(ep, cid, year):
    e = ep[ep.id == cid].set_index("epoch").impervious_frac
    return float(np.interp(year, e.index, e.values))


def attribution(rainstats, boot):
    cats = pd.read_csv(RES / f"{CITY}_catchments.csv")
    ep = pd.read_csv(RES / f"{CITY}_landcover_epochs.csv")
    k0 = cats.k_impervious_over_ghsl.iloc[0]
    kspread = (cats.wc2021_builtup / ep[ep.epoch == 2020].set_index("id").built_frac.reindex(cats.id).values).values
    cats["label"] = labels(cats)
    rows, mc = [], []
    for prod in ("CHIRPS", "ARC2"):
        rs = rainstats[rainstats["product"] == prod].set_index("T")
        b1, b2, cfs = boot[prod]
        for cat in cats.itertuples():
            imp1, imp2 = imp_at(ep, cat.id, LAND1), imp_at(ep, cat.id, LAND2)
            for k, Tv in enumerate(T):
                P1, P2 = rs.loc[Tv, "rl_1981_2003_mm"], rs.loc[Tv, "rl_2004_2025_mm"]
                cnp = CN_PERV["C"]
                f = lambda P, imp: peak(P, imp, cnp, cat)
                q11, v11, tc11 = f(P1, imp1)
                q21, v21, _ = f(P2, imp1)
                q12, v12, tc12 = f(P1, imp2)
                q22, v22, _ = f(P2, imp2)
                land = 0.5 * ((q12 - q11) + (q22 - q21))
                rainf = 0.5 * ((q21 - q11) + (q22 - q12))
                vland = 0.5 * ((v12 - v11) + (v22 - v21))
                vrain = 0.5 * ((v21 - v11) + (v22 - v12))
                rows.append(dict(product=prod, catchment=cat.label, id=cat.id, area_km2=cat.area_km2, T=Tv,
                                 imp_1992=imp1, imp_2014=imp2, P_1981_2003=P1, P_2004_2025=P2,
                                 tc_h_1992=float(tc11), tc_h_2014=float(tc12),
                                 qp_base_m3s=float(q11), qp_now_m3s=float(q22), qp_change_pct=float(100 * (q22 / q11 - 1)),
                                 qp_land_m3s=float(land), qp_rain_m3s=float(rainf),
                                 Q_base_mm=float(v11), Q_now_mm=float(v22), Q_change_pct=float(100 * (v22 / v11 - 1)),
                                 Q_land_mm=float(vland), Q_rain_mm=float(vrain)))
                # Monte Carlo
                n = 4000
                hsg = RNG.choice(list(HSG_P), n, p=list(HSG_P.values()))
                cnps = np.array([CN_PERV[h] for h in hsg])
                kf = RNG.choice(kspread, n) / k0 * RNG.uniform(0.8, 1.2, n)  # catchment spread, widened +-20% for change over time
                cf = cfs[RNG.integers(0, len(cfs), n), k]
                Pa, Pb = b1[:, k] * cf, b2[:, k] * cf
                i1, i2 = np.clip(imp1 * kf, 0, 0.95), np.clip(imp2 * kf, 0, 0.95)
                g = lambda P, imp: peak(P, imp, cnps, cat)[0]
                a11, a21, a12, a22 = g(Pa, i1), g(Pb, i1), g(Pa, i2), g(Pb, i2)
                L = 0.5 * ((a12 - a11) + (a22 - a21))
                R = 0.5 * ((a21 - a11) + (a22 - a12))
                mc.append(pd.DataFrame(dict(product=prod, catchment=cat.label, T=Tv, land=L, rain=R, base=a11)))
    att = pd.DataFrame(rows)
    att.round(3).to_csv(RES / f"{CITY}_attribution.csv", index=False)
    mc = pd.concat(mc)
    summ = mc.groupby(["product", "catchment", "T"]).apply(lambda d: pd.Series({
        "land_pct_of_base_p50": np.median(100 * d.land / d.base), "land_p05": np.percentile(100 * d.land / d.base, 5),
        "land_p95": np.percentile(100 * d.land / d.base, 95), "rain_pct_of_base_p50": np.median(100 * d.rain / d.base),
        "rain_p05": np.percentile(100 * d.rain / d.base, 5), "rain_p95": np.percentile(100 * d.rain / d.base, 95),
        "p_land_exceeds_rain": np.mean(d.land > d.rain)})).reset_index()
    summ.round(3).to_csv(RES / f"{CITY}_attribution_mc.csv", index=False)
    return att, summ, cats, ep


def figures(att, summ, cats, ep):
    # land-cover trajectories
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.4), sharey=False)
    lab = dict(zip(cats.id, cats.label))
    order = cats.sort_values("area_km2", ascending=False).id
    many = len(order) > 12
    for i, cid in enumerate(order):
        e = ep[ep.id == cid]
        c = MUTED if many else CAT[i % 8]
        lw = 0.6 if many else (1.8 if i < 4 else 1)
        axs[0].plot(e.epoch, 100 * e.impervious_frac, color=c, lw=lw, label=None if many else lab[cid], alpha=0.6 if many else 1)
        axs[1].plot(e.epoch, 100 * e.built_frac_valley, color=c, lw=lw, alpha=0.6 if many else 1)
    if many:
        w = cats.set_index("id").area_km2
        for ax, col in ((axs[0], "impervious_frac"), (axs[1], "built_frac_valley")):
            m = ep.pivot(index="epoch", columns="id", values=col)[w.index]
            ax.plot(m.index, 100 * (m * w).sum(1) / w.sum(), color=BLUE[4], lw=2.6, label="area-weighted mean")
        axs[0].plot([], [], color=MUTED, lw=0.6, label=f"{len(order)} catchments")
    for ax in axs:
        ax.axvspan(2020, 2030, color=GRID, alpha=0.6, lw=0)
        ax.text(2025, 0.97, "GHSL\nprojection", fontsize=7, color=INK2, ha="center", va="top", transform=ax.get_xaxis_transform())
    axs[0].set_ylabel("impervious cover (%)")
    axs[0].set_title("a  Impervious cover by catchment, 1975-2030")
    axs[1].set_ylabel("built-up share of valley floor (%)")
    axs[1].set_title("b  Building on valley floors (HAND < 3 m)")
    axs[0].legend(fontsize=7, ncol=2)
    save(fig, f"{CFG['prefix']}02_{CITY}_imperviousness.png")

    # attribution bars (CHIRPS, 10-yr), with MC intervals
    for prod in ("CHIRPS", "ARC2"):
        a = att[(att["product"] == prod) & (att["T"] == 10)].set_index("catchment")
        s = summ[(summ["product"] == prod) & (summ["T"] == 10)].set_index("catchment").loc[a.index]
        a = a.sort_values("area_km2", ascending=False)
        s = s.loc[a.index]
        fig, ax = plt.subplots(figsize=(10, 5.6))
        y = np.arange(len(a))[::-1]
        land = 100 * a.qp_land_m3s / a.qp_base_m3s
        rain_ = 100 * a.qp_rain_m3s / a.qp_base_m3s
        ax.barh(y + 0.18, land, 0.34, color=ORANGE[3], label="land cover (paving, building)")
        ax.barh(y - 0.18, rain_, 0.34, color=BLUE[3], label="rainfall")
        ax.errorbar(s.land_pct_of_base_p50, y + 0.18, xerr=[s.land_pct_of_base_p50 - s.land_p05, s.land_p95 - s.land_pct_of_base_p50],
                    fmt="none", ecolor=INK, capsize=3, lw=0.8)
        ax.errorbar(s.rain_pct_of_base_p50, y - 0.18, xerr=[s.rain_pct_of_base_p50 - s.rain_p05, s.rain_p95 - s.rain_pct_of_base_p50],
                    fmt="none", ecolor=INK, capsize=3, lw=0.8)
        ax.axvline(0, color=INK, lw=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels([f"{c} ({ar:.0f} km²)" for c, ar in zip(a.index, a.area_km2)], fontsize=8.5)
        ax.set_xlabel("change in 10-year peak flow, % of 1992 value")
        ax.set_title(f"Contribution to the change in 10-year peak flow, 1992 to 2014 ({prod} rainfall)\nwhiskers: 5-95% of 4,000 Monte Carlo runs")
        ax.legend(fontsize=8, loc="lower right")
        save(fig, f"{CFG['prefix']}03_attribution_{prod.lower()}.png")

    # catchment map on satellite
    import contextily as ctx
    import geopandas as gpd
    from rasterio.features import shapes
    with rasterio.open(PROC / f"{CITY}_catchments.tif") as r:
        cat = r.read(1).astype(int)
        hand = r.read(2)
        tr = r.transform
    keep = set(cats.id)
    polys = [(dict(id=int(v)), shp) for shp, v in shapes(np.where(np.isin(cat, list(keep)), cat, 0).astype("int32"), transform=tr) if v > 0]
    g = gpd.GeoDataFrame([p[0] for p in polys], geometry=[__import__("shapely").geometry.shape(p[1]) for p in polys], crs=4326).dissolve("id").reset_index()
    g["label"] = g.id.map(lab)
    fig, ax = plt.subplots(figsize=(9, 8.5))
    g.boundary.plot(ax=ax, color="#ffd400", lw=1.2, zorder=5)
    ext = g.total_bounds
    ax.set_xlim(ext[0] - 0.02, ext[2] + 0.02)
    ax.set_ylim(ext[1] - 0.02, ext[3] + 0.02)
    ctx.add_basemap(ax, crs="EPSG:4326", source=ctx.providers.Esri.WorldImagery, zoom=CFG["zoom"], attribution_size=5)
    lo = np.linspace(tr.c, tr.c + tr.a * hand.shape[1], hand.shape[1])
    la = np.linspace(tr.f, tr.f + tr.e * hand.shape[0], hand.shape[0])
    vf = np.where((hand < 3) & np.isin(cat, list(keep)), 1.0, np.nan)
    ax.pcolormesh(lo, la, vf, cmap=plt.matplotlib.colors.ListedColormap(["#5ec8ff"]), alpha=0.45, zorder=4, shading="auto")
    if CITY == "kampala":
        d2 = gpd.read_file(PROC / "uganda_adm2.geojson")
        d2[d2.shapeName == "Kampala"].boundary.plot(ax=ax, color="white", lw=1.0, ls="--", zorder=6)
    else:
        gpd.read_file(PROC / f"{CITY}_boundary.geojson").boundary.plot(ax=ax, color="white", lw=1.0, ls="--", zorder=6)
    big = set(cats.sort_values("area_km2", ascending=False).id.head(12))
    for _, r in g.iterrows():
        if r.id not in big:
            continue
        p = r.geometry.representative_point()
        ax.text(p.x, p.y, r.label, fontsize=8, color="white", fontweight="bold", ha="center", zorder=7,
                bbox=dict(fc="black", ec="none", alpha=0.45, pad=1.5))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"{CITY.title()} drainage catchments (yellow), valley floors HAND < 3 m (blue), city boundary (dashed)")
    save(fig, f"{CFG['prefix']}04_{CITY}_catchments_map.png")


if __name__ == "__main__":
    rs, boot = rain()
    print(rs.round(2).to_string())
    att, summ, cats, ep = attribution(rs, boot)
    print(att[att["T"] == 10][["product", "catchment", "area_km2", "imp_1992", "imp_2014", "P_1981_2003", "P_2004_2025",
                               "tc_h_1992", "tc_h_2014", "qp_base_m3s", "qp_now_m3s", "qp_change_pct", "qp_land_m3s",
                               "qp_rain_m3s", "Q_change_pct"]].round(2).to_string())
    print(summ[summ["T"] == 10].round(1).to_string())
    figures(att, summ, cats, ep)


def uplift():
    """Clausius-Clapeyron (7 %/degC) uplift of design rain for 2041-2070 vs 1991-2020, CMIP6 median warming."""
    if CITY == "kampala":
        c = pd.read_csv(RES / "cmip6_uganda_changes.csv")
        c = c[(c.variable == "tas") & (c.period == "2041-2070")].set_index("scenario")["median"]
        dT = {"ssp245": c["ssp245"], "ssp585": c["ssp585"]}
    else:
        from drainage import ROOT
        tag = "jhb" if CITY == "johannesburg" else CITY
        ds = [xr.open_dataset(f) for f in sorted((ROOT / "data" / "raw" / f"cmip6_{tag}").glob("*.nc"))]
        dT = {}
        for scen in ("ssp245", "ssp585"):
            d = []
            for x in ds:
                full = pd.concat([x.historical.to_series().dropna(), x[scen].to_series().dropna()])
                d.append(full.loc[2041:2070].mean() - full.loc[1991:2020].mean())
            dT[scen] = float(np.median(d))
        pd.Series(dT).to_csv(RES / f"{CITY}_cmip6_warming.csv")
    return {k: 1.07 ** v for k, v in dT.items()}, dT


def breakeven_timeline_future(att, cats, ep):
    """Rainfall increase that would match the land effect; peak flow by land epoch at fixed rainfall; futures."""
    rs = pd.read_csv(RES / f"{CITY}_rain_stats.csv")
    ams = ams_series()["CHIRPS"]
    CF = rs[rs["product"] == "CHIRPS"].set_index("T").cf_median
    P_stat = {Tv: gev_q(lmom_gev(ams.values), [Tv])[0] * CF[Tv] for Tv in T}
    cats = cats.copy()
    UP, _ = uplift()
    rows, tl, fut = [], [], []
    for cat in cats.itertuples():
        imp1, imp2 = imp_at(ep, cat.id, LAND1), imp_at(ep, cat.id, LAND2)
        for Tv in T:
            P = P_stat[Tv]
            base = peak(P, imp1, CN_PERV["C"], cat)[0]
            land = peak(P, imp2, CN_PERV["C"], cat)[0] - base
            f = optimize.brentq(lambda x: peak(P * x, imp1, CN_PERV["C"], cat)[0] - base - land, 1.0, 3.0)
            rows.append(dict(catchment=cat.label, T=Tv, P_stationary_mm=P, land_effect_pct=100 * land / base,
                             rain_increase_needed_pct=100 * (f - 1)))
            for y in range(1975, 2031, 5):
                tl.append(dict(catchment=cat.label, id=cat.id, T=Tv, epoch=y, imp=imp_at(ep, cat.id, y),
                               qp=float(peak(P, imp_at(ep, cat.id, y), CN_PERV["C"], cat)[0])))
            for scen, up in (("2014 land, 1981-2025 rain", 1.0), ("2030 land (GHSL), 1981-2025 rain", 1.0),
                             (f"2030 land, rain +{100 * (UP['ssp245'] - 1):.0f}% (SSP2-4.5, 2041-70)", UP["ssp245"]),
                             (f"2030 land, rain +{100 * (UP['ssp585'] - 1):.0f}% (SSP5-8.5, 2041-70)", UP["ssp585"]),
                             (f"2014 land, rain +{100 * (UP['ssp585'] - 1):.0f}% (SSP5-8.5, 2041-70)", UP["ssp585"])):
                yr = 2014 if scen.startswith("2014") else 2030
                fut.append(dict(catchment=cat.label, T=Tv, scenario=scen,
                                change_vs_1992_pct=100 * (peak(P * up, imp_at(ep, cat.id, yr), CN_PERV["C"], cat)[0] / base - 1)))
    be = pd.DataFrame(rows)
    be.round(2).to_csv(RES / f"{CITY}_breakeven.csv", index=False)
    tl = pd.DataFrame(tl)
    tl.round(3).to_csv(RES / f"{CITY}_peak_timeline.csv", index=False)
    fut = pd.DataFrame(fut)
    fut.round(2).to_csv(RES / f"{CITY}_futures.csv", index=False)
    return be, tl, fut


if __name__ == "__main__":  # robustness: break-even rainfall, land timeline, futures
    cats_ = pd.read_csv(RES / f"{CITY}_catchments.csv")
    cats_["label"] = labels(cats_)
    ep_ = pd.read_csv(RES / f"{CITY}_landcover_epochs.csv")
    be, tl, fut = breakeven_timeline_future(None, cats_, ep_)
    print(be[be["T"] == 10].round(1).to_string())
    print(fut[fut["T"] == 10].pivot(index="catchment", columns="scenario", values="change_vs_1992_pct").round(1).to_string())
    t10 = tl[tl["T"] == 10].pivot(index="epoch", columns="catchment", values="qp")
    print((100 * (t10 / t10.loc[1975] - 1)).round(0).to_string())
