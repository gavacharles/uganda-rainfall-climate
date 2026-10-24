"""Flood x AMR paper 1, step 4: satellite check of the routed source load at the shore of Inner Murchison Bay.

If routed load means something physical, the lake water off the channel outlets that carry more of it should be
murkier relative to the open lake, and more so after rain.
  Outlets   land cells within 60 m of the bay's open water (kd_bay water mask) where D8 flow accumulation is at least
            0.25 km2; cells within 400 m are one outlet, located at its largest accumulation. Routed load: the largest
            weighted load (am_index weights) in the outlet.
  Water     every cached Sentinel-2 turbidity scene (kd_bay.scene_turb, Dogliotti et al. 2015; 36 scenes 2018-2026):
            median turbidity of open-water pixels within 400 m of the outlet, over the median of the open-lake
            reference zone (kd_bay zone 4) in the same scene; at least 20 valid pixels at the outlet.
  Rain      CHIRPS over Kampala in the 3 days before each scene (kd_bay.chirps_kla).
  Tests     (p-values by permutation of load among outlets, 2,000 times; naive OLS p shown for reference)
            Spearman rank correlation, across outlets, of mean log ratio with log routed load; mixed comparison
            within scenes: log ratio ~ log(1 + load) + scene fixed effects, and its interaction with wet scenes (>= 25 mm).
Outputs: results/am_satcheck_outlets.csv, results/am_satcheck_tests.csv, figures/kampala_amr/am07_satellite_check.png
"""
import glob

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from pyproj import Transformer
from scipy import ndimage, stats

import kd_bay as kb
from am_index import CLASSES, W0
from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"


def outlets():
    R = np.load(KD / "amr" / "am_rasters.npz")
    L = sum(W0[c] * R[c].astype("float64") for c in CLASSES)
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        acc, tr = r.read(3), r.transform
    m = kb.watermask()
    water = m.values.astype(bool)
    band = ndimage.binary_dilation(water, iterations=3) & ~water           # land within 60 m (20 m pixels)
    X, Y = np.meshgrid(m.x.values, m.y.values)
    lon, lat = Transformer.from_crs(32636, 4326, always_xy=True).transform(X[band], Y[band])
    col = ((lon - tr.c) / tr.a).astype(int); row = ((lat - tr.f) / tr.e).astype(int)
    a, l = acc[row, col], L[row, col]
    keep = a >= 0.25
    px, py, a, l = X[band][keep], Y[band][keep], a[keep], l[keep]
    order = np.argsort(-a)
    lab = -np.ones(len(a), int); k = 0
    for i in order:
        if lab[i] < 0:
            lab[(lab < 0) & (np.hypot(px - px[i], py - py[i]) < 400)] = k; k += 1
    rows = []
    for j in range(k):
        g = lab == j
        i = np.argmax(np.where(g, a, -1))
        rows.append(dict(outlet=j, x=px[i], y=py[i], up_km2=round(float(a[i]), 2), load=float(l[g].max())))
    o = pd.DataFrame(rows)
    ll = Transformer.from_crs(32636, 4326, always_xy=True).transform(o.x.values, o.y.values)
    o["lon"], o["lat"] = np.round(ll[0], 5), np.round(ll[1], 5)
    return o, m


