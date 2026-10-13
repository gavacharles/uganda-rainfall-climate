"""One-page map of the Kampala drainage research programme -> figures/kampala_drainage/kd00_research_programme_map.png"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from common import FIG, save

OUT = FIG / "kampala_drainage"


def box(ax, x, y, w, h, title, body, fc, ec):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.012", fc=fc, ec=ec, lw=1.4))
    ax.text(x + 0.012, y + h - 0.018, title, fontsize=10.5, fontweight="bold", va="top", color="#1a1a1a")
    ax.text(x + 0.012, y + h - 0.058, body, fontsize=8.3, va="top", color="#333", linespacing=1.35)


def arrow(ax, a, b, c="#888"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=12, color=c, lw=1.1, shrinkA=2, shrinkB=2))


def main():
    fig = plt.figure(figsize=(16, 10))
    ax = fig.add_axes([0, 0, 1, 0.93])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.text(0.01, 0.975, "Kampala drainage and wetlands: one open-data base, six papers, one tool", fontsize=17,
             fontweight="bold", va="top")
    fig.text(0.01, 0.94, "Thread: Kampala's floods are increasingly a drainage-capacity and encroachment problem, not a "
             "rainfall problem - and open data can show where the next hotspots are forming.", fontsize=11, color="#555",
             va="top")
    G, Gc = "#eef3f8", "#5b7c99"
    box(ax, 0.01, 0.06, 0.22, 0.86, "Shared open-data base",
        "• 12,453 channel segments (~900 km)\n  OpenStreetMap drains & culverts\n• 3,135 culverts, 1,063 bridges\n"
        "• 1,553 waste/dump points, 130 markets\n• 537,000 building footprints\n  (Microsoft, 2023)\n"
        "• Built-up & population 1975-2030\n  (JRC GHSL)\n• Valley floors from 30 m DEM\n  (Copernicus)\n"
        "• Landsat 1986-2025\n• Sentinel-1 radar 2017-2026\n• Sentinel-2 2017-2026\n• CHIRPS rain 1981-2026,\n"
        "  NASA POWER hourly 2001-2026\n• 43 reported hotspots,\n  9 dated floods (growing)", G, Gc)
    papers = [
        ("D0  Flood catalogue 2000-2026 (data paper)", "Dated, geocoded floods from news & official\nreports. Unlocks A and C.  -> Scientific Data / ESSD", "#fff4e0", "#d08a00"),
        ("A  Rainfall or drainage?  (MAIN PAPER)", "Does it now take less rain to flood Kampala,\nand where will the next hotspots form?  -> JFRM / NHESS", "#fde8e8", "#b00020"),
        ("B  Radar tracking of wetland encroachment", "Sentinel-1 yearly change on valley floors,\ncloud-free, 2017-2026.  -> JAG / ISPRS", "#e8f1fd", "#1f5fa8"),
        ("C  Waste, culverts and floods", "City-wide test of the dumping -> blocked\nculvert -> flood chain.  -> Waste Management / STOTEN", "#eef8ea", "#2e7d32"),
        ("D  Moving into the water's path", "People on low ground beside channels,\n1975-2030.  -> Landscape & Urban Planning / ERL", "#f3ecfa", "#6a3d9a"),
        ("E  Satellites as drainage inspectors", "Sentinel-2 clogging & clearing in wide\nchannels.  -> Urban Water Journal / JAG", "#eaf7f7", "#00796b"),
    ]
    y = 0.80
    pos = {}
    for t, b, fc, ec in papers:
        box(ax, 0.30, y, 0.40, 0.115, t, b, fc, ec)
        pos[t[:2].strip()] = y
        arrow(ax, (0.235, 0.49), (0.298, y + 0.057))
        y -= 0.148
    box(ax, 0.77, 0.30, 0.22, 0.40, "T  Open maintenance dashboard",
        "• Segment priority & emerging risk\n• Radar encroachment alerts (B)\n• Channel clogging signal (E)\n"
        "• Rain-forecast flood trigger (A)\n• Population at risk (D)\n• Field reports: floods, blockages,\n"
        "  dumping -> grows D0\n\n-> Env. Modelling & Software /\n   SoftwareX", "#f5f5f5", "#444")
    for k in ("A", "B", "C", "D", "E"):
        arrow(ax, (0.702, pos[k] + 0.057), (0.768, 0.5), c="#bbb")
    ax.plot([0.88, 0.88], [0.703, 0.857], color="#d08a00", lw=1.3)
    arrow(ax, (0.88, 0.857), (0.703, 0.857), c="#d08a00")
    ax.text(0.885, 0.78, "field reports feed the\nflood catalogue (D0),\nwhich retrains A and C", fontsize=8.5,
            color="#d08a00", va="center")
    ax.text(0.30, 0.02, "Order: D0 -> B and D (data in hand) -> A -> C -> E; tool built alongside.", fontsize=10,
            fontweight="bold", color="#333")
    save(fig, "kd00_research_programme_map.png", OUT,
         source="Programme plan by Gava Charles. Data: OpenStreetMap contributors, Microsoft Building Footprints, JRC GHSL, "
                "Copernicus DEM / Sentinel-1 / Sentinel-2, NASA/USGS Landsat, CHIRPS, NASA POWER.")


if __name__ == "__main__":
    main()
