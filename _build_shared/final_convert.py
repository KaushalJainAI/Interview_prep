"""Final pass: render PNGs for new SVGs, expand playbook, convert all final files to docx+pdf."""
import subprocess, re, sys, shutil
from pathlib import Path
from PIL import Image, ImageChops
import markdown as md_lib

ROOT = Path(r"C:\Users\91700\Desktop\Interview notes")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DSA_BUILD = ROOT / "01-CS-Fundamentals" / "dsa-patterns" / "_build"
sys.path.insert(0, str(DSA_BUILD))
from md_to_docx import convert as md_to_docx

def parse(t):
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', t)
    return (int(m.group(1)), int(m.group(2))) if m else (1400,800)
def trim(im):
    bg = Image.new(im.mode, im.size, (255,255,255))
    diff = ImageChops.difference(im, bg); bb = diff.getbbox()
    if not bb: return im
    x0,y0,x1,y1 = bb; w,h = im.size
    return im.crop((max(0,x0-12), max(0,y0-12), min(w,x1+12), min(h,y1+12)))

# 1. Render new SVGs
for d in [ROOT / "JOB-SEARCH" / "diagrams", ROOT / "diagrams"]:
    if not d.exists(): continue
    for svg in sorted(d.glob("*.svg")):
        png = svg.with_suffix(".png")
        w,h = parse(svg.read_text(encoding="utf-8"))
        subprocess.run([EDGE,"--headless=new","--disable-gpu",
                        f"--screenshot={png}", f"--window-size={w*2},{h*2}",
                        "--force-device-scale-factor=2","--hide-scrollbars",
                        svg.resolve().as_uri()], check=True, timeout=60)
        trim(Image.open(png).convert("RGB")).save(png, "PNG", optimize=True)
        print("png", svg.parent.name, png.name)

# 2. Expand JOB-SEARCH/playbook.md
playbook = ROOT / "JOB-SEARCH" / "playbook.md"
t = playbook.read_text(encoding="utf-8")
imgs = ["diagrams/01-funnel.png","diagrams/02-cadence.png","diagrams/03-interview-pipeline.png"]
EXTRA = r"""

---

## 🔬 Deep dive — interview prep blueprint (12-week sprint)

| Weeks | Focus | Daily target |
|-------|-------|--------------|
| 1-2 | DSA refresh (NeetCode 150) | 3 problems/day + 1 pattern review |
| 3-4 | ML/DL fundamentals + math derivations | 1 cheatsheet + 1 paper summary |
| 5-6 | Transformers / LLMs / RAG | 1 deep file + 1 hands-on demo |
| 7-8 | System design + low-latency LLM serving | 1 mock problem written out |
| 9-10 | Behavioural + STAR stories + project narratives | refine pitch, mock with a friend |
| 11-12 | Mock interviews (5+) + iterate | rest day after each, debrief |

## 📌 Common interview questions to drill

1. **Tell me about a recent project.** STAR — situation, task, action, result. 90 sec.
2. **Walk me through your AIAAS architecture.** Use the diagram in 09-System-Design-Security/diagrams/02-aiaas-architecture.svg.
3. **Train/tune an LLM — what's the workflow?** Tokenise → continue-pretrain (optional) → SFT → DPO/RLHF → eval.
4. **Implement scaled dot-product attention from scratch.** Be ready to write the einsum + mask + softmax.
5. **Production ML systems — how do you monitor drift?** Distribution diff, performance proxies, alerts on regressions.

## 🎯 Salary negotiation in one paragraph

Always state a *range* anchored to current market data — not your past salary. For mid-level AI Engineer in India 2026, total comp commonly lands 18–45 LPA depending on tier. Sources: Levels.fyi (India tab), Glassdoor, recent LinkedIn announcements. Ask for total comp breakdown: base, bonus, ESOPs (vesting + strike), joining bonus, relocation. Never accept on the same call.

## 📚 References
- *Cracking the Coding Interview* (Gayle Laakmann McDowell) — DSA + interview structure
- "STAR method" — for behavioural questions
- Levels.fyi — comp data
- *System Design Interview Vol I & II* (Alex Xu)
"""
if "Deep dive — interview prep blueprint" not in t:
    lines = t.split("\n"); out=[]; inserted=False
    for ln in lines:
        out.append(ln)
        if not inserted and ln.startswith("# "):
            for img in imgs:
                out.append(""); out.append(f"![Diagram]({img})")
            inserted = True
    t = "\n".join(out)
    if not t.endswith("\n"): t += "\n"
    t += EXTRA
    playbook.write_text(t, encoding="utf-8")
    print("expanded playbook")

