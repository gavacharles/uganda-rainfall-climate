"""Shared screening hydraulics for Papers 4 and 6 (Kampala channel stretches draining >= 0.25 km2).

Design flow (rational method):  Q_T = 0.278 * C * i_T(tc) * A * ARF     [m3/s; i in mm/h, A in km2]
  C = 0.25 + 0.65 x upstream impervious share (2020, GHSL calibrated; Paper A)
  tc (min) = Kirpich, flow length L = 1.4 A^0.6 km (Hack), slope from DEM; minimum 10 min
  i_T(tc): gauge-corrected CHIRPS IDF for Kampala (results/drainage_idf_kampala.csv), log-log interpolation
  ARF (areal reduction) = 1 - 0.04 * A^0.5 (A km2), floor 0.7
Channel (bankfull) geometry, regime estimate for urban channels in the absence of surveyed sections:
  width W = 1.0 + 1.2 A^0.5 m,  depth D = min(0.5 + 0.30 A^0.4, 3.0) m,  rectangular, Manning n = 0.025 (lined/maintained)
  Sensitivity: geometry x0.7 and x1.3; n = 0.035 (silted, vegetated)
Bankfull capacity: Manning, rectangular W x D, bed slope S (DEM, along the stretch, floor 0.001)
Overbank stage (HAND synthetic rating curve, Zheng et al. 2018): for each stretch, the 30 m cells within 200 m with
  HAND < 6 m define width(h) = n_cells(HAND < h) x 900 / L; flow above the banks adds a wide floodplain section with
  n = 0.06. Stage h_T solves Q(h) = Q_T. Flood depth at a building = h_T - D - HAND_building (when h_T > D).
Outputs: data/kd/hydraulics.parquet (per stretch), results/kd_hyd_summary.csv
"""
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
import xarray as xr

from common import PROC, RES, ROOT

KD = ROOT / "data" / "kd"
BOX = (32.45, 0.20, 32.72, 0.42)
TS = [2, 5, 10, 25, 50, 100]


def idf_intensity(col="intensity_mm_h"):
    t = pd.read_csv(RES / "drainage_idf_kampala.csv")

    def f(T, tc_min):
        g = t[t["T"] == T].sort_values("duration_min")
        x = np.log(g.duration_min.values)
        y = np.log(g[col].values)
        return np.exp(np.interp(np.log(np.clip(tc_min, g.duration_min.min(), g.duration_min.max())), x, y))
    return f


def geometry(A, scale=1.0):
    W = (1.0 + 1.2 * np.sqrt(A)) * scale
    D = np.minimum(0.5 + 0.30 * A ** 0.4, 3.0) * scale
    return W, D


def manning_rect(W, y, S, n):
    Ar = W * y
    R = Ar / (W + 2 * y)
    return Ar * R ** (2 / 3) * np.sqrt(S) / n


