"""Render markdown to a styled HTML, then use Edge headless to print to PDF.
Bypasses docx2pdf (which needs Microsoft Word)."""
from pathlib import Path
import subprocess, shutil, markdown as md_lib

CS = Path(__file__).resolve().parent.parent.parent
DSA_PAT = CS / "dsa-patterns"
OUT = CS / "out"
HTML_TMP = OUT / "_html"
HTML_TMP.mkdir(parents=True, exist_ok=True)

# Stage diagrams under the html temp dir so img paths resolve
shutil.copytree(DSA_PAT / "diagrams", HTML_TMP / "dsa-patterns" / "diagrams", dirs_exist_ok=True)

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

CSS = r"""
<style>
@page { size: A4; margin: 18mm 16mm; }
body { font-family: 'Segoe UI', Calibri, sans-serif; font-size: 11pt; color:#1a1a1a; line-height: 1.45; max-width: 800px; margin: 0 auto;}
h1 { font-size: 22pt; border-bottom: 2px solid #1f6feb; padding-bottom: 4px; margin-top: 18px;}
h2 { font-size: 16pt; color: #1f6feb; margin-top: 22px;}
h3 { font-size: 13pt; color: #333; margin-top: 14px;}
h4 { font-size: 11.5pt; color: #555; }
code { font-family: 'Consolas','Courier New', monospace; background: #f4f6f8; padding: 1px 4px; border-radius: 3px; color: #0b468c; font-size: 9.5pt;}
pre  { background: #f4f6f8; border: 1px solid #ddd; border-radius: 6px; padding: 10px 12px; overflow-x: auto;
       font-family: 'Consolas','Courier New', monospace; font-size: 9.5pt; line-height: 1.35; page-break-inside: avoid;}
pre code { background: transparent; padding: 0; color: #1a1a1a;}
blockquote { border-left: 4px solid #1f6feb; margin-left: 0; padding: 4px 12px; color: #555; background: #f9fbff;}
table { border-collapse: collapse; width: 100%; margin: 10px 0; page-break-inside: avoid; font-size: 10pt;}
th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left;}
th { background: #e6f0ff;}
img { max-width: 100%; height: auto; display: block; margin: 12px auto; page-break-inside: avoid;}
hr { border: 0; border-top: 1px solid #aaa; margin: 22px 0;}
ul, ol { padding-left: 24px;}
a { color: #1f6feb; }
.title-banner { background: linear-gradient(90deg,#1f6feb,#22c55e); color: white; padding: 16px 20px; border-radius: 8px; margin-bottom: 18px;}
</style>
"""

def md_to_html(md_path: Path, out_html: Path):
    text = md_path.read_text(encoding="utf-8")
    html = md_lib.markdown(text, extensions=["fenced_code", "tables", "codehilite", "toc"])
    # rewrite diagram paths relative to where html lives
    rel_prefix = ""
    if out_html.parent.name == "dsa-patterns":
        # images referenced as diagrams/xx.png from inside dsa-patterns
        pass
    full = f"<!doctype html><html><head><meta charset='utf-8'>{CSS}<title>{md_path.stem}</title></head><body>{html}</body></html>"
    out_html.write_text(full, encoding="utf-8")

def html_to_pdf(html: Path, pdf: Path):
    cmd = [EDGE, "--headless=new", "--disable-gpu",
           f"--print-to-pdf={pdf}", "--no-pdf-header-footer",
           html.resolve().as_uri()]
    subprocess.run(cmd, check=True, timeout=90)

targets = [
    (CS / "dsa-cheatsheet.md",   HTML_TMP / "dsa-cheatsheet.html",   OUT / "dsa-cheatsheet.pdf"),
    (CS / "dsa-examples.md",     HTML_TMP / "dsa-examples.html",     OUT / "dsa-examples.pdf"),
]
(HTML_TMP / "dsa-patterns").mkdir(exist_ok=True)
(OUT / "dsa-patterns").mkdir(exist_ok=True)
for md in sorted(DSA_PAT.glob("[0-9][0-9]-*.md")):
    targets.append((
        md,
        HTML_TMP / "dsa-patterns" / f"{md.stem}.html",
        OUT / "dsa-patterns" / f"{md.stem}.pdf",
    ))

for src, html, pdf in targets:
    md_to_html(src, html)
    html_to_pdf(html, pdf)
    print("pdf:", pdf.relative_to(CS))

print("done")
