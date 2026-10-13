"""Kampala drainage study, part 2: channel-segment inventory, flood-risk drivers and validation.

Each OpenStreetMap waterway (drain, ditch, canal, stream, river) in Greater Kampala is cut into <= 200 m segments.
For each segment:
  up_km2            upstream drainage area (Copernicus 30 m DEM, D8; max within ~60 m of the segment)
  up_built_1990/2020 upstream built-up share (GHSL), and the runoff load = area x runoff coefficient
                    (C = 0.25 + 0.65 x built share), its growth since 1990
  valley_built_*    built-up share of the valley floor (HAND < 3 m: former wetland / floodplain) within ~250 m
  wetland_500m      WorldCover 2021 herbaceous-wetland share within ~500 m
  bldg_reserve      buildings (Microsoft footprints, 2023) within 15 m of the channel centreline
  bldg_floodplain   buildings within 150 m standing < 2 m above the nearest drainage line
  waste_100m        mapped waste dumps / disposal points (OSM) within 100 m; markets_300m: markets within 300 m
  crossings         culverts (OSM tunnel=culvert) and road bridges within 25 m (constriction / blockage points)
  hotspot           within 400 m of a reported flood hotspot (data/kd/flood_hotspots.csv, approx. +-500 m)
Each pressure is converted to a percentile rank. The current maintenance-priority index is the equal-weight mean of
the six present-day pressures, and each segment's three highest-ranked ones are reported as its likely causes. The two
change-since-1990 pressures form a separate emerging-risk score. Validation against reported hotspots
(AUC with a 2 km block bootstrap, also within the denser half of channels) is in results/kd_validation.csv.

Outputs: data/kd/segments.gpkg, results/kd_segments.csv, results/kd_drivers.csv, results/kd_validation.csv
"""
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
import xarray as xr
from pysheds.grid import Grid
from pysheds.sview import Raster
from rasterio.warp import Resampling, reproject
from scipy import ndimage
from shapely.ops import substring
from sklearn.metrics import roc_auc_score

from common import PROC, RES, ROOT

KD = ROOT / "data" / "kd"
UTM = 32636
STUDY = (32.45, 0.20, 32.72, 0.42)  # Greater Kampala core
SEG = 200.0
NOW = {  # present-day pressures -> current maintenance priority
    "load_2020": "Runoff load (upstream area x paving)",
    "crossings_per_km": "Culverts & bridges (constrictions)",
    "waste_pressure": "Waste dumps & markets nearby",
    "bldg_reserve_per_km": "Buildings in channel reserve",
    "bldg_floodplain": "Homes on the floodplain",
    "low_wetland": "Little wetland left to buffer",
}
TREND = {  # change since 1990 -> emerging risk
    "load_growth": "Runoff growth since 1990",
    "valley_built_change": "Wetland/floodplain built over since 1990",
}
DRIVERS = {**NOW, **TREND}


def rasters():
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        cat, hand, acc = r.read(1), r.read(2), r.read(3)
        tr, shape = r.transform, r.shape
    with rasterio.open(PROC / "kampala_worldcover.tif") as w:
        wc = np.zeros(shape, np.uint8)
        reproject(w.read(1), wc, src_transform=w.transform, src_crs=w.crs, dst_transform=tr, dst_crs="EPSG:4326",
                  resampling=Resampling.mode)
    xs = tr.c + tr.a * (np.arange(shape[1]) + 0.5)
    ys = tr.f + tr.e * (np.arange(shape[0]) + 0.5)
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc")
    clat = np.cos(np.deg2rad(0.3))
    cell = (abs(float(np.diff(g.lon.values).mean())) * 111320 * clat) * (abs(float(np.diff(g.lat.values).mean())) * 111320)
    built = {e: np.clip(g.sel(epoch=e).sel(lat=ys, lon=xs, method="nearest").values / cell, 0, 1) for e in (1990, 2020)}
    # upstream mean built share: weighted flow accumulation
    grid = Grid.from_raster(str(PROC / "kampala_dem.tif"))
    dem = grid.read_raster(str(PROC / "kampala_dem.tif"))
    inflated = grid.resolve_flats(grid.fill_depressions(grid.fill_pits(dem)))
    dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
    fdir = grid.flowdir(inflated, dirmap=dirmap)
    n = np.asarray(grid.accumulation(fdir, dirmap=dirmap), float)
    up = {}
    for e, b in built.items():
        wr = Raster(b.astype("float64"), viewfinder=fdir.viewfinder)
        up[e] = np.asarray(grid.accumulation(fdir, weights=wr, dirmap=dirmap), float) / np.maximum(n, 1)
    valley = (hand < 3).astype(float)
    k = 17  # ~500 m window at 30 m
    vb = {e: ndimage.uniform_filter(valley * built[e], 17) / np.maximum(ndimage.uniform_filter(valley, 17), 1e-6) for e in built}
    wet = ndimage.uniform_filter((wc == 90).astype(float), 2 * k + 1)
    return dict(tr=tr, xs=xs, ys=ys, cat=cat, hand=hand, acc=acc, up=up, vb=vb, wet=wet, valley_share=ndimage.uniform_filter(valley, 17))


