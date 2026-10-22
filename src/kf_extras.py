"""Kampala Flood Replay, step 3: extra layers for the page (run after kf_export.py).

  channels.pmtiles  every channel stretch (layer c): i = stretch index (model order), p = maintenance priority percentile,
                    n = name; from Kampala Drain Watch (kd_network)
  extras.json       per stretch: maintenance priority percentile and top-three driver codes, with the driver names
  cells_dist.bin    uint8 per floodable cell (cells.png scan order): distance to its stretch, metres / 2
  roads.bin         replaces kf_export's: uint16 stretch, uint16 HAND (cm), float32 length (m), float32 lon, float32 lat
  roads_names.json  road name per road piece (rid order)
  trees.png         tree cover (ESA WorldCover 2021, class 10) on a 30 m grid over the map view, grey levels 0-255
"""
import gzip
import json

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from PIL import Image

from common import PROC
from kf_export import BOX, KD, OUT, VIEW, segments

DRIVERS = ["Homes on the floodplain", "Buildings in channel reserve", "Little wetland left to buffer",
           "Culverts & bridges (constrictions)", "Waste dumps & markets nearby", "Runoff load (upstream area x paving)"]


def main():
    s, h = segments()
    n = len(s)
    # channels as vector tiles, and their priorities
    c = s[["name", "risk_pct", "geometry"]].copy()
    c["i"] = np.arange(n, dtype="int32")
    c["p"] = c.risk_pct.fillna(0).round().astype("int32")
    c["n"] = c["name"].fillna("")
    f = OUT / "channels.pmtiles"
    f.unlink(missing_ok=True)
    import pyogrio
    pyogrio.write_dataframe(c[["i", "p", "n", "geometry"]].to_crs(4326), f, driver="PMTiles", layer="c",
                            dataset_options=dict(MINZOOM=10, MAXZOOM=15, NAME="Kampala channels"))
    drv = [[DRIVERS.index(d.strip()) for d in str(x).split(";") if d.strip() in DRIVERS] for x in s.top_drivers.fillna("")]
    (OUT / "extras.json").write_text(json.dumps(dict(drivers=DRIVERS, seg_risk=c.p.tolist(), seg_drv=drv), separators=(",", ":")))
    print("channels", n, "pmtiles MB", round(f.stat().st_size / 1e6, 2), flush=True)

    # distance from each floodable cell to its stretch, in cells.png scan order
    M = json.loads((OUT / "meta.json").read_text())
    img = np.array(Image.open(OUT / "cells.png"))
    sg = img[..., 0].astype(int) * 256 + img[..., 1]
    W, Hh = M["cells_size"]
    w0, s0, e0, n0 = M["cells_bounds"]
    rows, cols = np.nonzero(sg != 65535)                      # row-major, the order the page reads them
    lon, lat = w0 + (cols + 0.5) * (e0 - w0) / W, n0 - (rows + 0.5) * (n0 - s0) / Hh
    su = s.to_crs(32636).geometry.values
    pts = gpd.GeoSeries(gpd.points_from_xy(lon, lat), crs=4326).to_crs(32636).values
    d = shapely.distance(pts, su[sg[rows, cols]])
    np.clip(np.round(d / 2), 0, 255).astype("uint8").tofile(OUT / "cells_dist.bin")
    print("cells", len(d), "median distance m", round(float(np.median(d))), flush=True)

    # roads: add position, and names
    p = gpd.read_parquet(KD / "road_pieces.parquet")
    idx = pd.Series(np.arange(n), index=h.seg_id.values)
    p = p[p.seg_id.isin(idx.index) & (p.hand_min <= 5)].copy().reset_index(drop=True)   # same selection as kf_export
    p["s"] = idx.loc[p.seg_id].values
    p["h"] = np.round(p.hand_min * 100).astype(int)
    p = p.to_crs(4326) if p.crs and p.crs.to_epsg() != 4326 else p
    mid = p.geometry.interpolate(0.5, normalized=True)
    old = np.fromfile(OUT / "roads.bin", "<u2").reshape(-1, 4)
    assert len(old) == len(p) and (old[:, 0] == p.s.values).all(), "road order differs from kf_export"
    rec = np.zeros(len(p), dtype=[("s", "<u2"), ("h", "<u2"), ("len", "<f4"), ("lon", "<f4"), ("lat", "<f4")])
    rec["s"], rec["h"], rec["len"], rec["lon"], rec["lat"] = p.s.values, p.h.values, p.len_m.values, mid.x.values, mid.y.values
    rec.tofile(OUT / "roads.bin")
    (OUT / "roads.bin.gz").write_bytes(gzip.compress((OUT / "roads.bin").read_bytes(), 9, mtime=0))
    (OUT / "roads_names.json").write_text(json.dumps(p["name"].fillna("").tolist(), separators=(",", ":")))
    for nm in ("cells_dist.bin",):
        (OUT / (nm + ".gz")).write_bytes(gzip.compress((OUT / nm).read_bytes(), 9, mtime=0))
    print("roads", len(p), "named", int((p["name"].fillna("") != "").sum()), flush=True)

    # trees: WorldCover class 10 averaged to 30 m over the view
    with rasterio.open(PROC / "kampala_worldcover.tif") as r:
        win = rasterio.windows.from_bounds(VIEW[0], VIEW[1], VIEW[2], VIEW[3], r.transform)
        wc = r.read(1, window=win)
    k = 3
    H_, W_ = wc.shape[0] // k * k, wc.shape[1] // k * k
    tree = (wc[:H_, :W_] == 10).reshape(H_ // k, k, W_ // k, k).mean((1, 3))
    # one grey channel, four cover levels (0, 1/3, 2/3, full): the page colours it green
    Image.fromarray((np.round(tree * 3) * 85).astype("uint8"), "L").save(OUT / "trees.png", optimize=True)
    ex = json.loads((OUT / "extras.json").read_text())
    ex["trees_bounds"] = [VIEW[0], VIEW[3] - H_ * 8.333333333333333e-05, VIEW[0] + W_ * 8.333333333333333e-05, VIEW[3]]
    (OUT / "extras.json").write_text(json.dumps(ex, separators=(",", ":")))
    print("trees", tree.shape, "cover", round(float(tree.mean()) * 100, 1), "% KB", (OUT / "trees.png").stat().st_size // 1000)


if __name__ == "__main__":
    main()
