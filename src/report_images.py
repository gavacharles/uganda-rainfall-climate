"""Web-sized JPEG copies of all figures for the HTML report (report/img/)."""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "report" / "img"
out.mkdir(parents=True, exist_ok=True)
for f in sorted((ROOT / "figures").glob("fig*.png")):
    im = Image.open(f).convert("RGB")
    if im.width > 2000:
        im = im.resize((2000, round(im.height * 2000 / im.width)), Image.LANCZOS)
    im.save(out / (f.stem + ".jpg"), quality=84, optimize=True, progressive=True)
print(sum(p.stat().st_size for p in out.glob("*.jpg")) / 1e6, "MB")
