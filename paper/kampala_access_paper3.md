---
title: "Cut off by water: how flooding of low-lying roads disrupts access to hospitals and schools in Kampala"
author: "Gava Charles"
date: "Draft, October 2026"
---

**Target journals:** *Transportation Research Part D*; *Journal of Transport Geography*; *International Journal of Disaster Risk Reduction*; *Natural Hazards*.

# Abstract

Urban flood studies count flooded homes. Yet in Kampala's flash floods, which rise and drain within hours, much of the harm comes from what the water cuts off, above all the route to a hospital. We build a routable road network for Greater Kampala from OpenStreetMap: 305,731 nodes and 220 hospitals. We place 2020 population (JRC GHS-POP) on it, and flood every road link on low ground beside a drainage channel at three water levels (0.5, 1 and 2 m above the nearest drain), plus a scenario built from 45 reported flood hotspots. We then measure who loses hospital access and which roads matter most.

At a 1 m flood level, 229 km of road go under water and 209,000 residents' homes are on flooded ground. Among residents whose own homes stay dry:
- **36,000** lose every road route to a hospital;
- **131,000** see their fastest trip at least double, by 10 minutes or more;
- **136,000** end up more than 30 minutes from a hospital, against **134** in normal conditions.

Three hospitals and 70 schools sit on flooded ground at that level; at 2 m, 11 hospitals and 118 schools do. A single-link criticality analysis ranks the flood-prone roads whose loss costs the most person-minutes of hospital access. Five roads dominate:
- the A5 at Busega roundabout and the Fort Portal–Kampala road (about 0.8 million person-minutes each, affecting about 95,000 people);
- the Kampala–Nansana road;
- Hoima Road;
- the Nansana–Busunju road.

These links, on the Lubigi and Nalukolongo valley floors, are where raising road levels, enlarging culverts and keeping drains clear would protect the most access to care.

# 1. Introduction

- Kampala's floods are short and sharp. On 26 March 2025, roads into the city (Jinja Road at Kyambogo, the Northern Bypass, Kinawataka, Queensway) became impassable within hours. On 11 October 2026 the Kampala–Hoima road flooded at Lubigi before dawn. Radar passes taken 13 and 25 hours later showed the water already gone (Paper A).
- In such floods, mortality and morbidity depend on access: ambulances, women in labour, injured people and patients on dialysis cannot wait for the water to drain. Studies of Kampala's flood impacts focus on damage to homes and on waterborne disease. City-wide network effects on access to care have not been quantified.
- **Questions:**
  - RQ1: How many people lose hospital access, or face large delays, when low-lying roads flood?
  - RQ2: Which hospitals and schools sit on flood-prone ground?
  - RQ3: Which individual road links are most critical, and so where should road and drainage investment go first?

# 2. Data and methods

| Layer | Source |
|---|---|
| Roads | OpenStreetMap drivable network (40,203 ways), segmented into 315,065 edges; largest connected component kept |
| Speeds | Congested urban speeds by class: motorway/trunk 40, primary 30, secondary 25, tertiary 20, other 15 km/h |
| Hospitals, schools | OpenStreetMap: 220 hospitals and 1,420 schools in the study box |
| Population | JRC GHS-POP R2023A, 2020, 100 m cells; each cell may use any road node within 250 m |
| Flooding | Height above nearest drainage (HAND, Copernicus 30 m DEM); flowing channels (Paper A inventory); 45 reported hotspots |

**Flood scenarios.** A road edge floods if its midpoint is below the water level *h* above the nearest drain (HAND < *h*, for *h* = 0.5, 1, 2 m) and within 300 m of a flowing channel. Lake-shore flats are therefore excluded, and bridges never flood. In the hotspot scenario, low roads (HAND < 2 m) within 400 m of a reported hotspot flood. A hospital or school "on flooded ground" has HAND < *h*.

**Measures.** Fastest travel time from each populated cell to the nearest operating hospital (multi-source Dijkstra), normal versus flooded. We report, for residents whose own home is not on flooded ground:
- people with no route;
- people whose trip doubles and grows by more than 10 minutes;
- people more than 30 minutes from a hospital.

