"""Generate SVG diagrams for each DSA pattern. One SVG per pattern, consistent style."""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)

# Shared style block
STYLE = """
<style>
  .title { font: bold 16px sans-serif; fill: #1a1a1a; }
  .label { font: 12px sans-serif; fill: #333; }
  .small { font: 10px sans-serif; fill: #555; }
  .mono  { font: 13px 'Consolas','Courier New',monospace; fill: #111; }
  .box   { fill: #f6f8fa; stroke: #444; stroke-width: 1.2; }
  .box2  { fill: #e6f0ff; stroke: #1f6feb; stroke-width: 1.5; }
  .box3  { fill: #fff3cd; stroke: #b58900; stroke-width: 1.5; }
  .box4  { fill: #d4edda; stroke: #1a7f37; stroke-width: 1.5; }
  .arrow { stroke: #444; stroke-width: 1.6; fill: none; marker-end: url(#arr); }
  .arrow2{ stroke: #1f6feb; stroke-width: 2; fill: none; marker-end: url(#arrB); }
  .arrow3{ stroke: #d33; stroke-width: 2; fill: none; marker-end: url(#arrR); }
  .dim   { stroke: #bbb; stroke-width: 1; fill: none; stroke-dasharray: 3 3; }
</style>
<defs>
  <marker id="arr"  viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M0,0 L10,5 L0,10 Z" fill="#444"/></marker>
  <marker id="arrB" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M0,0 L10,5 L0,10 Z" fill="#1f6feb"/></marker>
  <marker id="arrR" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M0,0 L10,5 L0,10 Z" fill="#d33"/></marker>
</defs>
"""

def svg(w, h, body, title=None):
    t = f'<text x="{w//2}" y="22" text-anchor="middle" class="title">{title}</text>' if title else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{STYLE}{t}{body}</svg>'

def cell(x, y, val, cls="box", w=46, h=46, font="mono"):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="{cls}"/>'
            f'<text x="{x+w/2}" y="{y+h/2+5}" text-anchor="middle" class="{font}">{val}</text>')

def idx_row(start_x, y, n, label_y_offset=-6):
    s = ""
    for i in range(n):
        s += f'<text x="{start_x + i*46 + 23}" y="{y + label_y_offset}" text-anchor="middle" class="small">{i}</text>'
    return s

# ---------------- 01 Arrays & Hashing ----------------
def d01():
    arr = [2, 7, 11, 15]
    body = ""
    body += '<text x="40" y="60" class="label">Array (scan once):</text>'
    body += idx_row(40, 78, 4)
    for i,v in enumerate(arr):
        cls = "box2" if i==1 else "box"
        body += cell(40+i*46, 85, v, cls)
    # arrow from arr[1]=7 to map lookup
    body += '<path class="arrow2" d="M 130 155 C 130 200 320 200 320 175"/>'
    body += '<text x="220" y="195" class="small">look up complement (9-7=2)</text>'
    # hashmap
    body += '<text x="320" y="70" class="label">Hashmap (seen values → idx):</text>'
    body += '<rect x="280" y="85" width="180" height="80" class="box4"/>'
    body += '<text x="295" y="115" class="mono">2 → 0  ✓ found!</text>'
    body += '<text x="295" y="140" class="mono">target = 9</text>'
    body += '<text x="295" y="158" class="mono">return [0, 1]</text>'
    body += '<text x="40" y="250" class="label">Idea: trade O(n) space for O(1) lookup; one pass replaces nested loop.</text>'
    body += '<text x="40" y="272" class="small">Time O(n) · Space O(n)</text>'
    return svg(560, 300, body, "Two-Sum via Hashmap (Arrays &amp; Hashing)")

# ---------------- 02 Two Pointers ----------------
def d02():
    arr = [-4, -1, 0, 3, 5, 8, 11]
    body = '<text x="40" y="60" class="label">Sorted array · target sum = 7</text>'
    n = len(arr)
    for i,v in enumerate(arr):
        cls = "box"
        if i == 1: cls = "box2"
        if i == 5: cls = "box3"
        body += cell(40+i*52, 80, v, cls, w=46, h=46)
    body += '<text x="63" y="150" text-anchor="middle" class="mono">L</text>'
    body += '<path class="arrow2" d="M 63 145 L 63 128"/>'
    body += '<text x="63+260" y="150" text-anchor="middle" class="mono">R</text>'.replace("63+260","323")
    body += '<path class="arrow3" d="M 323 145 L 323 128"/>'
    body += '<text x="40" y="190" class="label">arr[L] + arr[R] = -1 + 8 = 7 ✓</text>'
    body += '<text x="40" y="225" class="label">Decision rule:</text>'
    body += '<text x="60" y="247" class="mono">sum &lt; target → L++   (need larger)</text>'
    body += '<text x="60" y="267" class="mono">sum &gt; target → R--   (need smaller)</text>'
    body += '<text x="60" y="287" class="mono">sum = target → record &amp; move</text>'
    body += '<text x="40" y="320" class="small">Each step shrinks window by 1 → O(n) total.</text>'
    return svg(560, 340, body, "Two Pointers — Converging on Target")

