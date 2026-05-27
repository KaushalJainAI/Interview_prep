"""Audit the notes project for inconsistencies. Read-only; prints a report.

Tightened to avoid false positives:
- Strip fenced code blocks before regex link/image scan.
- Correct expected-output paths for root .md (out_root/) and dsa-patterns/.
- Skip legitimate non-ASCII (box-drawing, math superscripts, common technical glyphs).
"""
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"C:\Users\91700\Desktop\Interview notes")
EXCLUDE_DIRS = {"out", "out_root", "out_master", "_html", "_build", "_build_shared", "cheatsheets"}

findings = defaultdict(list)

def md_files():
    for p in ROOT.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in p.parts): continue
        yield p

FENCE_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`]*`")

def strip_code(text: str) -> str:
    """Replace fenced + inline code with spaces so regex link scans skip them."""
    text = FENCE_RE.sub(lambda m: " " * len(m.group(0)), text)
    text = INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), text)
    return text

# ---------- 1. Encoding regressions ----------
# Bytes that would render as mojibake when UTF-8 is mis-decoded as cp1252.
MOJIBAKE_BYTES = [
    bytes.fromhex("c3a2e282ace2809d"),
    bytes.fromhex("c3a2e282ace2809c"),
    bytes.fromhex("c3a2e282ace28099"),
    bytes.fromhex("c382c2b7"),
    bytes.fromhex("c3b0c5b8"),
]
# Whitelist of legitimate non-ASCII glyphs (ASCII diagrams, math, technical).
NON_ASCII_OK = set("\n\r\t")
NON_ASCII_OK |= set("─│┌┐└┘├┤┬┴┼"   # box-drawing
                    "▀▄█▌▐░▒▓"                       # block
                    "▲▼◀▶○●▪"                             # geometric
                    "←↑→↓↔↕"                                   # arrows
                    "ⁿ²³⁰ⁱ⁴⁵⁶⁷⁸⁹"   # superscripts
                    "₀₁₂₃₄₅₆₇₈₉"           # subscripts
                    "§°±×÷√∞≈≠≤≥"   # math
                    "∈∉∩∪⊕⊙′¬"
                    "⇒⇔∀∃⊥⊤"
                    "≡≃≅⌊⌋⌈⌉"
                    "∑∏∇∂∫∮∼∝"     # operators
                    "ᵀᵢⱼₖₙᵗᵈᵉᵏˡᵐⁿᵒᵖʳˢᵘᵛᵂᵡʸᶻ"   # superscript letters
                    "ₐₑₒᵤᵢⱼₖₙₜ"                                  # subscript letters
                    "̂̃̄̅̆̇̈̉̊̋̌̍̎̏̐̑̒̓̔̕̚"   # combining diacritics
                    "ŷ"                                                                                   # y-hat (specific common variant)
                    "ᾱᾳ"                                                              # accented greek
                    "½⅓¼¾⅔"                       # fractions
                    "ℝℕℤℚℂ"                       # number sets
                    "ºª"                                                                  # ordinals
                    "∅∼≪≫"                                       # more math
                    "Ġ▁"                                                              # tokenizer markers
                    "éšüöäßç"                                            # latin accents in names
                    "₹€£¥"                                                                # currency
                    "⊂⊃⊆⊇"                                                          # set inclusion
                    "⁻⁺"                                                              # extra superscripts (minus, plus)
                    "⏸⏵⏴⏯⏹"                                                      # media glyphs that survive (rare)
                    )
# Accept any character from common non-Latin scripts -- they appear legitimately in tokenizer examples
SCRIPT_RANGES = [
    (0x0900, 0x097F),  # Devanagari (Hindi)
    (0x4E00, 0x9FFF),  # CJK Unified Ideographs
    (0x3040, 0x30FF),  # Japanese hiragana + katakana
    (0xAC00, 0xD7AF),  # Hangul
    (0x0600, 0x06FF),  # Arabic
    (0x0400, 0x04FF),  # Cyrillic
    (0x0370, 0x03FF),  # Greek + Coptic (extra greek chars beyond whitelist)
]
def _in_script_range(ch):
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in SCRIPT_RANGES)
# (placeholder closing paren below replaced by no-op; whitelist set was extended via |= form earlier
NON_ASCII_OK |= set("X"  # no-op sentinel so the trailing ) below stays balanced
                    "αβγδεηθλμνπ"   # greek lowercase
                    "ρστφχψω"
                    "ΔΣΠΩ"
                    "…"                                                                 # ellipsis
                    "↳↱↰"                                                     # arrow turns
                    "✓✗✘"                                                    # checks/crosses
                    )

for p in md_files():
    raw = p.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    for token in MOJIBAKE_BYTES:
        if token in raw:
            findings["mojibake"].append(str(p.relative_to(ROOT)))
            break
    for i, line in enumerate(text.splitlines(), 1):
        for ch in line:
            if ord(ch) > 127 and ch not in NON_ASCII_OK and not _in_script_range(ch):
                findings["non_ascii"].append(str(p.relative_to(ROOT)) + ":" + str(i) + " " + repr(ch))
                break

