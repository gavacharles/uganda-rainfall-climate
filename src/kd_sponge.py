"""Paper 1: the lost sponge - how much flood-storage volume Kampala's valley floors have lost, 1975-2030.

Storage capacity of a valley-floor cell for water standing h metres above the nearest drain:
    V(h) = max(0, h - HAND) x cell area                          (Copernicus 30 m DEM, HAND from D8 routing)
Effective storage = V(h) x (1 - built fraction): buildings, plots and the fill placed under them displace water.
Built fraction per epoch: JRC GHSL built-up surface 1975-2030 (2025, 2030 projected).
Demand: runoff volume of the gauge-corrected 10-, 50- and 100-year 6-hour storms (Paper 1 IDF:
72, 89, 96 mm), C = 0.25 + 0.65 x built share, over each catchment.
Check: Landsat dry-season composites 1986 / 1995 / 2025 - vegetated, unbuilt valley floor (NDVI > 0.45 and not
GHSL-built) as an independent signal of the remaining wetland sponge.
Outputs: results/kd_sponge_*.csv, figures kd30-kd32.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from rasterio.windows import from_bounds

from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
BOX = (32.45, 0.20, 32.72, 0.42)
STORM = {10: 72.3, 50: 88.6, 100: 95.5}  # mm, 6-hour, gauge-corrected (results/drainage_idf_kampala.csv)
SRC = ("Terrain: Copernicus GLO-30 DEM · built-up: JRC GHSL R2023A (2025, 2030 projected) · storms: gauge-corrected "
       "CHIRPS IDF (this study) · imagery: NASA/USGS Landsat")
SYSTEMS = ["Lubigi", "Nakivubo", "Kinawataka", "Kansanga", "Nalukolongo", "Walufumbe"]


def grids():
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        w = from_bounds(*BOX, r.transform)
        cat, hand = r.read(1, window=w), r.read(2, window=w)
        tr = r.window_transform(w)
    H, W = hand.shape
    lon = tr.c + tr.a * (np.arange(W) + 0.5)
    lat = tr.f + tr.e * (np.arange(H) + 0.5)
    cell = (abs(tr.a) * 111320 * np.cos(np.deg2rad(lat.mean()))) * (abs(tr.e) * 110574)  # m2
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc")
    gcell = (abs(float(np.diff(g.lon).mean())) * 111320 * np.cos(np.deg2rad(0.3))) * (abs(float(np.diff(g.lat).mean())) * 110574)
    built = {int(e): np.clip(g.sel(epoch=e).sel(lat=lat, lon=lon, method="nearest").values / gcell, 0, 1) for e in g.epoch.values}
    names = pd.read_csv(RES / "kampala_catchments.csv").set_index("id").name.dropna().to_dict()
    k = float(pd.read_csv(RES / "kampala_catchments.csv").k_impervious_over_ghsl.iloc[0])  # GHSL -> impervious (WorldCover-calibrated)
    built = {e: np.clip(k * b, 0, 0.95) for e, b in built.items()}
    from rasterio.warp import Resampling, reproject
    wc = np.zeros(hand.shape, np.uint8)
    with rasterio.open(PROC / "kampala_worldcover.tif") as r:
        reproject(r.read(1), wc, src_transform=r.transform, src_crs=r.crs, dst_transform=tr, dst_crs="EPSG:4326",
                  resampling=Resampling.mode)
    hand = np.where(wc == 80, np.nan, hand)  # open water is not storage
    return hand, cat, built, cell, names, lon, lat


def main():
    hand, cat, built, cell, names, lon, lat = grids()
    epochs = sorted(built)
    rows = []
    regions = {nm: cat == cid for cid, nm in names.items() if nm in SYSTEMS}
    regions["Greater Kampala core"] = np.isfinite(hand)
    regions = {k_: m & np.isfinite(hand) for k_, m in regions.items()}
    for reg, m in regions.items():
        area_km2 = m.sum() * cell / 1e6
        for e in epochs:
            b = built[e]
            r = dict(region=reg, epoch=e, area_km2=area_km2,
                     built_share=float(b[m].mean()))
            for h in (1, 2, 3):
                cap = np.nan_to_num(np.clip(h - hand, 0, None)) * cell
                r[f"storage_{h}m_Mm3"] = float((cap * (1 - b))[m].sum() / 1e6)
                r[f"capacity_{h}m_Mm3"] = float(cap[m].sum() / 1e6)
            C = 0.25 + 0.65 * r["built_share"]
            for T, P in STORM.items():
                r[f"runoff_T{T}_Mm3"] = P / 1000 * C * area_km2 * 1e6 / 1e6
            rows.append(r)
    df = pd.DataFrame(rows)
    for h in (1, 2, 3):
        df[f"lost_{h}m_pct"] = 100 * (1 - df[f"storage_{h}m_Mm3"] / df[f"capacity_{h}m_Mm3"])
    df["sponge_ratio_T10"] = df.storage_1m_Mm3 / df.runoff_T10_Mm3  # share of a 10-yr storm's runoff the 1 m sponge can hold
    df.round(4).to_csv(RES / "kd_sponge_storage.csv", index=False)
    core = df[df.region == "Greater Kampala core"].set_index("epoch")
    print(core[["built_share", "capacity_1m_Mm3", "storage_1m_Mm3", "lost_1m_pct", "storage_2m_Mm3", "runoff_T10_Mm3",
                "sponge_ratio_T10"]].round(2).to_string())
    sys_tab = df[df.epoch.isin([1975, 2020, 2030])].pivot(index="region", columns="epoch", values="storage_1m_Mm3").round(3)
    print(sys_tab.to_string())
    # change in runoff vs change in storage, 1975 -> 2020, per region
    ch = []
    for reg in regions:
        a, b_ = df[(df.region == reg) & (df.epoch == 1975)].iloc[0], df[(df.region == reg) & (df.epoch == 2020)].iloc[0]
        ch.append(dict(region=reg, storage_lost_Mm3=a.storage_1m_Mm3 - b_.storage_1m_Mm3,
                       extra_runoff_T10_Mm3=b_.runoff_T10_Mm3 - a.runoff_T10_Mm3,
                       sponge_ratio_1975=a.sponge_ratio_T10, sponge_ratio_2020=b_.sponge_ratio_T10))
    ch = pd.DataFrame(ch)
    ch["combined_gap_Mm3"] = ch.storage_lost_Mm3 + ch.extra_runoff_T10_Mm3
    ch["olympic_pools"] = ch.combined_gap_Mm3 * 1e6 / 2500
    ch.round(3).to_csv(RES / "kd_sponge_gap.csv", index=False)
    print(ch.round(2).to_string())
    landsat = landsat_check(hand, built)
    figures(df, ch, hand, built, lon, lat, landsat)


def landsat_check(hand, built):
    """Functional sponge: storage capacity (1 m and 2 m above the drains) on valley floor that is still vegetated
    (NDVI > 0.45) in Landsat dry-season median composites, excluding open water (NDVI < 0)."""
    import pyproj
    rows = []
    tf = pyproj.Transformer.from_crs(32636, 4326, always_xy=True)
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        cfull, hfull = r.read(1), r.read(2)
        trf = r.transform
    names = pd.read_csv(RES / "kampala_catchments.csv").set_index("id").name.dropna().to_dict()
    for yr in (1986, 1995, 2025):
        f = KD / f"sat_landsat_{yr}.nc"
        if not f.exists():
            continue
        d = xr.open_dataset(f)
        ndvi = ((d.nir08 - d.red) / (d.nir08 + d.red)).values
        X, Y = np.meshgrid(d.x.values, d.y.values)
        lo, la = tf.transform(X, Y)
        col = ((lo - trf.c) / trf.a).astype(int).clip(0, hfull.shape[1] - 1)
        row = ((la - trf.f) / trf.e).astype(int).clip(0, hfull.shape[0] - 1)
        hh, cc = hfull[row, col], cfull[row, col]
        inbox = (lo >= BOX[0]) & (lo <= BOX[2]) & (la >= BOX[1]) & (la <= BOX[3]) & np.isfinite(ndvi) & (ndvi > 0)
        veg = ndvi > 0.45
        px = 900.0  # m2
        regs = {"Greater Kampala core": inbox}
        regs.update({nm: inbox & (cc == cid) for cid, nm in names.items() if nm in SYSTEMS})
        for reg, m in regs.items():
            r = dict(year=yr, region=reg)
            for h in (1, 2):
                cap = np.clip(h - hh, 0, None) * px
                r[f"capacity_{h}m_Mm3"] = float(cap[m].sum() / 1e6)
                r[f"sponge_{h}m_Mm3"] = float(cap[m & veg].sum() / 1e6)
            vf = m & (hh < 2)
            r["valley_floor_vegetated_pct"] = 100 * float(veg[vf].mean())
            rows.append(r)
    out = pd.DataFrame(rows)
    out["sponge_1m_pct"] = 100 * out.sponge_1m_Mm3 / out.capacity_1m_Mm3
    out.round(3).to_csv(RES / "kd_sponge_landsat.csv", index=False)
    print(out[out.region == "Greater Kampala core"].round(2).to_string())
    print(out.pivot(index="region", columns="year", values="sponge_1m_Mm3").round(3).to_string())
    return out


def figures(df, ch, hand, built, lon, lat, landsat):
    core = df[df.region == "Greater Kampala core"].set_index("epoch")
    fig, axs = plt.subplots(1, 3, figsize=(17, 5.3), gridspec_kw=dict(width_ratios=[1, 1.15, 1.15], wspace=0.42))
    ax = axs[0]
    for h, c in ((1, "#08519c"), (2, "#6baed6")):
        ax.plot(core.index, core[f"storage_{h}m_Mm3"], marker="o", ms=4, color=c, lw=2.4, label=f"{h} m above the drains")
        ax.plot(core.index, core[f"capacity_{h}m_Mm3"], ls=":", color=c, lw=1.2)
    ax.axvspan(2020, 2031, color="#eee", lw=0)
    ax.set_ylabel("storage on unpaved valley floor (million m³)")
    ax.set_title("a  Storage left as the city paves over\n(dotted: with no paving)", loc="left", fontsize=11)
    ax.legend(fontsize=8.5, loc="center right")
    ax = axs[1]
    L = landsat[landsat.region.isin(SYSTEMS)].pivot(index="region", columns="year", values="sponge_1m_Mm3").reindex(SYSTEMS[::-1])
    y = np.arange(len(L))
    ax.barh(y + 0.2, L[1986], 0.4, color="#41ab5d", label="1986")
    ax.barh(y - 0.2, L[2025], 0.4, color="#a1d99b", label="2025")
    for yy, a, b_ in zip(y, L[1986], L[2025]):
        ax.text(max(a, b_) * 1.03, yy, f"-{100 * (1 - b_ / a):.0f}%", va="center", fontsize=9.5, fontweight="bold", color="#b30000")
    ax.set_yticks(y)
    ax.set_yticklabels(L.index)
    ax.set_xlim(0, L.values.max() * 1.25)
    ax.set_xlabel("million m³ (1 m storage on vegetated valley floor)")
    ax.set_title("b  The living sponge (Landsat): wetland\nstorage, 1986 vs 2025", loc="left", fontsize=11)
    ax.legend(fontsize=8.5, loc="lower right")
    ax = axs[2]
    c2 = ch[ch.region != "Greater Kampala core"].set_index("region").reindex(SYSTEMS[::-1])
    ax.barh(y, c2.storage_lost_Mm3, color="#6baed6", label="storage lost")
    ax.barh(y, c2.extra_runoff_T10_Mm3, left=c2.storage_lost_Mm3, color="#fd8d3c", label="extra 10-year storm runoff")
    for yy, v in zip(y, c2.combined_gap_Mm3):
        ax.text(v * 1.03, yy, f"{v:.2f}", va="center", fontsize=9.5)
    ax.set_yticks(y)
    ax.set_yticklabels(c2.index)
    ax.set_xlim(0, c2.combined_gap_Mm3.max() * 1.25)
    ax.set_xlabel("million m³, 1975 → 2020")
    ax.set_title("c  Water with nowhere to go\n(1 m storage lost + extra runoff)", loc="left", fontsize=11)
    ax.legend(fontsize=8.5, loc="lower right")
    save(fig, "kd30_lost_sponge.png", OUT, source=SRC)
    # map: storage lost 1975 -> 2020 at 1 m
    cap = np.clip(1 - hand, 0, None)
    lost = cap * (built[2020] - built[1975])
    fig, ax = plt.subplots(figsize=(9.5, 8))
    ext = [lon.min(), lon.max(), lat.min(), lat.max()]
    ax.imshow(np.where(cap > 0, 1, np.nan), cmap=plt.matplotlib.colors.ListedColormap(["#dbe9f6"]), extent=ext)
    im = ax.imshow(np.where(lost > 0.02, lost, np.nan), cmap="OrRd", vmin=0, vmax=0.8, extent=ext)
    ax.set_xticks([])
    ax.set_yticks([])
    fig.colorbar(im, ax=ax, shrink=0.6, label="storage depth lost, 1975-2020 (m of water per m² of valley floor)")
    ax.set_title("Where Kampala's flood storage was paved over, 1975-2020\n(light blue: valley floor and wetland that can hold water 1 m above the drains)",
                 loc="left", fontsize=11)
    save(fig, "kd31_sponge_lost_map.png", OUT, source=SRC)


if __name__ == "__main__":
    main()
