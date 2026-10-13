---
title: "Rainfall or drainage? Open-data evidence on what drives Kampala's flood hotspots and where the next ones are forming"
author: "Gava Charles"
date: "Draft, October 2026"
---

**Target journals:** *Landscape and Urban Planning*; *Cities*; *Sustainable Cities and Society* (planning framing). Hydrology alternative: *Journal of Flood Risk Management*.

# Abstract

Kampala's floods are often blamed on heavier rain. We test that claim with open data alone. For 6,914 drainage-channel stretches across Greater Kampala (469 km of flowing channel), we combine OpenStreetMap drains, culverts and dump sites, Microsoft building footprints, JRC GHSL built-up and population layers (1975–2030), a 30 m terrain model and satellite rainfall (1981–2025). Kampala's rainfall extremes show no trend: the wettest day of the year changed by −1.0 mm per decade (p = 0.24) and the wettest three days by +0.7 mm per decade (p = 0.46). Annual totals rose by about 15% (p = 0.05). Reported flood days are often ordinary rain days: on five of seven well-dated events, satellite rain that day was below the 92nd percentile of wet days, and on two it was below the 22nd. An index of six present-day drainage pressures separates channels at 45 reported flood hotspots from other channels (AUC 0.73, 95% CI 0.58–0.89, spatial block bootstrap). The strongest pressures are buildings on low ground, buildings inside the 15 m channel reserve, culverts and bridges, and the loss of wetland. Upstream paving, by contrast, does not distinguish today's hotspots, which sit in long-built areas. A score built only from 1975–2000 change predicts where valley floors were built over in 2000–2020 (AUC 0.79, 95% CI 0.71–0.87), against 0.58 for the naive "already-built areas grow" rule. This identifies the fast-growing fringe as where the next hotspots are forming. Since 2000, the number of people on low ground beside channels has grown in step with the city, reaching about 205,000 in 2020. **[Pending: the 2017–2026 test of whether the rain needed to cause a reported flood has fallen, from the news-based flood catalogue.]** The evidence points to drainage capacity and encroachment, not rainfall, as the lever planners control. We release the channel inventory and an open maintenance dashboard.

# 1. Introduction

- Kampala floods most rainy seasons. Recent events include 26 March 2025 (seven deaths), 31 October 2025 (three deaths in the Nakivubo/Kisenyi channel), and 10–11 October 2026 (Lubigi, Kinawataka). Public debate swings between "climate change" and "encroachment and garbage".
- KCCA lists 68 flood hotspots. The Kampala Drainage Master Plan was adopted in 2016 but only partly implemented. Encroachment on wetlands is documented (about 73% wetland loss in Kampala–Wakiso, 1986–2016).
- Gap: no city-wide, channel-level, reproducible test of what separates flood hotspots, and no forward-looking map of where new ones will form. Earlier work modelled single catchments (Upper Lubigi) or simulated growth scenarios.
- Contribution:
  1. an open channel-level inventory of drainage pressures;
  2. a test of rainfall vs drainage explanations;
  3. a temporally validated early-warning score for emerging hotspots;
  4. an open tool for maintenance.

# 2. Study area and data

Greater Kampala core (32.45–32.72°E, 0.20–0.42°N): six main channel systems (Lubigi, Nakivubo, Kinawataka, Nalukolongo, Kansanga, Walufumbe) draining to Lake Victoria through former papyrus wetlands.

| Layer | Source | Use |
|---|---|---|
| Channels, culverts, bridges, dump sites, markets | OpenStreetMap (16,575 waterways; 3,135 culverts; 1,553 waste points) | Network, constrictions, waste pressure |
| Buildings | Microsoft Global ML Building Footprints (537,408 in the study box) | Encroachment on the 15 m reserve; buildings on low ground |
| Built-up 1975–2030 | JRC GHSL GHS-BUILT-S R2023A | Upstream paving, valley-floor building |
| Population 1975–2030 | JRC GHS-POP R2023A | Exposure |
| Terrain | Copernicus GLO-30 DEM | Flow routing (D8), upstream area, height above nearest drainage (HAND) |
| Land cover | ESA WorldCover 2021; Impact Observatory 2017–2023 | Wetland remaining; valley-floor change |
| Rain and temperature | CHIRPS v2.0 and ARC2 (daily, 1981–2025); NASA POWER hourly (2001–2026); NOAA CPC | Trends; flood-day rainfall |
| Radar | Sentinel-1 RTC (2017–2026) | After-storm water; new-structure leads |
| Flood record | 45 hotspots (KCCA/NEMA lists, news, local reports); dated events (news, GDELT) | Validation |

