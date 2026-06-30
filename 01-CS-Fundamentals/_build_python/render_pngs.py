"""Render diagrams/python/*.svg -> PNG via Edge headless, then auto-crop whitespace."""
import subprocess, re
from pathlib import Path
from PIL import Image, ImageChops

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DIAGRAMS = Path(__file__).resolve().parent.parent / "diagrams" / "python"

def parse_dims(t):
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', t)
    return (int(m.group(1)), int(m.group(2))) if m else (1400, 800)

def trim(im):
    bg = Image.new(im.mode, im.size, (255, 255, 255))
    bbox = ImageChops.difference(im, bg).getbbox()
    if bbox:
        x0, y0, x1, y1 = bbox
        w, h = im.size
        return im.crop((max(0, x0-12), max(0, y0-12), min(w, x1+12), min(h, y1+12)))
    return im

for svg in sorted(DIAGRAMS.glob("*.svg")):
    w, h = parse_dims(svg.read_text(encoding="utf-8"))
    scale = 2
    png = svg.with_suffix(".png")
    cmd = [EDGE, "--headless=new", "--disable-gpu", f"--screenshot={png}",
           f"--window-size={w*scale},{h*scale}", f"--force-device-scale-factor={scale}",
           "--hide-scrollbars", svg.resolve().as_uri()]
    subprocess.run(cmd, check=True, timeout=60)
    img = trim(Image.open(png).convert("RGB"))
    img.save(png, "PNG", optimize=True)
    print(f"png: {png.name}  ({img.size[0]}x{img.size[1]})")