def segments():
    w = gpd.read_file(KD / "osm_waterways.geojson").cx[STUDY[0]:STUDY[2], STUDY[1]:STUDY[3]]
    w = w[w.geom_type == "LineString"].to_crs(UTM)
    rows = []
    for _, r in w.iterrows():
        L = r.geometry.length
        n = max(1, int(np.ceil(L / SEG)))
        for i in range(n):
            g = substring(r.geometry, i * L / n, (i + 1) * L / n)
            if g.length < 5:
                continue
            rows.append(dict(osm_id=r.osm_id, name=r["name"], waterway=r.waterway,
                             culvert=r.tunnel in ("culvert", "yes") or r.culvert == "yes", geometry=g))
    s = gpd.GeoDataFrame(rows, crs=UTM)
    s["seg_id"] = np.arange(len(s))
    s["length_m"] = s.length
    return s


def sample(s, R):
    tr = R["tr"]
    pts, owner = [], []
    for i, g in enumerate(s.to_crs(4326).geometry):
        d = np.linspace(0, g.length, max(2, int(s.length_m.iloc[i] / 15) + 1))
        for p in (g.interpolate(x) for x in d):
            pts.append((p.x, p.y))
            owner.append(i)
    pts, owner = np.array(pts), np.array(owner)
    col = ((pts[:, 0] - tr.c) / tr.a).astype(int)
    row = ((pts[:, 1] - tr.f) / tr.e).astype(int)
    H, W = R["acc"].shape
    off = np.arange(-2, 3)
    rr = np.clip(row[:, None, None] + off[None, :, None], 0, H - 1)
    cc = np.clip(col[:, None, None] + off[None, None, :], 0, W - 1)
    rr, cc = np.broadcast_arrays(rr, cc)
    rr, cc = rr.reshape(len(pts), -1), cc.reshape(len(pts), -1)
    a = R["acc"][rr, cc]
    best = a.argmax(1)
    br, bc = rr[np.arange(len(pts)), best], cc[np.arange(len(pts)), best]
    df = pd.DataFrame({"o": owner, "acc": a.max(1), "u90": R["up"][1990][br, bc], "u20": R["up"][2020][br, bc],
                       "hand": R["hand"][row.clip(0, H - 1), col.clip(0, W - 1)],
                       "cat": R["cat"][row.clip(0, H - 1), col.clip(0, W - 1)],
                       "vb90": R["vb"][1990][row.clip(0, H - 1), col.clip(0, W - 1)],
                       "vb20": R["vb"][2020][row.clip(0, H - 1), col.clip(0, W - 1)],
                       "wet": R["wet"][row.clip(0, H - 1), col.clip(0, W - 1)],
                       "vshare": R["valley_share"][row.clip(0, H - 1), col.clip(0, W - 1)]})
    # per segment: take the downstream-most (max accumulation) sample for hydrology, means for the rest
    idx = df.groupby("o").acc.idxmax()
    hyd = df.loc[idx].set_index("o")[["acc", "u90", "u20"]]
    rest = df.groupby("o")[["hand", "vb90", "vb20", "wet", "vshare"]].mean()
    cat = df.groupby("o").cat.agg(lambda v: v.mode().iloc[0])
    return hyd.join(rest).join(cat)


def counts(s, layer, radius, where=None):
    g = gpd.read_file(KD / layer).to_crs(UTM)
    if where is not None:
        g = g[where(g)]
    g = g.copy()
    g["geometry"] = g.geometry.representative_point() if (g.geom_type != "Point").any() else g.geometry
    tree = shapely.STRtree(g.geometry.values)
    i, _ = tree.query(s.geometry.values, predicate="dwithin", distance=radius)
    return np.bincount(i, minlength=len(s))


