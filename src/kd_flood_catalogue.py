"""Kampala flood catalogue 2007-2026 (data paper D0): merge GDELT multi-outlet events with manually verified reports.

Quality grades
  A  exact date, reported by >= 2 independent outlets (GDELT multi-outlet or several verified reports)
  B  exact date, one verified report
  C  month known only (report undated or describes "this week")
Locations: every named place geocoded from data/kd/flood_hotspots.csv (curated, +-500 m) or the OSM places layer.
Rain on the day: CHIRPS Greater-Kampala mean (1-day, 3-day) and NASA POWER peak-hour rain where available.
Outputs: results/kampala_flood_catalogue_2007_2026.csv, results/kampala_flood_catalogue_places.csv, figure kd41.
"""
import re

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from common import FIG, PROC, RES, ROOT, save

KD = ROOT / "data" / "kd"
OUT = FIG / "kampala_drainage"

MANUAL_EXTRA = [  # verified earlier events (web searches, Oct 2026); month-only ones get day 15 and grade C
    ("2007-11-16", "B", "Entebbe Road at Namasuba flooded after heavy rain", "Namasuba", "", "Getty Images caption, 16 Nov 2007"),
    ("2010-02-15", "C", "Second flood in a week; 8-hour downpour; Bwaise, Kalerwe, Kireka, Katwe, Ndeeba; child drowned in Bwaise the week before",
     "Bwaise; Kalerwe; Kireka; Katwe; Ndeeba", "1", "New Vision via ReliefWeb (Feb 2010)"),
    ("2011-09-15", "C", "Two people died in floods", "", "2", "FloodList (Sep 2011)"),
    ("2011-11-15", "C", "Further floods", "", "", "FloodList (Nov 2011)"),
    ("2013-09-03", "B", "Houses and streets flooded, roads blocked; Bwaise, Kalerwe, Kireka, Katwe, Ndeeba",
     "Bwaise; Kalerwe; Kireka; Katwe; Ndeeba", "", "FloodList, 3 Sep 2013"),
    ("2016-04-13", "A", "4am downpour; trenches overfilled, roads impassable, houses submerged; Kyebando, Bwaise, Kamwokya, Mulago, Kalerwe",
     "Kyebando; Bwaise; Kamwokya; Mulago roundabout; Kalerwe", "", "Uganda Radio Network; FloodList (13 Apr 2016)"),
    ("2018-03-08", "B", "Large standing pool of water in Bwaise III after downpour", "Bwaise", "", "Daily Monitor, 9 Mar 2018"),
    ("2024-12-15", "C", "Downpour paralysed the central business district and eastern suburbs", "Clock Tower; Kyambogo", "", "Commentary citing Dec 2024 event"),
    ("2026-10-11", "A", "Rain from ~3am; Kampala-Hoima road flooded at Lubigi; two dead (wall collapse onto rented room)",
     "Lubigi at Hoima Road; Kinawataka; Banda; Kimbejja", "2", "Daily Monitor (two reports), KFM, NTV, allAfrica"),
]


def places_lookup():
    hs = pd.read_csv(KD / "flood_hotspots.csv")
    pl = gpd.read_file(KD / "osm_places.geojson").dropna(subset=["name"])
    lut = {r.place.lower(): (r.lat, r.lon) for r in hs.itertuples()}
    for r in pl.itertuples():
        lut.setdefault(r.name.lower(), (r.geometry.y, r.geometry.x))
    return lut


def geocode(text, lut):
    out = []
    for tok in re.split(r"[;,/()]", text or ""):
        t = tok.strip().lower()
        if len(t) < 4:
            continue
        hit = next((k for k in lut if k == t or k.startswith(t) or t.startswith(k)), None)
        if hit:
            out.append((tok.strip(), *lut[hit]))
    return out


