"""Fill table placeholders in report/index.html from results/*.csv (run after water, food_irrigation, drainage)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
html = ROOT / "report" / "index.html"
s = html.read_text()

# town design-storm rows
t = pd.read_csv(RES / "drainage_towns.csv")
rows = []
for r in t.itertuples():
    ch = r.change_10yr_pct_2004_25_vs_1981_03
    cls = "up" if ch >= 10 else ("down" if ch <= -10 else "")
    up = f"+{r.uplift_ssp245_2041_2070_pct:.0f}% / +{r.uplift_ssp585_2041_2070_pct:.0f}%"
    rows.append(f"<tr><td>{r.town}</td><td>{r.R24_2yr_point:.0f}</td><td>{r.R24_10yr_point:.0f}</td>"
                f"<td>{r.R24_50yr_point:.0f}</td><td>{r.R24_100yr_point:.0f}</td><td>{r.I_1h_10yr_mm_per_h:.0f}</td>"
                f"<td class=\"{cls}\">{ch:+.0f}%</td><td>{up}</td></tr>")
s = s.replace("TOWN_ROWS", "\n".join(rows))
u245, u585 = t.uplift_ssp245_2041_2070_pct.iloc[0], t.uplift_ssp585_2041_2070_pct.iloc[0]
s = s.replace("UPLIFT_RANGE", f"+{u245:.0f}% (SSP2-4.5) to +{u585:.0f}% (SSP5-8.5)")

# irrigation change by zone
i = pd.read_csv(RES / "irrigation_zone.csv").set_index("zone")
base = "NIR 80% dependable rain, year-round (mm/yr)"
keys = {"IRR_K": "Karamoja (NE, semi-arid)", "IRR_N": "North (Acholi-Kitgum)", "IRR_W": "West Nile-Lango-Teso-Elgon belt",
        "IRR_M": "Mid-west & Kyoga (Bunyoro-Kyoga)", "IRR_L": "Lake Victoria crescent (Central-Busoga)",
        "IRR_S": "South-west (Ankole-Kigezi)"}
for k, z in keys.items():
    a = 100 * (i.loc[z, "NIR 80% dependable, year-round ssp245 2041-2070 (mm/yr)"] / i.loc[z, base] - 1)
    b = 100 * (i.loc[z, "NIR 80% dependable, year-round ssp585 2041-2070 (mm/yr)"] / i.loc[z, base] - 1)
    s = s.replace(f"<td>{k}</td>", f"<td>{a:+.0f}% / {b:+.0f}%</td>")

c = pd.read_csv(RES / "cmip6_uganda_changes.csv")
s = s.replace("CMIP6_N", str(int(c.n_models.max())))
html.write_text(s)
left = [p for p in ("TOWN_ROWS", "UPLIFT_RANGE", "IRR_", "CMIP6_N", "FUTURE_TEXT") if p in s]
print("placeholders left:", left)
