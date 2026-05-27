"""Build a compact 'exam-day digest' by extracting from every cheatsheet:
- title
- first diagram image
- TL;DR section (if any)
- the first 'Common pitfalls' table (if any)
- the 'Interview questions' / 'Interview one-liners' section (if any)

Output: out_master/EXAM-DIGEST.{md,docx,pdf}
"""
import re, sys, shutil, subprocess
from pathlib import Path
import markdown as md_lib

ROOT = Path(r"C:\Users\91700\Desktop\Interview notes")
OUT  = ROOT / "out_master"
OUT.mkdir(exist_ok=True)
HTML = OUT / "_digest_html"
HTML.mkdir(exist_ok=True)

DSA_BUILD = ROOT / "01-CS-Fundamentals" / "dsa-patterns" / "_build"
sys.path.insert(0, str(DSA_BUILD))
from md_to_docx import convert as md_to_docx

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# Staged diagrams area (same scheme as build_master.py)
STAGE = OUT / "staged_diagrams"
if STAGE.exists(): shutil.rmtree(STAGE)
STAGE.mkdir()
for sub in (ROOT.glob("[0-9][0-9]-*"), [ROOT / "JOB-SEARCH"]):
    for s in sub:
        d = s / "diagrams"
        if d.exists():
            shutil.copytree(d, STAGE / s.name)
if (ROOT / "diagrams").exists():
    shutil.copytree(ROOT / "diagrams", STAGE / "root")

# File ordering (interview-prep order; deep / examples files skipped)
SECTIONS = [
    ("01 - CS Fundamentals", [
        "01-CS-Fundamentals/dsa-cheatsheet.md",
        "01-CS-Fundamentals/python-nuances-cheatsheet.md",
        "01-CS-Fundamentals/oop-cheatsheet.md",
        "01-CS-Fundamentals/sql-cheatsheet.md",
        "01-CS-Fundamentals/dbms-cheatsheet.md",
        "01-CS-Fundamentals/ds-libs-cheatsheet.md",
    ]),
    ("02 - ML & Deep Learning", [
        "02-ML-DL/ml-algos-cheatsheet.md",
        "02-ML-DL/dl-basics-cheatsheet.md",
        "02-ML-DL/gradient-descent-cheatsheet.md",
        "02-ML-DL/embeddings-nlp-cheatsheet.md",
        "02-ML-DL/cnn-resnet-unet-cheatsheet.md",
        "02-ML-DL/rnn-lstm-cheatsheet.md",
        "02-ML-DL/rl-cheatsheet.md",
    ]),
    ("03 - Transformers & LLMs", [
        "03-Transformers-LLMs/transformers-cheatsheet.md",
        "03-Transformers-LLMs/bert-gpt-cheatsheet.md",
        "03-Transformers-LLMs/tokenizers-cheatsheet.md",
        "03-Transformers-LLMs/moe-cheatsheet.md",
        "03-Transformers-LLMs/rag-hnsw-cheatsheet.md",
        "03-Transformers-LLMs/llm-evaluation-cheatsheet.md",
        "03-Transformers-LLMs/kv-cache-cheatsheet.md",
        "03-Transformers-LLMs/fine-tuning-cheatsheet.md",
        "03-Transformers-LLMs/prompt-engineering-cheatsheet.md",
        "03-Transformers-LLMs/scaling-laws-cheatsheet.md",
        "03-Transformers-LLMs/diffusion-cheatsheet.md",
        "03-Transformers-LLMs/latest-models-cheatsheet.md",
    ]),
    ("04 - AI Agents", [
        "04-AI-Agents/architecture-cheatsheet.md",
        "04-AI-Agents/tools-mcp-cheatsheet.md",
        "04-AI-Agents/stategraph-cheatsheet.md",
        "04-AI-Agents/pydantic-cheatsheet.md",
        "04-AI-Agents/memory-context-cheatsheet.md",
        "04-AI-Agents/guardrails-sandbox-hitl-cheatsheet.md",
    ]),
    ("05 - Backend (Django)", ["05-Backend-Django/django-full-cheatsheet.md"]),
    ("06 - Frontend",         ["06-Frontend/react-full-cheatsheet.md"]),
    ("07 - Deployment & MLOps", [
        "07-Deployment/deployment-full-cheatsheet.md",
        "07-Deployment/mlops-llmops-cheatsheet.md",
    ]),
    ("08 - VCS & Testing", [
        "08-VCS-Testing/git-testing-cheatsheet.md",
        "08-VCS-Testing/ai-system-testing-cheatsheet.md",
    ]),
    ("09 - System Design & Security", [
        "09-System-Design-Security/system-design-cheatsheet.md",
        "09-System-Design-Security/security-cheatsheet.md",
        "09-System-Design-Security/llm-security-cheatsheet.md",
    ]),
    ("Job Search", [
        "JOB-SEARCH/playbook.md",
        "JOB-SEARCH/behavioral-interview-cheatsheet.md",
    ]),
]

H1_RE   = re.compile(r"^#\s+(.+)$", re.M)
IMG_RE  = re.compile(r"!\[[^\]]*\]\(diagrams/([^)]+)\)")

def extract_section(text: str, *names) -> str | None:
    """Return the body of the first matching '## NAME ...' block."""
    pattern = "|".join(re.escape(n) for n in names)
    # match the header line and capture body until next ## or end
    m = re.search(rf"^##\s+(?:{pattern})\b.*?$\n(.*?)(?=^##\s|\Z)",
                  text, re.M | re.S | re.IGNORECASE)
    return m.group(1).strip() if m else None