def main():
    o, m = outlets()
    X, Y = np.meshgrid(m.x.values, m.y.values)
    water = m.values.astype(bool)
    zone = kb.zones(m.x.values, m.y.values, water)
    near = [water & (np.hypot(X - r.x, Y - r.y) <= 400) for r in o.itertuples()]
    ch = kb.chirps_kla()
    recs = []
    for f in sorted(glob.glob(str(KD / "bay_turb_*.nc"))):
        day = pd.Timestamp(f.split("bay_turb_")[1][:10])
        t = xr.open_dataarray(f).sel(x=m.x, y=m.y, method="nearest").values
        ref = np.nanmedian(np.where(zone == 4, t, np.nan))
        if not np.isfinite(ref) or np.isfinite(np.where(zone == 4, t, np.nan)).sum() < 200:
            continue
        r3 = float(ch[day - pd.Timedelta(days=3):day - pd.Timedelta(days=1)].sum())
        for j, nm in enumerate(near):
            v = t[nm]; v = v[np.isfinite(v)]
            if len(v) >= 20:
                recs.append(dict(date=day.date(), outlet=j, ratio=float(np.median(v) / ref), r3=r3))
    d = pd.DataFrame(recs).merge(o[["outlet", "load", "up_km2"]], on="outlet")
    d["lr"] = np.log(d.ratio)
    per = d.groupby("outlet").agg(scenes=("lr", "size"), mean_log_ratio=("lr", "mean"), wet_scenes=("r3", lambda v: int((v >= 25).sum()))).reset_index()
    o = o.merge(per, on="outlet", how="left")
    o["ratio"] = np.exp(o.mean_log_ratio).round(3)
    o.drop(columns=["x", "y"]).to_csv(RES / "am_satcheck_outlets.csv", index=False)
    use = o[o.scenes >= 5]
    rho, p = stats.spearmanr(np.log1p(use.load), use.mean_log_ratio)
    # within-scene comparison: demean by scene (fixed effects), then regress on log(1 + load), with wet interaction
    d = d[d.outlet.isin(use.outlet)].copy()
    d["x"] = np.log1p(d.load)
    d["lr_c"] = d.lr - d.groupby("date").lr.transform("mean")
    d["x_c"] = d.x - d.groupby("date").x.transform("mean")
    b = stats.linregress(d.x_c, d.lr_c)
    wet = d.r3 >= 25
    bw = stats.linregress(d.x_c[wet], d.lr_c[wet]) if wet.sum() > 10 else None
    bd = stats.linregress(d.x_c[~wet], d.lr_c[~wet])
    # permutation test: shuffle routed load among outlets (2,000 times), keeping each outlet's scenes together, so the
    # p-value respects that there are only as many independent units as outlets
    rng = np.random.default_rng(11)
    ids = use.outlet.values
    xl = dict(zip(use.outlet, np.log1p(use.load)))
    def slope(mask, mapping):
        dd = d[mask].copy(); dd["x"] = dd.outlet.map(mapping)
        xc = dd.x - dd.groupby("date").x.transform("mean"); yc = dd.lr - dd.groupby("date").lr.transform("mean")
        return float((xc * yc).sum() / (xc * xc).sum())
    obs = {k: slope(mk, xl) for k, mk in (("all", np.ones(len(d), bool)), ("wet", wet.values), ("dry", (~wet).values))}
    perm = {k: [] for k in obs}
    for _ in range(2000):
        sh = dict(zip(ids, rng.permutation([xl[i] for i in ids])))
        for k, mk in (("all", np.ones(len(d), bool)), ("wet", wet.values), ("dry", (~wet).values)):
            perm[k].append(slope(mk, sh))
    pp = {k: round(float((np.array(perm[k]) >= obs[k]).mean()), 4) for k in obs}
    T = pd.DataFrame([
        dict(test="outlets with >= 5 usable scenes", n=len(use), estimate=None, p=None),
        dict(test="permutation p (one-sided), within-scene slope, all scenes", n=len(use), estimate=round(obs["all"], 4), p=pp["all"]),
        dict(test="permutation p, dry scenes", n=len(use), estimate=round(obs["dry"], 4), p=pp["dry"]),
        dict(test="permutation p, wet scenes", n=len(use), estimate=round(obs["wet"], 4), p=pp["wet"]),
        dict(test="Spearman: outlet mean log ratio vs log routed load", n=len(use), estimate=round(rho, 3), p=round(p, 4)),
        dict(test="within-scene slope, log ratio per log(1+load), all scenes", n=len(d), estimate=round(b.slope, 4), p=round(b.pvalue, 4)),
        dict(test="same, dry scenes (< 25 mm in 3 days)", n=int((~wet).sum()), estimate=round(bd.slope, 4), p=round(bd.pvalue, 4)),
        dict(test="same, wet scenes (>= 25 mm in 3 days)", n=int(wet.sum()), estimate=None if bw is None else round(bw.slope, 4),
             p=None if bw is None else round(bw.pvalue, 4))])
    T["note"] = ["", "", "", "", "", "naive OLS p, outlet-days treated as independent", "naive", "naive"]
    T.to_csv(RES / "am_satcheck_tests.csv", index=False)
    print(o.drop(columns=["x", "y"]).to_string()); print(T.to_string(), flush=True)
    figure(o, use, rho, p, b, pp, d, wet)