# 3. Methods

**3.1 Channel inventory.** Waterways were cut into segments of 200 m or less (12,453 in total). For each segment we computed:
- upstream area (D8 routing on the conditioned DEM);
- upstream built-up share in 1990 and 2020, and a runoff load (area × C, with C = 0.25 + 0.65 × built share);
- valley-floor built share (HAND < 3 m within about 250 m) in 1990 and 2020;
- wetland share within 500 m;
- buildings within 15 m of the centreline (the channel reserve);
- buildings on low ground (HAND < 2 m) within 150 m;
- dump sites within 100 m and markets within 300 m;
- culverts within 25 m and road bridges.

Analysis uses the 6,914 segments draining 0.25 km² or more.

**3.2 Maintenance-priority and emerging-risk scores.** Each pressure was converted to a percentile rank. The priority index is the equal-weight mean of six present-day pressures. The emerging-risk score is the mean rank of upstream runoff growth and valley-floor building since 1990.

Equal weights were chosen over fitted weights because logistic weights fitted to the hotspots did not transfer across space (spatial cross-validated AUC 0.52–0.59). Hotspots were matched to segments within 400 m (positions ±500 m). AUC uncertainty comes from a 2 km block bootstrap (500 resamples). We repeat the test within the denser half of channels to check that the index does more than flag density.

**3.3 Rainfall.** Annual indices (totals, days with 20 mm or more, wettest day, wettest three days) were computed for the Greater Kampala mean. Trends use Sen's slope and Mann–Kendall. ARC2 shows a step change after 2019 not seen in CHIRPS, so we report CHIRPS trends only. For dated flood events we compute same-day, three-day and seven-day rain and their percentile among 1991–2020 wet days.

**3.4 Temporal hold-out.** To test whether early change predicts later encroachment, we built the emerging-risk score from 1975–2000 data only. We then asked whether it identifies the top quartile of segments by valley-floor building added in 2000–2020, among segments with unbuilt valley floor left in 2000.

**3.5 Falling-threshold test (pending catalogue).** For every day from 2017 to 2026 we fit a logistic model of whether a flood was reported, with three sets of predictors:
- same-day and three-day rain (CHIRPS; NASA POWER peak-hour rain as a sensitivity);
- a linear time trend;
- monthly news coverage of Kampala (GDELT volume), to absorb growth in reporting.

A trend odds ratio above 1 at fixed rain means the same rain floods more often. HAC errors use 7 lags.

**3.6 Exposure.** Residents on low ground (HAND < 2 m within 150 m of a flowing channel) for 1975–2030, decomposed into city growth at a constant share and a shift toward low ground.

# 4. Results

**4.1 Rainfall has not intensified; floods occur on ordinary rain.**

| Index (Greater Kampala, CHIRPS) | 1981–95 mean | 2011–25 mean | Sen slope / decade | p |
|---|---|---|---|---|
| Annual rain (mm) | 1,223 | 1,400 | +46.8 | 0.05 |
| Days ≥ 20 mm | 4.4 | 6.1 | +0.27 | 0.41 |
| Wettest day (mm) | 33.0 | 30.0 | −1.0 | 0.24 |
| Wettest 3 days (mm) | 52.3 | 54.7 | +0.7 | 0.46 |

Satellite rain on dated flood days ranged from 2.6 mm (6 March 2026, the 19th percentile of wet days) to 18.7 mm (14 March 2023, the 96th). Satellite products smooth local storms: on 29–31 October 2025 the Makerere gauge recorded 63 mm against 21 mm in CHIRPS. Even allowing for this, several floods followed unremarkable area-average rain (Fig. kd02).

Nights warmed by 0.40 °C per decade (p < 0.001); daytime maxima showed no trend. Hourly reanalysis suggests rain intensity rises steeply with humidity (32–44% per °C of dew point), but MERRA-2 hourly rain is a model product and we do not rely on it.

**4.2 What sets hotspots apart.** The priority index separates hotspot channels from others (AUC 0.73, 95% CI 0.58–0.89; 0.63 within the denser half of channels).