# ---------------- 03 Sliding Window ----------------
def d03():
    s = list("a b c a b c b b".split())
    body = '<text x="40" y="60" class="label">String:  a b c a b c b b   (longest substring w/o repeat)</text>'
    for i,v in enumerate(s):
        cls = "box"
        if 3 <= i <= 5: cls = "box4"
        body += cell(40+i*46, 80, v, cls)
    body += '<rect x="40+3*46-3" y="76" width="142" height="54" fill="none" stroke="#1a7f37" stroke-width="2.4" stroke-dasharray="4 3"/>'.replace("40+3*46-3","175")
    body += '<text x="246" y="148" text-anchor="middle" class="small">window [L..R]</text>'
    body += '<text x="40" y="180" class="label">Expand R; while invalid, shrink L. Best = max window seen.</text>'
    body += '<text x="40" y="215" class="mono">for r in range(n):</text>'
    body += '<text x="60" y="235" class="mono">count[s[r]] += 1</text>'
    body += '<text x="60" y="255" class="mono">while violates(count):</text>'
    body += '<text x="80" y="275" class="mono">count[s[l]] -= 1; l += 1</text>'
    body += '<text x="60" y="295" class="mono">best = max(best, r - l + 1)</text>'
    body += '<text x="40" y="325" class="small">Each index enters/leaves window once → O(n).</text>'
    return svg(560, 345, body, "Sliding Window — Expand / Shrink")

# ---------------- 04 Binary Search ----------------
def d04():
    arr = [1, 3, 5, 7, 9, 11, 13, 15]
    body = '<text x="40" y="60" class="label">Sorted array, target = 11</text>'
    body += idx_row(40, 78, 8)
    for i,v in enumerate(arr):
        cls = "box"
        if i in (0,7): cls = "box2"
        if i == 3: cls = "box3"
        body += cell(40+i*46, 85, v, cls)
    body += '<text x="63"  y="155" text-anchor="middle" class="mono">lo</text>'
    body += '<text x="201" y="155" text-anchor="middle" class="mono">mid</text>'
    body += '<text x="385" y="155" text-anchor="middle" class="mono">hi</text>'
    body += '<text x="40" y="195" class="label">arr[mid]=7 &lt; 11 → lo = mid+1   (discard left half)</text>'
    # next step
    body += '<text x="40" y="225" class="label">Step 2:</text>'
    for i,v in enumerate(arr):
        x = 40+i*46
        cls = "box"
        if i<4: cls = "box"  # eliminated, dim
        if i in (4,7): cls = "box2"
        if i == 5: cls = "box3"
        body += f'<rect x="{x}" y="240" width="46" height="46" class="{cls}" opacity="{0.3 if i<4 else 1}"/>'
        body += f'<text x="{x+23}" y="269" text-anchor="middle" class="mono" opacity="{0.3 if i<4 else 1}">{v}</text>'
    body += '<text x="40" y="320" class="small">Search space halves each step → O(log n).</text>'
    return svg(560, 340, body, "Binary Search — Halve the Search Space")

# ---------------- 05 Stack ----------------
def d05():
    body = '<text x="40" y="60" class="label">Monotonic decreasing stack (Next Greater Element)</text>'
    body += '<text x="40" y="85" class="mono">arr = [2, 1, 3]</text>'
    # 3 columns showing stack state
    cols = [
        ("push 2", ["2"]),
        ("push 1", ["1", "2"]),
        ("3 > 1: pop 1 (ans=3)\n3 > 2: pop 2 (ans=3)\npush 3", ["3"]),
    ]
    for c,(lbl, stk) in enumerate(cols):
        x0 = 60 + c*170
        body += f'<text x="{x0+40}" y="120" text-anchor="middle" class="small">step {c+1}</text>'
        for caption_i, line in enumerate(lbl.split("\n")):
            body += f'<text x="{x0}" y="{140+caption_i*15}" class="small">{line}</text>'
        # stack rendered bottom-up
        base_y = 290
        for i, v in enumerate(stk):
            y = base_y - i*44
            body += f'<rect x="{x0}" y="{y}" width="80" height="40" class="box2"/>'
            body += f'<text x="{x0+40}" y="{y+25}" text-anchor="middle" class="mono">{v}</text>'
        body += f'<line x1="{x0}" y1="291" x2="{x0+80}" y2="291" stroke="#444" stroke-width="2"/>'
    body += '<text x="40" y="335" class="small">Each element pushed/popped at most once → O(n) total.</text>'
    return svg(620, 360, body, "Monotonic Stack — Next Greater Element")

