"""Paper 2: the lost free treatment plant - wetland loss on the Nakivubo/Kinawataka/Kansanga valleys and storm
plumes in Inner Murchison Bay, Lake Victoria (no utility data needed).

composite  Sentinel-2 L2A dry-season composite of the bay (20 m) -> water mask, outlet geography
scenes     every Sentinel-2 L2A scene 2017-2026 over the bay: per-scene medians in zones by distance from the outlets
           turbidity (Dogliotti et al. 2015, 645 nm: T = 228.1 rho / (1 - rho/0.1641) FNU)
           chlorophyll index NDCI = (B05 - B04)/(B05 + B04) (Mishra and Mishra 2012)
landsat    Landsat 5/7/8/9 red-band turbidity in the same zones, 1986-2026 (long record)
wetland    vegetated, unbuilt valley floor draining to the bay, 1986-2025 (Landsat, from Paper 1 method)
analysis   storms vs dry spells (CHIRPS antecedent rain, flood catalogue), trend, wetland-loss link; figures kd42-kd44
"""
import sys

import numpy as np
import pandas as pd
import xarray as xr

from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
BAY = [32.58, 0.20, 32.72, 0.34]


def cat():
    import planetary_computer as pc
    import pystac_client
    return pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)


def composite():
    from odc.stac import load
    f = KD / "sat_bay_s2_dry.nc"
    if f.exists():
        return
    items = list(cat().search(collections=["sentinel-2-l2a"], bbox=BAY, datetime="2024-06-01/2026-08-31",
                              query={"eo:cloud_cover": {"lt": 20}}).items())
    items = [i for i in items if i.datetime.month in (6, 7, 8, 1, 2)]
    print("composite scenes", len(items), flush=True)
    ds = load(items, bands=["B02", "B03", "B04", "B05", "B08", "B11", "SCL"], bbox=BAY, crs="EPSG:32636", resolution=20,
              groupby="solar_day", chunks={"x": 1024, "y": 1024})
    clear = ds.SCL.isin([4, 5, 6, 7])
    out = ds[["B02", "B03", "B04", "B05", "B08", "B11"]].where(clear).median("time")
    out["water_frac"] = (ds.SCL == 6).where(ds.SCL > 0).mean("time")
    out = out.compute()
    for b in ["B02", "B03", "B04", "B05", "B08", "B11"]:
        out[b] = ((out[b] - 1000) / 10000).astype("float32")
    out.to_netcdf(f)


SCN = [32.60, 0.12, 32.72, 0.31]  # scene box: inner + outer bay and open-lake reference
MOUTHS_LL = {"Nakivubo": (0.2904, 32.6360), "Kansanga": (0.2840, 32.6363), "Kinawataka": (0.2975, 32.6620)}
A645, C645 = 228.1, 0.1641  # Dogliotti et al. 2015, 645 nm


def utm(lat, lon):
    import pyproj
    return pyproj.Transformer.from_crs(4326, 32636, always_xy=True).transform(lon, lat)


def zones(x, y, water):
    """Zone label per pixel: 1 outlet (<= 1.2 km of a mouth), 2 inner bay, 3 outer bay, 4 open-lake reference."""
    X, Y = np.meshgrid(x, y)
    d = np.full(X.shape, np.inf)
    for la, lo in MOUTHS_LL.values():
        mx, my = utm(la, lo)
        d = np.minimum(d, np.hypot(X - mx, Y - my))
    _, y_gap = utm(0.236, 32.64)   # narrows between inner and outer bay
    _, y_ref = utm(0.170, 32.64)
    z = np.zeros(X.shape, np.int8)
    z[(Y > y_gap)] = 2
    z[(Y <= y_gap) & (Y > y_ref)] = 3
    z[Y <= y_ref] = 4
    z[(d <= 1200)] = 1
    z[~water] = 0
    return z


