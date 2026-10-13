"""Paper 7: the same open-data flood-exposure method across Uganda's growing cities.

Cities: Kampala (core box) and the NDP IV regional cities Jinja, Mbale, Gulu, Mbarara, Arua (~18 km boxes).
Identical rules everywhere (channels from the terrain, not OSM, whose drain mapping varies between towns):
  terrain     Copernicus GLO-30; D8 routing (pysheds); channels = cells draining >= 0.25 km2; HAND
  low ground  HAND < 2 m and within 150 m of a channel
  valley floor HAND < 3 m (former wetland/floodplain)
  storage     1 m storage on valley floor not built over (GHSL built share), 1975 -> 2020 -> 2030
  people      JRC GHS-POP 1975-2030 on low ground; share of the box population; growth vs the whole box
  buildings   Microsoft footprints: median size on low ground vs higher ground (HAND >= 10 m)
Outputs: results/kd_cities_*.csv, figures kd40-kd41.
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from pysheds.grid import Grid
from rasterio.windows import from_bounds
from scipy import ndimage

from common import FIG, PROC, ROOT, RES, save

KD = ROOT / "data" / "kd"
CD = KD / "cities"
OUT = FIG / "kampala_drainage"
CITIES = ["kampala", "jinja", "mbale", "gulu", "mbarara", "arua"]
SRC = ("Terrain: Copernicus GLO-30 DEM · built-up and population: JRC GHSL R2023A (2025, 2030 projected) · buildings: "
       "Microsoft Global ML Building Footprints")


def kampala_inputs():
    box = (32.45, 0.20, 32.72, 0.42)
    f = CD / "kampala_dem.tif"
    if not f.exists():
        with rasterio.open(PROC / "kampala_dem.tif") as r:
            w = from_bounds(*box, r.transform)
            a = r.read(1, window=w)
            prof = r.profile | dict(height=a.shape[0], width=a.shape[1], transform=r.window_transform(w))
        with rasterio.open(f, "w", **prof) as o:
            o.write(a, 1)
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc").sel(lon=slice(box[0], box[2]), lat=slice(box[1], box[3]))
    p = xr.open_dataarray(PROC / "kampala_ghs_pop.nc").sel(lon=slice(box[0], box[2]), lat=slice(box[1], box[3]))
    b = gpd.read_parquet(KD / "ms_buildings.parquet").cx[box[0]:box[2], box[1]:box[3]]
    return f, g, p, b


def city_inputs(c):
    if c == "kampala":
        return kampala_inputs()
    return (CD / f"{c}_dem.tif", xr.open_dataarray(CD / f"{c}_built.nc"), xr.open_dataarray(CD / f"{c}_pop.nc"),
            gpd.read_parquet(CD / f"{c}_buildings.parquet"))


def terrain(f):
    g = Grid.from_raster(str(f))
    dem = g.read_raster(str(f))
    inf = g.resolve_flats(g.fill_depressions(g.fill_pits(dem)))
    fd = g.flowdir(inf)
    accr = g.accumulation(fd)
    acc = np.asarray(accr)
    with rasterio.open(f) as r:
        tr = r.transform
        lat0 = tr.f + tr.e * r.height / 2
    cell = abs(tr.a) * 111320 * np.cos(np.deg2rad(lat0)) * abs(tr.e) * 110574
    streamr = accr * (cell / 1e6) >= 0.25
    stream = np.asarray(streamr)
    hand = np.asarray(g.compute_hand(fd, inf, streamr)).astype(float)
    dist = ndimage.distance_transform_edt(~stream) * np.sqrt(cell)
    return hand, dist, tr, cell


def sample(da_lat, da_lon, tr, arr):
    LO, LA = np.meshgrid(da_lon, da_lat)
    col = ((LO - tr.c) / tr.a).astype(int).clip(0, arr.shape[1] - 1)
    row = ((LA - tr.f) / tr.e).astype(int).clip(0, arr.shape[0] - 1)
    return arr[row, col]


def main():
    rows, pop_rows = [], []
    for c in CITIES:
        f, built, pop, b = city_inputs(c)
        hand, dist, tr, cell = terrain(f)
        valley = (hand < 3) & np.isfinite(hand)
        # storage on valley floor not built over
        gcell = (abs(float(np.diff(built.lon).mean())) * 111320 * np.cos(np.deg2rad(float(built.lat.mean())))) * \
                (abs(float(np.diff(built.lat).mean())) * 110574)
        H, W = hand.shape
        lat = tr.f + tr.e * (np.arange(H) + 0.5)
        lon = tr.c + tr.a * (np.arange(W) + 0.5)
        cap = np.nan_to_num(np.clip(1 - hand, 0, None)) * cell
        r = dict(city=c, area_km2=hand.size * cell / 1e6, valley_km2=valley.sum() * cell / 1e6,
                 capacity_1m_Mm3=cap.sum() / 1e6)
        for e in (1975, 1995, 2005, 2020, 2030):
            bs = np.clip(built.sel(epoch=e).sel(lat=lat, lon=lon, method="nearest").values / gcell, 0, 1)
            r[f"valley_built_{e}"] = 100 * float(bs[valley].mean())
            r[f"storage_1m_{e}_Mm3"] = float((cap * (1 - bs)).sum() / 1e6)
            r[f"box_built_{e}"] = 100 * float(bs.mean())
        r["storage_lost_1975_2020_pct"] = 100 * (1 - r["storage_1m_2020_Mm3"] / r["storage_1m_1975_Mm3"])
        # people on low ground
        ph = sample(pop.lat.values, pop.lon.values, tr, hand)
        pdist = sample(pop.lat.values, pop.lon.values, tr, dist)
        low = (ph < 2) & (pdist <= 150)
        for e in pop.epoch.values:
            v = np.nan_to_num(pop.sel(epoch=e).values)
            pop_rows.append(dict(city=c, epoch=int(e), low=float(v[low].sum()), total=float(v.sum())))
        # buildings
        cen = b.geometry.centroid
        bh = sample(None, None, tr, hand) if False else None
        col = ((cen.x.values - tr.c) / tr.a).astype(int).clip(0, W - 1)
        row = ((cen.y.values - tr.f) / tr.e).astype(int).clip(0, H - 1)
        bhand, bdist = hand[row, col], dist[row, col]
        area = b.to_crs(32636).area.values
        bl = (bhand < 2) & (bdist <= 150)
        bhl = bhand >= 10
        r.update(buildings=len(b), bldg_low=int(bl.sum()), bldg_low_pct=100 * float(bl.mean()),
                 median_m2_low=float(np.median(area[bl])) if bl.any() else np.nan,
                 median_m2_hills=float(np.median(area[bhl])) if bhl.any() else np.nan,
                 share_lt40_low=100 * float((area[bl] < 40).mean()) if bl.any() else np.nan,
                 share_lt40_hills=100 * float((area[bhl] < 40).mean()) if bhl.any() else np.nan)
        rows.append(r)
        print(c, {k: round(v, 1) if isinstance(v, float) else v for k, v in r.items() if k in
                  ("valley_built_1975", "valley_built_2020", "valley_built_2030", "storage_lost_1975_2020_pct", "bldg_low_pct",
                   "median_m2_low", "median_m2_hills")}, flush=True)
    t = pd.DataFrame(rows)
    t.round(3).to_csv(RES / "kd_cities_summary.csv", index=False)
    p = pd.DataFrame(pop_rows)
    p["share_low"] = 100 * p.low / p.total
    p.round(1).to_csv(RES / "kd_cities_population.csv", index=False)
    g = []
    for c in CITIES:
        q = p[p.city == c].set_index("epoch")
        cg = lambda col, a, b_: 100 * ((q.loc[b_, col] / max(q.loc[a, col], 1)) ** (1 / (b_ - a)) - 1)
        g.append(dict(city=c, low_1975=q.loc[1975, "low"], low_2020=q.loc[2020, "low"], low_2030=q.loc[2030, "low"],
                      share_low_2020=q.loc[2020, "share_low"],
                      growth_low_2000_2020=cg("low", 2000, 2020), growth_all_2000_2020=cg("total", 2000, 2020),
                      growth_low_2020_2030=cg("low", 2020, 2030), growth_all_2020_2030=cg("total", 2020, 2030)))
    g = pd.DataFrame(g)
    g.round(2).to_csv(RES / "kd_cities_growth.csv", index=False)
    print(g.round(1).to_string())
    print(t[["city", "valley_built_1975", "valley_built_2020", "valley_built_2030", "storage_lost_1975_2020_pct"]].round(1).to_string())
    figures(t, p, g)


def figures(t, p, g):
    names = {c: c.capitalize() for c in CITIES}
    cols = {"kampala": "#333333", "jinja": "#1b9e77", "mbale": "#d95f02", "gulu": "#7570b3", "mbarara": "#e7298a", "arua": "#66a61e"}
    fig, axs = plt.subplots(1, 3, figsize=(17, 5), gridspec_kw=dict(wspace=0.35))
    ax = axs[0]
    for c in CITIES:
        r = t[t.city == c].iloc[0]
        ax.plot([1975, 1995, 2005, 2020, 2030], [r[f"valley_built_{e}"] for e in (1975, 1995, 2005, 2020, 2030)],
                marker="o", color=cols[c], lw=2.8 if c == "kampala" else 1.8, label=names[c])
    ax.axvspan(2020, 2031, color="#eee", lw=0)
    ax.set_ylabel("valley floor built over (%)")
    ax.set_title("a  Building on the valley floors", loc="left", fontsize=11)
    ax.legend(fontsize=8.5)
    ax = axs[1]
    for c in CITIES:
        q = p[p.city == c]
        ax.plot(q.epoch, q.low / q[q.epoch == 2000].low.values[0], marker="o", color=cols[c], lw=2.8 if c == "kampala" else 1.8,
                label=names[c])
    ax.axvspan(2020, 2031, color="#eee", lw=0)
    ax.set_ylabel("people on low ground (2000 = 1)")
    ax.set_title("b  People in the water's path, relative to 2000", loc="left", fontsize=11)
    ax = axs[2]
    gg = g.set_index("city").reindex(CITIES)
    x = np.arange(len(gg))
    ax.bar(x - 0.2, gg.growth_all_2020_2030, 0.4, color="#bdbdbd", label="whole area")
    ax.bar(x + 0.2, gg.growth_low_2020_2030, 0.4, color="#d6336c", label="low ground")
    ax.set_xticks(x)
    ax.set_xticklabels([names[c] for c in gg.index])
    ax.set_ylabel("population growth, % per year (2020-2030, projected)")
    ax.set_title("c  Is low ground filling faster than the city?", loc="left", fontsize=11)
    ax.legend(fontsize=8.5)
    save(fig, "kd40_cities_compare.png", OUT, source=SRC)


if __name__ == "__main__":
    main()
