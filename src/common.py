"""Shared paths, loaders, Uganda mask, rainfall zones, indices and plotting style."""
from functools import lru_cache
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import LinearSegmentedColormap
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
PROC, FIG, RES = ROOT / "data" / "processed", ROOT / "figures", ROOT / "results"
FIG.mkdir(exist_ok=True)
RES.mkdir(exist_ok=True)
NE = Path.home() / "uganda-concrete-climate" / "data" / "raw" / "naturalearth"

Y0, Y1 = 1981, 2025          # complete years used for trends (45 years)
BASE = (1991, 2020)          # WMO climatological normal
EPOCHS = [(1981, 1995), (1996, 2010), (2011, 2025)]

TOWNS = {  # name: (lat, lon)
    "Kampala": (0.32, 32.58), "Entebbe": (0.05, 32.46), "Jinja": (0.44, 33.20), "Masaka": (-0.33, 31.73),
    "Mbarara": (-0.61, 30.65), "Kabale": (-1.25, 29.99), "Fort Portal": (0.67, 30.27), "Kasese": (0.18, 30.08),
    "Hoima": (1.43, 31.35), "Masindi": (1.68, 31.72), "Gulu": (2.78, 32.30), "Lira": (2.25, 32.90),
    "Arua": (3.02, 30.91), "Soroti": (1.71, 33.61), "Mbale": (1.08, 34.18), "Tororo": (0.69, 34.18),
    "Moroto": (2.53, 34.66), "Kotido": (3.01, 34.11),
}

# ---- style (validated reference palette, see dataviz skill) ----
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#fcfcfb"
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
RED = ["#fbd5cf", "#f4aa9f", "#ec7f70", "#e34948", "#c13332", "#982524", "#6e1a1a"]
ORANGE = ["#fbdccb", "#f6b896", "#f09462", "#eb6834", "#c9521f", "#9c3f17", "#6f2d10"]
MID = "#f0efec"
CMAP_TEMP = LinearSegmentedColormap.from_list("temp", BLUE[::-1][1:] + [MID] + RED[1:])
CMAP_RAIN = LinearSegmentedColormap.from_list("rain", ORANGE[::-1][1:] + [MID] + BLUE[1:])
CMAP_SEQ = LinearSegmentedColormap.from_list("seq", ["#f4f8fd"] + BLUE)

mpl.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "figure.dpi": 110,
    "savefig.dpi": 200, "savefig.bbox": "tight", "font.size": 9, "axes.titlesize": 10,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": GRID, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2,
    "legend.frameon": False, "axes.prop_cycle": mpl.cycler(color=CAT),
})


CREDIT = "Credit: Gava Charles"


def credit_strip(fig, source, credit=CREDIT):
    """Write the data/map sources (left) and the credit (right) just below the lowest content of the figure
    (savefig bbox 'tight' then includes them without leaving empty space)."""
    import textwrap
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    bbs = [a.get_tightbbox(r).transformed(inv) for a in fig.axes if a.get_visible()]
    bbs += [t.get_window_extent(r).transformed(inv) for t in fig.texts if t.get_text()]
    y0 = min(b.y0 for b in bbs)
    x0, x1 = min(b.x0 for b in bbs), max(b.x1 for b in bbs)
    w = fig.get_size_inches()[0] * (min(x1, 1.0) - max(x0, 0.0)) - 2.4  # leave room for the credit
    lines = textwrap.wrap(source, max(40, int(w * 13)))
    fig.text(max(x0, 0.0), y0 - 0.012, "\n".join(lines), fontsize=7.5, color="#555", va="top")
    fig.text(min(x1, 1.0), y0 - 0.012, credit, fontsize=10, fontweight="bold", color="#333", ha="right", va="top")

def save(fig, name, folder=None, source=None):
    folder = folder or FIG
    folder.mkdir(parents=True, exist_ok=True)
    if source:
        credit_strip(fig, source)
    fig.savefig(folder / name)
    plt.close(fig)
    print("figure", name)


# ---- geography ----
@lru_cache()
def countries():
    return gpd.read_file(NE / "ne_10m_admin_0_countries.geojson")


