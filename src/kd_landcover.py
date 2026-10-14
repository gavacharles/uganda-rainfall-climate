"""Machine-learning land cover of Kampala's valley floors, 1986-2025 (for Papers 1 and 2).

Why: Papers 1 and 2 used one rule (NDVI > 0.45 = living wetland), which cannot separate papyrus from gardens, trees or
grass, or bare fill from roofs. Here a LightGBM classifier maps six classes on Landsat dry-season composites.

Labels   pixels where two independent 10 m maps agree: ESA WorldCover 2021 and Impact Observatory (IO) 2023
         wetland vegetation (WC 90 & IO 4) | trees/shrubs (WC 10,20 & IO 2,11) | crops/grass (WC 30,40 & IO 5,11)
         built (WC 50 & IO 7) | bare/fill (WC 60 & IO 8) | water (WC 80 & IO 1); 30 m cells taken by majority
Features 5 surface-reflectance bands, NDVI, MNDWI, NDBI, SWIR/NIR, brightness, plus HAND (wetlands sit low)
Sensors  TM/ETM+ composites (1986, 1995, 2005) mapped to OLI-equivalent with Roy et al. (2016) surface-reflectance OLS
Checks   (1) spatial block cross-validation on 2025 (3 km blocks, never train and test in the same block)
         (2) temporal transfer: model trained on 2025 predicts the 2015 composite, scored against IO 2017
         (3) built class in 1986 vs JRC GHSL built-up 1985 on the valley floor
Outputs  results/kd_landcover_*.csv, data/kd/landcover_<year>.nc, figure kd44
"""
import numpy as np
import pandas as pd
import pyproj
import rasterio
import xarray as xr
from rasterio.warp import Resampling, reproject

from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
YEARS = (1986, 1995, 2005, 2015, 2025)
CLASSES = ["wetland vegetation", "trees and shrubs", "crops and grass", "built and bare", "water"]
COLORS = ["#1b7837", "#a6d96a", "#e6c86e", "#d6604d", "#4393c3"]
# Roy et al. (2016) surface reflectance OLS, ETM+ -> OLI (TM treated as ETM+): intercept, slope
ROY = dict(blue=(0.0003, 0.8474), green=(0.0088, 0.8483), red=(0.0061, 0.9047), nir08=(0.0412, 0.8462),
           swir16=(0.0254, 0.8937))
SYSTEMS = {10: "Lubigi", 15: "Nakivubo", 40: "Kinawataka", 41: "Kansanga", 66: "Nalukolongo", 129: "Walufumbe"}


def grid():
    d = xr.open_dataset(KD / "sat_landsat_2025.nc")
    x, y = d.x.values, d.y.values
    tr = rasterio.transform.from_origin(x[0] - 15, y[0] + 15, 30, 30)
    return x, y, tr


def to_grid(src_arr, src_tr, src_crs, tr, shape, how=Resampling.mode):
    out = np.zeros(shape, src_arr.dtype)
    reproject(src_arr, out, src_transform=src_tr, src_crs=src_crs, dst_transform=tr, dst_crs="EPSG:32636", resampling=how)
    return out


def labels(x, y, tr):
    shape = (len(y), len(x))
    with rasterio.open(PROC / "kampala_worldcover.tif") as r:
        wc = to_grid(r.read(1), r.transform, r.crs, tr, shape)
    io = xr.open_dataset(KD / "sat_iolulc.nc").data
    iotr = rasterio.transform.from_origin(float(io.x[0]) - 5, float(io.y[0]) + 5, 10, 10)

    def io_year(yr):
        return to_grid(io.sel(time=yr).values.astype("uint8"), iotr, "EPSG:32636", tr, shape)
    wcmap = {90: 0, 10: 1, 20: 1, 30: 2, 40: 2, 50: 3, 60: 3, 80: 4}
    iomap = {4: [0], 2: [1], 11: [1, 2], 5: [2], 7: [3], 8: [3], 1: [4]}
    wcc = np.vectorize(lambda v: wcmap.get(int(v), -1))(wc)
    import geopandas as gpd
    from rasterio.features import rasterize
    ow = gpd.read_file(KD / "osm_wetlands.geojson").to_crs(32636)
    osm = rasterize(((g, 1) for g in ow.geometry if g is not None and not g.is_empty), out_shape=shape, transform=tr,
                    fill=0, dtype="uint8")

    def agree(ioa):
        lab = np.full(shape, -1, np.int8)
        for code, cls in iomap.items():
            for c in cls:
                lab[(ioa == code) & (wcc == c)] = c
        votes = (wcc == 0).astype(int) + (ioa == 4) + (osm == 1)
        lab[(votes >= 2) & (wcc != 4) & (ioa != 1)] = 0   # wetland: any two of WorldCover, IO, OSM (not open water)
        return lab
    return agree(io_year(2023)), agree(io_year(2017)), io_year(2017)


