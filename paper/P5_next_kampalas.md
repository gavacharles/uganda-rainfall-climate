---
title: "The next Kampalas: open-data screening of valley-floor encroachment, flood exposure and road exposure in Uganda's growing regional cities"
author: "Gava Charles"
date: "Draft, October 2026"
---

**Paper 5 of 5, Kampala drainage programme.** Extends earlier draft 7 with a road screening using the method of Paper 4.
**Target journals:** *Cities*; *Applied Geography*; *Habitat International*; *Journal of Urban Management*.

# Abstract

Uganda's Fourth National Development Plan (NDP IV) promotes regional cities as growth centres, yet almost nothing is known about their flood exposure. We apply one open-data method to Kampala and five regional cities: Jinja, Mbale, Gulu, Mbarara and Arua. Identical rules are used everywhere:
- channels and height above the nearest drain from the Copernicus 30 m terrain model;
- built-up area and population from JRC GHSL (1975–2030);
- building footprints from Microsoft.

Kampala's valley floors were built over earliest and most (2.3% in 1975, 7.9% in 2020, 8.7% projected for 2030). The regional cities start from far lower levels (1–3% in 2020), but their exposure is accelerating. In Kampala, the population on low ground beside channels is now projected to grow more slowly than the city (2.4% vs 3.5% a year, 2020–30). In every regional city it grows faster:

| City | Low ground (% a year) | Whole city (% a year) |
|---|---|---|
| Mbarara | 7.3 | 5.7 |
| Gulu | 6.7 | 3.4 |
| Mbale | 5.5 | 3.0 |
| Jinja | 3.7 | 1.8 |
| Arua | 3.5 | 2.1 |

People on low ground are projected to double in Gulu and Mbarara between 2020 and 2030.

Roads follow the same path. Using the same rules for every OpenStreetMap road in each city, 11% of road in Mbale and Mbarara already lies on low ground beside channels, the same share as Kampala (11%), against 4–7% in Gulu, Arua and Jinja. In every city, road built on recently urbanised ground is more likely to be in the valleys: in Jinja and Mbarara the share rises from about 5% for roads on ground urbanised by 1990 to 9–10% for 2010–20, approaching Kampala's 13%. Mbale has as many channel crossings per 100 km of road (62) as Kampala (53). In Kampala, silted channels at such crossings explain about four-fifths of road flooding (Paper 4). The regional cities are where Kampala was in the 1980s and 1990s: valley floors largely open but starting to fill. Protecting them now, through gazetted no-build valley corridors in physical development plans, costs a fraction of what Kampala now spends on flood recovery and drainage retrofits.

# 1. Introduction

- Kampala's flood problem has been built over five decades. Valley-floor wetlands were filled, exposure grew to about 205,000 people on low ground beside channels (Paper 3), and storage was lost (Paper 2). Flood hotspots followed (Paper 1).
- NDP IV and the National Physical Development Plan direct growth to regional cities, including Jinja, Mbale, Gulu, Mbarara and Arua. These cities have physical development plans but few flood studies, and their drainage, data and enforcement capacity is much thinner than KCCA's.
- **Questions:**
  - RQ1: How far have regional cities built onto their valley floors, compared with Kampala?
  - RQ2: Is population on low ground growing faster than the cities themselves?
  - RQ3: Can a uniform, open, reproducible method support national screening?

# 2. Study area: six cities

The five regional cities were among those given city status in 2020 and are promoted as regional growth centres in national planning (Fig. cm5):
- **Jinja** (about 450,000 people in its 18 km box, 2020) sits on the shore of Lake Victoria at the source of the Nile; an old industrial town with broad lake-shore flats.
- **Mbale** (470,000) sits at the foot of Mount Elgon, crossed by streams falling from the mountain; the most dissected terrain of the five.
- **Mbarara** (300,000), in the south-west, spreads along the Rwizi river valley among rolling hills.
- **Gulu** (250,000), in the north, sits on a gently undulating plateau with shallow valleys.
- **Arua** (350,000), in the north-west near the borders with DR Congo and South Sudan, also sits on a plateau; its box is smaller because the terrain tile is clipped.

Kampala (3.6 million in its core box) is the reference. The six panels of Fig. cm5 show each city's valley floors and roads at the same scale and under the same rules.

# 3. Data and methods