def watermask():
    """Static open-water mask over the scene box: water in >= 60% of clear dry-season Sentinel-2 looks (SCL water or
    SWIR < 0.03), so algae-rich and turbid water count as water; floating mats and land do not."""
    from odc.stac import load
    f = KD / "bay_watermask.nc"
    if f.exists():
        return xr.open_dataarray(f)
    items = list(cat().search(collections=["sentinel-2-l2a"], bbox=SCN, datetime="2024-06-01/2026-08-31",
                              query={"eo:cloud_cover": {"lt": 15}}).items())
    items = [i for i in items if i.datetime.month in (6, 7, 8, 1, 2)]
    ds = load(items, bands=["B11", "SCL"], bbox=SCN, crs="EPSG:32636", resolution=20, groupby="solar_day",
              chunks={"x": 2048, "y": 2048})
    off = 1000  # all these scenes are baseline >= 4
    clear = ds.SCL.isin([2, 4, 5, 6, 7, 11])
    wet = ((ds.SCL == 6) | (((ds.B11 - off) / 10000) < 0.03)).where(clear)
    m = (wet.mean("time") >= 0.6).compute().rename("water")
    m.astype("int8").to_netcdf(f)
    return m


def zone_grid(x, y):
    m = watermask()
    w = m.sel(x=xr.DataArray(x, dims="x"), y=xr.DataArray(y, dims="y"), method="nearest").values.astype(bool)
    return zones(x, y, w)


def turb(rho):
    rho = np.clip(rho, 0, 0.16)
    return A645 * rho / (1 - rho / C645)


def scenes():
    """Per-scene zone medians, every Sentinel-2 L2A scene 2017-2026 over the bay."""
    from odc.stac import load
    f = RES / "kd_bay_s2_scenes.csv"
    done = pd.read_csv(f, parse_dates=["date"]) if f.exists() else pd.DataFrame(columns=["date"])
    items = list(cat().search(collections=["sentinel-2-l2a"], bbox=SCN, datetime="2017-01-01/2026-10-13",
                              query={"eo:cloud_cover": {"lt": 70}}).items())
    by_day = {}
    for i in items:
        by_day.setdefault(i.datetime.date(), []).append(i)
    days = sorted(d for d in by_day if pd.Timestamp(d) not in set(done.date))
    print("scene-days", len(by_day), "to do", len(days), flush=True)
    rows = []
    zz = None
    for k in range(0, len(days), 20):
        its = [i for d in days[k:k + 20] for i in by_day[d]]
        ds = load(its, bands=["B04", "B05", "B08", "B11", "SCL"], bbox=SCN, crs="EPSG:32636", resolution=20,
                  groupby="solar_day", chunks={"x": 2048, "y": 2048}).compute()
        if zz is None:
            zz = zone_grid(ds.x.values, ds.y.values)
        for t in range(ds.sizes["time"]):
            day = pd.Timestamp(ds.time.values[t]).normalize()
            base = max(float(i.properties.get("s2:processing_baseline", "0")) for i in by_day[day.date()])
            off = 1000 if base >= 4 else 0
            s = ds.isel(time=t)
            r4, r5, r8, r11 = [(s[b].values.astype("float32") - off) / 10000 for b in ("B04", "B05", "B08", "B11")]
            ok = ~np.isin(s.SCL.values, [0, 1, 3, 8, 9, 10]) & (r11 < 0.03) & (r4 > 0) & (r4 < 0.16)
            row = dict(date=day, baseline=base)
            for zi, zn in ((1, "outlet"), (2, "inner"), (3, "outer"), (4, "ref")):
                m = ok & (zz == zi)
                n_all = (zz == zi).sum()
                row[f"{zn}_valid"] = m.sum() / n_all
                if m.sum() / n_all >= 0.3:
                    row[f"{zn}_turb"] = float(np.median(turb(r4[m])))
                    row[f"{zn}_ndci"] = float(np.median(((r5 - r4) / (r5 + r4))[m]))
            rows.append(row)
        out = pd.concat([done, pd.DataFrame(rows)]).sort_values("date")
        out.round(4).to_csv(f, index=False)
        print(days[min(k + 19, len(days) - 1)], "rows", len(out), flush=True)


