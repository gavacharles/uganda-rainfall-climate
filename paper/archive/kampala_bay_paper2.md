---
title: "The lost free treatment plant: urban wetland loss and the water reaching Inner Murchison Bay, Lake Victoria, 1986–2026"
author: "Gava Charles"
date: "Draft, October 2026"
---

**Target journals:** *Science of the Total Environment*; *Journal of Great Lakes Research*; *Ecological Indicators*; *Wetlands Ecology and Management*.

# Abstract

Kampala's valley wetlands once did two jobs for free: they held storm water, and they cleaned the wastewater and runoff flowing to Inner Murchison Bay, the arm of Lake Victoria that supplies most of the city's drinking water. Studies in the 1990s measured that cleaning in the Nakivubo swamp and priced it at US$1,500–2,900 per hectare per year. We ask how much of this "treatment plant" has been lost, and whether the loss shows in the bay. We use satellite data only, with no utility data:
- **Wetland:** vegetated valley floor in the four catchments that drain to the bay, from Landsat dry-season composites, 1986–2025;
- **Bay:** turbidity (Dogliotti et al. 2015) and a chlorophyll index (NDCI) at the channel outlets, in the inner and outer bay and in the open lake, from every usable Sentinel-2 scene in 2017–2026 (426 scene-days) and every Landsat scene in 1984–2026 (499 scene-days).

Results:
1. **The wetland halved.** Vegetated valley floor draining to the bay fell from 1,200 ha in 1986 to 587 ha in 2025 (−51%). The losses were Kinawataka −78%, Nakivubo −46% and Kansanga −46%. At published values, that is US$0.9–1.8 million a year of treatment the city no longer receives. At 1999 loads, it means about 64 t of nitrogen and 9 t of phosphorus a year that the Nakivubo swamp no longer retains.
2. **The bay carries the city's signature.** In 2017–2026, the chlorophyll index at the outlets (median 0.30) and in the inner bay (0.28) was four times the open lake's (0.07). Turbidity was 23% higher at the outlets than in the open lake on the same day.
3. **The signature has grown as the wetland shrank.** In the Landsat record, outlet turbidity relative to the open lake on the same day rose from 1.14 (1984–95) to 1.25, 1.34 and 1.51 (2016–26) (Kendall τ = 0.18, p < 0.001). Controlling for sensor, month and recent rain, each 100 ha of wetland lost is associated with a 5.3% higher outlet-to-lake ratio (95% CI 0.9–10%, p = 0.019).
4. **Storms add pulses on top of a chronic load.** After three days with 25 mm or more of rain, the outlet-to-lake ratio was 1.31, against 1.15 after dry spells. Individual scenes show plumes spreading across the inner bay, but across all scenes the storm effect is only borderline significant (p = 0.07). The degradation is chronic, not just a wet-weather event.

Kampala's flood problem and its water-quality problem share a cause: the valley floors that used to absorb both water and waste have been built over. Protecting and restoring the remaining Nakivubo, Kansanga and Kinawataka wetlands is a water-treatment investment as well as a flood measure.

# 1. Introduction

- **The bay and the city.** Inner Murchison Bay (IMB) is a shallow arm of Lake Victoria on Kampala's southern edge. It receives the city's main drainage channels, the Nakivubo, Kinawataka and Kansanga, together with much of its untreated wastewater, and the Ggaba waterworks draw the city's drinking water from the bay. Rising colour, turbidity and algae in the raw water at Ggaba were reported as early as 1995–2000 (Kanyesigye et al., cited in later studies), and the bay has continued to degrade (Akurut et al.; Nakkazi et al. 2024).
- **The wetland's job.** Before it was built over, the Nakivubo swamp received most of the city's wastewater. Kansiime and Nalubega (1999) measured swamp-wide removal of about 56% of nitrogen, 40% of phosphorus and 91% of faecal coliforms. Emerton et al. (1999) valued this treatment at US$1,500–2,900 per hectare per year, and estimated that about 800 kg of nitrogen and 150 kg of phosphorus a day passed through Nakivubo on the way to the bay.
- **The gap.** These studies are 25 years old. Since then the wetlands have been converted to industry, housing and farming, and the city has doubled. There is no recent public estimate of how much treatment capacity remains, and the water-quality record that would show the effect belongs to the utility and is hard to obtain.
- **Our approach.** Satellites can measure both sides: how much wetland remains, from Landsat since 1986, and how the bay's water compares with the open lake, from Landsat and Sentinel-2. Comparing the outlets with the open lake on the same day removes most effects of sensor, haze and season.
- **Questions:**
  - RQ1: How much of the bay-draining wetland has been lost since 1986, and what treatment does that represent?
  - RQ2: Do the channel outlets show a persistent turbidity and chlorophyll signal relative to the open lake?
  - RQ3: Has that signal grown as the wetland shrank, and how much do storms add?

