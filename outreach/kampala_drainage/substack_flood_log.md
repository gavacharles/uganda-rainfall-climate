# Kampala floods every rainy season. Nobody is counting.

*Gava Charles*

**Subtitle:** I pieced together the city's first open flood record from 20 years of news. It has a four-year hole, and that hole is the story.

**Cover image:** `x4_four_silent_years.png` (or `kd41_flood_catalogue.png`).

---

On Sunday 11 October, rain began falling on Kampala at around 3 a.m. By morning the Hoima road at Lubigi was a river. A wall collapsed onto a rented room and two people died. For a day or two it was the main story on every Ugandan news site.

Then the next story came along, and the flood went where Kampala's floods always go: into the archive, scattered across a dozen websites, often without a proper date or place.

So here is a simple question. **How many times has Kampala flooded since 2007, and where?**

Nobody can tell you. KCCA does not publish a flood log. The global disaster databases only record big disasters, and a flash flood that closes Jinja Road for an afternoon is not one of them. So I tried to build the record myself.

## How I built it

I combined two sources:
- **a global news index (GDELT)**, which tracks online news worldwide, searched for every Kampala flood story from 2017 to 2026 and kept only floods reported by at least two separate outlets;
- **a manual search** of the Daily Monitor, New Vision, NTV, The Observer, Uganda Radio Network, KFM, ReliefWeb and FloodList back to 2007, reading every report.

Each flood got a date, a grade for how well it is documented, the places named, the deaths reported, and the satellite rainfall that day.

The result: **22 floods, 2007–2026, with 26 people reported dead.** That is certainly not every flood. It is every flood I could prove.

> **[GRAPHIC: `kd41_flood_catalogue.png`. Left: every recorded flood by year and death toll. Right: the places named in flood reports.]**

## Three things the record shows

**1. The same places, again and again.**
Bwaise appears in 5 separate floods, and Kalerwe, Banda and Kyambogo in 4 each. Katwe, Ndeeba, Kyebando and the Clock Tower area each appear twice. They sit on the three channels that rank worst in my drainage analysis: the Lubigi, the Kinawataka and the Nakivubo. Floods in Kampala are not random. They return to the same few valleys.

**2. It does not take a big storm.**
On the median flood day, satellite rainfall over Kampala ranked only around the 74th percentile of normal wet days. On 7 of the 18 dated floods, it recorded less than 5 mm.

> **[GRAPHIC: `x1_floods_ordinary_rain.png`. Rain on flood days, as a percentile of all wet days.]**

Satellites do miss the short local cloudbursts. On 29–31 October 2025 the Makerere gauge measured 63 mm while the satellite saw 21 mm. But even allowing for that, the pattern holds: Kampala floods on rain a working drainage system should carry.

**3. Four silent years.**
Between April 2021 and March 2025, I could not find a single flood reported by more than one outlet.

> **[GRAPHIC: `x4_four_silent_years.png`. Top: floods on record each year. Bottom: how many Kampala news stories the index holds each year.]**

Kampala did not stop flooding in 2021. December 2024's downpour that paralysed the city centre shows up only in a later commentary. What changed was the reporting. The number of Kampala stories in the global news index fell by about 85% between 2017 and 2024, and the floods that did happen were covered locally, on radio and social media, where no archive catches them.

In other words, **Kampala's flood record measures how busy journalists were, not how often the city flooded.**

## Why this matters

Without a proper record, we cannot answer the questions that decide how money is spent:

- **Is flooding getting worse?** My earlier analysis could not tell whether it now takes less rain to flood Kampala. The record is too short and too patchy to test.
- **When should we warn people?** Cities like Alexandria in Egypt have set rain-based flood warnings by matching past floods to rainfall, using newspaper and social-media records (Young et al., 2021). Kampala could do the same, but only with dated floods.
- **Did the works help?** KCCA has rebuilt culverts on Ssebaana and Allen Roads and improved the Lubigi and Nakamiro channels. Did flooding at those places fall? Without a log, nobody can show it.
- **Who is hit?** Deaths, displaced families and closed clinics go uncounted, and so do not show up in any budget.

## What a flood log would look like

It does not need new technology. It needs one line per flood.

> **[GRAPHIC: `x5_flood_log_card.png`. The seven fields of a flood log, with 11 October 2026 as an example.]**

- **Who fills it in:** KCCA parish and ward officers, Uganda Red Cross volunteers, and residents.
- **What it records:** when, where (a GPS point), how deep, what closed, who was affected, why it happened, and a photo.
- **What happens next:** KCCA publishes it every quarter. UNMA adds the rain-gauge reading for the same day.

Within three or four rainy seasons, Kampala would know its flood thresholds, its worst places, and whether its investments work.

## You can start it today

Kampala Drain Watch, the open map I built, already lets anyone log a flood with the date, the place and a photo. Every confirmed report becomes a dated record that this catalogue can use.

**→ Log a flood: gavacharles.github.io/kampala-drain-watch**

If you have photos or videos of past floods with a date and place, especially from 2021–2024, please send them. Help fill the silent years.

The catalogue itself, all 22 events with sources, places and rainfall, is open. I am writing it up as a data paper so that researchers, KCCA and journalists can build on it.

---

*Methods and data: flood reports from Daily Monitor, New Vision, NTV Uganda, The Observer, Uganda Radio Network, KFM, ChimpReports, allAfrica, ReliefWeb and FloodList; GDELT news index; CHIRPS v2.0 and NASA POWER rainfall. Places are approximate (±500 m). Map data © OpenStreetMap contributors. All graphics: Credit: Gava Charles.*
