"""Generate SVG diagrams illustrating tricky Python concepts.
Consistent visual style with the DSA diagrams. One SVG per concept.
Output: 01-CS-Fundamentals/diagrams/python/*.svg
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "diagrams" / "python"
OUT.mkdir(parents=True, exist_ok=True)

STYLE = """
<style>
  .title { font: bold 17px sans-serif; fill: #1a1a1a; }
  .label { font: 13px sans-serif; fill: #333; }
  .small { font: 11px sans-serif; fill: #555; }
  .tiny  { font: 10px sans-serif; fill: #777; }
  .mono  { font: 13px 'Consolas','Courier New',monospace; fill: #111; }
  .monos { font: 11px 'Consolas','Courier New',monospace; fill: #111; }
  .box   { fill: #f6f8fa; stroke: #444; stroke-width: 1.2; }
  .box2  { fill: #e6f0ff; stroke: #1f6feb; stroke-width: 1.5; }
  .box3  { fill: #fff3cd; stroke: #b58900; stroke-width: 1.5; }
  .box4  { fill: #d4edda; stroke: #1a7f37; stroke-width: 1.5; }
  .boxR  { fill: #fde2e1; stroke: #d33; stroke-width: 1.5; }
  .name  { fill: #fff; stroke: #444; stroke-width: 1.2; }
  .arrow { stroke: #444; stroke-width: 1.6; fill: none; marker-end: url(#arr); }
  .arrow2{ stroke: #1f6feb; stroke-width: 2; fill: none; marker-end: url(#arrB); }
  .arrow3{ stroke: #d33; stroke-width: 2; fill: none; marker-end: url(#arrR); }
  .arrG  { stroke: #1a7f37; stroke-width: 2; fill: none; marker-end: url(#arrG); }
  .dim   { stroke: #bbb; stroke-width: 1; fill: none; stroke-dasharray: 3 3; }
  .ok    { fill: #1a7f37; font: bold 13px sans-serif; }
  .bad   { fill: #d33; font: bold 13px sans-serif; }
</style>
<defs>
  <marker id="arr"  viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M0,0 L10,5 L0,10 Z" fill="#444"/></marker>
  <marker id="arrB" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M0,0 L10,5 L0,10 Z" fill="#1f6feb"/></marker>
  <marker id="arrR" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M0,0 L10,5 L0,10 Z" fill="#d33"/></marker>
  <marker id="arrG" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M0,0 L10,5 L0,10 Z" fill="#1a7f37"/></marker>
</defs>
"""

def svg(w, h, body, title=None):
    t = f'<text x="{w//2}" y="24" text-anchor="middle" class="title">{title}</text>' if title else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}">{STYLE}<rect width="{w}" height="{h}" fill="#ffffff"/>{t}{body}</svg>')

def box(x, y, w, h, val, cls="box", font="mono", anchor="middle"):
    tx = x + w/2 if anchor == "middle" else x + 8
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" class="{cls}"/>'
            f'<text x="{tx}" y="{y+h/2+5}" text-anchor="{anchor}" class="{font}">{val}</text>')

def name_tag(x, y, label, cls="name", w=54, h=30):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" class="{cls}"/>'
            f'<text x="{x+w/2}" y="{y+h/2+5}" text-anchor="middle" class="mono">{label}</text>')

def text(x, y, s, cls="label", anchor="start"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{cls}">{s}</text>'

diagrams = {}

# ---------- 01 Names vs Objects (aliasing) ----------
def d01():
    b = ""
    b += text(30, 55, "b = a  copies the reference, not the list", "label")
    b += name_tag(40, 80, "a")
    b += name_tag(40, 130, "b")
    # the one shared list object
    b += box(230, 92, 210, 56, "", "box2")
    b += text(245, 112, "list object  id=0x7f..", "monos")
    b += text(245, 134, "[1, 2, 3, 4]", "mono")
    b += f'<path class="arrow2" d="M 94 95 C 160 95 160 110 228 112"/>'
    b += f'<path class="arrow2" d="M 94 145 C 160 145 160 130 228 126"/>'
    b += text(30, 200, "b.append(4)  mutates the shared object → visible through a too.", "small")
    b += text(30, 220, "Rebinding b = [9] would instead point b at a NEW object (a unchanged).", "small")
    return svg(560, 245, b, "Names are labels, not boxes (aliasing)")
diagrams["01-names-objects"] = d01

# ---------- 02 Mutable vs Immutable: rebind vs mutate ----------
def d02():
    b = ""
    # immutable side
    b += text(30, 55, "Immutable (int): += rebinds to a NEW object", "label")
    b += name_tag(40, 75, "x")
    b += box(150, 72, 50, 34, "10", "box")
    b += box(250, 72, 50, 34, "11", "box4")
    b += f'<path class="dim" d="M 94 89 L 148 89"/>'
    b += f'<path class="arrow3" d="M 94 95 C 120 130 230 130 275 108"/>'
    b += text(120, 150, "x += 1  → x now points to 11; old 10 untouched", "small")
    # mutable side
    b += text(30, 200, "Mutable (list): append mutates the SAME object in place", "label")
    b += name_tag(40, 220, "y")
    b += box(150, 217, 150, 34, "[1, 2]  →  [1, 2, 3]", "box2", "monos")
    b += f'<path class="arrow2" d="M 94 234 L 148 234"/>'
    b += text(120, 280, "y.append(3)  → same id(y), content changed", "small")
    return svg(560, 300, b, "Rebind (immutable) vs mutate (mutable)")
diagrams["02-mutable-immutable"] = d02

# ---------- 03 is vs == small int cache ----------
def d03():
    b = ""
    b += text(30, 52, "Small ints (−5..256) are cached singletons", "label")
    b += name_tag(40, 78, "a")
    b += name_tag(40, 122, "b")
    b += box(200, 88, 120, 40, "256", "box4")
    b += text(200, 150, "shared cached object", "tiny")
    b += f'<path class="arrow2" d="M 94 93 C 150 93 150 105 198 105"/>'
    b += f'<path class="arrow2" d="M 94 137 C 150 137 150 116 198 113"/>'
    b += text(335, 100, "a is b → True", "ok")
    b += text(335, 120, "a == b → True", "small")
    # 257 side
    b += name_tag(40, 200, "c")
    b += name_tag(40, 244, "d")
    b += box(200, 192, 120, 36, "257", "box")
    b += box(200, 236, 120, 36, "257", "box")
    b += f'<path class="arrow d3" stroke="#444" stroke-width="1.6" fill="none" marker-end="url(#arr)" d="M 94 215 L 198 210"/>'
    b += f'<path stroke="#444" stroke-width="1.6" fill="none" marker-end="url(#arr)" d="M 94 259 L 198 254"/>'
    b += text(335, 212, "c is d → False", "bad")
    b += text(335, 232, "c == d → True", "small")
    b += text(30, 295, "Rule: use == for value; reserve is for None / singletons.", "small")
    return svg(560, 315, b, "is vs == and the small-int cache")
diagrams["03-is-vs-eq"] = d03

# ---------- 04 shallow vs deep copy ----------
def d04():
    b = ""
    b += text(30, 50, "original = [[1, 2], 3]", "mono")
    # original
    b += name_tag(40, 70, "orig", w=60)
    b += box(140, 68, 90, 34, "[ * , 3 ]", "box", "monos")
    b += box(280, 60, 90, 30, "[1, 2]", "box2", "monos")
    b += f'<path class="arrow" d="M 104 85 L 138 85"/>'
    b += f'<path class="arrow2" d="M 232 78 L 278 75"/>'
    # shallow
    b += text(30, 140, "shallow = copy.copy(orig)", "mono")
    b += name_tag(40, 158, "shal", w=60)
    b += box(140, 156, 90, 34, "[ * , 3 ]", "box3", "monos")
    b += f'<path class="arrow" d="M 104 173 L 138 173"/>'
    b += f'<path class="arrow3" d="M 232 173 C 260 173 260 90 278 84"/>'
    b += text(245, 205, "inner list SHARED → mutating it hits both!", "bad")
    # deep
    b += text(30, 250, "deep = copy.deepcopy(orig)", "mono")
    b += name_tag(40, 268, "deep", w=60)
    b += box(140, 266, 90, 34, "[ * , 3 ]", "box4", "monos")
    b += box(280, 268, 90, 30, "[1, 2]", "box4", "monos")
    b += f'<path class="arrow" d="M 104 283 L 138 283"/>'
    b += f'<path class="arrG" d="M 232 283 L 278 283"/>'
    b += text(245, 315, "fully independent copy", "ok")
    return svg(560, 330, b, "Shallow vs deep copy")
diagrams["04-copy"] = d04

# ---------- 05 mutable default argument ----------
def d05():
    b = ""
    b += text(30, 50, "def add(x, bucket=[]):   # default built ONCE at def-time", "monos")
    b += box(60, 70, 160, 40, "bucket  (one list)", "boxR", "monos")
    b += text(60, 130, "Each call with no bucket reuses this same list:", "small")
    calls = [("add(1)", "[1]"), ("add(2)", "[1, 2]"), ("add(3)", "[1, 2, 3]")]
    x = 60
    for c, r in calls:
        b += box(x, 150, 130, 56, "", "box")
        b += text(x+12, 172, c, "mono")
        b += text(x+12, 194, "→ " + r, "monos")
        b += f'<path class="arrow3" d="M 140 112 C 140 130 {x+65} 130 {x+65} 148"/>'
        x += 160
    b += text(30, 245, "Fix: bucket=None; if bucket is None: bucket = []  (fresh each call)", "small")
    return svg(560, 265, b, "Mutable default argument trap")
diagrams["05-default-arg"] = d05

# ---------- 06 late-binding closure ----------
def d06():
    b = ""
    b += text(30, 50, "fns = [lambda: i for i in range(3)]", "mono")
    # three lambdas
    for k in range(3):
        b += box(40+k*110, 75, 90, 36, f"fns[{k}]", "box", "monos")
        b += f'<path class="arrow3" d="M {85+k*110} 111 C {85+k*110} 135 280 135 290 150"/>'
    b += box(290, 148, 110, 40, "i = 2", "boxR")
    b += text(300, 210, "all three close over the SAME i (final value 2)", "bad")
    b += text(30, 250, "fns[0]() == fns[1]() == fns[2]() == 2", "monos")
    b += text(30, 285, "Fix: lambda i=i: i  — capture current value as a default → 0,1,2", "small")
    return svg(560, 305, b, "Late-binding closures")
diagrams["06-closure"] = d06

# ---------- 07 LEGB ----------
def d07():
    b = ""
    rings = [("Built-in", "#f6f8fa", 40, 40, 480, 280),
             ("Global (module)", "#e6f0ff", 90, 70, 380, 220),
             ("Enclosing (outer fn)", "#fff3cd", 150, 105, 260, 150),
             ("Local (current fn)", "#d4edda", 210, 140, 140, 80)]
    for label, fill, x, y, w, h in rings:
        b += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="#888"/>'
        b += text(x+10, y+18, label, "small")
    b += text(280, 188, "name", "mono", "middle")
    b += f'<path class="arrow2" d="M 280 195 L 280 250"/>'
    b += text(530, 165, "lookup", "small")
    b += text(530, 182, "order ↓", "small")
    b += f'<path class="arrow" d="M 555 130 L 555 250"/>'
    return svg(600, 340, b, "LEGB name resolution order")
diagrams["07-legb"] = d07

# ---------- 08 decorator ----------
def d08():
    b = ""
    b += text(30, 55, "@retry  →  f = retry(f)", "mono")
    b += box(40, 80, 110, 60, "call f()", "box2")
    b += box(230, 75, 150, 90, "wrapper", "box3")
    b += text(248, 100, "try / retry", "monos")
    b += box(255, 110, 110, 44, "real f()", "box4")
    b += f'<path class="arrow2" d="M 150 110 L 228 110"/>'
    b += text(160, 100, "calls", "tiny")
    b += f'<path class="arrow" d="M 365 132 C 410 132 410 60 200 60 C 120 60 110 76 95 78"/>'
    b += text(250, 195, "wrapper adds behavior (retry/log/cache) around f,", "small")
    b += text(250, 213, "then returns f's result. @functools.wraps keeps f's name/doc.", "small")
    return svg(560, 235, b, "How a decorator wraps a function")
diagrams["08-decorator"] = d08

# ---------- 09 class vs instance attribute ----------
def d09():
    b = ""
    b += text(30, 50, "class Dog:  tricks = []   # CLASS attribute (shared)", "monos")
    b += box(220, 70, 130, 44, "Dog.tricks []", "boxR", "monos")
    b += name_tag(40, 110, "a", w=44)
    b += name_tag(40, 160, "b", w=44)
    b += f'<path class="arrow3" d="M 86 120 C 150 120 150 95 218 92"/>'
    b += f'<path class="arrow3" d="M 86 170 C 150 170 150 100 218 100"/>'
    b += text(30, 220, "a.tricks.append('sit')  →  b.tricks == ['sit']  (shared!)", "bad")
    b += text(30, 250, "Fix: set per-instance in __init__:  self.tricks = []", "small")
    return svg(560, 270, b, "Shared mutable class attribute trap")
diagrams["09-class-attr"] = d09

# ---------- 10 MRO diamond ----------
def d10():
    b = ""
    b += box(240, 50, 80, 38, "A", "box4")
    b += box(140, 130, 80, 38, "B", "box2")
    b += box(340, 130, 80, 38, "C", "box2")
    b += box(240, 210, 80, 38, "D", "box3")
    b += f'<path class="arrow" d="M 180 130 L 260 88"/>'
    b += f'<path class="arrow" d="M 380 130 L 300 88"/>'
    b += f'<path class="arrow" d="M 260 210 L 200 168"/>'
    b += f'<path class="arrow" d="M 300 210 L 360 168"/>'
    b += text(460, 120, "C3 linearization:", "small")
    b += text(460, 142, "D → B → C → A → object", "monos")
    b += text(460, 175, "super() follows MRO,", "small")
    b += text(460, 193, "not the literal parent.", "small")
    return svg(660, 270, b, "MRO / C3 in diamond inheritance")
diagrams["10-mro"] = d10

# ---------- 11 __slots__ vs __dict__ ----------
def d11():
    b = ""
    b += text(40, 55, "Default: per-instance __dict__", "label")
    b += box(40, 70, 200, 44, "instance", "box")
    b += box(40, 120, 200, 60, "__dict__ {'x':1,'y':2}", "box3", "monos")
    b += f'<path class="arrow" d="M 140 114 L 140 118"/>'
    b += text(40, 210, "flexible but bigger + slower", "small")
    b += text(330, 55, "__slots__ = ('x','y')", "label")
    b += box(330, 70, 200, 44, "instance", "box4")
    b += box(330, 120, 95, 60, "x slot", "box4", "monos")
    b += box(435, 120, 95, 60, "y slot", "box4", "monos")
    b += f'<path class="arrG" d="M 430 114 L 430 118"/>'
    b += text(330, 210, "compact + faster; no new attrs", "small")
    return svg(580, 235, b, "__slots__ removes the per-instance __dict__")
diagrams["11-slots"] = d11

# ---------- 12 generator lazy single-pass ----------
def d12():
    b = ""
    b += text(30, 50, "gen = (x*x for x in range(4))   # nothing computed yet", "monos")
    vals = ["0", "1", "4", "9"]
    for k, v in enumerate(vals):
        cls = "box4" if k == 0 else ("box2" if k == 1 else "box")
        b += box(60+k*110, 75, 90, 40, v, cls)
        b += text(60+k*110+45, 135, f"next() #{k+1}", "tiny", "middle")
    b += f'<path class="arrow2" d="M 60 160 L 480 160"/>'
    b += text(250, 185, "values produced on demand, one at a time →", "small", "middle")
    b += text(30, 215, "Single-pass: once exhausted it yields nothing; O(1) memory.", "small")
    return svg(560, 235, b, "Generators: lazy, single-pass evaluation")
diagrams["12-generator"] = d12

# ---------- 13 GIL ----------
def d13():
    b = ""
    b += text(30, 55, "3 threads, 1 process — only one holds the GIL at a time", "label")
    for k in range(3):
        b += box(40, 80+k*48, 110, 38, f"Thread {k+1}", "box2")
    b += box(230, 128, 80, 44, "GIL", "boxR")
    for k in range(3):
        b += f'<path class="dim" d="M 150 99+{k*48} L 228 150"/>'.replace("99+0","99").replace("99+48","147").replace("99+96","195")
    b += box(390, 128, 120, 44, "bytecode", "box4")
    b += f'<path class="arrow3" d="M 310 150 L 388 150"/>'
    b += text(40, 245, "CPU-bound → threads take turns (no speedup).", "small")
    b += text(40, 267, "I/O-bound → GIL released while waiting (threads help).", "small")
    return svg(600, 290, b, "The GIL serializes Python bytecode")
diagrams["13-gil"] = d13

# ---------- 14 concurrency decision ----------
def d14():
    b = ""
    b += box(210, 45, 150, 44, "What's the bottleneck?", "box")
    b += box(40, 140, 150, 70, "asyncio /\nthreads", "box2")
    b += box(210, 140, 150, 70, "multiprocessing", "box4")
    b += box(390, 140, 160, 70, "NumPy / native", "box3")
    # manual two-line text in boxes
    b = b.replace('<text x="115" y="179" text-anchor="middle" class="mono">asyncio /\nthreads</text>',
                  '<text x="115" y="172" text-anchor="middle" class="monos">asyncio /</text>'
                  '<text x="115" y="190" text-anchor="middle" class="monos">threads</text>')
    b = b.replace('<text x="285" y="179" text-anchor="middle" class="mono">multiprocessing</text>',
                  '<text x="285" y="180" text-anchor="middle" class="monos">multiprocessing</text>')
    b = b.replace('<text x="470" y="179" text-anchor="middle" class="mono">NumPy / native</text>',
                  '<text x="470" y="180" text-anchor="middle" class="monos">NumPy / native</text>')
    b += f'<path class="arrow2" d="M 250 89 L 130 138"/>'
    b += f'<path class="arrow" d="M 285 89 L 285 138"/>'
    b += f'<path class="arrow" d="M 320 89 L 450 138"/>'
    b += text(120, 120, "I/O-bound", "small", "middle")
    b += text(255, 120, "CPU-bound (Python)", "small", "middle")
    b += text(470, 120, "CPU-bound (numeric)", "small", "middle")
    b += text(115, 230, "GIL released on I/O", "tiny", "middle")
    b += text(285, 230, "separate processes", "tiny", "middle")
    b += text(470, 230, "releases GIL in C", "tiny", "middle")
    return svg(600, 255, b, "Concurrency: pick the right tool")
diagrams["14-concurrency"] = d14

# ---------- 15 bit concatenation ----------
def d15():
    b = ""
    b += text(30, 50, "Append binary of i onto ans:  ans = (ans &lt;&lt; i.bit_length()) | i", "monos")
    b += text(30, 95, "ans = 0b101", "mono")
    b += box(150, 78, 30, 30, "1", "box2")
    b += box(180, 78, 30, 30, "0", "box2")
    b += box(210, 78, 30, 30, "1", "box2")
    b += text(280, 95, "i = 3 = 0b11  (bit_length 2)", "mono")
    # shift
    b += text(30, 150, "&lt;&lt; 2 makes room:", "small")
    for k, v in enumerate(["1","0","1","0","0"]):
        cls = "box2" if k < 3 else "box"
        b += box(150+k*30, 133, 30, 30, v, cls)
    # OR
    b += text(30, 205, "| 3 fills it:", "small")
    for k, v in enumerate(["1","0","1","1","1"]):
        cls = "box2" if k < 3 else "box4"
        b += box(150+k*30, 188, 30, 30, v, cls)
    b += text(330, 208, "= 0b10111  ✓", "ok")
    b += text(30, 255, "WRONG: ans + ans &lt;&lt; k parses as (2*ans) &lt;&lt; k;  and ans+ans appends ans, not i.", "small")
    return svg(680, 275, b, "Concatenating binary: shift to make room, then OR i")
diagrams["15-bit-concat"] = d15

# write all
for name, fn in diagrams.items():
    (OUT / f"{name}.svg").write_text(fn(), encoding="utf-8")
    print("svg:", name)
print(f"\n{len(diagrams)} SVGs written to {OUT}")
