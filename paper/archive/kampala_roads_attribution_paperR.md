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
5. **The result is robust.** Across 400 Monte Carlo versions of the model, varying 12 uncertain assumptions, siltation is the largest driver in 399. Its share is 77% (90% interval 62–88%) of the increase in impassable road and 79% (64–90%) of the increase in people cut off. A machine-learning emulator (gradient boosting, cross-validated R² = 0.90) shows that the share depends mainly on how much depth silt removes and on channel roughness, while the absolute road length depends most on road height above the terrain model.
6. **The model puts floods where people report them, and the silted version does so best.** Reported flood-prone roads (KCCA's 2021 risk assessment, press lists and the flood catalogue) lie a median 335 m from modelled impassable main road, against 1,000 m for random road locations (AUC 0.80, p < 0.001). With clean channels the match is weaker (AUC 0.70), which is indirect evidence that the channels really are silted.
7. **Keeping channels clean is worth far more than it costs.** Avoided travel disruption (about US$0.5 million a year) plus avoided building damage (US$17 million, Paper 4) is about 6.6 times KCCA's annual road-and-drainage maintenance allocation.
8. **Much of today's exposure was built on former wetland.** 68% of the road that floods in a 10-year storm sits on valley floor that was wetland or bush in 1986. Urban road on low ground beside channels grew from 141 km (1975) to 315 km (2020).

The model reproduces all eight road floods reported in the news, 2007–2026. We rank the crossings where desilting would avoid the most closures: Jinja Road over the Nakivubo, Kibuye–Natete Road on the Nalukolongo, and the Northern Bypass, Gayaza Road and Bombo Road at Bwaise–Kalerwe. Kampala's road flooding is mainly a maintenance problem, and the cheapest adaptation is a shovel.

# 1. Introduction

- **The problem.** Flooded roads cut people off from work, markets, schools and hospitals, and in Kampala they are a fixture of every rainy season. Public debate tends to attribute them to heavier rain and climate change. Engineers and residents point instead to blocked drains, undersized culverts and building in the valleys. Both views are plausible, and neither has been quantified.
- **What is known.**
  - Global studies estimate road exposure and damage from river and surface floods (Koks et al. 2019).
  - City studies model the effect of flooded links on travel and emergency access (Yin et al. 2016; Green et al. 2017; Coles et al. 2017; Pregnolato et al. 2017).
  - In Kampala, a World Bank analysis estimated about 11 km of main roads flooded in a 50-year event in the inner city, with knock-on loss of access to health care (Hallegatte et al. 2019).
  - A recent traffic study of 22 links found overtopping from the 5-year storm and near-doubling of travel times under full closure (TRID record 2724562; published on ScienceDirect, article S2950196226000311).
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

## 2.7 Uncertainty and the machine-learning emulator

**Monte Carlo.** Twelve assumptions were varied together in 400 Latin hypercube draws (McKay et al. 1979), each re-running all 16 scenarios, six storms and the network model:

| Assumption | Range (main run) |
|---|---|
| Design standard of the channels | 5–25-year 1990 flow (10) |
| Manning n: clean channel / silted channel / floodplain | 0.020–0.030 (0.025) / 0.030–0.045 (0.035) / 0.04–0.10 (0.06) |
| Channel depth lost to silt | 10–50% (30%) |
| Paving calibration (GHSL → impervious) | 1.8–2.7 (2.27) |
| Runoff coefficient of unpaved ground | 0.15–0.35 (0.25) |
| Design-storm error | ±15% |
| Size of the climate change factor | 0.5–1.5 × (1) |
| Road surface above the 30 m DEM ground | 0–0.3 m (0) |
| Floodplain blocked per unit of footprint (walls, fill) | 1–3 × (1) |
| Depth that stops cars | 0.2–0.4 m (0.3) |

The rating curves are vectorised over all stretches and the network uses a compiled shortest-path routine (scipy), so one draw takes about 6 s. The central draw reproduces the main results (siltation share 82.5% vs 82.6%).

**Emulator.** A gradient-boosting regression (Friedman 2001; scikit-learn, Pedregosa et al. 2011) was trained on the 400 draws to predict the siltation share and the total disruption from the 12 assumptions. It was evaluated by 5-fold cross-validation, and permutation importance (Breiman 2001) ranks the assumptions by their influence. The emulator is used only to explain the uncertainty. The attribution itself comes from the physically based scenarios.

## 2.8 Validation

Two tests, against two independent sets of reports:
1. **Catalogue road floods.** Eight road floods named in the flood catalogue (Paper D0, 2007–2026). For each, the deepest modelled water on the named road within 1.5 km of the reported place.
2. **Flood-prone road list.** Seventeen flood-prone road locations: those named from KCCA's 2021 risk assessment (as listed in the Daily Monitor, 2023: Jinja Road at Game–Shoprite and at Banda, Lugogo Bypass, Kyambogo Junction, Kibuli Road, Mulago), the Observer's list of roads often cut off (Queen's Way, Ssebaana Kizito Road, Kabuusu, the Jinja Road roundabout), and the catalogue's road floods. Twelve could be geocoded (OpenStreetMap Nominatim, or the catalogue's positions). Report locations are approximate (±500 m), so the test asks whether reported spots lie closer to modelled impassable main road (10-year storm) than 5,000 random points on main roads do. We report the proximity AUC and a one-sided Mann–Whitney test (Mann and Whitney 1947).

## 2.9 Can satellites see channel condition?

To replace the uniform silt scenario with an observed one, we built Sentinel-2 dry-season median NDVI composites at 10 m for five seasons (2024–2026) and sampled the centreline of every channel stretch draining at least 3 km² (3,604 stretches, 262 km), and a band 30–60 m either side. We also ran a spatially varying silt scenario: depth lost = 10% + 40% × the stretch's dumping-pressure percentile (OSM waste points and markets; mean ≈ 30%).

## 2.10 Valuing disruption

Annual value of lost access = people cut off (expected annual) × hours a crossing stays impassable (2–8 h, flash floods) × share of residents travelling during the event (30–70%) × value of travel time (US$0.5–1.8 per hour; no official Ugandan value exists, and the upper end follows a published Kampala productivity estimate). Extra minutes for those still connected are valued the same way. All terms were sampled jointly (20,000 draws). This is compared with avoided building damage (Paper 4) and with KCCA's road-and-drainage maintenance allocation (UGX 10 billion, about US$2.7 million a year).

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

**The independent list** (Fig. kd54):

| 10-year storm | Median distance, reported spots → modelled impassable main road | Random road points | Reported within 500 m | Random within 500 m | Proximity AUC |
|---|---|---|---|---|---|
| Channels clean | 824 m | 1,560 m | 33% | 15% | 0.70 (p = 0.009) |
| Channels silted | 335 m | 1,000 m | 83% | 27% | 0.80 (p < 0.001) |

Reported flood-prone roads lie much closer to modelled flooding than random road locations. Two points matter:
- **The silted model matches the reports better than the clean one.** It is not just that silted channels flood more roads: the comparison against random points controls for that. The reported pattern of flooding is better explained by silted channels, which is indirect evidence for the scenario this paper puts at the centre.
- **Some reported spots are street floods, not channel floods.** At Banda and Kyambogo Junction the model places the water at the Kinawataka crossings 300–700 m away, not at the junction itself. Junction flooding there is partly from blocked roadside drains, which this model does not simulate.

## 3.3 Satellites cannot see the channels; where the silt sits does not matter

At 10 m, centreline NDVI tracks the surrounding land almost perfectly (r = 0.90): channels in green fringe areas look "choked", and channels in dense neighbourhoods look "clean". The difference between channel and surroundings is tiny (median +0.007) and is unrelated to dumping pressure (Spearman −0.10) or to reported hotspots. Kampala's channels, mostly under 10 m wide, cannot be inspected from Sentinel-2. Their condition needs very-high-resolution imagery, drones or KCCA's desilting records. We therefore keep silt as a scenario and test its pattern instead:

| Silt pattern (mean ≈ 30% of depth) | Siltation share, impassable road / people cut off | Impassable road, 2-year storm |
|---|---|---|
| Uniform | 83% / 86% | 199 km |
| Concentrated where dumping is heaviest | 84% / 87% | 208 km |

Where the silt sits changes the answer very little.

## 3.4 Attribution

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

## 3.5 How much silt does it take?

| Channel depth lost | Siltation share (road-km / people cut off) | Paving share |
|---|---|---|
| 10% | 71% / 75% | 27% / 22% |
| 20% | 78% / 81% | 19% / 16% |
| 30% (main) | 83% / 86% | 15% / 12% |
| 50% | 87% / 89% | 12% / 9% |

(Fig. kd52.) Even a light silting, a tenth of the channel depth plus a vegetated bed, accounts for most of the change. The conclusion does not depend on the assumed silt level.

## 3.6 Uncertainty: 400 versions of the model

| Quantity (today, average year) | Main run | Median | 90% interval |
|---|---|---|---|
| Siltation share, impassable road | 83% | 77% | 62–88% |
| Siltation share, people cut off | 86% | 79% | 64–90% |
| Paving share, impassable road | 15% | 15% | 8–29% |
| Encroachment share, impassable road | 2% | 7% | 3–14% |
| Climate share by the 2050s, impassable road | 9% | 9% | 5–19% |
| Impassable road, channels silted | 163 km | 132 km | 61–200 km |
| Impassable road, channels clean | 30 km | 16 km | 2–55 km |
| People cut off from centre, silted | 117,500 | 100,000 | 51,000–139,000 |

(Fig. kd53.) Siltation is the largest driver in 399 of 400 draws. The emulator predicts the siltation share well (cross-validated R² = 0.90). Its influence ranking:
- **the siltation share** depends mainly on silt depth, then the roughness of clean and of silted channels;
- **paving's calibration and the climate signal** barely matter for the share;
- **the absolute kilometres** depend most on how far roads sit above the DEM ground and on floodplain roughness. Absolute road lengths are therefore the least certain result, and the shares the most robust.

Encroachment rises from 2% to a median 7% once buildings are allowed to block more than their footprint. This supports the view that the main run understates it.

## 3.7 The crossings to clear first

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

## 3.8 What it costs

| Avoided by keeping channels clean (US$ million a year) | Central | 90% range |
|---|---|---|
| Travel disruption (lost access + delay) | 0.5 | 0.2–1.0 |
| Building damage (Paper 4) | 17.3 | 8.6–34.5 |
| **Total** | **17.7** | |
| KCCA road-and-drainage maintenance allocation | 2.7 | |

Travel losses are modest on their own because floods are short and the network offers detours. Building damage dominates. Together, the losses avoided by clean channels are about 6.6 times what KCCA is allocated for maintaining roads and drains. Even the low end of the range (about US$9 million) is more than three times that allocation. These are lower bounds: they exclude lost trade, goods, health effects, deaths and the cost of emergency response.

## 3.9 How the exposure was built

Kampala's urban road network grew from 2,127 km (1975) to 5,262 km (2020). The share on low ground beside channels stayed near 6%, but its length more than doubled, from 141 to 315 km (Fig. kd47). 526 km of today's road sits on valley floor that was wetland or bush in 1986. Of the road impassable in a 10-year storm with clean channels, 68% lies on such former wetland. At Lubigi, the Northern Bypass and its feeder roads were built across what was open wetland in 1986 (Fig. kd49).

# 4. Discussion

- **A maintenance problem first.** The single largest lever on Kampala's road flooding is the condition of its channels and culverts, not rainfall. A city that keeps its channels clear avoids roughly five-sixths of the disruption that has built up since 1990. This shifts the policy conversation from climate-proofing roads to funding routine desilting, trash screens and culvert clearing before every rainy season.
- **But maintenance is not enough everywhere.** Paving has made 1990-sized channels too small for the 10-year storm, and crossings like Bwaise Roundabout flood every 5 years even when clean. These need larger culverts, upstream detention and protection of the remaining wetland (Paper 1).
- **The reports point to silt too.** The flood-prone roads people report fit the silted model clearly better than the clean one (AUC 0.80 vs 0.70). Satellites cannot measure silt in Kampala's narrow channels, but the pattern of reported flooding is what silted channels would produce.
- **The economics are lopsided.** Losses avoided by clean channels are several times the maintenance allocation, so under-funding desilting is a false economy.
- **Climate adaptation depends on maintenance.** Climate change matters most for a well-maintained system. Investing in climate-resilient road drainage without a maintenance regime would see its benefits masked by silt.
- **Targeting.** The crossing ranking gives KCCA and UNRA a short list where pre-season desilting buys the most network function. Each of the top five crossings carries the fastest route into town for 200,000 to 1.1 million residents (these route counts overlap and cannot be summed).
- **Planning.** Most flooded road was built on former wetland. New roads in Kampala's fringe and in Uganda's regional cities (Paper 7) should avoid valley floors or cross them on bridges sized for future flows.
- **Limitations:**
  - **A screening model:** rule-based channel sizes; no backwater, culvert-specific capacity or blockage dynamics; static stages per stretch. Absolute depths are uncertain, and the attribution compares states within the same model.
  - **Silt is a uniform scenario**, not measured, but the sensitivity test shows the conclusion holds from 10% to 50%.
  - **Encroachment only through footprints.** It is represented only by footprint blockage of conveyance. Fill, walls and raised plots are not captured, so its contribution is probably underestimated.
  - **The network is simplified.** Network effects are measured as access to the centre and to hospitals, without travel demand or congestion feedback. They are lower bounds on economic disruption.
  - **Elevation data.** The DEM predates some embankments, and the Entebbe Expressway is treated as raised.
  - **Validation** uses 8 catalogue events and 12 geocoded flood-prone road locations: enough to show that the model places floods in the right areas, not to calibrate depths.
  - **Street flooding is not modelled.** Ponding at junctions from blocked roadside drains (for example Kyambogo Junction, Banda) is outside the model, which floods roads only from channel overflow.
  - **Costs** use assumed values of time, flood durations and trip shares, given as ranges.
  - **Culvert dimensions are not observed.** Street-level imagery could fill this gap with computer vision: measuring culvert openings and detecting blockage at the ranked crossings. Open street-level archives are thin in Kampala, though: KartaView has a photo within 60 m of only 2 of the top 60 crossings, and Mapillary was not accessible for this study. A culvert inventory from KCCA or UNRA would be the most direct way to close this gap.

# 5. Conclusion

Most of the growth in Kampala's road flooding since 1990 comes from silted channels, not storms. Siltation explains more than four-fifths of the increase in impassable road and in people cut off. Paving explains most of the rest, and climate change adds less than a tenth by the 2050s. Keeping a short list of channel crossings clear would restore much of the network's function in ordinary storms. The method uses only open data and can be applied to any city with a road map and a terrain model.

# Data and code availability

Code: `src/kd_roads.py` (road pieces, depths, history, validation), `src/kd_roads_attrib.py` (16 scenarios, network, Shapley, crossings, sensitivity), `src/kd_roads_mc.py` (Monte Carlo and emulator), `src/kd_roads_upgrade.py` (spatial silt, validation, costs), `src/kd_channel_condition.py` (Sentinel-2 channel test), `src/kd_roads_maps.py` and `src/kd_roadsR_figs.py` (figures kd45–kd52). Results: `results/kd_roads_*.csv`, `results/kd_roadsR_*.csv`.

# Figures

- kd45: every road in Kampala over shaded relief.
- kd46: roads impassable in a 10-year storm, clean vs silted, with reported road floods.
- kd47: roads on the valley floors by urbanisation epoch; low-ground road km 1975–2020; expected impassable road-km by state.
- kd48: satellite close-ups at Lubigi, Bwaise, Kyambogo–Banda and Entebbe Road.
- kd49: today's roads drawn on the 1986 landscape at Lubigi.
- kd50: Shapley attribution, today and 2050s; the 2-year storm, clean vs silted.
- kd51: the crossings to desilt first.
- kd52: sensitivity of the attribution to the silt level.
- kd53: Monte Carlo uncertainty (400 draws) and the emulator's ranking of assumptions.
- kd54: validation against flood-prone roads from KCCA, the press and the flood catalogue.

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
16. † Flood-induced traffic disruption and network vulnerability in Kampala's urban road system (2026). ScienceDirect, article S2950196226000311; TRID record 2724562 (authors and journal to confirm).
17. Yin, J., Yu, D., Yin, Z., Liu, M. and He, Q. (2016). Evaluating the impact and risk of pluvial flash flood on intra-urban road network: a case study in the city center of Shanghai, China. *Journal of Hydrology* 537, 138–145. doi:10.1016/j.jhydrol.2016.03.037
18. Zheng, X., Tarboton, D. G., Maidment, D. R., Liu, Y. Y. and Passalacqua, P. (2018). River channel geometry and rating curve estimation using height above the nearest drainage. *Journal of the American Water Resources Association* 54(4), 785–806. doi:10.1111/1752-1688.12661
19. Microsoft (2023). Global ML Building Footprints; OpenStreetMap contributors.
20. † Daily Monitor (2023). Let's watch out for flood prone roads (editorial listing KCCA's 2021 flood-risk roads).
21. † The Observer. Six killed, hundreds stranded as floods ravage Kampala (list of roads often cut off).
22. † KCCA. MPs: KCCA can't maintain roads, drainage on UGX 10 billion. kcca.go.ug/news/1102.
23. † Daily Monitor. Under the 30 km/h speed limit, Kampala's slower streets could spell a slower economy (commentary; productivity value of time).
24. Mann, H. B. and Whitney, D. R. (1947). On a test of whether one of two random variables is stochastically larger than the other. *Annals of Mathematical Statistics* 18, 50–60.
25. Breiman, L. (2001). Random forests. *Machine Learning* 45, 5–32.
26. Friedman, J. H. (2001). Greedy function approximation: a gradient boosting machine. *Annals of Statistics* 29(5), 1189–1232.
27. McKay, M. D., Beckman, R. J. and Conover, W. J. (1979). A comparison of three methods for selecting values of input variables in the analysis of output from a computer code. *Technometrics* 21(2), 239–245.
28. Pedregosa, F. et al. (2011). Scikit-learn: machine learning in Python. *Journal of Machine Learning Research* 12, 2825–2830.
29. Companion papers of this programme: A, D0 (flood catalogue), 1 (lost sponge, incl. machine-learning land cover), 3 (access), 4 (damage), 6 (channel design drift), 7 (regional cities).
