"""Flood x AMR paper 1, step 6: who is exposed, the wetland filter, and the drinking-water intake.

who       Relative Wealth Index (Meta / Chi et al. 2022, ~2.4 km tiles) at each stretch; median footprint of flooded
          buildings (small, dense buildings mark informal housing); WPdx water points within 500 m per 1,000 residents.
          Distribution of resistance-weighted exposure (load x expected annual people) across Kampala-relative wealth
          quintiles; concentration index (negative: borne by the poorer).
wetland   Vegetated valley floor (HAND < 3 m, NDVI > 0.45, Landsat dry-season composites as in paper 2) in 1986 and 2025,
          on the 30 m terrain grid. For every channel stretch: length of its downstream D8 path that runs through
          vegetated valley floor before leaving the map (the bay or the Mayanja). Load-weighted mean path, 1986 vs 2025.
intake    Ggaba waterworks (32.639 E, 0.244 N; OpenStreetMap). In each Sentinel-2 turbidity scene: median turbidity of
          water within 1 km of the intake over the open-lake reference; relation with 3-day rain and with the mean
          signal of the five highest-load outlets the same day (am_satcheck).
Outputs: results/am_who.csv, results/am_who_quintiles.csv, results/am_wetland_path.csv, results/am_intake.csv,
results/am_extra_tests.csv
"""
import glob
import json

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from pyproj import Transformer
from scipy import stats

from common import PROC, RES, ROOT

KD = ROOT / "data" / "kd"
AM = KD / "amr"
INTAKE = (32.639, 0.2437)
TESTS = []


def who(s, d):
    rwi = pd.read_csv(AM / "uga_rwi.csv")
    rwi = rwi[(rwi.latitude.between(0.10, 0.52)) & (rwi.longitude.between(32.36, 32.82))]
    c = s.to_crs(4326).geometry.centroid
    tree = gpd.GeoSeries(gpd.points_from_xy(rwi.longitude, rwi.latitude), crs=4326).to_crs(32636)
    import shapely
    cu = c.to_crs(32636).values
    idx = shapely.STRtree(tree.values).nearest(cu)
    d = d.assign(rwi=rwi.rwi.values[idx])
    # flooded buildings' median footprint, per stretch (10-year storm, silted)
    cl = np.load(KD / "depth_cells.npz")
    a, _, c0, _, e, f0 = cl["transform"]
    b = gpd.read_parquet(KD / "ms_buildings.parquet")
    area = b.to_crs(32636).area.values
    bc = b.geometry.centroid
    del b
    key = (((bc.y.values - f0) / e).astype(np.int64) << 20) + ((bc.x.values - c0) / a).astype(np.int64)
    cellseg = dict(zip((cl["rows"].astype(np.int64) << 20) + cl["cols"], cl["seg"]))
    seg = np.array([cellseg.get(k, -1) for k in key])
    m = seg >= 0
    med = pd.Series(area[m]).groupby(seg[m]).median()
    d["bldg_median_m2"] = d.seg.map(med).round(1)
    # water points per 1,000 residents within 500 m of the stretch
    wp = gpd.read_file(AM / "water_points.gpkg").to_crs(32636)
    pop = xr.open_dataset(PROC / "kampala_ghs_pop.nc").pop.sel(epoch=2020)
    near = shapely.STRtree(wp.geometry.values).query(cu, predicate="dwithin", distance=500)
    nwp = np.bincount(near[0], minlength=len(s))
    p500 = pop.sel(lat=xr.DataArray(c.y.values), lon=xr.DataArray(c.x.values), method="nearest").values * 31.0   # ~500 m radius of ~90 m cells
    d["water_points_500m"] = nwp
    d["wp_per_1000"] = np.where(p500 > 0, nwp / p500 * 1000, np.nan).round(2)
    d["amr_exposure"] = d.load * d.eae_people
    ex = d[d.eae_people > 0].copy()
    ex["rwi_q"] = pd.qcut(ex.rwi.rank(method="first"), 5, labels=["Q1 poorest", "Q2", "Q3", "Q4", "Q5 richest"])
    q = ex.groupby("rwi_q", observed=True).agg(stretches=("seg", "size"), people=("eae_people", "sum"), amr_exposure=("amr_exposure", "sum"),
                                               bldg_median_m2=("bldg_median_m2", "median"), rwi=("rwi", "median")).reset_index()
    q["share_people"] = (q.people / q.people.sum()).round(3); q["share_amr_exposure"] = (q.amr_exposure / q.amr_exposure.sum()).round(3)
    q.to_csv(RES / "am_who_quintiles.csv", index=False)
    # concentration index of AMR exposure over wealth rank (Kakwani), stretches weighted equally
    r = ex.rwi.rank(pct=True); y = ex.amr_exposure
    ci = 2 * np.cov(y, r, bias=True)[0, 1] / y.mean()
    top = ex[ex["rank"] <= int(np.ceil(0.1 * len(ex)))]
    TESTS.append(dict(test="concentration index of AMR exposure over wealth (negative = poorer)", n=len(ex), estimate=round(ci, 3)))
    TESTS.append(dict(test="median RWI, top-10% stretches vs other exposed", n=len(top), estimate=f"{top.rwi.median():.3f} vs {ex.drop(top.index).rwi.median():.3f}",
                      p=round(stats.mannwhitneyu(top.rwi, ex.drop(top.index).rwi).pvalue, 4)))
    TESTS.append(dict(test="median flooded-building footprint m2, top-10% vs other exposed", n=len(top),
                      estimate=f"{top.bldg_median_m2.median():.0f} vs {ex.drop(top.index).bldg_median_m2.median():.0f}",
                      p=round(stats.mannwhitneyu(top.bldg_median_m2.dropna(), ex.drop(top.index).bldg_median_m2.dropna()).pvalue, 4)))
    d[["seg", "rwi", "bldg_median_m2", "water_points_500m", "wp_per_1000", "amr_exposure"]].to_csv(RES / "am_who.csv", index=False)
    print(q.to_string(), flush=True)


