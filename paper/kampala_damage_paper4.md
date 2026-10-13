---
title: "The cost of a blocked drain: channel-by-channel flood damage and the value of maintenance in Kampala"
author: "Gava Charles"
date: "Draft, October 2026"
---

**Target journals:** *Natural Hazards and Earth System Sciences*; *Journal of Flood Risk Management*; *International Journal of Disaster Risk Reduction*; *Water Resources and Economics*.

# Abstract

Drain maintenance budgets in African cities are set without knowing what a blocked channel costs. We estimate expected annual flood damage (EAD) to buildings for each of 6,914 channel stretches in Greater Kampala using open data:
- **hazard:** gauge-corrected design storms (2–100-year) routed through screening channel hydraulics and a terrain-based (HAND) synthetic rating curve;
- **exposure:** 80,000 building footprints within 200 m of the channels;
- **vulnerability:** the JRC global depth–damage curve for African residential buildings.

We compare clean channels with channels that have lost 30% of their depth to silt and vegetation. At a screening value of US$150 per m² of footprint, Kampala's channels generate an EAD of US$3.0 million a year when clean, and US$20.3 million a year when silted. Keeping the channels clear is therefore worth about US$17 million a year in avoided building damage. Over 30 years at a 10% discount rate, that justifies roughly US$160 million of maintenance spending (US$80–330 million across value assumptions).

The value is highest per kilometre along Nalukolongo (US$152,000 per km per year), Kansanga (US$93,000), Lubigi (US$90,000) and Nakivubo (US$80,000). The most valuable named channels to keep clear are:

| Channel | Avoided damage per year |
|---|---|
| Nakivubo Channel | US$1.1 million |
| Lubigi Channel | US$0.66 million |
| Kibira A channel | US$0.44 million |
| Nabuny zone A drain | US$0.44 million |
| Lukuli–Nanganda drain | US$0.38 million |

These numbers turn a maintenance budget into an investment case. Desilting the top channels before each rainy season is among the highest-return flood measures available to KCCA.

# 1. Introduction

- Paper A found that Kampala's flood hotspots are explained by drainage pressures (encroachment, constrictions, lost wetland), not heavier rain. Paper 6 found that siltation removes more capacity than 30 years of paving adds. KCCA desilts channels each year, but there is no published estimate of what that work is worth, or where it pays most.
- **Gap.** Flood-risk assessments for Kampala are either city-wide, coarse global-model estimates or single-catchment hydraulic studies. None prices maintenance channel by channel.
- **Contribution:**
  1. a screening EAD for every channel stretch;
  2. the avoided damage from keeping channels desilted, per km;
  3. a ranking of channels by maintenance value, with a break-even maintenance budget.

# 2. Methods

**Hazard.** Peak flows for 2-, 5-, 10-, 25-, 50- and 100-year storms come from the rational method with gauge-corrected design storms. Each channel is sized to its 1990 10-year flow (Paper 6). Flow above bankfull spreads over a floodplain whose width at each stage comes from the HAND distribution of 30 m cells within 200 m of the stretch (synthetic rating curve; Zheng et al. 2018), with Manning n = 0.06 on the floodplain. This gives a stage above the bank top for each return period.

**Silted state.** The channel keeps 70% of its depth, with n = 0.035. The floodplain must then carry the lost conveyance, raising the stage along the local rating-curve slope.

**Exposure.** 79,982 buildings (Microsoft footprints) within 200 m of a flowing channel, each assigned to its nearest stretch. Flood depth at a building = stage above bank − HAND of the building's cell.

**Vulnerability.** JRC global depth–damage curve, Africa residential (Huizinga et al. 2017):

| Depth (m) | 0 | 0.5 | 1 | 1.5 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|---|---|
| Damage fraction | 0 | 0.22 | 0.38 | 0.53 | 0.64 | 0.82 | 0.90 | 0.96 | 1.0 |

The exposed value of structure plus contents is US$150 per m² of footprint, a screening value for Kampala's largely single-storey, low-cost stock. Sensitivity runs use US$75 and US$300.

**EAD** is the trapezoidal integral of event damage over annual exceedance probability, with zero damage at the 1-year event. The maintenance value is EAD(silted) − EAD(clean). The break-even budget is the 30-year present value of the maintenance value at 10% (factor 9.43).

# 3. Results

**3.1 City-wide.**

