#!/bin/sh
# Full pipeline, in order. Run from the project root: sh src/run_all.sh
set -e
cd "$(dirname "$0")"
PY=../.venv/bin/python
$PY fetch_data.py            # CHIRPS, CPC temperature, GHCN-CAMS, GPCP, ERSST, boundaries
$PY fetch_extra.py           # CPC soil moisture, NASA POWER monthly, CMIP6
$PY fetch_extra.py power_daily
$PY zones.py                 # fig01 rainfall-regime zones
$PY rain_trends.py           # fig02-06 rainfall trends, extremes, annual cycle by epoch
$PY seasons.py               # fig07-09 onset / cessation / length of rainy seasons
$PY climate_params.py        # fig10-13 temperature, wind, humidity, radiation, ET0, soil moisture
$PY forecast.py              # fig14-19 2026 status, ENSO/IOD, forecast skill, OND 2026 outlook
$PY regional_global.py       # fig20-22 East Africa, Africa, global comparison
$PY water.py                 # fig23-26 water balance now and CMIP6 future
$PY food_irrigation.py       # fig27-28 growing seasons, irrigation requirement
$PY drainage.py              # fig29-30 design storms, IDF (gauge-calibrated)
$PY bulk_water.py            # fig31-32 multi-year droughts, treatment drivers
$PY maps.py                  # fig33-37 satellite base maps and close-ups