# ---------------- 06 Linked List ----------------
def d06():
    body = '<text x="40" y="60" class="label">Reverse a singly linked list (3 pointers)</text>'
    # nodes
    vals = ["1","2","3","4","∅"]
    for i,v in enumerate(vals):
        x = 60 + i*100
        body += f'<rect x="{x}" y="100" width="60" height="40" class="box2"/>'
        body += f'<text x="{x+30}" y="125" text-anchor="middle" class="mono">{v}</text>'
        if i < len(vals)-1:
            body += f'<path class="arrow" d="M {x+62} 120 L {x+97} 120"/>'
    body += '<text x="90" y="180" text-anchor="middle" class="mono">prev=∅</text>'
    body += '<text x="190" y="180" text-anchor="middle" class="mono">curr</text>'
    body += '<text x="290" y="180" text-anchor="middle" class="mono">next</text>'
    body += '<text x="40" y="225" class="label">Loop:</text>'
    body += '<text x="60" y="247" class="mono">nxt = curr.next</text>'
    body += '<text x="60" y="267" class="mono">curr.next = prev      # flip pointer</text>'
    body += '<text x="60" y="287" class="mono">prev = curr; curr = nxt</text>'
    body += '<text x="40" y="320" class="small">Return prev at end. O(n) time, O(1) space.</text>'
    return svg(620, 340, body, "Linked List — Reversal Pattern")

# ---------------- 07 Trees ----------------
def d07():
    body = ''
    nodes = {
        "A":(280,80,"1"),
        "B":(180,150,"2"),"C":(380,150,"3"),
        "D":(120,220,"4"),"E":(230,220,"5"),"F":(330,220,"6"),"G":(430,220,"7"),
    }
    edges = [("A","B"),("A","C"),("B","D"),("B","E"),("C","F"),("C","G")]
    for a,b in edges:
        x1,y1,_ = nodes[a]; x2,y2,_ = nodes[b]
        body += f'<line x1="{x1}" y1="{y1+22}" x2="{x2}" y2="{y2-22}" stroke="#444" stroke-width="1.5"/>'
    for k,(x,y,v) in nodes.items():
        body += f'<circle cx="{x}" cy="{y}" r="22" class="box2"/>'
        body += f'<text x="{x}" y="{y+5}" text-anchor="middle" class="mono">{v}</text>'
    body += '<text x="40" y="270" class="label">Inorder  (L,Node,R):  4 2 5 1 6 3 7</text>'
    body += '<text x="40" y="290" class="label">Preorder (Node,L,R):  1 2 4 5 3 6 7</text>'
    body += '<text x="40" y="310" class="label">Postorder(L,R,Node):  4 5 2 6 7 3 1</text>'
    body += '<text x="40" y="330" class="label">Level   (BFS):        1 2 3 4 5 6 7</text>'
    return svg(620, 350, body, "Binary Tree — Traversals")