# 2. Data and methods

## 2.1 Wetland

| Item | Choice |
|---|---|
| Catchments | The four catchments that drain directly to the bay, from D8 routing of the Copernicus GLO-30 DEM (Paper A): Nakivubo (38 km²), Kinawataka (17 km²), Kansanga (17 km²), Munyonyo shore (5 km²) |
| Valley floor | Height above nearest drainage (HAND; Nobre et al. 2011) < 3 m |
| Vegetated wetland | NDVI > 0.45 in Landsat dry-season (June–September) median composites; 1986, 1995, 2005, 2015, 2025 (Landsat 5, 7, 8, 9; 4–24 scenes each) |
| Treatment value | US$1,500–2,900 per ha per year (Emerton et al. 1999) |
| Nutrients | 800 kg N and 150 kg P a day through Nakivubo; swamp-wide removal 56% N, 40% P (Kansiime and Nalubega 1999; Emerton et al. 1999); retention scaled by the share of Nakivubo wetland remaining relative to 1995 |

A lake-fringe zone (lower Kinawataka, Luzira, Port Bell) was also measured but is reported separately (Supplementary Table S1), because its boundary is arbitrary and it includes rural shoreline.

## 2.2 Bay water

- **Water mask.** Pixels classed as water in at least 60% of clear dry-season Sentinel-2 views (2024–26), with water defined as Sen2Cor class "water" or short-wave infrared (B11) reflectance below 0.03. This keeps algae-rich and turbid water but excludes floating vegetation mats and land.
- **Zones** (Fig. kd42a):
  - *outlets*: water within 1.2 km of the Nakivubo, Kansanga and Kinawataka mouths;
  - *inner bay*: the rest of IMB north of the narrows near Ggaba (0.236° N);
  - *outer bay*: from the narrows to 0.17° N;
  - *open lake* (reference): south of 0.17° N.
- **Per-scene values.** For every Sentinel-2 L2A scene with less than 70% cloud (2017–2026; 20 m), and every Landsat Collection 2 Level-2 scene with less than 60% cloud (1984–2026; 30 m), the median of each zone over valid water pixels. Valid pixels are clear (no cloud, shadow or saturation), have SWIR reflectance below 0.03 (no glint or floating mats), and have red reflectance between 0 and 0.16. A zone counts only when at least 30% of its pixels are valid.
- **Turbidity:** T = 228.1 ρ / (1 − ρ/0.1641) FNU from red reflectance (Dogliotti et al. 2015, 645 nm coefficients).
- **Chlorophyll index:** NDCI = (B05 − B04)/(B05 + B04) (Mishra and Mishra 2012), Sentinel-2 only. It is used as a relative index, not converted to concentrations.
- **Processing baselines.** The Sentinel-2 reflectance offset introduced with processing baseline 04.00 was removed scene by scene.
- **Rain:** CHIRPS daily, Greater Kampala mean. Antecedent rain is the 3 days before the overpass.

## 2.3 Analysis

- The outlet-to-open-lake ratio of turbidity on the same day is the main indicator. Taking a ratio within one scene removes most differences between sensors, atmospheres and seasons.
- RQ2: zone medians, and a Wilcoxon signed-rank test of the NDCI difference between outlets and open lake.
- RQ3, long term: Kendall's τ of the ratio against time; Spearman correlation with wetland area interpolated to each scene date; and OLS of log(ratio) on wetland area with sensor, month and log antecedent rain as controls (HC1 robust errors).
- RQ3, storms: OLS of log(ratio) on log(1 + 3-day rain), a linear trend and month, Sentinel-2, with HAC errors (3 lags).

# 3. Results

## 3.1 The wetland halved

| Vegetated valley floor (ha) | 1986 | 1995 | 2005 | 2015 | 2025 | Change |
|---|---|---|---|---|---|---|
| Nakivubo | 529 | 467 | 374 | 330 | 284 | −46% |
| Kansanga | 321 | 308 | 273 | 213 | 173 | −46% |
| Kinawataka | 250 | 215 | 182 | 110 | 56 | −78% |
| Munyonyo shore | 101 | 102 | 98 | 82 | 75 | −26% |
| **All bay-draining** | **1,200** | **1,092** | **927** | **735** | **587** | **−51%** |

The share of valley floor still vegetated fell from 90% to 44% (Fig. kd43a). The loss is steady across four decades and has not slowed. A machine-learning land-cover map (LightGBM trained on agreed WorldCover and Impact Observatory labels; 81% accuracy when trained on 2025 and tested on 2015; Paper 1, Section 3.4) gives the same picture: natural vegetation (wetland plus trees and shrubs) on these valley floors fell from 863 to 384 ha (−56%), and the built and bare share rose from 11% to 56%. Kinawataka is the extreme case, at 3% built in 1986 and 75% in 2025. Two independent methods agree on a loss of about half. A third check at 10 m (Sentinel-2 dry-season medians, 2024–26) finds 570 ha of green valley floor in the bay-draining catchments today, against 587 ha from Landsat 2025 (Fig. kd55).

