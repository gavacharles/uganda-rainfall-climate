"""Roads and drainage: how Kampala's valley-floor change, channel capacity and siltation affect its roads, over time.

Roads     every OpenStreetMap drivable road (motorway ... residential, service), Greater Kampala core, cut into <= 100 m
          pieces. Per piece: class, name, bridge, lowest HAND along it (sampled every 15 m), distance to the nearest
          flowing channel, channel crossing (culvert unless OSM bridge).
History   (a) urbanised: first GHSL epoch (1975-2020, 5-yearly) with built share >= 0.15 in the road's 100 m cell
          (b) on former wetland: valley-floor ground (HAND < 3 m) that was wetland vegetation or trees/shrubs in the
              1986 machine-learning land-cover map (kd_landcover.py)
Hazard    flood stage above bank for the 2-100-year storms per channel stretch (kd_hydraulics.py HAND rating curve),
          recomputed here for four states:
            1990 city   flows with 1990 upstream paving, channels clean (MODELLED: channels assumed sized for 1990)
            2020 clean  today's flows, clean channels
            2020 silted today's flows, channels 30% silted
            2050s       2030 land + 2041-70 SSP5-8.5 rainfall, clean channels
          Depth on a road piece = stage - lowest HAND (piece within 300 m of its stretch; bridges never flood).
          Impassable when depth >= 0.3 m (cars stall; Pregnolato et al. 2017 depth-disruption function).
          Expected annual impassable road-km: integral of impassable km over annual exceedance probability.
Drivers   the flooded road inherits the pressures of its channel stretch (segments.gpkg top_drivers)
Check     roads named in the flood catalogue (Hoima Rd at Lubigi, Jinja Rd at Kyambogo/Banda, Entebbe Rd at Namasuba,
          Bwaise, Mukwano Rd, Northern Bypass, Kinawataka Rd): modelled depth near the reported place
City-generic pieces (pieces(), hand sampling, history) take a box and rasters; the hazard uses Kampala's hydraulics.
Outputs   data/kd/road_pieces.parquet, results/kd_roads_*.csv, figures kd45-kd47
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import shapely
import xarray as xr
from shapely.ops import substring

from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
BOX = (32.45, 0.20, 32.72, 0.42)
TS = [2, 5, 10, 25, 50, 100]
IMPASSABLE = 0.3
CLASS = {"motorway": "highway", "trunk": "highway", "motorway_link": "highway", "trunk_link": "highway",
         "primary": "main road", "primary_link": "main road", "secondary": "main road", "secondary_link": "main road",
         "tertiary": "local through road", "tertiary_link": "local through road", "unclassified": "local through road",
         "residential": "residential street", "living_street": "residential street", "service": "service lane"}
ORDER = ["highway", "main road", "local through road", "residential street", "service lane"]
REPORTED = {  # catalogue road reports: OSM name pattern, reported place (catalogue / hotspot geocodes)
    "Hoima Road at Lubigi": ("Hoima Road", (0.3410, 32.5360)),
    "Jinja Road at Kyambogo": ("Jinja Road", (0.3335, 32.6270)),
    "Jinja Road at Banda": ("Jinja Road", (0.3380, 32.6400)),
    "Entebbe Road at Namasuba": ("Entebbe Road", (0.2722, 32.5634)),
    "Bombo Road at Bwaise": ("Bombo Road", (0.3520, 32.5620)),
    "Mukwano Road": ("Mukwano", (0.3083, 32.5872)),
    "Northern Bypass (Bwaise-Kalerwe)": ("Northern Bypass", (0.3530, 32.5700)),
    "Kinawataka Road": ("Kinawataka Road", (0.3351, 32.6432)),
}
SRC = ("Roads, channels: © OpenStreetMap contributors · terrain: Copernicus GLO-30 DEM · built-up: JRC GHSL R2023A · "
       "land cover 1986: Landsat machine-learning map (this study) · storms: gauge-corrected CHIRPS IDF")


def pieces(roads, maxlen=100.0):
    """Cut road lines (metric CRS) into pieces of at most maxlen m."""
    rows = []
    for r in roads.itertuples():
        g = r.geometry
        if g is None or g.is_empty:
            continue
        for line in (g.geoms if g.geom_type == "MultiLineString" else [g]):
            L = line.length
            n = max(1, int(np.ceil(L / maxlen)))
            for k in range(n):
                rows.append((r.osm_id, r.highway, r.name, r.bridge, substring(line, k * L / n, (k + 1) * L / n)))
    return gpd.GeoDataFrame(pd.DataFrame(rows, columns=["osm_id", "highway", "name", "bridge", "geometry"]),
                            geometry="geometry", crs=roads.crs)


def sample_raster(path, band, lon, lat):
    with rasterio.open(path) as r:
        a, t = r.read(band), r.transform
    col = ((lon - t.c) / t.a).astype(int).clip(0, a.shape[1] - 1)
    row = ((lat - t.f) / t.e).astype(int).clip(0, a.shape[0] - 1)
    return a[row, col]


def min_hand(p):
    """Lowest HAND along each piece (points every 15 m)."""
    pts, owner = [], []
    for i, g in enumerate(p.geometry.values):
        L = g.length
        for d in np.append(np.arange(0, L, 15.0), L):
            pts.append(g.interpolate(d))
            owner.append(i)
    ll = gpd.GeoSeries(pts, crs=p.crs).to_crs(4326)
    h = sample_raster(PROC / "kampala_catchments.tif", 2, ll.x.values, ll.y.values).astype(float)
    return pd.Series(h).groupby(np.array(owner)).min().reindex(range(len(p))).values


def history(p):
    mid = p.geometry.interpolate(0.5, normalized=True)
    ll = gpd.GeoSeries(mid, crs=p.crs).to_crs(4326)
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc")
    gcell = (abs(float(np.diff(g.lon).mean())) * 111320 * np.cos(np.deg2rad(0.3))) * (abs(float(np.diff(g.lat).mean())) * 110574)
    first = np.full(len(p), np.nan)
    for e in sorted(int(v) for v in g.epoch.values if int(v) <= 2020)[::-1]:
        b = g.sel(epoch=e).sel(lat=xr.DataArray(ll.y.values), lon=xr.DataArray(ll.x.values), method="nearest").values / gcell
        first = np.where(b >= 0.15, e, first)
    lc = xr.open_dataset(KD / "landcover_1986.nc").cls
    c86 = lc.sel(x=xr.DataArray(mid.x.values), y=xr.DataArray(mid.y.values), method="nearest").values
    return first, c86


def stage_states(s, h):
    """Overbank stage per stretch and return period for four states, from each stretch's HAND rating curve."""
    su = s.to_crs(32636)
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand, trh = r.read(2), r.transform
    rows, cols = np.nonzero((hand < 6) & np.isfinite(hand))
    lon, lat = trh.c + trh.a * (cols + 0.5), trh.f + trh.e * (rows + 0.5)
    keep = (lon > BOX[0]) & (lon < BOX[2]) & (lat > BOX[1]) & (lat < BOX[3])
    pts = gpd.GeoSeries(gpd.points_from_xy(lon[keep], lat[keep]), crs=4326).to_crs(32636).values
    hv = hand[rows[keep], cols[keep]]
    tree = shapely.STRtree(su.geometry.values)
    pi, si = tree.query(pts, predicate="dwithin", distance=200)
    cell = pd.DataFrame({"p": pi, "s": si, "d": shapely.distance(pts[pi], su.geometry.values[si])}) \
        .sort_values("d").drop_duplicates("p")
    cell["h"] = hv[cell.p.values]
    groups = {k: g.h.values for k, g in cell.groupby("s")}
    hgrid = np.arange(0.05, 6.01, 0.05)
    L = su.length.values
    C2020 = h.C.values
    C1990 = 0.25 + 0.65 * np.clip(2.27 * s.up_built_1990.values, 0, 0.95)
    f585 = (h.Q10_2050_ssp585 / h.Q10).values
    states = {"1990 city": (h.Qcap_clean.values, C1990 / C2020), "2020 clean": (h.Qcap_clean.values, 1.0),
              "2020 silted": (h.Qcap_silted.values, 1.0), "2050s": (h.Qcap_clean.values, f585)}
    out = {}
    for st, (cap, scale) in states.items():
        H = np.zeros((len(s), len(TS)))
        sc = np.broadcast_to(scale, (len(s),))
        for k in range(len(s)):
            hk = groups.get(k, np.array([]))
            wfp = np.maximum(np.array([(hk < x).sum() * 900.0 / max(L[k], 30) for x in hgrid]), h.W_design.values[k])
            area = np.cumsum(wfp * 0.05)
            # floodplain flow adds to what the channel carries in this state
            Qtot = cap[k] + area * (area / wfp) ** (2 / 3) * np.sqrt(h.S.values[k]) / 0.06
            for j, T in enumerate(TS):
                q = h[f"Q{T}"].values[k] * sc[k]
                H[k, j] = 0.0 if q <= cap[k] else hgrid[min(np.searchsorted(Qtot, q), len(hgrid) - 1)]
        out[st] = H
        print("stages", st, "median 10-yr", np.median(H[:, TS.index(10)]).round(2), flush=True)
    return out


