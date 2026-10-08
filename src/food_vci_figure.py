"""Figure fp03: growing-season vegetation condition (NOAA VHP VCI over cropland), first vs second season, 1982-2025."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import BLUE, CAT, GRID, INK2, MUTED, ORANGE, PROC, save

v = pd.read_csv(PROC / "vhi_uganda_weekly.csv")
v["district"] = v.province_id.map(pd.read_csv(PROC / "vhp_provinces.csv").set_index("province_id").name)
v = v[~v.district.str.startswith("Lake")]
lvc = ["Kampala", "Wakiso", "Mukono", "Jinja", "Mayuge", "Masaka", "Mpigi", "Iganga", "Bugiri", "Busia", "Kayunga"]
fig, axs = plt.subplots(1, 2, figsize=(13, 4.3))
for s, w, c, lab in (("S1", (17, 28), ORANGE[4], "First season (Apr-Jul)"), ("S2", (43, 52), BLUE[4], "Second season (Oct-Dec)")):
    x = v[(v.week >= w[0]) & (v.week <= w[1]) & ~v.district.isin(lvc)].groupby(["district", "year"]).VCI.mean().unstack(0).loc[1982:2025]
    axs[0].plot(x.index, x.median(1), color=c, lw=1.8, label=lab)
    axs[0].plot(x.index, x.median(1).rolling(9, center=True, min_periods=5).mean(), color=c, lw=3, alpha=0.35)
    axs[1].plot(x.index, 100 * (x < 35).mean(1).rolling(5, center=True, min_periods=3).mean(), color=c, lw=2, label=lab)
for ax in axs:
    ax.axvline(2012.5, color=MUTED, ls=":", lw=1)
    ax.text(2012.8, ax.get_ylim()[1] * 0.95, "AVHRR | VIIRS", fontsize=7, color=INK2, va="top")
axs[0].set_ylabel("median district VCI (0-100)")
axs[0].set_title("a  Vegetation condition in the growing season (outside the Lake Victoria crescent)")
axs[1].set_ylabel("% of districts with VCI < 35 (5-yr mean)")
axs[1].set_title("b  Share of districts in vegetation drought")
axs[0].legend(fontsize=8)
save(fig, "fp03_vci_seasons.png")