| Layer | Source |
|---|---|
| Terrain, channels, HAND | Copernicus GLO-30 DEM; D8 routing (pysheds); channels = cells draining ≥ 0.25 km² |
| Built-up, population 1975–2030 | JRC GHS-BUILT-S and GHS-POP R2023A (2025, 2030 projected) |
| Buildings | Microsoft Global ML Building Footprints |

**Study areas.** Square windows of about 18 km around each city centre (Kampala: the 30 × 24 km core used throughout this programme).

**Definitions:**
- *Low ground*: HAND < 2 m and within 150 m of a channel.
- *Valley floor*: HAND < 3 m.
- *1 m storage*: capacity to hold water 1 m above the drains on valley floor not built over.

Channels come from the terrain rather than OpenStreetMap, so that coverage is equal in every city. The Kampala figures here therefore differ slightly from Papers 1 and 3, which used OSM channels.

# 4. Results

**4.1 Valley floors built over.**

| City | 1975 | 1995 | 2005 | 2020 | 2030 (proj.) | Storage lost 1975–2020 |
|---|---|---|---|---|---|---|
| Kampala | 2.3% | 4.3% | 5.7% | 7.9% | 8.7% | 3.9% |
| Arua | 0.8% | 1.7% | 2.4% | 3.1% | 3.9% | 2.2% |
| Mbale | 0.3% | 1.1% | 1.5% | 2.4% | 3.2% | 1.7% |
| Gulu | 0.1% | 0.4% | 0.8% | 1.4% | 2.2% | 1.1% |
| Mbarara | 0.2% | 0.6% | 0.7% | 1.4% | 1.9% | 1.0% |
| Jinja | 0.2% | 0.6% | 0.8% | 1.1% | 1.3% | 0.4% |

(GHSL built-up share, uncalibrated, for comparability across cities; Fig. kd40a.)

**4.2 People in the water's path.**

| City | On low ground, 1975 | 2020 | 2030 (proj.) | Share of area, 2020 | Growth 2020–30, low ground vs whole area (% a year) |
|---|---|---|---|---|---|
| Kampala | 41,800 | 324,500 | 411,300 | 9.0% | 2.4 vs 3.5 |
| Mbale | 4,300 | 30,300 | 51,700 | 6.4% | 5.5 vs 3.0 |
| Mbarara | 1,300 | 16,500 | 33,500 | 5.4% | 7.3 vs 5.7 |
| Jinja | 4,200 | 15,600 | 22,300 | 3.4% | 3.7 vs 1.8 |
| Arua | 1,500 | 9,200 | 12,900 | 2.6% | 3.5 vs 2.1 |
| Gulu | 600 | 7,900 | 15,100 | 3.2% | 6.7 vs 3.4 |

Relative to 2000, low-ground population is projected to have grown 6.3-fold in Mbarara, 4.1-fold in Gulu and 3.6-fold in Mbale by 2030, against 3.1-fold in Kampala (Fig. kd40b). In 2000–2020 low ground already grew faster than the city in all six (Fig. kd40c).

**4.3 Building form.** In Kampala, buildings on low ground are smaller than on the hills (median 64 vs 83 m²), matching the rental-room pattern described in Paper 3. In the regional cities this pattern has not (yet) appeared: low-ground buildings are similar in size to, or larger than, those on higher ground (Jinja 59 vs 54 m², Mbale 58 vs 49 m², Mbarara 69 vs 65 m²). Low-ground development there is earlier-stage and mixed rather than dense rental housing.

**4.4 Roads in the valleys.**

| City | Road km (OSM) | On low ground | Channel crossings per 100 km | Low-ground share of road on ground urbanised: by 1990 → 2010–20 |
|---|---|---|---|---|
| Kampala | 6,725 | 11.1% | 53 | 8.5% → 12.7% |
| Mbale | 1,178 | 10.9% | 62 | 7.9% → 12.0% |
| Mbarara | 1,184 | 10.8% | 49 | 5.4% → 8.8% |
| Jinja | 1,485 | 6.9% | 50 | 4.7% → 9.8% |
| Arua | 982 | 5.4% | 41 | 1.8% → 2.4% |
| Gulu | 1,016 | 3.9% | 23 | 0.3% → 2.3% |

