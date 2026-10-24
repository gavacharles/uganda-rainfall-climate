"""Flood x AMR paper 1, step 2: routed source load, flood exposure, hotspot index, rank stability, sampling frame.

Load. Each source class is placed on the 30 m Copernicus grid and accumulated downstream (D8, pysheds, as in
kd_network). Accumulation is linear, so each class is routed once and any weighting is a weighted sum afterwards:
  L_k = sum over classes c of w_c x A_c(k),  A_c(k) = class-c sources upstream of stretch k
On-site sanitation is carried by population (GHS-POP, per 1,000 residents). Relative weights (central value, range for
the sensitivity test, log-uniform): wastewater works 50 (20-100), hospital 10 (5-20), abattoir 5 (2-10), clinic 2 (1-4),
market 1 (0.5-2), waste site 0.5 (0.2-1), sanitation 1 per 1,000 people (0.5-2). They rank expected loads of resistant
faecal bacteria and resistance genes from the literature; they are not measured concentrations.
Exposure. From the screening flood model (kd_roads stage states, 2020 silted channels): for each stretch and design storm
(2-100 years), people (GHS-POP 2020), buildings (Microsoft footprints) and water points (WPdx) on 30 m squares with
10 cm or more of water; expected annual exposure integrates over annual exceedance probability.
Index. H_k = (L_k / median L) x E_k (expected annual people exposed). Rank stability: share of 1,000 weight draws in
which a stretch is in the top 10%.
Also: 1990 vs 2020 (population and paving; facility counts held at today's), clean-channel scenario, and a stratified
sampling frame (high/low load x high/low exposure, plus upland controls) for paper 2.
Outputs: results/am_stretches.csv, results/am_summary.csv, results/am_sampling_frame.csv, data/kd/amr/am_rasters.npz
"""
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
import xarray as xr

from common import PROC, RES, ROOT

KD = ROOT / "data" / "kd"
AM = KD / "amr"
sys.path.insert(0, str(ROOT / "src"))
CLASSES = ["wastewater", "hospital", "abattoir", "clinic", "market", "waste", "sanitation"]
W0 = dict(wastewater=50, hospital=10, abattoir=5, clinic=2, market=1, waste=0.5, sanitation=1.0)
WR = dict(wastewater=(20, 100), hospital=(5, 20), abattoir=(2, 10), clinic=(1, 4), market=(0.5, 2), waste=(0.2, 1), sanitation=(0.5, 2))
TS = [2, 5, 10, 25, 50, 100]


def routed():
    """Upstream count of each source class (and population, per 1,000) on the DEM grid."""
    f = AM / "am_rasters.npz"
    if f.exists():
        return dict(np.load(f))
    from pysheds.grid import Grid
    from pysheds.sview import Raster
    grid = Grid.from_raster(str(PROC / "kampala_dem.tif"))
    dem = grid.read_raster(str(PROC / "kampala_dem.tif"))
    fdir = grid.flowdir(grid.resolve_flats(grid.fill_depressions(grid.fill_pits(dem))), dirmap=(64, 128, 1, 2, 4, 8, 16, 32))
    with rasterio.open(PROC / "kampala_dem.tif") as r:
        tr, shape = r.transform, r.shape
    src = gpd.read_file(AM / "sources.gpkg")
    pop = xr.open_dataset(PROC / "kampala_ghs_pop.nc").pop
    xs = tr.c + tr.a * (np.arange(shape[1]) + 0.5)
    ys = tr.f + tr.e * (np.arange(shape[0]) + 0.5)
    out = {}
    for c in CLASSES + ["sanitation1990"]:
        w = np.zeros(shape, "float64")
        if c.startswith("sanitation"):
            e = 1990 if c.endswith("1990") else 2020
            p = pop.sel(epoch=e).sel(lat=ys, lon=xs, method="nearest").values.astype("float64")
            w = np.nan_to_num(p) / 9.0 / 1000.0            # GHS-POP cell (~90 m) shared over 9 cells of 30 m, per 1,000 people
        else:
            g = src[src.cls == c]
            col = ((g.geometry.x.values - tr.c) / tr.a).astype(int); row = ((g.geometry.y.values - tr.f) / tr.e).astype(int)
            ok = (row >= 0) & (row < shape[0]) & (col >= 0) & (col < shape[1])
            np.add.at(w, (row[ok], col[ok]), 1.0)
        acc = grid.accumulation(fdir, weights=Raster(w, viewfinder=fdir.viewfinder), dirmap=(64, 128, 1, 2, 4, 8, 16, 32))
        out[c] = np.asarray(acc, "float32")
        print("routed", c, round(float(w.sum()), 1), flush=True)
    out["transform"] = np.array(tr)[:6]
    np.savez_compressed(f, **out)
    return out


