---
title: "Kampala drainage and wetlands: research programme"
author: "Gava Charles"
date: "12 October 2026"
---

# Purpose

This programme turns the Kampala drainage and wetlands study into six papers and one open tool. They all share one open-data base: OpenStreetMap drains, culverts and waste points; Microsoft building footprints; JRC GHSL built-up and population layers; Copernicus 30 m DEM; Sentinel-1, Sentinel-2 and Landsat imagery; and CHIRPS and NASA POWER rainfall. Each paper answers one question. Together they argue that **Kampala's floods are increasingly a drainage-capacity and encroachment problem rather than a rainfall problem, and that open data can show where the next hotspots are forming and help the city maintain its channels.**

The two papers already drafted in this repository (five-city urban flooding; Uganda growing seasons) stay separate. Paper A builds directly on the five-city paper.

| | Working title | Core question | Status | Target journals (Q1) |
|---|---|---|---|---|
| A | Rainfall or drainage? Falling flood-triggering rainfall and migrating flood hotspots in Kampala, 2000-2026 | Does it now take less rain to flood Kampala, and where will the next hotspots form? | Analysis started; needs the flood catalogue (D0) | *Journal of Flood Risk Management*; *Natural Hazards and Earth System Sciences*; *Sustainable Cities and Society* |
| B | Cloud-proof tracking of urban wetland encroachment with Sentinel-1 radar: Kampala 2017-2026 | Can free radar detect new building on valley floors every year, regardless of cloud? | First radar change maps running | *Int. J. Applied Earth Observation and Geoinformation*; *ISPRS J. Photogrammetry & Remote Sensing* |
| C | Waste, culverts and floods: quantifying the solid-waste blockage chain from open data | Do culverts downstream of dumping sites coincide with reported flooding, city-wide? | Inventory built (1,553 waste points, 3,135 culverts) | *Waste Management*; *Science of the Total Environment*; *J. Environmental Management* |
| D | Moving into the water's path: population on Kampala's floodplains, 1975-2030 | Is population on low ground beside channels growing faster than the city? | Population data downloading | *Landscape and Urban Planning*; *Environmental Research Letters*; *Cities*; *Habitat International* |
| E | Satellites as drainage inspectors: Sentinel-2 monitoring of channel clogging and clearing | Can 10 m imagery detect vegetation/silt choking wide channels and the effect of desilting? | Method coded; run pending | *Urban Water Journal*; *Remote Sensing*; *Int. J. Applied Earth Observation and Geoinformation* |
| D0 | A dated, geocoded catalogue of reported floods in Kampala, 2007-2026 (data paper) | A dated, geocoded, open record of floods | Drafted: 22 events (A 11, B 7, C 4), 51 place records; `kampala_flood_catalogue_paper.md` | *Scientific Data*; *Data in Brief* |
| T | An open-data drainage maintenance dashboard for Kampala (software paper) | A working tool: priority map, alerts, field reports | To build after A-C layers stabilise | *Environmental Modelling & Software*; *SoftwareX* |

# Status after first results (12 October 2026)

