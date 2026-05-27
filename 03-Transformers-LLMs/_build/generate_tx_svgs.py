"""Generate additional SVG diagrams for Transformers/LLMs cheatsheets."""
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

# ---------- BPE merge process ----------
def d_bpe():
    body = ''
    rounds = [
        ("init", ["l","o","w","e","s","t"]),
        ("merge e+s → es", ["l","o","w","es","t"]),
        ("merge es+t → est", ["l","o","w","est"]),
        ("merge l+o → lo", ["lo","w","est"]),
        ("merge lo+w → low", ["low","est"]),
    ]
    for r,(label, toks) in enumerate(rounds):
        y = 70 + r*52
        body += f'<text x="20" y="{y+20}" class="small">{label}</text>'
        x = 220
        for t in toks:
            w = max(40, len(t)*11+10)
            body += f'<rect x="{x}" y="{y}" width="{w}" height="36" class="box2"/>'
            body += f'<text x="{x+w/2}" y="{y+22}" text-anchor="middle" class="mono">{t}</text>'
            x += w + 6
    body += '<text x="20" y="370" class="label">BPE iteratively merges the most-frequent adjacent pair into a new token.</text>'
    body += '<text x="20" y="388" class="small">Stops at target vocab size (e.g. 32k for LLaMA, 50k for GPT-2, 100k for GPT-4).</text>'
    body += '<text x="20" y="406" class="small">Rare words become several subwords; common words become one token.</text>'
    return svg(720, 430, body, "Byte-Pair Encoding — Merge Trace")

# ---------- Scaling laws (log-log) ----------
def d_scaling():
    body = ''
    body += '<line x1="80" y1="320" x2="640" y2="320" stroke="#333"/>'
    body += '<line x1="80" y1="60" x2="80" y2="320" stroke="#333"/>'
    body += '<text x="635" y="340" class="small">compute / data / params (log)</text>'
    body += '<text x="65" y="60" text-anchor="end" class="small">loss (log)</text>'
    # three power-law lines (parallel descending)
    lines = [
        ("params N",  90,  100, 0.55, "#1f6feb"),
        ("data D",    90,  140, 0.45, "#1a7f37"),
        ("compute C", 90,  180, 0.50, "#d33"),
    ]
    for label, x0, y0, slope, col in lines:
        x1 = 640; y1 = y0 + (x1-x0)*slope*0.45
        body += f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="{col}" stroke-width="2.5"/>'
        body += f'<text x="650" y="{y1+4}" class="mono" fill="{col}">{label}</text>'
    body += '<text x="40" y="360" class="mono">L(N,D,C) ≈ A·N^(-α) + B·D^(-β) + C·C^(-γ)   (irreducible floor + power-laws)</text>'
    body += '<text x="40" y="382" class="mono">Chinchilla (Hoffmann 2022): optimal D ≈ 20·N tokens for given compute</text>'
    body += '<text x="40" y="402" class="small">Implication: many earlier models were UNDER-trained (e.g. GPT-3 trained on far &lt;20× tokens).</text>'
    return svg(720, 430, body, "LLM Scaling Laws")

# ---------- MoE routing ----------
def d_moe():
    body = ''
    body += '<rect x="280" y="60" width="160" height="50" class="box2"/>'
    body += '<text x="360" y="92" text-anchor="middle" class="mono">router (gate)</text>'
    body += '<text x="40" y="92" class="label">token →</text>'
    body += '<path class="arrow" d="M 100 85 L 280 85"/>'
    # experts
    experts = ["E1","E2","E3","E4","E5","E6","E7","E8"]
    for i,e in enumerate(experts):
        x = 80 + i*72
        active = i in (2, 5)
        cls = "box4" if active else "box"
        body += f'<rect x="{x}" y="180" width="60" height="46" class="{cls}"/>'
        body += f'<text x="{x+30}" y="207" text-anchor="middle" class="mono">{e}</text>'
        col = "#1f6feb" if active else "#bbb"
        body += f'<line x1="360" y1="110" x2="{x+30}" y2="180" stroke="{col}" stroke-width="{2 if active else 0.8}"/>'
        if active:
            body += f'<text x="{x+30}" y="170" text-anchor="middle" class="small" fill="#1f6feb">0.6</text>'
    body += '<rect x="280" y="270" width="160" height="50" class="box3"/>'
    body += '<text x="360" y="302" text-anchor="middle" class="mono">weighted sum</text>'
    body += '<path class="arrow" d="M 230 226 L 320 270"/>'
    body += '<path class="arrow" d="M 500 226 L 400 270"/>'
    body += '<text x="40" y="370" class="mono">Top-k routing: token sent only to top-k experts (k=1 or 2).</text>'
    body += '<text x="40" y="390" class="small">Total params huge but per-token FLOPs constant. Aux load-balancing loss prevents expert collapse.</text>'
    body += '<text x="40" y="410" class="small">Mixtral 8×7B, GPT-4 (rumoured), Switch-Transformer, DeepSeek-MoE.</text>'
    return svg(740, 440, body, "Mixture of Experts (MoE) — Sparse Routing")

