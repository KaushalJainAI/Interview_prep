"""Convert all SVGs in diagrams/ to PNGs using Edge headless, then auto-crop whitespace."""
import subprocess, re
from pathlib import Path
from PIL import Image, ImageChops

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DIAGRAMS = Path(__file__).resolve().parent.parent / "diagrams"

def parse_dims(svg_text):
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg_text)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 1400, 800

def trim(im):
    bg = Image.new(im.mode, im.size, (255,255,255))
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    if bbox:
        # pad 12px
        x0,y0,x1,y1 = bbox
        w,h = im.size
        return im.crop((max(0,x0-12), max(0,y0-12), min(w,x1+12), min(h,y1+12)))
    return im

for svg in sorted(DIAGRAMS.glob("*.svg")):
    txt = svg.read_text(encoding="utf-8")
    w,h = parse_dims(txt)
    # scale up 2x for crisp text
    scale = 2
    png = svg.with_suffix(".png")
    cmd = [
        EDGE, "--headless=new", "--disable-gpu",
        f"--screenshot={png}",
        f"--window-size={w*scale},{h*scale}",
        f"--force-device-scale-factor={scale}",
        "--hide-scrollbars",
        svg.resolve().as_uri(),
    ]
    subprocess.run(cmd, check=True, timeout=60)
    img = Image.open(png).convert("RGB")
    img = trim(img)
    img.save(png, "PNG", optimize=True)
    print(f"png: {png.name}  ({img.size[0]}x{img.size[1]})")