| Paper | Result so far | Decision | Planning-journal target |
|---|---|---|---|
| A | Hotspot index AUC 0.73; 1975-2000 score predicts 2000-2020 encroachment (AUC 0.79); rainfall extremes flat; falling-threshold test pending catalogue | Main paper; draft in `kampala_drainage_paperA.md` | *Landscape and Urban Planning*, *Cities* |
| B | Radar candidates: ~30% confirmed new building, ~1% of all new building detected | Not a standalone paper. Fold into A as a supporting method, or a short note on what free radar can and cannot do in an informal city | *Environment and Planning B* (short note) |
| C | Dumping near culverts: 19% vs 12% at hotspots raw, but no effect after controls (OR 0.87, 0.51-1.59) | **Dropped as a separate paper (no fieldwork possible).** Reported in Paper A as a tested-but-unsupported pathway: dumping does not predict hotspots once density is controlled | *Habitat International*, *Cities* |
| D | Exposure 36k (1975) to 205k (2020); exposure now growing fastest on the fringe; smaller building grain on low ground | **Drafted with land-tenure angle:** `kampala_drainage_paperD.md` | *Habitat International*, *Land Use Policy* |
| E | Method coded; Sentinel-2 run deferred (~10 GB) | **Parked** (needs KCCA desilting dates) | *Urban Water Journal* |
| D0 | GDELT (2017-2026) + verified reports (2007-2026); 2021-24 reporting gap | Drafted, `kampala_flood_catalogue_paper.md` | *Scientific Data* / *Data in Brief* |
| T | Kampala Drain Watch live (gavacharles.github.io/kampala-drain-watch) | **Parked** as a paper; the tool stays live | *Environment and Planning B* (urban analytics & code) |

Each planning-journal submission needs a policy and institutional section: the National Environment (Wetlands) Regulations, the KCCA drainage master plan (2016, partly implemented), NDP IV, and ideally interviews with KCCA and NEMA engineers.

# Follow-on papers (October 2026)

| # | Paper | Key result | File |
|---|---|---|---|
| 1 | The lost sponge: valley-floor flood storage 1975-2030 | 8.5 Mm³ storage paved over; living wetland sponge -73% to -91% in Kinawataka and Nalukolongo; most systems went from holding to failing a 10-yr storm | `kampala_sponge_paper1.md` |
| 3 | Cut off by water: hospital and school access | 1 m flood: 36,000 dry-home residents lose all routes to hospital, 131,000 see trips double; Busega A5 and Lubigi roads most critical | `kampala_access_paper3.md` |
| 4 | The cost of a blocked drain | EAD US$3.0m clean vs US$20.3m silted; maintenance worth ~US$17m/yr; Nakivubo and lower Lubigi most valuable to keep clear | `kampala_damage_paper4.md` |
| 5 | Double exposure: heat and flood | 53% of low-ground residents in the warmest 20% of nights vs 29% on hills (OR 2.7); low ground +0.33 °C at night after controls | `kampala_heat_flood_paper5.md` |
| 6 | Design-basis drift | Channels sized for 1990 now get +17% (median) 10-yr flow; 91% of length overloaded >20% under 2041-70 SSP5-8.5; drift is a fringe, not a hotspot, phenomenon | `kampala_capacity_paper6.md` |
| 7 | The next Kampalas: regional cities | Low ground filling 1.3-2x faster than the city in Mbarara, Gulu, Mbale, Jinja, Arua (2020-30) | `uganda_cities_paper7.md` |
| 2 | The lost free treatment plant: wetland loss and Inner Murchison Bay, 1986-2026 (satellite only, no NWSC data) | Drafted: bay-draining wetland -51% (1,200 to 587 ha); outlet/lake turbidity ratio 1.14 to 1.51; +5.3% per 100 ha lost (p = 0.019); `kampala_bay_paper2.md` | *Science of the Total Environment*; *J. Great Lakes Research* |

# Shared foundations (done)

- 12,453 channel segments (≈ 900 km) with upstream area, paving 1990/2020, culverts, bridges, waste points, markets, buildings within 15 m, floodplain buildings, wetland left, valley-floor building ([`src/kd_network.py`](../src/kd_network.py)).
- A current maintenance-priority index and an emerging-risk score. Validation against 43 reported hotspots: AUC 0.73 (95% block-bootstrap CI 0.57-0.89), 0.63 within dense areas. Weights fitted to the hotspots do not transfer between parts of the city (spatial-CV AUC 0.52-0.59).
- Rainfall and temperature for Greater Kampala 1981-2025 ([`src/kd_rain.py`](../src/kd_rain.py)). Annual rain is +15% (CHIRPS, p = 0.05); the wettest day of the year shows no trend; nights are 1.2 °C warmer. ARC2 shows a step change after 2019 that CHIRPS does not, so ARC2 trends are not used.
- Satellite layers: Landsat 1986-2025, Impact Observatory land cover 2017-2023, Sentinel-1 2017-2026, Sentinel-2 2026 ([`src/kd_satellite.py`](../src/kd_satellite.py), [`src/kd_radar.py`](../src/kd_radar.py)).
- Figures, area pages and animations: `figures/kampala_drainage/`.

