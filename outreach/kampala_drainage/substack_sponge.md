# The sponge we paved

*Gava Charles*

**Subtitle:** Kampala's valley swamps once soaked up storms and cleaned the water flowing into Lake Victoria. We have built over half of them. Here is the bill.

**Cover image:** `x6_sponge_pools.png` (or a frame of `kd_a3_wetlands_timelapse.gif`).

---

Ask anyone who grew up in Kampala in the 1980s about Kinawataka, Nakivubo or Lubigi, and they will describe papyrus. Tall green swamps filled the valley floors between the hills. Children were told to keep away from them.

Those swamps were not wasted land. They did two jobs for the city, for free:
1. **They held storm water.** When it rained, water spread out across the swamp and drained away slowly, instead of racing down a concrete channel into someone's house.
2. **They cleaned the water.** Sewage and runoff from the city filtered through the papyrus before reaching Lake Victoria, where Kampala gets its drinking water.

I measured, from satellite data and a terrain model, how much of both jobs is still being done.

## Job 1: holding the water

Picture each valley floor as a shallow basin. When a channel overflows, water spreads into it. I measured how much water Kampala's valley floors can hold up to a metre above the drains, then subtracted everything that has been built, paved or filled.

> **[GRAPHIC: `x6_sponge_pools.png`. 17 million m³ ≈ 6,800 Olympic swimming pools.]**

Between 1975 and 2020:
- the valleys lost **8.5 million m³** of room for flood water, and
- paving added **8.5 million m³** of extra runoff from a single 10-year storm, because rain that used to soak in now runs off roofs and roads.

Together that is **17 million m³, about 6,800 Olympic swimming pools**, that the city's drains must now carry in one big storm and that the landscape used to absorb.

> **[GRAPHIC: `x7_living_sponge.png`. Share of each channel's valley floor still green, 1986 vs 2025.]**

The green, living part of the sponge shrank fastest:
- **Nalukolongo:** 84% green in 1986, **7%** in 2025;
- **Kinawataka:** 98% to **23%**;
- **Lubigi:** 96% to **36%**;
- **Nakivubo:** 84% to **49%**.

I checked this a second way, using machine learning. I trained a model on modern land-cover maps and used it to classify every valley floor in the old Landsat images. It tells papyrus apart from gardens, trees and roofs. The answer is starker: built and bare ground went from **3% of Kampala's valley floors in 1986 to 35% in 2025**. On the Nalukolongo it is now **93%**, and on the Kinawataka **75%**.

> **[ANIMATION: `kd_a11_valley_landcover_ml.gif`, with `x9_valley_landcover_2025.png` (or `kd44_valley_landcover_ml.png`) as the still. What the valley floors became, 1986 to 2025.]**

> **[ANIMATION: `kd_a3_wetlands_timelapse.gif`, with `kd16_wetlands_timelapse_panels.png` as a still. Lubigi to Kinawataka from space, 1986–2025, with today's channels drawn on.]**

In 1975, five of Kampala's six main channel systems had more valley storage than one 10-year storm's runoff. They could swallow the storm. By 2020, none could comfortably. The water that the swamps used to hold now goes into homes in Bwaise, Kalerwe and Kinawataka.

## Job 2: cleaning the water

The second job gets far less attention.

In the 1990s, scientists measured what the Nakivubo swamp was doing to the city's wastewater on its way to the lake. It removed about **half the nitrogen, 40% of the phosphorus and 91% of the faecal bacteria**. Economists priced that service at **US$1,500–2,900 per hectare per year**, the cost of the treatment plant you would otherwise need to build.

So I measured the swamps that drain into Inner Murchison Bay, the arm of Lake Victoria next to the city: the Nakivubo, Kinawataka and Kansanga valleys.

> **[GRAPHIC: `x8_bay_treatment.png`. Green wetland draining to Murchison Bay: 1,200 ha in 1986, 587 ha in 2025.]**

**Half of it is gone: from 1,200 hectares in 1986 to 587 today.** Kinawataka has lost 78%. That is roughly **US$1–2 million a year of free water treatment** the city no longer gets. In nutrients, it is about 64 tonnes of nitrogen and 9 tonnes of phosphorus a year that now flow on to the lake instead of being held in the swamp.

## You can see it from space

Satellites can measure how murky and how green lake water is. I took every clear image of the bay since 1984, about 900 scene-days, and compared the water where Kampala's channels enter with the open lake further south, on the same day.

> **[GRAPHIC: `kd42_bay_plumes.png`. The bay from space: where the channels enter, a dry day, and the day after heavy rain.]**

What it shows:
- **The bay is green where the city drains into it.** The algae index at the channel mouths is about **four times** that of the open lake.
- **It is getting worse as the swamps disappear.** In the late 1980s and early 1990s, the water at the channel mouths was about 14% murkier than the open lake. Today it is **51% murkier**. The more wetland was lost, the bigger the gap.
- **Storms make it worse, but it is bad even in dry weather.** After heavy rain, plumes of brown water spread across the inner bay. But the channel mouths are degraded even after a week without rain.

> **[GRAPHIC: `kd43_bay_wetland_turbidity.png`. Wetland lost, the growing gap between the outlets and the open lake, and the algae gradient.]**

Kampala's drinking water is drawn from this bay at Ggaba. The dirtier the water arriving at the intake, the more it costs to treat.

## One loss, two bills

Kampala now pays twice for the same lost swamps: once in floods and once in dirtier lake water. That is why the remaining wetland should be treated as **infrastructure**, not empty land waiting for a building permit.

What that would mean:
1. **Gazette and protect what is left**, about 587 hectares in the bay's valleys, plus the remaining Lubigi and Kansanga swamps. Every hectare holds flood water and cleans the lake.
2. **No net loss of storage.** Anyone who builds on a valley floor provides equal storage elsewhere: a detention pond, a restored wetland, tanks.
3. **Restore where possible.** Each 100 hectares of restored swamp is worth roughly US$150,000–290,000 a year in water treatment alone, before counting flood protection.
4. **Connect sewers**, so the wetlands polish treated water instead of absorbing raw sewage.
5. **Count it.** KCCA, NEMA and NWSC could track wetland area and bay water quality from free satellite data every month. The method in this post runs on public data.

The swamps were never empty. They were working. We just stopped noticing until the bills arrived.

---

*Methods and data: Landsat 5/7/8/9 and Copernicus Sentinel-2 imagery (via Microsoft Planetary Computer); Copernicus 30 m DEM; JRC Global Human Settlement Layer; CHIRPS rainfall; turbidity method of Dogliotti et al. (2015); chlorophyll index of Mishra and Mishra (2012); wetland treatment rates and values from Kansiime and Nalubega (1999) and Emerton et al. (1999). Satellite water-quality values are relative indices, not laboratory measurements. All graphics: Credit: Gava Charles.*
