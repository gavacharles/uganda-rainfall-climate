---
title: "Building in the water's path: land tenure, informality and the growth of flood exposure along Kampala's drainage channels, 1975–2030"
author: "Gava Charles"
date: "Draft, October 2026"
---

**Target journals:** *Habitat International*; *Land Use Policy*; *Cities*. Companion to Paper A (*Rainfall or drainage?*), which tests the drivers of flood hotspots; this paper asks who lives in the water's path, how they got there, and what the land system has to do with it.

# Abstract

Flood risk in African cities is usually framed as a hazard problem: heavier rain and undersized drains. Exposure, meaning who lives where the water goes, is less studied, and the land arrangements that put people there even less. We measure residential exposure along Greater Kampala's drainage network from 1975 to 2030 using open data. We combine 6,914 channel stretches (OpenStreetMap), a 30 m terrain model, JRC GHSL population and built-up layers (1975–2030) and 537,000 Microsoft building footprints. People living on low ground (less than 2 m above the nearest drain, within 150 m of a flowing channel) rose from about 36,000 in 1975 to 205,000 in 2020, and are projected at 247,000 by 2030.

Three findings reframe the usual story:

1. **Pace.** Low-ground population outgrew the city in 1975–2000 (4.3% vs 3.7% a year) but has grown in step with it since 2000.
2. **Location.** The centre of gravity of exposure has moved from the old inner channels to the urban fringe. Catchments outside the six main drainage systems held 4,300 exposed residents in 1975, 78,000 in 2020 and a projected 107,000 in 2030, more than any single system.
3. **Building form.** Low ground is built at a finer grain: median footprints of 66 m² against 82 m² on the hills, and 25% of buildings under 40 m², the scale of single rooms and rental rows, against 20%.

Settlement timing on low ground has historically matched the hills (median first-built year 1990 for both). However, the projected 2025–2030 growth falls almost entirely on low ground (4.8% of built cells vs 0.4%), as higher land fills up. We interpret these patterns through Kampala's land system:
- the separation of land and building rights under mailo tenure;
- a kibanja and rental market that makes cheap low ground accessible;
- the constitutional trust over wetlands (Article 237), enforced inconsistently, including through the cancellation of wetland titles.

The policy implication is that exposure is now being created at the fringe, where development control is weakest. Protecting the remaining valley floors there is cheaper than relocating people later.

# 1. Introduction

- Kampala floods most rainy seasons. The 26 March 2025 floods killed seven people, the 31 October 2025 floods killed three in the Kisenyi channel, and the city flooded again on 10–11 October 2026. Paper A shows that rainfall extremes have not intensified (wettest day of the year −1.0 mm/decade, not significant), while drainage pressures distinguish the hotspots. This paper turns from the hazard to the people exposed to it.
- Kampala's informal settlements cluster in wetlands and former floodplains; one estimate puts them at a quarter of the city's area and over 60% of its population (IntechOpen chapter, 2024). KCCA reports that the number of houses in wetlands rose from 20,958 in 2004 to 56,679 in 2024, with Lubigi the most encroached. In a survey of 551 wetland households, tenants were more exposed to floods than landlords (crude OR 1.7, 95% CI 1.08–2.76; Isunju et al., 2016).
- **The land system matters:**
  - **Mailo is the dominant tenure.** It separates land ownership from ownership of developments (kibanja occupancy), and only leasehold land, under 30% of holdings, can easily obtain formal subdivision approval.
  - **Mailo and informal housing go together.** Bird and Venables find that mailo tenure is strongly associated with the location of informal housing in Kampala.
  - **Wetland titles are contested.** Wetlands are held in trust by government under Article 237(2)(b) of the Constitution, and the National Environment (Wetlands, River Banks and Lake Shores) Regulations bar their alienation. Yet titles were issued: a 2014 Cabinet directive ordered cancellation of titles acquired in wetlands after 1995, and a later government statement put wetland titles at about 20,000 nationally, with 330 cancelled in Kampala, Wakiso and Mukono.
- **Gap.** Studies of Kampala's flood exposure are either household surveys of particular settlements (Bwaise, Nakivubo) or scenario models of single catchments (Upper Lubigi). There is no city-wide, observed, channel-level account of how exposure has grown since 1975, where it is moving, and what the built form says about who lives there.
- **Questions:**
  - RQ1: How many people live on low ground beside Kampala's channels, and how has this changed since 1975 relative to city growth?
  - RQ2: Where is exposure growing fastest?
  - RQ3: Does the timing and form of building on low ground differ from higher ground?
  - RQ4: How do these patterns relate to Kampala's land system, and what does that imply for planning?

# 2. Study area: Kampala's land and water

