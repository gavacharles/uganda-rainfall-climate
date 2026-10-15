---
title: "The double loss: Kampala's valley wetlands as flood storage and water treatment, 1975–2026"
author: "Gava Charles"
date: "Draft, October 2026"
---

**Paper 2 of 5, Kampala drainage programme.** Merges earlier drafts 1 (*The lost sponge*) and 2 (*The lost free treatment plant*).
**Target journals:** *Science of the Total Environment*; *Landscape and Urban Planning*; *Journal of Hydrology: Regional Studies*.

# Abstract

Kampala's valley floors were papyrus wetlands that did two jobs for the city at no cost: they held storm water, and they cleaned the wastewater and runoff flowing to Inner Murchison Bay, the arm of Lake Victoria that supplies most of the city's drinking water. Wetland loss is usually reported as an area. We measure both services in their own units, flood storage in cubic metres and treatment in hectares of functioning wetland, and track them from 1975 to 2026 with open data and three independent satellite methods.

1. **Half the living valley floor is gone.** Landsat, a machine-learning land-cover classifier (LightGBM; 84% spatial cross-validated accuracy, 81% when transferred to another year) and 10 m Sentinel-2 agree within a few percentage points. Natural vegetation on the valley floors fell by 48% city-wide between 1986 and 2025, and by 68–95% in the Lubigi, Kinawataka and Nalukolongo systems. Built and bare ground rose from 3% to 35% of the valley floors.
2. **Flood storage.** Valley-floor storage up to 1 m above the drains fell by 8.5 million m³ between 1975 and 2020 while 10-year storm runoff rose by 8.5 million m³: a combined gap of 17 million m³ (about 6,800 Olympic pools) for one storm. In 1975, five of six channel systems could hold a 10-year storm's runoff on their valley floors. By 2020 only one, barely, could.
3. **Water treatment.** Green wetland in the valleys draining to Murchison Bay fell from 1,200 ha (1986) to 587 ha (2025), −51%. At published values, that is US$0.9–1.8 million a year of treatment lost, and about 64 t of nitrogen and 9 t of phosphorus a year no longer retained.
4. **The bay shows it.** In every usable Sentinel-2 scene (2017–2026) the channel outlets carry four times the open lake's chlorophyll index. In 40 years of Landsat, outlet turbidity relative to the open lake rose from 1.14 to 1.51 as the wetland shrank: +5.3% per 100 ha lost (p = 0.019), controlling for sensor, month and rain.

The same land conversion removed two services at once. Valley-floor wetland should be treated as infrastructure, protected and accounted for in cubic metres of storage and hectares of treatment.

# 1. Introduction

- **One landscape, two services.** Before the 1980s, Kampala's valley floors were papyrus swamps between the hills. They stored storm water and released it slowly, and the Nakivubo swamp received most of the city's wastewater, removing about 56% of nitrogen, 40% of phosphorus and 91% of faecal coliforms before it reached the lake (Kansiime and Nalubega 1999). Emerton et al. (1999) valued that treatment at US$1,500–2,900 per hectare per year.
- **Loss is measured as area.** About 73% of Kampala–Wakiso wetland was lost between 1986 and 2016 (Kabiri et al. 2022), and houses in wetlands nearly tripled between 2004 and 2024 (KCCA). Planners and engineers need volumes and functions instead: storage in m³ compared with runoff, and treatment capacity compared with loads.
- **The bay.** Inner Murchison Bay receives the Nakivubo, Kinawataka and Kansanga channels, and the Ggaba waterworks draw the city's water from it. Colour, turbidity and algae in the raw water rose as early as 1995–2000 (Kanyesigye et al.), and the bay has continued to degrade (Akurut et al.; Nakkazi et al. 2024).
- **Gap.** No study converts Kampala's wetland loss into lost storage volume, compares it with design-storm runoff, separates papyrus from gardens and fill with validated classification, or links the loss to the water reaching the bay.
- **Contributions:**
  1. three independent satellite measures of valley-floor change, including a validated machine-learning land-cover history;
  2. a 1975–2030 flood-storage series and storm-to-storage ratio per channel system;
  3. the loss of treatment wetland and its nutrient and economic value;
  4. a 40-year satellite record of the channel outlets relative to the open lake.

# 2. Study area: the valley floors and the bay

