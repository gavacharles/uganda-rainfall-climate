"""Word version of paper 6 (floodwater and resistance): figures as compressed JPEG copies, then pandoc."""
import re

import pypandoc
from PIL import Image

from common import ROOT

P = ROOT / "paper" / "P6_floodwater_and_resistance"
D = ROOT / "figures" / "kampala_amr" / "_docx"


def jpg(stem):
    D.mkdir(parents=True, exist_ok=True)
    src, dst = ROOT / "figures" / "kampala_amr" / f"{stem}.png", D / f"{stem}.jpg"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
        im = Image.open(src).convert("RGB")
        if im.width > 2000:
            im = im.resize((2000, round(im.height * 2000 / im.width)), Image.LANCZOS)
        im.save(dst, quality=82, optimize=True)
    return f"../figures/kampala_amr/_docx/{stem}.jpg"


text = P.with_suffix(".md").read_text()
text = re.sub(r"\]\(\.\./figures/kampala_amr/([^)]+)\.png\)", lambda m: f"]({jpg(m.group(1))})", text)
pypandoc.convert_text(text, "docx", format="md", outputfile=str(P.with_suffix(".docx")),
                      extra_args=["--resource-path", str(ROOT / "paper")])
print("docx", P.with_suffix(".docx"), round(P.with_suffix(".docx").stat().st_size / 1e6, 1), "MB")
