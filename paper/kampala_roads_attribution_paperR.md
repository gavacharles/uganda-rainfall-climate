---
title: "Silt, not storms: attributing flood disruption of an African city's road network to drainage neglect, land-use change, floodplain encroachment and climate change"
author: "Gava Charles"
date: "Draft, October 2026"
---

**Target journals:** *Transportation Research Part D*; *Natural Hazards and Earth System Sciences*; *Journal of Transport Geography*; *Sustainable Cities and Society*.

# Abstract

Flooded roads are among the most visible costs of urban flooding in African cities, and they are routinely blamed on heavier rain. We ask what actually drives road flood disruption in Kampala, Uganda, and how much each driver contributes. We combine:
- every drivable road in OpenStreetMap (6,725 km, split into 88,056 pieces of 100 m or less);
- a channel-by-channel screening flood model for 6,914 drainage stretches, using a terrain-based rating curve and gauge-corrected design storms;
- a road network model of 3.6 million residents' access to the city centre and to hospitals.

Four drivers are switched on and off in a full factorial design of 16 scenarios:
- **paving:** upstream impervious cover, 1990 vs 2020;
- **siltation:** channels clean vs 30% of depth lost to silt and vegetation;
- **floodplain encroachment:** building footprints blocking floodplain flow;
- **climate change:** 2041–70 SSP5-8.5 design storms.

Shapley values divide the change between drivers.

Results:
1. **Road flooding has grown about 30-fold since 1990.** In an average year, 163 km of road becomes impassable (water at least 0.3 m deep), against about 6 km in the 1990 baseline. About 118,000 people are cut off from the city centre, against about 4,600.
2. **Siltation causes most of it:** 83% of the increase in impassable road and 86% of the increase in people cut off. Paving contributes 15% and 12%, and floodplain encroachment about 2%.
3. **Even an ordinary 2-year storm closes the city when channels are silted.** It puts 199 km of road under water and cuts off 149,000 people, against 4 km and 1,500 people with clean channels. Of 636 road–channel crossings without a bridge, 387 close in a 2-year storm when channels are silted and 13 when they are clean.
4. **Climate change matters less than maintenance, but it matters more for a well-kept system.** By the 2050s, climate change adds 9% to road flooding if channels stay silted. With clean channels it nearly doubles expected disruption (from 30 to 57 km a year), because silt otherwise masks it.
5. **The result is robust.** Siltation remains the largest driver whether channels lose 10% (71–75% of the change) or 50% (87–89%) of their depth.
6. **Much of today's exposure was built on former wetland.** 68% of the road that floods in a 10-year storm sits on valley floor that was wetland or bush in 1986. Urban road on low ground beside channels grew from 141 km (1975) to 315 km (2020).

The model reproduces all eight road floods reported in the news, 2007–2026. We rank the crossings where desilting would avoid the most closures: Jinja Road over the Nakivubo, Kibuye–Natete Road on the Nalukolongo, and the Northern Bypass, Gayaza Road and Bombo Road at Bwaise–Kalerwe. Kampala's road flooding is mainly a maintenance problem, and the cheapest adaptation is a shovel.

# 1. Introduction

- **The problem.** Flooded roads cut people off from work, markets, schools and hospitals, and in Kampala they are a fixture of every rainy season. Public debate tends to attribute them to heavier rain and climate change. Engineers and residents point instead to blocked drains, undersized culverts and building in the valleys. Both views are plausible, and neither has been quantified.
- **What is known.**
  - Global studies estimate road exposure and damage from river and surface floods (Koks et al. 2019).
  - City studies model the effect of flooded links on travel and emergency access (Yin et al. 2016; Green et al. 2017; Coles et al. 2017; Pregnolato et al. 2017).
  - In Kampala, a World Bank analysis estimated about 11 km of main roads flooded in a 50-year event in the inner city, with knock-on loss of access to health care (Hallegatte et al. 2019).
  - A recent traffic study of 22 links found overtopping from the 5-year storm and near-doubling of travel times under full closure (TRID record 2724562).
- **The gap.** None of these studies separates the drivers. Road flood risk is usually presented as a single state, sometimes compared with a future climate. To our knowledge there is no published decomposition of urban road flood disruption into maintenance, land use, encroachment and climate, and none for an African city. That decomposition decides where adaptation money should go.
- **Contributions:**
  1. a city-wide, road-by-road flood depth model for every drivable road in Kampala, checked against reported road floods;
  2. a factorial attribution with Shapley values, for road flooding and for network access;
  3. a ranked list of crossings where desilting avoids the most disruption;
  4. a history of how much of today's exposed road was built on former wetland.

