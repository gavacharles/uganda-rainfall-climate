---
title: "Double exposure: flood-prone low ground and urban heat coincide in Kampala"
author: "Gava Charles"
date: "Draft, October 2026"
---

**Target journals:** *Urban Climate*; *Environmental Research Letters*; *Sustainable Cities and Society*; *Climate Risk Management*.

# Abstract

Heat and floods are usually studied apart. In Kampala, nights are warming at 0.40 °C per decade (NOAA CPC minimum temperature, 1981–2025, p < 0.001). Flood exposure is concentrated on the low valley floors beside drainage channels, where about 205,000 people live (Paper D). We ask whether the same people face both hazards. We combine:
- **heat:** MODIS night-time and daytime land-surface temperature (1 km, 2013–16 and 2022–25), with Landsat 30 m daytime surface temperature where available;
- **flood ground:** height above the nearest drain from a 30 m terrain model, together with OpenStreetMap channels;
- **people:** JRC GHS-POP 2020.

Of residents on flood-prone low ground, 53% also live in the warmest fifth of night-time surfaces, against 29% of residents on the hills (people-weighted odds ratio 2.7). About 108,000 people face both hazards. Low ground is 0.33 °C warmer at night than higher ground with the same built-up share and vegetation (95% CI 0.25–0.41, 2 km block-clustered errors). This holds in every built-up quintile, with gaps of 0.3–0.5 °C. Night-time surface temperature rose about 0.8 °C across the city between 2013–16 and 2022–25.

The double exposure falls on the central valleys: Nakivubo, the Lubigi–Bwaise system and Nalukolongo. These are dense, low-cost neighbourhoods where small single-room dwellings dominate (Paper D) and where cooling options are scarce. Wetland restoration and tree planting along the channels would reduce both hazards at once.

# 1. Introduction

- Heat-health research in African cities is growing, and Kampala's nights are warming fastest of all its temperature measures: warm nights rose from about 22 to 60 a year between 1981–95 and 2011–25 (climate report).
- Flood studies, including this programme (Papers A, D, 1), show exposure concentrated on valley floors where wetland has been built over.
- Valley floors could plausibly be cooler, since they are wetter, lower and close to water. Or they could be hotter, since they are dense, built-up and enclosed by hills that trap still night air. Which holds for Kampala is an empirical question that has not been tested.
- **Gap and contribution:** the first city-wide test of whether Kampala's flood-exposed population also faces the most heat, using open satellite data, with controls for density and vegetation.

# 2. Data and methods

| Layer | Source |
|---|---|
| Night and day surface temperature | NASA MODIS MOD11A2 (8-day, 1 km), median of all clear observations 2013–16 and 2022–25 |
| Daytime surface temperature, 30 m | Landsat 8/9 Collection 2 ST_B10, dry-season medians (about 59% of the area: ST is unavailable where the ASTER emissivity input is missing) |
| Vegetation | Landsat NDVI, dry-season median 2022–25 |
| Flood-prone low ground | HAND < 2 m within 150 m of a flowing channel; hills are HAND ≥ 10 m |
| Population, built-up | JRC GHS-POP and GHS-BUILT R2023A, 2020 |

Night-time surface temperature (about 22:30 local) is the primary heat measure, because it captures the urban heat retained overnight that drives heat stress. "Hot" means the warmest 20% of populated cells (≥ 19.96 °C). Open water and 1 km of lake shore are excluded, since the lake keeps the shore warm at night.

Analysis:
- people-weighted shares and odds ratio of heat given flood exposure;
- weighted least squares of night temperature on low ground, built-up share and NDVI, with errors clustered by 2 km block;
- night temperature by built-up quintile, low ground versus higher ground.

# 3. Results

**3.1 The same people.**

| | All residents | Flood-prone low ground | Hills |
|---|---|---|---|
| Share in the warmest 20% of nights | 31% | **53%** | 29% |
| Mean night surface temperature (°C) | | 19.8 | 19.4 |
| Mean day surface temperature, MODIS (°C) | | 32.6 | 31.5 |

People-weighted odds ratio of heat given flood exposure: 2.7. Residents facing both: about 108,000 (3% of the study area's 3.6 million).

**3.2 Not just density.** Controlling for built-up share and vegetation, low ground is 0.33 °C warmer at night (95% CI 0.25–0.41; R² = 0.20). Within each built-up quintile, low ground is 0.3–0.5 °C warmer at night than higher ground (Fig. kd35a). This is consistent with cool night air pooling in valleys being outweighed by dense construction and still air in the enclosed valley floors.

**3.3 Warming nights.** Night-time surface temperature rose about 0.8 °C between 2013–16 and 2022–25, both on low ground (+0.74 °C) and on the hills (+0.81 °C). The double exposure is therefore not easing.

**3.4 Where.** The warmest nights form a heat dome over the central city. The double-exposure cells (white rings in Fig. kd36) follow the central valleys of Nakivubo and the Lubigi–Bwaise–Kalerwe system, and the Nalukolongo and Kinawataka channels.

# 4. Discussion

- **Compound risk.** Floods and heat strike the same neighbourhoods. They are low-income and densely built, with small, often single-room dwellings (Paper D) that are poorly ventilated and cannot be cooled. Heat-health and flood programmes should share a target map.
- **Co-benefits.** Restoring vegetated channel corridors and protecting the remaining valley-floor wetland (Paper 1) would add flood storage and cool the night-time valley floor. NDVI's strong cooling coefficient (about −0.5 °C per 0.1 NDVI at night, and much more in the day) quantifies the gain.
- **Limitations:**
  - surface temperature is not air temperature;
  - MODIS at 1 km blurs narrow valleys;
  - Landsat 30 m covers only part of the city, and its daytime surface temperature shows no low/high-ground difference;
  - GHS-POP is modelled population.

  Low-cost air-temperature loggers along a valley-to-ridge transect would test the night-air result directly.

# 5. Conclusion

Kampala's flood-prone low ground is also where its nights are warmest. More than half of the people who live where floods go are in the hottest fifth of the city at night, nearly twice the rate on the hills. Treating the channel corridors as green, cooler, wetter infrastructure addresses both hazards.

# Figures

- kd35: a, night temperature by built-up quintile, low vs higher ground; b, residents facing heat, flood or both
- kd36: map of night-time surface temperature with channels and double-exposure cells

# References (to complete)

- Papers A, D, 1 of this programme; the Uganda climate report (warm-nights analysis).
- NASA MODIS MOD11A2 v061; USGS Landsat Collection 2 Surface Temperature; JRC GHSL R2023A.
