"""Generate SVG diagrams for ML/DL cheatsheets. Adds to existing diagrams/ folder."""
from pathlib import Path
import math

OUT = Path(__file__).resolve().parent.parent / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)

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
  .box5  { fill: #fce7f3; stroke: #be185d; stroke-width: 1.5; }
  .arrow { stroke: #444; stroke-width: 1.6; fill: none; marker-end: url(#arr); }
  .arrow2{ stroke: #1f6feb; stroke-width: 2; fill: none; marker-end: url(#arrB); }
  .arrow3{ stroke: #d33; stroke-width: 2; fill: none; marker-end: url(#arrR); }
</style>
<defs>
  <marker id="arr"  viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#444"/></marker>
  <marker id="arrB" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#1f6feb"/></marker>
  <marker id="arrR" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#d33"/></marker>
</defs>
"""

def svg(w, h, body, title=None):
    t = f'<text x="{w//2}" y="22" text-anchor="middle" class="title">{title}</text>' if title else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{STYLE}{t}{body}</svg>'

# ---------- Gradient descent: loss surface + steps ----------
def d_gd():
    body = ''
    # contour ellipses
    cx, cy = 320, 200
    for r in [180, 145, 110, 75, 40]:
        body += f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r*0.6}" fill="none" stroke="#88a" stroke-width="1"/>'
    body += f'<circle cx="{cx}" cy="{cy}" r="6" fill="#1a7f37"/>'
    body += f'<text x="{cx+10}" y="{cy+4}" class="small">minimum</text>'
    # GD path
    pts = [(120,80),(170,120),(220,150),(265,175),(295,190),(312,198)]
    for i in range(len(pts)-1):
        x1,y1 = pts[i]; x2,y2 = pts[i+1]
        body += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#1f6feb" stroke-width="2"/>'
        body += f'<circle cx="{x1}" cy="{y1}" r="4" fill="#1f6feb"/>'
    body += f'<circle cx="{pts[-1][0]}" cy="{pts[-1][1]}" r="4" fill="#1f6feb"/>'
    body += f'<text x="100" y="70" class="mono">θ₀</text>'
    # SGD path (noisier)
    pts2 = [(540,90),(490,140),(510,160),(460,180),(440,210),(390,200),(360,205),(340,205)]
    for i in range(len(pts2)-1):
        x1,y1 = pts2[i]; x2,y2 = pts2[i+1]
        body += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#d33" stroke-width="2"/>'
        body += f'<circle cx="{x1}" cy="{y1}" r="3" fill="#d33"/>'
    body += '<text x="555" y="80" class="mono">θ₀ (SGD)</text>'
    body += '<text x="40" y="340" class="mono">θ ← θ − η · ∇L(θ)</text>'
    body += '<text x="40" y="362" class="small">Blue: batch GD — smooth path. Red: SGD — noisy but cheaper per step.</text>'
    body += '<text x="40" y="382" class="small">Learning rate η: too small → slow; too large → overshoot / divergence.</text>'
    return svg(680, 410, body, "Gradient Descent on a Loss Surface")

# ---------- Backprop computational graph ----------
def d_backprop():
    body = ''
    # forward arrows: x → linear → ReLU → linear → softmax → loss
    nodes = [("x",60,140),("Wx+b",170,140),("ReLU",290,140),("Wh+b",410,140),("softmax",530,140),("L",650,140)]
    for name,x,y in nodes:
        body += f'<rect x="{x-40}" y="{y-22}" width="80" height="44" class="box2"/>'
        body += f'<text x="{x}" y="{y+5}" text-anchor="middle" class="mono">{name}</text>'
    for i in range(len(nodes)-1):
        x1 = nodes[i][1]+40; x2 = nodes[i+1][1]-40
        body += f'<path class="arrow2" d="M {x1} {nodes[i][2]} L {x2} {nodes[i+1][2]}"/>'
    body += '<text x="350" y="100" text-anchor="middle" class="label">forward pass (compute activations)</text>'
    # backward arrows
    for i in range(len(nodes)-1, 0, -1):
        x1 = nodes[i][1]-40; x2 = nodes[i-1][1]+40
        body += f'<path class="arrow3" d="M {x1} {nodes[i][2]+50} L {x2} {nodes[i-1][2]+50}"/>'
    body += '<text x="350" y="240" text-anchor="middle" class="label">backward pass (chain rule: ∂L/∂param)</text>'
    body += '<text x="40" y="290" class="mono">∂L/∂Wᵢ = ∂L/∂yᵢ · ∂yᵢ/∂Wᵢ        (chain rule)</text>'
    body += '<text x="40" y="312" class="small">Each node stores its local jacobian; gradients flow right-to-left, multiplied along edges.</text>'
    body += '<text x="40" y="332" class="small">Computational cost of backward ≈ 2× forward (one mat-vec per edge).</text>'
    return svg(720, 360, body, "Backpropagation — Forward &amp; Reverse Pass")

# ---------- Optimizers (SGD vs Momentum vs Adam path) ----------
def d_opt():
    body = ''
    cx, cy = 320, 220
    for r in [180, 140, 100, 60]:
        body += f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r*0.55}" fill="none" stroke="#aab" stroke-width="1"/>'
    body += f'<circle cx="{cx}" cy="{cy}" r="5" fill="#1a7f37"/>'
    # SGD: oscillates across the valley
    sgd = [(80,290),(140,170),(170,280),(220,180),(255,270),(285,195),(305,250),(315,225)]
    # Momentum: smoother
    mom = [(80,90),(150,120),(220,160),(270,185),(300,205),(315,218)]
    # Adam: most direct
    ad = [(540,90),(470,135),(410,165),(370,190),(340,210),(322,220)]
    def draw(pts, col, lbl, lx, ly):
        out = ""
        for i in range(len(pts)-1):
            x1,y1 = pts[i]; x2,y2 = pts[i+1]
            out += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="2"/>'
            out += f'<circle cx="{x1}" cy="{y1}" r="3" fill="{col}"/>'
        out += f'<text x="{lx}" y="{ly}" class="mono" fill="{col}">{lbl}</text>'
        return out
    body += draw(sgd, "#d33",  "SGD",      60, 305)
    body += draw(mom, "#b58900","Momentum", 60, 80)
    body += draw(ad,  "#1f6feb","Adam",    555, 80)
    body += '<text x="40" y="360" class="mono">Momentum:  v ← βv + (1-β)∇L;  θ ← θ - η·v</text>'
    body += '<text x="40" y="380" class="mono">Adam:      m,v ← EMA(∇,∇²);    θ ← θ - η · m̂/(√v̂+ε)</text>'
    body += '<text x="40" y="402" class="small">Adam = momentum + adaptive per-parameter LR. Defaults: β₁=0.9, β₂=0.999, ε=1e-8.</text>'
    return svg(680, 430, body, "Optimizers — SGD vs Momentum vs Adam")

# ---------- Activations chart ----------
def d_act():
    body = ''
    # axes
    body += '<line x1="60" y1="200" x2="640" y2="200" stroke="#555"/>'
    body += '<line x1="350" y1="60" x2="350" y2="340" stroke="#555"/>'
    body += '<text x="635" y="220" class="small">x</text>'
    body += '<text x="358" y="60" class="small">y</text>'
    # ReLU: max(0,x)
    pts = []
    for x in range(-290, 291, 4):
        xs = 350 + x*0.9
        y = max(0, x*0.7)
        ys = 200 - y
        pts.append(f"{xs},{ys}")
    body += f'<polyline points="{" ".join(pts)}" stroke="#1f6feb" fill="none" stroke-width="2"/>'
    body += '<text x="500" y="100" class="mono" fill="#1f6feb">ReLU</text>'
    # sigmoid
    pts = []
    for x in range(-290, 291, 4):
        xs = 350 + x*0.9
        y = 1/(1+math.exp(-x/30))
        ys = 200 - y*100
        pts.append(f"{xs},{ys}")
    body += f'<polyline points="{" ".join(pts)}" stroke="#1a7f37" fill="none" stroke-width="2"/>'
    body += '<text x="500" y="130" class="mono" fill="#1a7f37">sigmoid</text>'
    # tanh
    pts = []
    for x in range(-290, 291, 4):
        xs = 350 + x*0.9
        y = math.tanh(x/40)
        ys = 200 - y*100
        pts.append(f"{xs},{ys}")
    body += f'<polyline points="{" ".join(pts)}" stroke="#d33" fill="none" stroke-width="2"/>'
    body += '<text x="500" y="160" class="mono" fill="#d33">tanh</text>'
    # GeLU (approx)
    pts = []
    for x in range(-290, 291, 4):
        xs = 350 + x*0.9
        v = x/30
        y = 0.5 * v * (1 + math.tanh(math.sqrt(2/math.pi)*(v + 0.044715*v**3))) * 30 * 0.7
        ys = 200 - y
        pts.append(f"{xs},{ys}")
    body += f'<polyline points="{" ".join(pts)}" stroke="#b58900" fill="none" stroke-width="2"/>'
    body += '<text x="500" y="190" class="mono" fill="#b58900">GeLU</text>'
    body += '<text x="60" y="370" class="small">ReLU: cheap, no vanishing. Dying ReLU on negative input.</text>'
    body += '<text x="60" y="388" class="small">sigmoid/tanh: vanishing gradients in deep nets.</text>'
    body += '<text x="60" y="406" class="small">GeLU: smooth ReLU; default in transformers (BERT, GPT-2).</text>'
    return svg(680, 430, body, "Activation Functions")

# ---------- Attention diagram ----------
def d_attention():
    body = ''
    body += '<text x="40" y="55" class="label">Self-attention:  softmax(QKᵀ / √d) · V</text>'
    # tokens
    toks = ["The","cat","sat","on","mat"]
    for i,t in enumerate(toks):
        x = 60 + i*100
        body += f'<rect x="{x}" y="80" width="80" height="40" class="box"/>'
        body += f'<text x="{x+40}" y="105" text-anchor="middle" class="mono">{t}</text>'
    # Q,K,V
    for i,letter in enumerate("QKV"):
        for j,t in enumerate(toks):
            x = 60 + j*100; y = 160 + i*60
            cls = ["box2","box3","box4"][i]
            body += f'<rect x="{x}" y="{y}" width="80" height="36" class="{cls}"/>'
            body += f'<text x="{x+40}" y="{y+22}" text-anchor="middle" class="mono">{letter}_{j+1}</text>'
            # link from token
            if i == 0:
                body += f'<line x1="{x+40}" y1="120" x2="{x+40}" y2="{y}" stroke="#aaa" stroke-dasharray="2 2"/>'
    body += '<text x="20" y="180" class="mono">Q:</text>'
    body += '<text x="20" y="240" class="mono">K:</text>'
    body += '<text x="20" y="300" class="mono">V:</text>'
    body += '<text x="40" y="380" class="mono">attn_ij = softmax_j ( Q_i · K_j / √d )</text>'
    body += '<text x="40" y="400" class="small">"Each token mixes information from all others, weighted by Q·K similarity."</text>'
    body += '<text x="40" y="418" class="small">Multi-head: H independent (Q,K,V) projections, concat outputs → linear.</text>'
    return svg(680, 440, body, "Scaled Dot-Product Attention")

# ---------- Embeddings (word vectors in 2D) ----------
def d_embed():
    body = ''
    # axes
    body += '<line x1="60" y1="320" x2="640" y2="320" stroke="#555"/>'
    body += '<line x1="60" y1="60" x2="60" y2="320" stroke="#555"/>'
    body += '<text x="635" y="338" class="small">dim 1 (PCA)</text>'
    body += '<text x="68" y="55" class="small">dim 2</text>'
    pts = {
        "king":   (480,100), "queen": (510,120),
        "man":    (440,170), "woman": (470,190),
        "Paris":  (160,260), "France":(180,280),
        "Tokyo":  (140,210), "Japan": (160,230),
        "cat":    (260,140), "dog":   (280,160), "kitten":(245,155),"puppy":(275,180),
        "apple":  (340,260), "banana":(360,275), "orange":(355,250),
    }
    for word,(x,y) in pts.items():
        body += f'<circle cx="{x}" cy="{y}" r="4" fill="#1f6feb"/>'
        body += f'<text x="{x+6}" y="{y+4}" class="mono">{word}</text>'
    # analogy arrows
    body += '<path class="arrow2" d="M 440 170 L 480 100"/>'
    body += '<path class="arrow2" d="M 470 190 L 510 120"/>'
    body += '<text x="395" y="135" class="small" fill="#1f6feb">king − man = queen − woman</text>'
    body += '<text x="40" y="370" class="small">Similar meanings cluster. Linear relationships encode analogies (Mikolov 2013).</text>'
    return svg(680, 400, body, "Word Embeddings — Clusters &amp; Analogies")

# ---------- ML algos decision tree ----------
def d_ml_tree():
    body = ''
    boxes = [
        ("data", 320, 60, "box2"),
        ("labels?", 320, 120, "box3"),
        ("supervised", 180, 190, "box2"),
        ("unsupervised", 460, 190, "box2"),
        ("classification", 80, 260, "box4"),
        ("regression", 280, 260, "box4"),
        ("cluster", 420, 260, "box4"),
        ("dim. reduction", 560, 260, "box4"),
        ("linear sep?", 80, 330, "box3"),
        ("# features", 280, 330, "box3"),
        ("LogReg / SVM (linear)", 60, 400, "box"),
        ("RF / XGBoost", 180, 400, "box"),
        ("linear regression", 250, 400, "box"),
        ("RF/XGB regressor", 380, 400, "box"),
        ("KMeans / DBSCAN", 420, 330, "box"),
        ("PCA / t-SNE / UMAP", 560, 330, "box"),
    ]
    for (txt,x,y,cls) in boxes:
        w = max(90, len(txt)*7 + 12)
        body += f'<rect x="{x - w/2}" y="{y-18}" width="{w}" height="32" class="{cls}"/>'
        body += f'<text x="{x}" y="{y+5}" text-anchor="middle" class="mono">{txt}</text>'
    edges = [(0,1),(1,2),(1,3),(2,4),(2,5),(3,6),(3,7),(4,8),(5,9),(8,10),(8,11),(9,12),(9,13),(6,14),(7,15)]
    for a,b in edges:
        x1,y1 = boxes[a][1], boxes[a][2]+16
        x2,y2 = boxes[b][1], boxes[b][2]-18
        body += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#888" stroke-width="1.4"/>'
    return svg(720, 440, body, "ML Algorithm Selection")

# ---------- Bias-variance ----------
def d_biasvar():
    body = ''
    # axes
    body += '<line x1="80" y1="320" x2="640" y2="320" stroke="#333"/>'
    body += '<line x1="80" y1="320" x2="80" y2="60" stroke="#333"/>'
    body += '<text x="635" y="340" class="small">model complexity →</text>'
    body += '<text x="40" y="65" class="small">error</text>'
    # train (decreasing)
    pts = []
    for cx in range(0,101,2):
        x = 80 + cx*5.6
        y = 320 - 240*math.exp(-cx/40)
        pts.append(f"{x},{y}")
    body += f'<polyline points="{" ".join(pts)}" stroke="#1f6feb" fill="none" stroke-width="2"/>'
    body += '<text x="600" y="280" class="mono" fill="#1f6feb">train</text>'
    # test (U-shape)
    pts = []
    for cx in range(0,101,2):
        x = 80 + cx*5.6
        y = 320 - 220*math.exp(-cx/35) + 0.05*(cx-40)**2
        pts.append(f"{x},{y}")
    body += f'<polyline points="{" ".join(pts)}" stroke="#d33" fill="none" stroke-width="2"/>'
    body += '<text x="600" y="140" class="mono" fill="#d33">test</text>'
    # sweet spot
    body += '<line x1="305" y1="100" x2="305" y2="320" stroke="#1a7f37" stroke-dasharray="4 4"/>'
    body += '<text x="310" y="95" class="mono" fill="#1a7f37">sweet spot</text>'
    # labels under regions
    body += '<text x="130" y="370" class="label">underfitting</text>'
    body += '<text x="130" y="388" class="small">high bias, low variance</text>'
    body += '<text x="490" y="370" class="label">overfitting</text>'
    body += '<text x="490" y="388" class="small">low bias, high variance</text>'
    return svg(720, 410, body, "Bias-Variance Tradeoff")

# ---------- RL MDP ----------
def d_rl():
    body = ''
    # agent / environment loop
    body += '<rect x="80" y="100" width="180" height="80" class="box2"/>'
    body += '<text x="170" y="145" text-anchor="middle" class="label">Agent</text>'
    body += '<text x="170" y="165" text-anchor="middle" class="small">policy π(a|s)</text>'
    body += '<rect x="440" y="100" width="180" height="80" class="box4"/>'
    body += '<text x="530" y="145" text-anchor="middle" class="label">Environment</text>'
    body += '<text x="530" y="165" text-anchor="middle" class="small">P(s\'|s,a), R(s,a)</text>'
    body += '<path class="arrow2" d="M 260 130 L 440 130"/>'
    body += '<text x="350" y="120" text-anchor="middle" class="mono">action a_t</text>'
    body += '<path class="arrow3" d="M 440 155 L 260 155"/>'
    body += '<text x="350" y="180" text-anchor="middle" class="mono">state s_{t+1}, reward r_{t+1}</text>'
    body += '<text x="40" y="240" class="mono">Goal: maximise E[Σ γᵗ rₜ]</text>'
    body += '<text x="40" y="265" class="mono">Bellman:  V(s) = max_a [R(s,a) + γ Σ P(s\'|s,a) V(s\')]</text>'
    body += '<text x="40" y="295" class="mono">Q-learning: Q(s,a) ← Q(s,a) + α [r + γ max_a\' Q(s\',a\') − Q(s,a)]</text>'
    body += '<text x="40" y="330" class="small">Model-free TD update; off-policy because we use max over next actions, not the policy.</text>'
    return svg(720, 360, body, "Reinforcement Learning — Agent-Environment Loop")

# ---------- Confusion matrix + metrics ----------
def d_metrics():
    body = ''
    # 2x2 matrix
    cells = [
        (190, 100, 140, 60, "TP",  "box4"),
        (350, 100, 140, 60, "FN",  "box3"),
        (190, 170, 140, 60, "FP",  "box3"),
        (350, 170, 140, 60, "TN",  "box4"),
    ]
    for (x,y,w,h,t,c) in cells:
        body += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" class="{c}"/>'
        body += f'<text x="{x+w/2}" y="{y+h/2+5}" text-anchor="middle" class="mono">{t}</text>'
    body += '<text x="260" y="92" text-anchor="middle" class="small">Pred = 1</text>'
    body += '<text x="420" y="92" text-anchor="middle" class="small">Pred = 0</text>'
    body += '<text x="185" y="135" text-anchor="end" class="small">Actual=1</text>'
    body += '<text x="185" y="205" text-anchor="end" class="small">Actual=0</text>'
    body += '<text x="40" y="270" class="mono">Precision = TP / (TP + FP)         "of those I called positive, how many are?"</text>'
    body += '<text x="40" y="290" class="mono">Recall    = TP / (TP + FN)         "of actual positives, how many did I catch?"</text>'
    body += '<text x="40" y="310" class="mono">F1        = 2·P·R / (P + R)        harmonic mean — balances both</text>'
    body += '<text x="40" y="330" class="mono">Accuracy  = (TP + TN) / total      misleading on imbalanced data</text>'
    body += '<text x="40" y="350" class="mono">ROC-AUC   = P(score(pos) &gt; score(neg))  threshold-independent</text>'
    return svg(720, 380, body, "Classification Metrics — Confusion Matrix")

# ---------- Transformer encoder block (compact) ----------
def d_transformer():
    body = ''
    # stacked blocks
    rects = [
        ("Input embedding + positional",  340, 60,  300, 36, "box"),
        ("Multi-head self-attention",     340, 130, 300, 40, "box2"),
        ("Add & LayerNorm",               340, 180, 300, 28, "box3"),
        ("Feed-Forward (MLP)",            340, 230, 300, 40, "box2"),
        ("Add & LayerNorm",               340, 280, 300, 28, "box3"),
    ]
    for (t,cx,y,w,h,c) in rects:
        body += f'<rect x="{cx-w/2}" y="{y}" width="{w}" height="{h}" class="{c}"/>'
        body += f'<text x="{cx}" y="{y+h/2+5}" text-anchor="middle" class="mono">{t}</text>'
        if y > 60:
            body += f'<path class="arrow" d="M {cx} {y-2} L {cx} {y-12}"/>'
    # residual arrows
    body += '<path class="arrow2" d="M 200 145 C 160 145 160 205 200 205"/>'
    body += '<text x="135" y="180" class="small" fill="#1f6feb">residual</text>'
    body += '<path class="arrow2" d="M 200 245 C 160 245 160 305 200 305"/>'
    body += '<text x="135" y="280" class="small" fill="#1f6feb">residual</text>'
    body += '<text x="40" y="360" class="small">Repeated N× (12 in BERT-base, 96 in GPT-3). Decoder adds masked attention.</text>'
    return svg(720, 390, body, "Transformer Encoder Block")

# ---------- LSTM cell internals ----------
def d_lstm():
    body = ''
    # cell box
    body += '<rect x="80" y="80" width="540" height="220" class="box" fill="#fafbff"/>'
    # gates
    gates = [
        ("forget f",   160, 130, "box3"),
        ("input  i",   240, 130, "box3"),
        ("candidate g",320, 130, "box3"),
        ("output o",   400, 130, "box3"),
    ]
    for t,x,y,c in gates:
        body += f'<rect x="{x-40}" y="{y-18}" width="80" height="36" class="{c}"/>'
        body += f'<text x="{x}" y="{y+5}" text-anchor="middle" class="mono">{t}</text>'
    # cell state
    body += '<rect x="80" y="210" width="540" height="36" fill="#d4edda" stroke="#1a7f37"/>'
    body += '<text x="350" y="232" text-anchor="middle" class="mono">cell state cₜ  = fₜ ⊙ cₜ₋₁ + iₜ ⊙ gₜ</text>'
    body += '<text x="350" y="280" text-anchor="middle" class="mono">hₜ = oₜ ⊙ tanh(cₜ)</text>'
    # inputs
    body += '<text x="40" y="135" class="mono">[xₜ, hₜ₋₁]</text>'
    body += '<path class="arrow" d="M 110 135 L 120 135"/>'
    body += '<text x="40" y="350" class="small">Gates use sigmoid; candidate uses tanh. Cell state is the long-term highway.</text>'
    body += '<text x="40" y="370" class="small">Solves vanishing-gradient by additive update through cₜ instead of multiplicative.</text>'
    return svg(720, 400, body, "LSTM Cell — Gates &amp; Cell State")

# ---------- Regularization ----------
def d_reg():
    body = ''
    # left: dropout
    body += '<text x="180" y="55" text-anchor="middle" class="label">Dropout (training)</text>'
    nodes = [(80,130),(110,130),(140,130),(170,130),(200,130),(230,130),(260,130),(290,130)]
    drop = {1,3,6}
    for i,(x,y) in enumerate(nodes):
        cls = "box" if i in drop else "box2"
        op = "0.25" if i in drop else "1"
        body += f'<circle cx="{x}" cy="{y}" r="9" class="{cls}" opacity="{op}"/>'
    body += '<text x="180" y="170" text-anchor="middle" class="small">randomly zero ~p of activations</text>'
    # right: L1/L2 contours
    body += '<text x="510" y="55" text-anchor="middle" class="label">L1 vs L2 regularization</text>'
    # L2 = circle
    body += '<circle cx="510" cy="160" r="55" fill="none" stroke="#1f6feb" stroke-width="2"/>'
    # L1 = diamond
    body += '<polygon points="510,100 565,160 510,220 455,160" fill="none" stroke="#d33" stroke-width="2"/>'
    # contours of loss
    body += '<ellipse cx="555" cy="120" rx="40" ry="25" fill="none" stroke="#888"/>'
    body += '<ellipse cx="555" cy="120" rx="60" ry="38" fill="none" stroke="#888"/>'
    body += '<circle cx="510" cy="105" r="3" fill="#d33"/>'
    body += '<text x="515" y="105" class="small" fill="#d33">L1 hits axis → sparsity</text>'
    body += '<text x="40" y="280" class="mono">Dropout: drop nodes with prob p during training, scale by 1/(1-p) at test.</text>'
    body += '<text x="40" y="302" class="mono">L2:  loss += λ·||w||²    smooth shrinkage of all weights</text>'
    body += '<text x="40" y="322" class="mono">L1:  loss += λ·||w||₁    induces SPARSE solutions (many w=0)</text>'
    body += '<text x="40" y="350" class="small">Other: early stopping, data augmentation, batch norm (mild reg.), label smoothing.</text>'
    return svg(720, 380, body, "Regularization Techniques")

# ---------- ResNet skip connection: already exists. Skip. ----------

diagrams = {
    "05-gradient-descent":   d_gd(),
    "06-backprop":           d_backprop(),
    "07-optimizers":         d_opt(),
    "08-activations":        d_act(),
    "09-attention":          d_attention(),
    "10-embeddings":         d_embed(),
    "11-ml-tree":            d_ml_tree(),
    "12-bias-variance":      d_biasvar(),
    "13-rl-mdp":             d_rl(),
    "14-confusion-metrics":  d_metrics(),
    "15-transformer-block":  d_transformer(),
    "16-lstm-cell":          d_lstm(),
    "17-regularization":     d_reg(),
}

for name, body in diagrams.items():
    (OUT / f"{name}.svg").write_text(body, encoding="utf-8")
    print("wrote", name)