# ---------- BERT vs GPT vs T5 ----------
def d_bert_gpt_t5():
    body = ''
    # three columns
    cols = [
        ("BERT (encoder)",    80, "box2", ["bidirectional attn","masked LM + NSP","[CLS] / [SEP]","Classify / NER / QA"]),
        ("GPT (decoder)",    280, "box3", ["causal attn","next-token LM","auto-regressive","Generate / chat"]),
        ("T5 (enc-dec)",     480, "box4", ["enc bidi, dec causal","text-to-text","span corruption","Translate / summarise"]),
    ]
    for label, x, cls, rows in cols:
        body += f'<rect x="{x}" y="60" width="180" height="46" class="{cls}"/>'
        body += f'<text x="{x+90}" y="88" text-anchor="middle" class="mono">{label}</text>'
        for i,r in enumerate(rows):
            y = 120 + i*38
            body += f'<rect x="{x}" y="{y}" width="180" height="32" class="box"/>'
            body += f'<text x="{x+10}" y="{y+20}" class="mono">{r}</text>'
    body += '<text x="40" y="305" class="mono">All three use the same Transformer block; differences = attention mask + objective + architecture.</text>'
    body += '<text x="40" y="330" class="small">2024+: decoder-only dominates (LLaMA, GPT, Claude, Mistral). Encoder-only retains a niche in retrieval/classification.</text>'
    return svg(720, 360, body, "Transformer Families — BERT vs GPT vs T5")

# ---------- Sampling temperature / top-k / top-p ----------
def d_sampling():
    body = ''
    # bar chart of probs
    words = ["cat","dog","bird","car","tree","sun","run","blue","jump","leaf"]
    probs = [0.42, 0.21, 0.12, 0.09, 0.05, 0.04, 0.03, 0.02, 0.015, 0.005]
    body += '<text x="20" y="55" class="label">P(next token):</text>'
    x0 = 40
    for i,(w,p) in enumerate(zip(words, probs)):
        x = x0 + i*60; h = int(p*400)
        in_topk = i < 3
        in_topp = i < 3
        cls = "box4" if in_topk else "box"
        body += f'<rect x="{x}" y="{260-h}" width="44" height="{h}" class="{cls}"/>'
        body += f'<text x="{x+22}" y="278" text-anchor="middle" class="mono">{w}</text>'
        body += f'<text x="{x+22}" y="295" text-anchor="middle" class="small">{p}</text>'
    # cutoff lines
    body += '<line x1="220" y1="60" x2="220" y2="260" stroke="#1a7f37" stroke-dasharray="4 3"/>'
    body += '<text x="225" y="80" class="small" fill="#1a7f37">top-k=3 cutoff</text>'
    body += '<text x="40" y="330" class="mono">Temperature T:  P\'(x) ∝ P(x)^(1/T)         T→0 = greedy, T=1 = unchanged, T&gt;1 = flatter</text>'
    body += '<text x="40" y="352" class="mono">Top-k: keep k highest then renormalise</text>'
    body += '<text x="40" y="372" class="mono">Top-p (nucleus): keep smallest set with cumulative prob ≥ p</text>'
    body += '<text x="40" y="395" class="small">Defaults for chat: T=0.7, top-p=0.9. Code-gen: T=0.2 (more deterministic).</text>'
    return svg(720, 420, body, "LLM Sampling — Temperature, Top-k, Top-p")

