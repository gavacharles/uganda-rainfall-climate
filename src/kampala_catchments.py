"""Kampala drainage catchments from the Copernicus 30 m DEM, and their land-cover history.

Catchments: flow routing (pysheds, D8) on the conditioned DEM; an urban catchment ends where its channel enters a
large wetland (WorldCover class 90, > 0.3 km2) or Lake Victoria (class 80), or leaves the study box. Outlets with
>= 4 km2 upstream area define catchments; those with >= 40 % of their area inside Kampala city (KCCA, geoBoundaries
ADM2 'Kampala') are kept for analysis.
Valley floor: height above nearest drainage (HAND) < 3 m on streams of >= 0.5 km2 - the zone of former wetlands and
floodplains.
Land cover: GHSL built-up surface fraction per epoch (1975-2030); WorldCover 2021 class fractions; impervious
fraction = k x GHSL built fraction, with k calibrated so GHSL 2020 matches WorldCover 2021 'built-up' (class 50)
across catchments.

Run: python kampala_catchments.py [kampala|johannesburg]. For Johannesburg the minimum catchment is 10 km2 (the
metro is ~8 times larger), only water bodies > 1 km2 act as sinks, and the city boundary is the City of Johannesburg
Metropolitan Municipality. Catchments are named after the longest named OpenStreetMap waterway inside them.

Outputs: data/processed/<city>_catchments.tif, results/<city>_catchments.csv, results/<city>_landcover_epochs.csv
"""
import sys
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
import xarray as xr
from pysheds.grid import Grid
from rasterio.features import shapes
from rasterio.warp import Resampling, reproject
from scipy import ndimage

from common import PROC, RES

CITY = sys.argv[1] if len(sys.argv) > 1 and __name__ == "__main__" else "kampala"
DEM = PROC / f"{CITY}_dem.tif"
WC = PROC / f"{CITY}_worldcover.tif"
NEW = ("nairobi", "dar_es_salaam", "lagos")
MIN_AREA = {"kampala": 4.0, "johannesburg": 10.0, **{c: 5.0 for c in NEW}}
MIN_SINK = {"kampala": 0.0, "johannesburg": 1.0, **{c: 1.0 for c in NEW}}
TRIB = {"kampala": None, "johannesburg": 15.0, **{c: 15.0 for c in NEW}}  # km2: close catchments where a tributary this large joins
MIN_BUILT = {"kampala": 0.0, "johannesburg": 0.15, **{c: 0.15 for c in NEW}}  # keep urban catchments only (WorldCover 2021 built-up share)  # km2; Kampala's only open water is Lake Victoria and its bays
LANDMARKS = {  # neighbourhood points used only to name catchments (approximate locations)
    "Nakivubo": (0.315, 32.582), "Lubigi": (0.352, 32.556), "Nalukolongo": (0.300, 32.545),
    "Kinawataka": (0.335, 32.640), "Kansanga": (0.278, 32.602), "Walufumbe": (0.375, 32.612),
    "Nakelere": (0.352, 32.668),
}


def load():
    grid = Grid.from_raster(str(DEM))
    dem = grid.read_raster(str(DEM))
    with rasterio.open(DEM) as r:
        tr, crs, shape = r.transform, r.crs, r.shape
    wc = np.zeros(shape, np.uint8)
    with rasterio.open(WC) as w:
        reproject(w.read(1), wc, src_transform=w.transform, src_crs=w.crs, dst_transform=tr, dst_crs=crs,
                  resampling=Resampling.mode)
    return grid, dem, wc, tr


def city_geometry():
    if CITY == "kampala":
        d2 = gpd.read_file(PROC / "uganda_adm2.geojson")
        return d2[d2.shapeName == "Kampala"].geometry.union_all()
    return gpd.read_file(PROC / f"{CITY}_boundary.geojson").geometry.union_all()


def waterway_names(cat, keep_ids, xs, ys):
    """Longest named OSM waterway inside each catchment."""
    f = PROC / f"{CITY}_waterways.geojson"
    if not f.exists():
        return {}
    w = gpd.read_file(f)
    out = {}
    tr = (xs[0], xs[1] - xs[0], ys[0], ys[1] - ys[0])
    for _, r in w.iterrows():
        g = r.geometry
        n = max(int(g.length / abs(tr[1])) * 2, 2)
        pts = [g.interpolate(t, normalized=True) for t in np.linspace(0, 1, n)]
        jj = np.clip(np.round((np.array([p.x for p in pts]) - tr[0]) / tr[1]).astype(int), 0, len(xs) - 1)
        ii = np.clip(np.round((np.array([p.y for p in pts]) - tr[2]) / tr[3]).astype(int), 0, len(ys) - 1)
        ids = cat[ii, jj]
        for k in keep_ids:
            L = np.mean(ids == k) * g.length
            if L > 0:
                out.setdefault(k, {}).setdefault(r["name"], 0.0)
                out[k][r["name"]] += L
    return {k: max(v, key=v.get) for k, v in out.items()}


