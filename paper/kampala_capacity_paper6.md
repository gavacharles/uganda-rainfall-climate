---
title: "Design-basis drift: how far Kampala's drainage channels have fallen behind the flows they now receive"
author: "Gava Charles"
date: "Draft, October 2026"
---

**Target journals:** *Urban Water Journal*; *Journal of Flood Risk Management*; *Water Science and Technology*; *Journal of Hydrology: Regional Studies*.

# Abstract

Drainage channels are sized for the catchment that exists when they are designed. As cities pave their catchments, the same storm sends more water down channels that have not grown, a gap we call design-basis drift. Without surveyed cross-sections it cannot be measured directly. It can, however, be estimated consistently from open data by asking how much today's design storm exceeds the flow a channel would have been sized for at an earlier date.

For 6,914 channel stretches in Greater Kampala (468 km draining 0.25 km² or more), we size each channel to carry the 10-year storm under 1990 land cover. We then compute peak flows (rational method, gauge-corrected design storms) under:
- 2020 and 2030 land cover (JRC GHSL, calibrated to impervious cover);
- 2041–70 rainfall under SSP2-4.5 and SSP5-8.5 (CMIP6 uplift);
- 30% siltation.

Results:
1. **Today.** The 10-year storm now delivers a median 17% more flow than the 1990 design flow. Half of all channel length (230 km) is overloaded by more than 20%, and 18% of channel length can no longer carry even a 2-year storm.
2. **Future.** With 2030 land cover and 2041–70 rainfall, the overloaded share rises to 80% (SSP2-4.5) and 91% (SSP5-8.5).
3. **Siltation dwarfs drift.** A channel silted by 30% carries a median 2.7 times less than the 10-year flow, far more than 30 years of paving.
4. **Where drift is concentrated.** Drift is greatest in Kinawataka, Walufumbe and the fringe catchments, and smallest in Nakivubo, Kansanga and Nalukolongo. It is strongly negatively associated with today's reported flood hotspots (AUC 0.16), because those lie in the old city, paved before 1990.

So today's hotspots fail mainly through encroachment, siltation and undersized pre-1990 channels. Design-basis drift is building the next generation of overloaded channels on the fringe. Maintenance (desilting) is the largest immediate capacity lever. Upsizing and on-site detention are needed where paving and climate will push flows past design.

# 1. Introduction

- Most of Kampala's primary channels were built or upgraded in phases from the 1950s to the 2010s, sized with the hydrology of their time. Since 1990 the city's impervious share has roughly tripled (15% to 42% in the Greater Kampala core; Paper 1), and the 2041–70 design storms are projected to be 9–13% heavier (CMIP6).
- Paper A found that the hotspot drivers of today are encroachment, constrictions and lost wetland, not runoff growth, and that change measured early predicts later encroachment. Paper 6 asks the capacity question directly: by how much has each channel's design basis drifted, where, and what will climate change add?
- **Gap.** Capacity assessments in African cities require surveyed cross-sections and are done reach by reach. No city-wide, reproducible screening of design-basis drift exists for Kampala or comparable cities.

# 2. Methods

**Peak flow (rational method):** Q_T = 0.278 · C · i_T(t_c) · A · ARF.
- C = 0.25 + 0.65 × upstream impervious share, from JRC GHSL calibrated to WorldCover (factor 2.27).
- i_T comes from the gauge-corrected CHIRPS IDF for Kampala, with 2041–70 SSP2-4.5 and SSP5-8.5 versions (Clausius–Clapeyron uplift from CMIP6 warming).
- Time of concentration: Kirpich formula, with flow length L = 1.4·A^0.6 km and slope from the DEM; minimum 10 min.
- Areal reduction: ARF = 1 − 0.04·A^0.5 (floor 0.7).

**Design basis.** Each stretch is sized to carry the 10-year flow under 1990 land cover at bankfull. The section is rectangular with width 3 × depth, Manning n = 0.025 (maintained, lined), and bed slope from the DEM.