# ---------- Quantization ----------
def d_quant():
    body = ''
    # number line with FP16 vs INT8 vs INT4
    body += '<text x="40" y="60" class="label">FP16 (16 bits, ~65k values)</text>'
    body += '<line x1="40" y1="90" x2="680" y2="90" stroke="#1f6feb" stroke-width="2"/>'
    for i in range(33):
        x = 40 + i*20
        body += f'<line x1="{x}" y1="86" x2="{x}" y2="94" stroke="#1f6feb"/>'
    body += '<text x="40" y="140" class="label">INT8 (256 values)</text>'
    body += '<line x1="40" y1="170" x2="680" y2="170" stroke="#1a7f37" stroke-width="2"/>'
    for i in range(17):
        x = 40 + i*40
        body += f'<line x1="{x}" y1="164" x2="{x}" y2="176" stroke="#1a7f37"/>'
    body += '<text x="40" y="220" class="label">INT4 (16 values)</text>'
    body += '<line x1="40" y1="250" x2="680" y2="250" stroke="#d33" stroke-width="2"/>'
    for i in range(9):
        x = 40 + i*80
        body += f'<line x1="{x}" y1="244" x2="{x}" y2="256" stroke="#d33"/>'
    body += '<text x="40" y="310" class="mono">Memory:  FP16 = 2N bytes;  INT8 = N bytes;  INT4 = N/2 bytes</text>'
    body += '<text x="40" y="332" class="mono">Quantize:  q = round((x − zero_point) / scale)  with calibration on activations</text>'
    body += '<text x="40" y="354" class="small">GPTQ, AWQ, GGUF for INT4. Latency↓, memory↓; small quality drop.</text>'
    body += '<text x="40" y="374" class="small">LLaMA-7B: FP16 = 14 GB, INT4 = ~3.5 GB → runs on consumer GPU.</text>'
    return svg(720, 400, body, "Quantization — FP16 → INT8 → INT4")

# ---------- LoRA detail ----------
def d_lora():
    body = ''
    # original W matrix (frozen) + A·B low rank
    body += '<rect x="80" y="80" width="180" height="180" class="box" opacity="0.7"/>'
    body += '<text x="170" y="180" text-anchor="middle" class="mono">W (frozen)</text>'
    body += '<text x="170" y="200" text-anchor="middle" class="small">d × d</text>'
    body += '<text x="280" y="180" text-anchor="middle" class="mono">+</text>'
    body += '<rect x="320" y="80" width="60" height="180" class="box4"/>'
    body += '<text x="350" y="180" text-anchor="middle" class="mono">A</text>'
    body += '<text x="350" y="200" text-anchor="middle" class="small">d × r</text>'
    body += '<rect x="400" y="160" width="180" height="40" class="box4"/>'
    body += '<text x="490" y="185" text-anchor="middle" class="mono">B</text>'
    body += '<text x="490" y="220" text-anchor="middle" class="small">r × d</text>'
    body += '<text x="610" y="180" text-anchor="middle" class="mono">≈ W\'</text>'
    body += '<text x="40" y="300" class="mono">Effective update:  W\' = W + ΔW = W + AB    where rank(AB) ≤ r ≪ d</text>'
    body += '<text x="40" y="325" class="mono">Trainable params drop from d² to 2·d·r  →  ~1% of full fine-tune</text>'
    body += '<text x="40" y="350" class="small">Typical r=8-64. QLoRA = LoRA on 4-bit quantised base model — 65B in 48GB.</text>'
    body += '<text x="40" y="370" class="small">Multiple adapters can be hot-swapped at inference (one base + N small adapters).</text>'
    return svg(720, 400, body, "LoRA — Low-Rank Adaptation")

# ---------- Positional encodings ----------
def d_pos():
    body = ''
    body += '<text x="40" y="55" class="label">Sinusoidal (original Transformer)</text>'
    # heatmap-like sin waves
    for pos in range(40):
        for d in range(20):
            v = math.sin(pos / (10000 ** (d/20))) if d % 2 == 0 else math.cos(pos / (10000 ** ((d-1)/20)))
            color_val = int(128 + v*100)
            color_val = max(0, min(255, color_val))
            body += f'<rect x="{40+pos*15}" y="{70+d*10}" width="15" height="10" fill="rgb({color_val},{color_val},255)"/>'
    body += '<text x="40" y="290" class="mono">PE(pos, 2i)   = sin(pos / 10000^(2i/d))</text>'
    body += '<text x="40" y="310" class="mono">PE(pos, 2i+1) = cos(pos / 10000^(2i/d))</text>'
    body += '<text x="40" y="340" class="label">Modern alternatives:</text>'
    body += '<text x="60" y="362" class="mono">• Learned positional embeddings (BERT, GPT-2)</text>'
    body += '<text x="60" y="382" class="mono">• ALiBi: linear bias on attention scores (no PE vector)</text>'
    body += '<text x="60" y="402" class="mono">• RoPE: rotate Q,K by angle ∝ position (LLaMA, GPT-NeoX)</text>'
    body += '<text x="40" y="430" class="small">RoPE generalises to longer contexts than seen in training (with NTK / YaRN tweaks).</text>'
    return svg(720, 460, body, "Positional Encodings")