def main():
    roads = gpd.read_file(KD / "osm_roads.geojson").cx[BOX[0]:BOX[2], BOX[1]:BOX[3]].to_crs(32636)
    p = pieces(roads)
    p["cls"] = p.highway.map(CLASS).fillna("service lane")
    p["len_m"] = p.length
    p["bridge"] = p.bridge.fillna("").isin(["yes", "viaduct"])
    print("road pieces", len(p), "km", round(p.len_m.sum() / 1000), flush=True)
    p["hand_min"] = min_hand(p)
    p["urbanised"], p["lc1986"] = history(p)
    s = gpd.read_file(KD / "segments.gpkg")
    h = pd.read_parquet(KD / "hydraulics.parquet")
    s = s[s.seg_id.isin(h.seg_id)].set_index("seg_id").loc[h.seg_id].reset_index()
    su = s.to_crs(32636)
    mid = p.geometry.interpolate(0.5, normalized=True)
    tree = shapely.STRtree(su.geometry.values)
    ri, si = tree.query(mid.values, predicate="dwithin", distance=300)
    pr = pd.DataFrame({"r": ri, "s": si, "d": shapely.distance(mid.values[ri], su.geometry.values[si])}) \
        .sort_values("d").drop_duplicates("r")
    p["stretch"] = -1
    p.loc[pr.r.values, "stretch"] = pr.s.values
    p["dist_channel_m"] = np.nan
    p.loc[pr.r.values, "dist_channel_m"] = pr.d.values
    xi, _ = tree.query(p.geometry.values, predicate="intersects")
    p["crosses_channel"] = False
    p.loc[np.unique(xi), "crosses_channel"] = True
    p["seg_id"] = np.where(p.stretch >= 0, su.seg_id.values[p.stretch.clip(0)], -1)
    p["drivers"] = np.where(p.stretch >= 0, su.top_drivers.astype(str).values[p.stretch.clip(0)], "")
    p["system"] = np.where(p.stretch >= 0, su.system.astype(str).values[p.stretch.clip(0)], "")
    st = stage_states(s, h)
    has = (p.stretch >= 0).values & ~p.bridge.values & np.isfinite(p.hand_min.values)
    for name, H in st.items():
        for j, T in enumerate(TS):
            stage = np.where(has, H[p.stretch.clip(0).values, j], 0)
            p[f"d{T}_{name}"] = np.where(has, np.clip(stage - p.hand_min.values, 0, None) * (stage > 0), 0).round(2)
    p.to_crs(4326).to_parquet(KD / "road_pieces.parquet")
    resummarise()