# ---------------- 08 Tries ----------------
def d08():
    body = ''
    # root
    body += '<circle cx="310" cy="70" r="20" class="box2"/><text x="310" y="75" text-anchor="middle" class="mono">·</text>'
    # children: c, b
    body += '<circle cx="200" cy="140" r="20" class="box2"/><text x="200" y="145" text-anchor="middle" class="mono">c</text>'
    body += '<circle cx="420" cy="140" r="20" class="box2"/><text x="420" y="145" text-anchor="middle" class="mono">b</text>'
    body += '<line x1="310" y1="90" x2="200" y2="120" stroke="#444"/>'
    body += '<line x1="310" y1="90" x2="420" y2="120" stroke="#444"/>'
    # c-a, c-o
    body += '<circle cx="140" cy="210" r="20" class="box2"/><text x="140" y="215" text-anchor="middle" class="mono">a</text>'
    body += '<circle cx="260" cy="210" r="20" class="box2"/><text x="260" y="215" text-anchor="middle" class="mono">o</text>'
    body += '<line x1="200" y1="160" x2="140" y2="190" stroke="#444"/>'
    body += '<line x1="200" y1="160" x2="260" y2="190" stroke="#444"/>'
    # c-a-t, c-a-r
    body += '<circle cx="100" cy="280" r="20" class="box3"/><text x="100" y="285" text-anchor="middle" class="mono">t</text>'
    body += '<circle cx="180" cy="280" r="20" class="box3"/><text x="180" y="285" text-anchor="middle" class="mono">r</text>'
    body += '<line x1="140" y1="230" x2="100" y2="260" stroke="#444"/>'
    body += '<line x1="140" y1="230" x2="180" y2="260" stroke="#444"/>'
    # c-o-w
    body += '<circle cx="260" cy="280" r="20" class="box3"/><text x="260" y="285" text-anchor="middle" class="mono">w</text>'
    body += '<line x1="260" y1="230" x2="260" y2="260" stroke="#444"/>'
    # b-a-t
    body += '<circle cx="420" cy="210" r="20" class="box2"/><text x="420" y="215" text-anchor="middle" class="mono">a</text>'
    body += '<line x1="420" y1="160" x2="420" y2="190" stroke="#444"/>'
    body += '<circle cx="420" cy="280" r="20" class="box3"/><text x="420" y="285" text-anchor="middle" class="mono">t</text>'
    body += '<line x1="420" y1="230" x2="420" y2="260" stroke="#444"/>'
    body += '<text x="40" y="320" class="label">Words: cat, car, cow, bat   (yellow = end-of-word)</text>'
    body += '<text x="40" y="338" class="small">Shared prefixes compressed. Lookup/insert O(m) where m = word length.</text>'
    return svg(620, 360, body, "Trie — Prefix Tree")

# ---------------- 09 Heap ----------------
def d09():
    body = ''
    # tree
    pos = {0:(220,70),1:(140,140),2:(300,140),3:(90,210),4:(190,210),5:(260,210),6:(360,210)}
    vals = [1,3,2,7,5,4,8]
    edges = [(0,1),(0,2),(1,3),(1,4),(2,5),(2,6)]
    for a,b in edges:
        x1,y1 = pos[a]; x2,y2 = pos[b]
        body += f'<line x1="{x1}" y1="{y1+22}" x2="{x2}" y2="{y2-22}" stroke="#444"/>'
    for i,(x,y) in pos.items():
        body += f'<circle cx="{x}" cy="{y}" r="22" class="box2"/>'
        body += f'<text x="{x}" y="{y+5}" text-anchor="middle" class="mono">{vals[i]}</text>'
    # array
    body += '<text x="450" y="80" class="label">Array form (1-indexed nav):</text>'
    for i,v in enumerate(vals):
        x = 450 + i*30
        body += f'<rect x="{x}" y="95" width="28" height="32" class="box"/>'
        body += f'<text x="{x+14}" y="117" text-anchor="middle" class="mono">{v}</text>'
        body += f'<text x="{x+14}" y="90" text-anchor="middle" class="small">{i}</text>'
    body += '<text x="450" y="160" class="mono">parent(i) = (i-1)//2</text>'
    body += '<text x="450" y="180" class="mono">left(i)   = 2i + 1</text>'
    body += '<text x="450" y="200" class="mono">right(i)  = 2i + 2</text>'
    body += '<text x="40" y="270" class="label">Min-heap invariant: parent ≤ both children.</text>'
    body += '<text x="40" y="290" class="label">push: append + sift-up    pop: swap root with last + sift-down</text>'
    body += '<text x="40" y="312" class="small">Both O(log n). Build heap from array: O(n) via heapify from bottom up.</text>'
    return svg(720, 330, body, "Heap — Tree &amp; Array Representation")