Greater Kampala sits on a series of hills separated by valley wetlands that drain through six main channel systems to Lake Victoria: Lubigi, Nakivubo, Kinawataka, Nalukolongo, Kansanga and Walufumbe. The valley floors were papyrus swamps; around most flood hotspots, less than 1% of land within 500 m is still wetland (Paper A).

**Land tenure** is described in four forms:
- **Mailo**, the dominant form, granted under the 1900 Buganda Agreement. Registered owners hold the land while kibanja occupants own the developments on it.
- **Leasehold**, mostly on public and Buganda kingdom land.
- **Freehold.**
- **Customary**, which is negligible in the city.

The Land Act 1998 gave lawful and bona fide occupants security, but registered owners contest these rights and the administrative procedures have largely not been implemented. As a result, much land access is informal, via local-council-witnessed kibanja transactions and room rentals. Wetlands should sit outside this market as public trust land, but encroachment, informal sales and contested titles have brought much of the valley floor into it.

# 3. Data and methods

| Layer | Source | Use |
|---|---|---|
| Channels | OpenStreetMap; 6,914 stretches draining ≥ 0.25 km² (Paper A inventory) | Defines "beside a channel" (≤ 150 m) |
| Terrain | Copernicus GLO-30 DEM; height above nearest drainage (HAND) | Low ground (HAND < 2 m); hills (HAND ≥ 10 m) |
| Population 1975–2030 | JRC GHS-POP R2023A, ~100 m (2025 and 2030 projected) | Exposure, growth, decomposition |
| Built-up 1975–2030 | JRC GHS-BUILT-S R2023A | Settlement age; crowding |
| Buildings | Microsoft Global ML Building Footprints (2023), 537,408 in the study box | Building size and grain |
| Catchments | D8 routing on the DEM (Paper A) | Channel systems |

**Exposure.** Residents in 100 m cells whose centre is on low ground, by channel system and epoch. Growth rates are compound annual rates, compared with hills and the whole study area. The decomposition (Paper A) splits change into city growth at a constant share and a shift toward low ground.

**Settlement age.** For each 100 m cell, the first GHSL epoch at which built-up surface reached 20%. We compare the distribution of first-built periods for low ground and hills.

**Building form.** Footprint area (median, share under 40 m², share over 200 m²), buildings per hectare and roof cover, for buildings on low ground versus hills, and by channel system. Under 40 m² approximates single rooms and rental rows ("muzigo"). Residents per built hectare (GHS-POP / GHS-BUILT, 2020) measures crowding.

**Tenure interpretation.** No open dataset maps tenure parcel by parcel. We therefore interpret the spatial patterns against the documented tenure system, legal framework and survey evidence, and treat the links as hypotheses for cadastral analysis (Section 6).

# 4. Results

**4.1 Exposure has grown fivefold, mostly with the city.**

| | 1975 | 1990 | 2000 | 2010 | 2020 | 2030 (proj.) |
|---|---|---|---|---|---|---|
| Residents on low ground beside channels | 35,600 | 64,000 | 101,600 | 144,500 | 205,100 | 247,200 |

| Compound annual growth | Low ground | Hills | Whole area |
|---|---|---|---|
| 1975–2000 | **4.3%** | 3.5% | 3.7% |
| 2000–2020 | 3.6% | 3.5% | 3.6% |
| 2020–2030 (projected) | 1.9% | 3.6% | 3.5% |

In 1975–2000, low ground grew faster than the city: 13,400 more people moved onto it than city growth alone would have put there (Paper A, Fig. kd25). Since 2000, exposure has grown at the city's pace. The projected slowdown after 2020 comes from the GHSL population model and should be treated with caution.

**4.2 The centre of exposure has moved to the fringe.**

| Residents on low ground | 1975 | 2000 | 2020 | 2030 (proj.) |
|---|---|---|---|---|
| Lubigi | 11,800 | 36,100 | 58,900 | 66,200 |
| Nalukolongo | 12,300 | 22,200 | 28,600 | 32,500 |
| Nakivubo | 5,300 | 11,000 | 17,200 | 17,900 |
| Kansanga | 900 | 6,700 | 12,000 | 13,200 |
| Kinawataka | 900 | 3,600 | 8,600 | 8,100 |
| Walufumbe | 100 | 600 | 2,000 | 2,000 |
| **Other (fringe) catchments** | **4,300** | **21,400** | **77,900** | **107,400** |

In 1975 the exposed population was concentrated in the old inner valleys of Nalukolongo and Lubigi. By 2020 the fringe catchments, outside the six systems KCCA's drainage programme focuses on, held more exposed residents than any single system. By 2030 they are projected to hold over 40% of the total (Fig. kd27). This matches Paper A's emerging-risk map, which places the next generation of hotspots on the northern and eastern fringe.