**Overload ratio.** The scenario 10-year flow divided by design capacity, under five scenarios:
1. 2020 land;
2. 2030 land (projected);
3. 2030 land + 2041–70 SSP2-4.5;
4. 2030 land + 2041–70 SSP5-8.5;
5. 2020 land with 30% siltation (depth −30%, n = 0.035).

**Validation.** Overload ratio against the 45 reported flood hotspots (AUC, 2 km block bootstrap), compared with Paper A's priority index.

**Interpretation.** The absolute capacities are hypothetical, since the true sizes are unknown. The *ratio* is the meaningful quantity: it measures how much the flow has changed relative to a consistent design rule, independent of actual channel dimensions.

# 3. Results

**3.1 Drift so far.**

| Scenario | Median overload | Channel length overloaded > 20% | > 50% |
|---|---|---|---|
| 2020 land | 1.17 | 230 km (49%) | 55 km |
| 2030 land | 1.20 | 254 km (54%) | 57 km |
| + 2041–70 SSP2-4.5 | 1.31 | 374 km (80%) | 90 km |
| + 2041–70 SSP5-8.5 | 1.36 | 424 km (91%) | 120 km |
| 2020 land, 30% silted | 2.73 | 468 km (100%) | 468 km |

Today, 84 km of channel (18%) can no longer carry a 2-year storm, 252 km carries between the 2- and 5-year storm, and only 6 km still carries the 10-year storm it was sized for.

**3.2 Where.**

| 2020, by system | Median overload | % length > 20% |
|---|---|---|
| Walufumbe | 1.21 | 81% |
| Kinawataka | 1.21 | 64% |
| Lubigi | 1.15 | 38% |
| Nakivubo | 1.06 | 8% |
| Kansanga | 1.17 | 7% |
| Nalukolongo | 1.06 | 0% |

The most overloaded named channels are Nasere and upper Lubigi (1.6–1.7), Mayanja–Waswa (1.5), Kajjansi, Kalidubi and the Kinawataka main channel (1.3). The map (Fig. kd38) shows drift concentrated on the northern and eastern fringe and the Lubigi headwaters. Central channels are near their design flow (Fig. kd37).

**3.3 Drift is not what floods today.** The overload ratio is strongly *negatively* associated with reported hotspots: AUC 0.16 (95% CI 0.09–0.25), against 0.73 for Paper A's priority index. Today's hotspots sit where paving was already high by 1990. Their channels fail through other mechanisms: encroachment, constrictions, siltation and sizing that predates 1990.

# 4. Discussion

- **Two problems, two responses:**
  - **In the old city,** capacity has been lost to siltation and encroachment. A 30% silted channel carries less than half of a clean one, a larger effect than 30 years of paving. Desilting and reserve enforcement give the fastest gains.
  - **On the fringe,** channels are being overtaken by paving now and by heavier storms after 2040. The response is on-site detention for new development, upsizing at the next reconstruction, and protecting the remaining storage (Paper 1).
- **Design standards.** KCCA and Wakiso design manuals should require future-conditions design: projected land cover plus a climate uplift. Under SSP5-8.5, flows 36% above 1990 conditions are the median by 2041–70.
- **Limitations:**
  - the channel geometry is hypothetical (sized by rule), so the analysis screens change rather than measuring capacity;
  - the rational method overestimates peaks for larger catchments (partly offset by the ARF);
  - DEM slopes are noisy over short stretches;
  - the siltation scenario is a uniform assumption.

  Surveyed sections from KCCA's drainage inventory would convert the ratios into absolute capacities.

# 5. Conclusion

Kampala's drainage channels are falling behind the flows their catchments now produce: by a median 17% since 1990, and by 31–36% once 2041–70 rainfall is added. The drift is concentrated on the fringe, where tomorrow's flood hotspots are forming. The old city's channels fail for a different reason, siltation and encroachment, which maintenance can fix fastest.

# Figures

- kd37: a, overload ratio by scenario; b, overloaded length by system
- kd38: map of 2020 overload ratio

# References (to complete)

- Kirpich (1940); Hack (1957); USDA rational-method and ARF guidance.
- Zheng et al. (2018). HAND-based synthetic rating curves, *JAWRA*.
- Papers A and 1 of this programme; CMIP6 uplift from the five-city paper.
