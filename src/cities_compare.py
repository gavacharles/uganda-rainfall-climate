"""Cross-city comparison: rain vs land attribution (1992-2014) and 'urbanisation already done' vs 'climate to come'.

For each city with results:
  urban_past   = area-weighted % increase in 10-yr peak flow from land change alone, 1975 -> 2020 (fixed rainfall)
  climate_2050 = % increase in 10-yr peak flow from the CMIP6-median rain uplift (SSP2-4.5 and SSP5-8.5, 2041-2070),
                 applied to 2030 land cover
  ratio        = urban_past / climate_2050
Outputs: figures/kp05_two_city_attribution.png (all cities), figures/kp06_urban_vs_climate.png,
         results/two_city_summary.csv, results/cities_urban_vs_climate.csv
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import CAT, INK, INK2, MUTED, RES, save

CITIES = [("kampala", "Kampala"), ("johannesburg", "Johannesburg"), ("nairobi", "Nairobi"),
          ("dar_es_salaam", "Dar es Salaam"), ("lagos", "Lagos")]
CITIES = [(c, n) for c, n in CITIES if (RES / f"{c}_attribution_mc.csv").exists()]


def area_weights(city, idx):
    a = pd.read_csv(RES / f"{city}_attribution.csv")
    a = a[(a["product"] == "CHIRPS") & (a["T"] == 10)].drop_duplicates("catchment").set_index("catchment").area_km2
    return a.reindex(idx)


rows, urows = [], []
fig, ax = plt.subplots(figsize=(8, 6.6))
for k, (city, name) in enumerate(CITIES):
    s = pd.read_csv(RES / f"{city}_attribution_mc.csv")
    s = s[(s["product"] == "CHIRPS") & (s["T"] == 10)].set_index("catchment")
    area = area_weights(city, s.index)
    ax.scatter(s.rain_pct_of_base_p50, s.land_pct_of_base_p50, s=10 + area * 2.5, color=CAT[k], alpha=0.7,
               edgecolor="white", lw=0.5, label=f"{name} ({len(s)})", zorder=3)
    w = area / area.sum()
    rows.append(dict(city=name, catchments=len(s), area_km2=area.sum(), land_effect_aw=(s.land_pct_of_base_p50 * w).sum(),
                     rain_effect_aw=(s.rain_pct_of_base_p50 * w).sum(),
                     share_land_dominant=float((s.p_land_exceeds_rain > 0.5).mean())))
    # urbanisation already done vs climate to come
    tl = pd.read_csv(RES / f"{city}_peak_timeline.csv")
    tl = tl[tl["T"] == 10].pivot(index="epoch", columns="catchment", values="qp")
    aw = area_weights(city, tl.columns)
    up = (tl.loc[2020] / tl.loc[1975] - 1) * 100
    fu = pd.read_csv(RES / f"{city}_futures.csv")
    fu = fu[fu["T"] == 10].pivot(index="catchment", columns="scenario", values="change_vs_1992_pct")
    base30 = fu["2030 land (GHSL), 1981-2025 rain"]
    c245 = [c for c in fu.columns if c.startswith("2030 land, rain") and "SSP2-4.5" in c][0]
    c585 = [c for c in fu.columns if c.startswith("2030 land, rain") and "SSP5-8.5" in c][0]
    cl245 = ((1 + fu[c245] / 100) / (1 + base30 / 100) - 1) * 100
    cl585 = ((1 + fu[c585] / 100) / (1 + base30 / 100) - 1) * 100
    wa = aw / aw.sum()
    U = float((up * wa).sum())
    C1 = float((cl245.reindex(wa.index) * wa).sum())
    C2 = float((cl585.reindex(wa.index) * wa).sum())
    urows.append(dict(city=name, urban_past_1975_2020_pct=U, climate_ssp245_pct=C1, climate_ssp585_pct=C2,
                      ratio_ssp245=U / C1, ratio_ssp585=U / C2, rain_uplift_ssp245=c245.split("+")[1].split("%")[0],
                      rain_uplift_ssp585=c585.split("+")[1].split("%")[0]))
lim = (-30, 60)
ax.plot(lim, lim, color=MUTED, lw=1, ls="--")
ax.axhline(0, color=INK, lw=0.6)
ax.axvline(0, color=INK, lw=0.6)
ax.text(40, 43, "land = rain", color=INK2, fontsize=8, rotation=38)
ax.text(-28, 56, "land cover dominates", color=INK2, fontsize=8)
ax.text(44, 24, "rainfall dominates", color=INK2, fontsize=8)
ax.set_xlim(*lim)
ax.set_ylim(-5, 60)
ax.set_xlabel("rainfall effect on 10-year peak flow, 1992-2014 (% of 1992)")
ax.set_ylabel("land-cover effect on 10-year peak flow (% of 1992)")
ax.set_title("Rain or concrete? Each dot is one catchment (size = area)")
ax.legend(fontsize=8, loc="lower right", title="city (catchments)", title_fontsize=8)
save(fig, "kp05_two_city_attribution.png")

u = pd.DataFrame(urows)
fig, ax = plt.subplots(figsize=(9, 4.4))
x = np.arange(len(u))
ax.bar(x - 0.27, u.urban_past_1975_2020_pct, 0.26, color=CAT[1], label="urbanisation already done, 1975-2020")
ax.bar(x, u.climate_ssp245_pct, 0.26, color=CAT[0], alpha=0.55, label="climate to come, 2041-70, SSP2-4.5")
ax.bar(x + 0.27, u.climate_ssp585_pct, 0.26, color=CAT[0], label="climate to come, 2041-70, SSP5-8.5")
for i, r in u.iterrows():
    ax.text(i - 0.27, r.urban_past_1975_2020_pct + 1, f"{r.urban_past_1975_2020_pct:.0f}%", ha="center", fontsize=8, color=INK)
ax.set_xticks(x)
ax.set_xticklabels(u.city)
ax.set_ylabel("increase in 10-year peak flow (%)")
ax.set_title("Urbanisation already done vs climate change to come (area-weighted, CHIRPS-based design rain)")
ax.legend(fontsize=8)
save(fig, "kp06_urban_vs_climate.png")
pd.DataFrame(rows).round(2).to_csv(RES / "two_city_summary.csv", index=False)
u.round(2).to_csv(RES / "cities_urban_vs_climate.csv", index=False)
print(pd.DataFrame(rows).round(1).to_string())
print(u.round(2).to_string())
