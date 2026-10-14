---
title: "The lost sponge: measuring the flood-storage volume Kampala has paved over, 1975–2030"
author: "Gava Charles"
date: "Draft, October 2026"
---

**Target journals:** *Journal of Hydrology: Regional Studies*; *Landscape and Urban Planning*; *Nature-Based Solutions*; *Ecological Engineering*.

# Abstract

Urban wetland loss is usually reported as an area: hectares of papyrus replaced by roofs. For flood management, what matters is volume, meaning how much storm water the valley floors can hold before it spills into streets and homes. We measure that storage for Greater Kampala from open data, then track it from 1975 to 2030. The inputs are:
- **Terrain:** a 30 m terrain model, from which we compute height above nearest drainage;
- **Paving:** JRC GHSL built-up surface, calibrated to impervious cover;
- **Vegetation:** Landsat composites from 1986, 1995 and 2025;
- **Storms:** gauge-corrected design storms.

Main results:
1. **Storage on unpaved valley floor.** Ground that can hold water up to 1 m above the drains fell from 86.4 to 77.9 million m³ between 1975 and 2020 (−8.5 million m³). It is projected at 76.2 million m³ by 2030. Over the same period, runoff from a 10-year, 6-hour storm rose from 17.5 to 26.0 million m³ as paving increased.
2. **The combined gap.** The storage lost plus the extra runoff is 17 million m³ for one 10-year storm, about 6,800 Olympic swimming pools.
3. **The living sponge.** Measured as storage on still-vegetated valley floor (Landsat), the loss is steeper: 90 million m³ in 1986 to 73 million m³ in 2025 city-wide. In the main channel systems the losses are:

| Channel system | Loss |
|---|---|
| Nalukolongo | −91% |
| Kinawataka | −73% |
| Lubigi | −59% |
| Walufumbe | −43% |
| Kansanga | −39% |
| Nakivubo | −37% |

4. **Storm-to-storage ratio.** In 1975, the valley-floor storage of the Lubigi, Kinawataka, Kansanga and Walufumbe systems exceeded the runoff of a 10-year storm. By 2020 none did.

We argue that valley-floor storage should be counted, protected and traded as infrastructure. Restoring even part of the lost volume through protected wetlands, detention basins and on-plot storage is likely cheaper than enlarging the downstream channels to carry the extra water.

# 1. Introduction

- Kampala's valleys were papyrus wetlands that held and slowly released storm water. Their loss is well documented as area: for example, about 73% of Kampala–Wakiso wetland area was lost between 1986 and 2016 (Landsat), and houses in wetlands rose from 20,958 in 2004 to 56,679 in 2024 (KCCA). Planners and engineers, however, need volumes: storage in m³, compared with runoff in m³.
- Paper A of this programme shows that Kampala's flood hotspots are explained by drainage pressures rather than heavier rain (rainfall extremes show no significant trend since 1981). Lost storage is the hydrological mechanism that connects encroachment to flooding.
- **Gap:** no study converts Kampala's wetland loss into lost storage volume, compares it with design-storm runoff, or tracks it per drainage system over 50 years.
- **Contribution:**
  1. an open, reproducible method to measure city-wide valley-floor storage from global datasets;
  2. a 1975–2030 storage series, with a Landsat cross-check;
  3. a storm-to-storage ratio per channel system, which planners can use to set storage targets.

# 2. Data and methods

| Layer | Source |
|---|---|
| Terrain, flow routing, HAND | Copernicus GLO-30 DEM; D8 routing (Paper A); open water (ESA WorldCover class 80) excluded |
| Paving 1975–2030 | JRC GHS-BUILT-S R2023A; impervious = 2.27 × built share, calibrated so 2020 matches WorldCover 2021 built-up; 2025 and 2030 are projections |
| Vegetated valley floor | Landsat 5/8/9 dry-season median composites, 1986, 1995, 2025; NDVI > 0.45 |
| Design storms | Gauge-corrected CHIRPS IDF: 6-hour depths of 72.3, 88.6 and 95.5 mm for 10-, 50- and 100-year return periods |
| Drainage systems | Lubigi, Nakivubo, Kinawataka, Kansanga, Nalukolongo, Walufumbe (Paper A catchments) |