**4.3 Low ground was settled at the same time as the hills, until now.** The share of today's built cells first built in each period is almost identical for low ground and hills: 34% vs 36% by 1975, 25% vs 26% in 1995–2005, 20% vs 20% in 2010–2020, with a median first-built year of 1990 for both. In the projected 2025–2030 period, however, new built cells are almost all on low ground (4.8% vs 0.4%; Fig. kd28). As higher land saturates, new building is pushed onto what remains open: the valley floors.

**4.4 A finer grain of building on low ground.**

| Building form (2023) | Low ground beside channels | Hills and ridges |
|---|---|---|
| Buildings | 22,225 | 338,112 |
| Median footprint | **66 m²** | 82 m² |
| Under 40 m² (single rooms, rental rows) | **25%** | 20% |
| Over 200 m² | 11% | 13% |
| Roof cover (median, per hectare) | 4.8% | 8.1% |
| Residents per built hectare (2020) | 377 | 367 |

Buildings on low ground are smaller and more often single-room scale (Fig. kd29). The finest grain is on the Kinawataka and Walufumbe low ground (median 58 and 51 m²; a third under 40 m²) and the coarsest along Nakivubo (87 m²), where commercial and industrial buildings line the channel. Crowding per built hectare is similar. Roof cover on low ground is lower, reflecting the open, unbuilt valley floor that remains, and that the projection in 4.3 suggests will fill next.

# 5. Discussion: the land system behind the exposure

**5.1 Why low ground fills.** The patterns fit a land-market account:
- **Cheap, accessible land.** Valley floors are the cheapest land within reach of the city's jobs; flooding and poor drainage depress their price.
- **Access without title.** Under mailo, land can be occupied and built on through kibanja purchase or room rental without registered title or planning approval. That is the only route open to most households, since formal subdivision approval is effectively limited to leasehold land.
- **Rental supply.** The finer building grain on low ground, with more single-room footprints, fits a rental housing stock of "muzigo" rows built by small landlords for tenants. This is consistent with Isunju et al.'s finding that tenants, not owners, carry most flood exposure in Kampala's wetlands.

**5.2 Public trust land in a private market.** Wetlands are held in trust under Article 237(2)(b), and the Wetlands Regulations prohibit their alienation. In practice:
- titles were issued, informal sales took place, and industrial estates were legally sited in wetlands under earlier policies;
- the 2014 directive to cancel post-1995 wetland titles has moved slowly, with court injunctions and only hundreds of cancellations against an estimated 20,000 titles nationally;
- enforcement falls on the most visible and least protected occupants (demolitions), while titled developments persist.

The result is legal ambiguity that keeps the valley floor in the land market without the services, drainage or security that formal development would bring.

**5.3 Exposure is now made at the fringe.** Inner valleys such as Bwaise, Nalukolongo and Kisenyi were settled before 1990 and are now largely built over. New exposure is being created in the fringe catchments of Wakiso district (Kira, Nansana, Namugongo, Kyaliwajjala), where:
- the GHSL projection places almost all new low-ground building;
- KCCA's mandate does not reach, so development control rests with town and municipal councils with fewer resources;
- mailo and kibanja transactions are common.

**5.4 Planning implications.**
- **Map and gazette the remaining valley floors on the fringe now**, using the open-data low-ground layer here as a first screen, and prioritise them for protection before they are subdivided.
- **Align tenure and planning tools**:
  - recognise kibanja occupancy and local-council records in subdivision approval (as Muinde and others propose), so that development control can reach the land where most building happens;
  - pair it with a no-build valley-floor zone.
- **Protect tenants**: flood early warning, raised floors and minimum rental-room standards in existing low-ground settlements, where removal is neither feasible nor just.
- **Resolve wetland titles transparently**, starting with large titled parcels rather than the most visible informal occupants.
- **Coordinate across the metropolitan boundary** (KCCA, Wakiso, Mukono), since exposure has moved beyond the city's administrative reach.

# 6. Limitations and next steps

- **No parcel-level tenure data.** The tenure links are interpretive. The next step is to overlay the exposure layer with the national cadastre (Ministry of Lands, Housing and Urban Development) to measure mailo, leasehold and public-land shares on low ground, and with KCCA building approvals.
- **Population model.** GHS-POP distributes census totals by built-up area. It cannot see tenants versus owners, and the 2025–2030 values are projections.
- **Building footprints** from machine learning miss some small structures and merge attached rows. Small rental rooms are, if anything, under-counted, so the grain difference is conservative.
- **Low-ground definition** (HAND < 2 m, ≤ 150 m from a channel) is a screening threshold. Results are robust in direction to 1–3 m (to be reported in the supplement).
- **Household validation.** A short survey in a fringe and an inner settlement would test the tenant-exposure and rental-grain links directly.