def wetland(s, d):
    from pysheds.grid import Grid
    grid = Grid.from_raster(str(PROC / "kampala_dem.tif"))
    dem = grid.read_raster(str(PROC / "kampala_dem.tif"))
    dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
    fdir = np.asarray(grid.flowdir(grid.resolve_flats(grid.fill_depressions(grid.fill_pits(dem))), dirmap=dirmap))
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand, acc, tr = r.read(2), r.read(3), r.transform
    H, W = hand.shape
    dr = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
    # vegetated valley floor per year, on the terrain grid
    tf = Transformer.from_crs(4326, 32636, always_xy=True)
    xs = tr.c + tr.a * (np.arange(W) + 0.5); ys = tr.f + tr.e * (np.arange(H) + 0.5)
    chan = acc >= 0.05                                        # cells draining >= 0.05 km2: every channel path
    rr, cc = np.nonzero(chan)
    X, Y = tf.transform(xs[cc], ys[rr])
    out = {}
    for yr in (1986, 2025):
        L = xr.open_dataset(KD / f"sat_landsat_{yr}.nc")
        ndvi = ((L.nir08 - L.red) / (L.nir08 + L.red))
        v = ndvi.sel(x=xr.DataArray(X), y=xr.DataArray(Y), method="nearest").values
        inside = (X > float(L.x.min())) & (X < float(L.x.max())) & (Y > float(L.y.min())) & (Y < float(L.y.max()))
        veg = np.zeros(H * W, bool)
        veg[rr * W + cc] = inside & (v > 0.45) & (hand[rr, cc] < 3)
        out[yr] = veg
    # downstream accumulation of wetland length: process channel cells from the most downstream (largest acc) up
    lin = rr * W + cc
    order = lin[np.argsort(-acc[rr, cc])]
    down = np.full(H * W, -1, np.int64)
    fd = fdir[rr, cc]
    for code, (di, dj) in dr.items():
        k = fd == code
        r2, c2 = rr[k] + di, cc[k] + dj
        ok = (r2 >= 0) & (r2 < H) & (c2 >= 0) & (c2 < W)
        down[lin[k][ok]] = r2[ok] * W + c2[ok]
    step = np.where(np.isin(fd, [128, 2, 8, 32]), 30 * 1.414, 30.0)
    stepf = np.zeros(H * W, "float32"); stepf[lin] = step
    res = {}
    for yr, veg in out.items():
        wl = np.zeros(H * W, "float32"); tot = np.zeros(H * W, "float32")
        for i in order:                                       # downstream cells first
            j = down[i]
            add = stepf[i]
            wl[i] = (add if veg[i] else 0) + (wl[j] if j >= 0 else 0)
            tot[i] = add + (tot[j] if j >= 0 else 0)
        res[yr] = (wl, tot)
        print("wetland path", yr, flush=True)
    # each stretch: its downstream-most cell (as in am_index)
    seg_rc = []
    for g in s.to_crs(32636).geometry.values:
        pts = [g.interpolate(t_) for t_ in np.linspace(0, g.length, max(2, int(g.length // 30) + 1))]
        ll = gpd.GeoSeries(pts, crs=32636).to_crs(4326)
        col = ((ll.x.values - tr.c) / tr.a).astype(int).clip(0, W - 1); row = ((ll.y.values - tr.f) / tr.e).astype(int).clip(0, H - 1)
        i = int(np.argmax(acc[row, col])); seg_rc.append(row[i] * W + col[i])
    seg_rc = np.array(seg_rc)
    w = pd.DataFrame({"seg": d.seg, "system": d.system, "load": d.load,
                      "wet_km_1986": (res[1986][0][seg_rc] / 1000).round(3), "wet_km_2025": (res[2025][0][seg_rc] / 1000).round(3),
                      "path_km": (res[2025][1][seg_rc] / 1000).round(2)})
    w.to_csv(RES / "am_wetland_path.csv", index=False)
    for sysn, g in [("all", w)] + list(w.groupby("system")):
        if g.load.sum() <= 0:
            continue
        m86, m25 = np.average(g.wet_km_1986, weights=g.load), np.average(g.wet_km_2025, weights=g.load)
        TESTS.append(dict(test=f"load-weighted wetland on the downstream path, km, 1986 -> 2025 ({sysn})", n=len(g),
                          estimate=f"{m86:.2f} -> {m25:.2f}"))
    print(pd.DataFrame(TESTS).tail(8).to_string(), flush=True)


def intake():
    import kd_bay as kb
    m = kb.watermask()
    X, Y = np.meshgrid(m.x.values, m.y.values)
    water = m.values.astype(bool)
    zone = kb.zones(m.x.values, m.y.values, water)
    ix, iy = Transformer.from_crs(4326, 32636, always_xy=True).transform(*INTAKE)
    near = water & (np.hypot(X - ix, Y - iy) <= 1000)
    ch = kb.chirps_kla()
    o = pd.read_csv(RES / "am_satcheck_outlets.csv").dropna(subset=["scenes"])
    hi = o.nlargest(5, "load")
    hi_xy = Transformer.from_crs(4326, 32636, always_xy=True).transform(hi.lon.values, hi.lat.values)
    himask = np.zeros_like(water)
    for x_, y_ in zip(*hi_xy):
        himask |= water & (np.hypot(X - x_, Y - y_) <= 400)
    rows = []
    for f in sorted(glob.glob(str(KD / "bay_turb_*.nc"))):
        day = pd.Timestamp(f.split("bay_turb_")[1][:10])
        t = xr.open_dataarray(f).sel(x=m.x, y=m.y, method="nearest").values
        ref = np.nanmedian(np.where(zone == 4, t, np.nan))
        vi, vh = t[near], t[himask]
        vi, vh = vi[np.isfinite(vi)], vh[np.isfinite(vh)]
        if not np.isfinite(ref) or len(vi) < 30 or len(vh) < 20:
            continue
        rows.append(dict(date=day.date(), intake_ratio=float(np.median(vi) / ref), outlets_ratio=float(np.median(vh) / ref),
                         r3=float(ch[day - pd.Timedelta(days=3):day - pd.Timedelta(days=1)].sum())))
    q = pd.DataFrame(rows); q.to_csv(RES / "am_intake.csv", index=False)
    r1 = stats.spearmanr(q.r3, q.intake_ratio); r2 = stats.spearmanr(q.outlets_ratio, q.intake_ratio)
    wet = q.r3 >= 25
    TESTS.append(dict(test="intake turbidity / open lake, median (scenes)", n=len(q), estimate=round(q.intake_ratio.median(), 3)))
    TESTS.append(dict(test="intake ratio vs 3-day rain, Spearman", n=len(q), estimate=round(r1[0], 3), p=round(r1[1], 4)))
    TESTS.append(dict(test="intake ratio vs high-load outlets ratio same day, Spearman", n=len(q), estimate=round(r2[0], 3), p=round(r2[1], 4)))
    TESTS.append(dict(test="intake ratio, wet vs dry scenes (median)", n=len(q), estimate=f"{q.intake_ratio[wet].median():.3f} vs {q.intake_ratio[~wet].median():.3f}",
                      p=round(stats.mannwhitneyu(q.intake_ratio[wet], q.intake_ratio[~wet]).pvalue, 4) if wet.sum() > 2 else None))
    print(q.describe().round(3).to_string(), flush=True)


def main():
    from kf_export import segments
    s, h = segments()
    d = pd.read_csv(RES / "am_stretches.csv")
    who(s, d)
    intake()
    wetland(s, d)
    pd.DataFrame(TESTS).to_csv(RES / "am_extra_tests.csv", index=False)
    print(pd.DataFrame(TESTS).to_string())


if __name__ == "__main__":
    main()
