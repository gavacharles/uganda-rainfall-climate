"""Kampala Flood Replay, step 1: hourly rain for the 10-11 October 2026 storm.

PERSIANN-CCS hourly (CHRS, UC Irvine; 0.04 deg, about 4 km), files rgccs1hYYDDDHH.bin.gz in data/raw/persiann_ccs/,
big-endian int16, mm/h x 100, 3000 x 9000 grid from 59.98 N / 0.02 E. HH is UTC; Kampala is UTC+3.
Output: data/processed/kf_rain_persiann.nc (time in Kampala local time, lat, lon) over 32.30-32.90 E, -0.06-0.60 N.
"""
import gzip

import numpy as np
import pandas as pd
import xarray as xr

from common import PROC, ROOT

RAW = ROOT / "data" / "raw" / "persiann_ccs"
LON0, LON1, LAT0, LAT1 = 32.30, 32.90, -0.06, 0.60


def main():
    c0, c1 = int(round((LON0 - 0.02) / 0.04)), int(round((LON1 - 0.02) / 0.04)) + 1
    r0, r1 = int(round((59.98 - LAT1) / 0.04)), int(round((59.98 - LAT0) / 0.04)) + 1
    lats, lons = 59.98 - 0.04 * np.arange(r0, r1), 0.02 + 0.04 * np.arange(c0, c1)
    frames, times = [], []
    for f in sorted(RAW.glob("rgccs1h*.bin.gz")):
        k = f.name[7:14]
        t = pd.Timestamp(f"20{k[:2]}-01-01") + pd.Timedelta(days=int(k[2:5]) - 1, hours=int(k[5:7]) + 3)  # local time
        a = np.frombuffer(gzip.open(f).read(), dtype=">i2").reshape(3000, 9000)[r0:r1, c0:c1].astype("float32")
        frames.append(np.where(a < 0, np.nan, a / 100)); times.append(t)
    ds = xr.Dataset({"rain": (("time", "lat", "lon"), np.stack(frames))}, coords=dict(time=times, lat=lats, lon=lons))
    ds.rain.attrs.update(units="mm/h", note="hour beginning at time, Kampala local (UTC+3)")
    ds.to_netcdf(PROC / "kf_rain_persiann.nc")
    k = ds.rain.sel(lat=slice(0.42, 0.20), lon=slice(32.45, 32.72))
    print("Kampala box mean and max by hour (mm/h):")
    for t in ds.time.values:
        m, x = float(k.sel(time=t).mean()), float(k.sel(time=t).max())
        if x > 0.5:
            print(str(t)[5:16], round(m, 1), round(x, 1))
    print("event total, box mean:", round(float(k.sum("time").mean()), 1), "max cell:", round(float(k.sum("time").max()), 1))


if __name__ == "__main__":
    main()
