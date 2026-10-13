# Uganda rainfall, climate and urban flooding: a research programme

**Author:** Gavamukulya (Gava) Charles · started October 2026

This repository is the single home for all of this work: data pipelines, analysis code, results, papers, the report, the open maintenance map, and every graphic, animation and post made for Substack, LinkedIn and X. Raw data is not stored here; the scripts in `src/` download and rebuild it.

## What's here at a glance

| Strand | Status | Where |
| --- | --- | --- |
| **1. Uganda climate report**: the failed 2026 El Niño forecast, shifting seasons, heat, water scarcity, food security, irrigation and design advice for drainage and bulk water | Complete; published as a private web report | [`report/`](report/) · code in [`src/`](src/) · figures `fig01`–`fig37` in [`figures/`](figures/) |
| **2. Paper: urban flooding in five cities**: *Quantifying land-cover change and climate change as drivers of urban flood peaks in Kampala, Nairobi, Dar es Salaam, Lagos and Johannesburg* | Full draft (16-model CMIP6 ensemble) | [`paper/urban_flooding_five_cities.md`](paper/urban_flooding_five_cities.md) (+ `.docx`) |
| **3. Paper: food security**: *Divergent satellite rainfall and vegetation signals of growing-season change in Uganda, 1981–2025* | Full draft | [`paper/uganda_growing_seasons_food_security.md`](paper/uganda_growing_seasons_food_security.md) (+ `.docx`) |
| **4. Kampala drainage and wetlands study**: channel-by-channel flood pressures, emerging hotspots, people on low ground, radar, 3D films | Analysis done; Paper A drafted (one test pending a flood catalogue) | [`paper/kampala_drainage_paperA.md`](paper/kampala_drainage_paperA.md) · [`paper/kampala_drainage_research_programme.md`](paper/kampala_drainage_research_programme.md) · code `src/kd_*.py` · figures [`figures/kampala_drainage/`](figures/kampala_drainage/) |
| **5. Kampala Drain Watch**: open maintenance map of all 6,914 channel stretches | Live and public | Source in [`tool/`](tool/) · live site **https://gavacharles.github.io/kampala-drain-watch/** |
| **6. Outreach: El Niño and changing seasons**: Substack article, X posts, NDP IV pieces, city cards, animations | Ready to post | [`outreach/`](outreach/) |
| **7. Outreach: Kampala drains**: Substack ("Kampala isn't drowning in rain. It's drowning in its drains."), LinkedIn, 30+ X posts, covers, GIFs, fly-through videos, 3D films | Ready to post | [`outreach/kampala_drainage/`](outreach/kampala_drainage/) |

## Related public repositories (published outputs of this one)

These are public copies made for sharing; their content comes from this repository.