def raised(p):
    """The Entebbe Expressway and its Southern Bypass spur (opened 2018) run on embankments built after the DEM (2011-15): treated
    like bridges (never flooded) in the headline numbers; their modelled depths are kept as *_ground columns."""
    r = p.name.fillna("").str.contains("Expressway|Southern Bypass", case=False)  # opened 2018, after the DEM
    for c in [c for c in p.columns if c.startswith("d") and "_" in c and c[1].isdigit()]:
        p[c + "_ground"] = p[c]
        p.loc[r, c] = 0.0
    p["raised"] = r
    return p


def resummarise():
    p = gpd.read_parquet(KD / "road_pieces.parquet")
    for c in [c for c in p.columns if c.endswith("_ground")]:   # restore unmasked depths before re-masking
        p[c[:-7]] = p[c]
    p = p[[c for c in p.columns if not c.endswith("_ground")]]
    p = raised(p).to_crs(32636)
    p["len_m"] = p.length
    p.to_crs(4326).to_parquet(KD / "road_pieces.parquet")
    summarise(p, ["1990 city", "2020 clean", "2020 silted", "2050s"])


def ea_km(p, name):
    """Expected annual impassable road-km."""
    km = np.array([0.0] + [p.len_m[p[f"d{T}_{name}"] >= IMPASSABLE].sum() / 1000 for T in TS])
    prob = np.array([1.0] + [1 / T for T in TS])
    return float(-np.trapz(km, prob))


