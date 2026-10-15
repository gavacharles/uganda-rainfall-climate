"""Embed numbered figures (with captions) in the five Kampala papers and the data paper, then export Word files.

For each paper: main figures are numbered in order, placed after the first paragraph that cites them, and in-text
codes ("Fig. kd44", "Figs. kd04, kd06") become "Figure N". Supplementary figures go to a closing section (Figure S1...).
The old "# Figures" list is replaced by a short note. Idempotent: run on the clean drafts (it strips earlier embeds).
"""
import re
import sys

import pypandoc

from common import ROOT

P = ROOT / "paper"
F = "../figures/kampala_drainage/"

SPEC = {
    "P0_flood_catalogue_data_paper": dict(
        main=[("cm0", "cm0_case_flood_catalogue.png", "Study area: places named in Kampala's 22 catalogued flood events, 2007–2026, by best record grade and number of events, with the independent KCCA/NEMA and press hotspot list."),
              ("kd41", "kd41_flood_catalogue.png", "The catalogue: (a) events by date, grade, reported deaths and number of outlets, with the 2021–2024 reporting gap shaded; (b) places named in flood reports over the channel network.")],
        supp=[]),
    "P1_rainfall_or_drainage": dict(
        main=[("cm1", "cm1_case_rainfall_or_drainage.png", "Study area: Greater Kampala's six channel systems, channels draining at least 2 km², 45 reported flood hotspots, the KCCA boundary and the Makerere rain gauge."),
              ("fw1", "fw1_study_design_rainfall_or_drainage.png", "Study design: the two explanations tested, the three tests applied to each, and where their results are reported."),
              ("kd02", "kd02_flood_days_rain.png", "Rain on reported flood days as a percentile of all wet days (CHIRPS, Greater Kampala mean)."),
              ("kd41", "kd41_flood_catalogue.png", "Dated flood events 2007–2026 from the flood catalogue (Gava 2026) and the places they affected."),
              ("kd04", "kd04_priority_overview.png", "Maintenance-priority index for every channel stretch, with reported hotspots."),
              ("kd06", "kd06_hotspot_drivers.png", "What sets hotspot channels apart: drainage pressures at hotspots versus other channels."),
              ("kd37", "kd37_design_drift.png", "Design-basis drift: (a) overload ratio of the 10-year flow against 1990 design capacity under each scenario; (b) overloaded channel length by system."),
              ("kd38", "kd38_overload_map.png", "Map of the 2020 overload ratio."),
              ("kd23", "kd23_holdout_encroachment.png", "Temporal hold-out: valley-floor building added in 2000–2020 by quintile of the 1975–2000 emerging-risk score."),
              ("kd05", "kd05_emerging_risk.png", "Emerging-risk map: where the next hotspots are forming.")],
        supp=[("kd12", "kd12_priority_vs_emerging.png", "Current priority against emerging risk for every channel stretch."),
              ("kd26", "kd26_flood_threshold_trend.png", "Falling-threshold test: rain on flood days 2017–2026 and the trend odds ratios."),
              ("kd10", "kd10_sentinel1_after_storm.png", "Sentinel-1 radar about 13 hours after the 11 October 2026 storm: almost no standing water remained.")]),
    "P2_double_loss_wetlands": dict(
        main=[("cm2", "cm2_case_double_loss.png", "Study area: valley-floor land cover today (machine-learning map), the catchments draining to Inner Murchison Bay, the bay zones used for the water analysis and the Ggaba intake."),
              ("lc2", "lc2_nakivubo_then_now.png", "The Nakivubo and Kinawataka valleys from Landsat, 1986 and 2025, with the edge of the valley floor (3 m above the nearest drain)."),
              ("kd44", "kd44_valley_landcover_ml.png", "Machine-learning land cover of the valley floors, 1986 and 2025, and class areas 1986–2025."),
              ("kd30", "kd30_lost_sponge.png", "Flood storage: (a) valley-floor storage against storm runoff 1975–2030; (b) the living sponge, 1986 vs 2025, by system; (c) combined gap by system."),
              ("kd31", "kd31_sponge_lost_map.png", "Map of valley-floor storage lost, 1975–2020."),
              ("kd42", "kd42_bay_plumes.png", "Inner Murchison Bay from Sentinel-2: (a) the outlets; (b) turbidity after a dry spell; (c) turbidity after rain."),
              ("kd43", "kd43_bay_wetland_turbidity.png", "(a) Wetland draining to the bay, 1986–2025; (b) outlet-to-open-lake turbidity ratio from Landsat, 1984–2026; (c) chlorophyll index by zone.")],
        supp=[("kd55", "kd55_valley_vegetation_10m.png", "Valley floors today at 10 m (Sentinel-2, 2024–26) and the agreement of three methods."),
              ("kd16", "kd16_wetlands_timelapse_panels.png", "Landsat time-lapse of the valley wetlands, 1986–2025.")]),
    "P3_building_in_the_waters_path": dict(
        main=[("cm3", "cm3_case_waters_path.png", "Study area: residents on low ground beside the channels in 2020, inside the KCCA boundary and in the Wakiso fringe."),
              ("bg3", "bg3_building_grain.png", "The grain of building: footprints by size in a low-ground neighbourhood (Bwaise) and on a nearby hill (Kawempe), with their size distributions."),
              ("kd27", "kd27_exposure_by_system.png", "Residents on low ground by channel system, 1975–2030."),
              ("kd28", "kd28_settlement_age.png", "Settlement age: first-built period of today's built cells, low ground vs hills."),
              ("kd29", "kd29_building_form.png", "Building size on low ground vs hills, by system."),
              ("kd35", "kd35_heat_flood.png", "Heat and flood: (a) night surface temperature by built-up quintile, low vs higher ground; (b) residents facing heat, flood or both."),
              ("kd36", "kd36_heat_map.png", "Night-time surface temperature with channels and double-exposure cells.")],
        supp=[("kd25", "kd25_exposure_decomposition.png", "Exposure growth decomposed into city growth and a shift toward low ground."),
              ("kd15", "kd15_people_on_low_ground.png", "People on low ground beside channels, 1975 and 2020.")]),
    "P4_silt_not_storms": dict(
        main=[("cm4", "cm4_case_silt_not_storms.png", "Study area: Kampala's road network, the 636 road–channel crossings without a bridge, hospitals, the city centre and the reported flood-prone roads used for validation."),
              ("fw4", "fw4_attribution_design.png", "Attribution design: four drivers switched on and off (16 scenarios), the model chain, Shapley attribution and the uncertainty analysis."),
              ("kd46", "kd46_roads_flood_10yr.png", "Roads impassable in a 10-year storm with clean and with silted channels, and the road floods reported in the news."),
              ("kd54", "kd54_roads_validation.png", "Validation: distance from reported flood-prone roads to modelled impassable main road, against random road locations."),
              ("kd50", "kd50_roads_attribution.png", "Attribution: Shapley shares of paving, siltation, encroachment and climate in road flooding and in people cut off; and the 2-year storm, clean vs silted."),
              ("kd52", "kd52_roads_silt_sensitivity.png", "How much silt does it take: attribution across siltation levels."),
              ("kd53", "kd53_roads_uncertainty.png", "Uncertainty across 400 model versions, and the emulator's ranking of assumptions."),
              ("kd51", "kd51_roads_crossings_priority.png", "The crossings to clear first, ranked by the closures desilting would avoid."),
              ("kd39", "kd39_flood_damage.png", "Building damage: damage per storm, clean vs silted, and avoided damage per km by system."),
              ("kd47", "kd47_roads_over_time.png", "Roads on the valley floors by urbanisation period; urban road on low ground 1975–2020; expected impassable road-km by state."),
              ("kd49", "kd49_roads_lubigi_then_now.png", "Lubigi: today's roads drawn on the 1986 landscape, beside today's imagery.")],
        supp=[("kd45", "kd45_roads_all.png", "Every drivable road in Kampala over shaded relief."),
              ("kd48", "kd48_roads_satellite_closeups.png", "Satellite close-ups of four reported road floods, 10-year storm, silted channels."),
              ("kd32", "kd32_access_scenarios.png", "Access to hospitals under water-level scenarios."),
              ("kd33", "kd33_access_map.png", "Extra travel time to hospital at the 1 m water-level scenario.")]),
    "P5_next_kampalas": dict(
        main=[("cm5", "cm5_case_next_kampalas.png", "Study area: Kampala and the five regional cities, each shown at the same scale with its valley floors and roads on low ground."),
              ("kd40", "kd40_cities_compare.png", "(a) Valley floor built over 1975–2030; (b) people on low ground relative to 2000; (c) 2020–30 growth, low ground vs whole area."),
              ("kd56", "kd56_cities_roads.png", "(a) Share of road on low ground by when its ground urbanised; (b) road on low ground and channel crossings per 100 km, by city.")],
        supp=[]),
}