| Repository | What it is |
| --- | --- |
| [gavacharles/kampala-drain-watch](https://github.com/gavacharles/kampala-drain-watch) | Hosts the public map on GitHub Pages (copy of [`tool/`](tool/)) |
| [gavacharles/where-is-the-el-nino-rain](https://github.com/gavacharles/where-is-the-el-nino-rain) | Public companion to the El Niño Substack article (copy of the [`outreach/`](outreach/) graphics) |

## Folder guide

| Folder | Contents |
| --- | --- |
| `src/` | All Python code: downloads, analysis, models, figures, animations, 3D films (see script tables below) |
| `figures/` | Report and paper figures (PNG); `figures/kampala_drainage/` holds the drainage study: maps, `areas/` (one page per hotspot), `areas/flythrough/` (walk-through videos), `animations/`, `3d/` |
| `results/` | Result tables (CSV) and run logs; Kampala drainage tables start with `kd_` |
| `paper/` | Manuscripts (Markdown and Word) and the drainage research programme |
| `report/` | The climate report (HTML) and its web images |
| `tool/` | Kampala Drain Watch source: `index.src.html` (page), segment data and basemaps |
| `outreach/` | Substack articles, X/LinkedIn posts, social graphics and animations; `outreach/kampala_drainage/` for the drainage study (`gifs/` holds every GIF) |
| `models/`, `docs/` | Model outputs and notes |
| `data/` | Not in git. Rebuilt by the download scripts (`data/raw/`, `data/processed/`, `data/kd/`) |

## Data sources

- **Rainfall**: CHIRPS v2.0 daily, 0.25° (UCSB Climate Hazards Center), 1981–present; ARC2 (NOAA CPC); GHCN-Daily gauges to calibrate extremes; NASA POWER hourly (MERRA-2)
- **Temperature**: NOAA CPC Global Daily Tmax/Tmin, 0.5°; NASA POWER daily; GHCN-CAMS monthly land temperature
- **Wind, humidity, radiation, pressure**: NASA POWER daily (MERRA-2 / CERES), regridded to 0.5°
- **Soil moisture**: CPC leaky-bucket model, 0.5° · **Global rainfall**: GPCP v2.3
- **Ocean drivers**: NOAA ERSST v5 (Niño-3.4, Indian Ocean Dipole), NOAA CPC ONI
- **Projections**: CMIP6 (Pangeo Google Cloud zarr), 16 models, SSP2-4.5 and SSP5-8.5
- **Vegetation and food security**: NOAA STAR Vegetation Health (VCI), FEWS NET IPC, FAOSTAT
- **Cities and buildings**: JRC Global Human Settlement Layer R2023A (built-up and population, 1975–2030), Microsoft Global ML Building Footprints, ESA WorldCover 2021, Impact Observatory 10 m land cover 2017–2023
- **Drains, culverts, waste points, places**: © OpenStreetMap contributors (ODbL)
- **Terrain and satellites**: Copernicus GLO-30 DEM; Sentinel-1 RTC and Sentinel-2 (via Microsoft Planetary Computer); NASA/USGS Landsat 1986–2025; Esri World Imagery
- **Flood records**: KCCA and NEMA hotspot lists; Daily Monitor, New Vision, NTV, The Observer, KFM, ReliefWeb, FloodList; GDELT news index
- **Boundaries**: Natural Earth, geoBoundaries

## Running

```
sh src/run_all.sh                        # climate report pipeline (downloads ≈ 1 GB)
.venv/bin/python src/report_images.py    # web-sized figures for report/index.html
```

### Climate report scripts

| Script | Figures | What it answers |
| --- | --- | --- |
| `zones.py` | fig01 | Six rainfall-regime regions |
| `rain_trends.py` | fig02–06 | Seasonal and extreme rainfall trends, annual cycle by epoch |
| `seasons.py` | fig07–09 | Onset, cessation and length of each rainy season |
| `climate_params.py` | fig10–13 | Temperature, wind, humidity, radiation, ET0, soil moisture |
| `forecast.py` | fig14–19 | 2026 so far, ENSO/IOD links, hindcast skill, OND 2026 outlook |
| `regional_global.py` | fig20–22 | Uganda vs East Africa, Africa, world |
| `water.py` | fig23–26 | Water balance and scarcity by county, CMIP6 future |
| `food_irrigation.py` | fig27–28 | Growing period, failed seasons, irrigation requirement |
| `drainage.py` | fig29–30 | Gauge-calibrated design storms, IDF, climate uplift |
| `bulk_water.py` | fig31–32 | Design droughts, SPI, treatment drivers |
| `maps.py` | fig33–37 | Satellite overview and close-ups |

### Five-city flooding paper and food paper

`kampala_catchments.py <city>`, `kampala_flood.py <city>`, `cities_compare.py`, `fetch_city.py` (flooding); `food_paper.py`, `food_divergence.py`, `food_vci_figure.py` (food security).

### Kampala drainage study (`src/kd_*.py`)

| Script | Output | What it does |
| --- | --- | --- |
| `kd_fetch.py` | `data/kd/osm_*`, POWER hourly | OpenStreetMap drains, culverts, wetlands, waste points, markets, bridges; hourly weather |
| `kd_rain.py` | kd01–kd03 | Kampala rainfall trends, rain on flood days, intensity vs humidity |
| `kd_network.py` | `results/kd_segments.csv`, `data/kd/segments.gpkg` | 6,914 channel stretches: pressures, priority and emerging-risk scores, validation |
| `kd_satellite.py` | Landsat, Sentinel-1/2, land-cover layers | Satellite downloads and composites; single radar passes |
| `kd_maps.py` | kd04–kd12, kd10b | Priority and emerging-risk maps, drivers, overlay, wetland loss, radar after the storm |
| `kd_areas.py` | kd13 (`figures/kampala_drainage/areas/`) | One in-depth page per flood-hotspot area |
| `kd_flythrough.py` | `areas/flythrough/*_social.mp4` | Smooth vertical walk-throughs along the channels |
| `kd_anim.py`, `kd_anim2.py` | kd14–kd21 + `animations/` | Valley floors, people on low ground, wetland time-lapse, paving, drivers, land cover, work classes |
| `kd_radar.py`, `kd_radar_storm_anim.py` | kd17, kd18, kd22, radar GIFs | Radar new-construction leads; storm-weekend animation |
| `kd_3d.py`, `kd_sculpt3d.py` | `figures/kampala_drainage/3d/` | 3D films: water rising, people on low ground, the three-act "sculpt" film |
| `kd_tests.py` | kd23–kd25 | Hold-out test, waste–culvert test, exposure decomposition |
| `kd_catalogue.py`, `kd_threshold.py` | flood catalogue, kd26 | News-based flood catalogue (GDELT); falling-threshold test (pending) |
| `kd_tool_promo.py`, `kd_programme_map.py` | demo, kd00 | Tool demo render; research-programme diagram |

## Credit and licence

Analysis, graphics and text by **Gava Charles**. Every graphic carries "Credit: Gava Charles" and its data sources. Third-party data remain under their own licences (OpenStreetMap and Microsoft buildings under ODbL; Copernicus, JRC, NASA, NOAA and ESA data under their open terms).