# Paper A: Rainfall or drainage? (questions 3 + 6 combined)

**Hypotheses.**
H1: the area-average rainfall on flood days has fallen since 2000, meaning floods now occur at lower rain, while rainfall extremes have not risen (CHIRPS: wettest day −1.0 mm/decade, p = 0.24).
H2: today's reported hotspots sit in long-built areas; the emerging-risk score, computed only from data up to 2010, predicts where hotspots first reported after 2015 appear.

**Data.** Flood catalogue D0 (target ≥ 80 dated events, 2000-2026). CHIRPS daily (0.05° station-blended product for event days) and NASA POWER hourly. The segment inventory, with GHSL 1990/2000/2010 inputs re-run to make an "as of 2010" emerging-risk score.

**Methods.**
1. For each event, 1-, 3- and 7-day rain and antecedent wetness; compare with all wet days (percentile).
2. Trend in the event-rain percentile and in the rain needed to flood, using a logistic exceedance model with a time term. Control for reporting growth by using event-size classes (deaths, roads closed) and a placebo test on non-flood heavy-rain days.
3. Temporal hold-out: build the risk scores with pre-2010 land cover only, then test against hotspots first reported in 2015-2026 (AUC, hit rate within 400 m vs random channel points).

**Key figures.** kd02 (flood days vs rain distribution), kd05 (emerging risk), kd12 (now vs emerging), kd13 area pages, plus new ones: event-rain percentile through time, and hold-out validation.

**Novelty.** Rainfall thresholds for urban flood warnings have been derived from news and social media (e.g. Alexandria; Young et al.), but we found no study testing whether the triggering threshold has **fallen over time** as a signature of drainage decline, nor one using it to forecast hotspot migration in an African city.

**Risks.** Reporting bias (more news coverage now); satellite rain smooths storms (on 29-31 Oct 2025 the Makerere gauge recorded 63 mm vs 21 mm from CHIRPS). Mitigation: event-size classes, placebo days, sensitivity to the rain product, and any gauge data obtainable from UNMA/Makerere.

# Paper B: Radar tracking of wetland encroachment

**Question.** Can yearly Sentinel-1 composites detect new structures on valley floors (HAND < 3 m), cloud-free, and how much wetland/floodplain has been built over in 2017-2026, by channel system?

**Methods.** Yearly median VV/VH on one orbit track; new structure = VV up ≥ 3 dB vs 2017-18, now above −6 dB, and persistent into the next year. Accuracy assessment against Microsoft footprints (2023), Impact Observatory land cover 2017-2023, and a stratified sample checked on very-high-resolution imagery. Compare with Landsat/optical encroachment estimates (e.g. the 1986-2016 Landsat study reporting ~73% wetland loss in Kampala-Wakiso).

**Figures.** kd17 (radar change map), kd18 (panels), kd_a4 (animation), kd10 (radar after the 11 Oct 2026 storm: why radar cannot catch flash floods but can track encroachment).

**Novelty.** Published Kampala wetland-loss work uses optical snapshots (Landsat, aerial photos). We found no Sentinel-1 time-series encroachment study for Kampala; the operational angle (yearly alerts per channel) is new.

# Paper C: Waste, culverts and floods

**Question.** City-wide, are culverts and channel reaches downstream of mapped dumping sites more often reported as flooding points, after controlling for runoff load and density?

