"""Flood x AMR paper 1, figures for the additions: am08 real floods, am09 who is exposed, am10 the wetland filter,
am11 the drinking-water intake. Reads only results tables (light on memory)."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIG, RES, save

OUT = FIG / "kampala_amr"
SRC = "Exposure: Kampala drainage screening model (indicative) · population: JRC GHS-POP 2020"


def am08():
    e = pd.read_csv(RES / "am_events.csv")
    e = e[e.hours_with_data >= 30].sort_values("date")
    p = pd.read_csv(RES / "am_event_places.csv")
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.6), gridspec_kw=dict(width_ratios=[1.5, 1]))
    fig.subplots_adjust(top=0.8, bottom=0.2, left=0.07, right=0.98, wspace=0.28)
    for x in axs:
        x.set_axisbelow(True); x.grid(axis="x", visible=False)
    a = axs[0]
    lab = pd.to_datetime(e.date).dt.strftime("%d %b %Y")
    a.bar(lab, e.person_hours / 1000, color=np.where(e.grade == "A", "#b2182b", "#ef8a62"))
    a.set_ylabel("Person-hours in floodwater (thousands)")
    a.tick_params(axis="x", rotation=60, labelsize=9.5)
    a.set_title("a  Each catalogued flood, replayed with hourly satellite rain", loc="left", fontsize=11.5)
    for i, (v, r) in enumerate(zip(e.person_hours, e.rain_42h_mm)):
        a.text(i, v / 1000 + 4, f"{r:.0f} mm", ha="center", fontsize=8, color="#555", rotation=90, va="bottom")
    a.set_ylim(0, e.person_hours.max() / 1000 * 1.3)
    a.text(0.01, 0.97, "dark: grade A record; light: grade B · label: city-average rain over 42 h", transform=a.transAxes, fontsize=9, va="top", color="#555")
    b = axs[1]
    g = p.merge(e[["event", "person_hours"]], on="event")
    g["flooded"] = g.person_hours > 0
    hit = g.groupby("flooded").modelled_water_within_500m.agg(["mean", "size"])
    xs = ["events the model floods", "events it leaves dry"]
    vals = [hit.loc[True, "mean"] * 100 if True in hit.index else 0, hit.loc[False, "mean"] * 100 if False in hit.index else 0]
    ns = [int(hit.loc[k, "size"]) if k in hit.index else 0 for k in (True, False)]
    b.bar(xs, vals, color=["#2166ac", "#bbbbbb"])
    for i, (v, n) in enumerate(zip(vals, ns)):
        b.text(i, v + 2, f"{v:.0f}% of {n}", ha="center", fontsize=10.5, fontweight="bold")
    b.set_ylim(0, 110); b.set_ylabel("Reported places with modelled water within 500 m (%)")
    b.set_title("b  Do reported places get water in the model?", loc="left", fontsize=11.5)
    fig.suptitle("Real floods, not only design storms", x=0.01, ha="left", fontweight="bold", fontsize=14)
    save(fig, "am08_real_floods.png", OUT, "Rain: PERSIANN-CCS hourly (CHRS, UC Irvine), x1.5 · reports: Kampala flood catalogue · " + SRC)


def am09():
    q = pd.read_csv(RES / "am_who_quintiles.csv")
    fig, ax = plt.subplots(figsize=(10, 5.4)); fig.subplots_adjust(top=0.8, bottom=0.14, left=0.09, right=0.98)
    x = np.arange(len(q)); w = 0.38
    ax.bar(x - w / 2, q.share_people * 100, w, color="#4393c3", label="people in floodwater")
    ax.bar(x + w / 2, q.share_amr_exposure * 100, w, color="#b2182b", label="resistance-weighted exposure")
    ax.axhline(20, color="#888", ls=":", lw=1); ax.text(len(q) - 0.5, 20.6, "equal share", ha="right", fontsize=9, color="#666")
    ax.set_xticks(x); ax.set_xticklabels([f"{a}\n(RWI {r:.2f})" for a, r in zip(q.rwi_q, q.rwi)])
    ax.set_ylabel("Share of exposure (%)"); ax.legend(fontsize=10, loc="upper left")
    ax.set_title("Exposed stretches by wealth quintile of their neighbourhood (Kampala-relative)", loc="left", fontsize=11.5)
    fig.suptitle("Who is exposed? Not clearly the poorest, at 2.4 km", x=0.01, ha="left", fontweight="bold", fontsize=14)
    save(fig, "am09_who_is_exposed.png", OUT, "Wealth: Relative Wealth Index (Meta, Chi et al. 2022), ~2.4 km tiles · " + SRC)


def am10():
    w = pd.read_csv(RES / "am_wetland_path.csv")
    w = w[w.load > 0]
    rows = []
    for sysn, g in w.groupby("system"):
        if len(g) < 20:
            continue
        rows.append((sysn if sysn != "other / outside city catchments" else "Mayanja and outside",
                     np.average(g.wet_km_1986, weights=g.load), np.average(g.wet_km_2025, weights=g.load)))
    r = pd.DataFrame(rows, columns=["system", "y1986", "y2025"]).sort_values("y1986")
    fig, ax = plt.subplots(figsize=(10, 5.4)); fig.subplots_adjust(top=0.8, bottom=0.12, left=0.22, right=0.97)
    y = np.arange(len(r))
    ax.hlines(y, r.y2025, r.y1986, color="#999", lw=2)
    ax.scatter(r.y1986, y, s=70, color="#1a9850", zorder=3, label="1986")
    ax.scatter(r.y2025, y, s=70, color="#d73027", zorder=3, label="2025")
    for yy, a_, b_ in zip(y, r.y1986, r.y2025):
        ax.text(max(a_, b_) + 0.25, yy, f"−{100 * (a_ - b_) / a_:.0f}%", va="center", fontsize=10)
    ax.set_yticks(y); ax.set_yticklabels(r.system); ax.set_xlabel("Vegetated valley floor on the downstream path (km, load-weighted)")
    ax.legend(fontsize=10, loc="lower right")
    ax.set_title("How much wetland the routed load passes through before leaving the city", loc="left", fontsize=11.5)
    fig.suptitle("The wetland filter is shrinking", x=0.01, ha="left", fontweight="bold", fontsize=14)
    save(fig, "am10_wetland_filter.png", OUT, "Vegetated valley floor: Landsat dry-season NDVI > 0.45 and HAND < 3 m (paper 2) · flow paths: Copernicus GLO-30 D8")


def am11():
    q = pd.read_csv(RES / "am_intake.csv")
    fig, axs = plt.subplots(1, 2, figsize=(13, 5.2)); fig.subplots_adjust(top=0.8, bottom=0.14, left=0.07, right=0.98, wspace=0.28)
    a = axs[0]
    a.scatter(q.outlets_ratio, q.intake_ratio, s=40, c=np.where(q.r3 >= 25, "#08519c", "#9ecae1"), edgecolor="white")
    k = np.polyfit(q.outlets_ratio, q.intake_ratio, 1); xx = np.linspace(q.outlets_ratio.min(), q.outlets_ratio.max(), 2)
    a.plot(xx, np.polyval(k, xx), color="#b2182b", lw=2)
    a.set_xlabel("Five highest-load outlets: turbidity / open lake"); a.set_ylabel("Within 1 km of the Ggaba intake: turbidity / open lake")
    a.set_title("a  The intake water moves with the outlet plume (ρ = 0.56)", loc="left", fontsize=11.5)
    b = axs[1]
    b.scatter(q.r3, q.intake_ratio, s=40, color="#4d4d4d", edgecolor="white")
    b.axhline(1, color="#888", ls=":"); b.set_xlabel("Rain over Kampala in the 3 days before (mm)"); b.set_ylabel("Intake turbidity / open lake")
    b.set_title("b  but not with rain on the same few days (ρ = −0.02)", loc="left", fontsize=11.5)
    fig.suptitle("The drinking-water intake sits in the outlets' water", x=0.01, ha="left", fontweight="bold", fontsize=14)
    save(fig, "am11_intake.png", OUT, "Turbidity: Copernicus Sentinel-2, Dogliotti et al. (2015), 35 scenes · intake: Ggaba waterworks (OpenStreetMap) · rain: CHIRPS")


if __name__ == "__main__":
    am08(); am09(); am10(); am11()