def main():
    m = pd.read_csv(KD / "flood_events.csv", parse_dates=["date"])
    g = pd.read_csv(KD / "flood_catalogue_gdelt.csv", parse_dates=["start", "end"])
    rows = []
    for r in m.itertuples():
        rows.append(dict(date=r.date, grade="B", description=r.places, places=r.places, channels=r.channels,
                         deaths=r.deaths, sources=r.source, n_outlets=1))
    for d, gr, desc, pl, dead, src in MANUAL_EXTRA:
        rows.append(dict(date=pd.Timestamp(d), grade=gr, description=desc, places=pl, channels="", deaths=dead or np.nan,
                         sources=src, n_outlets=2 if gr == "A" else 1))
    for r in g.itertuples():
        rows.append(dict(date=r.start, grade="A", description=r.titles.split(" | ")[0], places="", channels="",
                         deaths=np.nan, sources="GDELT: " + " ".join(r.urls.split()[:2]), n_outlets=int(r.n_outlets)))
    c = pd.DataFrame(rows).sort_values(["date", "n_outlets"], ascending=[True, False])
    # merge duplicates within 3 days: keep best grade, union text
    c["grp"] = (c.date.diff().dt.days.fillna(99) > 3).cumsum()
    agg = c.groupby("grp").agg(date=("date", "min"), grade=("grade", "min"), n_outlets=("n_outlets", "max"),
                               description=("description", lambda v: " | ".join(dict.fromkeys(x for x in v if isinstance(x, str) and x))),
                               places=("places", lambda v: "; ".join(dict.fromkeys(x for x in v if isinstance(x, str) and x))),
                               channels=("channels", lambda v: "; ".join(dict.fromkeys(x for x in v if isinstance(x, str) and x))),
                               deaths=("deaths", lambda v: pd.to_numeric(v, errors="coerce").max()),
                               sources=("sources", lambda v: " | ".join(dict.fromkeys(str(x) for x in v))))
    agg.loc[agg.n_outlets >= 2, "grade"] = "A"
    agg = agg.reset_index(drop=True)
    agg.insert(0, "event_id", [f"KLA-{d:%Y%m%d}" for d in agg.date])
    # rain on the day
    ch = xr.open_dataset(PROC / "chirps_uganda_daily.nc")["precip"].sel(lat=slice(0.15, 0.5), lon=slice(32.4, 32.8)).mean(("lat", "lon")).to_series()
    pw = pd.read_csv(KD / "power_hourly_kampala.csv", index_col=0, parse_dates=True).PRECTOTCORR
    pw = pw.where(pw < 150)
    wet = ch["1991":"2020"]
    wet = wet[wet >= 1]
    agg["chirps_1d_mm"] = [ch.get(d, np.nan) for d in agg.date]
    agg["chirps_3d_mm"] = [ch[d - pd.Timedelta(days=2):d].sum() if d in ch.index else np.nan for d in agg.date]
    agg["chirps_1d_pctile"] = [(wet < v).mean() * 100 if np.isfinite(v) else np.nan for v in agg.chirps_1d_mm]
    agg["power_peak_hour_mm"] = [pw[d:d + pd.Timedelta(hours=23)].max() if d >= pw.index[0] else np.nan for d in agg.date]
    agg.loc[agg.grade == "C", ["chirps_1d_mm", "chirps_3d_mm", "chirps_1d_pctile", "power_peak_hour_mm"]] = np.nan
    agg["date_precision"] = np.where(agg.grade == "C", "month", "day")
    agg["date"] = agg.date.dt.strftime("%Y-%m-%d")
    agg.loc[agg.grade == "C", "date"] = agg.loc[agg.grade == "C", "date"].str[:7]
    lut = places_lookup()
    pl_rows = []
    for r in agg.itertuples():
        for name, la, lo in geocode(r.places, lut):
            pl_rows.append(dict(event_id=r.event_id, place=name, lat=round(la, 5), lon=round(lo, 5), location_uncertainty_m=500))
    pls = pd.DataFrame(pl_rows).drop_duplicates(["event_id", "place"])
    agg["n_places_geocoded"] = agg.event_id.map(pls.groupby("event_id").size()).fillna(0).astype(int)
    agg.round(1).to_csv(RES / "kampala_flood_catalogue_2007_2026.csv", index=False)
    pls.to_csv(RES / "kampala_flood_catalogue_places.csv", index=False)
    print(agg[["event_id", "grade", "n_outlets", "deaths", "chirps_1d_mm", "chirps_1d_pctile", "power_peak_hour_mm", "n_places_geocoded"]].to_string())
    print("events", len(agg), "| by grade", agg.grade.value_counts().to_dict(), "| deaths", int(agg.deaths.sum()),
          "| place records", len(pls))
    figure(agg, pls)


