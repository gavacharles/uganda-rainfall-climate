"""Paper D: who lives in the water's path, and how they got there (exposure, building form, settlement age).

Low ground = height above nearest drainage (HAND) < 2 m within 150 m of a flowing channel (>= 0.25 km2 upstream).
Comparison ground = HAND >= 10 m (hillslopes and ridges). Study box: Greater Kampala core (32.45-32.72E, 0.20-0.42N).
  exposure   residents on low ground by channel system, 1975-2030 (JRC GHS-POP)
  form       building footprints (Microsoft, 2023): median footprint area, buildings per hectare, share < 40 m2
             (single-room / rental-row scale), on low ground vs comparison ground
  age        year each 100 m cell first reached 20% built-up (JRC GHSL): when was low ground settled vs hills
  density    residents per built hectare (crowding) on low ground vs hills, 2020
Outputs: results/kd_D_*.csv, figures kd27-kd29.
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import shapely
import xarray as xr

from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
BOX = (32.45, 0.20, 32.72, 0.42)
SRC = ("Buildings: Microsoft Global ML Building Footprints (2023) · built-up and population: JRC GHSL R2023A · "
       "terrain: Copernicus GLO-30 DEM · channels: © OpenStreetMap contributors")
SYSTEMS = ["Lubigi", "Nalukolongo", "Nakivubo", "Kinawataka", "Kansanga", "Walufumbe", "other"]


def hand_lookup():
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        cat, hand = r.read(1), r.read(2)
        tr = r.transform

    def f(lon, lat):
        col = ((np.asarray(lon) - tr.c) / tr.a).astype(int).clip(0, hand.shape[1] - 1)
        row = ((np.asarray(lat) - tr.f) / tr.e).astype(int).clip(0, hand.shape[0] - 1)
        return hand[row, col], cat[row, col]
    return f


_FL = None


def near_channel(lon, lat, dist=150):
    global _FL
    if _FL is None:
        s = gpd.read_file(KD / "segments.gpkg").to_crs(32636)
        _FL = s[s.up_km2 >= 0.25].geometry.values
    pts = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs=4326).to_crs(32636).values
    near = np.zeros(len(pts), bool)
    near[np.unique(shapely.STRtree(pts).query(_FL, predicate="dwithin", distance=dist)[1])] = True
    return near


def sysnames(c):
    n = pd.read_csv(RES / "kampala_catchments.csv").set_index("id").name.dropna().to_dict()
    return np.array([n.get(int(x), "other") if x > 0 else "other" for x in c])


def main():
    look = hand_lookup()
    # ---------------- exposure by system
    pop = xr.open_dataarray(PROC / "kampala_ghs_pop.nc").sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    LO, LA = np.meshgrid(pop.lon.values, pop.lat.values)
    h, c = look(LO.ravel(), LA.ravel())
    low = (h < 2) & near_channel(LO.ravel(), LA.ravel())
    hill = h >= 10
    sysn = sysnames(c)
    rows = []
    for e in pop.epoch.values:
        v = np.nan_to_num(pop.sel(epoch=e).values.ravel())
        for sname in SYSTEMS:
            m = sysn == sname
            rows.append(dict(epoch=int(e), system=sname, low=v[low & m].sum(), total=v[m].sum()))
        rows.append(dict(epoch=int(e), system="hills (all)", low=v[hill].sum(), total=v.sum()))
    ex = pd.DataFrame(rows)
    ex["share_low"] = 100 * ex.low / ex.total.clip(lower=1)
    ex.round(1).to_csv(RES / "kd_D_exposure_by_system.csv", index=False)
    print(ex[ex.system != "hills (all)"].pivot(index="system", columns="epoch", values="low").round(-2).to_string())
    # growth rates: low ground vs hills vs whole box
    tot = ex[ex.system != "hills (all)"].groupby("epoch").low.sum()
    hl = ex[ex.system == "hills (all)"].set_index("epoch")
    gr = pd.DataFrame({"low_ground": tot, "hills": hl.low, "whole_area": hl.total})
    cagr = lambda s, a, b: 100 * ((s[b] / s[a]) ** (1 / (b - a)) - 1)
    gtab = pd.DataFrame([{**{"period": f"{a}-{b}"}, **{k: cagr(gr[k], a, b) for k in gr}} for a, b in ((1975, 2000), (2000, 2020), (2020, 2030))])
    gtab.round(2).to_csv(RES / "kd_D_growth_rates.csv", index=False)
    print(gtab.round(2).to_string())
    # crowding 2020: residents per hectare of built-up surface
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc").sel(lon=slice(BOX[0], BOX[2]), lat=slice(BOX[1], BOX[3]))
    gb = g.sel(epoch=2020).interp(lon=pop.lon, lat=pop.lat, method="nearest").values.ravel() / 1e4
    p20 = np.nan_to_num(pop.sel(epoch=2020).values.ravel())
    crowd = {k: p20[m].sum() / max(np.nan_to_num(gb[m]).sum(), 1e-9) for k, m in (("low ground", low), ("hills", hill))}
    # ---------------- settlement age (GHSL 100 m cells first >= 20% built)
    cell = (abs(float(np.diff(g.lon).mean())) * 111320 * np.cos(np.deg2rad(0.3))) * (abs(float(np.diff(g.lat).mean())) * 111320)
    GLO, GLA = np.meshgrid(g.lon.values, g.lat.values)
    gh, _ = look(GLO.ravel(), GLA.ravel())
    glow = (gh < 2) & near_channel(GLO.ravel(), GLA.ravel())
    ghill = gh >= 10
    first = np.full(GLO.size, np.nan)
    for e in sorted(g.epoch.values, reverse=True):
        first[(g.sel(epoch=e).values.ravel() / cell) >= 0.2] = e
    age = []
    for lab, m in (("low ground", glow), ("hills", ghill)):
        f_ = first[m]
        nb = max(np.isfinite(f_).sum(), 1)
        for a, b in ((1975, 1975), (1980, 1990), (1995, 2005), (2010, 2020), (2025, 2030)):
            age.append(dict(ground=lab, period="by 1975" if a == b else f"{a}-{b}", share=100 * ((f_ >= a) & (f_ <= b)).sum() / nb))
        age.append(dict(ground=lab, period="median year", share=float(np.nanmedian(f_))))
    ag = pd.DataFrame(age)
    ag.round(1).to_csv(RES / "kd_D_settlement_age.csv", index=False)
    print(ag.pivot(index="period", columns="ground", values="share").round(1))
    # ---------------- building form
    b = gpd.read_parquet(KD / "ms_buildings.parquet").cx[BOX[0]:BOX[2], BOX[1]:BOX[3]]
    bu = b.to_crs(32636)
    area = bu.area.values
    cen = b.geometry.centroid
    bh, bc = look(cen.x.values, cen.y.values)
    blow = (bh < 2) & near_channel(cen.x.values, cen.y.values)
    bhill = bh >= 10
    cu = bu.geometry.centroid
    form = []
    for lab, m in (("low ground", blow), ("hills", bhill)):
        gx = (cu.x.values[m] // 100).astype(int)
        gy = (cu.y.values[m] // 100).astype(int)
        per_ha = pd.Series(1, index=pd.MultiIndex.from_arrays([gx, gy])).groupby(level=[0, 1]).size()
        cov = pd.Series(area[m], index=pd.MultiIndex.from_arrays([gx, gy])).groupby(level=[0, 1]).sum() / 1e4 * 100
        form.append(dict(ground=lab, buildings=int(m.sum()), median_m2=float(np.median(area[m])),
                         share_lt40=100 * float((area[m] < 40).mean()), share_gt200=100 * float((area[m] > 200).mean()),
                         median_buildings_per_ha=float(per_ha.median()), median_roof_cover_pct=float(cov.median()),
                         residents_per_built_ha=crowd[lab]))
    fm = pd.DataFrame(form)
    fm.round(2).to_csv(RES / "kd_D_building_form.csv", index=False)
    print(fm.round(1).to_string())
    bsys = sysnames(bc)
    bs = pd.DataFrame({"system": bsys[blow], "area": area[blow]}).groupby("system").area.agg(
        n="size", median_m2="median", share_lt40=lambda v: 100 * (v < 40).mean())
    bs.round(1).to_csv(RES / "kd_D_building_form_by_system.csv")
    print(bs.round(1).to_string())
    figures(ex, ag, fm, area, blow, bhill)


def figures(ex, ag, fm, area, blow, bhill):
    cols = {"Lubigi": "#1f78b4", "Nakivubo": "#e31a1c", "Kinawataka": "#6a3d9a", "Nalukolongo": "#ff7f00",
            "Kansanga": "#33a02c", "Walufumbe": "#b15928", "other": "#999999"}
    piv = ex[ex.system != "hills (all)"].pivot(index="epoch", columns="system", values="low") / 1000
    fig, ax = plt.subplots(figsize=(11, 5.2))
    bottom = np.zeros(len(piv))
    for sname in SYSTEMS:
        ax.fill_between(piv.index, bottom, bottom + piv[sname].values, color=cols[sname], alpha=0.85, lw=0,
                        label=sname if sname != "other" else "other catchments (fringe)")
        bottom = bottom + piv[sname].values
    ax.axvspan(2020, 2031, color="#eee", lw=0, zorder=0)
    ax.text(2025.5, bottom.max() * 1.03, "projected", ha="center", fontsize=9, color="#666")
    ax.set_xlim(1975, 2030)
    ax.set_ylim(0, bottom.max() * 1.12)
    ax.set_ylabel("residents on low ground beside channels (thousands)")
    ax.legend(fontsize=8.5, loc="upper left", ncol=2)
    ax.set_title("Who lives in the water's path, by drainage system, 1975-2030", loc="left")
    save(fig, "kd27_exposure_by_system.png", OUT, source=SRC)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    order = ["by 1975", "1980-1990", "1995-2005", "2010-2020", "2025-2030"]
    p = ag[ag.period.isin(order)].pivot(index="period", columns="ground", values="share").reindex(order)
    x = np.arange(len(p))
    ax.bar(x - 0.2, p["hills"], 0.4, color="#9ecae1", label="hills and ridges (>= 10 m above the drains)")
    ax.bar(x + 0.2, p["low ground"], 0.4, color="#d6336c", label="low ground beside channels (< 2 m)")
    for i, (a, b_) in enumerate(zip(p["hills"], p["low ground"])):
        ax.text(i - 0.2, a + 0.6, f"{a:.0f}%", ha="center", fontsize=9)
        ax.text(i + 0.2, b_ + 0.6, f"{b_:.0f}%", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(["by 1975", "1980-90", "1995-2005", "2010-20", "2025-30\n(projected)"])
    ax.set_ylim(0, max(p.max()) * 1.18)
    ax.set_ylabel("share of built-up 100 m cells, by period first built")
    ax.set_title("When was it built? Low ground versus the hills", loc="left")
    ax.legend(fontsize=9, loc="upper right")
    save(fig, "kd28_settlement_age.png", OUT, source=SRC)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    bins = np.logspace(np.log10(10), np.log10(2000), 50)
    ax.hist(area[bhill], bins=bins, density=True, histtype="stepfilled", color="#9ecae1", alpha=0.7, label="hills and ridges")
    ax.hist(area[blow], bins=bins, density=True, histtype="step", color="#d6336c", lw=2.2, label="low ground beside channels")
    ax.set_xscale("log")
    ax.axvline(40, color="#555", ls="--", lw=1)
    ax.text(43, ax.get_ylim()[1] * 0.93, "40 m²: single rooms, rental rows", fontsize=9, color="#555")
    lo, hi = fm.set_index("ground").loc["low ground"], fm.set_index("ground").loc["hills"]
    ax.set_xlabel("building footprint (m², log scale)")
    ax.set_ylabel("density")
    ax.set_title(f"Building size: median {lo.median_m2:.0f} m² on low ground vs {hi.median_m2:.0f} m² on the hills", loc="left")
    ax.legend(fontsize=9, loc="upper right")
    save(fig, "kd29_building_form.png", OUT, source=SRC)


if __name__ == "__main__":
    main()
