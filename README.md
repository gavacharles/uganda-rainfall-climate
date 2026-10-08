# Uganda rainfall & temperature, 1981–2026: patterns, shifting seasons, forecasting and engineering advice

Everything for this study lives in this folder.

| Folder | What goes in it |
| --- | --- |
| `data/raw/` | Downloaded source files as received (ENSO/IOD index text files, temporary CHIRPS yearly subsets) |
| `data/processed/` | Cleaned, subset datasets used by the analysis (NetCDF/GeoJSON) |
| `src/` | All Python code (download, analysis, models, figures) |
| `figures/` | All maps and graphs (PNG) |
| `results/` | Tables of results (CSV) and run logs |
| `models/` | Trained machine-learning models and forecast outputs |
| `report/` | The written report (HTML) and exports |
| `docs/` | Notes, methods, data sources and references |

## Data sources
- **Rainfall**: CHIRPS v2.0 daily, 0.25° (UCSB Climate Hazards Center), 1981–present; CHIRPS preliminary for the latest weeks; 7 GHCN-Daily gauges (1926–1986) to calibrate extremes
- **Temperature**: NOAA CPC Global Daily Tmax/Tmin, 0.5°; NASA POWER daily (MERRA-2); GHCN-CAMS monthly land temperature (Uganda, Africa, world)
- **Wind, humidity, radiation, pressure**: NASA POWER daily (MERRA-2 / CERES), regridded to 0.5°
- **Soil moisture**: CPC leaky-bucket model, 0.5°
- **Global rainfall**: GPCP v2.3 monthly, 2.5°
- **Ocean drivers**: NOAA ERSST v5 (Niño-3.4, Indian Ocean Dipole and its poles), NOAA CPC ONI
- **Projections**: CMIP6 (Pangeo Google Cloud zarr), r1i1p1f1, historical + SSP2-4.5 + SSP5-8.5
- **Boundaries and imagery**: Natural Earth, geoBoundaries (Uganda ADM2 = 151 counties), Esri World Imagery tiles

## Running
```
sh src/run_all.sh                       # full pipeline (downloads ≈ 1 GB kept)
.venv/bin/python src/report_images.py   # web-sized figures for report/index.html
```

| Script | Figures | What it answers |
| --- | --- | --- |
| `zones.py` | fig01 | Six rainfall-regime regions |
| `rain_trends.py` | fig02–06 | Seasonal and extreme rainfall trends, annual cycle by epoch |
| `seasons.py` | fig07–09 | Onset, cessation and length of each rainy season |
| `climate_params.py` | fig10–13 | Temperature (3 sources), wind, humidity, radiation, ET0, soil moisture |
| `forecast.py` | fig14–19 | 2026 so far, ENSO/IOD links, hindcast skill, OND 2026 outlook |
| `regional_global.py` | fig20–22 | Uganda vs East Africa, Africa, world |
| `water.py` | fig23–26 | Water balance and scarcity by county, CMIP6 future |
| `food_irrigation.py` | fig27–28 | Growing period, failed seasons, irrigation requirement and design duty |
| `drainage.py` | fig29–30 | Gauge-calibrated design storms, IDF, climate uplift |
| `bulk_water.py` | fig31–32 | Design droughts, SPI, treatment drivers |
| `maps.py` | fig33–37 | Satellite overview and close-ups (Kampala, Elgon, Karamoja, south-west) |
