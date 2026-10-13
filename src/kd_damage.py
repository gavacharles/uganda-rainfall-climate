"""Paper 4: the cost of a flood, channel by channel - expected annual damage (EAD) to buildings in Greater Kampala.

Hazard: overbank stage above the bank top for the 2-, 5-, 10-, 25-, 50- and 100-year storms per channel stretch
(kd_hydraulics.py: rational-method peaks, channels sized for the 1990 10-year flow, HAND synthetic rating curve).
Each building (Microsoft footprints) within 200 m of a stretch is assigned to its nearest stretch; flood depth =
stage_T - HAND_building (when positive). Two capacity states: clean channel, and 30% silted (damages recomputed with
the silted capacity: the stage rises by the extra flow over the floodplain rating curve).
Vulnerability: JRC global depth-damage curve for residential buildings, Africa (Huizinga et al. 2017):
depth m 0, 0.5, 1, 1.5, 2, 3, 4, 5, 6 -> damage 0, 0.22, 0.38, 0.53, 0.64, 0.82, 0.90, 0.96, 1.0.
Exposed value: structure + contents per m2 of footprint, US$ 150 (central; sensitivity 75 and 300), a screening value for
Kampala's mostly single-storey, low-cost building stock.
EAD: trapezoidal integration of damage over annual exceedance probability (1/T), with zero damage at T = 1.
Maintenance value: EAD(silted) - EAD(clean) = the annual damage avoided by keeping channels desilted.
Justified investment (break-even): present value of 30 years of avoided EAD at 10% (factor 9.43).
Outputs: results/kd_damage_*.csv, figures kd39-kd40.
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import shapely

from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"
TS = [2, 5, 10, 25, 50, 100]
DEPTH = np.array([0, 0.5, 1, 1.5, 2, 3, 4, 5, 6])
FRAC = np.array([0, 0.22, 0.38, 0.53, 0.64, 0.82, 0.90, 0.96, 1.0])
VALUE = {"low": 75.0, "central": 150.0, "high": 300.0}  # US$ per m2 footprint (structure + contents)
PV30 = sum(1 / 1.1 ** t for t in range(1, 31))
SYSTEMS = ["Lubigi", "Nakivubo", "Kinawataka", "Kansanga", "Nalukolongo", "Walufumbe"]
SRC = ("Buildings: Microsoft Global ML Building Footprints · depth-damage: JRC global curves, Africa residential "
       "(Huizinga et al. 2017) · design storms: gauge-corrected CHIRPS IDF (this study) · terrain: Copernicus GLO-30 DEM · "
       "channels: © OpenStreetMap contributors")


def silted_stages(h, s):
    """Stage above bank for each T when the channel is 30% silted: the extra flow (Qcap_clean - Qcap_silted) must also
    pass over the floodplain. Approximated by shifting each storm to the flow that exceeds silted capacity."""
    import kd_hydraulics as kh  # reuse the rating-curve construction
    return None


def ead(damages):
    p = np.array([1.0] + [1 / T for T in TS])
    d = np.vstack([np.zeros(damages.shape[0])] + [damages[:, i] for i in range(len(TS))]).T
    return -np.trapz(d, p, axis=1)


def main():
    h = pd.read_parquet(KD / "hydraulics.parquet")
    s = gpd.read_file(KD / "segments.gpkg").merge(h, on="seg_id")
    su = s.to_crs(32636)
    b = gpd.read_parquet(KD / "ms_buildings.parquet").cx[32.45:32.72, 0.20:0.42]
    bu = b.to_crs(32636)
    area = bu.area.values
    cen = bu.geometry.centroid.values
    tree = shapely.STRtree(su.geometry.values)
    bi, si = tree.query(cen, predicate="dwithin", distance=200)
    dd = shapely.distance(cen[bi], su.geometry.values[si])
    pair = pd.DataFrame({"b": bi, "s": si, "d": dd}).sort_values("d").drop_duplicates("b")
    c4 = b.geometry.centroid
    with rasterio.open(PROC / "kampala_catchments.tif") as r:
        hand = r.read(2)
        tr = r.transform
    lon, lat = c4.x.values[pair.b.values], c4.y.values[pair.b.values]
    col = ((lon - tr.c) / tr.a).astype(int).clip(0, hand.shape[1] - 1)
    row = ((lat - tr.f) / tr.e).astype(int).clip(0, hand.shape[0] - 1)
    pair["hand"] = hand[row, col]
    pair["area"] = area[pair.b.values]
    D = su.D_design.values[pair.s.values]
    # clean-channel damages: water surface stands D + overbank stage above the bed (HAND measured from the drain cell)
    dmg = {}
    for state in ("clean", "silted"):
        out = np.zeros((len(pair), len(TS)))
        for i, T in enumerate(TS):
            stage = su[f"overbank_h{T}"].values[pair.s.values]
            if state == "silted":
                # silted: channel conveys only Qcap_silted, so the floodplain must carry the extra flow; approximate the
                # extra stage with the floodplain slope of the rating curve between the 10- and 100-yr points
                qc, qs = su.Qcap_clean.values[pair.s.values], su.Qcap_silted.values[pair.s.values]
                q10, q100 = su.Q10.values[pair.s.values], su.Q100.values[pair.s.values]
                h10, h100 = su.overbank_h10.values[pair.s.values], su.overbank_h100.values[pair.s.values]
                dhdq = np.where(q100 > q10, (h100 - h10) / np.maximum(q100 - q10, 1e-6), 0.01)
                qT = su[f"Q{T}"].values[pair.s.values]
                stage = np.where(qT > qs, np.maximum(stage, 0) + (qc - qs) * np.clip(dhdq, 0.002, 0.05), 0)
            depth = np.clip(stage + D - pair.hand.values - D, 0, None)  # depth above ground = stage above bank - HAND above bank level
            depth = np.where(stage > 0, depth, 0)
            out[:, i] = np.interp(depth, DEPTH, FRAC) * pair.area.values
        dmg[state] = out
    pair["seg"] = su.seg_id.values[pair.s.values]
    pair["system"] = su.system.values[pair.s.values]
    pair["name"] = su["name"].values[pair.s.values]
    for state in ("clean", "silted"):
        pair[f"ead_m2_{state}"] = ead(dmg[state])  # damage-equivalent m2 per year
        for i, T in enumerate(TS):
            pair[f"d{T}_{state}"] = dmg[state][:, i]
    flooded10 = (dmg["clean"][:, TS.index(10)] > 0)
    rows = []
    for k, v in VALUE.items():
        rows.append(dict(value_case=k, usd_per_m2=v,
                         ead_clean_musd=pair.ead_m2_clean.sum() * v / 1e6, ead_silted_musd=pair.ead_m2_silted.sum() * v / 1e6,
                         d10_clean_musd=pair.d10_clean.sum() * v / 1e6, d100_clean_musd=pair.d100_clean.sum() * v / 1e6,
                         maintenance_value_musd_per_yr=(pair.ead_m2_silted - pair.ead_m2_clean).sum() * v / 1e6,
                         pv30_maintenance_musd=(pair.ead_m2_silted - pair.ead_m2_clean).sum() * v / 1e6 * PV30))
    tot = pd.DataFrame(rows)
    tot.round(2).to_csv(RES / "kd_damage_totals.csv", index=False)
    print(tot.round(2).to_string())
    print("buildings within 200 m:", len(pair), "| flooded in 10-yr (clean):", int(flooded10.sum()))
    v = VALUE["central"]
    seg = pair.groupby("seg").agg(system=("system", "first"), name=("name", "first"), buildings=("b", "size"),
                                  ead_clean=("ead_m2_clean", "sum"), ead_silted=("ead_m2_silted", "sum"))
    seg = seg.join(su.set_index("seg_id")[["length_m", "up_km2"]])
    seg["ead_clean_usd"] = seg.ead_clean * v
    seg["ead_silted_usd"] = seg.ead_silted * v
    seg["avoided_usd_per_yr"] = seg.ead_silted_usd - seg.ead_clean_usd
    seg["breakeven_maint_usd_per_km_yr"] = seg.avoided_usd_per_yr / (seg.length_m / 1000)
    seg.round(1).to_csv(RES / "kd_damage_by_segment.csv")
    sysd = seg.groupby("system").agg(km=("length_m", lambda x: x.sum() / 1000), ead_clean_musd=("ead_clean_usd", lambda x: x.sum() / 1e6),
                                     ead_silted_musd=("ead_silted_usd", lambda x: x.sum() / 1e6),
                                     avoided_musd=("avoided_usd_per_yr", lambda x: x.sum() / 1e6))
    sysd["avoided_usd_per_km"] = sysd.avoided_musd * 1e6 / sysd.km
    sysd.round(3).to_csv(RES / "kd_damage_by_system.csv")
    print(sysd.round(3).to_string())
    import json
    nm = {f["i"]: f["nm"] for f in json.load(open(ROOT / "tool" / "segments.json"))}
    seg["drain"] = seg.index.map(nm)
    long_ = seg[(seg.length_m >= 150) & (seg.up_km2 >= 1)]
    bych = long_.groupby("drain").agg(system=("system", "first"), km=("length_m", lambda x: x.sum() / 1000),
                                      buildings=("buildings", "sum"), avoided_usd=("avoided_usd_per_yr", "sum"),
                                      ead_clean_usd=("ead_clean_usd", "sum"))
    bych["avoided_usd_per_km"] = bych.avoided_usd / bych.km
    bych = bych[bych.km >= 0.5].sort_values("avoided_usd", ascending=False)
    bych.round(0).to_csv(RES / "kd_damage_top_channels.csv")
    top = bych.head(15)
    print(top.round(0).to_string())
    figures(seg, sysd, tot, pair, dmg)


def figures(seg, sysd, tot, pair, dmg):
    v = VALUE["central"]
    fig, axs = plt.subplots(1, 2, figsize=(14.5, 5), gridspec_kw=dict(wspace=0.4))
    ax = axs[0]
    d_c = [dmg["clean"][:, i].sum() * v / 1e6 for i in range(len(TS))]
    d_s = [dmg["silted"][:, i].sum() * v / 1e6 for i in range(len(TS))]
    ax.plot(TS, d_c, "o-", color="#3182bd", lw=2.4, label="channels clean")
    ax.plot(TS, d_s, "o-", color="#a63603", lw=2.4, label="channels 30% silted")
    ax.fill_between(TS, d_c, d_s, color="#fdae6b", alpha=0.35)
    ax.set_xscale("log")
    ax.set_xticks(TS)
    ax.set_xticklabels([f"{T}-yr" for T in TS])
    ax.set_ylabel("building damage per event (US\\$ million)")
    c = tot.set_index("value_case").loc["central"]
    ax.set_title(f"a  Damage per storm, and what maintenance avoids\nExpected annual damage: US\\${c.ead_clean_musd:.1f}m clean vs US\\${c.ead_silted_musd:.1f}m silted",
                 loc="left", fontsize=11)
    ax.legend(fontsize=9)
    ax = axs[1]
    t = sysd.reindex(SYSTEMS).sort_values("avoided_usd_per_km")
    ax.barh(t.index, t.avoided_usd_per_km / 1000, color="#a63603")
    for i, val in enumerate(t.avoided_usd_per_km / 1000):
        ax.text(val * 1.02, i, f"{val:,.0f}k", va="center", fontsize=9)
    ax.set_xlim(0, (t.avoided_usd_per_km / 1000).max() * 1.22)
    ax.set_xlabel("damage avoided by desilting, US\\$ thousand per km of channel per year")
    ax.set_title("b  Where keeping channels clean pays most", loc="left", fontsize=11)
    save(fig, "kd39_flood_damage.png", OUT, source=SRC + " · exposed value US\\$150/m² (screening)")


if __name__ == "__main__":
    main()