**Criticality.** Each flood-prone main road (motorway to tertiary, HAND < 1 m, near a channel) is removed alone. Its cost is the added person-minutes to the nearest hospital, with a cut-off counted as +60 minutes.

# 3. Results

**3.1 Access losses by flood level.**

| | 0.5 m | 1 m | 2 m | Reported hotspots |
|---|---|---|---|---|
| Road flooded (km) | 156 | 229 | 353 | 52 |
| Residents with homes on flooded ground | 144,000 | 209,000 | 317,000 | n/a |
| Residents (dry homes) cut off from all hospitals | 35,000 | 36,000 | 30,000 | 9,300 |
| Trip to hospital doubles (+10 min) | 128,000 | 131,000 | 163,000 | 0 |
| More than 30 min from a hospital | 122,000 | 136,000 | 128,000 | 9,500 |
| (normal conditions: > 30 min) | 134 | 134 | 134 | 134 |
| Hospitals on flooded ground | 2 | 3 | 11 | 3 |
| Schools on flooded ground | 46 | 70 | 118 | 70 |

The number of dry-home residents cut off falls slightly from 1 m to 2 m because more of them now have flooded homes and are counted in that row instead. Access disruption reaches far beyond the flooded valleys: residents on dry hillsides lose access because their routes to hospital cross the valley floor (Fig. kd32a, kd33).

**3.2 The most critical roads** (single-link removal, extra person-minutes to hospital):

| Road | Extra person-minutes | Residents delayed > 5 min |
|---|---|---|
| A5 at Busega roundabout (Masaka/Fort Portal road) | 0.80 million | 95,000 |
| Fort Portal–Kampala Road | 0.80 million | 95,000 |
| Kampala–Nansana Road | 0.40 million | 9,200 |
| Hoima Road | 0.35 million | (many small delays) |
| Nansana–Busunju Road | 0.13 million | 11,000 |
| Sentema Road | 0.12 million | 1,600 |
| Jinja Road | 0.08 million | 1,400 |
| Kampala–Masaka Road | 0.08 million | < 100 |

The two highest-ranked links cross the Nalukolongo and Lubigi valley floors at Busega. Hoima Road at Lubigi (flooded on 11 October 2026) affects few residents strongly but very many slightly, because it is the main western artery.

# 4. Discussion

- **Priorities:** about ten road links carry most of the access risk. Raising road levels, enlarging culverts and keeping drains clear at Busega, Lubigi (Hoima and Nansana roads) and Kyambogo protects the most access per shilling. These should be ranked alongside, not after, channel works.
- **Health-system planning:**
  - Hospitals on flood-prone ground (3 at 1 m, 11 at 2 m) need flood-proofed access and backup routes.
  - Flood emergency plans should pre-position ambulances on the far side of critical links during heavy-rain warnings.
- **Schools:** 70 to 118 schools sit on flood-prone ground. Rain warnings should trigger early-closure or shelter-in-place protocols.
- **Limitations:**
  - travel speeds are class averages, not measured congestion;
  - OSM hospital tags include small private facilities and may miss capacity differences;
  - flooding is a static scenario, not a time-varying model;
  - pedestrian and boda-boda routes that bypass flooded roads are not modelled.

  A next step is to weight hospitals by service level (referral, regional, private) and add measured travel times.

# 5. Conclusion

When Kampala's low roads flood, harm reaches far beyond the flooded homes: 36,000 people on dry ground lose every route to a hospital, and over 130,000 face doubled travel times. A handful of road crossings on the Lubigi and Nalukolongo valley floors carry most of that risk, which makes them the first places to invest.

# Figures

- kd32: a, residents affected by scenario; b, most critical flood-prone roads
- kd33: map of extra travel time to hospital (1 m scenario), flooded links, hospitals, critical roads

# References (to complete)

- Papers A, D and 1 of this programme.
- OpenStreetMap contributors; JRC GHS-POP R2023A; Copernicus GLO-30.
- Literature on flood impacts on emergency access (for example, Green et al., urban flood access and ambulance response) to be added.