**What was lost.**
- **Treatment value:** 613 ha × US$1,500–2,900 = **US$0.9–1.8 million a year**. This matches Emerton's whole-wetland estimate of US$1–1.75 million a year for Nakivubo's treatment, a useful consistency check.
- **Nutrients:** with Nakivubo's wetland at 61% of its 1995 extent, retention at 1999 loads falls from 448 to 272 kg N a day and from 60 to 36 kg P a day: **about 64 t of nitrogen and 9 t of phosphorus a year** no longer retained. Loads have risen with the population since 1999, so these are lower bounds.

## 3.2 The bay carries the city's signature

| Zone (Sentinel-2, 2017–2026, median of scene medians) | Turbidity (FNU) | NDCI |
|---|---|---|
| Outlets | 12.3 | 0.30 |
| Inner bay | 13.2 | 0.28 |
| Outer bay | 11.1 | 0.11 |
| Open lake | 10.0 | 0.07 |

On the same day, the outlets' NDCI exceeded the open lake's by a median of 0.22 (n = 124 scenes, p < 0.001). The gradient is sharp: the inner bay is green and algae-rich, and the water clears beyond the narrows (Figs. kd42, kd43c). Turbidity follows the same pattern but less steeply, because algae, not only sediment, drive the inner bay's optical signal.

## 3.3 The signature grew as the wetland shrank

| Landsat period | Scenes | Outlet ÷ open-lake turbidity | Wetland (ha, mid-period) |
|---|---|---|---|
| 1984–95 | 4 | 1.14 | 1,152 |
| 1996–2005 | 21 | 1.25 | 1,009 |
| 2006–15 | 43 | 1.34 | 831 |
| 2016–26 | 111 | 1.51 | 646 |

- Trend in the ratio: Kendall τ = 0.18, p < 0.001 (n = 179 scenes with both zones valid).
- Ratio against remaining wetland: Spearman ρ = −0.25, p < 0.001.
- With sensor, month and antecedent rain controlled: each 100 ha of wetland lost goes with a 5.3% higher outlet-to-lake ratio (95% CI 0.9–10%, p = 0.019) (Fig. kd43b).

The open lake itself changed less: median open-lake turbidity was 8–9 FNU in 1996–2015 and 7.4 FNU in 2016–26. The rise is local to the outlets.

## 3.4 Storms add pulses to a chronic load

| Sentinel-2 scenes | n | Outlet ÷ open lake |
|---|---|---|
| Dry spell (3-day rain < 1 mm) | 35 | 1.15 |
| After rain (≥ 25 mm in 3 days) | 15 | 1.31 |

The regression coefficient on log antecedent rain is positive (0.043, p = 0.069). Single scenes show what this means: after 37 mm on 18–20 November 2019, turbid water (15–23 FNU) covered most of the inner bay, while after a dry spell in June 2026 the inner bay was at 10–14 FNU (Fig. kd42b–c). Clear images within a day or two of storms are rare in the rainy seasons, so the storm signal is undersampled. The main finding is that the outlets are degraded even in dry weather.

# 4. Discussion

- **Two services, one loss.** Paper 1 counted the valley floors' lost flood storage, and this paper counts their lost treatment. Both result from the same conversion of papyrus valley floor to buildings, fill and gardens. A hectare of Nakivubo wetland protects homes from floods and the bay from sewage. Valuing only one of these understates the case for protection.
- **Why it matters for the water supply.** The Ggaba waterworks draw from the bay. More algae and turbidity raise treatment costs, through more coagulant, more frequent filter washing and taste and odour problems. The satellite record shows that the water near the channels is getting worse relative to the lake, the same direction the plant operators reported 25 years ago.
- **Policy:**
  - Treat the remaining Nakivubo, Kansanga and Kinawataka wetland (587 ha) as water-treatment infrastructure: gazette it, stop further conversion, and include it in KCCA and NWSC asset planning.
  - Restore where possible. Each 100 ha restored is worth roughly US$0.15–0.29 million a year in treatment, plus flood storage (Paper 1).
  - Extend sewer connections to the city's sewage treatment works, so that wetlands polish treated effluent instead of absorbing raw sewage.
  - Monitor from space. The method here runs on free data and could be updated after every clear scene as an early warning for the waterworks.