# 3. Add overview diagram to README
readme = ROOT / "README.md"
rt = readme.read_text(encoding="utf-8")
if "diagrams/00-topic-map.png" not in rt:
    lines = rt.split("\n"); out=[]; inserted=False
    for ln in lines:
        out.append(ln)
        if not inserted and ln.startswith("# "):
            out.append(""); out.append("![Topic Map](diagrams/00-topic-map.png)")
            inserted = True
    readme.write_text("\n".join(out), encoding="utf-8")
    print("added overview to README")

# 4. Convert JOB-SEARCH + root files
CSS = r"""<style>
@page { size: A4; margin: 18mm 16mm; }
body { font-family: 'Segoe UI', Calibri, sans-serif; font-size: 11pt; color:#1a1a1a; line-height: 1.45; max-width: 800px; margin: 0 auto;}
h1 { font-size: 22pt; border-bottom: 2px solid #1f6feb; padding-bottom: 4px; margin-top: 18px;}
h2 { font-size: 16pt; color: #1f6feb; margin-top: 22px;}
h3 { font-size: 13pt; color: #333; margin-top: 14px;}
code { font-family: 'Consolas','Courier New', monospace; background: #f4f6f8; padding: 1px 4px; border-radius: 3px; color: #0b468c; font-size: 9.5pt;}
pre { background: #f4f6f8; border: 1px solid #ddd; border-radius: 6px; padding: 10px 12px; overflow-x: auto;
      font-family: 'Consolas','Courier New', monospace; font-size: 9.5pt; line-height: 1.35; page-break-inside: avoid;}
pre code { background: transparent; padding: 0; color: #1a1a1a;}
blockquote { border-left: 4px solid #1f6feb; margin-left: 0; padding: 4px 12px; color: #555; background: #f9fbff;}
table { border-collapse: collapse; width: 100%; margin: 10px 0; page-break-inside: avoid; font-size: 10pt;}
th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left;}
th { background: #e6f0ff;}
img { max-width: 100%; height: auto; display: block; margin: 12px auto; page-break-inside: avoid;}
hr { border: 0; border-top: 1px solid #aaa; margin: 22px 0;}
</style>"""

def convert_folder(folder: Path, root_out: Path):
    out = folder / "out" if folder != ROOT else (ROOT / "out_root")
    out.mkdir(exist_ok=True)
    html_dir = out / "_html"; html_dir.mkdir(exist_ok=True)
    if (folder / "diagrams").exists():
        shutil.copytree(folder / "diagrams", out / "diagrams", dirs_exist_ok=True)
        shutil.copytree(folder / "diagrams", html_dir / "diagrams", dirs_exist_ok=True)
    # also stage root-level diagrams when converting root files
    if folder == ROOT and (ROOT / "diagrams").exists():
        shutil.copytree(ROOT / "diagrams", out / "diagrams", dirs_exist_ok=True)
        shutil.copytree(ROOT / "diagrams", html_dir / "diagrams", dirs_exist_ok=True)
    for md in sorted(folder.glob("*.md")):
        t2 = md.read_text(encoding="utf-8").replace(".svg)", ".png)")
        md.write_text(t2, encoding="utf-8")
        docx = out / f"{md.stem}.docx"; pdf = out / f"{md.stem}.pdf"
        print(">>", folder.name, md.name)
        md_to_docx(md, docx, md.parent)
        html = html_dir / (md.stem + ".html")
        body = md_lib.markdown(md.read_text(encoding="utf-8"), extensions=["fenced_code","tables","codehilite"])
        html.write_text(f"<!doctype html><html><head><meta charset='utf-8'>{CSS}</head><body>{body}</body></html>", encoding="utf-8")
        subprocess.run([EDGE,"--headless=new","--disable-gpu",
                        f"--print-to-pdf={pdf}", "--no-pdf-header-footer",
                        html.resolve().as_uri()], check=True, timeout=90)

convert_folder(ROOT / "JOB-SEARCH", ROOT)
# root .md files
convert_folder(ROOT, ROOT)
print("done")