def main():
    R = rasters()
    s = segments()
    print("segments", len(s), flush=True)
    a = sample(s, R)
    s = s.join(a, on=s.index.to_series().rename("o")) if False else s.assign(**{c: a[c].reindex(range(len(s))).values for c in a})
    s = s.rename(columns={"acc": "up_km2", "u90": "up_built_1990", "u20": "up_built_2020", "vb90": "valley_built_1990",
                          "vb20": "valley_built_2020", "wet": "wetland_500m", "vshare": "valley_share_500m"})
    C = lambda b: 0.25 + 0.65 * b
    s["load_1990"] = s.up_km2 * C(s.up_built_1990)
    s["load_2020"] = s.up_km2 * C(s.up_built_2020)
    s["load_growth"] = s.load_2020 / s.load_1990.clip(lower=1e-6) - 1
    s["valley_built_change"] = s.valley_built_2020 - s.valley_built_1990
    # buildings
    b = gpd.read_parquet(KD / "ms_buildings.parquet").cx[STUDY[0] - 0.01:STUDY[2] + 0.01, STUDY[1] - 0.01:STUDY[3] + 0.01]
    bc = b.to_crs(UTM).geometry.centroid
    tree = shapely.STRtree(bc.values)
    i, _ = tree.query(s.geometry.values, predicate="dwithin", distance=15)
    s["bldg_reserve"] = np.bincount(i, minlength=len(s))
    # floodplain buildings: HAND < 2 m at the building centroid, within 150 m
    tr = R["tr"]
    ll = bc.to_crs(4326)
    col = ((ll.x.values - tr.c) / tr.a).astype(int).clip(0, R["hand"].shape[1] - 1)
    row = ((ll.y.values - tr.f) / tr.e).astype(int).clip(0, R["hand"].shape[0] - 1)
    low = R["hand"][row, col] < 2
    tree2 = shapely.STRtree(bc.values[low])
    i, j = tree2.query(s.geometry.values, predicate="dwithin", distance=150)
    # assign each floodplain building to its nearest segment only (avoid double counting)
    dd = shapely.distance(s.geometry.values[i], bc.values[low][j])
    pair = pd.DataFrame({"i": i, "j": j, "d": dd}).sort_values("d").drop_duplicates("j")
    s["bldg_floodplain"] = np.bincount(pair.i, minlength=len(s))
    s["waste_100m"] = counts(s, "osm_waste.geojson", 100)
    s["markets_300m"] = counts(s, "osm_markets.geojson", 300)
    cul = gpd.read_file(KD / "osm_waterways.geojson")
    cul = cul[cul.tunnel.isin(["culvert", "yes"]) | (cul.culvert == "yes")].to_crs(UTM)
    cul["geometry"] = cul.geometry.interpolate(0.5, normalized=True)
    i, _ = shapely.STRtree(cul.geometry.values).query(s.geometry.values, predicate="dwithin", distance=25)
    s["culverts"] = np.bincount(i, minlength=len(s))
    br = gpd.read_file(KD / "osm_bridges.geojson").to_crs(UTM)
    i, _ = shapely.STRtree(br.geometry.values).query(s.geometry.values, predicate="intersects")
    s["bridges"] = np.bincount(i, minlength=len(s))
    km = s.length_m / 1000
    s["crossings_per_km"] = (s.culverts + s.bridges) / km.clip(lower=0.05)
    s["bldg_reserve_per_km"] = s.bldg_reserve / km.clip(lower=0.05)
    s["waste_pressure"] = s.waste_100m + 0.5 * s.markets_300m
    s["low_wetland"] = -s.wetland_500m
    # hotspot labels
    hs = pd.read_csv(KD / "flood_hotspots.csv")
    hp = gpd.GeoSeries(gpd.points_from_xy(hs.lon, hs.lat), crs=4326).to_crs(UTM)
    i, j = shapely.STRtree(hp.values).query(s.geometry.values, predicate="dwithin", distance=400)
    s["hotspot"] = 0
    s.loc[np.unique(i), "hotspot"] = 1
    near = pd.DataFrame({"i": i, "j": j})
    s["hotspot_name"] = near.groupby("i").j.first().reindex(range(len(s))).map(hs.place)
    # flood-prone tagged roads (OSM)
    fp = gpd.read_file(KD / "osm_flood_prone.geojson").to_crs(UTM)
    i, _ = shapely.STRtree(fp.geometry.values).query(s.geometry.values, predicate="dwithin", distance=150)
    s["osm_flood_prone"] = (np.bincount(i, minlength=len(s)) > 0).astype(int)
    names = pd.read_csv(RES / "kampala_catchments.csv").set_index("id").name.dropna()
    s["system"] = s.cat.astype(int).map(names).fillna("other / outside city catchments")
    s["cls"] = pd.cut(s.up_km2, [-1, 0.25, 2, 1e9], labels=["minor", "secondary", "primary"])

    # --- maintenance-priority index on channels that carry real flow (>= 0.25 km2): equal-weight mean of the
    # percentile ranks of the six present-day pressures; the two change-since-1990 pressures form a separate
    # "emerging risk" score (split made after seeing that reported hotspots sit in long-built areas) (not fitted - the hotspot list is too small and too centre-biased
    # to learn weights that transfer; fitted weights scored AUC 0.52-0.59 under spatial cross-validation)
    m = s[s.up_km2 >= 0.25].copy()
    X = pd.DataFrame({k: m[k].rank(pct=True) for k in DRIVERS})
    y = m.hotspot.values
    eq = X[list(NOW)].mean(1)
    m["risk"] = eq
    m["risk_pct"] = eq.rank(pct=True) * 100
    m["emerging_pct"] = X[list(TREND)].mean(1).rank(pct=True) * 100
    m["top_drivers"] = X[list(NOW)].apply(lambda r: "; ".join(NOW[k] for k in r.sort_values(ascending=False).index[:3]), axis=1)
    cx, cy = m.geometry.centroid.x, m.geometry.centroid.y
    blk = ((cx // 2000).astype(int).astype(str) + "_" + (cy // 2000).astype(int).astype(str)).values
    ub = np.unique(blk)
    rng = np.random.default_rng(1)
    boot = []
    for _ in range(500):
        idx = np.concatenate([np.flatnonzero(blk == b) for b in rng.choice(ub, len(ub))])
        if 0 < y[idx].sum() < len(idx):
            boot.append(roc_auc_score(y[idx], eq.values[idx]))
    em = X[list(TREND)].mean(1)
    dens = (m.bldg_reserve_per_km + m.bldg_floodplain).rank(pct=True).values > 0.5
    hs = pd.read_csv(KD / "flood_hotspots.csv")
    hp = gpd.GeoSeries(gpd.points_from_xy(hs.lon, hs.lat), crs=4326).to_crs(UTM)
    top = shapely.STRtree(m[m.risk_pct >= 80].geometry.values)
    hit = np.mean([len(top.query(p, predicate="dwithin", distance=400)) > 0 for p in hp])
    rnd = m.geometry.interpolate(0.5, normalized=True).sample(2000, random_state=0)
    rhit = np.mean([len(top.query(p, predicate="dwithin", distance=400)) > 0 for p in rnd])
    val = dict(n_segments=len(y), n_hotspot_segments=int(y.sum()), n_hotspots=len(hs),
               auc_index=roc_auc_score(y, eq), auc_ci_lo=np.percentile(boot, 2.5), auc_ci_hi=np.percentile(boot, 97.5),
               auc_index_dense_half=roc_auc_score(y[dens], eq.values[dens]), auc_emerging=roc_auc_score(y, em),
               auc_fitted_spatial_cv="0.52-0.59", hotspots_with_top20_within_400m=hit, random_points_same=rhit)
    pd.DataFrame([val]).round(3).to_csv(RES / "kd_validation.csv", index=False)
    print(val)
    drv = pd.DataFrame({"driver": list(DRIVERS), "label": list(DRIVERS.values()),
                        "auc_alone": [roc_auc_score(y, X[k]) for k in DRIVERS],
                        "auc_alone_dense_half": [roc_auc_score(y[dens], X.loc[dens, k]) for k in DRIVERS],
                        "hotspot_median_pct": [X.loc[y == 1, k].median() for k in DRIVERS],
                        "other_median_pct": [X.loc[y == 0, k].median() for k in DRIVERS]}).sort_values("auc_alone", ascending=False)
    drv.round(3).to_csv(RES / "kd_drivers.csv", index=False)
    print(drv.round(2).to_string())
    s = s.join(m[["risk", "risk_pct", "emerging_pct", "top_drivers"]])
    s.to_crs(4326).to_file(KD / "segments.gpkg", driver="GPKG")
    s.drop(columns="geometry").round(4).to_csv(RES / "kd_segments.csv", index=False)
    # summaries by channel system
    print(m.groupby("system").agg(n=("seg_id", "size"), km=("length_m", lambda v: v.sum() / 1000),
                                                   risk=("risk_pct", "median"), emerging=("emerging_pct", "median"), bldg_res=("bldg_reserve", "sum"),
                                                   waste=("waste_100m", "sum"), culv=("culverts", "sum"),
                                                   vb90=("valley_built_1990", "median"),
                                                   vb20=("valley_built_2020", "median")).round(2).to_string())


if __name__ == "__main__":
    main()