# ---------- 2. Broken markdown links ----------
LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
for p in md_files():
    text = strip_code(p.read_text(encoding="utf-8"))
    for m in LINK_RE.finditer(text):
        href = m.group(2).split("#")[0]
        if not href or href.startswith(("http://", "https://", "mailto:", "ftp:")):
            continue
        # skip obvious non-paths (commas, braces, spaces look like code spill)
        if any(c in href for c in (" ", ",", "{", "}", "*")):
            continue
        target = (p.parent / href).resolve()
        if not target.exists():
            findings["broken_link"].append(f"{p.relative_to(ROOT)}: -> {href}")

# ---------- 3. Broken image refs ----------
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
for p in md_files():
    text = strip_code(p.read_text(encoding="utf-8"))
    for m in IMG_RE.finditer(text):
        href = m.group(1)
        if href.startswith(("http://", "https://", "data:")): continue
        target = (p.parent / href).resolve()
        if not target.exists():
            findings["broken_image"].append(f"{p.relative_to(ROOT)}: -> {href}")

# ---------- 4. SYLLABUS items in TOC ----------
syllabus = (ROOT / "SYLLABUS.md").read_text(encoding="utf-8").lower()
toc      = (ROOT / "TOC.md").read_text(encoding="utf-8").lower()

key_terms = [
    "dsa", "python", "oop", "sql", "dbms",
    "ml algorithms", "dl basics", "gradient descent", "embedding", "cnn", "rnn", "lstm",
    "reinforcement learning", "diffusion",
    "transformer", "bert", "gpt", "tokenizer", "moe", "rag", "kv-cache",
    "fine-tuning", "prompt engineering", "scaling laws", "llm evaluation", "latest ai models",
    "agent architecture", "tool", "mcp", "stategraph", "pydantic", "memory",
    "guardrail", "agent code",
    "django", "backend observability",
    "react", "streaming",
    "deployment", "mlops", "llm production",
    "git", "testing", "ai system testing",
    "system design", "security", "llm security",
    "behavioral",
]
for term in key_terms:
    if term in syllabus and term not in toc:
        findings["term_in_syllabus_missing_from_toc"].append(term)

# ---------- 5. SYLLABUS/TOC referenced files exist ----------
TOC_LINK_RE = re.compile(r"\(([^)]+\.md)\)")
for m in TOC_LINK_RE.finditer((ROOT / "TOC.md").read_text(encoding="utf-8")):
    href = m.group(1)
    target = (ROOT / href).resolve()
    if not target.exists():
        findings["toc_missing_target"].append(href)

# ---------- 6. Output artefacts ----------
def expected_docx(p: Path) -> Path:
    rel = p.relative_to(ROOT)
    parts = rel.parts
    if parts[0] == "01-CS-Fundamentals" and len(parts) >= 3 and parts[1] == "dsa-patterns":
        return ROOT / "01-CS-Fundamentals" / "out" / "dsa-patterns" / f"{p.stem}.docx"
    if parts[0] == "JOB-SEARCH":
        return ROOT / "JOB-SEARCH" / "out" / f"{p.stem}.docx"
    if len(parts) == 1:  # root .md (README, SYLLABUS, TOC)
        return ROOT / "out_root" / f"{p.stem}.docx"
    return ROOT / parts[0] / "out" / f"{p.stem}.docx"

for p in md_files():
    ex = expected_docx(p)
    if not ex.exists():
        findings["missing_output"].append(str(ex.relative_to(ROOT)))
        continue
    pdf = ex.with_suffix(".pdf")
    if not pdf.exists():
        findings["missing_output"].append(str(pdf.relative_to(ROOT)))

# ---------- 7. Master + digest ----------
for f in ["INTERVIEW-NOTES-MASTER.docx", "INTERVIEW-NOTES-MASTER.pdf",
          "EXAM-DIGEST.docx", "EXAM-DIGEST.pdf"]:
    if not (ROOT / "out_master" / f).exists():
        findings["missing_output"].append(f"out_master/{f}")

# ---------- 8. Stale / suspicious wording ----------
STALE = [
    (r"GPT-3 \(now ", "stale GPT-3 framing"),
    (r"as of 2024", "year-bound copy"),
    (r"as of 2025", "year-bound copy"),
    (r"\bFIXME\b", "FIXME marker"),
    (r"\bXXX\b", "XXX marker"),
    (r"\[citation needed\]", "missing citation"),
]
for p in md_files():
    text = strip_code(p.read_text(encoding="utf-8"))
    for pat, label in STALE:
        for m in re.finditer(pat, text):
            findings["stale_wording"].append(f"{p.relative_to(ROOT)}: {label!r} near pos {m.start()}")

# ---------- 9. Empty / placeholder files ----------
for p in md_files():
    text = p.read_text(encoding="utf-8").strip()
    if len(text) < 200:
        findings["short_file"].append(f"{p.relative_to(ROOT)} ({len(text)} chars)")

# ---------- print summary ----------
print("=" * 60)
print("Notes project audit")
print("=" * 60)
total = sum(len(v) for v in findings.values())
print(f"Total findings: {total}\n")
if total == 0:
    print("Clean.")
for category in sorted(findings.keys()):
    items = findings[category]
    print(f"## {category}  ({len(items)})")
    for it in items[:15]:
        print(f"  - {it}")
    if len(items) > 15:
        print(f"  ... and {len(items)-15} more")
    print()