def landsat():
    """Long record: Landsat 5/7/8/9 red-band turbidity in the same zones, 1986-2026."""
    from odc.stac import load
    f = RES / "kd_bay_landsat_scenes.csv"
    done = pd.read_csv(f, parse_dates=["date"]) if f.exists() else pd.DataFrame(columns=["date"])
    items = list(cat().search(collections=["landsat-c2-l2"], bbox=SCN, datetime="1984-01-01/2026-10-13",
                              query={"eo:cloud_cover": {"lt": 60},
                                     "platform": {"in": ["landsat-5", "landsat-7", "landsat-8", "landsat-9"]}}).items())
    by_day = {}
    for i in items:
        by_day.setdefault(i.datetime.date(), []).append(i)
    days = sorted(d for d in by_day if pd.Timestamp(d) not in set(done.date))
    print("landsat scene-days", len(by_day), "to do", len(days), flush=True)
    rows, zz = [], None
    for k in range(0, len(days), 25):
        its = [i for d in days[k:k + 25] for i in by_day[d]]
        ds = load(its, bands=["red", "nir08", "swir16", "qa_pixel"], bbox=SCN, crs="EPSG:32636", resolution=30, fail_on_error=False,
                  groupby="solar_day", chunks={"x": 2048, "y": 2048}).compute()
        if zz is None:
            zz = zone_grid(ds.x.values, ds.y.values)
        for t in range(ds.sizes["time"]):
            day = pd.Timestamp(ds.time.values[t]).normalize()
            s = ds.isel(time=t)
            qa = s.qa_pixel.values
            r, n8, s1 = [s[b].values * 0.0000275 - 0.2 for b in ("red", "nir08", "swir16")]
            ok = (qa != 0) & ((qa & 0b11110) == 0) & (s1 < 0.03) & (r > 0) & (r < 0.16)
            row = dict(date=day, platform=by_day[day.date()][0].properties["platform"])
            for zi, zn in ((1, "outlet"), (2, "inner"), (3, "outer"), (4, "ref")):
                m = ok & (zz == zi)
                row[f"{zn}_valid"] = m.sum() / max((zz == zi).sum(), 1)
                if row[f"{zn}_valid"] >= 0.3:
                    row[f"{zn}_turb"] = float(np.median(turb(r[m])))
            rows.append(row)
        out = pd.concat([done, pd.DataFrame(rows)]).sort_values("date")
        out.round(4).to_csv(f, index=False)
        print(days[min(k + 24, len(days) - 1)], "rows", len(out), flush=True)


BAY_CATCH = {15: "Nakivubo", 40: "Kinawataka", 41: "Kansanga", 112: "Munyonyo shore"}
VAL_HA = (1500, 2900)          # US$/ha/yr, wastewater treatment by intact papyrus wetland (Emerton et al. 1999)
LOAD = dict(N=800, P=150)      # kg/day entering the Inner Murchison Bay swamps via Nakivubo (Emerton et al. 1999)
EFF = dict(N=0.56, P=0.40)     # swamp-wide removal (Kansiime and Nalubega 1999)


def ls_composite(year):
    from odc.stac import load
    f = KD / f"sat_landsat_{year}.nc"
    if f.exists():
        return
    BB = [32.45, 0.20, 32.72, 0.42]
    plats = ["landsat-5"] if year < 2012 else ["landsat-8", "landsat-9"]
    items = []
    for y in range(year - 1, year + 2):
        items += list(cat().search(collections=["landsat-c2-l2"], bbox=BB, datetime=f"{y}-06-01/{y}-09-30",
                                   query={"eo:cloud_cover": {"lt": 40}, "platform": {"in": plats}}).items())
    if len(items) < 3:  # Landsat 5 is sparse over East Africa in the 2000s: all months, add Landsat 7
        for y in range(year - 1, year + 2):
            items += list(cat().search(collections=["landsat-c2-l2"], bbox=BB, datetime=f"{y}-01-01/{y}-12-31",
                                       query={"eo:cloud_cover": {"lt": 40},
                                              "platform": {"in": ["landsat-5", "landsat-7"]}}).items())
    print(year, "landsat scenes", len(items), flush=True)
    ds = load(items, bands=["red", "green", "blue", "nir08", "swir16", "qa_pixel"], bbox=BB, crs="EPSG:32636",
              resolution=30, groupby="solar_day", chunks={"x": 1024, "y": 1024})
    qa = ds.qa_pixel
    clear = ((qa & (1 << 3)) == 0) & ((qa & (1 << 4)) == 0) & ((qa & (1 << 1)) == 0) & (qa != 0)
    out = ds[["red", "green", "blue", "nir08", "swir16"]].where(clear).median("time")
    out = (out * 0.0000275 - 0.2).astype("float32").compute()
    out.attrs["n_scenes"] = len(items)
    out.to_netcdf(f)