(Fig. kd56. Same terrain-channel rules as Section 2; a crossing is a road passing over a channel cell and not tagged as a bridge. OSM road completeness varies between cities.) Mbale and Mbarara already have Kampala's share of road on low ground; Jinja and Mbarara are moving their new road into the valleys fastest. Gulu and Arua still have most of their roads on higher ground, the clearest opportunity to keep it that way.

# 5. Discussion

- **Terrain sets the starting point; growth decides the outcome.** Mbale's steep, stream-cut terrain and Mbarara's river valley put more of their road and housing on low ground from the start, while Gulu and Arua sit on plateaus with shallow valleys. But in every city the newest urban land is more likely to be low than the oldest, because the ridges and higher ground are taken first.

- **The window is open now.** Regional valley floors are 1–3% built, compared with Kampala's 8%. Kampala reached today's regional levels in the 1980s, and the same trajectory is visible, only faster.
- **Policy:**
  - Gazette valley corridors (HAND < 2–3 m) as no-build drainage and wetland reserves in the physical development plans of Mbarara, Gulu, Mbale, Jinja and Arua.
  - Use NDP IV urban infrastructure programmes to fund primary drainage *before* settlement.
  - Adopt this screening as a national tool: the method needs only global open data and runs city by city in minutes.
  - Route new roads along ridges and cross valleys on bridges or culverts sized for future flows, with a maintenance budget attached; in Kampala, silt at crossings drives most road flooding (Paper 4).
- **Limitations:**
  - GHSL population in small cities rests on coarse census inputs and modelled projections;
  - terrain channels may include dry valleys and miss piped drains;
  - 30 m terrain smooths small towns' drainage lines;
  - no flood-event records were available for validation outside Kampala;
  - OSM road completeness differs between cities, so road shares are more comparable than road lengths.

  Local verification with municipal engineers and the Uganda National Meteorological Authority is the next step.

# 6. Conclusion

Kampala shows where unmanaged valley-floor development leads. Uganda's regional cities are on the same path, starting later but moving faster: their low-ground populations are projected to grow up to twice as fast as the cities themselves this decade. Open data can identify these valleys today, while protecting them is still cheap.

# Figures

- cm5: study area, six cities at the same scale
- kd40: a, valley floor built over 1975–2030; b, people on low ground relative to 2000; c, 2020–30 growth, low ground vs whole area
- kd56: a, share of road on low ground by when its ground urbanised; b, road on low ground and channel crossings per 100 km, by city

# References

Items marked † were found through search, or are grey literature not yet opened; verify them before submission.

1. National Planning Authority (2025). *Fourth National Development Plan (NDP IV) 2025/26–2029/30*. Government of Uganda, Kampala.
2. † Ministry of Lands, Housing and Urban Development. National Physical Development Plan, Uganda.
3. Rentschler, J., Avner, P., Marconcini, M., Su, R., Strano, E., Vousdoukas, M. and Hallegatte, S. (2023). Global evidence of rapid urban growth in flood zones since 1985. *Nature* 622, 87–92. doi:10.1038/s41586-023-06468-9
4. Tellman, B. et al. (2021). Satellite imaging reveals increased proportion of population exposed to floods. *Nature* 596, 80–86. doi:10.1038/s41586-021-03695-w
5. Nobre, A. D., Cuartas, L. A., Hodnett, M., Rennó, C. D., Rodrigues, G., Silveira, A., Waterloo, M. and Saleska, S. (2011). Height Above the Nearest Drainage – a hydrologically relevant new terrain model. *Journal of Hydrology* 404, 13–29. doi:10.1016/j.jhydrol.2011.03.051
6. Bartos, M. pysheds: simple and fast watershed delineation in Python. github.com/mdbartos/pysheds
7. Pesaresi, M. and Politis, P. (2023). GHS-BUILT-S R2023A: GHS built-up surface grid, 1975–2030. European Commission, Joint Research Centre.
8. Schiavina, M., Freire, S., Carioli, A. and MacManus, K. (2023). GHS-POP R2023A: GHS population grid, 1975–2030. European Commission, Joint Research Centre.
9. European Space Agency (2021). Copernicus DEM GLO-30. doi:10.5270/ESA-c5d3d65
10. Microsoft (2023). Global ML Building Footprints. github.com/microsoft/GlobalMLBuildingFootprints
11. Companion papers: 1 (*Rainfall or drainage?*), 2 (*The double loss*), 3 (*Building in the water's path*), 4 (*Silt, not storms*).
