---
title: "The next Kampalas: open-data screening of valley-floor encroachment and flood exposure in Uganda's growing regional cities"
author: "Gava Charles"
date: "Draft, October 2026"
---

**Target journals:** *Cities*; *Habitat International*; *Applied Geography*; *Journal of Urban Management*.

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

People on low ground are projected to double in Gulu and Mbarara between 2020 and 2030. The regional cities are where Kampala was in the 1980s and 1990s: valley floors largely open but starting to fill. Protecting them now, through gazetted no-build valley corridors in physical development plans, costs a fraction of what Kampala now spends on flood recovery and drainage retrofits.

# 1. Introduction

- Kampala's flood problem has been built over five decades. Valley-floor wetlands were filled, exposure grew to about 205,000 people on low ground beside channels (Paper D), and storage was lost (Paper 1). Flood hotspots followed (Paper A).
- NDP IV and the National Physical Development Plan direct growth to regional cities, including Jinja, Mbale, Gulu, Mbarara and Arua. These cities have physical development plans but few flood studies, and their drainage, data and enforcement capacity is much thinner than KCCA's.
- **Questions:**
  - RQ1: How far have regional cities built onto their valley floors, compared with Kampala?
  - RQ2: Is population on low ground growing faster than the cities themselves?
  - RQ3: Can a uniform, open, reproducible method support national screening?

# 2. Data and methods

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

Channels come from the terrain rather than OpenStreetMap, so that coverage is equal in every city. The Kampala figures here therefore differ slightly from Papers A and D, which used OSM channels.

# 3. Results

**3.1 Valley floors built over.**

| City | 1975 | 1995 | 2005 | 2020 | 2030 (proj.) | Storage lost 1975–2020 |
|---|---|---|---|---|---|---|
| Kampala | 2.3% | 4.3% | 5.7% | 7.9% | 8.7% | 3.9% |
| Arua | 0.8% | 1.7% | 2.4% | 3.1% | 3.9% | 2.2% |
| Mbale | 0.3% | 1.1% | 1.5% | 2.4% | 3.2% | 1.7% |
| Gulu | 0.1% | 0.4% | 0.8% | 1.4% | 2.2% | 1.1% |
| Mbarara | 0.2% | 0.6% | 0.7% | 1.4% | 1.9% | 1.0% |
| Jinja | 0.2% | 0.6% | 0.8% | 1.1% | 1.3% | 0.4% |

(GHSL built-up share, uncalibrated, for comparability across cities; Fig. kd40a.)

**3.2 People in the water's path.**

| City | On low ground, 1975 | 2020 | 2030 (proj.) | Share of area, 2020 | Growth 2020–30, low ground vs whole area (% a year) |
|---|---|---|---|---|---|
| Kampala | 41,800 | 324,500 | 411,300 | 9.0% | 2.4 vs 3.5 |
| Mbale | 4,300 | 30,300 | 51,700 | 6.4% | 5.5 vs 3.0 |
| Mbarara | 1,300 | 16,500 | 33,500 | 5.4% | 7.3 vs 5.7 |
| Jinja | 4,200 | 15,600 | 22,300 | 3.4% | 3.7 vs 1.8 |
| Arua | 1,500 | 9,200 | 12,900 | 2.6% | 3.5 vs 2.1 |
| Gulu | 600 | 7,900 | 15,100 | 3.2% | 6.7 vs 3.4 |

Relative to 2000, low-ground population is projected to have grown 6.3-fold in Mbarara, 4.1-fold in Gulu and 3.6-fold in Mbale by 2030, against 3.1-fold in Kampala (Fig. kd40b). In 2000–2020 low ground already grew faster than the city in all six (Fig. kd40c).

**3.3 Building form.** In Kampala, buildings on low ground are smaller than on the hills (median 64 vs 83 m²), matching the rental-room pattern described in Paper D. In the regional cities this pattern has not (yet) appeared: low-ground buildings are similar in size to, or larger than, those on higher ground (Jinja 59 vs 54 m², Mbale 58 vs 49 m², Mbarara 69 vs 65 m²). Low-ground development there is earlier-stage and mixed rather than dense rental housing.

# 4. Discussion

- **The window is open now.** Regional valley floors are 1–3% built, compared with Kampala's 8%. Kampala reached today's regional levels in the 1980s, and the same trajectory is visible, only faster.
- **Policy:**
  - Gazette valley corridors (HAND < 2–3 m) as no-build drainage and wetland reserves in the physical development plans of Mbarara, Gulu, Mbale, Jinja and Arua.
  - Use NDP IV urban infrastructure programmes to fund primary drainage *before* settlement.
  - Adopt this screening as a national tool: the method needs only global open data and runs city by city in minutes.
- **Limitations:**
  - GHSL population in small cities rests on coarse census inputs and modelled projections;
  - terrain channels may include dry valleys and miss piped drains;
  - 30 m terrain smooths small towns' drainage lines;
  - no flood-event records were available for validation outside Kampala.

  Local verification with municipal engineers and the Uganda National Meteorological Authority is the next step.

# 5. Conclusion

Kampala shows where unmanaged valley-floor development leads. Uganda's regional cities are on the same path, starting later but moving faster: their low-ground populations are projected to grow up to twice as fast as the cities themselves this decade. Open data can identify these valleys today, while protecting them is still cheap.

# Figures

- kd40: a, valley floor built over 1975–2030; b, people on low ground relative to 2000; c, 2020–30 growth, low ground vs whole area

# References (to complete)

- Government of Uganda (2024). Fourth National Development Plan (NDP IV) 2025/26–2029/30; National Physical Development Plan.
- JRC GHSL R2023A; Copernicus GLO-30; Microsoft Building Footprints; Nobre et al. (2011) HAND.
- Papers A, D, 1 of this programme.