| Pressure | Hotspots (median pct) | Other channels | AUC alone |
|---|---|---|---|
| Buildings on low ground ≤ 150 m | 75 | 36 | 0.65 |
| Buildings in the 15 m reserve | 73 | 36 | 0.64 |
| Culverts and bridges | 68 | 33 | 0.60 |
| Little wetland left | 66 | 46 | 0.68 |
| Dump sites and markets | 41 | 41 | 0.61 |
| Runoff load (area × paving) | 39 | 50 | 0.50 |
| Runoff growth since 1990 | 21 | 55 | 0.23 |

In the top-20% priority segments, 60% of hotspots fall within 400 m, against 47% of random channel points. Of 469 km of flowing channel:
- 138 km rank high now and are still worsening;
- 44 km rank high but are stable;
- 100 km show rising risk that is not yet high.

**4.3 Where the next hotspots are forming.** The early-change score predicts later valley-floor building (AUC 0.79, 95% CI 0.71–0.87; Spearman ρ = 0.43). Channels in the top quintile gained 6.5 percentage points of built valley floor between 2000 and 2020, against 1.6 in the bottom quintile (Fig. kd23). Today's hotspots have low runoff growth because they were built over before 1990. The emerging-risk map (Fig. kd05) puts the next generation on the northern and eastern fringe (Kira, Nansana, Namugongo) and the Kinawataka and Kansanga headwaters.

**4.4 People in the water's path.** People on low ground beside channels numbered 35,600 in 1975, 64,000 in 1990, 205,000 in 2020, and are projected at 247,000 in 2030. The shift toward low ground happened in 1975–2000: 13,000 people beyond what city growth explains. Since 2000, exposure has grown in step with the city (Fig. kd25).

**4.5 Waste and culverts: a tested but unsupported pathway.** Culverts with a mapped dump site within 250 m upstream were more often near a reported hotspot (19% vs 12%). However, the effect disappears once upstream paving, catchment size and building density are controlled (odds ratio 0.87 per SD, 95% CI 0.51–1.59; 1,163 culverts). Dumping clusters where the city is dense and paved, so open data cannot separate its effect. Uncollected waste is still large: an estimated 53,000 t per year in the Lubigi catchment and 29,000 t in Nakivubo (2020; 0.55 kg/person/day, about half collected). Testing blockage directly needs field inspection of culverts, which we flag as future work for KCCA.

**4.6 Satellite limits.** A Sentinel-1 pass about 13 hours after the 11 October 2026 storm showed no extensive standing water (0.18% of the area looked newly wet). Kampala's floods rise and drain within hours, faster than any satellite revisit.

Radar change detection of new structures on open land is only exploratory:
- about 30% of its detections are confirmed by 10 m land cover;
- it captures about 1% of all new building.

It is useful for inspection leads, not for counting encroachment.

**4.7 Falling flood thresholds.** **[Pending: trend odds ratio, CI and Kendall τ from kd_threshold.py once the GDELT catalogue is complete.]**

# 5. Discussion: what this means for planning

- **Lever:** the pressures that separate hotspots (building in the reserve and on the floodplain, constrictions, lost wetland) are planning and enforcement variables, not climate variables. These include the National Environment (Wetlands) Regulations, KCCA physical-planning controls and the 2016 Drainage Master Plan.
- **Prioritising:** an equal-weight, transparent index beats a fitted model when flood records are sparse and biased toward the city centre.
- **Prevention:** the hold-out shows that encroachment can be anticipated 20 years ahead from open data. Development control on emerging-risk channels now is cheaper than retrofitting.
- **Monitoring:** satellites track slow change. Flood detection needs gauges, culvert water-level sensors and resident reports (the open dashboard collects these).
- **Limitations:**
  - hotspot positions are approximate and the list is centre-biased;
  - OSM completeness varies;
  - GHSL 2025–2030 values are projections;
  - satellite rainfall underestimates local storms;
  - there is no direct observation of channel blockage;
  - the waste–culvert link could not be isolated without field inspection (Section 4.5).

# 6. Conclusion

[To finalise after 4.6.]

# Data and code availability

Code: `src/kd_*.py`. Figures: `figures/kampala_drainage/`. Dashboard: Kampala Drain Watch (claude.ai artifact).

# Figures

kd04 priority map · kd05 emerging risk · kd06 hotspot drivers · kd12 priority vs emerging · kd02 flood-day rain · kd23 hold-out · kd25 exposure · kd26 threshold trend (pending) · kd13 area pages (supplement) · kd10 radar after the storm.