Kampala's valley floors, the land less than 3 m above the nearest drain, cover about 104 km² of the study box, a quarter of its land (Fig. cm2). In 1986 most was green: papyrus in the wet centres, *Miscanthidium* grass, gardens and trees at the edges. Two kinds of valley matter here:
- **Valleys that drain away from the lake**, chiefly the Lubigi, which flows north-west to the Mayanja river. Their wetlands matter for flood storage only.
- **Valleys that drain to Inner Murchison Bay**: Nakivubo (the city centre and Industrial Area), Kinawataka (Ntinda, Kyambogo, Banda, joining the Namanve wetland), Kansanga (Kabalagala, Ggaba) and a strip of Munyonyo shore. Their wetlands did both jobs, storing storm water and treating it before it reached the lake.

Inner Murchison Bay is a shallow, sheltered arm of Lake Victoria about 4 km across, opening south through a narrows near Ggaba into the outer bay and the open lake. The Ggaba waterworks, which supply most of Kampala's piped water, draw from the bay's western shore. The bay therefore receives the city's drainage and supplies its drinking water, with the valley wetlands between the two. Figure lc2 shows that landscape from Landsat in 1986 and 2025: the dark papyrus of the Nakivubo and Kinawataka valleys in 1986, and roofs, industry and gardens across most of it by 2025.

# 3. Data and methods

## 3.1 Valley floors and their cover

| Item | Source and rule |
|---|---|
| Valley floor | Height above nearest drainage (HAND; Nobre et al. 2011) < 3 m, Copernicus GLO-30 DEM; open water (WorldCover class 80) excluded |
| Channel systems | Lubigi, Nakivubo, Kinawataka, Kansanga, Nalukolongo, Walufumbe (D8 catchments) |
| Paving 1975–2030 | JRC GHS-BUILT-S R2023A; impervious = 2.27 × built share (calibrated to WorldCover 2021) |
| Green valley floor (method 1) | Landsat 5/7/8/9 dry-season median composites, 1986, 1995, 2005, 2015, 2025; NDVI > 0.45 |
| Land cover (method 2) | LightGBM classifier (Ke et al. 2017) on the same composites: wetland vegetation, trees and shrubs, crops and grass, built and bare, water. Labels where ESA WorldCover 2021 and Impact Observatory 2017/2023 agree (wetland: two of three sources including OSM). TM/ETM+ harmonised to OLI (Roy et al. 2016) |
| Today at 10 m (method 3) | Sentinel-2 L2A dry-season medians, five seasons 2024–26; NDVI > 0.45 |

The classifier was validated by spatial block cross-validation (3 km blocks) and, more relevantly for history, by training on 2025 and testing on 2015 imagery against 2017 labels.

## 3.2 Flood storage

For a water level *h* above the nearest drain, each 30 m cell holds max(0, h − HAND) × area. Effective storage multiplies by (1 − impervious share). Runoff demand = design rainfall × C × area, C = 0.25 + 0.65 × impervious share, with gauge-corrected 6-hour design depths of 72.3, 88.6 and 95.5 mm (10-, 50-, 100-year). The storm-to-storage ratio is 1 m storage divided by 10-year runoff. The "living sponge" is storage on valley floor still green in Landsat.

## 3.3 Treatment and the bay

- **Treatment wetland:** green valley floor in the four catchments draining to the bay (Nakivubo, Kinawataka, Kansanga, Munyonyo shore). Value: US$1,500–2,900 per ha per year (Emerton et al. 1999). Nutrients: 800 kg N and 150 kg P a day through Nakivubo, swamp-wide removal 56% N and 40% P, retention scaled by the share of Nakivubo wetland remaining relative to 1995.
- **Bay water:** a static water mask (water in ≥ 60% of clear dry-season Sentinel-2 views). Zones: outlets (within 1.2 km of the Nakivubo, Kansanga and Kinawataka mouths), inner bay, outer bay, open lake (south of 0.17° N). Per scene: zone medians of turbidity (Dogliotti et al. 2015, 645 nm) and NDCI (Mishra and Mishra 2012) over clear, glint-free water. Sentinel-2 2017–2026 (426 scene-days) and Landsat 1984–2026 (499 scene-days; Sentinel-2 processing-baseline offset removed scene by scene).
- **Analysis:** the same-day outlet-to-open-lake turbidity ratio, which cancels most sensor, haze and season effects. Kendall trend; OLS of log(ratio) on wetland area with sensor, month and 3-day rain controls (HC1 errors).

