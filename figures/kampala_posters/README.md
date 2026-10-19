# Kampala posters and animations

Map styles vary by purpose. Every image carries its data sources and "Credit: Gava Charles". GIFs are at most 1,200 px wide, so they post directly to X; MP4 versions are for slides and video.

| File | Style | What it shows |
|---|---|---|
| `kp01_kampala_false_colour.png` | satellite poster | Greater Kampala in Sentinel-2 false colour: built-up hills in purple, the remaining wetlands green |
| `kp02_kampala_flood_depth_10yr.png` | emergency-map poster | Where Kampala floods in a 10-year storm: water depth on a greyscale satellite base |
| `kp03_kampala_roads_glow.png` | glowing network | Roads under water in an ordinary 2-year storm: 198 km with silted channels, 5 km with clean ones |
| `kp04_murchison_bay_plume.png` | satellite poster | Inner Murchison Bay: true colour with satellite turbidity on the water |
| `animations/ka01_kampala_spreads` | Landsat time-lapse | Kampala spreading over its valleys, 1986–2025 |
| `animations/ka02_kampala_roads_storm` | glowing network | Roads going under as the storm grows from 2- to 100-year |
| `animations/ka03_kampala_flood_rising` | emergency-map style | The flood rising with the storm, 2- to 100-year |

Code: `src/kp_posters.py` (and `src/kp_s2.py` for the Sentinel-2 composite). Flood depths come from the Kampala drainage screening model; they are indicative, not for design.