# 2. Data and methods

## 2.1 Roads

All OpenStreetMap drivable roads (motorway to service lanes) in the Greater Kampala core (32.45–32.72° E, 0.20–0.42° N) were cut into pieces of 100 m or less (88,056 pieces, 6,725 km). For each piece:
- **class** (Table 1);
- **lowest HAND** (height above nearest drainage, Copernicus GLO-30) along the piece, sampled every 15 m;
- **nearest channel stretch** within 300 m;
- **crossing** where the piece intersects a channel; it counts as a culvert unless tagged as a bridge.

Bridges never flood. The Entebbe Expressway and its Southern Bypass spur, which opened in 2018 on embankments built after the DEM was acquired (2011–15), are also treated as never flooding. Their modelled ground-level depths are kept for sensitivity.

| Class | OSM tags | km |
|---|---|---|
| Highway | motorway, trunk | 147 |
| Main road | primary, secondary | 368 |
| Local through road | tertiary, unclassified | 1,039 |
| Residential street | residential, living street | 4,493 |
| Service lane | service | 678 |

## 2.2 Flood depth on roads

The hydraulic model is the screening model of Papers 4 and 6. For each of 6,914 channel stretches draining at least 0.25 km²:
- **Peak flows:** the rational method with gauge-corrected CHIRPS design storms (2–100-year), Kirpich time of concentration, Hack flow length and an areal reduction factor.
- **Channel size:** sized to carry the 1990 10-year flow (n = 0.025, width = 3 × depth).
- **Overbank stage:** solved on a HAND synthetic rating curve (Zheng et al. 2018) built from the 30 m cells within 200 m of the stretch, floodplain n = 0.06.

Depth on a road piece = stage above bank − lowest HAND of the piece. A road is impassable at depths of 0.3 m or more. At that depth cars stall, and the depth–disruption function of Pregnolato et al. (2017) reaches zero speed.

## 2.3 Four drivers, 16 scenarios

| Driver | Off (1990 baseline) | On |
|---|---|---|
| L, paving | Flows with 1990 upstream impervious cover (GHSL, calibrated to WorldCover) | 2020 impervious cover |
| S, siltation | Clean channel | 30% of depth lost, n = 0.035 (silt and vegetation) |
| E, encroachment | Open floodplain | Each floodplain cell conveys (1 − building footprint share) of its width (Microsoft footprints) |
| C, climate | Today's design storms | 2041–70 SSP5-8.5 intensities at each stretch's time of concentration |

All 16 combinations were run for six return periods.

## 2.4 Network impacts

- **Graph:** the road graph is built from every vertex of the road pieces, so that junctions at shared OpenStreetMap nodes connect, with congested urban speeds of 40, 30, 25, 20 and 15 km/h by class.
- **Population:** JRC GHS-POP 2020 at 100 m, 3.62 million people on the network, each 100 m cell attached to its nearest road node.
- **Per scenario and storm:** impassable pieces are removed, and we compute:
  - the people cut off from the city centre (any road node within 1 km of the Clock Tower) and from the nearest hospital (OSM);
  - the population-weighted extra travel time for those who can still reach them.
- **Expected annual values:** integrated over annual exceedance probability, with zero at T = 1.

## 2.5 Attribution

For a metric V and a set of drivers F, the Shapley value of driver i is the average of its marginal contribution V(S ∪ {i}) − V(S) over all subsets S of the other drivers (Shapley 1953). Shapley values add up exactly to the total change and do not depend on the order in which drivers are added. This matters here because the drivers interact strongly: silt amplifies the effect of paving and masks that of climate. We report two decompositions:
- **today:** L, S and E, from the 1990 baseline to today with silted channels;
- **2050s:** all four drivers.

## 2.6 Crossings and history

**Crossings.** The 636 road–channel crossings without a bridge were ranked by the closures that desilting would avoid: (annual closure probability, silted − clean) × the population whose fastest route to the centre runs through the crossing. That route count comes from the shortest-path tree from the centre.

**History.** Each road piece is dated by the first GHSL epoch (1975–2020) in which its 100 m cell was at least 15% built. It is also classified by its 1986 land cover from the machine-learning land-cover map (Paper 1, Section 3.4).

## 2.7 Validation