def terrain(x, y):
    tf = pyproj.Transformer.from_crs(32636, 4326, always_xy=True)
    X, Y = np.meshgrid(x, y)
    lo, la = tf.transform(X, Y)
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        c, h, t = r.read(1), r.read(2), r.transform
    col = ((lo - t.c) / t.a).astype(int).clip(0, h.shape[1] - 1)
    row = ((la - t.f) / t.e).astype(int).clip(0, h.shape[0] - 1)
    return h[row, col], c[row, col], lo, la


def features(year, hand):
    d = xr.open_dataset(KD / f"sat_landsat_{year}.nc")
    b = {k: d[k].values.astype("float32") for k in ROY}
    if year < 2013:
        b = {k: ROY[k][0] + ROY[k][1] * v for k, v in b.items()}
    e = 1e-6
    f = dict(b)
    f["ndvi"] = (b["nir08"] - b["red"]) / (b["nir08"] + b["red"] + e)
    f["mndwi"] = (b["green"] - b["swir16"]) / (b["green"] + b["swir16"] + e)
    f["ndbi"] = (b["swir16"] - b["nir08"]) / (b["swir16"] + b["nir08"] + e)
    f["swir_nir"] = b["swir16"] / (b["nir08"] + e)
    f["bright"] = (b["blue"] + b["green"] + b["red"] + b["nir08"] + b["swir16"]) / 5
    f["hand"] = np.where(np.isfinite(hand), np.clip(hand, 0, 60), 60).astype("float32")
    names = list(f)
    return np.stack([f[n] for n in names], -1), names


def sample(lab, X, blocks, n_per=5000, seed=0):
    rng = np.random.default_rng(seed)
    ok = (lab >= 0) & np.isfinite(X).all(-1)
    idx = []
    for c in range(len(CLASSES)):
        p = np.flatnonzero(ok.ravel() & (lab.ravel() == c))
        idx.append(rng.choice(p, min(n_per, len(p)), replace=False))
    idx = np.concatenate(idx)
    return X.reshape(-1, X.shape[-1])[idx], lab.ravel()[idx], blocks.ravel()[idx]


def model():
    import lightgbm as lgb
    return lgb.LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31, min_child_samples=30,
                              subsample=0.8, subsample_freq=1, colsample_bytree=0.8, class_weight="balanced",
                              random_state=0, verbose=-1)


