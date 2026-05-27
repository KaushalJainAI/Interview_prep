"""Replace non-ASCII characters in all .md files with ASCII equivalents.

Goal: any editor (Notepad, cp1252 viewers, GitHub) renders the files cleanly.
Side benefit: smaller files, no encoding ambiguity.

Conservative mappings only — preserves meaning, drops decorative emoji.
"""
import re
from pathlib import Path

ROOT = Path(r"C:\Users\91700\Desktop\Interview notes")

# Character → ASCII replacement (most common first)
REPL = {
    # Dashes
    "—": "--",      # em dash
    "–": "-",       # en dash
    "−": "-",       # minus sign
    # Quotes
    "‘": "'", "’": "'",   # single curly
    "“": '"', "”": '"',   # double curly
    # Spaces & punctuation
    " ": " ",       # nbsp
    "…": "...",     # ellipsis
    "•": "*",       # bullet
    "·": "*",       # middle dot
    "°": " deg ",   # degree
    # Math
    "≤": "<=", "≥": ">=", "≠": "!=",
    "×": "x",       # multiplication
    "÷": "/",       # division
    "²": "^2", "³": "^3",
    "√": "sqrt",
    "∞": "inf",
    "≈": "~=",      # almost equal
    "→": "->", "←": "<-", "↑": "^", "↓": "v",
    "⇒": "=>",
    "∀": "for all", "∃": "exists",
    "∈": "in", "∉": "not in",
    "∩": "intersect", "∪": "union",
    "⊕": "(+)",     # XOR (oplus)
    "⊙": "(.)",     # dot in circle
    "′": "'",       # prime
    "±": "+/-",
    # Greek (keep names for readability)
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
    "ε": "epsilon", "η": "eta", "θ": "theta", "λ": "lambda",
    "μ": "mu", "ν": "nu", "π": "pi", "ρ": "rho",
    "σ": "sigma", "τ": "tau", "φ": "phi", "χ": "chi",
    "ψ": "psi", "ω": "omega",
    "Δ": "Delta", "Σ": "Sigma", "Π": "Pi",
    # Subscript/superscript digits (drop fancy)
    "₀":"0","₁":"1","₂":"2","₃":"3","₄":"4",
    "₅":"5","₆":"6","₇":"7","₈":"8","₉":"9",
    "⁰":"0","¹":"1","⁴":"4","⁵":"5","⁶":"6",
    "⁷":"7","⁸":"8","⁹":"9",
    # Misc
    "©": "(c)", "®": "(R)", "™": "(TM)",
}

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"   # most pictographs
    "\U0001F600-\U0001F64F"   # emoticons
    "\U0001F900-\U0001F9FF"   # supplemental
    "\U00002600-\U000027BF"   # dingbats / misc symbols
    "\U0001F680-\U0001F6FF"   # transport
    "\U00002700-\U000027BF"   # dingbats
    "\U0001F1E6-\U0001F1FF"   # flags
    "]+",
    flags=re.UNICODE
)

def sanitize(text: str) -> str:
    for k, v in REPL.items():
        if k in text:
            text = text.replace(k, v)
    # strip leading emoji from headings — they're decorative
    text = EMOJI_RE.sub("", text)
    # collapse double spaces introduced by emoji removal at the start of headings
    text = re.sub(r"^(#+) +", r"\1 ", text, flags=re.MULTILINE)
    return text

def main():
    changed = 0
    for md in ROOT.rglob("*.md"):
        # Skip the cheatsheets/ external PDFs README — leave alone
        # Skip any "out/" generated subdirs
        if any(part in {"out", "out_root", "out_master", "_html"} for part in md.parts):
            continue
        original = md.read_text(encoding="utf-8")
        new = sanitize(original)
        if new != original:
            md.write_text(new, encoding="utf-8")
            changed += 1
            print("sanitized:", md.relative_to(ROOT))
    print(f"\ntotal files changed: {changed}")

if __name__ == "__main__":
    main()
