"""Paper 5: double exposure - do the people on Kampala's flood-prone low ground also live in its hottest places?

Heat: Landsat 8/9 surface temperature (ST_B10, 30 m), median of dry-season daytime scenes (~10:30 local),
2014-2016 ("early") and 2023-2025 ("late"), plus NDVI. Hot = cell in the top quintile of LST within the study box.
Context: CPC night-time minimum temperature trend (+0.40 C/decade, Paper A) - Landsat sees daytime surfaces only.
Flood: low ground = HAND < 2 m within 150 m of a flowing channel (Papers A, D).
Population: JRC GHS-POP 2020 (100 m).
Measures:
  share of residents that are hot, flood-exposed, both; odds ratio of heat given flood exposure
  LST of low ground vs hills, controlling for built-up share and NDVI (OLS with 2 km block-clustered errors)
  warming 2015 -> 2024 of low ground vs hills
Outputs: results/kd_heat_*.csv, figures kd35-kd36.
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyproj
import rasterio
import shapely
import statsmodels.formula.api as smf
import xarray as xr

from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
BOX = (32.45, 0.20, 32.72, 0.42)
SRC = ("Surface temperature: NASA MODIS MOD11A2 (1 km, day and night) and USGS Landsat 8/9 (Microsoft Planetary Computer) · population and built-up: "
       "JRC GHSL R2023A · terrain: Copernicus GLO-30 DEM · channels: © OpenStreetMap contributors")


def main():
    lst = xr.open_dataset(KD / "sat_lst.nc")
    pop = xr.open_dataarray(PROC / "kampala_ghs_pop.nc").sel(epoch=2020).sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc").sel(epoch=2020).sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    gcell = (abs(float(np.diff(g.lon).mean())) * 111320 * np.cos(np.deg2rad(0.3))) * (abs(float(np.diff(g.lat).mean())) * 110574)
    LO, LA = np.meshgrid(pop.lon.values, pop.lat.values)
    tf = pyproj.Transformer.from_crs(4326, 32636, always_xy=True)
    X, Y = tf.transform(LO, LA)
    samp = lambda da: da.sel(x=xr.DataArray(X.ravel(), dims="p"), y=xr.DataArray(Y.ravel(), dims="p"), method="nearest").values
    mo = xr.open_dataset(KD / "sat_modis_lst.nc")
    df = pd.DataFrame({"lon": LO.ravel(), "lat": LA.ravel(), "x": X.ravel(), "y": Y.ravel(),
                       "night_e": samp(mo.night_early), "night_l": samp(mo.night_late),
                       "day_e": samp(mo.day_early), "day_l": samp(mo.day_late),
                       "pop": np.nan_to_num(pop.values.ravel()),
                       "built": np.clip(g.interp(lon=pop.lon, lat=pop.lat, method="nearest").values.ravel() / gcell, 0, 1),
                       "lst_e": samp(lst.lst_early), "lst_l": samp(lst.lst_late),
                       "ndvi_l": samp(lst.ndvi_late)})
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand = r.read(2)
        tr = r.transform
    col = ((df.lon.values - tr.c) / tr.a).astype(int).clip(0, hand.shape[1] - 1)
    row = ((df.lat.values - tr.f) / tr.e).astype(int).clip(0, hand.shape[0] - 1)
    df["hand"] = hand[row, col]
    s = gpd.read_file(KD / "segments.gpkg").to_crs(32636)
    fl = s[s.up_km2 >= 0.25].geometry.values
    pts = gpd.points_from_xy(df.x, df.y)
    near = np.zeros(len(df), bool)
    near[np.unique(shapely.STRtree(pts).query(fl, predicate="dwithin", distance=150)[1])] = True
    df["flood"] = (df.hand < 2) & near
    df["hill"] = df.hand >= 10
    df = df[np.isfinite(df.night_l) & (df.ndvi_l > 0)]  # MODIS covers everything; drop open water
    q80 = df.night_l.quantile(0.8)
    df["hot"] = df.night_l >= q80  # hot = top 20% of NIGHT-time surface temperature (MODIS, 2022-25)
    w = df["pop"]
    tot = w.sum()
    both = w[df.hot & df.flood].sum()
    summ = dict(hot_threshold_C=q80, residents=tot, share_hot=100 * w[df.hot].sum() / tot,
                share_flood=100 * w[df.flood].sum() / tot, share_both=100 * both / tot,
                share_hot_among_flood=100 * w[df.hot & df.flood].sum() / w[df.flood].sum(),
                share_hot_among_hills=100 * w[df.hot & df.hill].sum() / w[df.hill].sum(),
                residents_both=both,
                night_flood=float(np.average(df.night_l[df.flood], weights=w[df.flood] + 1e-6)),
                night_hill=float(np.average(df.night_l[df.hill], weights=w[df.hill] + 1e-6)),
                day_flood=float(np.average(df.day_l[df.flood], weights=w[df.flood] + 1e-6)),
                day_hill=float(np.average(df.day_l[df.hill], weights=w[df.hill] + 1e-6)),
                night_warming_flood=float(np.average((df.night_l - df.night_e)[df.flood], weights=w[df.flood] + 1e-6)),
                night_warming_hill=float(np.average((df.night_l - df.night_e)[df.hill], weights=w[df.hill] + 1e-6)),
                night_warming_all=float(np.average(df.night_l - df.night_e, weights=w + 1e-6)),
                landsat_day_flood=float(np.nanmean(df.lst_l[df.flood])), landsat_day_hill=float(np.nanmean(df.lst_l[df.hill])),
                landsat_coverage_pct=100 * float(np.isfinite(df.lst_l).mean()))
    hf = w[df.hot & df.flood].sum(); hn = w[df.hot & ~df.flood].sum()
    cf = w[~df.hot & df.flood].sum(); cn = w[~df.hot & ~df.flood].sum()
    summ["odds_ratio_hot_given_flood"] = (hf / cf) / (hn / cn)
    pd.Series(summ).round(3).to_csv(RES / "kd_heat_summary.csv", header=["value"])
    print(pd.Series(summ).round(2).to_string())
    # regression: LST ~ low ground + built + ndvi, people-weighted, 2 km blocks
    d = df[(df["pop"] > 5)].copy()
    d["blk"] = (d.x // 2000).astype(int).astype(str) + "_" + (d.y // 2000).astype(int).astype(str)
    d["lowground"] = d.flood.astype(int)
    d = d.dropna(subset=["night_l", "built", "ndvi_l"]).copy()
    d["gid"] = pd.factorize(d.blk)[0]
    m = smf.wls("night_l ~ lowground + built + ndvi_l", data=d, weights=d["pop"]).fit(cov_type="cluster", cov_kwds={"groups": d.gid.values})
    co = pd.DataFrame({"coef": m.params, "ci_lo": m.conf_int()[0], "ci_hi": m.conf_int()[1], "p": m.pvalues})
    co.round(4).to_csv(RES / "kd_heat_regression.csv")
    print(co.round(3).to_string(), "R2", round(m.rsquared, 3))
    # by density decile: is low ground hotter at equal built-up share?
    d["bdec"] = pd.qcut(d.built.rank(method="first"), 5, labels=["least built", "2", "3", "4", "most built"])
    byb = d.groupby(["bdec", "lowground"], observed=True).apply(lambda g_: np.average(g_.night_l, weights=g_["pop"])).unstack()
    byb.columns = ["higher ground", "low ground"]
    byb.round(2).to_csv(RES / "kd_heat_by_density.csv")
    print(byb.round(2).to_string())
    figures(df, summ, byb, lst)


def figures(df, summ, byb, lst):
    fig, axs = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw=dict(wspace=0.35))
    ax = axs[0]
    x = np.arange(len(byb))
    ax.bar(x - 0.2, byb["higher ground"], 0.4, color="#fdae6b", label="higher ground")
    ax.bar(x + 0.2, byb["low ground"], 0.4, color="#d7301f", label="low ground beside channels")
    ax.set_xticks(x)
    ax.set_xticklabels(byb.index)
    ax.set_ylim(byb.values.min() - 2, byb.values.max() + 1.5)
    ax.set_xlabel("built-up share (quintile of 100 m cells)")
    ax.set_ylabel("night-time surface temperature, °C (MODIS, 2022-25)")
    ax.set_title("a  Night heat by how built-up the land is", loc="left")
    ax.legend(fontsize=9)
    ax = axs[1]
    labels = ["hot only", "flood-exposed only", "both"]
    w = df["pop"]
    vals = [w[df.hot & ~df.flood].sum(), w[~df.hot & df.flood].sum(), w[df.hot & df.flood].sum()]
    ax.bar(labels, np.array(vals) / 1000, color=["#fd8d3c", "#3182bd", "#6a3d9a"])
    for i, v in enumerate(vals):
        ax.text(i, v / 1000, f"{v / 1000:,.0f}k", ha="center", va="bottom", fontsize=10)
    ax.set_ylabel("residents (thousands, 2020)")
    ax.set_title(f"b  Residents facing heat, flood or both\n(hot = warmest 20% of nights, ≥ {summ['hot_threshold_C']:.1f} °C surface)",
                 loc="left")
    save(fig, "kd35_heat_flood.png", OUT, source=SRC)
    # map: MODIS night surface temperature (complete coverage)
    mo = xr.open_dataset(KD / "sat_modis_lst.nc")
    fig, ax = plt.subplots(figsize=(10, 8.6))
    im = mo.night_late
    ext = [float(im.x.min()) - 500, float(im.x.max()) + 500, float(im.y.min()) - 500, float(im.y.max()) + 500]
    org = "upper" if float(im.y[0]) > float(im.y[-1]) else "lower"
    wat = (lst.ndvi_late < 0).astype(float).coarsen(x=33, y=33, boundary="trim").mean().interp(x=im.x, y=im.y, method="nearest")
    from scipy import ndimage
    wm = ndimage.binary_dilation(np.nan_to_num(wat.values) > 0.2, iterations=1)  # lake + 1 km shore buffer
    v = np.where(wm, np.nan, im.values)  # open water (lake) warms at night: masked
    hh = ax.imshow(v, cmap="inferno", vmin=np.nanpercentile(v, 3), vmax=np.nanpercentile(v, 99.5), extent=ext, origin=org,
                   interpolation="bilinear")
    s_ = gpd.read_file(KD / "segments.gpkg").to_crs(32636)
    s_[s_.up_km2 >= 2].plot(ax=ax, color="#4fc3f7", lw=0.7)
    fd = df[df.flood & df.hot & (df["pop"] > 50)]
    ax.scatter(fd.x, fd.y, s=7, facecolor="none", edgecolor="#ffffff", lw=0.5)
    ax.set_xlim(ext[:2])
    ax.set_ylim(ext[2:])
    ax.set_axis_off()
    fig.colorbar(hh, ax=ax, shrink=0.6, label="night-time surface temperature, 2022-25 median (°C)")
    ax.set_title("Kampala's warmest nights and its drains (Lake Victoria and 1 km of shore masked)\nblue: main channels · white rings: populated low ground in the warmest 20% of nights",
                 loc="left", fontsize=11)
    save(fig, "kd36_heat_map.png", OUT, source=SRC)


if __name__ == "__main__":
    main()