def wetland():
    """Vegetated valley floor (HAND < 3 m, NDVI > 0.45) draining to Inner Murchison Bay, 1986-2025."""
    import pyproj
    import rasterio
    for y in (2005, 2015):
        ls_composite(y)
    tf = pyproj.Transformer.from_crs(32636, 4326, always_xy=True)
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        cfull, hfull, trf = r.read(1), r.read(2), r.transform
    rows = []
    for yr in (1986, 1995, 2005, 2015, 2025):
        d = xr.open_dataset(KD / f"sat_landsat_{yr}.nc")
        ndvi = ((d.nir08 - d.red) / (d.nir08 + d.red)).values
        X, Y = np.meshgrid(d.x.values, d.y.values)
        lo, la = tf.transform(X, Y)
        col = ((lo - trf.c) / trf.a).astype(int).clip(0, hfull.shape[1] - 1)
        row = ((la - trf.f) / trf.e).astype(int).clip(0, hfull.shape[0] - 1)
        hh, cc = hfull[row, col], cfull[row, col]
        land = np.isfinite(ndvi) & (ndvi > 0)
        fringe = (la > 0.24) & (la < 0.33) & (lo > 0.0 + 32.62) & (lo < 32.70)
        regs = {nm: (cc == cid) for cid, nm in BAY_CATCH.items()}
        regs["Bay fringe (lower Kinawataka, Luzira, Port Bell)"] = fringe & ~np.isin(cc, list(BAY_CATCH))
        for reg, m in regs.items():
            vf = m & land & (hh < 3)
            rows.append(dict(year=yr, region=reg, valley_floor_ha=vf.sum() * 0.09,
                             vegetated_ha=(vf & (ndvi > 0.45)).sum() * 0.09, n_scenes=d.attrs.get("n_scenes")))
    w = pd.DataFrame(rows)
    tot = w[w.region.isin(BAY_CATCH.values())].groupby("year")[["valley_floor_ha", "vegetated_ha"]].sum().reset_index() \
        .assign(region="Bay-draining catchments")
    w = pd.concat([w, tot])
    w["vegetated_pct"] = 100 * w.vegetated_ha / w.valley_floor_ha
    w.round(1).to_csv(RES / "kd_bay_wetland.csv", index=False)
    print(w.round(1).to_string())
    a = tot.set_index("year").vegetated_ha
    lost = a[1986] - a[2025]
    t = dict(vegetated_ha_1986=a[1986], vegetated_ha_1995=a[1995], vegetated_ha_2025=a[2025], lost_ha_1986_2025=lost,
             lost_pct=100 * lost / a[1986], value_lost_lo_usd=lost * VAL_HA[0], value_lost_hi_usd=lost * VAL_HA[1])
    nak = w[w.region == "Nakivubo"].set_index("year").vegetated_ha
    t["nakivubo_ratio_2025_1995"] = nak[2025] / nak[1995]
    for k in ("N", "P"):
        ratio = nak[2025] / nak[1995]
        t[f"{k}_retained_1995_kg_d"] = LOAD[k] * EFF[k]
        t[f"{k}_retained_2025_kg_d"] = LOAD[k] * EFF[k] * ratio
        t[f"{k}_lost_t_yr"] = (t[f"{k}_retained_1995_kg_d"] - t[f"{k}_retained_2025_kg_d"]) * 365 / 1000
    pd.Series(t).round(2).to_csv(RES / "kd_bay_treatment.csv", header=["value"])
    print(pd.Series(t).round(1).to_string())


