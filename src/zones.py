"""Objective rainfall-regime zones for Uganda from CHIRPS (1991-2020 climatology).

Each land cell is described by the shape of its mean annual cycle (36 dekads, as a share of the annual
total, smoothed) and its annual total. K-means groups cells with similar regimes; zone names are given
from the cluster geography. Outputs: data/processed/zones.nc, results/zone_names.csv, figures/fig01_zones.png
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from common import (BASE, CAT, INK2, PROC, RES, TOWNS, UG_EXTENT, chirps, draw_borders, save,
                    ug_mask_chirps)

K = 6


def features():
    pr = chirps()[0].sel(time=slice(f"{BASE[0]}", f"{BASE[1]}"))
    doy = pr.time.dt.dayofyear.clip(max=365)
    clim = pr.groupby(doy).mean()  # (365, lat, lon)
    sm = clim.pad(dayofyear=15, mode="wrap").rolling(dayofyear=31, center=True).mean().isel(dayofyear=slice(15, -15))
    dek = sm.coarsen(dayofyear=10, boundary="trim").mean()  # 36 "dekads"
    shape = dek / dek.sum("dayofyear")
    total = clim.sum("dayofyear")
    return shape, total, sm


def name_zone(lat, lon, total, bimodality):
    # named from the cluster centroid; boundaries checked visually against fig01
    if total < 950:
        return "Karamoja (NE, semi-arid)"
    if lat < 0:
        return "South-west (Ankole-Kigezi)"
    if lat < 0.9:
        return "Lake Victoria crescent (Central-Busoga)"
    if lat < 1.7:
        return "Mid-west & Kyoga (Bunyoro-Kyoga)"
    if lon > 32.8:
        return "North (Acholi-Kitgum)"
    return "West Nile-Lango-Teso-Elgon belt"


def main():
    mask = ug_mask_chirps()
    shape, total, sm = features()
    X = shape.stack(cell=("lat", "lon")).transpose("cell", "dayofyear")
    m = mask.stack(cell=("lat", "lon")).values
    T = total.stack(cell=("lat", "lon")).values
    F = np.column_stack([X.values[m] * 36, 0.6 * (np.log(T[m]) - np.log(T[m]).mean()) / np.log(T[m]).std()])
    for k in range(4, 10):
        lab = KMeans(k, n_init=50, random_state=0).fit_predict(F)
        print("k", k, "silhouette", round(silhouette_score(F, lab), 3))
    km = KMeans(K, n_init=100, random_state=0).fit(F)
    lab = np.full(m.shape, -1)
    lab[m] = km.labels_
    z = xr.DataArray(lab.reshape(mask.shape), dims=("lat", "lon"), coords=mask.coords)

    # name each cluster by its centroid; merge clusters with the same name
    names = {}
    lat2, lon2 = xr.broadcast(z.lat, z.lon)
    for k in range(K):
        sel = z == k
        names[k] = name_zone(float(lat2.where(sel).mean()), float(lon2.where(sel).mean()),
                             float(total.where(sel).mean()), None)
    uniq = list(dict.fromkeys(names[k] for k in sorted(names, key=lambda k: -float(lat2.where(z == k).mean()))))
    remap = {k: uniq.index(names[k]) for k in names}
    z = xr.where(z >= 0, xr.apply_ufunc(np.vectorize(lambda v: remap.get(int(v), -1)), z), -1)
    z.name = "zone"
    z.to_netcdf(PROC / "zones.nc")
    nm = pd.DataFrame({"name": uniq}, index=pd.RangeIndex(len(uniq), name="zone"))
    nm["cells"] = [int((z == i).sum()) for i in nm.index]
    nm["annual_mm_1991_2020"] = [float(total.where(z == i).mean()) for i in nm.index]
    nm.to_csv(RES / "zone_names.csv")
    print(nm)

    # figure: map + mean annual cycle per zone
    fig = plt.figure(figsize=(10, 4.6))
    ax = fig.add_axes([0.0, 0.05, 0.42, 0.88])
    cols = CAT[:len(uniq)]
    from matplotlib.colors import ListedColormap
    zz = z.where(z >= 0)
    ax.pcolormesh(z.lon, z.lat, zz, cmap=ListedColormap(cols), vmin=-0.5, vmax=len(uniq) - 0.5, shading="nearest")
    draw_borders(ax, UG_EXTENT)
    for t, (la, lo) in TOWNS.items():
        if t in ("Kampala", "Gulu", "Mbarara", "Arua", "Moroto", "Mbale", "Fort Portal", "Lira", "Kabale", "Hoima"):
            ax.plot(lo, la, "o", ms=3, color="#0b0b0b", zorder=7)
            ax.annotate(t, (lo, la), xytext=(3, 2), textcoords="offset points", fontsize=7, zorder=7)
    ax.set_title("a  Rainfall-regime zones (CHIRPS, 1991-2020)")
    ax2 = fig.add_axes([0.5, 0.12, 0.48, 0.78])
    days = np.arange(1, 366)
    for i, n in enumerate(uniq):
        y = sm.where(z == i).mean(("lat", "lon"))
        ax2.plot(days, y, color=cols[i], lw=1.8, label=f"{n} ({nm.annual_mm_1991_2020[i]:.0f} mm/yr)")
    ax2.set_xticks([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335])
    ax2.set_xticklabels(list("JFMAMJJASOND"))
    ax2.set_ylabel("mm/day (31-day mean)")
    ax2.set_xlim(1, 365)
    ax2.set_ylim(0)
    ax2.legend(fontsize=7, loc="upper left", ncol=1)
    ax2.set_title("b  Mean annual cycle of rainfall by zone")
    save(fig, "fig01_zones.png")


if __name__ == "__main__":
    main()
