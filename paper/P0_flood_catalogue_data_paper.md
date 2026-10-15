---
title: "A dated, geocoded catalogue of reported floods in Kampala, Uganda, 2007–2026, from news, humanitarian and official reports"
author: "Gava Charles"
date: "Draft, October 2026"
---

**Article type:** Data descriptor (companion data paper to the five-paper Kampala programme).
**Target journals:** *Scientific Data*; *Data in Brief*; *Geoscience Data Journal*; *Earth System Science Data*.

# Abstract

Kampala floods several times a year, yet no public, dated and geocoded record of these floods exists. Without one, rainfall thresholds cannot be set, flood models cannot be validated, and nobody can tell whether flooding is getting worse. We describe an open catalogue of 22 reported flood events in Kampala between 2007 and 2026, with 51 geocoded place records. The catalogue was built by combining:
- a systematic search of the GDELT global news index, 2017–2026, for events reported by at least two outlets;
- manually verified reports from Ugandan newspapers, broadcasters, ReliefWeb and FloodList.

Each event carries:
- a quality grade: A, dated and reported by two or more outlets (11 events); B, dated, one report (7); C, month only (4);
- the places named, geocoded with a 500 m uncertainty radius, and the drainage channel where it can be identified;
- reported deaths (26 in total);
- satellite and reanalysis rainfall on the day: CHIRPS daily and 3-day totals, the percentile of the daily total among wet days, and the NASA POWER peak-hour rate.

Two features of the record matter for anyone using it:
1. **Floods often follow ordinary daily rain.** The median flood day ranks only at the 74th percentile of wet days, and 7 of 18 dated events had less than 5 mm of CHIRPS rain on the day. Daily satellite rainfall misses the short cloudbursts that flood Kampala.
2. **There is a four-year hole in the record (April 2021 to March 2025).** No multi-outlet flood event was found in the news index in that period, although floods are known to have occurred (for example December 2024). Over the same years the index's coverage of Kampala news fell by about 85%. The record reflects reporting, not flooding.

The catalogue, its code and its grading rules are open. It is designed to be extended by KCCA, the Uganda National Meteorological Authority (UNMA), the Uganda Red Cross and residents, and the Kampala Drain Watch map already collects resident flood reports in the same format.

# Background and summary

- **The problem.** Urban floods in African cities are frequent, local and short. They rarely meet the thresholds of global disaster databases such as EM-DAT (Guha-Sapir et al.) or the Dartmouth Flood Observatory archive (Brakenridge), which record large events. Kampala's floods are recorded mainly in news reports, scattered across outlets and often undated online.
- **Why a catalogue matters.**
  - Rainfall-threshold early warning needs observed floods matched to rainfall. Young et al. (2021) built such thresholds for Alexandria, Egypt, from newspaper and social-media flood records.
  - Flood models need events to test against. Olsson et al. (2025) modelled culvert blockage in the upper Lubigi catchment using a dedicated rain and water-level network that exists for few other places in the city.
  - Trend questions, such as whether the same rain now floods more often, need a long, consistent record.
- **Related efforts.** De Bruijn et al. (2019) built a global flood database from Twitter, and Barnolas and Llasat (2007) built a regional geodatabase from historical press for Catalonia. To our knowledge there is no event-level, open flood record for Kampala or for any other Ugandan city.
- **This dataset** is the event backbone for a programme of Kampala drainage studies. It provides the flood days for the threshold test (Paper 1) and the reported road floods used to validate the road model (Paper 4).

# Methods

## Sources

| Stream | Coverage | What was done |
|---|---|---|
| GDELT DOC 2.0 news index (Leetaru and Schrodt 2013) | 2017-01 to 2026-10 | Queries for Kampala with flood terms (flood, floods, flooding, flash flood, downpour, heavy rain), English, 40 quarterly windows split adaptively to stay under the 250-article cap |
| Manual search | 2007 to 2026 | Web searches of Daily Monitor, New Vision, NTV Uganda, The Observer, Uganda Radio Network, KFM, ChimpReports, allAfrica, ReliefWeb and FloodList; each report read in full |
| Earlier project list | 2018 to 2026 | 11 events compiled during the hotspot study, with places and channels from the article text |

## From articles to events

1. **Filtering.** GDELT articles were kept if the title mentions Kampala or a Kampala place name *and* a flood term. Articles about floods elsewhere in Uganda (for example Kasese, Bududa, Ntoroko) were dropped.
2. **Grouping.** Articles within 3 days of each other were grouped into one event. A storm reported on the day, then followed by reports of bodies recovered or damage counted, is one event.
3. **Multi-outlet rule.** An event from GDELT alone enters only if at least two distinct web domains reported it. This removes single re-posts and misdated items.
4. **Merging streams.** Events from the three streams were merged when their dates fell within 3 days. The merged record keeps the earliest date, the union of places and channels, the highest reported death toll and all sources.

## Quality grades

