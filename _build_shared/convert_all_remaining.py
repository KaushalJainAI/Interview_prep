"""Convert markdown in the 5 remaining folders to docx + pdf."""
from pathlib import Path
import sys, shutil, subprocess
import markdown as md_lib

ROOT = Path(r"C:\Users\91700\Desktop\Interview notes")
FOLDERS = ["05-Backend-Django","06-Frontend","07-Deployment","08-VCS-Testing","09-System-Design-Security"]
DSA_BUILD = ROOT / "01-CS-Fundamentals" / "dsa-patterns" / "_build"
sys.path.insert(0, str(DSA_BUILD))
from md_to_docx import convert as md_to_docx

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
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

for folder in FOLDERS:
    fd = ROOT / folder
    diag = fd / "diagrams"
    out  = fd / "out"
    out.mkdir(exist_ok=True)
    html_dir = out / "_html"; html_dir.mkdir(exist_ok=True)
    if diag.exists():
        shutil.copytree(diag, out / "diagrams", dirs_exist_ok=True)
        shutil.copytree(diag, html_dir / "diagrams", dirs_exist_ok=True)
    # fix .svg → .png refs
    for md in fd.glob("*.md"):
        t = md.read_text(encoding="utf-8")
        t2 = t.replace(".svg)", ".png)")
        if t != t2:
            md.write_text(t2, encoding="utf-8")
    for md in sorted(fd.glob("*.md")):
        docx = out / f"{md.stem}.docx"
        pdf  = out / f"{md.stem}.pdf"
        print(">>", folder, md.name)
        md_to_docx(md, docx, md.parent)
        html = html_dir / (md.stem + ".html")
        body = md_lib.markdown(md.read_text(encoding="utf-8"), extensions=["fenced_code","tables","codehilite"])
        html.write_text(f"<!doctype html><html><head><meta charset='utf-8'>{CSS}</head><body>{body}</body></html>", encoding="utf-8")
        subprocess.run([EDGE,"--headless=new","--disable-gpu",
                        f"--print-to-pdf={pdf}", "--no-pdf-header-footer",
                        html.resolve().as_uri()], check=True, timeout=90)
print("done.")