def jpg(stem):
    """Compressed copy for the Word file (max 2200 px wide, JPEG q85); the Markdown keeps the full PNG."""
    from PIL import Image
    src = ROOT / "figures" / "kampala_drainage" / f"{stem}.png"
    dst = ROOT / "figures" / "kampala_drainage" / "_docx" / f"{stem}.jpg"
    dst.parent.mkdir(exist_ok=True)
    if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
        im = Image.open(src).convert("RGB")
        if im.width > 2200:
            im = im.resize((2200, round(im.height * 2200 / im.width)), Image.LANCZOS)
        im.save(dst, quality=85, optimize=True)
    return str(dst)


def strip(t):
    t = re.sub(r"\n!\[\*\*Figure S?\d+[^\n]*\n", "\n", t)
    t = re.sub(r"\n# Supplementary figures\n.*?(?=\n# References)", "\n", t, flags=re.S)
    return t


def embed(name, spec):
    t = strip((P / f"{name}.md").read_text())
    body = t.partition("\n# Figures\n")[0]
    cited = []
    for g in re.finditer(r"Figs?\. ((?:(?:cm\d|fw\d|lc\d|bg\d|kd\d+)[a-c]?(?:, | and |–)?)+)", body):
        for c in re.findall(r"(cm\d|fw\d|lc\d|bg\d|kd\d+)", g.group(1)):
            if c not in cited:
                cited.append(c)
    order = lambda lst: sorted(lst, key=lambda x: cited.index(x[0]) if x[0] in cited else 999)
    spec = dict(main=order(spec["main"]), supp=order(spec["supp"]))
    num = {c: i + 1 for i, (c, _, _) in enumerate(spec["main"])}
    snum = {c: i + 1 for i, (c, _, _) in enumerate(spec["supp"])}
    lab = lambda c: f"Figure {num[c]}" if c in num else (f"Figure S{snum[c]}" if c in snum else None)
    # split off figures/references
    head, _, tail = t.partition("\n# Figures\n")
    refs = tail[tail.index("\n# References"):] if "\n# References" in tail else ""

    def repl(m):
        codes = re.findall(r"(cm\d|fw\d|lc\d|bg\d|kd\d+)([a-c]?)", m.group(0))
        out = []
        for c, sub in codes:
            l_ = lab(c)
            out.append((l_ + sub) if l_ else c)
        return ", ".join(out) if len(out) > 1 else out[0]
    head = re.sub(r"Figs?\. (?:(?:cm\d|fw\d|lc\d|bg\d|kd\d+)[a-c]?(?:, | and |–)?)+", lambda m: repl(m).replace("Figure ", "Figure ", 1), head)
    head = head.replace("Figure Figure", "Figure")
    blocks = head.split("\n\n")
    placed = set()
    for c, f, cap in spec["main"]:
        l_ = lab(c)
        for i, b in enumerate(blocks):
            if re.search(rf"{l_}(?!\d)", b) and not b.startswith("#") and "![" not in b:
                j = i + 1
                while j < len(blocks) and blocks[j].startswith("![**Figure"):
                    j += 1
                blocks.insert(j, f"![**{l_}.** {cap}]({F}{f}){{width=100%}}")
                placed.add(c)
                break
    head = "\n\n".join(blocks)
    rest = [(c, f, cap) for c, f, cap in spec["main"] if c not in placed]
    note = "\n# Figures\n\nFigures are embedded in the text"
    note += (" (Figures " + ", ".join(str(num[c]) for c, _, _ in rest) + " follow).\n\n" +
             "\n\n".join(f"![**{lab(c)}.** {cap}]({F}{f}){{width=100%}}" for c, f, cap in rest)) if rest else "."
    supp = ""
    if spec["supp"]:
        supp = "\n\n# Supplementary figures\n\n" + "\n\n".join(f"![**{lab(c)}.** {cap}]({F}{f}){{width=100%}}"
                                                              for c, f, cap in spec["supp"])
    out = head.rstrip() + "\n" + note + supp + "\n" + refs
    (P / f"{name}.md").write_text(out)
    docx_text = re.sub(r"\]\(\.\./figures/kampala_drainage/([^)]+)\.png\)", lambda m: f"]({jpg(m.group(1))})", out)
    pypandoc.convert_text(docx_text, "docx", format="md", outputfile=str(P / f"{name}.docx"),
                          extra_args=[f"--resource-path={P}"])
    print(name, "main", len(spec["main"]), "placed in text", len(placed), "supp", len(spec["supp"]))


if __name__ == "__main__":
    for n in sys.argv[1:] or SPEC:
        embed(n, SPEC[n])