# ---------------- 10 Backtracking ----------------
def d10():
    body = ''
    # decision tree for subsets of [1,2,3]
    levels = [
        [(310, 60, "[]")],
        [(180,140,"[1]"),(440,140,"[]")],
        [(110,220,"[1,2]"),(250,220,"[1]"),(370,220,"[2]"),(510,220,"[]")],
        [(70,300,"[1,2,3]"),(140,300,"[1,2]"),(220,300,"[1,3]"),(290,300,"[1]"),
         (340,300,"[2,3]"),(410,300,"[2]"),(490,300,"[3]"),(560,300,"[]")],
    ]
    # edges
    parents = [[0,0],[0,0,1,1],[0,0,1,1,2,2,3,3]]
    for li in range(1,4):
        for ci,(x,y,_) in enumerate(levels[li]):
            px,py,_ = levels[li-1][parents[li-1][ci]]
            body += f'<line x1="{px}" y1="{py+12}" x2="{x}" y2="{y-12}" stroke="#888"/>'
    for li,row in enumerate(levels):
        for (x,y,v) in row:
            cls = "box4" if li==3 else "box2"
            body += f'<rect x="{x-32}" y="{y-14}" width="64" height="28" class="{cls}"/>'
            body += f'<text x="{x}" y="{y+5}" text-anchor="middle" class="mono">{v}</text>'
    body += '<text x="40" y="340" class="label">Decision tree: at each step, "include" (left) or "skip" (right).</text>'
    body += '<text x="40" y="360" class="small">Pruning = cut subtrees that can\'t lead to a valid answer (e.g. sum &gt; target).</text>'
    return svg(640, 380, body, "Backtracking — Decision Tree (subsets of [1,2,3])")

# ---------------- 11 Graphs ----------------
def d11():
    body = ''
    nodes = {"A":(120,100),"B":(260,80),"C":(400,100),"D":(180,200),"E":(340,200),"F":(260,300)}
    edges = [("A","B"),("A","D"),("B","C"),("B","D"),("C","E"),("D","E"),("D","F"),("E","F")]
    for a,b in edges:
        x1,y1 = nodes[a]; x2,y2 = nodes[b]
        body += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#666" stroke-width="1.4"/>'
    layer_color = {"A":"#1f6feb","B":"#1f6feb","D":"#1f6feb","C":"#1a7f37","E":"#1a7f37","F":"#b58900"}
    layer_label = {"A":"L0","B":"L1","D":"L1","C":"L2","E":"L2","F":"L3"}
    for k,(x,y) in nodes.items():
        body += f'<circle cx="{x}" cy="{y}" r="22" fill="white" stroke="{layer_color[k]}" stroke-width="2.4"/>'
        body += f'<text x="{x}" y="{y+5}" text-anchor="middle" class="mono">{k}</text>'
        body += f'<text x="{x}" y="{y-28}" text-anchor="middle" class="small">{layer_label[k]}</text>'
    body += '<text x="460" y="110" class="label">BFS from A:</text>'
    body += '<text x="460" y="130" class="mono">L0: A</text>'
    body += '<text x="460" y="150" class="mono">L1: B, D</text>'
    body += '<text x="460" y="170" class="mono">L2: C, E</text>'
    body += '<text x="460" y="190" class="mono">L3: F</text>'
    body += '<text x="460" y="225" class="label">DFS preorder:</text>'
    body += '<text x="460" y="245" class="mono">A B C E D F</text>'
    body += '<text x="40" y="360" class="small">BFS = queue, gives shortest path in unweighted graph. DFS = stack/recursion, gives topo &amp; SCC.</text>'
    return svg(660, 380, body, "Graph Traversal — BFS Layers vs DFS")

# ---------------- 12 DP 1D ----------------
def d12():
    body = '<text x="40" y="60" class="label">Climbing Stairs:  dp[i] = dp[i-1] + dp[i-2]</text>'
    vals = [1,1,2,3,5,8,13]
    for i,v in enumerate(vals):
        x = 60 + i*70
        body += f'<rect x="{x}" y="90" width="58" height="44" class="box2"/>'
        body += f'<text x="{x+29}" y="118" text-anchor="middle" class="mono">{v}</text>'
        body += f'<text x="{x+29}" y="85" text-anchor="middle" class="small">i={i}</text>'
    # arrows i-1 and i-2 into i=4
    body += '<path class="arrow2" d="M 248 134 C 260 180 320 180 332 134"/>'
    body += '<path class="arrow3" d="M 178 134 C 200 200 320 200 332 134"/>'
    body += '<text x="240" y="200" class="small">dp[2] + dp[3] = 2 + 3 = 5</text>'
    body += '<text x="40" y="245" class="label">Bottom-up: fill left → right. O(n) time, O(1) space (only last two).</text>'
    body += '<text x="40" y="280" class="label">Top-down: recursion + memo. Same complexity, easier to derive.</text>'
    body += '<text x="40" y="310" class="small">Key: recurrence + base cases + order of evaluation.</text>'
    return svg(620, 330, body, "1-D DP — Recurrence Chain")