Eight road floods named in the flood catalogue (Paper D0, 2007–2026) were checked against the model. For each, we took the deepest modelled water on the named road within 1.5 km of the reported place.

# 3. Results

## 3.1 Where roads flood

| State | Impassable road, 2-year storm (km) | 10-year (km) | Average year (km) | People cut off from centre, average year |
|---|---|---|---|---|
| 1990 baseline | 0 | 0 | 6 | 4,600 |
| Today, channels clean | 4 | 109 | 30 | 19,800 |
| Today, channels silted | 199 | 251 | 163 | 117,800 |
| 2050s, clean | 18 | 170 | 57 | 38,900 |
| 2050s, silted | 223 | 269 | 179 | 125,100 |

Flooding concentrates on the Lubigi system (Bwaise, Kalerwe, the Northern Bypass), on the Nalukolongo (Kibuye–Natete), on the Nakivubo below the city centre, on the Kinawataka along Jinja Road, and on the southern streams crossed by Entebbe Road (Figs. kd46, kd48). In a 10-year storm with silted channels, the trip to the centre is on average 14 minutes longer, averaged over all residents. The figures for hospital access are almost identical.

## 3.2 Validation

| Reported road flood (catalogue) | Deepest water within 1.5 km, 10-year (clean → silted) | 2-year, silted |
|---|---|---|
| Hoima Road at Lubigi (11 Oct 2026) | 0.45 → 1.05 m | 0.80 m |
| Northern Bypass, Bwaise–Kalerwe (26 Mar 2025) | 1.10 → 2.80 m | 2.00 m |
| Bombo Road at Bwaise (26 Apr 2018) | 1.75 → 2.40 m | 2.10 m |
| Jinja Road at Kyambogo (14 Mar 2023; 18 Mar 2026) | 0.40 → 1.05 m | 0.85 m |
| Jinja Road at Banda | 0.35 → 0.70 m | 0.55 m |
| Entebbe Road, Namasuba (16 Nov 2007) | 1.05 → 2.80 m | 2.00 m |
| Mukwano Road (26 Mar 2025) | 0.20 → 1.73 m | 1.48 m |
| Kinawataka Road (17 Sep 2026) | 0.12 → 1.52 m | 1.17 m |

All eight reported roads are impassable in the silted state even in a 2-year storm, and six of eight in a 10-year storm with clean channels. This is consistent with the flood catalogue's finding that Kampala floods on ordinary rain.

## 3.3 Attribution

| Share of the change since 1990 (Shapley) | Paving | Siltation | Encroachment | Climate |
|---|---|---|---|---|
| Impassable road-km, today | 15% | **83%** | 2% | – |
| People cut off from centre, today | 12% | **86%** | 2.5% | – |
| People cut off from hospitals, today | 12% | **86%** | 2.5% | – |
| Extra travel time to centre, today | 13% | **86%** | 0% | – |
| Impassable road-km, 2050s | 15% | **74%** | 2% | 9% |
| People cut off from centre, 2050s | 12% | **78%** | 2% | 8% |

(Fig. kd50.) Siltation dominates every measure. Paving is the second driver: Kampala's flows have risen as its catchments were paved, and channels sized for 1990 now overflow in the 10-year storm even when clean. Climate change adds the least by the 2050s.

**The interaction matters.** With clean channels, climate change nearly doubles expected road disruption (30 → 57 km a year; 19,800 → 38,900 people cut off). With silted channels it adds only about 10%, because the system already fails in frequent storms. In other words, maintaining the drains is also what makes climate adaptation visible.

## 3.4 How much silt does it take?

| Channel depth lost | Siltation share (road-km / people cut off) | Paving share |
|---|---|---|
| 10% | 71% / 75% | 27% / 22% |
| 20% | 78% / 81% | 19% / 16% |
| 30% (main) | 83% / 86% | 15% / 12% |
| 50% | 87% / 89% | 12% / 9% |

(Fig. kd52.) Even a light silting, a tenth of the channel depth plus a vegetated bed, accounts for most of the change. The conclusion does not depend on the assumed silt level.

## 3.5 The crossings to clear first

Of 636 road–channel crossings without a bridge, 387 close in a 2-year storm when silted and 13 when clean. The crossings where desilting avoids the most disruption (Fig. kd51) are:

