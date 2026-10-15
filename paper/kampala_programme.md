---
title: "Kampala drainage and wetlands: research programme (five papers)"
author: "Gava Charles"
date: "15 October 2026"
---

# Structure

The Kampala study was consolidated from thirteen drafts into **five papers and one short data paper**. Each paper makes one claim, and together they run from cause to consequence to response. Earlier drafts are kept in `paper/archive/`.

| # | Paper | One claim | Merges | Target journals |
|---|---|---|---|---|
| 1 | **Rainfall or drainage?** Kampala's floods come from how the city was built, not from heavier storms | Rainfall extremes flat; floods on ordinary rain; hotspots set apart by encroachment, constrictions and lost wetland; channels outgrown by paved catchments; next hotspots visible on the fringe | A, 6 | *J. Flood Risk Management*; *NHESS* |
| 2 | **The double loss**: valley wetlands as flood storage and water treatment | Half the living valley floor gone (three satellite methods); 17 million m³ storage gap; 51% of bay-draining treatment wetland lost; bay outlets murkier as wetland shrank | 1, 2, ML land cover | *Science of the Total Environment*; *Landscape and Urban Planning* |
| 3 | **Building in the water's path**: land, housing and double exposure to floods and heat | Exposure 36k → 205k; moving to the fringe; rental grain on low ground; 53% of low-ground residents in the hottest nights | D, 5 | *Habitat International*; *Environment and Urbanization* |
| 4 | **Silt, not storms**: attributing flood damage and road disruption | Siltation explains ~80% of the rise in road flooding and multiplies building damage sevenfold; validated against KCCA's list (AUC 0.80); avoided losses ~6.6× the maintenance allocation | R, 4, 3 | *NHESS*; *Transportation Research Part D* |
| 5 | **The next Kampalas**: valley floors, exposure and roads in Uganda's regional cities | Regional cities filling their valleys faster than Kampala did; Mbale and Mbarara already have Kampala's share of road on low ground | 7 + regional roads screening | *Cities*; *Applied Geography* |
| 0 | **Flood catalogue** (data paper) | An open, dated, geocoded record of Kampala floods 2007–2026; a four-year reporting gap | D0 | *Data in Brief* |

**Separate papers in this repository (not part of the Kampala programme):**
- *Quantifying land-cover change and climate change as drivers of urban flood peaks in Kampala, Nairobi, Dar es Salaam, Lagos and Johannesburg* (`urban_flooding_five_cities.md`). It supplies the climate uplift used in Papers 1 and 4. A follow-on applying the road attribution to the other four cities is possible later.
- *Uganda growing seasons and food security* (`uganda_growing_seasons_food_security.md`).

**Parked:** radar monitoring of encroachment (folded into Paper 1 as a note); the Drain Watch software paper.

# Case-study maps and supporting figures

Each paper opens its study-area section with a case-study map in a common style (shaded relief, inset locator, north arrow, scale bar, credits), built by `src/kd_casemaps.py`:

| Paper | Case-study map | Supporting figure |
|---|---|---|
| 0 | cm0: where reported floods happened, by grade, with the hotspot list | – |
| 1 | cm1: six channel systems, channels, 45 hotspots, KCCA boundary, Makerere gauge | fw1: study design (two explanations, six tests) |
| 2 | cm2: valley-floor land cover today, bay-draining catchments, bay zones, Ggaba intake | lc2: Nakivubo–Kinawataka from Landsat, 1986 vs 2025 |
| 3 | cm3: people on low ground in 2020, inside vs outside KCCA | bg3: building grain, Bwaise vs Kawempe hill |
| 4 | cm4: road network, 636 bridge-less crossings, hospitals, validation spots | fw4: attribution design |
| 5 | cm5: six cities at the same scale, valley floors and low-ground roads | – |

# Shared data and code

OpenStreetMap drains, culverts, roads, waste points; Microsoft building footprints; JRC GHSL built-up and population 1975–2030; Copernicus GLO-30; CHIRPS and NASA POWER; Landsat, Sentinel-1 and Sentinel-2 via the Microsoft Planetary Computer; CMIP6 design-storm uplift. Code in `src/kd_*.py`; results in `results/`; figures in `figures/kampala_drainage/`.

# Before submission

1. Verify references marked † in each paper.
2. Literature search in Scopus/Google Scholar for each paper's novelty claim (especially Paper 4).
3. Move supporting figures to supplements and check journal word limits.
4. Seek a co-author from KCCA, UNRA, NEMA or Makerere (culvert inventory, desilting records, cadastre for Paper 3).
5. Suggested order: Paper 4 and the data paper first (strongest and quickest), then 1, 2, 3, 5.
