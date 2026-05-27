"""Rebuild docx + pdf for every .md whose mtime is newer than its corresponding .docx,
plus always rebuild the combined master.
"""
from pathlib import Path
import sys, shutil, subprocess
import markdown as md_lib

ROOT = Path(r"C:\Users\91700\Desktop\Interview notes")
DSA_BUILD = ROOT / "01-CS-Fundamentals" / "dsa-patterns" / "_build"
sys.path.insert(0, str(DSA_BUILD))
from md_to_docx import convert as md_to_docx

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CSS = r"""<style>
@page { size: A4; margin: 18mm 16mm; }
body { font-family: 'Segoe UI', Calibri, sans-serif; font-size: 11pt; color:#1a1a1a; line-height: 1.45; max-width: 820px; margin: 0 auto;}
h1 { font-size: 22pt; border-bottom: 2px solid #1f6feb; padding-bottom: 4px; margin-top: 20px;}
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

# Determine per-file out path (mirror layout used previously)
def out_paths(md: Path):
    rel = md.relative_to(ROOT)
    # root .md -> ROOT/out_root
    if md.parent == ROOT:
        out_dir = ROOT / "out_root"
    elif rel.parts[0] == "JOB-SEARCH":
        out_dir = ROOT / "JOB-SEARCH" / "out"
    elif rel.parts[0] == "01-CS-Fundamentals" and "dsa-patterns" in rel.parts:
        out_dir = ROOT / "01-CS-Fundamentals" / "out" / "dsa-patterns"
    elif rel.parts[0].startswith(("0", "1")) and rel.parts[0][:2].isdigit():
        out_dir = ROOT / rel.parts[0] / "out"
    else:
        return None, None
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{md.stem}.docx", out_dir / f"{md.stem}.pdf"

def needs_rebuild(md: Path, docx: Path) -> bool:
    if not docx.exists(): return True
    return md.stat().st_mtime > docx.stat().st_mtime

def html_for(md: Path, out_dir: Path) -> Path:
    html_dir = out_dir / "_html"; html_dir.mkdir(exist_ok=True)
    # stage diagrams adjacent to html so relative paths work
    src_diag = md.parent / "diagrams"
    if src_diag.exists():
        shutil.copytree(src_diag, out_dir / "diagrams", dirs_exist_ok=True)
        shutil.copytree(src_diag, html_dir / "diagrams", dirs_exist_ok=True)
    html_path = html_dir / (md.stem + ".html")
    body = md_lib.markdown(md.read_text(encoding="utf-8"), extensions=["fenced_code","tables","codehilite"])
    html_path.write_text(f"<!doctype html><html><head><meta charset='utf-8'>{CSS}</head><body>{body}</body></html>", encoding="utf-8")
    return html_path

EXCLUDE = {"out", "out_root", "out_master", "_html", "_build", "_build_shared", "cheatsheets"}

count = 0
for md in ROOT.rglob("*.md"):
    if any(part in EXCLUDE for part in md.parts): continue
    docx, pdf = out_paths(md)
    if docx is None: continue
    if not needs_rebuild(md, docx): continue
    print(">>", md.relative_to(ROOT))
    md_to_docx(md, docx, md.parent)
    html = html_for(md, docx.parent)
    subprocess.run([EDGE, "--headless=new", "--disable-gpu",
                    f"--print-to-pdf={pdf}", "--no-pdf-header-footer",
                    html.resolve().as_uri()], check=True, timeout=120)
    count += 1

print(f"\nrebuilt {count} files")
