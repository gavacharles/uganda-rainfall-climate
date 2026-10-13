"""Social-media demo of the Kampala Drain Watch tool (rendered from the tool's own data, mimicking its interface)
-> outreach/kampala_drainage/drain_watch_demo.mp4 (16:9, ~24 s) and .gif."""
import json

import imageio.v2 as iio
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyBboxPatch
from PIL import Image

from common import ROOT

T = ROOT / "tool"
OUT = ROOT / "outreach" / "kampala_drainage"
CLS = {"urgent": ("Urgent", "#574249"), "fix": ("Fix now", "#c85a5a"), "coming": ("Coming", "#64acbe"),
       "watch": ("Watch", "#ad9ea5"), "low": ("Low", "#bdbdbd"), "other": ("Mixed", "#cfcfcf")}
BG, PANEL, INK, MUTE, ACC = "#f4f2ee", "#ffffff", "#1d2328", "#5d6870", "#0b7a8a"


def ease(t):
    return t * t * (3 - 2 * t)


def main():
    segs = json.load(open(T / "segments.json"))
    by = {s["i"]: s for s in segs}
    kids = {}
    for s in segs:
        if s["dn"] >= 0:
            kids.setdefault(s["dn"], []).append(s["i"])
    # pick a high-priority Lubigi stretch near Bwaise
    def n_up(i):
        st, seen = [i], {i}
        while st:
            c = st.pop()
            for k in kids.get(c, []):
                if k not in seen:
                    seen.add(k); st.append(k)
        return len(seen)
    near = [s for s in segs if s["k"] in ("urgent", "fix") and
            ((s["c"][0][1] - 0.352) ** 2 + (s["c"][0][0] - 32.565) ** 2) ** 0.5 < 0.015]
    sel = max(near, key=lambda s: n_up(s["i"]) if s["a"] < 40 else 0)
    dn, c, seen = [], sel["i"], set()
    while c >= 0 and c in by and c not in seen:
        seen.add(c); dn.append(c); c = by[c]["dn"]
    up, st, seen = [], [sel["i"]], {sel["i"]}
    while st:
        c = st.pop(); up.append(c)
        for k in kids.get(c, []):
            if k not in seen:
                seen.add(k); st.append(k)
    img = Image.open(T / "basemap_light.png").convert("RGB")
    ext = (32.45, 32.72, 0.20, 0.42)
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor=BG)
    # header
    fig.text(0.015, 0.955, "KAMPALA DRAIN WATCH", fontsize=20, fontweight="bold", color=INK, va="center", family="DejaVu Sans")
    fig.text(0.33, 0.955, "Open maintenance map for Greater Kampala's drainage channels", fontsize=11, color=MUTE, va="center")
    fig.text(0.985, 0.955, "© OpenStreetMap · Copernicus · JRC GHSL · Microsoft", fontsize=7.5, color=MUTE, va="center", ha="right")
    ax = fig.add_axes([0.0, 0.0, 0.69, 0.91])
    ax.imshow(img, extent=ext, origin="upper")
    ax.set_axis_off()
    order = sorted(segs, key=lambda s: s["a"])
    lines = [np.array(s["c"]) for s in order]
    widths = [4.0 if s["a"] >= 10 else 2.6 if s["a"] >= 2 else 1.3 for s in order]
    cols = [CLS.get(s["k"], CLS["other"])[1] for s in order]
    lc = LineCollection(lines, colors=cols, linewidths=widths, alpha=0.0, capstyle="round")
    ax.add_collection(lc)
    trace = LineCollection([], colors="#2196f3", linewidths=9, alpha=0.5)
    ax.add_collection(trace)
    hl = LineCollection([], colors="#00e5ff", linewidths=12, alpha=0.65)
    ax.add_collection(hl)
    pin, = ax.plot([], [], "o", ms=14, mfc=ACC, mec="white", mew=2.5, zorder=9)
    cursor, = ax.plot([], [], marker=(3, 0, 20), ms=16, color="#111", mec="white", mew=1.2, zorder=10)
    # legend
    lg = fig.add_axes([0.012, 0.03, 0.16, 0.2])
    lg.axis("off")
    lg.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02", fc=PANEL, ec="#dcd8d0", transform=lg.transAxes))
    for k_, key in enumerate(["urgent", "fix", "coming", "watch", "low"]):
        lg.plot([0.08, 0.25], [0.84 - k_ * 0.17] * 2, color=CLS[key][1], lw=4, transform=lg.transAxes)
        lg.text(0.3, 0.84 - k_ * 0.17, CLS[key][0], va="center", fontsize=9.5, transform=lg.transAxes)
    # side panel
    pn = fig.add_axes([0.69, 0.0, 0.31, 0.91])
    pn.set_xlim(0, 1)
    pn.set_ylim(0, 1)
    pn.axis("off")
    pn.add_patch(plt.Rectangle((0, 0), 1, 1, color=PANEL, transform=pn.transAxes))
    pn.plot([0, 0], [0, 1], color="#dcd8d0", lw=1, transform=pn.transAxes)
    tabs = ["CHANNEL", "WORK QUEUE", "REPORTS"]
    for k_, t_ in enumerate(tabs):
        pn.text(0.06 + k_ * 0.31, 0.955, t_, fontsize=10, fontweight="bold", color=INK if k_ == 0 else MUTE)
    pn.plot([0.06, 0.25], [0.935, 0.935], color=ACC, lw=3)
    txt = {k: pn.text(0.06, y, "", fontsize=fs, fontweight=fw, color=c, va="top", wrap=True)
           for k, y, fs, fw, c in (("title", 0.89, 17, "bold", INK), ("sub", 0.83, 10, "normal", MUTE),
                                   ("body", 0.76, 10.5, "normal", INK), ("trace", 0.38, 10.5, "bold", "#2196f3"),
                                   ("report", 0.17, 10.5, "bold", ACC))}
    bar_bg = pn.add_patch(plt.Rectangle((0.06, 0.785), 0.88, 0.012, color="#eef3f3"))
    bar = pn.add_patch(plt.Rectangle((0.06, 0.785), 0.0, 0.012, color="#a50026"))
    fig.text(0.985, 0.012, "Credit: Gava Charles", ha="right", fontsize=10, fontweight="bold", color=INK)
    full = (32.50, 32.68, 0.25, 0.39)
    sx, sy = np.mean([p[0] for p in sel["c"]]), np.mean([p[1] for p in sel["c"]])
    zoom = (sx - 0.018, sx + 0.018, sy - 0.0101, sy + 0.0101)
    frames = []
    W = iio.get_writer(str(OUT / "drain_watch_demo.mp4"), fps=24, quality=8, macro_block_size=8)

    def view(a, b, t):
        e = ease(t)
        v = [x + (y - x) * e for x, y in zip(a, b)]
        asp = (0.91 * 7.2) / (0.69 * 12.8)
        cx, cy, w = (v[0] + v[1]) / 2, (v[2] + v[3]) / 2, v[1] - v[0]
        ax.set_xlim(cx - w / 2, cx + w / 2)
        ax.set_ylim(cy - w * asp / 2, cy + w * asp / 2)

    def shot(n=1):
        fig.canvas.draw()
        fr = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
        for _ in range(n):
            W.append_data(fr)
            frames.append(fr)

    seg_xy = np.array(sel["c"])
    txt["title"].set_text("Pick a channel")
    txt["sub"].set_text("6,914 stretches ranked for maintenance")
    # 1: channels draw in (2 s)
    for k in range(48):
        lc.set_alpha(min(1, k / 36))
        view(full, full, 0)
        shot()
    # 2: zoom to Bwaise (2.5 s) with cursor
    for k in range(60):
        view(full, zoom, k / 59)
        cursor.set_data([sx + 0.004 * (1 - ease(k / 59))], [sy - 0.003 * (1 - ease(k / 59))])
        shot()
    # 3: select (hover + card) (3 s)
    hl.set_segments([seg_xy])
    txt["title"].set_text(sel["nm"])
    txt["sub"].set_text(f"{sel.get('sy') or 'Greater Kampala'} catchment · {sel['a']:.0f} km² upstream · {CLS[sel['k']][0]}")
    drivers = "\n".join("• " + d for d in sel["d"].split("; "))
    for k in range(72):
        bar.set_width(0.88 * sel["p"] / 100 * ease(min(k / 30, 1)))
        txt["body"].set_text(f"Maintenance priority {sel['p']:.0f}/100\n\nLikely causes here:\n{drivers}\n\n"
                             f"Buildings within 15 m: {sel['b']}\nCulverts: {sel['cu']}   Dump sites ≤100 m: {sel['w']}")
        shot()
    # 4: trace downstream (3 s)
    dsegs = [np.array(by[i]["c"]) for i in dn]
    txt["trace"].set_color("#2196f3")
    for k in range(72):
        m = max(1, int(len(dsegs) * ease(min(k / 50, 1))))
        trace.set_segments(dsegs[:m])
        trace.set_color("#2196f3")
        txt["trace"].set_text(f"Follow the water ↓\nDownstream: {sum(by[i]['L'] for i in dn[:m]) / 1000:.1f} km to where it drains")
        pts = np.vstack(dsegs[:m])
        view(zoom, (pts[:, 0].min() - 0.01, pts[:, 0].max() + 0.01, pts[:, 1].min() - 0.006, pts[:, 1].max() + 0.006)
             if m > 3 else zoom, min(k / 60, 1) * 0.6)
        shot()
    # 5: trace upstream (3 s)
    usegs = [np.array(by[i]["c"]) for i in up]
    nb = sum(by[i]["b"] for i in up)
    for k in range(72):
        m = max(1, int(len(usegs) * ease(min(k / 50, 1))))
        trace.set_segments(usegs[:m])
        trace.set_color("#ff9800")
        txt["trace"].set_color("#e07b00")
        txt["trace"].set_text(f"Everything that drains here ↑\n{sum(by[i]['L'] for i in up[:m]) / 1000:.1f} km upstream · "
                              f"{sum(by[i]['b'] for i in up[:m]):,} buildings in the reserve")
        pts = np.vstack(usegs)
        tgt = (pts[:, 0].min() - 0.006, pts[:, 0].max() + 0.006, pts[:, 1].min() - 0.004, pts[:, 1].max() + 0.004)
        view(ax.get_xlim() + ax.get_ylim() if k == 0 else tgt, tgt, 1)
        shot()
    # 6: report pin (3 s)
    trace.set_segments([])
    view(zoom, zoom, 0)
    mx, my = seg_xy[len(seg_xy) // 2]
    for k in range(72):
        drop = max(0, 1 - k / 18)
        pin.set_data([mx], [my + 0.004 * drop ** 2])
        cursor.set_data([], [])
        txt["report"].set_text("Report saved: culvert blocked with plastic and silt\nVisible to every crew and resident using the map"
                               if k > 20 else "Log a report…")
        shot()
    # 7: end card (3 s)
    end = fig.add_axes([0, 0, 1, 1])
    end.axis("off")
    end.add_patch(plt.Rectangle((0, 0), 1, 1, color=BG, alpha=0.0, transform=end.transAxes))
    e1 = end.text(0.5, 0.56, "KAMPALA DRAIN WATCH", ha="center", fontsize=40, fontweight="bold", color=INK, alpha=0)
    e2 = end.text(0.5, 0.45, "Every channel ranked · trace the water · log blockages and floods",
                  ha="center", fontsize=16, color=MUTE, alpha=0)
    rect = end.patches[0]
    for k in range(72):
        a = min(1, k / 18)
        rect.set_alpha(0.93 * a)
        e1.set_alpha(a)
        e2.set_alpha(a)
        shot()
    W.close()
    plt.close(fig)
    gif = [Image.fromarray(f).resize((640, 360), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE) for f in frames[::3]]
    gif[0].save(OUT / "drain_watch_demo.gif", save_all=True, append_images=gif[1:], duration=125, loop=0)
    print("frames", len(frames), "selected", sel["nm"], "down", len(dn), "up", len(up), "bldg upstream", nb)


if __name__ == "__main__":
    main()
