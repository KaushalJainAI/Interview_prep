"""Convert every DSA markdown file to .docx (and .pdf when Word is available).

Outputs land under 01-CS-Fundamentals/out/  (docx + pdf side by side).
"""
from pathlib import Path
import sys, shutil
sys.path.insert(0, str(Path(__file__).resolve().parent))
from md_to_docx import convert as md_to_docx

CS = Path(__file__).resolve().parent.parent.parent      # 01-CS-Fundamentals
DSA_PAT = CS / "dsa-patterns"
OUT = CS / "out"
OUT.mkdir(exist_ok=True)
(OUT / "dsa-patterns").mkdir(exist_ok=True)

# Stage diagrams so relative paths work when docx is in OUT
shutil.copytree(DSA_PAT / "diagrams", OUT / "dsa-patterns" / "diagrams", dirs_exist_ok=True)

targets = [
    (CS / "dsa-cheatsheet.md",      OUT / "dsa-cheatsheet.docx"),
    (CS / "dsa-examples.md",        OUT / "dsa-examples.docx"),
]
for md in sorted(DSA_PAT.glob("[0-9][0-9]-*.md")):
    targets.append((md, OUT / "dsa-patterns" / f"{md.stem}.docx"))

for md, dx in targets:
    print(">>", md.relative_to(CS), "->", dx.relative_to(CS))
    md_to_docx(md, dx, md.parent)

# Now PDFs via docx2pdf (uses Word COM on Windows)
try:
    from docx2pdf import convert as docx_to_pdf
    for _, dx in targets:
        pdf = dx.with_suffix(".pdf")
        docx_to_pdf(str(dx), str(pdf))
        print("pdf:", pdf.name)
except Exception as e:
    print("PDF step failed:", e)
print("done. Outputs in", OUT)
