"""Flood x AMR paper 1, step 5: exposure in each real flood of the catalogue (the replay model, event by event).

For every catalogued Kampala flood dated to the day (2007-2026), PERSIANN-CCS hourly rain (CHRS, UC Irvine) is fetched for
42 hours, from noon the day before to 06:00 the day after (Kampala time); only the Kampala window is kept and the raw files
are deleted. The hourly screening model of the replay (kf_export.run: rational method per stretch, HAND rating curves,
channels 30% silted, rain x1.5) gives water depth on every floodable 30 m square for each hour.
Per event and stretch: person-hours in water of 10 cm or more (GHS-POP 2020 residents x hours), building-hours,
water-point-hours, and resistance-weighted person-hours (routed source load x person-hours, am_index weights).
Check: is a reported place (catalogue geocodes) within 500 m of modelled water in that event?
Outputs: data/processed/am_event_rain/<event>.nc, results/am_events.csv (per event), results/am_event_stretches.csv
(per stretch, summed over events), results/am_event_places.csv
"""
import gzip
import subprocess

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr

from common import PROC, RES, ROOT

KD = ROOT / "data" / "kd"
EV = PROC / "am_event_rain"
TMP = ROOT / "data" / "raw" / "persiann_tmp"
LON0, LON1, LAT0, LAT1 = 32.30, 32.90, -0.06, 0.60


def online():
    r = subprocess.run(["curl", "-s", "--max-time", "30", "-o", "/dev/null", "-w", "%{http_code}",
                        "ftp://persiann.eng.uci.edu/CHRSdata/PERSIANN-CCS/hrly/readme.hrly"], capture_output=True, text=True)
    return r.stdout.strip() in ("226", "200", "150")


def fetch(event, day, can_fetch=True):
    """42 hourly PERSIANN-CCS grids around the event day, Kampala window only; None if not cached and not fetchable."""
    f = EV / f"{event}.nc"
    if f.exists():
        return xr.open_dataarray(f)
    if not can_fetch:
        return None
    EV.mkdir(parents=True, exist_ok=True); TMP.mkdir(parents=True, exist_ok=True)
    c0, c1 = int(round((LON0 - 0.02) / 0.04)), int(round((LON1 - 0.02) / 0.04)) + 1
    r0, r1 = int(round((59.98 - LAT1) / 0.04)), int(round((59.98 - LAT0) / 0.04)) + 1
    times = pd.date_range(pd.Timestamp(day) - pd.Timedelta(hours=12), periods=42, freq="h")     # local time
    frames = []
    for t in times:
        u = t - pd.Timedelta(hours=3)                                                            # file hours are UTC
        name = f"rgccs1h{u:%y}{u.dayofyear:03d}{u:%H}.bin.gz"
        p = TMP / name
        url = f"ftp://persiann.eng.uci.edu/CHRSdata/PERSIANN-CCS/hrly/{u:%Y}/{name}"
        subprocess.run(["curl", "-s", "--max-time", "180", "-o", str(p), url], check=False)
        try:
            a = np.frombuffer(gzip.open(p).read(), dtype=">i2").reshape(3000, 9000)[r0:r1, c0:c1].astype("float32")
            frames.append(np.where(a < 0, np.nan, a / 100))
        except Exception:
            frames.append(np.full((r1 - r0, c1 - c0), np.nan, "float32"))
        p.unlink(missing_ok=True)
    if all(np.isnan(x).all() for x in frames):
        return None                                                                                 # nothing fetched: do not cache
    da = xr.DataArray(np.stack(frames), dims=("time", "lat", "lon"), name="rain",
                      coords=dict(time=times, lat=59.98 - 0.04 * np.arange(r0, r1), lon=0.02 + 0.04 * np.arange(c0, c1)))
    da.to_netcdf(f)
    return da


def intensity(s, h, r):
    """As kf_export.seg_rain, for any hourly rain grid."""
    from kd_hydraulics import idf_intensity
    r = r.fillna(0)
    c = s.to_crs(32636).geometry.centroid.to_crs(4326)
    la, lo = r.lat.values, r.lon.values
    R = np.zeros((len(s), r.sizes["time"]), "float32")
    for k, (x, y) in enumerate(zip(c.x.values, c.y.values)):
        i, j = np.abs(la - y).argmin(), np.abs(lo - x).argmin()
        R[k] = r.values[:, max(i - 1, 0):i + 2, max(j - 1, 0):j + 2].mean((1, 2))
    fi = idf_intensity()
    tc = h.tc_min.values
    peak = fi(2, np.minimum(tc, 60)) / fi(2, np.full(len(tc), 60.0))
    I = np.zeros_like(R)
    for k in range(len(s)):
        if tc[k] <= 60:
            I[k] = R[k] * peak[k]
        else:
            n = int(np.ceil(tc[k] / 60)); I[k] = np.convolve(R[k], np.ones(n) / n)[:R.shape[1]]
    return I