# ---------------- 13 DP 2D ----------------
def d13():
    body = '<text x="40" y="60" class="label">Unique Paths grid:  dp[i][j] = dp[i-1][j] + dp[i][j-1]</text>'
    rows, cols = 4, 5
    cell_w = 56
    grid_vals = [[1]*cols] + [[1] + [0]*(cols-1) for _ in range(rows-1)]
    # compute
    for i in range(1,rows):
        for j in range(1,cols):
            grid_vals[i][j] = grid_vals[i-1][j] + grid_vals[i][j-1]
    for i in range(rows):
        for j in range(cols):
            x = 80 + j*cell_w; y = 90 + i*cell_w
            cls = "box3" if (i,j)==(rows-1,cols-1) else "box"
            body += f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_w}" class="{cls}"/>'
            body += f'<text x="{x+cell_w/2}" y="{y+cell_w/2+5}" text-anchor="middle" class="mono">{grid_vals[i][j]}</text>'
    # arrows showing dependency for one cell (2,3)
    tx,ty = 80+3*cell_w, 90+2*cell_w
    body += f'<path class="arrow2" d="M {tx} {ty-2} L {tx+cell_w/2} {ty+cell_w/2}"/>'  # from top
    body += f'<path class="arrow2" d="M {tx-2} {ty+cell_w/2} L {tx+cell_w/2} {ty+cell_w/2}"/>'  # from left
    body += '<text x="430" y="100" class="label">Each cell depends on:</text>'
    body += '<text x="430" y="125" class="mono">↑ top</text>'
    body += '<text x="430" y="145" class="mono">← left</text>'
    body += '<text x="430" y="180" class="label">Fill order:</text>'
    body += '<text x="430" y="200" class="mono">row by row, left to right</text>'
    body += '<text x="430" y="230" class="label">Answer = dp[m-1][n-1]</text>'
    body += '<text x="40" y="345" class="small">O(m·n) time. Space O(min(m,n)) using rolling row.</text>'
    return svg(720, 360, body, "2-D DP — Grid Recurrence")

# ---------------- 14 Greedy ----------------
def d14():
    body = '<text x="40" y="60" class="label">Activity selection: pick max non-overlapping intervals.</text>'
    # intervals on a number line
    intervals = [(1,4,True),(3,5,False),(0,6,False),(5,7,True),(3,8,False),(5,9,False),(6,10,True),(8,11,False),(8,12,True)]
    base_y = 90
    for i,(s,e,picked) in enumerate(intervals):
        y = base_y + i*22
        x1 = 60 + s*40; x2 = 60 + e*40
        col = "#1a7f37" if picked else "#bbb"
        body += f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{col}" stroke-width="6" stroke-linecap="round"/>'
        body += f'<text x="{x2+8}" y="{y+4}" class="small">[{s},{e}]{"  ✓" if picked else ""}</text>'
    # number line
    body += '<line x1="60" y1="290" x2="540" y2="290" stroke="#555"/>'
    for t in range(13):
        x = 60 + t*40
        body += f'<line x1="{x}" y1="285" x2="{x}" y2="295" stroke="#555"/>'
        body += f'<text x="{x}" y="308" text-anchor="middle" class="small">{t}</text>'
    body += '<text x="40" y="335" class="label">Greedy: sort by END time, pick if start ≥ last picked end.</text>'
    body += '<text x="40" y="355" class="small">Exchange argument: any optimal solution can swap its first activity for ours without losing count.</text>'
    return svg(640, 380, body, "Greedy — Activity Selection")

# ---------------- 15 Intervals ----------------
def d15():
    body = '<text x="40" y="60" class="label">Merge overlapping intervals (sort by start, sweep):</text>'
    raw = [(1,3),(2,6),(8,10),(15,18)]
    merged = [(1,6),(8,10),(15,18)]
    for i,(s,e) in enumerate(raw):
        y = 90+i*24
        body += f'<line x1="{60+s*22}" y1="{y}" x2="{60+e*22}" y2="{y}" stroke="#1f6feb" stroke-width="6"/>'
        body += f'<text x="{60+e*22+8}" y="{y+4}" class="small">[{s},{e}]</text>'
    body += '<text x="40" y="210" class="label">After merge:</text>'
    for i,(s,e) in enumerate(merged):
        y = 230+i*24
        body += f'<line x1="{60+s*22}" y1="{y}" x2="{60+e*22}" y2="{y}" stroke="#1a7f37" stroke-width="6"/>'
        body += f'<text x="{60+e*22+8}" y="{y+4}" class="small">[{s},{e}]</text>'
    body += '<line x1="60" y1="320" x2="540" y2="320" stroke="#555"/>'
    for t in range(0,21,2):
        x = 60 + t*22
        body += f'<line x1="{x}" y1="316" x2="{x}" y2="324" stroke="#555"/>'
        body += f'<text x="{x}" y="338" text-anchor="middle" class="small">{t}</text>'
    body += '<text x="40" y="365" class="small">If start ≤ last.end → merge (extend end). Else push new. O(n log n) for sort.</text>'
    return svg(620, 385, body, "Intervals — Sort &amp; Sweep")