| Exposed value (US$/m²) | EAD clean | EAD silted | Maintenance value per year | 30-yr PV at 10% |
|---|---|---|---|---|
| 75 | 1.5 m | 10.1 m | 8.6 m | 81 m |
| **150 (central)** | **3.0 m** | **20.3 m** | **17.3 m** | **163 m** |
| 300 | 6.0 m | 40.5 m | 34.5 m | 325 m |

Event damage (central value) ranges from US$0.2 m (2-year) to US$30 m (100-year) with clean channels. With silted channels it ranges from US$21 m to US$69 m (Fig. kd39a). Siltation turns the frequent storms, the 2- and 5-year events, from nuisances into damaging floods. That is why it multiplies the annual damage roughly sevenfold. In a clean-channel 10-year storm, 7,852 buildings are flooded.

**3.2 By system** (central value):

| System | Channel km | EAD clean (US$ m/yr) | EAD silted | Avoided per km per year |
|---|---|---|---|---|
| Nalukolongo | 26.4 | 0.41 | 4.42 | US$152,000 |
| Kansanga | 7.8 | 0.10 | 0.83 | US$93,000 |
| Lubigi | 70.9 | 1.38 | 7.79 | US$90,000 |
| Nakivubo | 28.8 | 0.21 | 2.53 | US$80,000 |
| Kinawataka | 12.9 | 0.10 | 0.48 | US$30,000 |
| Walufumbe | 2.0 | 0.01 | 0.04 | US$15,000 |
| Fringe catchments | 135.0 | 0.80 | 4.18 | US$25,000 |

**3.3 The channels most worth keeping clear** (stretches ≥ 150 m, channels ≥ 0.5 km):

| Channel | System | km | Buildings within 200 m | Avoided damage (US$/yr) |
|---|---|---|---|---|
| Nakivubo Channel | Nakivubo | 6.0 | 655 | 1,140,000 |
| Lubigi Channel | Lubigi (lower) | 6.0 | 712 | 664,000 |
| Kibira A channel | fringe | 7.0 | 3,194 | 441,000 |
| Nabuny zone A drain | Nalukolongo | 2.0 | 330 | 438,000 |
| Lukuli–Nanganda drain | Kansanga | 2.0 | 1,772 | 378,000 |
| Nabisasiro drain | fringe | 2.0 | 1,340 | 330,000 |
| Good Hope channel | Lubigi | 1.0 | 315 | 264,000 |

(Fig. kd39b; full table in `results/kd_damage_top_channels.csv`.)

# 4. Discussion

- **Maintenance is an investment.** On these estimates, each year of keeping Kampala's channels desilted avoids about US$17 million of building damage. This excludes damage to roads, goods, health and livelihoods, and the lives lost in floods that kill people every year. A break-even budget of about US$160 million over 30 years (US$5–6 million a year) is far above typical desilting spending, which supports a larger and better-targeted programme.
- **Targeting:**
  - The ranking by avoided damage per km gives KCCA an order of work for pre-season desilting: Nakivubo, the lower Lubigi, and the Nalukolongo and Kansanga drains first.
  - Combined with Paper A's work queue and Paper 3's critical roads, it gives a multi-criteria maintenance plan.
- **Limitations:**
  - **Hazard:** a screening model with rule-based channel sizes; no backwater, culvert blockage or timing effects; the rational method overestimates large-catchment peaks.
  - **Silted scenario:** a uniform 30% loss, not measured silt depths.
  - **Values:** screening, not appraised; contents and non-residential buildings simplified.
  - **Footprints:** miss some small structures.

  The *ratios* (silted ÷ clean, rankings between channels) are more robust than the absolute dollar values. Calibration against KCCA damage records or insurance data would anchor the levels.

# 5. Conclusion

Keeping Kampala's drainage channels clean is worth roughly US$17 million a year in avoided building damage, about six times the residual damage with clean channels. The value is concentrated in a few channels, led by the Nakivubo and lower Lubigi, which makes desilting one of the most cost-effective flood measures the city controls.

# Figures

- kd39: a, damage per storm, clean vs silted; b, avoided damage per km by system

# References (to complete)

- Huizinga, J., de Moel, H., Szewczyk, W. (2017). *Global flood depth-damage functions*. JRC Technical Report.
- Zheng, X. et al. (2018). River channel geometry and rating curve estimation using height above the nearest drainage. *JAWRA*.
- Papers A, 1, 3 and 6 of this programme.