**Storage capacity.** For a water level *h* metres above the nearest drain, each 30 m cell can hold *max(0, h − HAND) × area*. The *capacity* is this volume summed over the valley floor. *Effective storage* multiplies each cell by (1 − impervious share): roofs, plots and the fill placed under them displace water. We report *h* = 1, 2 and 3 m.

**Runoff demand.** Storm runoff = rainfall depth × runoff coefficient × area, with C = 0.25 + 0.65 × impervious share (Paper A). The *storm-to-storage ratio* is effective storage at 1 m divided by 10-year runoff. A ratio above 1 means the valley floor could, in principle, hold one 10-year storm's runoff.

**Landsat check.** Independent of GHSL: the storage capacity (1 m and 2 m) on valley-floor pixels that remain vegetated (NDVI > 0.45, not open water) in 1986, 1995 and 2025. This "living sponge" captures loss to fill, bare ground and paving that GHSL may miss.

# 3. Results

**3.1 City-wide storage is falling while runoff rises.**

| Greater Kampala core | 1975 | 2020 | 2030 (proj.) |
|---|---|---|---|
| Impervious share | 15% | 42% | 43% |
| Effective storage, 1 m (million m³) | 86.4 | 77.9 | 76.2 |
| Effective storage, 2 m (million m³) | 207.4 | 184.1 | 179.6 |
| Share of 1 m capacity lost | 3% | 13% | 15% |
| 10-year storm runoff (million m³) | 17.5 | 26.0 | 26.3 |
| 100-year storm runoff (million m³) | 23.1 | 34.3 | 34.8 |

Between 1975 and 2020 the city lost 8.5 million m³ of 1 m storage and gained 8.5 million m³ of 10-year storm runoff: a combined gap of 17 million m³, about 6,800 Olympic pools, for a single storm (Fig. kd30a).

**3.2 The living sponge has shrunk faster.** Storage on still-vegetated valley floor fell from 90.3 million m³ (1986) to 73.2 million m³ (2025), with the vegetated share of the valley floor falling from 82% to 66%. Losses are concentrated in the drainage systems that flood most:

| 1 m storage on vegetated valley floor (million m³) | 1986 | 2025 | Change |
|---|---|---|---|
| Lubigi | 4.06 | 1.66 | −59% |
| Nakivubo | 2.48 | 1.56 | −37% |
| Kinawataka | 1.11 | 0.31 | −73% |
| Kansanga | 1.42 | 0.87 | −39% |
| Nalukolongo | 1.01 | 0.09 | −91% |
| Walufumbe | 0.17 | 0.10 | −43% |

(Fig. kd30b.) The GHSL-based estimate is conservative, because it counts only paving, not fill, drainage or conversion of wetland to bare ground.

**3.3 From surplus to deficit.**

| Storm-to-storage ratio (1 m storage ÷ 10-yr runoff) | 1975 | 2020 |
|---|---|---|
| Kansanga | 2.21 | 1.06 |
| Lubigi | 2.05 | 0.93 |
| Kinawataka | 1.80 | 0.50 |
| Nakivubo | 1.36 | 0.97 |
| Walufumbe | 1.19 | 0.41 |
| Nalukolongo | 0.71 | 0.32 |

In 1975, five of the six systems had more valley-floor storage than one 10-year storm's runoff. By 2020 only Kansanga, barely, remained above 1. The largest combined gaps are in Lubigi (2.0 million m³), Kinawataka (0.9) and Kansanga (0.7) (Fig. kd30c). The map of lost storage (Fig. kd31) shows the losses as thin ribbons along nearly every channel, worst on the Lubigi, Kinawataka and Nalukolongo valley floors.

# 4. Discussion

- **Storage is infrastructure.** Every cubic metre of valley floor lost must be replaced by channel capacity downstream, or it floods. Valuing storage in m³ makes this trade-off visible in budgets: the 17 million m³ gap for one 10-year storm is the volume the drainage system must now handle that the landscape once absorbed.
- **Targets.** Restoring each system's storm-to-storage ratio to at least 1 would need roughly:

| System | Storage needed |
|---|---|
| Kinawataka | 0.44 million m³ |
| Nalukolongo | 0.41 million m³ |
| Lubigi | 0.16 million m³ |
| Walufumbe | 0.13 million m³ |
| Nakivubo | 0.05 million m³ |

  This could come from protected wetland, detention basins in parks and sports grounds, and on-plot tanks and permeable paving required in building approval.
