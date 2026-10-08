"""Outcome data for the food-security paper.

Outputs (data/processed/):
  vhi_uganda_weekly.csv   NOAA STAR Vegetation Health (VCI, TCI, VHI) weekly means over cropland, per Ugandan
                          province (district) in the VHP admin set, 1982-2025
  vhp_provinces.csv       province id -> name
  fews_ipc_uganda.csv     FEWS NET IPC-compatible phase classifications for Uganda (all units, all dates)
  faostat_uganda_qcl.csv  FAOSTAT crop area, production, yield for Uganda (maize, beans, sorghum, millet, cassava,
                          bananas), 1961-latest
"""
import io
import re
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw" / "food"
RAW.mkdir(parents=True, exist_ok=True)
VHP = "https://www.star.nesdis.noaa.gov/smcd/emb/vci/VH/get_TS_admin.php?country=UGA&provinceID={}&year1=1981&year2=2025&type=Mean"


def get(url, **kw):
    for i in range(5):
        try:
            r = requests.get(url, timeout=300, **kw)
            if r.ok:
                return r
        except requests.RequestException:
            pass
        time.sleep(10 * (i + 1))
    raise RuntimeError(url)


def vhi():
    f = OUT / "vhi_uganda_weekly.csv"
    if f.exists():
        return
    rows, names = [], []
    pid, misses = 1, 0
    while misses < 3 and pid < 200:
        t = get(VHP.format(pid)).text
        m = re.search(r"Province=\s*(\d+):\s*([^,]+),", t)
        data = re.findall(r"^\s*(\d{4}),\s*(\d+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)", t, re.M)
        if not m or not data:
            misses += 1
            pid += 1
            continue
        misses = 0
        names.append(dict(province_id=pid, name=m.group(2).strip()))
        for d in data:
            rows.append(dict(province_id=pid, year=int(d[0]), week=int(d[1]), SMN=float(d[2]), SMT=float(d[3]),
                             VCI=float(d[4]), TCI=float(d[5]), VHI=float(d[6])))
        print("vhp", pid, m.group(2).strip(), len(data), flush=True)
        pid += 1
    df = pd.DataFrame(rows)
    for c in ("VCI", "TCI", "VHI"):
        df[c] = df[c].where(df[c] >= 0)
    df.to_csv(f, index=False)
    pd.DataFrame(names).to_csv(OUT / "vhp_provinces.csv", index=False)


def ipc():
    f = OUT / "fews_ipc_uganda.csv"
    if f.exists():
        return
    r = get("https://fdw.fews.net/api/ipcphase/?country_code=UG&format=csv")
    f.write_bytes(r.content)
    print("ipc rows", len(pd.read_csv(f)))


def faostat():
    f = OUT / "faostat_uganda_qcl.csv"
    if f.exists():
        return
    z = RAW / "Production_Crops_Livestock_E_Africa.zip"
    if not z.exists():
        z.write_bytes(get("https://bulks-faostat.fao.org/production/Production_Crops_Livestock_E_Africa.zip").content)
    with zipfile.ZipFile(z) as zz:
        name = "Production_Crops_Livestock_E_Africa_NOFLAG.csv"
        df = pd.read_csv(zz.open(name), encoding="latin-1")
    df = df[(df.Area == "Uganda") & df.Item.isin(["Maize (corn)", "Beans, dry", "Sorghum", "Millet", "Cassava, fresh",
                                                   "Plantains and cooking bananas", "Bananas", "Groundnuts, excluding shelled"])]
    ycols = [c for c in df.columns if re.fullmatch(r"Y\d{4}", c)]
    long = df.melt(id_vars=["Item", "Element", "Unit"], value_vars=ycols, var_name="year", value_name="value")
    long["year"] = long.year.str[1:].astype(int)
    long.dropna().to_csv(f, index=False)
    print(long.groupby(["Item", "Element"]).year.agg(["min", "max"]))


if __name__ == "__main__":
    import sys
    for s in sys.argv[1:] or ["ipc", "faostat", "vhi"]:
        globals()[s]()