| # | Crossing | System | Closes every … years (silted → clean) | People routed through |
|---|---|---|---|---|
| 1 | Jinja Road | Nakivubo | 2 → 50 | 641,000 |
| 2 | Kibuye–Natete Road | Nalukolongo | 2 → 25 | 401,000 |
| 3 | Northern Bypass | Lubigi | 2 → 10 | 366,000 |
| 4 | Katwe Road | Nakivubo | 10 → never in 100 | 1,126,000 |
| 5 | Gayaza Road | Lubigi | 2 → 100 | 204,000 |
| 6 | Bwaise Roundabout | Lubigi | 2 → 5 | 294,000 |
| 7 | Bombo Road | Lubigi | 2 → 5 | 294,000 |
| 8 | Unnamed main road, Kalerwe | Lubigi | 2 → 10 | 200,000 |
| 9 | Entebbe Road | southern stream | 2 → 50 | 140,000 |
| 10 | Kampala–Masaka Road | western stream | 2 → 10 | 119,000 |

Several of these, such as Bwaise Roundabout and Bombo Road, close every 5 years even with clean channels: they also need more capacity, not only maintenance. The full ranked list is in `results/kd_roadsR_crossings.csv`.

## 3.6 How the exposure was built

Kampala's urban road network grew from 2,127 km (1975) to 5,262 km (2020). The share on low ground beside channels stayed near 6%, but its length more than doubled, from 141 to 315 km (Fig. kd47). 526 km of today's road sits on valley floor that was wetland or bush in 1986. Of the road impassable in a 10-year storm with clean channels, 68% lies on such former wetland. At Lubigi, the Northern Bypass and its feeder roads were built across what was open wetland in 1986 (Fig. kd49).

# 4. Discussion

- **A maintenance problem first.** The single largest lever on Kampala's road flooding is the condition of its channels and culverts, not rainfall. A city that keeps its channels clear avoids roughly five-sixths of the disruption that has built up since 1990. This shifts the policy conversation from climate-proofing roads to funding routine desilting, trash screens and culvert clearing before every rainy season.
- **But maintenance is not enough everywhere.** Paving has made 1990-sized channels too small for the 10-year storm, and crossings like Bwaise Roundabout flood every 5 years even when clean. These need larger culverts, upstream detention and protection of the remaining wetland (Paper 1).
- **Climate adaptation depends on maintenance.** Climate change matters most for a well-maintained system. Investing in climate-resilient road drainage without a maintenance regime would see its benefits masked by silt.
- **Targeting.** The crossing ranking gives KCCA and UNRA a short list where pre-season desilting buys the most network function. Each of the top five crossings carries the fastest route into town for 200,000 to 1.1 million residents (these route counts overlap and cannot be summed).
- **Planning.** Most flooded road was built on former wetland. New roads in Kampala's fringe and in Uganda's regional cities (Paper 7) should avoid valley floors or cross them on bridges sized for future flows.
- **Limitations:**
  - **A screening model:** rule-based channel sizes; no backwater, culvert-specific capacity or blockage dynamics; static stages per stretch. Absolute depths are uncertain, and the attribution compares states within the same model.
  - **Silt is a uniform scenario**, not measured, but the sensitivity test shows the conclusion holds from 10% to 50%.
  - **Encroachment only through footprints.** It is represented only by footprint blockage of conveyance. Fill, walls and raised plots are not captured, so its contribution is probably underestimated.
  - **The network is simplified.** Network effects are measured as access to the centre and to hospitals, without travel demand or congestion feedback. They are lower bounds on economic disruption.
  - **Elevation data.** The DEM predates some embankments, and the Entebbe Expressway is treated as raised.
  - **Validation** relies on eight reported events: enough to confirm that the model places floods in the right spots, not to calibrate depths.

# 5. Conclusion

Most of the growth in Kampala's road flooding since 1990 comes from silted channels, not storms. Siltation explains more than four-fifths of the increase in impassable road and in people cut off. Paving explains most of the rest, and climate change adds less than a tenth by the 2050s. Keeping a short list of channel crossings clear would restore much of the network's function in ordinary storms. The method uses only open data and can be applied to any city with a road map and a terrain model.

# Data and code availability

Code: `src/kd_roads.py` (road pieces, depths, history, validation), `src/kd_roads_attrib.py` (16 scenarios, network, Shapley, crossings, sensitivity), `src/kd_roads_maps.py` and `src/kd_roadsR_figs.py` (figures kd45–kd52). Results: `results/kd_roads_*.csv`, `results/kd_roadsR_*.csv`.

# Figures