# 7. Conclusion

Kampala's flood exposure grew fivefold between 1975 and 2020, to about 205,000 people living on low ground beside its channels. The first phase moved people disproportionately onto the valley floors. The second has simply followed the city's growth. The next is moving to the fringe, where almost all projected new low-ground building lies and where development control is weakest. Buildings on low ground are smaller and more often room-sized, which is consistent with a rental housing stock reached through Kampala's dual land system rather than through formal planning. Reducing future flood losses therefore depends as much on land policy as on drains: protecting the remaining fringe valley floors, bringing kibanja and rental housing within planning, and resolving wetland titles fairly.

# Figures

- kd27 exposure by drainage system, 1975–2030
- kd28 settlement age, low ground vs hills
- kd29 building size distribution
- kd25 exposure decomposition (from Paper A)
- kd15 people on low ground, maps
- kd05 emerging-risk map (from Paper A)

# References

Items marked † were found through search, or are grey literature not yet opened; verify them before submission.

1. Isunju, J. B., Orach, C. G. and Kemp, J. (2016). Hazards and vulnerabilities among informal wetland communities in Kampala, Uganda. *Environment and Urbanization* 28(1), 275–293. doi:10.1177/0956247815613689
2. Bird, J. and Venables, A. J. (2020). Land tenure and land-use in a developing city: a quantitative spatial model applied to Kampala, Uganda. *Journal of Urban Economics* 119, 103268. doi:10.1016/j.jue.2020.103268
3. Goodfellow, T. (2013). Planning and development regulation amid rapid urban growth: explaining divergent trajectories in Africa. *Geoforum* 48, 83–93. doi:10.1016/j.geoforum.2013.04.007
4. Lwasa, S. (2010). Adapting urban areas in Africa to climate change: the case of Kampala. *Current Opinion in Environmental Sustainability* 2(3), 166–171. doi:10.1016/j.cosust.2010.06.009
5. Douglas, I., Alam, K., Maghenda, M., Mcdonnell, Y., McLean, L. and Campbell, J. (2008). Unjust waters: climate change, flooding and the urban poor in Africa. *Environment and Urbanization* 20(1), 187–205. doi:10.1177/0956247808089156
6. Arinabo, D. (2024). Understanding the evolving nature of urban flood risks in sub-Saharan Africa: the case of Kampala City, Uganda. IntechOpen.
7. † Amooti Godfrey Nyakaana v. National Environment Management Authority and others. Constitutional Court of Uganda (2009); Supreme Court of Uganda, Constitutional Appeal (2015). Summary at UNEP LEAP national case law.
8. Government of Uganda. Constitution of the Republic of Uganda (1995), Article 237; Land Act, Cap. 227 (1998); National Environment Act (2019); National Environment (Wetlands, River Banks and Lake Shores Management) Regulations, S.I. No. 3 of 2000.
9. † Muinde, K. (2013). Land tenure and informal land access in Kampala. MSc thesis, Faculty ITC, University of Twente.
10. † KCCA (2024). Kampala moves to protect wetlands as loss reaches alarming levels. KCCA news release.
11. † Daily Monitor (2023). Govt to cancel 20,000 land titles in wetlands.
12. Rentschler, J., Avner, P., Marconcini, M., Su, R., Strano, E., Vousdoukas, M. and Hallegatte, S. (2023). Global evidence of rapid urban growth in flood zones since 1985. *Nature* 622, 87–92. doi:10.1038/s41586-023-06468-9
13. Tellman, B. et al. (2021). Satellite imaging reveals increased proportion of population exposed to floods. *Nature* 596, 80–86. doi:10.1038/s41586-021-03695-w
14. Pesaresi, M. and Politis, P. (2023). GHS-BUILT-S R2023A: GHS built-up surface grid, 1975–2030. European Commission, Joint Research Centre.
15. Schiavina, M., Freire, S., Carioli, A. and MacManus, K. (2023). GHS-POP R2023A: GHS population grid, 1975–2030. European Commission, Joint Research Centre.
16. Microsoft (2023). Global ML Building Footprints. github.com/microsoft/GlobalMLBuildingFootprints
17. European Space Agency (2021). Copernicus DEM GLO-30. doi:10.5270/ESA-c5d3d65
18. Nobre, A. D., Cuartas, L. A., Hodnett, M., Rennó, C. D., Rodrigues, G., Silveira, A., Waterloo, M. and Saleska, S. (2011). Height Above the Nearest Drainage – a hydrologically relevant new terrain model. *Journal of Hydrology* 404, 13–29. doi:10.1016/j.jhydrol.2011.03.051
19. OpenStreetMap contributors. OpenStreetMap. openstreetmap.org (data under ODbL).
20. Companion papers of this programme: A, 1, 7.