# ---------------- 16 Bit Manipulation ----------------
def d16():
    body = '<text x="40" y="60" class="label">XOR trick: find the unique element in [2,3,2,4,4]</text>'
    # rows of bits
    nums = [2,3,2,4,4]
    body += '<text x="50" y="100" class="mono">num   bits</text>'
    cum = 0
    for i,n in enumerate(nums):
        y = 100 + (i+1)*24
        body += f'<text x="50" y="{y}" class="mono">{n:>3}   {n:03b}</text>'
        cum ^= n
    body += f'<line x1="40" y1="{100+ (len(nums)+1)*24 - 8}" x2="220" y2="{100+ (len(nums)+1)*24 - 8}" stroke="#444"/>'
    body += f'<text x="50" y="{100+ (len(nums)+1)*24 + 10}" class="mono">xor = {cum:03b}  → {cum}</text>'
    body += '<text x="280" y="120" class="label">Why it works:</text>'
    body += '<text x="280" y="145" class="mono">x ⊕ x = 0</text>'
    body += '<text x="280" y="165" class="mono">x ⊕ 0 = x</text>'
    body += '<text x="280" y="185" class="mono">commutative + associative</text>'
    body += '<text x="280" y="220" class="label">Useful tricks:</text>'
    body += '<text x="280" y="245" class="mono">x &amp; (x-1)   → clear lowest set bit</text>'
    body += '<text x="280" y="265" class="mono">x &amp; -x      → isolate lowest set bit</text>'
    body += '<text x="280" y="285" class="mono">x &gt;&gt; i &amp; 1 → read bit i</text>'
    body += '<text x="280" y="305" class="mono">x | (1&lt;&lt;i)  → set bit i</text>'
    body += '<text x="40" y="335" class="small">Pairs cancel; the lone one survives. O(n) time, O(1) space.</text>'
    return svg(620, 360, body, "Bit Manipulation — XOR Cancellation")

# ---------------- 17 Math & Geometry ----------------
def d17():
    body = '<text x="40" y="60" class="label">Rotate matrix 90° clockwise:  transpose then reverse rows</text>'
    # 3x3 grids: original, transposed, final
    grids = [
        [[1,2,3],[4,5,6],[7,8,9]],
        [[1,4,7],[2,5,8],[3,6,9]],
        [[7,4,1],[8,5,2],[9,6,3]],
    ]
    labels = ["original","transpose","reverse rows"]
    for gi,g in enumerate(grids):
        ox = 60 + gi*200
        body += f'<text x="{ox+70}" y="95" text-anchor="middle" class="label">{labels[gi]}</text>'
        for i,row in enumerate(g):
            for j,v in enumerate(row):
                x = ox + j*44; y = 110 + i*44
                body += f'<rect x="{x}" y="{y}" width="44" height="44" class="box"/>'
                body += f'<text x="{x+22}" y="{y+28}" text-anchor="middle" class="mono">{v}</text>'
        if gi < 2:
            ax = ox + 3*44 + 8
            body += f'<path class="arrow2" d="M {ax} 170 L {ax+30} 170"/>'
    body += '<text x="40" y="310" class="label">Transpose:   M[i][j] ↔ M[j][i]   (swap across diagonal)</text>'
    body += '<text x="40" y="332" class="label">Reverse rows: row[k] = reversed(row[k])</text>'
    body += '<text x="40" y="360" class="small">Counter-clockwise: transpose then reverse COLUMNS instead.</text>'
    return svg(680, 380, body, "Math &amp; Geometry — Rotate Matrix 90°")

