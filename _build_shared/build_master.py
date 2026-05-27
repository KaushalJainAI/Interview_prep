"""Stitch all 63 markdown files into one master PDF + docx in interview-prep order.

Strategy:
1. Build an ordered list of (section_title, files).
2. Concatenate markdown, prefixing each file with a page break + h1.
3. Rewrite image paths from `diagrams/...` (folder-relative) to absolute file URLs
   so they resolve in the combined output.
4. Convert via md_to_docx + Edge headless PDF.
"""
from pathlib import Path
import sys, shutil, subprocess, re
import markdown as md_lib

ROOT = Path(r"C:\Users\91700\Desktop\Interview notes")
OUT  = ROOT / "out_master"
OUT.mkdir(exist_ok=True)
HTML = OUT / "_html"
HTML.mkdir(exist_ok=True)

DSA_BUILD = ROOT / "01-CS-Fundamentals" / "dsa-patterns" / "_build"
sys.path.insert(0, str(DSA_BUILD))
from md_to_docx import convert as md_to_docx

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# Stage every diagrams folder under OUT so relative links work
STAGE = OUT / "staged_diagrams"
if STAGE.exists(): shutil.rmtree(STAGE)
STAGE.mkdir()
for folder in (ROOT.glob("[0-9][0-9]-*"), [ROOT / "JOB-SEARCH"]):
    for sub in folder:
        d = sub / "diagrams"
        if d.exists():
            dest = STAGE / sub.name
            shutil.copytree(d, dest)
# also root-level diagrams
if (ROOT / "diagrams").exists():
    shutil.copytree(ROOT / "diagrams", STAGE / "root", dirs_exist_ok=True)

# Build ordering
SECTIONS = [
    ("Foundations",                       [ROOT / "README.md", ROOT / "SYLLABUS.md", ROOT / "TOC.md"]),
    ("01 · CS Fundamentals — Cheatsheets",
        sorted((ROOT / "01-CS-Fundamentals").glob("*.md"))),
    ("01 · CS Fundamentals — DSA Patterns",
        sorted((ROOT / "01-CS-Fundamentals" / "dsa-patterns").glob("*.md"))),
    ("02 · ML & Deep Learning",
        sorted((ROOT / "02-ML-DL").glob("*.md"))),
    ("03 · Transformers & LLMs",
        sorted((ROOT / "03-Transformers-LLMs").glob("*.md"))),
    ("04 · AI Agents",
        sorted((ROOT / "04-AI-Agents").glob("*.md"))),
    ("05 · Backend (Django)",
        sorted((ROOT / "05-Backend-Django").glob("*.md"))),
    ("06 · Frontend (React)",
        sorted((ROOT / "06-Frontend").glob("*.md"))),
    ("07 · Deployment",
        sorted((ROOT / "07-Deployment").glob("*.md"))),
    ("08 · VCS & Testing",
        sorted((ROOT / "08-VCS-Testing").glob("*.md"))),
    ("09 · System Design & Security",
        sorted((ROOT / "09-System-Design-Security").glob("*.md"))),
    ("Job Search",
        sorted((ROOT / "JOB-SEARCH").glob("*.md"))),
]

# Image path remap: each file's `diagrams/foo.png` → `staged_diagrams/<folder>/foo.png`
IMG_RE = re.compile(r'(!\[[^\]]*\]\()diagrams/([^)]+)\)')
ROOT_IMG_RE = re.compile(r'(!\[[^\]]*\]\()/?diagrams/([^)]+)\)')

def remap_images(md_text: str, source_file: Path) -> str:
    """Convert diagrams/xx.png references to point inside the staged_diagrams area."""
    parent_name = source_file.parent.name
    # Files directly under ROOT use staged_diagrams/root
    if source_file.parent == ROOT:
        prefix = "staged_diagrams/root"
    else:
        # If source is in dsa-patterns subfolder, parent is dsa-patterns
        # diagrams live at 01-CS-Fundamentals/dsa-patterns/diagrams, but staged under dsa-patterns
        prefix = f"staged_diagrams/{parent_name}"
    def repl(m):
        return f"{m.group(1)}{prefix}/{m.group(2)})"
    return IMG_RE.sub(repl, md_text)

# Build big combined markdown
out_md = OUT / "INTERVIEW-NOTES-MASTER.md"
combined = []
combined.append("# Interview Prep — Master Notes\n")
combined.append("\n> Single combined export of the Interview-notes project. Auto-generated.\n\n")
combined.append("![Topic Map](staged_diagrams/root/00-topic-map.png)\n\n")

for section_name, files in SECTIONS:
    combined.append("\n<div style='page-break-before: always'></div>\n\n")
    combined.append(f"# § {section_name}\n\n")
    for f in files:
        if not f.exists(): continue
        combined.append("\n<div style='page-break-before: always'></div>\n\n")
        text = f.read_text(encoding="utf-8")
        text = remap_images(text, f)
        # Demote top-level headings by one level so the section title stays h1
        # (replace ^# with ^##)
        text = re.sub(r"^# ", "## ", text, count=1, flags=re.MULTILINE)
        combined.append(text)
        combined.append("\n")
    print("section staged:", section_name)

out_md.write_text("".join(combined), encoding="utf-8")
print("wrote", out_md, "size", out_md.stat().st_size)

# Convert to docx
docx_out = OUT / "INTERVIEW-NOTES-MASTER.docx"
md_to_docx(out_md, docx_out, OUT)
print("wrote", docx_out, "size", docx_out.stat().st_size)

# Convert to PDF via Edge headless
CSS = r"""<style>
@page { size: A4; margin: 18mm 16mm; }
body { font-family: 'Segoe UI', Calibri, sans-serif; font-size: 11pt; color:#1a1a1a; line-height: 1.45; max-width: 820px; margin: 0 auto;}
h1 { font-size: 22pt; border-bottom: 2px solid #1f6feb; padding-bottom: 4px; margin-top: 20px; page-break-before: always;}
h1:first-of-type { page-break-before: avoid;}
h2 { font-size: 16pt; color: #1f6feb; margin-top: 24px;}
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

html_path = HTML / "MASTER.html"
body = md_lib.markdown(out_md.read_text(encoding="utf-8"), extensions=["fenced_code","tables","codehilite"])
html_path.write_text(f"<!doctype html><html><head><meta charset='utf-8'>{CSS}</head><body>{body}</body></html>", encoding="utf-8")

pdf_out = OUT / "INTERVIEW-NOTES-MASTER.pdf"
subprocess.run([EDGE, "--headless=new", "--disable-gpu",
                f"--print-to-pdf={pdf_out}", "--no-pdf-header-footer",
                html_path.resolve().as_uri()], check=True, timeout=300)
print("wrote", pdf_out, "size", pdf_out.stat().st_size / 1e6, "MB")

print("done.")