def scene_turb(day):
    """Turbidity (FNU) map of one Sentinel-2 day over the bay; NaN off water, cloud, glint or floating mats."""
    from odc.stac import load
    f = KD / f"bay_turb_{day}.nc"
    if f.exists():
        return xr.open_dataarray(f)
    its = list(cat().search(collections=["sentinel-2-l2a"], bbox=SCN, datetime=f"{day}/{day}").items())
    base = max(float(i.properties.get("s2:processing_baseline", "0")) for i in its)
    off = 1000 if base >= 4 else 0
    s = load(its, bands=["B04", "B11", "SCL"], bbox=SCN, crs="EPSG:32636", resolution=20, groupby="solar_day").isel(time=0)
    r4, r11 = [(s[b].astype("float32") - off) / 10000 for b in ("B04", "B11")]
    w = watermask().sel(x=s.x, y=s.y, method="nearest").values.astype(bool)
    ok = w & ~np.isin(s.SCL.values, [0, 1, 3, 8, 9, 10]) & (r11.values < 0.03) & (r4.values > 0) & (r4.values < 0.16)
    T = xr.DataArray(np.where(ok, turb(r4.values), np.nan), coords=dict(y=s.y, x=s.x), dims=("y", "x"), name="turbidity")
    T.to_netcdf(f)
    return T


def chirps_kla():
    return xr.open_dataset(PROC / "chirps_uganda_daily.nc")["precip"].sel(lat=slice(0.15, 0.5), lon=slice(32.4, 32.8)) \
        .mean(("lat", "lon")).to_series()


def analysis():
    import statsmodels.formula.api as smf
    from scipy import stats
    ch = chirps_kla()
    rows = []
    # 1. long record: outlet / open-lake turbidity ratio vs wetland remaining (same-scene ratio removes sensor and haze)
    L = pd.read_csv(RES / "kd_bay_landsat_scenes.csv", parse_dates=["date"]).dropna(subset=["outlet_turb", "ref_turb"])
    L = L[L.ref_turb > 1].copy()
    L["ratio"] = L.outlet_turb / L.ref_turb
    w = pd.read_csv(RES / "kd_bay_wetland.csv")
    wb = w[w.region == "Bay-draining catchments"].set_index("year").vegetated_ha
    L["yr"] = L.date.dt.year + L.date.dt.dayofyear / 365.25
    L["wet_ha"] = np.interp(L.yr, wb.index.values, wb.values)
    L["m"] = L.date.dt.month
    L["r3"] = [ch[d - pd.Timedelta(days=3):d - pd.Timedelta(days=1)].sum() for d in L.date]
    tau, p = stats.kendalltau(L.yr, L.ratio)
    rows.append(dict(test="Landsat outlet/open-lake turbidity ratio vs time (Kendall)", n=len(L), estimate=tau, p=p))
    rho, p = stats.spearmanr(L.wet_ha, L.ratio)
    rows.append(dict(test="Landsat ratio vs bay-draining wetland remaining (Spearman)", n=len(L), estimate=rho, p=p))
    m = smf.ols("np.log(ratio) ~ I(wet_ha/100) + C(platform) + C(m) + np.log1p(r3)", data=L).fit(cov_type="HC1")
    rows.append(dict(test="log ratio per 100 ha wetland lost (sensor, month, 3-day rain controls)", n=len(L),
                     estimate=-m.params["I(wet_ha / 100)"], p=m.pvalues["I(wet_ha / 100)"],
                     ci_lo=-m.conf_int().loc["I(wet_ha / 100)", 1], ci_hi=-m.conf_int().loc["I(wet_ha / 100)", 0]))
    L["period"] = pd.cut(L.date.dt.year, [1983, 1995, 2005, 2015, 2026], labels=["1984-95", "1996-2005", "2006-15", "2016-26"])
    per = L.groupby("period", observed=True).agg(n=("ratio", "size"), ratio_median=("ratio", "median"),
                                                 outlet_fnu=("outlet_turb", "median"), lake_fnu=("ref_turb", "median"))
    per["wetland_ha_mid"] = [np.interp(v, wb.index.values, wb.values) for v in (1990, 2000, 2010, 2021)]
    per.round(3).to_csv(RES / "kd_bay_landsat_periods.csv")
    # 2. Sentinel-2 2017-2026: gradient and storms
    S = pd.read_csv(RES / "kd_bay_s2_scenes.csv", parse_dates=["date"])
    zt = {z: S[f"{z}_turb"].median() for z in ("outlet", "inner", "outer", "ref")}
    zn = {z: S[f"{z}_ndci"].median() for z in ("outlet", "inner", "outer", "ref")}
    pd.DataFrame(dict(turbidity_fnu=zt, ndci=zn, n={z: S[f"{z}_turb"].notna().sum() for z in zt})).round(3) \
        .to_csv(RES / "kd_bay_s2_zones.csv")
    b = S.dropna(subset=["outlet_turb", "ref_turb"]).copy()
    b["r3"] = [ch[d - pd.Timedelta(days=3):d - pd.Timedelta(days=1)].sum() for d in b.date]
    b = b[b.date <= ch.index.max()]
    b["ratio"] = b.outlet_turb / b.ref_turb
    b["t"] = (b.date - pd.Timestamp("2017-01-01")).dt.days / 365.25
    b["m"] = b.date.dt.month
    m2 = smf.ols("np.log(ratio) ~ np.log1p(r3) + t + C(m)", data=b).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
    rows.append(dict(test="S2 log outlet/lake ratio per log(1+3-day rain mm)", n=len(b), estimate=m2.params["np.log1p(r3)"],
                     p=m2.pvalues["np.log1p(r3)"]))
    rows.append(dict(test="S2 ratio, dry scenes (3-day rain < 1 mm), median", n=int((b.r3 < 1).sum()),
                     estimate=b[b.r3 < 1].ratio.median(), p=np.nan))
    rows.append(dict(test="S2 ratio, wet scenes (3-day rain >= 25 mm), median", n=int((b.r3 >= 25).sum()),
                     estimate=b[b.r3 >= 25].ratio.median(), p=np.nan))
    nd = S.dropna(subset=["outlet_ndci", "ref_ndci"])
    rows.append(dict(test="S2 NDCI outlet minus open lake (median, same scene)", n=len(nd),
                     estimate=(nd.outlet_ndci - nd.ref_ndci).median(), p=stats.wilcoxon(nd.outlet_ndci - nd.ref_ndci).pvalue))
    out = pd.DataFrame(rows)
    out.round(4).to_csv(RES / "kd_bay_tests.csv", index=False)
    print(per.round(2).to_string())
    print(out.round(4).to_string())
    figures(L, per, S, b, w)