@lru_cache()
def lakes():
    return gpd.read_file(NE / "ne_10m_lakes.geojson")


@lru_cache()
def uganda():
    c = countries()
    return c[c.ADM0_A3 == "UGA"].geometry.union_all() if hasattr(c.geometry, "union_all") else \
        c[c.ADM0_A3 == "UGA"].geometry.unary_union


def grid_mask(lat, lon, geom=None, exclude_lakes=True):
    """Boolean (lat, lon) DataArray: cell centre inside Uganda (or `geom`) and not in a large lake."""
    import shapely
    geom = geom or uganda()
    shapely.prepare(geom)
    lo, la = np.meshgrid(np.asarray(lon, float), np.asarray(lat, float))
    m = shapely.contains_xy(geom, lo, la)
    if exclude_lakes:
        big = lakes()
        big = big[big.geometry.area > 0.05].geometry.unary_union
        shapely.prepare(big)
        m &= ~shapely.contains_xy(big, lo, la)
    return xr.DataArray(m, dims=("lat", "lon"), coords={"lat": lat, "lon": lon})


def draw_borders(ax, extent=None, lw=0.6, uganda_lw=1.0, lake_fill="#dfe9f3"):
    c = countries()
    c.boundary.plot(ax=ax, color=INK2, lw=lw, zorder=5)
    lakes()[lambda d: d.geometry.area > 0.05].plot(ax=ax, color=lake_fill, edgecolor=INK2, lw=0.3, zorder=4)
    gpd.GeoSeries([uganda()]).boundary.plot(ax=ax, color=INK, lw=uganda_lw, zorder=6)
    if extent:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
    ax.set_aspect("equal")
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


UG_EXTENT = (29.4, 35.1, -1.6, 4.35)


# ---- loaders ----
@lru_cache()
def chirps():
    ds = xr.open_dataset(PROC / "chirps_uganda_daily.nc")
    return ds["precip"].load(), ds["is_prelim"].load(), ds.attrs.get("last_final")


@lru_cache()
def ug_mask_chirps():
    pr = chirps()[0]
    f = PROC / "mask_chirps.nc"
    if f.exists():
        return xr.open_dataarray(f).load().astype(bool)
    m = grid_mask(pr.lat, pr.lon)
    m.astype("int8").to_netcdf(f)
    return m


@lru_cache()
def zones():
    """Rainfall-regime zones (from zones.py): integer DataArray on the CHIRPS grid, -1 outside Uganda."""
    return xr.open_dataarray(PROC / "zones.nc").load()


@lru_cache()
def zone_names():
    return pd.read_csv(RES / "zone_names.csv", index_col=0)["name"].to_dict()


def zone_mean(da, z=None):
    """Area mean by zone (cos-lat weighted) -> DataArray with a 'zone' dim, plus 'Uganda'."""
    z = zones() if z is None else z
    w = np.cos(np.deg2rad(da.lat)) * xr.ones_like(z)
    out = {}
    for k in sorted(int(v) for v in np.unique(z) if v >= 0):
        m = z == k
        out[zone_names()[k]] = da.where(m).weighted(w.where(m, 0)).mean(("lat", "lon"))
    m = z >= 0
    out["Uganda"] = da.where(m).weighted(w.where(m, 0)).mean(("lat", "lon"))
    return xr.concat(list(out.values()), pd.Index(list(out), name="zone"))


# ---- climate indices from ERSST v5 ----
@lru_cache()
def sst():
    s = xr.open_dataset(PROC / "ersst_monthly.nc")["sst"].load()
    return s


def sst_anom(base=BASE):
    s = sst()
    clim = s.sel(time=slice(f"{base[0]}", f"{base[1]}")).groupby("time.month").mean()
    return s.groupby("time.month") - clim


def box_mean(da, lat, lon):
    sub = da.sel(lat=slice(*lat), lon=slice(*lon))
    return sub.weighted(np.cos(np.deg2rad(sub.lat))).mean(("lat", "lon"))