- kd45: every road in Kampala over shaded relief.
- kd46: roads impassable in a 10-year storm, clean vs silted, with reported road floods.
- kd47: roads on the valley floors by urbanisation epoch; low-ground road km 1975–2020; expected impassable road-km by state.
- kd48: satellite close-ups at Lubigi, Bwaise, Kyambogo–Banda and Entebbe Road.
- kd49: today's roads drawn on the 1986 landscape at Lubigi.
- kd50: Shapley attribution, today and 2050s; the 2-year storm, clean vs silted.
- kd51: the crossings to desilt first.
- kd52: sensitivity of the attribution to the silt level.

# References

Items marked † were found through search but not opened, or their author lists are not confirmed; verify them before submission.

1. Coles, D., Yu, D., Wilby, R. L., Green, D. and Herring, Z. (2017). Beyond 'flood hotspots': modelling emergency service accessibility during flooding in York, UK. *Journal of Hydrology* 546, 419–436. doi:10.1016/j.jhydrol.2016.12.013
2. Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. *Numerische Mathematik* 1, 269–271.
3. European Space Agency (2021). Copernicus DEM GLO-30. doi:10.5270/ESA-c5d3d65
4. Eyring, V. et al. (2016). Overview of the Coupled Model Intercomparison Project Phase 6 (CMIP6) experimental design and organization. *Geoscientific Model Development* 9, 1937–1958. doi:10.5194/gmd-9-1937-2016
5. Funk, C. et al. (2015). The climate hazards infrared precipitation with stations. *Scientific Data* 2, 150066. doi:10.1038/sdata.2015.66
6. Green, D. et al. (2017). City-scale accessibility of emergency responders operating during flood events. *Natural Hazards and Earth System Sciences* 17, 1–16. doi:10.5194/nhess-17-1-2017
7. Hack, J. T. (1957). Studies of longitudinal stream profiles in Virginia and Maryland. U.S. Geological Survey Professional Paper 294-B.
8. Hagberg, A. A., Schult, D. A. and Swart, P. J. (2008). Exploring network structure, dynamics, and function using NetworkX. *Proceedings of the 7th Python in Science Conference*, 11–15.
9. Hallegatte, S., Rentschler, J. and Rozenberg, J. (2019). *Lifelines: The Resilient Infrastructure Opportunity*. World Bank, Washington, DC. doi:10.1596/978-1-4648-1430-3
10. † World Bank (2019). *Three feet under: the impact of floods on urban jobs, connectivity and infrastructure*. Background paper for Lifelines.
11. Kirpich, Z. P. (1940). Time of concentration of small agricultural watersheds. *Civil Engineering* 10(6), 362.
12. Koks, E. E. et al. (2019). A global multi-hazard risk analysis of road and railway infrastructure assets. *Nature Communications* 10, 2677. doi:10.1038/s41467-019-10442-3
13. Pesaresi, M. and Politis, P. (2023); Schiavina, M. et al. (2023). GHS-BUILT-S and GHS-POP R2023A. European Commission, Joint Research Centre.
14. Pregnolato, M., Ford, A., Wilkinson, S. M. and Dawson, R. J. (2017). The impact of flooding on road transport: a depth-disruption function. *Transportation Research Part D* 55, 67–81. doi:10.1016/j.trd.2017.06.020
15. Shapley, L. S. (1953). A value for n-person games. In Kuhn, H. W. and Tucker, A. W. (eds.), *Contributions to the Theory of Games II*, 307–317. Princeton University Press.
16. † TRID record 2724562 (2025/26). Flood-induced traffic disruption and network vulnerability in Kampala's urban road system. Transportation Research Board (authors and journal to confirm).
17. Yin, J., Yu, D., Yin, Z., Liu, M. and He, Q. (2016). Evaluating the impact and risk of pluvial flash flood on intra-urban road network: a case study in the city center of Shanghai, China. *Journal of Hydrology* 537, 138–145. doi:10.1016/j.jhydrol.2016.03.037
18. Zheng, X., Tarboton, D. G., Maidment, D. R., Liu, Y. Y. and Passalacqua, P. (2018). River channel geometry and rating curve estimation using height above the nearest drainage. *Journal of the American Water Resources Association* 54(4), 785–806. doi:10.1111/1752-1688.12661
19. Microsoft (2023). Global ML Building Footprints; OpenStreetMap contributors.
20. Companion papers of this programme: A, D0 (flood catalogue), 1 (lost sponge, incl. machine-learning land cover), 3 (access), 4 (damage), 6 (channel design drift), 7 (regional cities).
