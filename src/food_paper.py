"""Shifting reliability of Uganda's growing seasons, and its food-security footprint.

Rainfall: CHIRPS v2.0 (0.25 deg, 1981-2025) and ARC2 (0.1 deg, 1983-2025), Uganda land cells.
ET0: FAO-56 Penman-Monteith from NASA POWER (climate_params.py), monthly totals spread evenly over days.
Seasons: first (S1) and second (S2) season for every cell.
  Onset A (agronomic, planting): first day in the window with >= 20 mm in 3 days and no dry spell of >= 10 days
    (< 1 mm) in the following 30 days. Windows: S1 15 Feb - 15 May, S2 1 Aug - 31 Oct. No onset = failed season.
  Onset B (anomalous accumulation, Liebmann et al. 2012): day after the minimum of cumulative (R - mean R) in
    S1 1 Feb - 31 Jul / S2 1 Aug - 31 Jan; cessation = day of the following maximum.
Crop water balance (WRSI, FAO / FEWS NET GeoWRSI logic): planting at onset; maize 120 d (Kc 0.3/1.2/0.6; stages
  20-35-40-25 d), beans 90 d (Kc 0.4/1.15/0.35; 15-25-35-15 d); soil water holding capacity 100 mm, depletion
  fraction 0.5. WRSI = 100 x sum(AET) / sum(Kc x ET0). Failure: WRSI < 50 (FEWS NET 'failure') or no onset.
Changes: 1981-2003 vs 2004-2025 (ARC2: 1983-2003); per-cell Fisher exact test, Benjamini-Hochberg FDR 10 % for
  field significance (Wilks 2016).
Validation: NOAA VHP Vegetation Condition Index over cropland (58 districts, weekly, 1982-2025); FAOSTAT national
  yields (detrended); FEWS NET IPC phases for Karamoja (2011-2026).

Outputs: data/processed/wrsi_<dataset>.nc, results/fp_*.csv, figures/fp01-fp07*.png
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shapely
import xarray as xr
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap
from scipy import stats

from common import (BASE, BLUE, CAT, CMAP_RAIN, GRID, INK, INK2, MUTED, ORANGE, PROC, RES, ROOT, UG_EXTENT,
                    draw_borders, grid_mask, save, series_trend, zone_names, zones)

CROPS = {"maize": (120, [(20, 0.3, 0.3), (35, 0.3, 1.2), (40, 1.2, 1.2), (25, 1.2, 0.6)]),
         "beans": (90, [(15, 0.4, 0.4), (25, 0.4, 1.15), (35, 1.15, 1.15), (15, 1.15, 0.35)])}
WHC, PDEP = 100.0, 0.5
P1, P2 = (1981, 2003), (2004, 2025)
CMAP_RISK = LinearSegmentedColormap.from_list("risk", ["#f4f8fd"] + ORANGE)


def kc_curve(stages):
    return np.concatenate([np.linspace(a, b, n, endpoint=False) if a != b else np.full(n, a) for n, a, b in stages])


# ------------------------------------------------------------------ inputs
def load(dataset):
    if dataset == "CHIRPS":
        pr = xr.open_dataset(PROC / "chirps_uganda_daily.nc")["precip"].sel(time=slice("1981-01-01", "2026-06-30"))
    else:
        pr = xr.open_dataset(PROC / "arc2_uganda_daily.nc")["precip"].sel(time=slice("1983-01-01", "2025-12-31"))
    pr = pr.load()
    z = zones()
    zz = z.interp(lat=pr.lat, lon=pr.lon, method="nearest") if dataset != "CHIRPS" else z
    if dataset != "CHIRPS":
        m = grid_mask(pr.lat, pr.lon) & (zz >= 0)
    else:
        m = zz >= 0
    st = pr.stack(cell=("lat", "lon"))
    keep = m.stack(cell=("lat", "lon")).values
    st = st.isel(cell=np.flatnonzero(keep))
    zc = zz.stack(cell=("lat", "lon")).values[keep].astype(int)
    et = xr.open_dataset(PROC / "et0_monthly.nc")["et0"]
    et = (et / et.time.dt.days_in_month).interp(lat=pr.lat, lon=pr.lon, method="nearest", kwargs={"fill_value": None})
    et = et.stack(cell=("lat", "lon")).isel(cell=np.flatnonzero(keep))
    # extend ET0 climatology beyond POWER's last month
    clim = et.groupby("time.month").mean()
    t = pd.DatetimeIndex(st.time.values)
    em = et.reindex(time=pd.DatetimeIndex(t.to_period("M").to_timestamp().unique()))
    em = em.fillna(clim.sel(month=em.time.dt.month).drop_vars("month"))
    etd = em.reindex(time=t.to_period("M").to_timestamp()).values
    etd = np.where(np.isnan(etd), np.nanmean(etd, 1, keepdims=True), etd)  # edge cells without POWER data
    rain = np.nan_to_num(st.values.astype("float32"))
    lat = np.array([c[0] for c in st.indexes["cell"]])
    lon = np.array([c[1] for c in st.indexes["cell"]])
    return rain, etd.astype("float32"), t, lat, lon, zc


# ------------------------------------------------------------------ onsets
def onset_agronomic(rain, t, years, window):
    dry = rain < 1
    run = np.zeros_like(rain, dtype=np.int16)
    for i in range(1, len(t)):
        run[i] = np.where(dry[i], run[i - 1] + 1, 0)
    r3 = np.zeros_like(rain)
    r3[:-2] = rain[:-2] + rain[1:-1] + rain[2:]
    maxdry = np.zeros_like(run)
    n = len(t)
    for k in range(30):
        idx = np.minimum(np.arange(n) + 3 + k, n - 1)
        maxdry = np.maximum(maxdry, np.minimum(run[idx], k + 1))
    ok = (r3 >= 20) & (maxdry < 10)
    out = np.full((len(years), rain.shape[1]), -1, int)
    for yi, y in enumerate(years):
        a = np.searchsorted(t, pd.Timestamp(f"{y}-{window[0]}"))
        b = np.searchsorted(t, pd.Timestamp(f"{y}-{window[1]}"))
        if b >= n - 130:
            continue
        seg = ok[a:b]
        has = seg.any(0)
        out[yi] = np.where(has, a + seg.argmax(0), -1)
    return out


def onset_anomaly(rain, t, years, window, ybump=0):
    rbar = rain.mean(0)
    on = np.full((len(years), rain.shape[1]), -1, int)
    ce = np.full_like(on, -1)
    for yi, y in enumerate(years):
        a = np.searchsorted(t, pd.Timestamp(f"{y}-{window[0]}"))
        b = np.searchsorted(t, pd.Timestamp(f"{y + ybump}-{window[1]}"))
        if b >= len(t) or b - a < 150:
            continue
        A = np.cumsum(rain[a:b] - rbar, 0)
        c = A.argmax(0)  # cessation first: the late-window dry spell can create a later, spurious minimum
        A2 = np.where(np.arange(b - a)[:, None] <= c[None, :], A, np.inf)
        o = np.minimum(A2.argmin(0) + 1, c)
        good = (c - o) >= 20  # no recognisable season otherwise
        on[yi], ce[yi] = np.where(good, a + o, -1), np.where(good, a + c, -1)
    return on, ce


# ------------------------------------------------------------------ WRSI
def wrsi(rain, etd, onset, crop):
    L, stages = CROPS[crop]
    kc = kc_curve(stages)
    ny, nc = onset.shape
    o = onset.ravel()
    cell = np.tile(np.arange(nc), ny)
    valid = (o >= 0) & (o + L < rain.shape[0])
    S = np.zeros(o.size)
    aet = np.zeros(o.size)
    pet = np.zeros(o.size)
    oo = np.where(valid, o, 0)
    for k in range(L):
        idx = oo + k
        P = rain[idx, cell]
        E = etd[idx, cell] * kc[k]
        S = np.minimum(WHC, S + P)
        a = E * np.minimum(1.0, S / (WHC * (1 - PDEP)))
        S = np.maximum(0.0, S - a)
        aet += a
        pet += E
    w = np.where(valid, 100 * aet / pet, np.nan)
    w = np.where(o < 0, 0.0, w)  # no onset in the planting window = failed season
    return w.reshape(ny, nc)


def compute(dataset):
    f = PROC / f"wrsi_{dataset.lower()}.nc"
    if f.exists():
        return xr.open_dataset(f).load()
    rain, etd, t, lat, lon, zc = load(dataset)
    years = np.arange(t[0].year, 2026)
    base = (t.year >= 1991) & (t.year <= 2020)
    clim = pd.DataFrame(rain[base]).groupby(np.minimum(t[base].dayofyear, 365)).mean().values
    ff = np.fft.rfft(clim - clim.mean(0), axis=0)
    bimodal = np.abs(ff[2]) / np.abs(ff[1]) > 1  # two rainy seasons (Dunning et al. 2016)
    ds = xr.Dataset(coords={"year": years, "cell": np.arange(rain.shape[1])})
    ds["bimodal"] = ("cell", bimodal)
    ds["lat"], ds["lon"], ds["zone"] = ("cell", lat), ("cell", lon), ("cell", zc)
    for s, win, winB, bump in (("S1", ("02-15", "05-15"), ("02-01", "07-31"), 0), ("S2", ("08-01", "10-31"), ("08-01", "01-31"), 1)):
        oa = onset_agronomic(rain, t, years, win)
        ob, cb = onset_anomaly(rain, t, years, winB, bump)
        ob[:, ~bimodal], cb[:, ~bimodal] = -1, -1  # method B only defined for two-season cells
        y0 = pd.to_datetime([f"{y}-01-01" for y in years]).values[:, None]
        tv = t.values
        ds[f"{s}_onsetA"] = (("year", "cell"), np.where(oa >= 0, (tv[np.maximum(oa, 0)] - y0) / np.timedelta64(1, "D") + 1, np.nan))
        ds[f"{s}_onsetB"] = (("year", "cell"), np.where(ob >= 0, (tv[np.maximum(ob, 0)] - y0) / np.timedelta64(1, "D") + 1, np.nan))
        ds[f"{s}_cessB"] = (("year", "cell"), np.where(cb >= 0, (tv[np.maximum(cb, 0)] - y0) / np.timedelta64(1, "D") + 1, np.nan))
        for crop in CROPS:
            ds[f"{s}_{crop}_A"] = (("year", "cell"), wrsi(rain, etd, oa, crop))
            wb = wrsi(rain, etd, np.where(ob >= 0, ob, -1), crop)
            wb[:, ~bimodal] = np.nan
            ds[f"{s}_{crop}_B"] = (("year", "cell"), wb)
        print(dataset, s, "done", flush=True)
    ds.to_netcdf(f)
    return ds


# ------------------------------------------------------------------ statistics
def bh(p, q=0.10):
    p = np.asarray(p)
    ok = np.isfinite(p)
    ps = np.sort(p[ok])
    m = ps.size
    thr = ps[ps <= q * np.arange(1, m + 1) / m]
    cut = thr.max() if thr.size else -1
    return np.where(ok, p <= cut, False)


def failure_tables(dss):
    zn = zone_names()
    rows, cellrows = [], []
    for (dname, ds), thr in [(kv, th) for kv in dss.items() for th in (50, 80)]:
        yrs = ds.year.values
        e = (yrs >= max(P1[0], yrs[0])) & (yrs <= P1[1])
        l = (yrs >= P2[0]) & (yrs <= P2[1])
        for s in ("S1", "S2"):
            for crop in CROPS:
                for meth in ("A", "B"):
                    w = ds[f"{s}_{crop}_{meth}"].values
                    fail = (w < thr).astype(float)
                    fail[np.isnan(w)] = np.nan
                    fe, fl = np.nanmean(fail[e], 0), np.nanmean(fail[l], 0)
                    ne, nl = np.sum(np.isfinite(fail[e]), 0), np.sum(np.isfinite(fail[l]), 0)
                    pv = np.array([stats.fisher_exact([[int(fe[c] * ne[c]), ne[c] - int(fe[c] * ne[c])],
                                                       [int(fl[c] * nl[c]), nl[c] - int(fl[c] * nl[c])]])[1]
                                   if ne[c] and nl[c] else np.nan for c in range(w.shape[1])])
                    sig = bh(pv)
                    cellrows.append(pd.DataFrame(dict(dataset=dname, threshold=thr, season=s, crop=crop, onset=meth, cell=ds.cell.values,
                                                      lat=ds.lat.values, lon=ds.lon.values, zone=ds.zone.values,
                                                      fail_early=fe, fail_late=fl, p=pv, sig_fdr=sig)))
                    for zid in list(np.unique(ds.zone.values)) + ["Uganda"]:
                        mk = np.ones(w.shape[1], bool) if zid == "Uganda" else ds.zone.values == zid
                        name = "Uganda" if zid == "Uganda" else zn[int(zid)]
                        # zone-year failure share, then period means + permutation test on years
                        zy = np.nanmean(fail[:, mk], 1)
                        diff = np.nanmean(zy[l]) - np.nanmean(zy[e])
                        pool = zy[e | l]
                        rng = np.random.default_rng(1)
                        perm = [np.nanmean(x[:l.sum()]) - np.nanmean(x[l.sum():]) for x in (rng.permutation(pool) for _ in range(2000))]
                        rows.append(dict(dataset=dname, threshold=thr, season=s, crop=crop, onset=meth, zone=name,
                                         fail_early=100 * np.nanmean(zy[e]), fail_late=100 * np.nanmean(zy[l]),
                                         change_pts=100 * diff, p_perm=float(np.mean(np.abs(perm) >= abs(diff))),
                                         share_cells_sig_increase=float(np.mean(sig[mk] & (fl[mk] > fe[mk]))),
                                         share_cells_sig_decrease=float(np.mean(sig[mk] & (fl[mk] < fe[mk])))))
    t = pd.DataFrame(rows)
    t.round(3).to_csv(RES / "fp_failure_zone.csv", index=False)
    c = pd.concat(cellrows)
    c.to_csv(RES / "fp_failure_cells.csv", index=False)
    return t, c


def timing_tables(dss):
    zn = zone_names()
    rows = []
    for dname, ds in dss.items():
        for v in ("S1_onsetA", "S1_onsetB", "S1_cessB", "S2_onsetA", "S2_onsetB", "S2_cessB"):
            for zid in list(np.unique(ds.zone.values)) + ["Uganda"]:
                mk = np.ones(ds.sizes["cell"], bool) if zid == "Uganda" else ds.zone.values == zid
                y = np.nanmedian(ds[v].values[:, mk], 1)
                ok = np.isfinite(y)
                if ok.sum() < 20:
                    continue
                s, p, _ = series_trend(y[ok])
                rows.append(dict(dataset=dname, variable=v, zone="Uganda" if zid == "Uganda" else zn[int(zid)],
                                 median_doy=float(np.nanmedian(y)), trend_days_per_decade=s, p=p))
        for s in ("S1", "S2"):
            L = ds[f"{s}_cessB"] - ds[f"{s}_onsetB"]
            for zid in list(np.unique(ds.zone.values)) + ["Uganda"]:
                mk = np.ones(ds.sizes["cell"], bool) if zid == "Uganda" else ds.zone.values == zid
                y = np.nanmedian(L.values[:, mk], 1)
                if np.isfinite(y).sum() < 20:
                    continue
                tr, p, _ = series_trend(y[np.isfinite(y)])
                rows.append(dict(dataset=dname, variable=f"{s}_lengthB", zone="Uganda" if zid == "Uganda" else zn[int(zid)],
                                 median_doy=float(np.nanmedian(y)), trend_days_per_decade=tr, p=p))
    t = pd.DataFrame(rows)
    t.round(3).to_csv(RES / "fp_timing_zone.csv", index=False)
    return t


# ------------------------------------------------------------------ validation
def district_index(ds):
    g = gpd.read_file(ROOT / "data" / "raw" / "gadm" / "gadm41_UGA_1.json")
    pts = shapely.points(ds.lon.values, ds.lat.values)
    dist = np.full(ds.sizes["cell"], None, object)
    for _, r in g.iterrows():
        dist[shapely.contains(r.geometry, pts)] = r.NAME_1
    return dist


def vhi_validation(ds, dname):
    v = pd.read_csv(PROC / "vhi_uganda_weekly.csv")
    names = pd.read_csv(PROC / "vhp_provinces.csv").set_index("province_id").name
    v["district"] = v.province_id.map(names)
    dist = district_index(ds)
    rows = []
    for s, weeks in (("S1", (17, 28)), ("S2", (43, 52))):
        vv = v[(v.week >= weeks[0]) & (v.week <= weeks[1])].groupby(["district", "year"]).VCI.mean()
        w = ds[f"{s}_maize_A"].values
        for d in np.unique(dist[dist != None]):
            mk = dist == d
            if mk.sum() == 0 or d not in vv.index.get_level_values(0):
                continue
            wy = pd.Series(np.nanmean(w[:, mk], 1), index=ds.year.values)
            fy = pd.Series(np.nanmean((w[:, mk] < 50), 1), index=ds.year.values)
            x = vv.loc[d]
            j = wy.index.intersection(x.index)
            for y in j:
                rows.append(dict(dataset=dname, season=s, district=d, year=int(y), wrsi=wy[y], fail_share=fy[y], vci=x[y]))
    df = pd.DataFrame(rows)
    # anomalies within district
    for c in ("wrsi", "vci", "fail_share"):
        df[c + "_anom"] = df[c] - df.groupby(["season", "district"])[c].transform("mean")
    res = []
    for s in ("S1", "S2"):
        d = df[df.season == s].dropna()
        r, p = stats.spearmanr(d.wrsi_anom, d.vci_anom)
        perd = d.groupby("district").apply(lambda x: stats.spearmanr(x.wrsi, x.vci)[0] if len(x) > 10 else np.nan)
        failed = d.fail_share >= 0.5
        res.append(dict(dataset=dname, season=s, n=len(d), spearman_pooled=r, p=p, median_district_r=float(np.nanmedian(perd)),
                        share_districts_r_pos=float(np.mean(perd > 0)), vci_when_failed=float(d.vci[failed].mean()),
                        vci_when_not=float(d.vci[~failed].mean()), n_failed=int(failed.sum()),
                        vci_drought_rate_when_failed=float(np.mean(d.vci[failed] < 35)),
                        vci_drought_rate_when_not=float(np.mean(d.vci[~failed] < 35))))
    return df, pd.DataFrame(res)


def vci_reliability():
    """Rainfall-independent check: growing-season vegetation condition by district, 1982-2025."""
    v = pd.read_csv(PROC / "vhi_uganda_weekly.csv")
    names = pd.read_csv(PROC / "vhp_provinces.csv").set_index("province_id").name
    v["district"] = v.province_id.map(names)
    v = v[~v.district.str.startswith("Lake")]
    rows, drows = [], []
    for s, weeks in (("S1", (17, 28)), ("S2", (43, 52))):
        x = v[(v.week >= weeks[0]) & (v.week <= weeks[1])].groupby(["district", "year"]).VCI.mean().unstack(0)
        x = x.loc[1982:2025]
        for d in x.columns:
            y = x[d].dropna()
            if len(y) < 20 or y.std() == 0:
                continue
            tr, p, _ = series_trend(y.values)
            e, l = y.loc[1982:2003], y.loc[2004:2025]
            drows.append(dict(season=s, district=d, trend_per_decade=tr, p=p, drought_early=float(np.mean(e < 35)),
                              drought_late=float(np.mean(l < 35)), mean_early=e.mean(), mean_late=l.mean()))
        dd = pd.DataFrame([r for r in drows if r["season"] == s])
        rows.append(dict(season=s, districts=len(dd), median_trend=dd.trend_per_decade.median(),
                         share_sig_up=float(np.mean((dd.p < 0.05) & (dd.trend_per_decade > 0))),
                         share_sig_down=float(np.mean((dd.p < 0.05) & (dd.trend_per_decade < 0))),
                         share_sig_fdr=float(np.mean(bh(dd.p.values))),
                         drought_early=100 * dd.drought_early.mean(), drought_late=100 * dd.drought_late.mean()))
    pd.DataFrame(drows).round(3).to_csv(RES / "fp_vci_district_trends.csv", index=False)
    out = pd.DataFrame(rows)
    out.round(3).to_csv(RES / "fp_vci_reliability.csv", index=False)
    return out


def ipc_vs_vci():
    v = pd.read_csv(PROC / "vhi_uganda_weekly.csv")
    names = pd.read_csv(PROC / "vhp_provinces.csv").set_index("province_id").name
    v["district"] = v.province_id.map(names)
    k = v[v.district.isin(["Kotido", "Moroto", "Nakapiripirit"]) & (v.week >= 17) & (v.week <= 36)]
    kv = k.groupby("year").VCI.mean()
    t = pd.read_csv(RES / "fp_ipc_karamoja.csv", parse_dates=["date"])
    t = t[t.dataset == "CHIRPS"].copy()
    t["vci"] = t.harvest_year.map(kv)
    r = stats.spearmanr(t.vci, t.share_phase3plus, nan_policy="omit")
    # also: trend in IPC over time
    tt = stats.spearmanr(t.date.astype("int64"), t.share_phase3plus)
    return dict(n=int(t.vci.notna().sum()), spearman_vci_vs_phase3=r[0], p=r[1], spearman_time_vs_phase3=tt[0], p_time=tt[1])


def yield_validation(ds, dname):
    fy = pd.read_csv(PROC / "faostat_uganda_qcl.csv")
    fy = fy[fy.Element == "Yield"].pivot(index="year", columns="Item", values="value")
    nat = {}
    for s in ("S1", "S2"):
        for crop in ("maize", "beans"):
            nat[f"{s}_{crop}"] = pd.Series(np.nanmean(ds[f"{s}_{crop}_A"].values, 1), index=ds.year.values)
    nat = pd.DataFrame(nat)
    nat["maize_both"] = nat[["S1_maize", "S2_maize"]].mean(1)
    nat["beans_both"] = nat[["S1_beans", "S2_beans"]].mean(1)
    out = []
    for item, col in (("Maize (corn)", "maize_both"), ("Beans, dry", "beans_both"), ("Sorghum", "maize_both"), ("Millet", "maize_both")):
        y = fy[item].dropna()
        y = y[(y.index >= 1981) & (y.index <= 2024)]
        rel = np.log(y) - np.log(y).rolling(7, center=True, min_periods=4).median()
        repeats = float((y.diff() == 0).mean())
        j = rel.index.intersection(nat.index)
        r, p = stats.spearmanr(rel[j], nat.loc[j, col])
        out.append(dict(dataset=dname, item=item, wrsi_series=col, n=len(j), spearman=r, p=p, share_years_unchanged=repeats))
    return pd.DataFrame(out), nat


def ipc_validation(ds, dname):
    d = pd.read_csv(PROC / "fews_ipc_uganda.csv", low_memory=False)
    d = d[(d.scenario_name == "Current Situation") & d.value.notna()]
    d["district"] = d.geographic_unit_full_name.str.split(", ").str[-3]
    kar = ["Kaabong", "Kotido", "Abim", "Moroto", "Napak", "Nakapiripirit", "Amudat", "Nabilatuk", "Karenga"]
    k = d[d.district.isin(kar)].copy()
    k["date"] = pd.to_datetime(k.projection_start)
    q = k.groupby("date").apply(lambda x: pd.Series({"share_phase3plus": float(np.mean(x.value >= 3)), "mean_phase": x.value.mean()}))
    zk = [i for i, n in zone_names().items() if n.startswith("Karamoja")][0]
    mk = ds.zone.values == zk
    w = pd.Series(np.nanmean(ds["S1_maize_A"].values[:, mk], 1), index=ds.year.values)  # Karamoja's single main season
    f = pd.Series(np.nanmean(ds["S1_maize_A"].values[:, mk] < 50, 1), index=ds.year.values)
    rows = []
    for dt, r in q.iterrows():
        # the harvest that matters: main season of the same year if Oct-Dec, of previous year if Jan-Sep
        hy = dt.year if dt.month >= 10 else dt.year - 1
        if hy in w.index:
            rows.append(dict(date=dt, harvest_year=hy, share_phase3plus=r.share_phase3plus, mean_phase=r.mean_phase,
                             wrsi=w[hy], fail_share=f[hy]))
    t = pd.DataFrame(rows)
    rr = stats.spearmanr(t.fail_share, t.share_phase3plus)
    return t, dict(dataset=dname, n=len(t), spearman_fail_vs_phase3=rr[0], p=rr[1])


# ------------------------------------------------------------------ figures
def cell_map(ax, c, value, cmap, norm, title, sig=None, res=0.25):
    from matplotlib.patches import Rectangle
    draw_borders(ax, UG_EXTENT)
    for la, lo, v in zip(c.lat, c.lon, value):
        if np.isfinite(v):
            ax.add_patch(Rectangle((lo - res / 2, la - res / 2), res, res, color=cmap(norm(v)), lw=0, zorder=3))
    if sig is not None:
        ax.scatter(c.lon[sig], c.lat[sig], s=2.5, c=INK, lw=0, zorder=7)
    ax.set_title(title, fontsize=9)


def figures(dss, cells, ftab, ttab):
    c = cells[(cells.dataset == "CHIRPS") & (cells.crop == "maize") & (cells.onset == "A") & (cells.threshold == 80)]
    fig, axs = plt.subplots(2, 3, figsize=(13, 8.6))
    nrm = BoundaryNorm([0, 5, 10, 15, 20, 30, 40, 60, 100], 256)
    dn = BoundaryNorm([-30, -20, -10, -5, 5, 10, 20, 30], 256, extend="both")
    for i, s in enumerate(("S1", "S2")):
        d = c[c.season == s].reset_index(drop=True)
        cell_map(axs[i, 0], d, 100 * d.fail_early, CMAP_RISK, nrm, f"{'First' if s == 'S1' else 'Second'} season: maize failure, 1981-2003 (%)")
        cell_map(axs[i, 1], d, 100 * d.fail_late, CMAP_RISK, nrm, f"{'First' if s == 'S1' else 'Second'} season: maize failure, 2004-2025 (%)")
        cell_map(axs[i, 2], d, 100 * (d.fail_late - d.fail_early), CMAP_RAIN.reversed(), dn,
                 "Change (percentage points; dots = FDR-significant)", sig=d.sig_fdr.values)
    fig.colorbar(plt.cm.ScalarMappable(nrm, CMAP_RISK), ax=axs[:, :2], shrink=0.5, label="% of seasons with WRSI < 80 or no onset")
    fig.colorbar(plt.cm.ScalarMappable(dn, CMAP_RAIN.reversed()), ax=axs[:, 2], shrink=0.5, label="percentage points (red = riskier)")
    save(fig, "fp01_failure_maps.png")

    # reversal: which season is more reliable
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 4.6))
    s1 = c[c.season == "S1"].reset_index(drop=True)
    s2 = c[c.season == "S2"].reset_index(drop=True)
    dn2 = BoundaryNorm([-40, -20, -10, -5, 5, 10, 20, 40], 256, extend="both")
    for ax, col, t in ((axs[0], "fail_early", "1981-2003"), (axs[1], "fail_late", "2004-2025")):
        cell_map(ax, s1, 100 * (s1[col] - s2[col]), CMAP_RAIN.reversed(), dn2, f"First minus second season maize failure, {t}")
    fig.colorbar(plt.cm.ScalarMappable(dn2, CMAP_RAIN.reversed()), ax=axs, shrink=0.6,
                 label="percentage points (red = first season riskier)")
    save(fig, "fp02_season_balance.png")


def main():
    dss = {d: compute(d) for d in ("CHIRPS", "ARC2")}
    ftab, cells = failure_tables(dss)
    ttab = timing_tables(dss)
    val = []
    vdfs = []
    for d, ds in dss.items():
        vdf, vres = vhi_validation(ds, d)
        vdfs.append(vdf)
        val.append(vres)
    pd.concat(vdfs).to_csv(RES / "fp_vhi_district_year.csv", index=False)
    pd.concat(val).round(3).to_csv(RES / "fp_validation_vhi.csv", index=False)
    yv, nat = zip(*[yield_validation(ds, d) for d, ds in dss.items()])
    pd.concat(yv).round(3).to_csv(RES / "fp_validation_yield.csv", index=False)
    iv = [ipc_validation(ds, d) for d, ds in dss.items()]
    pd.concat([t.assign(dataset=d) for (t, _), d in zip(iv, dss)]).to_csv(RES / "fp_ipc_karamoja.csv", index=False)
    pd.DataFrame([r for _, r in iv]).round(3).to_csv(RES / "fp_validation_ipc.csv", index=False)
    figures(dss, cells, ftab, ttab)
    vr = vci_reliability()
    iv2 = ipc_vs_vci()
    pd.DataFrame([iv2]).round(3).to_csv(RES / "fp_validation_ipc_vci.csv", index=False)
    print(vr.round(2).to_string())
    print(iv2)
    print(ftab[(ftab.crop == "maize") & (ftab.onset == "A")].round(2).to_string())
    print(ttab[ttab.zone == "Uganda"].round(1).to_string())
    print(pd.concat(val).round(2).to_string())
    print(pd.concat(yv).round(2).to_string())
    print(pd.DataFrame([r for _, r in iv]).round(2).to_string())


if __name__ == "__main__":
    main()
