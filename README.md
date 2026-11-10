# uganda-rainfall-climate

Code, results, figures and manuscripts for research on Uganda's rainfall and climate (1981 onwards), urban flooding in five African cities, growing-season reliability, and Kampala's drainage network. Raw data is not stored here; the download scripts rebuild it.

Author: Gava Charles.

## Folder guide

| Folder | Contents |
| --- | --- |
| `src/` | All Python code: downloads, analysis, models, figures, animations, 3D films (script tables below) |
| `figures/` | Report and paper figures (PNG); `figures/kampala_drainage/` holds the drainage study maps, per-hotspot pages (`areas/`), fly-through videos, animations and 3D renders |
| `results/` | Result tables (CSV) and run logs; Kampala drainage tables start with `kd_` |
| `paper/` | Manuscripts (Markdown and Word) |
| `report/` | The climate report (HTML) and its web images |
| `tool/` | Source of the Kampala Drain Watch map: `index.src.html`, segment data, labels and basemaps |
| `tool_replay/` | Replay page and developer notes |
| `outreach/` | Social graphics, animations and post drafts |
| `data/` | Not in git (except `data/kd/flood_events.csv`); rebuilt by the download scripts into `data/raw/`, `data/processed/` and `data/kd/` |

Related public repositories, made from this one: [kampala-drain-watch](https://github.com/gavacharles/kampala-drain-watch) (copy of `tool/`, served on GitHub Pages) and [where-is-the-el-nino-rain](https://github.com/gavacharles/where-is-the-el-nino-rain) (copy of outreach graphics).

## Setup and running

```
pip install -r requirements.txt
sh src/run_all.sh                        # climate report pipeline (downloads about 1 GB)
python src/report_images.py              # web-sized figures for report/index.html
```

### Climate report scripts

| Script | Figures | Topic |
| --- | --- | --- |
| `zones.py` | fig01 | Rainfall-regime regions |
| `rain_trends.py` | fig02–06 | Seasonal and extreme rainfall trends, annual cycle by epoch |
| `seasons.py` | fig07–09 | Onset, cessation and length of each rainy season |
| `climate_params.py` | fig10–13 | Temperature, wind, humidity, radiation, ET0, soil moisture |
| `forecast.py` | fig14–19 | ENSO/IOD links, hindcast skill, seasonal outlook |
| `regional_global.py` | fig20–22 | Uganda against East Africa, Africa and the world |
| `water.py` | fig23–26 | Water balance and scarcity, CMIP6 projections |
| `food_irrigation.py` | fig27–28 | Growing period, failed seasons, irrigation requirement |
| `drainage.py` | fig29–30 | Gauge-calibrated design storms, IDF curves, climate uplift |
| `bulk_water.py` | fig31–32 | Design droughts, SPI, treatment drivers |
| `maps.py` | fig33–37 | Satellite overview and close-ups |

### Five-city flooding and food-security scripts

`kampala_catchments.py <city>`, `kampala_flood.py <city>`, `cities_compare.py`, `fetch_city.py` (flooding); `food_paper.py`, `food_divergence.py`, `food_vci_figure.py` (food security).

### Kampala drainage scripts (`src/kd_*.py`)

| Script | Output | Purpose |
| --- | --- | --- |
| `kd_fetch.py`, `kd_fetch2.py` | `data/kd/` | OpenStreetMap drains, culverts, wetlands, waste points, roads, facilities; hourly weather |
| `kd_rain.py` | kd01–kd03 | Kampala rainfall trends and flood-day rainfall |
| `kd_network.py` | `results/kd_segments.csv`, `data/kd/segments.gpkg` | Channel stretches with pressure, priority and risk scores |
| `kd_satellite.py` | satellite layers | Landsat, Sentinel-1/2 and land-cover downloads and composites |
| `kd_maps.py` | kd04–kd12 | Priority and risk maps, drivers, wetland loss, radar |
| `kd_areas.py`, `kd_flythrough.py` | `figures/kampala_drainage/areas/` | Per-hotspot pages and walk-through videos |
| `kd_anim.py`, `kd_anim2.py`, `kd_radar.py`, `kd_radar_storm_anim.py` | kd14–kd22, animations | Animations and radar products |
| `kd_3d.py`, `kd_sculpt3d.py` | `figures/kampala_drainage/3d/` | 3D films |
| `kd_tests.py`, `kd_catalogue.py`, `kd_threshold.py` | kd23–kd26 | Hold-out and other tests; news-based flood catalogue |
| `kd_sponge.py`, `kd_access.py`, `kd_hydraulics.py`, `kd_damage.py`, `kd_heat.py`, `kd_capacity.py`, `kd_cities.py`, `kd_cities_roads.py`, `kd_paperD.py` | kd27–kd56 | Analyses for the drainage manuscripts |
| `kd_tool_promo.py`, `kd_programme_map.py` | demo, kd00 | Tool demo render; programme diagram |

## Data sources

Rainfall: CHIRPS v2.0, ARC2, GHCN-Daily, NASA POWER. Temperature: NOAA CPC, NASA POWER, GHCN-CAMS. Other climate variables: NASA POWER, CPC soil moisture, GPCP v2.3, NOAA ERSST v5 and ONI, CMIP6 (Pangeo). Vegetation and food: NOAA STAR VHI, FEWS NET IPC, FAOSTAT. Settlements and land cover: JRC GHSL R2023A, Microsoft building footprints, ESA WorldCover, Impact Observatory. Infrastructure: OpenStreetMap (ODbL). Terrain and imagery: Copernicus GLO-30, Sentinel-1/2 (Microsoft Planetary Computer), Landsat, Esri World Imagery. Flood records: KCCA and NEMA hotspot lists, news sources, GDELT. Boundaries: Natural Earth, geoBoundaries.

## Credit and licence

Analysis, graphics and text by Gava Charles. Third-party data remain under their own licences (OpenStreetMap and Microsoft buildings under ODbL; Copernicus, JRC, NASA, NOAA and ESA data under their open terms).