def figures(L, per, S, b, w):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    src = ("Imagery: Copernicus Sentinel-2 L2A (ESA), NASA/USGS Landsat 5/7/8/9 via Microsoft Planetary Computer · rain: CHIRPS v2.0 · "
           "terrain: Copernicus GLO-30 · turbidity: Dogliotti et al. 2015 · NDCI: Mishra and Mishra 2012")
    # kd42: maps
    comp = xr.open_dataset(KD / "sat_bay_s2_dry.nc")
    rgb = np.clip(np.dstack([comp.B04, comp.B03, comp.B02]) / 0.15, 0, 1)
    ext = [float(comp.x.min()), float(comp.x.max()), float(comp.y.min()), float(comp.y.max())]
    fig, axs = plt.subplots(1, 3, figsize=(16, 7.2), gridspec_kw=dict(wspace=0.06))
    fig.subplots_adjust(left=0.02, right=0.92, top=0.86, bottom=0.12)
    axs[0].imshow(rgb, extent=ext)
    for nm, (la, lo) in MOUTHS_LL.items():
        x, y = utm(la, lo)
        axs[0].scatter([x], [y], s=60, color="#d0461e", edgecolor="white", zorder=3)
    lab = {"Nakivubo": (-3200, 1500), "Kansanga": (-3400, -1600), "Kinawataka": (700, -2200)}
    for nm, (dx, dy) in lab.items():
        x, y = utm(*MOUTHS_LL[nm])
        axs[0].annotate(nm, (x, y), xytext=(x + dx, y + dy), fontsize=10, color="white", fontweight="bold",
                        arrowprops=dict(arrowstyle="-", color="white", lw=0.8))
    axs[0].text(461200, 28500, "Inner\nMurchison Bay", color="white", fontsize=10, ha="center")
    axs[0].text(459800, 23300, "Outer bay", color="white", fontsize=10, ha="center")
    axs[0].set_title("a  Where the city's channels meet the lake", loc="left", fontsize=11)
    for ax, (dd, ttl) in zip(axs[1:], (("2026-06-29", "b  Dry spell, 29 Jun 2026 (0 mm in 3 days)"),
                                       ("2019-11-21", "c  After rain, 21 Nov 2019 (37 mm in 3 days)"))):
        T = scene_turb(dd)
        ax.imshow(rgb.mean(2), cmap="Greys_r", extent=ext, vmin=0, vmax=1.4, alpha=0.6)
        im = ax.imshow(T.values, cmap="YlOrBr", vmin=4, vmax=24, extent=[float(T.x.min()), float(T.x.max()),
                                                                        float(T.y.min()), float(T.y.max())])
        ax.set_title(ttl, loc="left", fontsize=11)
    for ax in axs:
        ax.set_xlim(456000, 465500)
        ax.set_ylim(22200, 34500)
        ax.set_xticks([])
        ax.set_yticks([])
    cax = fig.add_axes([0.93, 0.2, 0.012, 0.55])
    fig.colorbar(im, cax=cax, label="turbidity (FNU)")
    fig.suptitle("Inner Murchison Bay: the city's water reaches the lake", x=0.02, ha="left", fontweight="bold")
    save(fig, "kd42_bay_plumes.png", OUT, source=src)
    # kd43: wetland, long-term ratio, chlorophyll gradient
    fig, axs = plt.subplots(1, 3, figsize=(17, 5.4), gridspec_kw=dict(wspace=0.32))
    fig.subplots_adjust(left=0.05, right=0.98, top=0.84, bottom=0.25)
    ww = w[w.region.isin(BAY_CATCH.values())].pivot(index="year", columns="region", values="vegetated_ha")
    cols = {"Nakivubo": "#1b7837", "Kansanga": "#5aae61", "Kinawataka": "#a6dba0", "Munyonyo shore": "#d9f0d3"}
    bot = np.zeros(len(ww))
    for c in ["Nakivubo", "Kansanga", "Kinawataka", "Munyonyo shore"]:
        axs[0].bar(ww.index, ww[c], bottom=bot, width=6, color=cols[c], label=c, edgecolor="white", lw=1)
        bot += ww[c].values
    axs[0].set_ylabel("vegetated valley floor (ha)")
    axs[0].set_ylim(0, bot.max() * 1.3)
    axs[0].legend(fontsize=8.5, ncol=2, loc="upper right")
    axs[0].set_title("a  Wetland draining to the bay", loc="left", fontsize=11)
    pl = {"landsat-5": "#7570b3", "landsat-7": "#999999", "landsat-8": "#d95f02", "landsat-9": "#e7298a"}
    for k_, g in L.groupby("platform"):
        axs[1].scatter(g.date, g.ratio, s=10, color=pl[k_], alpha=0.5, label=k_.replace("landsat-", "Landsat "))
    mids = pd.to_datetime(["1990-07-01", "2000-07-01", "2010-07-01", "2021-07-01"])
    axs[1].plot(mids, per.ratio_median.values, "-o", color="#111", lw=2.2, ms=7, label="period median")
    axs[1].axhline(1, color="#888", lw=1)
    axs[1].set_ylim(0.4, 3.9)
    axs[1].set_ylabel("turbidity at outlets ÷ open lake (same day)")
    axs[1].legend(fontsize=8.5, ncol=3, loc="upper left")
    axs[1].set_title("b  The outlets are getting murkier than the lake", loc="left", fontsize=11)
    zl = ["outlet", "inner", "outer", "ref"]
    data = [S[f"{z}_ndci"].dropna().values for z in zl]
    axs[2].boxplot(data, widths=0.55, showfliers=False, medianprops=dict(color="#d0461e", lw=2))
    axs[2].set_xticks([1, 2, 3, 4])
    axs[2].set_xticklabels(["outlets", "inner bay", "outer bay", "open lake"])
    axs[2].set_ylabel("chlorophyll index, NDCI")
    axs[2].set_title("c  Algae: highest where the channels enter", loc="left", fontsize=11)
    save(fig, "kd43_bay_wetland_turbidity.png", OUT, source=src)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        globals()[s]()
        print("done", s, flush=True)