def figure(o, use, rho, p, b, pp, d, wet):
    from matplotlib.colors import LogNorm
    fig, axs = plt.subplots(1, 2, figsize=(13.5, 6.4), gridspec_kw=dict(width_ratios=[1, 1]))
    fig.subplots_adjust(top=0.82, bottom=0.14, left=0.03, right=0.97, wspace=0.22)
    a = axs[0]
    wm = kb.watermask()
    base = np.where(wm.values.astype(bool)[..., None], np.array([0.80, 0.87, 0.93]), np.array([0.94, 0.935, 0.915]))
    a.imshow(base, extent=[float(wm.x.min()), float(wm.x.max()), float(wm.y.min()), float(wm.y.max())], origin="upper" if wm.y.values[0] > wm.y.values[-1] else "lower",
             interpolation="nearest")
    nrm = LogNorm(1e-2, max(o.load.max(), 1))
    sc = a.scatter(o.x, o.y, s=55, c=o.load.clip(1e-2), cmap="magma_r", norm=nrm, edgecolor="white", lw=1.1, zorder=5)
    for r in use.nlargest(5, "load").itertuples():
        a.annotate(f"{r.ratio:.2f}", (r.x, r.y), xytext=(7, 5), textcoords="offset points", fontsize=9.5, color="white",
                   bbox=dict(boxstyle="round,pad=0.15", fc="#000000b0", ec="none"), zorder=6)
    cb = fig.colorbar(sc, ax=a, shrink=0.7, pad=0.01); cb.set_label("Routed source load at the outlet (relative, log)")
    pad = 800
    a.set_xlim(o.x.min() - pad, o.x.max() + pad); a.set_ylim(o.y.min() - pad, o.y.max() + pad); a.set_aspect("equal")
    a.set_xticks([]); a.set_yticks([])
    a.set_title(f"a  {len(o)} channel outlets on Inner Murchison Bay\n    labels: nearshore turbidity / open lake, five largest loads", loc="left", fontsize=10.5)
    a2 = axs[1]
    dd = d.assign(w=np.where(wet, "wet", "dry"))
    dd["lr_c"] = dd.lr - dd.groupby("date").lr.transform("mean")                 # relative to the other outlets that day
    per = dd.groupby(["outlet", "w"]).lr_c.mean().unstack()
    xl = np.log10(use.set_index("outlet").load.clip(1e-4))
    for w_, col, lab in (("dry", "#9ecae1", f"dry spells (permutation p = {pp['dry']:.2f})"), ("wet", "#08519c", f"after ≥ 25 mm of rain in 3 days (p = {pp['wet']:.3f})")):
        y = (np.exp(per[w_].reindex(xl.index)) - 1) * 100
        a2.scatter(xl, y, s=34, color=col, edgecolor="white", lw=0.6, zorder=3, label=lab)
        k = np.isfinite(y)
        sl, ic = np.polyfit(xl[k], y[k], 1)
        xx = np.array([xl.min(), xl.max()]); a2.plot(xx, ic + sl * xx, color=col, lw=2.2, zorder=4)
    a2.axhline(0, color="#666", lw=0.8)
    a2.set_xticks([-4, -2, 0, 2]); a2.set_xticklabels(["≤ 0.0001", "0.01", "1", "100"])
    a2.set_xlabel("Routed source load at the outlet (relative, log scale)"); a2.set_ylabel("Nearshore turbidity vs other outlets the same day (%)")
    a2.legend(fontsize=9.5, loc="upper left")
    a2.set_title("b  After rain, outlets carrying more load are murkier than others the same day;\n"
                 f"    in dry spells the gradient is flat (all scenes: p = {pp['all']:.2f}; p by permutation of load among outlets)", loc="left", fontsize=10.5)
    fig.suptitle("A satellite check: is the water murkier where more load arrives?", x=0.01, ha="left", fontweight="bold", fontsize=14)
    save(fig, "am07_satellite_check.png", FIG / "kampala_amr",
         "Turbidity: Copernicus Sentinel-2 L2A, Dogliotti et al. (2015), 36 scenes 2018–2026 · rain: CHIRPS · routed load: this study "
         "(OpenStreetMap, GHS-POP, Copernicus GLO-30) · turbidity tracks sediment and runoff, not resistance itself")


if __name__ == "__main__":
    main()