def summarise(p, states):
    km = lambda m: p.len_m[m].sum() / 1000
    rows = []
    for name in states:
        r = dict(state=name, expected_annual_impassable_km=ea_km(p, name))
        for T in TS:
            r[f"impassable_km_T{T}"] = km(p[f"d{T}_{name}"] >= IMPASSABLE)
        for c in ORDER:
            r[f"T10_km_{c}"] = km((p[f"d10_{name}"] >= IMPASSABLE) & (p.cls == c))
        rows.append(r)
    hz = pd.DataFrame(rows)
    hz.round(2).to_csv(RES / "kd_roads_hazard.csv", index=False)
    print(hz.round(1).T.to_string(), flush=True)
    # exposure over time: roads on low ground by the epoch their ground urbanised
    low = (p.hand_min < 2) & (p.dist_channel_m <= 150)
    ex = []
    for e in range(1975, 2021, 5):
        ex.append(dict(epoch=e, road_km_urban=km(p.urbanised <= e), road_km_urban_low_ground=km(low & (p.urbanised <= e))))
    ex = pd.DataFrame(ex)
    ex["share_on_low_ground_pct"] = 100 * ex.road_km_urban_low_ground / ex.road_km_urban
    ex.round(2).to_csv(RES / "kd_roads_exposure_by_epoch.csv", index=False)
    print(ex.round(1).to_string(), flush=True)
    vf = p.hand_min < 3
    wet86 = vf & p.lc1986.isin([0, 1])
    hist = dict(total_road_km=km(p.len_m > 0), valley_floor_road_km=km(vf), on_1986_wetland_or_bush_km=km(wet86),
                on_1986_wetland_km=km(vf & (p.lc1986 == 0)), low_ground_road_km=km(low),
                channel_crossings=int(p[p.crosses_channel].osm_id.nunique()),
                crossings_without_bridge=int(p[p.crosses_channel & ~p.bridge].osm_id.nunique()),
                impassable_T10_2020_on_1986_wetland_or_bush_km=km(wet86 & (p["d10_2020 clean"] >= IMPASSABLE)),
                impassable_T10_2020_total_km=km(p["d10_2020 clean"] >= IMPASSABLE))
    pd.Series(hist).round(2).to_csv(RES / "kd_roads_history.csv", header=["value"])
    print(pd.Series(hist).round(1).to_string(), flush=True)
    # drivers behind flooded roads (2020 clean, 10-yr)
    f = p[p["d10_2020 clean"] >= IMPASSABLE]
    dr = f.assign(dr=f.drivers.str.split("; ")).explode("dr")
    dr = dr[dr.dr.str.len() > 0].groupby("dr").len_m.sum().div(1000).sort_values(ascending=False)
    dr.round(2).to_csv(RES / "kd_roads_drivers.csv", header=["impassable_km_T10"])
    print(dr.round(1).to_string(), flush=True)
    # named roads: impassable length in 10-yr storm (2020 clean, silted)
    nm = p[p.cls.isin(["highway", "main road", "local through road"]) & p.name.notna()]
    g = nm.groupby("name").apply(lambda d: pd.Series(dict(
        km=d.len_m.sum() / 1000, imp_T10_clean_m=d.len_m[d["d10_2020 clean"] >= IMPASSABLE].sum(),
        imp_T10_silted_m=d.len_m[d["d10_2020 silted"] >= IMPASSABLE].sum(),
        imp_T2_silted_m=d.len_m[d["d2_2020 silted"] >= IMPASSABLE].sum(),
        max_depth_T10_m=d["d10_2020 clean"].max())))
    g = g.sort_values("imp_T10_silted_m", ascending=False)
    g.round(2).to_csv(RES / "kd_roads_named.csv")
    print(g.head(20).round(2).to_string(), flush=True)
    # check against reported road floods
    pl = p.to_crs(4326)
    ck = []
    for lab, (pat, (la, lo)) in REPORTED.items():
        pt = gpd.GeoSeries(gpd.points_from_xy([lo], [la]), crs=4326).to_crs(32636).iloc[0]
        cand = p[p.name.fillna("").str.contains(pat, case=False)]
        near = cand[cand.distance(pt) <= 1500]
        ck.append(dict(report=lab, pieces=len(near), nearest_m=float(cand.distance(pt).min()) if len(cand) else np.nan,
                       max_depth_T2_silted=near["d2_2020 silted"].max() if len(near) else np.nan,
                       max_depth_T10_clean=near["d10_2020 clean"].max() if len(near) else np.nan,
                       max_depth_T10_silted=near["d10_2020 silted"].max() if len(near) else np.nan,
                       min_hand=near.hand_min.min() if len(near) else np.nan))
    ck = pd.DataFrame(ck)
    base = (p.cls.isin(["highway", "main road"])) & (p["d10_2020 silted"] >= IMPASSABLE)
    ck.round(2).to_csv(RES / "kd_roads_check.csv", index=False)
    print(ck.round(2).to_string(), "\nshare of all highway/main-road km impassable (T10 silted):",
          round(100 * km(base) / km(p.cls.isin(["highway", "main road"])), 1), flush=True)


if __name__ == "__main__":
    import sys
    globals()[sys.argv[1] if len(sys.argv) > 1 else "main"]()