- **Planning tools:**
  - a "no net loss of storage" rule for development on valley floors, with compensatory storage where building is permitted;
  - gazetting the remaining vegetated valley floor, especially in Lubigi, Kansanga and Nakivubo, where the most living sponge remains;
  - prioritising the fringe catchments where new building is projected (Papers A and D).
- **Limitations:**
  - HAND storage is a static volume; it ignores timing, infiltration and the connectivity of storage to the channel;
  - a 30 m DEM smooths small embankments and fill;
  - GHSL 2025–2030 is projected;
  - the runoff coefficients are screening values.

  A hydrodynamic model of one system (for example Lubigi) would test how much of the lost storage translates into higher flood peaks.

# 5. Conclusion

Kampala has paved over about 8.5 million m³ of valley-floor flood storage since 1975, and its living wetland sponge has shrunk by 17 million m³ since 1986, by up to 91% in some systems. Over the same period storm runoff has risen by half. Most channel systems have gone from holding a 10-year storm to holding a fraction of one. Counting storage in cubic metres turns wetland protection from an environmental preference into an engineering requirement.

# Figures

- kd30: a, storage vs paving 1975–2030; b, living sponge 1986 vs 2025 by system; c, combined gap by system
- kd31: map of storage lost 1975–2020
- kd16: wetland time-lapse panels (Landsat), from the companion study

# References

Items marked † were found through search, or are grey literature not yet opened; verify them before submission.

1. Acreman, M. and Holden, J. (2013). How wetlands affect floods. *Wetlands* 33, 773–786. doi:10.1007/s13157-013-0473-2
2. Bullock, A. and Acreman, M. (2003). The role of wetlands in the hydrological cycle. *Hydrology and Earth System Sciences* 7(3), 358–389. doi:10.5194/hess-7-358-2003
3. Kabiri, S., Allen, M., Okuonzia, J. T., Akello, B., Ssabaganzi, R., Mubiru, D., Wan, H., Dale, P. and Brooks, B. (2022). Detecting wetland encroachment and urban agriculture land classification in Uganda using hyper-temporal remote sensing. *AAS Open Research*. doi:10.12688/aasopenres.13040.2
4. Kansiime, F. and Nalubega, M. (1999). *Wastewater treatment by a natural wetland: the Nakivubo swamp, Uganda – processes and implications*. PhD thesis, IHE Delft / Wageningen University.
5. † Emerton, L., Iyango, L., Luwum, P. and Malinga, A. (1999). *The present economic value of Nakivubo urban wetland, Uganda*. IUCN Eastern Africa Regional Office and National Wetlands Programme, Kampala.
6. † KCCA (2024). Kampala moves to protect wetlands as loss reaches alarming levels. KCCA news release.
7. Nobre, A. D., Cuartas, L. A., Hodnett, M., Rennó, C. D., Rodrigues, G., Silveira, A., Waterloo, M. and Saleska, S. (2011). Height Above the Nearest Drainage – a hydrologically relevant new terrain model. *Journal of Hydrology* 404, 13–29. doi:10.1016/j.jhydrol.2011.03.051
8. Pesaresi, M. and Politis, P. (2023). GHS-BUILT-S R2023A: GHS built-up surface grid, 1975–2030. European Commission, Joint Research Centre.
9. European Space Agency (2021). Copernicus DEM GLO-30. doi:10.5270/ESA-c5d3d65
10. Zanaga, D. et al. (2022). ESA WorldCover 10 m 2021 v200. doi:10.5281/zenodo.7254221
11. Crawford, C. J. et al. (2023). The 50-year Landsat collection 2 archive. *Science of Remote Sensing* 8, 100103. doi:10.1016/j.srs.2023.100103
12. Tucker, C. J. (1979). Red and photographic infrared linear combinations for monitoring vegetation. *Remote Sensing of Environment* 8, 127–150.
13. Xu, H. (2006). Modification of normalised difference water index (NDWI) to enhance open water features in remotely sensed imagery. *International Journal of Remote Sensing* 27(14), 3025–3033.
14. Companion papers of this programme: A (*Rainfall or drainage?*), D (*Building in the water's path*).