def main():
    s = gpd.read_file(KD / "segments.gpkg")
    s = s[s.up_km2 >= 0.25].reset_index(drop=True)
    su = s.to_crs(32636)
    with rasterio.open(PROC / "kampala_dem.tif") as r:
        dem = r.read(1)
        trd = r.transform
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand = r.read(2)
        trh = r.transform
    # slope along each stretch from DEM at its ends (smoothed by stretch length)
    ends = [(g.coords[0], g.coords[-1]) for g in s.geometry]
    z = lambda lo, la: dem[int((la - trd.f) / trd.e), int((lo - trd.c) / trd.a)]
    dz = np.array([abs(float(z(*a) - z(*b))) for a, b in ends])
    S = np.clip(dz / np.maximum(su.length.values, 30), 0.001, 0.08)
    A = s.up_km2.values
    imp = np.clip(2.27 * s.up_built_2020.values, 0, 0.95)
    C = 0.25 + 0.65 * imp
    L_km = 1.4 * A ** 0.6
    Sc = np.clip(S, 0.002, 0.08)
    tc = np.maximum(0.0195 * (L_km * 1000) ** 0.77 * Sc ** -0.385, 10)
    ARF = np.clip(1 - 0.04 * np.sqrt(A), 0.7, 1)
    fi = idf_intensity()
    out = pd.DataFrame({"seg_id": s.seg_id, "A_km2": A, "S": S, "C": C, "tc_min": tc})
    pav = pd.read_csv(RES / "kd_segment_upstream_paving.csv").set_index("seg_id")
    imp_of = lambda col: np.clip(2.27 * s.seg_id.map(pav[col]).fillna(0).values, 0, 0.95)
    C1990 = 0.25 + 0.65 * imp_of("up_built_1995") * 0 + 0.65 * np.clip(2.27 * s.up_built_1990.values, 0, 0.95)
    C2030 = 0.25 + 0.65 * imp_of("up_built_2030")
    fi, f245, f585 = idf_intensity(), idf_intensity("intensity_ssp245_2041_2070"), idf_intensity("intensity_ssp585_2041_2070")
    for T in TS:
        out[f"Q{T}"] = 0.278 * C * fi(T, tc) * A * ARF                # today: 2020 land, current climate
    out["Qdesign"] = 0.278 * C1990 * fi(10, tc) * A * ARF            # 10-yr flow under 1990 land cover
    out["Q10_2030land"] = 0.278 * C2030 * fi(10, tc) * A * ARF
    out["Q10_2050_ssp245"] = 0.278 * C2030 * f245(10, tc) * A * ARF
    out["Q10_2050_ssp585"] = 0.278 * C2030 * f585(10, tc) * A * ARF
    # channel sized to carry Qdesign at bankfull: rectangular, width = 3 x depth, n = 0.025
    Dd = np.zeros(len(s))
    for k in range(len(s)):
        lo, hi = 0.1, 8.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if manning_rect(3 * mid, mid, S[k], 0.025) < out.at[k, "Qdesign"]:
                lo = mid
            else:
                hi = mid
        Dd[k] = hi
    out["D_design"], out["W_design"] = Dd, 3 * Dd
    out["Qcap_clean"] = out.Qdesign
    out["Qcap_silted"] = manning_rect(3 * Dd, 0.7 * Dd, S, 0.035)      # 30% depth lost to silt + vegetation
    for tag, q in (("2020", out.Q10), ("2030land", out.Q10_2030land), ("2050_245", out.Q10_2050_ssp245),
                   ("2050_585", out.Q10_2050_ssp585)):
        out[f"ratio_{tag}"] = q / out.Qcap_clean
    out["ratio_2020_silted"] = out.Q10 / out.Qcap_silted
    # return period the channel can still carry today (clean and silted)
    for tag in ("clean", "silted"):
        out[f"capT_{tag}"] = np.select([out[f"Qcap_{tag}"] >= out[f"Q{T}"] for T in TS[::-1]], TS[::-1], 1)
    # floodplain HAND samples within 200 m of each stretch
    H, Wd = hand.shape
    rows, cols = np.nonzero((hand < 6) & np.isfinite(hand))
    lon = trh.c + trh.a * (cols + 0.5)
    lat = trh.f + trh.e * (rows + 0.5)
    keep = (lon > BOX[0]) & (lon < BOX[2]) & (lat > BOX[1]) & (lat < BOX[3])
    lon, lat, hv = lon[keep], lat[keep], hand[rows[keep], cols[keep]]
    pts = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs=4326).to_crs(32636).values
    tree = shapely.STRtree(su.geometry.values)
    pi, si = tree.query(pts, predicate="dwithin", distance=200)
    # each cell to its nearest stretch only
    d = shapely.distance(pts[pi], su.geometry.values[si])
    cell = pd.DataFrame({"p": pi, "s": si, "d": d}).sort_values("d").drop_duplicates("p")
    cell["h"] = hv[cell.p.values]
    groups = {k: g.h.values for k, g in cell.groupby("s")}
    Lseg = su.length.values
    hgrid = np.arange(0.05, 6.01, 0.05)
    res = {f"h{T}": np.full(len(s), np.nan) for T in TS}
    capr = {}
    W, D, Qcap = out.W_design.values, out.D_design.values, out.Qcap_clean.values
    for k in range(len(s)):
        hv_k = groups.get(k, np.array([]))
        wfp = np.array([(hv_k < h).sum() * 900.0 / max(Lseg[k], 30) for h in hgrid])
        wfp = np.maximum(wfp, W[k])
        area_fp = np.cumsum(wfp * 0.05)
        Rfp = area_fp / wfp
        Qtot = Qcap[k] + area_fp * Rfp ** (2 / 3) * np.sqrt(S[k]) / 0.06
        for T in TS:
            q = out.at[k, f"Q{T}"]
            res[f"h{T}"][k] = 0.0 if q <= Qcap[k] else hgrid[min(np.searchsorted(Qtot, q), len(hgrid) - 1)]
    for T in TS:
        out[f"overbank_h{T}"] = res[f"h{T}"]  # stage above bank top (m)
    out.to_parquet(KD / "hydraulics.parquet")
    summ = pd.DataFrame([dict(scenario=k_, median_ratio=float(out[c_].median()), share_over_1_2=100 * float((out[c_] > 1.2).mean()),
                              share_over_1_5=100 * float((out[c_] > 1.5).mean()))
                         for k_, c_ in (("2020 land, today's climate", "ratio_2020"), ("2020, channel silted 30%", "ratio_2020_silted"),
                                        ("2030 land", "ratio_2030land"), ("2030 land + 2041-70 SSP2-4.5", "ratio_2050_245"),
                                        ("2030 land + 2041-70 SSP5-8.5", "ratio_2050_585"))])
    summ.round(2).to_csv(RES / "kd_hyd_summary.csv", index=False)
    print(summ.round(2).to_string())
    print(out[["capT_clean", "capT_silted"]].apply(lambda c: c.value_counts(normalize=True).round(3)).to_string())
    print(out[["Q10", "Qdesign", "D_design", "overbank_h10", "overbank_h100"]].describe().round(2).to_string())


if __name__ == "__main__":
    main()