def main():
    from sklearn.metrics import classification_report, confusion_matrix, f1_score
    from sklearn.model_selection import GroupKFold
    x, y, tr = grid()
    lab23, lab17, io17 = labels(x, y, tr)
    hand, cat, lo, la = terrain(x, y)
    X25, names = features(2025, hand)
    X_, Y_ = np.meshgrid(x, y)
    blocks = ((X_ - x.min()) // 3000).astype(int) * 100 + ((Y_ - y.min()) // 3000).astype(int)
    Xs, ys, gs = sample(lab23, X25, blocks)
    X15, _ = features(2015, hand)
    Xs15, ys15, gs15 = sample(lab17, X15, blocks, seed=1)
    print("training cells per class 2025", np.bincount(ys, minlength=5), "2015", np.bincount(ys15, minlength=5), flush=True)
    # (1) spatial block CV
    pred = np.zeros_like(ys)
    for trn, tst in GroupKFold(n_splits=5).split(Xs, ys, gs):
        m = model().fit(Xs[trn], ys[trn])
        pred[tst] = m.predict(Xs[tst])
    rep = classification_report(ys, pred, target_names=CLASSES, output_dict=True, zero_division=0)
    cv = pd.DataFrame(rep).T.round(3)
    cv.to_csv(RES / "kd_landcover_cv.csv")
    pd.DataFrame(confusion_matrix(ys, pred), index=CLASSES, columns=CLASSES).to_csv(RES / "kd_landcover_confusion.csv")
    print(cv.to_string(), flush=True)
    # (2) temporal transfer: a model trained on 2025 only, scored on 2015 against 2017 labels (two-source agreement)
    m25 = model().fit(Xs, ys)
    p15 = m25.predict(Xs15)
    tt = pd.DataFrame([dict(check="2025-trained model on 2015 imagery vs 2017 labels", n=len(ys15),
                            overall_accuracy=(p15 == ys15).mean(), macro_f1=f1_score(ys15, p15, average="macro"),
                            wetland_f1=f1_score(ys15 == 0, p15 == 0))])
    # final model: 2025 and 2015 samples together (sensor and season variety)
    m = model().fit(np.vstack([Xs, Xs15]), np.concatenate([ys, ys15]))
    pd.Series(m.feature_importances_, index=names).sort_values(ascending=False) \
        .to_csv(RES / "kd_landcover_importance.csv", header=["splits"])
    maps = {}
    for yr in YEARS:
        X, _ = features(yr, hand)
        ok = np.isfinite(X).all(-1)
        P = np.full(ok.shape + (len(CLASSES),), np.nan, "float32")
        P[ok] = m.predict_proba(X[ok])
        cls = np.where(ok, np.nanargmax(np.nan_to_num(P, nan=-1), -1), -1).astype("int8")
        conf = np.nanmax(P, -1)
        maps[yr] = cls
        xr.Dataset(dict(cls=(("y", "x"), cls), conf=(("y", "x"), conf)), coords=dict(x=x, y=y)) \
            .to_netcdf(KD / f"landcover_{yr}.nc")
        print("classified", yr, flush=True)
    # (3) built 1986 vs GHSL 1985 on valley floor
    g = xr.open_dataarray(PROC / "kampala_ghsl_built.nc")
    gcell = (abs(float(np.diff(g.lon).mean())) * 111320 * np.cos(np.deg2rad(0.3))) * (abs(float(np.diff(g.lat).mean())) * 110574)
    vf = (hand < 3) & (maps[1986] >= 0)
    gb = np.clip(g.sel(epoch=1985).sel(lat=xr.DataArray(la[vf]), lon=xr.DataArray(lo[vf]), method="nearest").values / gcell, 0, 1)
    tt.loc[len(tt)] = dict(check="1986 built share of valley floor (overall_accuracy = classifier, macro_f1 = GHSL 1985)",
                           n=int(vf.sum()), overall_accuracy=(maps[1986][vf] == 3).mean(), macro_f1=float(gb.mean()),
                           wetland_f1=np.nan)
    tt.round(3).to_csv(RES / "kd_landcover_checks.csv", index=False)
    print(tt.round(3).to_string(), flush=True)
    # areas on the valley floor by system and year
    rows = []
    regs = {nm: cat == cid for cid, nm in SYSTEMS.items()}
    regs["Bay-draining (Nakivubo, Kinawataka, Kansanga, Munyonyo)"] = np.isin(cat, [15, 40, 41, 112])
    regs["Greater Kampala core"] = cat > 0
    for reg, mm in regs.items():
        v = mm & (hand < 3) & np.isfinite(hand)
        for yr in YEARS:
            c = maps[yr][v]
            c = c[c >= 0]
            r = dict(region=reg, year=yr, valley_floor_ha=len(c) * 0.09)
            for i, nm in enumerate(CLASSES):
                r[nm + "_ha"] = (c == i).sum() * 0.09
            rows.append(r)
    a = pd.DataFrame(rows)
    a.round(1).to_csv(RES / "kd_landcover_valley.csv", index=False)
    print(a[a.region.str.startswith(("Greater", "Bay"))].round(0).to_string(), flush=True)
    figure(maps, hand, a, x, y, cv, tt)


def figure(maps, hand, a, x, y, cv, tt):
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    cm = ListedColormap(COLORS)
    fig = plt.figure(figsize=(17, 8.2))
    ext = [x.min() - 15, x.max() + 15, y.min() - 15, y.max() + 15]
    for i, yr in enumerate((1986, 2025)):
        ax = fig.add_axes([0.01 + i * 0.315, 0.14, 0.3, 0.72])
        mp = np.where((hand < 3) & (maps[yr] >= 0), maps[yr], np.nan).astype(float)
        ax.imshow(np.where(np.isfinite(hand), 1, np.nan), cmap="Greys", vmin=0, vmax=8, extent=ext)
        ax.imshow(mp, cmap=cm, vmin=-0.5, vmax=len(CLASSES) - 0.5, extent=ext, interpolation="nearest")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"{'ab'[i]}  Valley floors, {yr}", loc="left", fontsize=12)
    fig.legend(handles=[Patch(color=c, label=n) for c, n in zip(COLORS, CLASSES)], loc="lower left", ncol=6,
               bbox_to_anchor=(0.01, 0.06), fontsize=9.5, frameon=False)
    ax = fig.add_axes([0.69, 0.2, 0.29, 0.62])
    s = a[a.region == "Greater Kampala core"].set_index("year")
    bot = np.zeros(len(s))
    for c, col in zip(CLASSES, COLORS):
        v = s[c + "_ha"].values / 100
        ax.bar(s.index, v, bottom=bot, width=6, color=col, edgecolor="white", lw=0.8)
        bot += v
    ax.set_ylabel("valley floor (km²)")
    ax.set_xticks(list(s.index))
    ax.set_title("c  What the valley floors became", loc="left", fontsize=12)
    oa = cv.loc["accuracy", "precision"] if "accuracy" in cv.index else np.nan
    ax.text(0, -0.2, f"Spatial cross-validation accuracy {oa:.0%}, wetland F1 {cv.loc['wetland vegetation', 'f1-score']:.2f}; "
            f"trained on 2025, tested on 2015: {tt.overall_accuracy[0]:.0%}", transform=ax.transAxes, fontsize=9, color="#555")
    fig.suptitle("Kampala's valley floors, 1986 vs 2025 (machine-learning land cover, height above drain < 3 m)",
                 x=0.01, ha="left", fontweight="bold")
    save(fig, "kd44_valley_landcover_ml.png", OUT,
         source="Imagery: NASA/USGS Landsat 5/7/8/9 · labels: ESA WorldCover 2021, Impact Observatory/Esri 10 m LULC 2017-2023 · "
                "terrain: Copernicus GLO-30 · model: LightGBM")