| Grade | Rule | Events |
|---|---|---|
| A | Exact date; at least two independent outlets | 11 |
| B | Exact date; one verified report | 7 |
| C | Month only (report undated, or describes "this week") | 4 |

Grade C events are kept for completeness. They carry no rainfall attribution and should be left out of any day-level analysis.

## Geocoding

Each named place was matched first to a curated list of 43 Kampala flood hotspots (positions checked against satellite imagery, ±500 m), then to OpenStreetMap place nodes. Places that could not be matched are kept in the text field but not geocoded. Every coordinate carries a 500 m uncertainty radius. A report naming "Bwaise" says the flooding was somewhere in Bwaise, not at a point.

## Rainfall on the day

For every dated event:
- **CHIRPS v2.0** (Funk et al. 2015): the mean over Greater Kampala (0.15–0.50° N, 32.40–32.80° E) for the day and the 3 days ending on it;
- **percentile**: the daily total ranked against all wet days (≥ 1 mm) in 1991–2020;
- **NASA POWER hourly** (MERRA-2; Gelaro et al. 2017): the highest hourly rain in the 24 hours from the event date (values ≥ 150 mm/h treated as missing).

Both products are coarse (CHIRPS 0.05°, POWER 0.5°) and smooth out convective storms. They are included to characterise each event, not as a measured storm total.

# Data records

Two CSV files, linked by `event_id` (format `KLA-YYYYMMDD`):

**`kampala_flood_catalogue_2007_2026.csv`** (one row per event)

| Field | Content |
|---|---|
| event_id, date, date_precision | ID; date (YYYY-MM-DD, or YYYY-MM for grade C); "day" or "month" |
| grade, n_outlets | Quality grade; number of distinct outlets |
| description | Headline or summary, as reported |
| places, channels | Places named; drainage channel(s) where identifiable |
| deaths | Highest reported death toll (blank if none reported) |
| sources | Outlets and URLs |
| chirps_1d_mm, chirps_3d_mm, chirps_1d_pctile | CHIRPS rainfall and wet-day percentile |
| power_peak_hour_mm | NASA POWER peak hourly rain (mm/h) |
| n_places_geocoded | Number of place records |

**`kampala_flood_catalogue_places.csv`** (one row per event and place): event_id, place, lat, lon, location_uncertainty_m.

## Summary of the record

| Measure | Value |
|---|---|
| Events (A / B / C) | 22 (11 / 7 / 4) |
| Years with at least one event | 12 of 20 |
| Reported deaths | 26, in 8 events; the deadliest are 26 May 2019 (8 dead, Lufuka/Mayanja–Kaliddubi) and 26 March 2025 (7) |
| Place records / distinct places | 51 / 31 |
| Most-named places | Bwaise (5 events), Kalerwe (4), Banda (4), Kyambogo (4), then Katwe, Ndeeba, Kyebando, Namasuba, Kinawataka, Clock Tower (2 each) |
| Channels most often named | Lubigi; Kinawataka; Nakivubo |

The most-named places sit on the three systems that the hotspot study ranks highest: Bwaise and Kalerwe on the Lubigi and Nsooba, Banda and Kyambogo on the Kinawataka, and Katwe, Ndeeba and the Clock Tower on the Nakivubo (Fig. kd41).

## Rainfall on flood days

| Measure (18 dated events) | Value |
|---|---|
| Median CHIRPS wet-day percentile | 74th |
| Events above the 90th percentile | 6 (for example 18 Mar 2026: 23.8 mm, 99th) |
| Events with < 5 mm on the day | 7 (for example 3 Sep 2013: 2.4 mm, 17th; 6 Mar 2026: 2.6 mm, 19th) |
| Highest POWER peak hour | 5.5 mm/h (13 Apr 2016) |

Kampala floods on days that are, by daily satellite rainfall, ordinary. Two explanations apply, and both matter for users:
- **Rain mismatch.** The storms that flood the city are short and local, and are smeared out in 5 km daily and 50 km hourly products. Gauge readings reported in the news are much higher. For example, Makerere recorded 63.4 mm over 29–31 October 2025, while the CHIRPS 3-day total was 20.7 mm.
- **Date lag.** Some news dates are the day after the storm. Two GDELT events (3 Mar 2018, 15 Dec 2019) have near-zero rain on the listed day but wet antecedent days (18–21 mm in 3 days), which is consistent with a report published the morning after.

# Technical validation

- **Duplicates.** The 3-day grouping was checked by hand. No two catalogue events describe the same storm.
- **Every event read.** Each event's sources were read to confirm a flood in Kampala (not elsewhere in Uganda) on or near the stated date.
- **Geocoding.** Place matches were inspected on a map. Ambiguous names (for example "Kampala", "city centre") were not geocoded.
- **Independent check against terrain.** 17 of the 31 distinct geocoded places lie within 500 m of a channel draining at least 2 km² (median distance 480 m). Place points are neighbourhood centres, not flood locations, so this is a loose check. The curated hotspot positions, which are located on the flooded spot, score AUC 0.73 on an independent drainage-pressure index (Paper 1).
- **Coverage control.** The volume of all English-language GDELT articles mentioning Kampala was retrieved by month. It fell from about 55,000 a year in 2017 to 28,000 in 2021, 9,500 in 2023 and 7,900 in 2024, so part of the 2021–2024 gap is the index itself shrinking. It is not the whole story: in 2025 and 2026, at similar or lower volume (about 6,900 a year), the index again picked up multi-outlet floods. The gap reflects both thinner indexing and floods reported locally rather than in national, indexed media. Either way, a news-based record is not a stable measuring instrument.