def extract_first_table_after(text: str, anchor_re: str) -> str | None:
    m = re.search(anchor_re, text, re.M | re.IGNORECASE)
    if not m: return None
    rest = text[m.end():]
    # find first markdown table (lines starting with |)
    tbl_m = re.search(r"(\|[^\n]*\|\s*\n\|[\s\-:|]+\|[^\n]*\n(?:\|[^\n]*\n?)+)", rest)
    return tbl_m.group(1).strip() if tbl_m else None

def first_diagram(text: str, source_file: Path) -> str | None:
    m = IMG_RE.search(text)
    if not m: return None
    img_name = m.group(1)
    # Remap to staged diagrams location
    parent = source_file.parent.name
    if source_file.parent == ROOT:
        return f"staged_diagrams/root/{img_name}"
    return f"staged_diagrams/{parent}/{img_name}"

def digest_one(rel_path: str) -> str:
    p = ROOT / rel_path
    text = p.read_text(encoding="utf-8")
    h1 = H1_RE.search(text)
    title = h1.group(1) if h1 else p.stem
    parts = [f"### {title}", f"_source: `{rel_path}`_"]

    img = first_diagram(text, p)
    if img:
        parts.append(f"\n![Diagram]({img})\n")

    tldr = extract_section(text, "TL;DR", "TL DR", "TLDR")
    if tldr:
        parts.append("**TL;DR**\n\n" + tldr.strip())

    pitfalls = extract_first_table_after(text, r"^##.*pitfall", )
    if pitfalls:
        parts.append("**Common pitfalls**\n\n" + pitfalls)

    qs = extract_section(text, "Interview questions", "Interview one-liners",
                         "Top interview questions", "Interview-style questions")
    if qs:
        # trim to first ~12 lines to keep digest compact
        qs_lines = [ln for ln in qs.splitlines() if ln.strip()]
        qs_short = "\n".join(qs_lines[:20])
        parts.append("**Interview questions**\n\n" + qs_short)

    return "\n\n".join(parts) + "\n"

def main():
    out_md = OUT / "EXAM-DIGEST.md"
    chunks = [
        "# Exam-Day Digest",
        "_Compact revision artefact pulled from every cheatsheet. For the full notes see `INTERVIEW-NOTES-MASTER.{docx,pdf}`._\n",
        "![Topic Map](staged_diagrams/root/00-topic-map.png)\n",
    ]
    for section_name, files in SECTIONS:
        chunks.append(f"\n<div style='page-break-before: always'></div>\n")
        chunks.append(f"# {section_name}\n")
        for f in files:
            try:
                chunks.append(digest_one(f))
            except FileNotFoundError:
                print("missing:", f)
    out_md.write_text("\n".join(chunks), encoding="utf-8")
    print("md:", out_md, "size", out_md.stat().st_size)

    # docx
    docx_out = OUT / "EXAM-DIGEST.docx"
    md_to_docx(out_md, docx_out, OUT)
    print("docx:", docx_out)

    # pdf via Edge
    CSS = r"""<style>
@page { size: A4; margin: 16mm 14mm; }
body { font-family: 'Segoe UI', Calibri, sans-serif; font-size: 10.5pt; color:#1a1a1a; line-height: 1.35; max-width: 820px; margin: 0 auto;}
h1 { font-size: 22pt; border-bottom: 2px solid #1f6feb; padding-bottom: 4px; margin-top: 20px; page-break-before: always;}
h1:first-of-type { page-break-before: avoid;}
h2 { font-size: 15pt; color: #1f6feb; margin-top: 18px;}
h3 { font-size: 12pt; color: #333; margin-top: 14px; padding-top: 6px; border-top: 1px dashed #ccc;}
code { font-family: 'Consolas', monospace; background: #f4f6f8; padding: 1px 4px; border-radius: 3px; color: #0b468c; font-size: 9pt;}
pre { background: #f4f6f8; border: 1px solid #ddd; padding: 8px 10px; font-size: 9pt; page-break-inside: avoid;}
blockquote { border-left: 4px solid #1f6feb; margin-left: 0; padding: 4px 12px; color: #555;}
table { border-collapse: collapse; width: 100%; margin: 6px 0; page-break-inside: avoid; font-size: 9.5pt;}
th, td { border: 1px solid #ccc; padding: 4px 8px; text-align: left;}
th { background: #e6f0ff;}
img { max-width: 100%; height: auto; display: block; margin: 8px auto; page-break-inside: avoid;}
hr { border: 0; border-top: 1px solid #aaa;}
</style>"""
    html_path = HTML / "DIGEST.html"
    body = md_lib.markdown(out_md.read_text(encoding="utf-8"), extensions=["fenced_code","tables","codehilite"])
    html_path.write_text(f"<!doctype html><html><head><meta charset='utf-8'>{CSS}</head><body>{body}</body></html>", encoding="utf-8")
    pdf_out = OUT / "EXAM-DIGEST.pdf"
    subprocess.run([EDGE, "--headless=new", "--disable-gpu",
                    f"--print-to-pdf={pdf_out}", "--no-pdf-header-footer",
                    html_path.resolve().as_uri()], check=True, timeout=300)
    print("pdf:", pdf_out, "size", pdf_out.stat().st_size / 1e6, "MB")

if __name__ == "__main__":
    main()