# 4. Results

## 4.1 Three methods, one picture of the valley floors

| Validation of the classifier | Overall accuracy | Wetland F1 |
|---|---|---|
| Spatial block cross-validation, 2025 | 84% | 0.89 |
| Trained on 2025, tested on 2015 imagery | 81% | 0.90 |

| Valley floor, 1986 → 2025 (classifier) | Natural vegetation (wetland + trees) | Built and bare share |
|---|---|---|
| Nalukolongo | 99 → 5 ha (−95%) | 18% → 93% |
| Kinawataka | 183 → 27 ha (−85%) | 3% → 75% |
| Walufumbe | 30 → 7 ha (−77%) | 0% → 48% |
| Lubigi | 672 → 214 ha (−68%) | 7% → 66% |
| Kansanga | 260 → 122 ha (−53%) | 1% → 50% |
| Nakivubo | 343 → 178 ha (−48%) | 21% → 56% |
| **Greater Kampala core** | **8,006 → 4,144 ha (−48%)** | **3% → 35%** |

Cultivation took part of the valley floor first, in the 1990s and 2000s, and was then itself built over. Today's green share from 10 m Sentinel-2 agrees with 30 m Landsat within 1–7 points (Lubigi 34% vs 36%, Kinawataka 24% vs 23%, Nalukolongo 9% vs 7%; Fig. kd55). The classifier's share is lower because it counts only wetland and trees (Fig. kd44).

## 4.2 Flood storage: from surplus to deficit

| Greater Kampala core | 1975 | 2020 | 2030 (proj.) |
|---|---|---|---|
| Impervious share | 15% | 42% | 43% |
| Effective storage, 1 m (million m³) | 86.4 | 77.9 | 76.2 |
| 10-year storm runoff (million m³) | 17.5 | 26.0 | 26.3 |

The city lost 8.5 million m³ of 1 m storage and gained 8.5 million m³ of 10-year runoff: a 17 million m³ gap for one storm (Fig. kd30). Storage on still-green valley floor fell faster, from 90.3 to 73.2 million m³ (1986–2025).

| Storm-to-storage ratio (1 m storage ÷ 10-yr runoff) | 1975 | 2020 | Storage needed to restore a ratio of 1 |
|---|---|---|---|
| Kansanga | 2.21 | 1.06 | – |
| Lubigi | 2.05 | 0.93 | 0.16 million m³ |
| Kinawataka | 1.80 | 0.50 | 0.44 million m³ |
| Nakivubo | 1.36 | 0.97 | 0.05 million m³ |
| Walufumbe | 1.19 | 0.41 | 0.13 million m³ |
| Nalukolongo | 0.71 | 0.32 | 0.41 million m³ |

## 4.3 Treatment: the wetland draining to the bay halved

| Green valley floor draining to the bay (ha) | 1986 | 1995 | 2005 | 2015 | 2025 | Change |
|---|---|---|---|---|---|---|
| Nakivubo | 529 | 467 | 374 | 330 | 284 | −46% |
| Kansanga | 321 | 308 | 273 | 213 | 173 | −46% |
| Kinawataka | 250 | 215 | 182 | 110 | 56 | −78% |
| Munyonyo shore | 101 | 102 | 98 | 82 | 75 | −26% |
| **All** | **1,200** | **1,092** | **927** | **735** | **587** | **−51%** |

The classifier gives the same picture (natural vegetation 863 → 384 ha, −56%), and Sentinel-2 finds 570 ha today. The lost 613 ha were worth US$0.9–1.8 million a year in treatment, matching Emerton's whole-wetland estimate for Nakivubo. At 1999 loads, about 64 t of nitrogen and 9 t of phosphorus a year are no longer retained; loads have since risen, so these are lower bounds.

## 4.4 The bay carries the city's signature, and it has grown

| Zone (Sentinel-2, 2017–2026) | Turbidity (FNU) | NDCI |
|---|---|---|
| Outlets | 12.3 | 0.30 |
| Inner bay | 13.2 | 0.28 |
| Outer bay | 11.1 | 0.11 |
| Open lake | 10.0 | 0.07 |