**Data and methods.** OSM waste points (1,325 disposal points, 71 landfills); culverts (3,135); markets; uncollected-waste load per catchment = GHS-POP × per-capita generation × (1 − collection coverage). KCCA states 730,000 t/yr is generated and about half collected. Matched comparison of culverts with and without upstream dumping; hotspot association with spatial block bootstrap. A small field or photo audit at about 30 culverts to validate the blockage proxy.

**Novelty.** Olsson, Mugume & Sörensen (2025, *Water Sci. Technol.*) modelled blockage at three Lubigi culverts, finding flood volumes up by 40-105%. We found no city-wide, open-data quantification linking dumping sites, culverts and reported floods.

# Paper D: Population moving into the water's path

**Question.** How many people live on low ground beside Kampala's channels (HAND < 2 m, within 150 m), 1975-2030, and is that growing faster than the city overall?

**Methods.** JRC GHS-POP 1975-2030 (2025/2030 projected); exposure by channel system and division; decomposition of exposure growth into city growth vs a shift toward low ground; sensitivity to the HAND threshold and buffer; cross-check with WorldPop 2000-2020.

**Figures.** kd15 (people on low ground), kd_a2 (animation), kd14 / kd_a1 (valley floors built).

**Novelty.** Earlier Kampala work simulated urban growth and flood exposure for the upper Lubigi to 2025-2030 (Pérez-Molina, Sliuzas & Flacke). We found no city-wide, observed 1975-2030 channel-level exposure series.

# Paper E: Satellites as drainage inspectors

**Question.** Can monthly Sentinel-2 vegetation and water indices inside wide channels (≥ 8 m: Nakivubo, Lubigi, Kinawataka, Nalukolongo) detect clogging and clearing, and does clogging precede reported floods?

**Methods.** Monthly NDVI/NDWI along centrelines 2017-2026 (code in `kd_satellite.py channels`); change-point detection for clearing events; validation against KCCA desilting records and contract dates (to request) and Google Earth historical imagery.

**Novelty.** Sentinel-2 has been used for river and floodplain vegetation and agricultural ditches (e.g. Rhine/Meuse floodplains). We found no application to urban stormwater channels in Africa. Narrow channels (< 10 m) are a resolution limit, to be stated plainly.

# D0: Flood catalogue (data paper)

Systematic search of Daily Monitor, New Vision, The Observer, NTV, Nile Post, ChimpReports, Uganda Radio Network, ReliefWeb, FloodList, Uganda Red Cross and KCCA statements, 2000-2026. Record date, time, places, channel, deaths, roads closed, source. Geocode with an uncertainty radius. Publish openly; the dashboard's field reports extend it.

# T: The tool

Web dashboard: segment priority and emerging risk; radar encroachment alerts; rain forecast trigger; field reporting of blockages, dumping and floods (feeds D0 and Papers A, C, E). Paper in *Environmental Modelling & Software* or *SoftwareX* once in use.

# Order of work

1. D0 flood catalogue: unlocks A and C, and the threshold analysis.
2. B radar and D population: data mostly in hand; quickest to submit.
3. A main paper, once D0 has ≥ 80 events.
4. C waste-blockage (needs the small validation audit).
5. E channel monitoring (needs KCCA maintenance dates).
6. T dashboard, built alongside, then the software paper.

# Literature checked (Oct 2026, not exhaustive)

- Wetland encroachment, Kampala-Wakiso, Landsat 1986-2016: PMC10521074.
- Spatiotemporal encroachment on wetlands, Kampala (Stellenbosch thesis).
- Olsson, Mugume & Sörensen (2025), culvert blockage in upper Lubigi, *Water Science & Technology*.
- KCCA KIIDP2 ToR, Nakivubo sub-surface storm-water network (solid waste and drainage).
- Young, Bhattacharya & Zevenbergen: rainfall thresholds from news and social media, Alexandria.
- Pérez-Molina, Sliuzas & Flacke: simulating urban growth in Kampala and flood risk.
- UBOS rapid assessment of the March 2025 GKMA floods.