# Master cheatsheet diagrams
def d_complexity():
    body = '<text x="40" y="60" class="label">Big-O growth (relative cost as n grows):</text>'
    # qualitative growth curves
    import math
    funcs = [
        ("O(1)",     lambda n: 1,           "#0a0"),
        ("O(log n)", lambda n: math.log2(max(n,1)+1)*4, "#080"),
        ("O(n)",     lambda n: n*0.3,       "#b58900"),
        ("O(n log n)", lambda n: n*0.3*math.log2(max(n,1)+1), "#e67700"),
        ("O(n²)",    lambda n: n*n*0.005,   "#d33"),
        ("O(2ⁿ)",    lambda n: 2**min(n*0.08, 8), "#900"),
    ]
    # plot from x=0 to 100
    ox, oy = 60, 350
    w, h = 480, 280
    body += f'<line x1="{ox}" y1="{oy}" x2="{ox+w}" y2="{oy}" stroke="#333"/>'
    body += f'<line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy-h}" stroke="#333"/>'
    body += f'<text x="{ox+w/2}" y="{oy+25}" text-anchor="middle" class="small">input size n →</text>'
    body += f'<text x="{ox-30}" y="{oy-h+8}" class="small">cost</text>'
    for name, fn, col in funcs:
        pts = []
        for n in range(0, 101, 2):
            y = min(fn(n), h-4)
            pts.append(f"{ox + n*w/100},{oy - y}")
        body += f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" stroke-width="2"/>'
    # legend
    for i,(name,_,col) in enumerate(funcs):
        ly = 90 + i*22
        body += f'<line x1="580" y1="{ly}" x2="610" y2="{ly}" stroke="{col}" stroke-width="3"/>'
        body += f'<text x="615" y="{ly+4}" class="mono">{name}</text>'
    return svg(720, 390, body, "Big-O Growth Curves")

def d_ds_choice():
    body = ''
    ops = ["lookup","insert","delete","ordered scan","min/max"]
    rows = [
        ("array",        ["O(n)","O(1) end","O(n)","O(n)","O(n)"]),
        ("hashmap",      ["O(1)","O(1)","O(1)","✗","✗"]),
        ("sorted array", ["O(log n)","O(n)","O(n)","O(n)","O(1)"]),
        ("BST balanced", ["O(log n)","O(log n)","O(log n)","O(n)","O(log n)"]),
        ("heap",         ["O(n)","O(log n)","O(log n)","✗","O(1)"]),
        ("trie (m=len)", ["O(m)","O(m)","O(m)","O(n)","✗"]),
    ]
    body += '<text x="180" y="65" class="label">Data structure × operation complexity</text>'
    cols = [(40,140)] + [(140 + i*100, 100) for i in range(5)]
    # header
    for i,op in enumerate(["DS"] + ops):
        x, w = cols[i]
        body += f'<rect x="{x}" y="80" width="{w}" height="32" class="box2"/>'
        body += f'<text x="{x+w/2}" y="100" text-anchor="middle" class="mono">{op}</text>'
    for r,(ds,vals) in enumerate(rows):
        y = 112 + r*32
        body += f'<rect x="{cols[0][0]}" y="{y}" width="{cols[0][1]}" height="32" class="box"/>'
        body += f'<text x="{cols[0][0]+cols[0][1]/2}" y="{y+20}" text-anchor="middle" class="mono">{ds}</text>'
        for ci,v in enumerate(vals):
            x,w = cols[ci+1]
            body += f'<rect x="{x}" y="{y}" width="{w}" height="32" class="box"/>'
            body += f'<text x="{x+w/2}" y="{y+20}" text-anchor="middle" class="mono">{v}</text>'
    return svg(750, 320, body, "Data-Structure Cheat Matrix")

# Write all
diagrams = {
    "01-arrays-hashing":    d01(),
    "02-two-pointers":      d02(),
    "03-sliding-window":    d03(),
    "04-binary-search":     d04(),
    "05-stack":             d05(),
    "06-linked-list":       d06(),
    "07-trees":             d07(),
    "08-tries":             d08(),
    "09-heap":              d09(),
    "10-backtracking":      d10(),
    "11-graphs":            d11(),
    "12-dp-1d":             d12(),
    "13-dp-2d":             d13(),
    "14-greedy":            d14(),
    "15-intervals":         d15(),
    "16-bit-manipulation":  d16(),
    "17-math-geometry":     d17(),
    "00-complexity-curves": d_complexity(),
    "00-ds-choice":         d_ds_choice(),
}

for name, content in diagrams.items():
    (OUT / f"{name}.svg").write_text(content, encoding="utf-8")
    print("wrote", name)

# Render to PNG via cairosvg
try:
    import cairosvg
    for name in diagrams:
        cairosvg.svg2png(url=str(OUT/f"{name}.svg"), write_to=str(OUT/f"{name}.png"), output_width=1200)
        print("png", name)
except Exception as e:
    print("PNG render failed:", e)