| Landsat period | Scenes | Outlet ÷ open-lake turbidity | Wetland draining to the bay (ha) |
|---|---|---|---|
| 1984–95 | 4 | 1.14 | 1,152 |
| 1996–2005 | 21 | 1.25 | 1,009 |
| 2006–15 | 43 | 1.34 | 831 |
| 2016–26 | 111 | 1.51 | 646 |

The outlets' NDCI exceeds the open lake's by a median 0.22 on the same day (n = 124, p < 0.001). The ratio rose over time (Kendall τ = 0.18, p < 0.001) and with wetland loss: +5.3% per 100 ha lost (95% CI 0.9–10%, p = 0.019), controlling for sensor, month and rain (Fig. kd43). After rain, plumes spread across the inner bay (ratio 1.31 after ≥ 25 mm in three days, 1.15 after dry spells, p = 0.07), but the outlets are degraded even in dry weather (Fig. kd42).

# 5. Discussion

- **How the valleys were lost.** The land-cover history shows a sequence, not a single event. Papyrus was first drained and cultivated (crops and grass peaked on many valley floors in the 1990s and 2000s), then filled and built on. Industrial estates were sited on the Nakivubo and Kinawataka floors under earlier planning, and informal and rental housing followed on the Lubigi and Nalukolongo floors (Paper 3). Each stage removed some function: cultivation shortened the path water took through the papyrus, and building removed storage and treatment altogether.
- **Why the bay records it.** A papyrus swamp slows water, settles sediment and lets plants and microbes take up nutrients. When channels cut straight through a shrunken wetland, the city's runoff and wastewater reach the bay faster and less treated. The satellite record cannot isolate this from population growth, but the outlet-to-lake contrast rising step by step with wetland loss is what that mechanism predicts.

- **One loss, two bills.** Each hectare of papyrus valley floor lost removed both storage and treatment. Valuing either alone understates the case for protection. Flood storage is the volume the drainage system must now carry (Papers 1 and 4); treatment is a cost passed to the Ggaba waterworks and the lake.
- **Storage is infrastructure.** Restoring each system's storm-to-storage ratio to 1 needs about 1.2 million m³ in total, mostly in Kinawataka and Nalukolongo. It could come from protected wetland, detention basins in parks and sports grounds, and on-plot storage required in building approval.
- **Policy:**
  - a "no net loss of storage" rule for valley-floor development, with compensatory storage;
  - gazetting the remaining green valley floor, especially the 587 ha draining to the bay and the Lubigi and Kansanga floors where most living sponge remains;
  - sewer connections, so that wetlands polish treated effluent rather than absorb raw sewage;
  - routine satellite monitoring of both valley-floor cover and bay water, using the open methods here.
- **Limitations:**
  - HAND storage is a static volume (no timing, infiltration or connectivity);
  - a 30 m DEM smooths embankments and fill;
  - surface reflectance products are designed for land, so bay values are relative indices; the same-day ratio cancels most error;
  - few Landsat scenes before 1996;
  - the bay–wetland link is an association: population and sewage loads also grew. Utility raw-water records would allow attribution;
  - treatment values and nutrient loads are transferred from 1999 studies.

# 6. Conclusion

Half of Kampala's living valley floor has been built over since 1986. Three independent satellite methods agree. The loss shows up twice: as 17 million m³ of flood water with nowhere to go in a single 10-year storm, and as murkier, greener water where the city's channels enter Lake Victoria, the source of its drinking water. Protecting what remains is cheaper than replacing either service.

# Data and code availability

Code: `src/kd_sponge.py`, `kd_landcover.py`, `kd_bay.py`, `kd_channel_condition.py` (Sentinel-2 composites). Results: `results/kd_sponge_*.csv`, `kd_landcover_*.csv`, `kd_bay_*.csv`, `kd_valley_s2_check.csv`.

# Figures

Main: cm2 study area · lc2 Nakivubo–Kinawataka 1986 vs 2025 · kd44 machine-learning land cover 1986 vs 2025 · kd30 storage vs runoff · kd31 map of storage lost · kd42 bay plumes · kd43 wetland and outlet turbidity.
Supplement: kd55 valley floors at 10 m and method agreement · kd16 wetland time-lapse panels.

# References