- **Limitations:**
  - *Optical:* Sen2Cor and Landsat surface reflectance are designed for land, and water-specific atmospheric correction (such as ACOLITE) would be more accurate. The same-day ratio cancels much of this error, but absolute FNU values are approximate.
  - *Turbidity vs algae:* in eutrophic water, red reflectance reflects both sediment and algae, so the "turbidity" here is an optical index of both.
  - *Sampling:* only 4 usable Landsat scenes before 1996, so the early ratio is uncertain. Cloud cover biases the record toward dry-season and post-storm-clearing days.
  - *Attribution:* the association with wetland loss is not proof of cause. Population, sewage loads and industrial discharges grew over the same period. A design with loads would need the utility's data. The correlation is nonetheless consistent with the measured treatment function of these wetlands.
  - *Treatment value and nutrients* are transferred from 1999 studies and scaled by area, as screening estimates only.
- **Validation path.** NWSC raw-water records at Ggaba, if made available, would calibrate the turbidity and chlorophyll indices, and a few field transects from the Nakivubo mouth to the open lake would anchor the gradient.

# 5. Conclusion

Half of the wetland that cleaned Kampala's water before it reached Lake Victoria has been built over since 1986, which removes roughly US$1–2 million a year of free treatment. The satellite record shows the consequence. The water where the city's channels enter the bay is green and turbid relative to the open lake, and the contrast has grown from 1.14 to 1.51 times as the wetland shrank. The wetlands that remain are infrastructure, for floods and for water, and they are cheaper to keep than to replace.

# Data and code availability

Code: `src/kd_bay.py` (water mask, zones, Sentinel-2 and Landsat extraction, wetland, tests, Figs. kd42–kd43). Results: `results/kd_bay_*.csv`. All inputs are open (Microsoft Planetary Computer STAC; CHIRPS; Copernicus DEM).

# Figures

- kd42: a, Sentinel-2 true colour of Inner Murchison Bay with the channel outlets; b, turbidity after a dry spell (29 Jun 2026); c, turbidity after rain (21 Nov 2019).
- kd43: a, vegetated wetland draining to the bay, 1986–2025, by catchment; b, Landsat outlet-to-open-lake turbidity ratio, 1986–2026, by sensor, with period medians; c, Sentinel-2 chlorophyll index (NDCI) by zone.

# References

Items marked † were found through search but not opened; verify them before submission.

1. † Akurut, M., Niwagaba, C. B. and Willems, P. (2016). Long-term variations of water quality in the Inner Murchison Bay, Lake Victoria.
2. Dogliotti, A. I., Ruddick, K. G., Nechad, B., Doxaran, D. and Knaeps, E. (2015). A single algorithm to retrieve turbidity from remotely-sensed data in all coastal and estuarine waters. *Remote Sensing of Environment* 156, 157–168. doi:10.1016/j.rse.2014.09.020
3. Emerton, L., Iyango, L., Luwum, P. and Malinga, A. (1999). *The present economic value of Nakivubo urban wetland, Uganda*. IUCN Eastern Africa Regional Office and National Wetlands Programme, Kampala.
4. European Space Agency (2021). Copernicus DEM GLO-30. doi:10.5270/ESA-c5d3d65
5. Funk, C. et al. (2015). The climate hazards infrared precipitation with stations: a new environmental record for monitoring extremes. *Scientific Data* 2, 150066. doi:10.1038/sdata.2015.66
6. † Kanyesigye, C. et al. (2001). Raw water quality changes at the Gaba water treatment works, Inner Murchison Bay, 1995–2000.
7. Kansiime, F. and Nalubega, M. (1999). *Wastewater treatment by a natural wetland: the Nakivubo swamp, Uganda – processes and implications*. PhD thesis, IHE Delft / Wageningen University.
8. Mishra, S. and Mishra, D. R. (2012). Normalized difference chlorophyll index: a novel model for remote estimation of chlorophyll-a concentration in turbid productive waters. *Remote Sensing of Environment* 117, 394–406. doi:10.1016/j.rse.2011.10.016
9. † Nakkazi et al. (2024). Linking land use and precipitation changes to water quality changes in Lake Victoria using earth observation data. *Environmental Monitoring and Assessment*. doi:10.1007/s10661-024-13261-2
10. Nobre, A. D. et al. (2011). Height Above the Nearest Drainage – a hydrologically relevant new terrain model. *Journal of Hydrology* 404, 13–29. doi:10.1016/j.jhydrol.2011.03.051
11. Crawford, C. J. et al. (2023). The 50-year Landsat collection 2 archive. *Science of Remote Sensing* 8, 100103. doi:10.1016/j.srs.2023.100103
12. † Vanhellemont, Q. and Ruddick, K. (2018). Atmospheric correction of metre-scale optical satellite data for inland and coastal water applications. *Remote Sensing of Environment* 216, 586–597.
13. Ke, G. et al. (2017). LightGBM: a highly efficient gradient boosting decision tree. *Advances in Neural Information Processing Systems* 30, 3146–3154.
14. Companion papers of this programme: A, 1 (*The lost sponge*), D0 (flood catalogue).