if __name__ == "__main__":
    main()


def animate():
    """Social GIF: valley-floor land cover 1986 -> 2025 (still companion: kd44)."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    from PIL import Image
    x, y, tr = grid()
    hand, cat, lo, la = terrain(x, y)
    a = pd.read_csv(RES / "kd_landcover_valley.csv")
    core = a[a.region == "Greater Kampala core"].set_index("year")
    cm = ListedColormap(COLORS)
    ext = [x.min() - 15, x.max() + 15, y.min() - 15, y.max() + 15]
    frames = []
    for yr in YEARS:
        cls = xr.open_dataset(KD / f"landcover_{yr}.nc").cls.values
        fig = plt.figure(figsize=(10.8, 10.8), dpi=100)
        fig.patch.set_facecolor("#fbfaf7")
        ax = fig.add_axes([0.02, 0.17, 0.96, 0.66])
        ax.imshow(np.where(np.isfinite(hand), 1, np.nan), cmap="Greys", vmin=0, vmax=8, extent=ext)
        ax.imshow(np.where((hand < 3) & (cls >= 0), cls, np.nan).astype(float), cmap=cm, vmin=-0.5,
                  vmax=len(CLASSES) - 0.5, extent=ext, interpolation="nearest")
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        fig.text(0.03, 0.94, "What Kampala's valley floors became", fontsize=26, fontweight="bold", color="#16201c")
        fig.text(0.03, 0.895, "Ground less than 3 m above the drains, mapped by machine learning",
                 fontsize=15, color="#6f7a75")
        fig.text(0.97, 0.875, str(yr), fontsize=40, fontweight="bold", color="#16201c", ha="right", va="top")
        r = core.loc[yr]
        nat = r["wetland vegetation_ha"] + r["trees and shrubs_ha"]
        fig.text(0.03, 0.845, f"Natural vegetation {nat / 100:,.0f} km²   ·   built and bare {r['built and bare_ha'] / 100:,.0f} km²",
                 fontsize=16, color="#16201c", fontweight="bold")
        fig.legend(handles=[Patch(color=c, label=n) for c, n in zip(COLORS, CLASSES)], loc="lower left", ncol=3,
                   bbox_to_anchor=(0.02, 0.06), fontsize=13, frameon=False)
        fig.text(0.03, 0.025, "Data: NASA/USGS Landsat · labels: ESA WorldCover, Impact Observatory · terrain: Copernicus GLO-30",
                 fontsize=10.5, color="#6f7a75")
        fig.text(0.97, 0.025, "Credit: Gava Charles", fontsize=12, fontweight="bold", color="#16201c", ha="right", alpha=0.8)
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3]))
        if yr == 2025:
            fig.savefig(ROOT / "outreach" / "kampala_drainage" / "x9_valley_landcover_2025.png")
        plt.close(fig)
    out = ROOT / "outreach" / "kampala_drainage" / "gifs" / "kd_a11_valley_landcover_ml.gif"
    frames[0].save(out, save_all=True, append_images=frames[1:] + [frames[-1]] * 2, duration=1600, loop=0)
    print("gif", out)