# Usage notes

- **Use grade A and B for day-level analysis**, grade A alone for conservative tests, and grade C only for counts by year.
- **Do not read a trend from the counts.** The number of events per year tracks news coverage, which grows over time and has a hole in 2021–2024. Any trend analysis must control for coverage (as the threshold test in Paper 1 does) and will still be underpowered at this size.
- **Use gauge rainfall where possible.** CHIRPS and POWER values characterise the day and should be replaced with station or radar data when these become available.
- **Place points are areas.** Use the 500 m uncertainty radius, for example by buffering points, when matching to model output or channel segments.
- **Extending the record.** The schema is deliberately simple so that agencies and residents can add to it. The Kampala Drain Watch map (gavacharles.github.io/kampala-drain-watch) collects resident flood reports with date, location and photo, which map directly onto grade B records once confirmed.

# Limitations

- **Reporting bias.** The record favours floods that are large, deadly, central or on main roads, as news coverage does. Floods in informal settlements that close no road may go unreported.
- **Language.** Only English sources were searched. Luganda radio and social media carry many more reports.
- **Size.** At 22 events the catalogue is a beginning. A complete record would draw on KCCA incident logs, Uganda Red Cross response records, UNMA impact reports and the print archives of the Daily Monitor and New Vision, which hold the pre-2017 years.

# Recommendation: a city flood log

The 2021–2024 hole is itself a finding. Kampala's flood record depends on whether journalists write about a flood, not on whether it happened. A minimal, official flood log would fix this at almost no cost. KCCA ward officers would record, for each flood, the date and time, the place (GPS), the depth, the roads closed and the people affected, and publish the log each quarter. Combined with sub-hourly rain gauges, that log would within a few years allow rainfall thresholds for early warning, honest trend testing, and validation of every flood model of the city.

# Code availability

`src/kd_catalogue.py` (GDELT download and event building) and `src/kd_flood_catalogue.py` (merging, grading, geocoding, rainfall attribution, Fig. kd41). Python 3; pandas, geopandas, xarray. Data are released under CC BY 4.0. Source articles remain the property of their publishers, and only headlines, dates and URLs are redistributed.

# Figures

- kd41: a, timeline of events by grade, reported deaths and number of outlets, with the 2021–2024 gap shaded; b, places named in flood reports, sized by number of events, over the channel network.

# References

1. Barnolas, M. and Llasat, M. C. (2007). A flood geodatabase and its climatological applications: the case of Catalonia for the last century. *Natural Hazards and Earth System Sciences* 7, 271–281.
2. Brakenridge, G. R. Global Active Archive of Large Flood Events. Dartmouth Flood Observatory, University of Colorado. floodobservatory.colorado.edu.
3. de Bruijn, J. A., de Moel, H., Jongman, B., de Ruiter, M. C., Wagemaker, J. and Aerts, J. C. J. H. (2019). A global database of historic and real-time flood events based on social media. *Scientific Data* 6, 311. doi:10.1038/s41597-019-0326-9
4. Funk, C. et al. (2015). The climate hazards infrared precipitation with stations: a new environmental record for monitoring extremes. *Scientific Data* 2, 150066. doi:10.1038/sdata.2015.66
5. Gelaro, R. et al. (2017). The Modern-Era Retrospective Analysis for Research and Applications, version 2 (MERRA-2). *Journal of Climate* 30, 5419–5454. doi:10.1175/JCLI-D-16-0758.1
6. Guha-Sapir, D., Below, R. and Hoyois, Ph. EM-DAT: The International Disaster Database. CRED, Université catholique de Louvain, Brussels. www.emdat.be.
7. Leetaru, K. and Schrodt, P. A. (2013). GDELT: Global data on events, location and tone, 1979–2012. Paper presented at the International Studies Association annual convention, San Francisco.
8. Olsson, H., Mugume, S. N. and Sörensen, J. (2025). Modelling the effect of sediment and solid waste deposition on pluvial flood risk using in situ high-resolution rainfall and water level measurements. *Water Science & Technology* 91(6), 757–. doi:10.2166/wst.2025.039
9. Young, A., Bhattacharya, B. and Zevenbergen, C. (2021). A rainfall threshold-based approach to early warnings in urban data-scarce regions: a case study of pluvial flooding in Alexandria, Egypt. *Journal of Flood Risk Management* 14(2), e12702. doi:10.1111/jfr3.12702
10. Companion papers: 1 (*Rainfall or drainage?*), 4 (*Silt, not storms*).
