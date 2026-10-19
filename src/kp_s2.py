"""Sentinel-2 L2A cloud-masked median composite for Greater Kampala (posters): dry seasons Jun-Aug and Dec-Feb,
2024-2026, cloud < 30 %, SCL clear classes only, 20 m, UTM 36N. Output: data/kd/sat_kampala_s2_2024_26.nc"""
import numpy as np
import planetary_computer as pc
import pystac_client
from odc.stac import load

from common import ROOT

BOX = [32.40, 0.15, 32.78, 0.45]
OUT = ROOT / "data" / "kd" / "sat_kampala_s2_2024_26.nc"


def main():
    cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
    items = []
    for a, b in (("2024-06-01", "2024-08-31"), ("2024-12-01", "2025-02-28"), ("2025-06-01", "2025-08-31"),
                 ("2025-12-01", "2026-02-28"), ("2026-06-01", "2026-08-31")):
        items += list(cat.search(collections=["sentinel-2-l2a"], bbox=BOX, datetime=f"{a}/{b}",
                                 query={"eo:cloud_cover": {"lt": 30}}).items())
    print("scenes", len(items), flush=True)
    ds = load(items, bands=["B02", "B03", "B04", "B08", "B11", "SCL"], bbox=BOX, crs="EPSG:32636", resolution=20,
              groupby="solar_day", chunks={"x": 2048, "y": 2048, "time": 1}, fail_on_error=False)
    base = {i.datetime.date(): float(i.properties.get("s2:processing_baseline", "0")) for i in items}
    off = np.array([1000 if base.get(np.datetime64(t, "D").astype(object), 0) >= 4 else 0 for t in ds.time.values])
    import xarray as xr
    offx = xr.DataArray(off, coords={"time": ds.time}, dims="time")
    clear = ds.SCL.isin([4, 5, 6, 7, 11])
    out = ((ds[["B02", "B03", "B04", "B08", "B11"]].where(clear).astype("float32") - offx) / 10000).median("time")
    out.compute().to_netcdf(OUT)
    print("saved", OUT, flush=True)


if __name__ == "__main__":
    main()