def stretch_loads(s, R):
    """Each stretch takes the routed values at its downstream-most sample (highest flow accumulation)."""
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        acc, tr = r.read(3), r.transform
    rows = []
    for k, g in enumerate(s.to_crs(32636).geometry.values):
        pts = [g.interpolate(d) for d in np.linspace(0, g.length, max(2, int(g.length // 30) + 1))]
        ll = gpd.GeoSeries(pts, crs=32636).to_crs(4326)
        col = ((ll.x.values - tr.c) / tr.a).astype(int).clip(0, acc.shape[1] - 1)
        row = ((ll.y.values - tr.f) / tr.e).astype(int).clip(0, acc.shape[0] - 1)
        i = int(np.argmax(acc[row, col]))
        rows.append((row[i], col[i]))
    rc = np.array(rows)
    return pd.DataFrame({c: R[c][rc[:, 0], rc[:, 1]] for c in CLASSES + ["sanitation1990"]})


def exposure(s, h):
    """People, buildings and water points flooded (>= 10 cm) per stretch and design storm, today and alternatives."""
    from kd_roads import stage_states
    cl = np.load(KD / "depth_cells.npz")
    st = stage_states(s, h)
    a, _, c0, _, e, f0 = cl["transform"]
    lon, lat = c0 + a * (cl["cols"] + 0.5), f0 + e * (cl["rows"] + 0.5)
    pop = xr.open_dataset(PROC / "kampala_ghs_pop.nc").pop
    p20 = np.nan_to_num(pop.sel(epoch=2020).sel(lat=xr.DataArray(lat), lon=xr.DataArray(lon), method="nearest").values) / 9.0
    p90 = np.nan_to_num(pop.sel(epoch=1990).sel(lat=xr.DataArray(lat), lon=xr.DataArray(lon), method="nearest").values) / 9.0
    key = (cl["rows"].astype(np.int64) << 20) + cl["cols"]
    def per_cell(gdf):
        x, y = gdf.geometry.x.values, gdf.geometry.y.values
        k = (((y - f0) / e).astype(np.int64) << 20) + ((x - c0) / a).astype(np.int64)
        u, n = np.unique(k, return_counts=True)
        m = dict(zip(u, n))
        return np.array([m.get(v, 0) for v in key], "float32")
    b = gpd.read_parquet(KD / "ms_buildings.parquet")
    nb = per_cell(gpd.GeoDataFrame(geometry=b.geometry.centroid, crs=4326))
    del b
    nw = per_cell(gpd.read_file(AM / "water_points.gpkg"))
    out = {}
    for state, pp in (("2020 silted", p20), ("2020 clean", p20), ("1990 city", p90)):
        H = st[state]
        wet = (H[cl["seg"]] - cl["hand"][:, None]) >= 0.0999           # cells x storms
        res = {}
        for name, v in (("people", pp), ("buildings", nb), ("water_points", nw)):
            M = np.zeros((len(s), len(TS)))
            for j in range(len(TS)):
                np.add.at(M[:, j], cl["seg"][wet[:, j]], v[wet[:, j]])
            res[name] = M
        out[state] = res
    return out


def ead(M):
    """Expected annual value: integrate over annual exceedance probability (trapezoid), 2- to 100-year storms."""
    p = 1 / np.array(TS, float)
    return (np.trapz(M[:, ::-1], p[::-1], axis=1) + M[:, -1] * p[-1])     # plus the tail beyond 100 years at the 100-year value


def main():
    from kf_export import segments
    s, h = segments()
    R = routed()
    L = stretch_loads(s, R)
    X = exposure(s, h)
    df = pd.DataFrame({"seg": np.arange(len(s)), "name": s["name"].fillna("").values, "system": s["system"].fillna("").values,
                       "up_km2": h.A_km2.values})
    for c in CLASSES + ["sanitation1990"]:
        df["up_" + c] = L[c].values.round(3)
    df["load"] = sum(W0[c] * L[c] for c in CLASSES)
    df["load_1990"] = df.load - W0["sanitation"] * (L["sanitation"] - L["sanitation1990"])
    for state, tag in (("2020 silted", ""), ("2020 clean", "_clean"), ("1990 city", "_1990")):
        for v in ("people", "buildings", "water_points"):
            df[f"eae_{v}{tag}"] = ead(X[state][v]).round(2)
        df[f"people_10yr{tag}"] = X[state]["people"][:, TS.index(10)].round(1)
    ref = np.median(df.load[df.load > 0])
    df["index"] = df.load / ref * df.eae_people
    df["index_clean"] = df.load / ref * df.eae_people_clean
    df["index_1990"] = df.load_1990 / ref * df.eae_people_1990
    # rank stability over weight uncertainty
    rng = np.random.default_rng(7)
    A = np.stack([L[c].values for c in CLASSES], 1)
    top = np.zeros(len(df))
    n_top = int(np.ceil(0.1 * (df.eae_people > 0).sum()))
    for _ in range(1000):
        w = np.array([np.exp(rng.uniform(np.log(WR[c][0]), np.log(WR[c][1]))) for c in CLASSES])
        idx = (A @ w) * df.eae_people.values
        top[np.argsort(-idx)[:n_top]] += 1
    df["p_top10"] = (top / 1000).round(3)
    df["rank"] = df["index"].rank(ascending=False, method="min").astype(int)
    df.to_csv(RES / "am_stretches.csv", index=False)

    # summary
    exp = df[df.eae_people > 0]
    topk = df.nsmallest(n_top, "rank")
    summ = {
        "stretches": len(df), "stretches with flood exposure": int((df.eae_people > 0).sum()),
        "expected annual people exposed, 2020 silted": round(df.eae_people.sum()), "same, clean channels": round(df.eae_people_clean.sum()),
        "same, 1990 city": round(df.eae_people_1990.sum()),
        "expected annual buildings exposed": round(df.eae_buildings.sum()), "expected annual water points exposed": round(df.eae_water_points.sum(), 1),
        "people exposed, 10-year storm": round(df.people_10yr.sum()), "water points exposed, 10-year storm":
            round(float(X["2020 silted"]["water_points"][:, TS.index(10)].sum()), 1),
        "top-10% stretches": n_top, "share of index in top 10%": round(topk["index"].sum() / df["index"].sum(), 3),
        "top-10% stretches robust (p_top10 >= 0.8)": int((topk.p_top10 >= 0.8).sum()),
        "index total, clean channels / silted": round(df.index_clean.sum() / df["index"].sum(), 3),
        "index total, 1990 / 2020": round(df.index_1990.sum() / df["index"].sum(), 3),
    }
    pd.Series(summ).to_csv(RES / "am_summary.csv", header=["value"])
    print(pd.Series(summ).to_string(), flush=True)
    print(topk.sort_values("rank")[["rank", "name", "system", "load", "eae_people", "p_top10"]].head(15).to_string(), flush=True)
    sampling_frame(s, df)


def sampling_frame(s, df):
    """Six sites per stratum (high/low routed load x high/low exposure) and six upland controls, at least 1 km apart."""
    c = s.to_crs(32636).geometry.centroid
    df = df.assign(x=c.x.values, y=c.y.values)
    e = df[df.eae_people > 0].copy()
    e["L"] = np.where(e.load >= e.load.median(), "high load", "low load")
    e["E"] = np.where(e.eae_people >= e.eae_people.median(), "high exposure", "low exposure")
    ctrl = df[(df.eae_people == 0) & (df.up_km2 >= 1)].assign(L="control", E="no flooding")
    picks = []
    for (lv, ev), g in list(e.groupby(["L", "E"])) + [(("control", "no flooding"), ctrl)]:
        g = g.sort_values("index" if lv != "control" else "load", ascending=False)
        chosen = []
        for _, r in g.iterrows():
            if all(np.hypot(r.x - q.x, r.y - q.y) >= 1000 for q in chosen + picks):
                chosen.append(r)
            if len(chosen) == 6:
                break
        picks += chosen
    f = pd.DataFrame(picks)
    ll = gpd.GeoSeries(gpd.points_from_xy(f.x, f.y), crs=32636).to_crs(4326)
    f["lon"], f["lat"] = ll.x.round(5).values, ll.y.round(5).values
    f["stratum"] = f.L + ", " + f.E
    f[["stratum", "seg", "name", "system", "load", "eae_people", "p_top10", "lon", "lat"]].to_csv(RES / "am_sampling_frame.csv", index=False)
    print(f.stratum.value_counts().to_string(), flush=True)


if __name__ == "__main__":
    main()
