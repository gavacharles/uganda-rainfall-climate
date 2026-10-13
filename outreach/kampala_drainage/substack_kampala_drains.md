# Kampala isn't drowning in rain. It's drowning in its drains.

*Gava Charles*

**Cover image (Substack post settings):** `cover_substack_1456x1048.png` (1456 × 1048).

**Subtitle:** The storms haven't got heavier in 45 years. The channels have been built over, blocked and squeezed, and the data shows where the next floods are coming.

---

> **[GRAPHIC: `kd3d_sculpt.mp4` or a frame from it as the header image. Kampala's channels glowing on a dark relief, concrete rising, water filling the valleys.]**

On Sunday morning, 11 October, rain started around 3 a.m. By daybreak the Kampala–Hoima road at Lubigi was under water. Motorists inched through floodwater at Kinawataka and Banda, and young men charged 5,000 shillings to carry people across. The evening before, homes in Kimbejja had flooded and walls had collapsed.

It happens every rainy season, and every season the same argument follows: is it climate change, or is it us?

I spent the past weeks putting that question to the data. I used only open sources: satellite rainfall back to 1981, a map of every drain and culvert volunteers have put on OpenStreetMap, more than half a million building footprints, 50 years of built-up and population maps, a 30-metre terrain model and ten years of radar. Here is what it shows.

## 1. The storms have not got heavier. The floods come on ordinary rain.

Across Greater Kampala, the wettest day of the year has not grown since the early 1980s. If anything it has edged down (about −1 mm per decade, not statistically significant). The wettest three days are flat. Total rain per year is up about 15%, which matters for water supply, but it is not what turns a street into a river.

Then I looked at the rain on the days Kampala actually flooded.

> **[GRAPHIC: `x1_floods_ordinary_rain.png`. Rain on reported flood days, as a percentile of all wet days.]**

Some were genuinely heavy days, such as 14 March 2023 at the 96th percentile. But 31 October 2025, when three people died in the Kisenyi channel, was around the 60th percentile by satellite. The floods of 6 March 2026 at Centenary Park and 17 September 2026 at Banda came on rain that ranked about the 20th percentile: an unremarkable wet day.

One caveat: satellites average rain over 5 km squares and miss the local cloudburst. On 29–31 October 2025 the Makerere gauge recorded 63 mm while the satellite saw 21 mm. Even allowing for that, the pattern is clear. Kampala floods on rain it should be able to carry.

## 2. What the flood hotspots have in common

I cut every drain in Greater Kampala into 200-metre stretches, 6,914 of which carry real flow, and measured the pressures on each. Then I asked which pressures set apart the channels near the 45 places where flooding has been reported.

> **[GRAPHIC: `kd04_priority_overview.png`. Every channel stretch coloured by maintenance priority, with reported hotspots circled.]**

Four things stand out:

- **Homes on the floodplain:** buildings standing less than 2 metres above the drain, within 150 m of it.
- **Buildings inside the channel reserve:** structures within 15 metres of the channel's centreline.
- **Constrictions:** culverts and bridges, the pinch points where silt and rubbish lodge.
- **Lost wetland:** around most hotspots, less than 1% of the land within 500 m is still wetland.

A simple, transparent score built from these pressures picks out the hotspot channels well (AUC 0.73). What does not set them apart is how much paving was added upstream recently. Today's hotspots are in places that were built over decades ago: Bwaise, Kalerwe, Kisenyi, Nalukolongo.

> **[GRAPHIC: `kd13_01_bwaise_kalerwe.png`. The Bwaise–Kalerwe page: 22 km of channel, 1,039 buildings within 15 m of the channels, 163 dump points within 100 m, 79 culverts.]**

> **[VIDEO: `kd_fly_01_bwaise_kalerwe_social.mp4`. A slow fly-along down the Lubigi and Nsooba channels, with each building in the reserve, culvert and dump site called out as we pass.]**

## 3. We can see the next hotspots coming

If today's hotspots were built over long ago, where are tomorrow's? I built an early-warning score using only what changed between 1975 and 2000: paving creeping up the catchments and building spreading onto the valley floors. Then I checked it against what actually happened next.

> **[GRAPHIC: `x2_next_hotspots.png`. Valley floor built over 2000–2020, by the 1975–2000 score.]**

Where the score was highest, four times more valley floor was built over in the following 20 years. The score anticipates encroachment (AUC 0.79), and run today it points to the northern and eastern fringe, the Kinawataka and Kansanga headwaters, and the edges of Kira and Nansana.

> **[GRAPHIC: `kd12_priority_vs_emerging.png`. How much work is waiting: 138 km of channel is high priority now and still worsening; 100 km is not yet high but rising fast.]**

## 4. The wetlands that used to hold the water

> **[ANIMATION: `kd_a3_wetlands_timelapse.gif`, with `kd16_wetlands_timelapse_panels.png` as a still. Lubigi to Kinawataka from space, 1986–2025, with today's channels drawn on.]**

The dark green valley floors in the 1986 image were papyrus swamps that soaked up storm water. Watch them fill with roofs. Kampala's drainage was designed around wetlands that, around most hotspots, are now gone.

## 5. People in the water's path

> **[GRAPHIC: `x3_people_low_ground.png`. Residents on low ground beside channels: 36,000 in 1975, 205,000 in 2020, about 247,000 by 2030.]**

About 205,000 people now live on low ground within 150 metres of a Kampala drainage channel, nearly six times as many as in 1975. Most of that is simply the city growing. But between 1975 and 2000, people also moved disproportionately onto low ground: cheap land in the valleys, settled by those with the fewest options.

## 6. What satellites can and cannot do

> **[GRAPHIC: `kd10_sentinel1_after_storm.png`. Radar view of Kampala 13 hours after the 11 October storm.]**

Radar sees through cloud, so I looked at Kampala on the afternoon after the 11 October storm. There was almost no standing water left. Kampala's floods are flash floods that rise and drain within hours, faster than any satellite revisit.

Radar can pick up some new building on open land.

> **[GRAPHIC: `kd22_radar_cluster_zooms.png`. New estates and industrial parks seen by radar.]**

But it catches only a small share of new homes, so it gives leads for inspection, not a count. Flood detection needs rain gauges, water-level sensors at key culverts, and reports from people on the ground.

## 7. What this means for NDP IV, KCCA and NEMA

The pressures that separate Kampala's flood hotspots are planning and enforcement variables, not weather:

1. **Clear and enforce the drainage reserve** on the stretches that rank high now. Start where buildings narrow or cover the channel.
2. **Desilt culverts before every rainy season**, and fit trash screens upstream of the worst ones.
3. **Protect what wetland is left as flood storage.** Around most hotspots it is under 1% of the land; every hectare matters.
4. **Use the early-warning map for development control** on the fringe now, while it is still cheaper than retrofitting.
5. **Measure:** a few dozen rain gauges and culvert sensors would tell us more about Kampala's floods than any satellite.

## A tool for the people who do the work

I have built an open maintenance map, **Kampala Drain Watch**. It ranks every channel stretch, shows why each one ranks where it does, and lets KCCA crews and residents log blockages, dumping, flooding and completed works in one shared record. *[Link: share the dashboard from its Share menu before posting.]*

Next: a full news-based flood catalogue for 2017–2026, to test directly whether the rain needed to flood Kampala has fallen.

---

*Methods and data: CHIRPS v2.0 and NASA POWER rainfall; OpenStreetMap drains, culverts and waste points (© OpenStreetMap contributors); Microsoft building footprints; JRC Global Human Settlement Layer built-up and population, 1975–2030; Copernicus 30 m DEM; ESA WorldCover; Landsat; Sentinel-1. Flood reports from Daily Monitor, New Vision, NTV Uganda, The Observer, KFM, ReliefWeb and FloodList. Hotspot positions are approximate. All graphics: Credit: Gava Charles.*