@lru_cache()
def indices():
    """Monthly Nino3.4, relative Nino3.4 (minus tropical mean), DMI, west/east IO poles (ERSST v5, 1991-2020 base)."""
    a = sst_anom()
    n34 = box_mean(a, (-5, 5), (190, 240))
    trop = box_mean(a, (-20, 20), (0, 360))
    w = box_mean(a, (-10, 10), (50, 70))
    e = box_mean(a, (-10, 0), (90, 110))
    df = pd.DataFrame({"nino34": n34.values, "rnino34": (n34 - trop).values, "dmi": (w - e).values,
                       "wio": w.values, "eio": e.values, "trop": trop.values},
                      index=pd.DatetimeIndex(a.time.values, name="time"))
    return df


def oni():
    """NOAA CPC ONI (3-month running Nino3.4, ERSSTv5, centred base periods) indexed by centre month."""
    rows = []
    seas = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
    for line in (ROOT / "data" / "raw" / "oni.txt").read_text().splitlines()[1:]:
        p = line.split()
        if len(p) == 4:
            rows.append((pd.Timestamp(int(p[1]), seas.index(p[0]) + 1, 1), float(p[3])))
    return pd.Series(dict(rows), name="oni")


def enso_years(season_months=(10, 11, 12)):
    """El Nino / La Nina years from ONI averaged over season_months (>= +0.5 / <= -0.5)."""
    o = oni()
    o = o[o.index.month.isin(season_months)].groupby(o[o.index.month.isin(season_months)].index.year).mean()
    return o


# ---- trend statistics ----
def sen_mk(y, axis=0):
    """Sen's slope (per step) and two-sided Mann-Kendall p-value along `axis`, vectorised; NaN-safe per series."""
    from scipy.stats import norm
    y = np.moveaxis(np.asarray(y, float), axis, 0)
    n = y.shape[0]
    i, j = np.triu_indices(n, 1)
    d = y[j] - y[i]
    slopes = d / (j - i).reshape((-1,) + (1,) * (y.ndim - 1))
    slope = np.nanmedian(slopes, axis=0)
    s = np.nansum(np.sign(d), axis=0)
    nn = np.sum(np.isfinite(y), axis=0)
    var = nn * (nn - 1) * (2 * nn + 5) / 18.0
    z = np.where(s > 0, (s - 1) / np.sqrt(var), np.where(s < 0, (s + 1) / np.sqrt(var), 0))
    p = 2 * (1 - norm.cdf(np.abs(z)))
    return slope, p


def trend_da(da, dim="year"):
    """Sen slope per decade and MK p-value as DataArrays (dims of da minus `dim`)."""
    ax = da.dims.index(dim)
    s, p = sen_mk(da.values, ax)
    dims = [d for d in da.dims if d != dim]
    coords = {d: da[d] for d in dims}
    return xr.DataArray(s * 10, dims=dims, coords=coords), xr.DataArray(p, dims=dims, coords=coords)


def series_trend(y):
    """Modified MK (Hamed-Rao, autocorrelation-corrected) on a 1-D series: (slope/decade, p, intercept)."""
    import pymannkendall as mk
    y = np.asarray(y, float)
    r = mk.hamed_rao_modification_test(y[np.isfinite(y)])
    return r.slope * 10, r.p, r.intercept


SEASONS = {"MAM": (3, 4, 5), "JJA": (6, 7, 8), "SON": (9, 10, 11), "DJF": (12, 1, 2), "OND": (10, 11, 12)}


def season_total(da, months, how="sum"):
    """Seasonal aggregate per year from a daily/monthly series; DJF is assigned to the year of the January."""
    sel = da.where(da.time.dt.month.isin(months), drop=True)
    yr = sel.time.dt.year + ((sel.time.dt.month == 12) & (12 in months) & (1 in months))
    g = sel.groupby(yr.rename("year"))
    return g.sum("time", min_count=1) if how == "sum" else g.mean("time")


def stipple(ax, p, lon, lat, alpha=0.05, step=1, s=0.6):
    """Dots where the trend is significant."""
    lo, la = np.meshgrid(lon, lat)
    m = np.asarray(p) < alpha
    ax.scatter(lo[::step, ::step][m[::step, ::step]], la[::step, ::step][m[::step, ::step]], s=s, c=INK, lw=0, zorder=7)
