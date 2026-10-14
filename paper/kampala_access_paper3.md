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

# References

1. Green, D., Yu, D., Pattison, I., Wilby, R., Bosher, L., Patel, R., Thompson, P., Trowell, K., Draycon, J., Halse, M., Yang, L. and Ryley, T. (2017). City-scale accessibility of emergency responders operating during flood events. *Natural Hazards and Earth System Sciences* 17, 1–16. doi:10.5194/nhess-17-1-2017
2. Coles, D., Yu, D., Wilby, R. L., Green, D. and Herring, Z. (2017). Beyond 'flood hotspots': modelling emergency service accessibility during flooding in York, UK. *Journal of Hydrology* 546, 419–436. doi:10.1016/j.jhydrol.2016.12.013
3. Yin, J., Yu, D., Yin, Z., Liu, M. and He, Q. (2016). Evaluating the impact and risk of pluvial flash flood on intra-urban road network: a case study in the city center of Shanghai, China. *Journal of Hydrology* 537, 138–145. doi:10.1016/j.jhydrol.2016.03.037
4. Pregnolato, M., Ford, A., Wilkinson, S. M. and Dawson, R. J. (2017). The impact of flooding on road transport: a depth-disruption function. *Transportation Research Part D* 55, 67–81. doi:10.1016/j.trd.2017.06.020
5. Weiss, D. J. et al. (2020). Global maps of travel time to healthcare facilities. *Nature Medicine* 26, 1835–1838. doi:10.1038/s41591-020-1059-1
6. Dijkstra, E. W. (1959). A note on two problems in connexion with graphs. *Numerische Mathematik* 1, 269–271.
7. Hagberg, A. A., Schult, D. A. and Swart, P. J. (2008). Exploring network structure, dynamics, and function using NetworkX. *Proceedings of the 7th Python in Science Conference*, 11–15.
8. OpenStreetMap contributors. OpenStreetMap. openstreetmap.org (data under ODbL).
9. Schiavina, M., Freire, S., Carioli, A. and MacManus, K. (2023). GHS-POP R2023A: GHS population grid, 1975–2030. European Commission, Joint Research Centre.
10. European Space Agency (2021). Copernicus DEM GLO-30. doi:10.5270/ESA-c5d3d65
11. Nobre, A. D., Cuartas, L. A., Hodnett, M., Rennó, C. D., Rodrigues, G., Silveira, A., Waterloo, M. and Saleska, S. (2011). Height Above the Nearest Drainage – a hydrologically relevant new terrain model. *Journal of Hydrology* 404, 13–29. doi:10.1016/j.jhydrol.2011.03.051
12. Companion papers of this programme: A, D and 1.