# ---------- Inference pipeline (prefill vs decode) ----------
def d_infer():
    body = ''
    # prefill phase (parallel)
    body += '<rect x="60" y="70" width="280" height="80" class="box2"/>'
    body += '<text x="200" y="100" text-anchor="middle" class="label">Prefill</text>'
    body += '<text x="200" y="125" text-anchor="middle" class="small">process all N input tokens in parallel</text>'
    body += '<text x="200" y="142" text-anchor="middle" class="mono">O(N²) attention</text>'
    # arrow
    body += '<path class="arrow" d="M 340 110 L 400 110"/>'
    body += '<text x="370" y="100" text-anchor="middle" class="small">KV cache</text>'
    # decode phase (sequential)
    body += '<rect x="400" y="70" width="280" height="80" class="box3"/>'
    body += '<text x="540" y="100" text-anchor="middle" class="label">Decode</text>'
    body += '<text x="540" y="125" text-anchor="middle" class="small">one token at a time, reusing KV cache</text>'
    body += '<text x="540" y="142" text-anchor="middle" class="mono">O(N) per new token</text>'
    # memory bottleneck
    body += '<text x="40" y="195" class="label">KV cache memory: 2 · n_layers · n_heads · head_dim · seq_len · batch · dtype</text>'
    body += '<text x="60" y="215" class="mono">LLaMA-7B, ctx=4k, bf16:  ~2 GB per request</text>'
    body += '<text x="60" y="235" class="mono">LLaMA-70B, ctx=32k, bf16:  ~40 GB per request</text>'
    body += '<text x="40" y="270" class="label">Optimisations:</text>'
    body += '<text x="60" y="290" class="mono">• PagedAttention (vLLM) — virtual memory for KV</text>'
    body += '<text x="60" y="310" class="mono">• Grouped Query Attention — fewer K,V heads</text>'
    body += '<text x="60" y="330" class="mono">• FlashAttention — fused kernels, ~2× speedup</text>'
    body += '<text x="60" y="350" class="mono">• Speculative decoding — small draft model</text>'
    return svg(720, 380, body, "LLM Inference — Prefill vs Decode")

# ---------- RAG architecture (extended) ----------
def d_rag_arch():
    body = ''
    # boxes flow: query → embed → retrieve → rerank → prompt → LLM → answer
    stages = [
        ("user query",         80, "box"),
        ("embed query",       210, "box2"),
        ("vector search\n(HNSW)", 340, "box4"),
        ("rerank\n(cross-enc)", 470, "box3"),
        ("LLM prompt\n+ retrieved", 600, "box5"),
    ]
    for label, x, cls in stages:
        body += f'<rect x="{x-55}" y="80" width="110" height="60" class="{cls}"/>'
        for i,line in enumerate(label.split("\n")):
            body += f'<text x="{x}" y="{105 + i*16}" text-anchor="middle" class="mono">{line}</text>'
    # arrows
    for i in range(len(stages)-1):
        x1 = stages[i][1] + 55
        x2 = stages[i+1][1] - 55
        body += f'<path class="arrow" d="M {x1} 110 L {x2} 110"/>'
    # vector DB
    body += '<rect x="285" y="190" width="110" height="44" class="box"/>'
    body += '<text x="340" y="217" text-anchor="middle" class="mono">vector index</text>'
    body += '<text x="340" y="252" text-anchor="middle" class="small">millions of doc chunks</text>'
    body += '<path class="arrow" d="M 340 145 L 340 188"/>'
    # offline indexing
    body += '<rect x="60" y="290" width="120" height="44" class="box"/>'
    body += '<text x="120" y="317" text-anchor="middle" class="mono">documents</text>'
    body += '<rect x="200" y="290" width="120" height="44" class="box2"/>'
    body += '<text x="260" y="317" text-anchor="middle" class="mono">chunk + embed</text>'
    body += '<path class="arrow" d="M 180 312 L 198 312"/>'
    body += '<path class="arrow" d="M 320 312 L 340 235"/>'
    body += '<text x="60" y="280" class="small">offline indexing</text>'
    body += '<text x="40" y="380" class="mono">Quality knobs: chunk size, overlap, retrieve k, rerank top-n, prompt template</text>'
    return svg(720, 410, body, "RAG Pipeline — Online &amp; Offline")

diagrams = {
    "09-bpe-merge":      d_bpe(),
    "10-scaling-laws":   d_scaling(),
    "11-moe-routing":    d_moe(),
    "12-bert-gpt-t5":    d_bert_gpt_t5(),
    "13-sampling":       d_sampling(),
    "14-quantization":   d_quant(),
    "15-lora-detail":    d_lora(),
    "16-positional":     d_pos(),
    "17-inference":      d_infer(),
    "18-rag-arch":       d_rag_arch(),
}

for name, body in diagrams.items():
    (OUT / f"{name}.svg").write_text(body, encoding="utf-8")
    print("wrote", name)