def cell_area_km2(tr, shape):
    lat = tr.f + tr.e * (np.arange(shape[0]) + 0.5)
    dy = abs(tr.e) * 111.32
    dx = tr.a * 111.32 * np.cos(np.deg2rad(lat))
    return np.repeat((dx * dy)[:, None], shape[1], 1)


def main():
    grid, dem, wc, tr = load()
    A = cell_area_km2(tr, dem.shape)
    water = wc == 80
    labw, nw = ndimage.label(water)
    wsz = ndimage.sum(A, labw, range(1, nw + 1)) if nw else np.array([])
    lake = np.isin(labw, 1 + np.flatnonzero(wsz > MIN_SINK[CITY]))
    wet = wc == 90
    lab, n = ndimage.label(wet)
    sizes = ndimage.sum(A, lab, range(1, n + 1))
    bigwet = np.isin(lab, 1 + np.flatnonzero(sizes > 0.3))
    # condition DEM; flatten lake so it acts as a sink surface
    d = dem.copy()
    if lake.any():
        d[lake] = np.nanmin(dem[~lake]) - 1
    pit = grid.fill_pits(d)
    flooded = grid.fill_depressions(pit)
    inflated = grid.resolve_flats(flooded)
    dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
    fdir = grid.flowdir(inflated, dirmap=dirmap)
    acc = grid.accumulation(fdir, dirmap=dirmap)
    acc_km2 = np.asarray(acc) * A.mean()
    # downstream pointer for each cell (flat index); terminal cells point to themselves
    dr = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
    fd = np.asarray(fdir)
    H, W = fd.shape
    sink = lake | bigwet
    I, J = np.indices((H, W))
    di, dj = np.zeros((H, W), int), np.zeros((H, W), int)
    for k, (a_, b_) in dr.items():
        di[fd == k], dj[fd == k] = a_, b_
    ii, jj = I + di, J + dj
    out = (ii < 0) | (ii >= H) | (jj < 0) | (jj >= W) | ((di == 0) & (dj == 0))
    ii, jj = np.clip(ii, 0, H - 1), np.clip(jj, 0, W - 1)
    xs = tr.c + tr.a * (np.arange(W) + 0.5)
    ys = tr.f + tr.e * (np.arange(H) + 0.5)
    city = city_geometry()
    LO, LA = np.meshgrid(xs, ys)
    incity = shapely.contains_xy(city, LO, LA)
    flat = np.arange(H * W).reshape(H, W)
    exits_city = incity & ~incity[ii, jj]
    terminal = out | sink[ii, jj] | sink | exits_city
    if TRIB[CITY]:
        joins = (acc_km2 >= TRIB[CITY]) & ((acc_km2[ii, jj] - acc_km2) >= TRIB[CITY] + 0.1)
        terminal |= joins
    reason = np.where(sink[ii, jj] & lake[ii, jj], "lake", np.where(sink[ii, jj], "wetland",
                      np.where(exits_city, "city boundary", np.where(terminal & ~out, "confluence", "box edge"))))
    nxt = np.where(terminal, flat, flat[ii, jj]).ravel()
    clat = np.cos(np.deg2rad(np.mean(ys)))
    step = np.where(terminal, 0.0, 30.0 * np.hypot(di, dj * clat)).ravel()

    # terminal (outlet) of each cell, and flow distance to it (pointer doubling)
    nx, dist = nxt.copy(), step.copy()
    for _ in range(40):
        nd = dist + dist[nx] * (nx != np.arange(H * W))
        nn = nx[nx]
        if np.array_equal(nn, nx):
            break
        dist, nx = nd, nn
    term = nx.reshape(H, W)
    dist = dist.reshape(H, W)
    tarea = np.bincount(term.ravel(), weights=A.ravel(), minlength=H * W)
    cat = np.zeros((H, W), np.int32)
    outlets = [divmod(int(t), W) for t in np.flatnonzero(tarea >= MIN_AREA[CITY])]
    outlets.sort(key=lambda p: -tarea[p[0] * W + p[1]])
    for k, (i, j) in enumerate(outlets, start=1):
        cat[term == i * W + j] = k
    cat[sink] = 0
    # HAND (valley floor)
    stream = (acc_km2 >= 0.5) | sink
    nx2 = np.where(stream.ravel(), np.arange(H * W), nxt)
    for _ in range(40):
        nn = nx2[nx2]
        if np.array_equal(nn, nx2):
            break
        nx2 = nn
    hand = np.asarray(inflated) - np.asarray(inflated).ravel()[nx2].reshape(H, W)
    valley = (hand < 3) & ~lake
    slope_pct = 100 * np.hypot(*np.gradient(dem, 30.0))
    rows = []
    for k in np.unique(cat[cat > 0]):
        m = cat == k
        area = A[m].sum()
        if area < MIN_AREA[CITY]:
            continue
        share_city = A[m & incity].sum() / area
        name = next((nm for nm, (la, lo) in LANDMARKS.items()
                     if m[np.abs(ys - la).argmin(), np.abs(xs - lo).argmin()]), None) if CITY == "kampala" else None
        i, j = outlets[k - 1]
        s = slope_pct[m]
        relief = np.nanpercentile(dem[m], 98) - dem[i, j]
        # longest flow path ~ max flow distance
        L = float(np.nanmax(np.where(m, dist, np.nan)))
        rows.append(dict(id=int(k), name=name, area_km2=area, share_in_city=share_city, outlet_lat=ys[i], outlet_lon=xs[j],
                         outlet_to=str(reason[i, j]),
                         mean_slope_pct=float(np.nanmean(s)), relief_m=float(relief), flow_length_m=float(L),
                         valley_floor_share=float(A[m & valley].sum() / area)))
    cdf = pd.DataFrame(rows).sort_values("area_km2", ascending=False)
    keep = cdf[cdf.share_in_city >= 0.5].copy()
    if MIN_BUILT[CITY]:
        bshare = {k: A[(cat == k) & (wc == 50)].sum() / A[cat == k].sum() for k in keep.id}
        keep = keep[keep.id.map(bshare) >= MIN_BUILT[CITY]].copy()
    osm = waterway_names(cat, list(keep.id), xs, ys)
    keep["osm_name"] = keep.id.map(osm)
    # land cover per catchment: WorldCover fractions
    for cls, nm in ((10, "tree"), (20, "shrub"), (30, "grass"), (40, "crop"), (50, "builtup"), (60, "bare"), (80, "water"), (90, "wetland")):
        keep[f"wc2021_{nm}"] = [A[(cat == k) & (wc == cls)].sum() / A[cat == k].sum() for k in keep.id]
    # GHSL epochs on the DEM grid
    g = xr.open_dataarray(PROC / f"{CITY}_ghsl_built.nc")
    gl = g.sel(lat=ys, lon=xs, method="nearest").values / (
        (np.abs(np.diff(g.lon.values).mean()) * 111320 * clat) * (np.abs(np.diff(g.lat.values).mean()) * 111320))
    gl = np.clip(gl, 0, 1)
    ep = []
    for e, epoch in enumerate(g.epoch.values):
        for k, nm in zip(keep.id, keep.name):
            m = cat == k
            ep.append(dict(id=int(k), name=nm, epoch=int(epoch),
                           built_frac=float((gl[e] * A)[m].sum() / A[m].sum()),
                           built_frac_valley=float((gl[e] * A)[m & valley].sum() / max(A[m & valley].sum(), 1e-9)),
                           built_frac_upland=float((gl[e] * A)[m & ~valley].sum() / max(A[m & ~valley].sum(), 1e-9))))
    ep = pd.DataFrame(ep)
    b20 = ep[ep.epoch == 2020].set_index("id").built_frac
    ratio = (keep.set_index("id").wc2021_builtup / b20).replace([np.inf, -np.inf], np.nan)
    kfac = float(np.nanmedian(ratio))
    ep["impervious_frac"] = np.clip(kfac * ep.built_frac, 0, 0.95)
    ep.attrs["k"] = kfac
    keep["k_impervious_over_ghsl"] = kfac
    keep.to_csv(RES / f"{CITY}_catchments.csv", index=False)
    ep.to_csv(RES / f"{CITY}_landcover_epochs.csv", index=False)
    prof = dict(driver="GTiff", height=H, width=W, count=3, dtype="float32", crs="EPSG:4326", transform=tr, compress="deflate")
    with rasterio.open(PROC / f"{CITY}_catchments.tif", "w", **prof) as out:
        out.write(cat.astype("float32"), 1)
        out.write(hand.astype("float32"), 2)
        out.write(acc_km2.astype("float32"), 3)
    print(cdf.head(25).round(2).to_string())
    print(keep.round(3).to_string())
    print("k =", round(kfac, 2))
    print(ep.pivot(index="epoch", columns="id", values="built_frac").round(3).to_string())


if __name__ == "__main__":
    main()