def main():
    from kf_export import rating, run, segments
    s, h = segments()
    C1990 = 0.25 + 0.65 * np.clip(2.27 * s.up_built_1990.values, 0, 0.95)
    FP = rating(s, h)
    cl = np.load(KD / "depth_cells.npz")
    a, _, c0, _, e, f0 = cl["transform"]
    lon, lat = c0 + a * (cl["cols"] + 0.5), f0 + e * (cl["rows"] + 0.5)
    pop = np.nan_to_num(xr.open_dataset(PROC / "kampala_ghs_pop.nc").pop.sel(epoch=2020)
                        .sel(lat=xr.DataArray(lat), lon=xr.DataArray(lon), method="nearest").values) / 9.0
    key = (cl["rows"].astype(np.int64) << 20) + cl["cols"]
    def per_cell(x, y):
        k = (((y - f0) / e).astype(np.int64) << 20) + ((x - c0) / a).astype(np.int64)
        u, n = np.unique(k, return_counts=True); m = dict(zip(u, n))
        return np.array([m.get(v, 0) for v in key], "float32")
    b = gpd.read_parquet(KD / "ms_buildings.parquet"); bc = b.geometry.centroid
    nb = per_cell(bc.x.values, bc.y.values); del b, bc
    wp = gpd.read_file(KD / "amr" / "water_points.gpkg"); nw = per_cell(wp.geometry.x.values, wp.geometry.y.values)
    st = pd.read_csv(RES / "am_stretches.csv")
    load = st.load.values
    cat = pd.read_csv(RES / "kampala_flood_catalogue_2007_2026.csv")
    cat = cat[cat.date_precision == "day"]
    places = pd.read_csv(RES / "kampala_flood_catalogue_places.csv")
    rows, prow = [], []
    acc = dict(ph=np.zeros(len(s)), bh=np.zeros(len(s)), wh=np.zeros(len(s)))
    can = online()
    print("PERSIANN archive reachable:", can, flush=True)
    for ev in cat.itertuples():
        r = fetch(ev.event_id, ev.date, can)
        if r is None:
            print("no rain data for", ev.event_id, flush=True)
            rows.append(dict(event=ev.event_id, date=ev.date, grade=ev.grade, hours_with_data=0)); continue
        I = intensity(s, h, r)
        H = run(h, FP, I, mult=1.5, silt=0.3, paving="2020", C1990=C1990)
        wet = (H[cl["seg"]] - (np.round(cl["hand"] * 20) / 20)[:, None]) >= 0.0999          # cells x hours
        hrs = wet.sum(1)
        ph = np.bincount(cl["seg"], weights=pop * hrs, minlength=len(s))
        bh = np.bincount(cl["seg"], weights=nb * hrs, minlength=len(s))
        wh = np.bincount(cl["seg"], weights=nw * hrs, minlength=len(s))
        for k_, v in (("ph", ph), ("bh", bh), ("wh", wh)):
            acc[k_] += v
        area = wet.sum(0) * 900 / 1e6
        rain = float(r.sel(lat=slice(0.42, 0.20), lon=slice(32.45, 32.72)).mean(("lat", "lon")).sum())
        valid = int(np.isfinite(r.values).all((1, 2)).sum())
        rows.append(dict(event=ev.event_id, date=ev.date, grade=ev.grade, rain_42h_mm=round(rain, 1), hours_with_data=valid,
                         peak_km2=round(float(area.max()), 2), person_hours=round(float(ph.sum())), building_hours=round(float(bh.sum())),
                         water_point_hours=round(float(wh.sum()), 1), amr_weighted_person_hours=round(float((ph * load).sum()))))
        for p in places[places.event_id == ev.event_id].itertuples():
            d = np.hypot((lon - p.lon) * 111320, (lat - p.lat) * 110570)
            near = d <= 500
            prow.append(dict(event=ev.event_id, place=p.place, modelled_water_within_500m=bool(wet[near].any()),
                             max_hours=int(hrs[near].max()) if near.any() else 0))
        print(rows[-1], flush=True)
    E = pd.DataFrame(rows); E.to_csv(RES / "am_events.csv", index=False)
    P = pd.DataFrame(prow); P.to_csv(RES / "am_event_places.csv", index=False)
    S = st[["seg", "name", "system", "load", "eae_people", "rank"]].copy()
    S["event_person_hours"] = acc["ph"].round(1); S["event_building_hours"] = acc["bh"].round(1); S["event_water_point_hours"] = acc["wh"].round(2)
    S["event_amr_weighted"] = (acc["ph"] * load).round(1)
    S.to_csv(RES / "am_event_stretches.csv", index=False)
    from scipy.stats import spearmanr
    m = S.eae_people > 0
    rho = spearmanr(S.eae_people[m] * S.load[m], S.event_amr_weighted[m])[0]
    print("places hit", P.modelled_water_within_500m.mean().round(2), "of", len(P), "; rank agreement design vs events rho", round(rho, 3))


if __name__ == "__main__":
    main()