def figure(agg, pls):
    d = agg.copy()
    d["dt"] = pd.to_datetime(d.date.str.slice(0, 7) + "-15")
    d.loc[d.date.str.len() == 10, "dt"] = pd.to_datetime(d.date[d.date.str.len() == 10])
    fig = plt.figure(figsize=(15, 6.4))
    ax = fig.add_axes([0.05, 0.16, 0.55, 0.72])
    cols = {"A": "#b30000", "B": "#fc8d59", "C": "#bdbdbd"}
    for gr in "ABC":
        e = d[d.grade == gr]
        ax.scatter(e.dt, np.where(e.deaths.fillna(0) > 0, e.deaths.fillna(0), 0.3), s=60 + 25 * e.n_outlets, color=cols[gr],
                   edgecolor="k", lw=0.5, label={"A": "A: dated, 2+ outlets", "B": "B: dated, 1 report", "C": "C: month only"}[gr], zorder=3)
    ax.axvspan(pd.Timestamp("2021-04-01"), pd.Timestamp("2025-03-01"), color="#eee", lw=0, zorder=0)
    ax.text(pd.Timestamp("2023-03-15"), 7.3, "no multi-outlet events\nin the news index", ha="center", fontsize=8.5, color="#666")
    ax.set_ylim(0, 9)
    ax.set_ylabel("reported deaths (0.3 = none reported)")
    ax.set_title("Kampala's recorded floods, 2007-2026 (marker size: number of outlets)", loc="left", fontsize=11)
    ax.legend(fontsize=8.5, loc="upper left")
    ax2 = fig.add_axes([0.64, 0.10, 0.34, 0.80])
    s = gpd.read_file(KD / "segments.gpkg")
    s[s.up_km2 >= 2].plot(ax=ax2, color="#9ecae1", lw=0.6)
    cnt = pls.groupby(["place", "lat", "lon"]).size().reset_index(name="n")
    ax2.scatter(cnt.lon, cnt.lat, s=30 * cnt.n, color="#b30000", alpha=0.7, edgecolor="k", lw=0.4, zorder=3)
    OFF = {"Bwaise": (-62, 10), "Kalerwe": (8, 12), "Banda": (10, 8), "Kyambogo": (-30, -20), "Katwe": (8, 6), "Ndeeba": (-58, -12)}
    for r in cnt.sort_values("n", ascending=False).head(6).itertuples():
        ax2.annotate(f"{r.place} ({r.n})", (r.lon, r.lat), xytext=OFF.get(r.place.split(" ")[0], (6, 4)), textcoords="offset points",
                     fontsize=8.5, arrowprops=dict(arrowstyle="-", lw=0.5, color="#555"),
                     bbox=dict(facecolor="white", edgecolor="none", pad=0.8, alpha=0.85))
    ax2.set_xlim(32.47, 32.70)
    ax2.set_ylim(0.22, 0.40)
    ax2.set_aspect("equal")
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.set_title("Places named in flood reports (size = events)", loc="left", fontsize=11)
    save(fig, "kd41_flood_catalogue.png", OUT,
         source="Flood reports: Daily Monitor, New Vision, NTV Uganda, The Observer, Uganda Radio Network, KFM, ReliefWeb, FloodList, "
                "GDELT news index · channels: © OpenStreetMap contributors")


if __name__ == "__main__":
    main()