Items marked † were found through search, or are grey literature not yet opened; verify them before submission.

1. Acreman, M. and Holden, J. (2013). How wetlands affect floods. *Wetlands* 33, 773–786. doi:10.1007/s13157-013-0473-2
2. † Akurut, M., Niwagaba, C. B. and Willems, P. (2016). Long-term variations of water quality in the Inner Murchison Bay, Lake Victoria.
3. Bullock, A. and Acreman, M. (2003). The role of wetlands in the hydrological cycle. *Hydrology and Earth System Sciences* 7(3), 358–389. doi:10.5194/hess-7-358-2003
4. Crawford, C. J. et al. (2023). The 50-year Landsat collection 2 archive. *Science of Remote Sensing* 8, 100103. doi:10.1016/j.srs.2023.100103
5. Dogliotti, A. I., Ruddick, K. G., Nechad, B., Doxaran, D. and Knaeps, E. (2015). A single algorithm to retrieve turbidity from remotely-sensed data in all coastal and estuarine waters. *Remote Sensing of Environment* 156, 157–168. doi:10.1016/j.rse.2014.09.020
6. Emerton, L., Iyango, L., Luwum, P. and Malinga, A. (1999). *The present economic value of Nakivubo urban wetland, Uganda*. IUCN Eastern Africa Regional Office and National Wetlands Programme, Kampala.
7. European Space Agency (2021). Copernicus DEM GLO-30. doi:10.5270/ESA-c5d3d65
8. Funk, C. et al. (2015). The climate hazards infrared precipitation with stations. *Scientific Data* 2, 150066. doi:10.1038/sdata.2015.66
9. Kabiri, S. et al. (2022). Detecting wetland encroachment and urban agriculture land classification in Uganda using hyper-temporal remote sensing. *AAS Open Research*. doi:10.12688/aasopenres.13040.2
10. Kansiime, F. and Nalubega, M. (1999). *Wastewater treatment by a natural wetland: the Nakivubo swamp, Uganda – processes and implications*. PhD thesis, IHE Delft / Wageningen University.
11. † Kanyesigye, C. et al. (2001). Raw water quality changes at the Gaba water treatment works, Inner Murchison Bay, 1995–2000.
12. Karra, K. et al. (2021). Global land use/land cover with Sentinel 2 and deep learning. *IEEE IGARSS 2021*, 4704–4707.
13. † KCCA (2024). Kampala moves to protect wetlands as loss reaches alarming levels. KCCA news release.
14. Ke, G. et al. (2017). LightGBM: a highly efficient gradient boosting decision tree. *Advances in Neural Information Processing Systems* 30, 3146–3154.
15. Mishra, S. and Mishra, D. R. (2012). Normalized difference chlorophyll index. *Remote Sensing of Environment* 117, 394–406. doi:10.1016/j.rse.2011.10.016
16. † Nakkazi et al. (2024). Linking land use and precipitation changes to water quality changes in Lake Victoria using earth observation data. *Environmental Monitoring and Assessment*. doi:10.1007/s10661-024-13261-2
17. Nobre, A. D. et al. (2011). Height Above the Nearest Drainage. *Journal of Hydrology* 404, 13–29. doi:10.1016/j.jhydrol.2011.03.051
18. Pesaresi, M. and Politis, P. (2023). GHS-BUILT-S R2023A. European Commission, JRC.
19. Roy, D. P. et al. (2016). Characterization of Landsat-7 to Landsat-8 reflective wavelength and NDVI continuity. *Remote Sensing of Environment* 185, 57–70. doi:10.1016/j.rse.2015.12.024
20. Tucker, C. J. (1979). Red and photographic infrared linear combinations for monitoring vegetation. *Remote Sensing of Environment* 8, 127–150.
21. Xu, H. (2006). Modification of normalised difference water index (NDWI). *International Journal of Remote Sensing* 27(14), 3025–3033.
22. Zanaga, D. et al. (2022). ESA WorldCover 10 m 2021 v200. doi:10.5281/zenodo.7254221
23. Copernicus Sentinel-2 L2A (ESA) and NASA/USGS Landsat Collection 2, via the Microsoft Planetary Computer.
24. Companion papers: 1 (*Rainfall or drainage?*), 3 (*Building in the water's path*), 4 (*Silt, not storms*).
