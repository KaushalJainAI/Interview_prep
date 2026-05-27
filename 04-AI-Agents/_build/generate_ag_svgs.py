"""Generate additional SVG diagrams for AI-Agents."""
from pathlib import Path

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

def svg(w,h,body,title=None):
    t = f'<text x="{w//2}" y="22" text-anchor="middle" class="title">{title}</text>' if title else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{STYLE}{t}{body}</svg>'

def d_react():
    body = ''
    body += '<text x="40" y="55" class="label">ReAct loop: Thought → Action → Observation → Repeat</text>'
    body += '<rect x="80" y="80" width="160" height="55" class="box2"/><text x="160" y="115" text-anchor="middle" class="mono">Thought</text>'
    body += '<text x="160" y="100" text-anchor="middle" class="small">"I need to look up X"</text>'
    body += '<path class="arrow2" d="M 240 108 L 280 108"/>'
    body += '<rect x="280" y="80" width="160" height="55" class="box3"/><text x="360" y="115" text-anchor="middle" class="mono">Action</text>'
    body += '<text x="360" y="100" text-anchor="middle" class="small">search("X")</text>'
    body += '<path class="arrow2" d="M 440 108 L 480 108"/>'
    body += '<rect x="480" y="80" width="160" height="55" class="box4"/><text x="560" y="115" text-anchor="middle" class="mono">Observation</text>'
    body += '<text x="560" y="100" text-anchor="middle" class="small">tool returns "..."</text>'
    body += '<path class="arrow2" d="M 560 140 C 560 180 160 180 160 140"/>'
    body += '<text x="360" y="200" text-anchor="middle" class="small">repeat until Thought says "I have the answer"</text>'
    body += '<rect x="280" y="240" width="160" height="50" class="box5"/><text x="360" y="270" text-anchor="middle" class="mono">Final answer</text>'
    body += '<path class="arrow2" d="M 360 200 L 360 240"/>'
    body += '<text x="40" y="330" class="mono">Prompt encodes the loop format with "Thought:" / "Action:" / "Observation:" tokens.</text>'
    body += '<text x="40" y="352" class="small">Limits: token budget per step, max steps, optional ToolException → reflect.</text>'
    return svg(720, 380, body, "ReAct — Thought + Tool Loop")

def d_planner():
    body = ''
    body += '<rect x="280" y="60" width="160" height="44" class="box2"/><text x="360" y="88" text-anchor="middle" class="mono">Planner LLM</text>'
    body += '<text x="40" y="86" class="small">user goal →</text>'
    body += '<path class="arrow" d="M 110 80 L 280 80"/>'
    body += '<rect x="60" y="160" width="120" height="40" class="box3"/><text x="120" y="185" text-anchor="middle" class="mono">step 1</text>'
    body += '<rect x="200" y="160" width="120" height="40" class="box3"/><text x="260" y="185" text-anchor="middle" class="mono">step 2</text>'
    body += '<rect x="340" y="160" width="120" height="40" class="box3"/><text x="400" y="185" text-anchor="middle" class="mono">step 3</text>'
    body += '<rect x="480" y="160" width="120" height="40" class="box3"/><text x="540" y="185" text-anchor="middle" class="mono">step 4</text>'
    for x in (120,260,400,540):
        body += f'<path class="arrow" d="M {x} 110 L {x} 158"/>'
    # executor below
    body += '<rect x="280" y="260" width="160" height="44" class="box4"/><text x="360" y="288" text-anchor="middle" class="mono">Executor</text>'
    for x in (120,260,400,540):
        body += f'<path class="arrow2" d="M {x} 200 L 360 258"/>'
    body += '<rect x="510" y="260" width="160" height="44" class="box5"/><text x="590" y="288" text-anchor="middle" class="mono">Critic / Replan</text>'
    body += '<path class="arrow3" d="M 510 282 L 440 282"/>'
    body += '<text x="40" y="340" class="mono">Plan-Execute-Critique = decompose first, run, replan on failure</text>'
    body += '<text x="40" y="362" class="small">Variants: Tree-of-Thought (branch), ReWOO (plan + parallel tool calls), Reflexion (self-critique).</text>'
    return svg(720, 390, body, "Plan-Execute-Critic Agent")

def d_multi_agent():
    body = ''
    # network of agents
    agents = {
        "Orchestrator": (360, 80,  "box2"),
        "Researcher":   (160, 200, "box4"),
        "Coder":        (360, 200, "box4"),
        "Reviewer":     (560, 200, "box4"),
        "Tools":        (360, 320, "box3"),
    }
    for name,(x,y,cls) in agents.items():
        body += f'<rect x="{x-65}" y="{y-22}" width="130" height="44" class="{cls}"/>'
        body += f'<text x="{x}" y="{y+5}" text-anchor="middle" class="mono">{name}</text>'
    edges = [("Orchestrator","Researcher"),("Orchestrator","Coder"),("Orchestrator","Reviewer"),
             ("Researcher","Tools"),("Coder","Tools"),("Reviewer","Coder")]
    for a,b in edges:
        x1,y1,_ = agents[a]; x2,y2,_ = agents[b]
        body += f'<line x1="{x1}" y1="{y1+22}" x2="{x2}" y2="{y2-22}" stroke="#1f6feb" stroke-width="1.5"/>'
    body += '<text x="40" y="380" class="mono">Patterns: hierarchical (above), debate, swarm, blackboard.</text>'
    body += '<text x="40" y="402" class="small">Comm via shared memory or message bus. Risks: infinite chatter, cost blow-up, role drift.</text>'
    return svg(720, 430, body, "Multi-Agent System — Hierarchical")

def d_memory_layers():
    body = ''
    layers = [
        ("Short-term (chat history)",  80,  "box2", "in context window; truncated/compressed"),
        ("Working memory (scratchpad)",140, "box3", "free-form notes the agent writes"),
        ("Long-term (vector DB)",      200, "box4", "embedded facts, retrieved on demand"),
        ("Episodic (past trajectories)",260,"box5", "previous task runs, for self-reflection"),
        ("Procedural (skills / tools)",  320,"box", "available actions, docs, examples"),
    ]
    for label, y, cls, desc in layers:
        body += f'<rect x="60" y="{y-20}" width="240" height="40" class="{cls}"/>'
        body += f'<text x="180" y="{y+5}" text-anchor="middle" class="mono">{label}</text>'
        body += f'<text x="320" y="{y+5}" class="small">{desc}</text>'
    body += '<text x="40" y="380" class="mono">Context assembly each turn: pick from each layer, fit token budget.</text>'
    body += '<text x="40" y="402" class="small">Compression strategies: summarisation, lossless eviction, embeddings recall.</text>'
    return svg(720, 430, body, "Agent Memory — Layered Architecture")

def d_tool_call():
    body = ''
    body += '<rect x="60"  y="80" width="160" height="50" class="box2"/><text x="140" y="110" text-anchor="middle" class="mono">LLM</text>'
    body += '<path class="arrow2" d="M 220 100 L 280 100"/>'
    body += '<text x="250" y="92" text-anchor="middle" class="small">tool_call(args)</text>'
    body += '<rect x="280" y="80" width="160" height="50" class="box3"/><text x="360" y="110" text-anchor="middle" class="mono">Runtime / Router</text>'
    body += '<path class="arrow" d="M 440 100 L 500 100"/>'
    body += '<rect x="500" y="80" width="160" height="50" class="box4"/><text x="580" y="110" text-anchor="middle" class="mono">Tool function</text>'
    # response back
    body += '<path class="arrow3" d="M 500 160 L 280 160"/>'
    body += '<text x="390" y="180" text-anchor="middle" class="small">tool_response (JSON)</text>'
    body += '<path class="arrow3" d="M 280 160 L 220 160"/>'
    body += '<rect x="280" y="240" width="160" height="50" class="box5"/><text x="360" y="270" text-anchor="middle" class="mono">JSON Schema</text>'
    body += '<path class="arrow2" d="M 360 130 L 360 238"/>'
    body += '<text x="40" y="330" class="mono">LLM emits structured args; runtime validates against schema, executes, returns result.</text>'
    body += '<text x="40" y="352" class="small">MCP standardises this protocol (Anthropic, 2024) — tools/resources/prompts as servers.</text>'
    return svg(720, 380, body, "Tool / Function Calling Flow")

def d_eval():
    body = ''
    cols = [
        ("Unit (component)",   100, "box4", ["tool args correctness","retrieval recall@k","prompt → JSON validates"]),
        ("Integration (flow)", 280, "box2", ["full trace ends","right tool sequence","budget respected"]),
        ("E2E (task)",        460, "box3", ["task succeeds","user satisfied","ground truth match"]),
    ]
    for label,x,cls,bullets in cols:
        body += f'<rect x="{x-60}" y="60" width="160" height="40" class="{cls}"/>'
        body += f'<text x="{x+20}" y="86" text-anchor="middle" class="mono">{label}</text>'
        for i,b in enumerate(bullets):
            y = 120 + i*32
            body += f'<rect x="{x-60}" y="{y-15}" width="160" height="28" class="box"/>'
            body += f'<text x="{x-50}" y="{y+5}" class="small">• {b}</text>'
    body += '<text x="40" y="280" class="mono">LLM-as-judge: cheap proxy but biased; pair with human spot-checks.</text>'
    body += '<text x="40" y="302" class="mono">Datasets: BrowseComp, SWE-bench, GAIA, TAU-bench, WebArena.</text>'
    body += '<text x="40" y="324" class="mono">Track: success rate, cost / call, latency p95, # tool calls.</text>'
    body += '<text x="40" y="350" class="small">Regression suite per release — store full traces for diff review.</text>'
    return svg(720, 380, body, "Agent Evaluation Stack")

def d_guard():
    body = ''
    layers = [
        ("Input filter",     100, "box2", "PII redact, prompt injection check"),
        ("Tool whitelist",   170, "box3", "only approved tools; arg validation"),
        ("Sandbox exec",     240, "box4", "containers / WASM / restricted FS"),
        ("Output filter",    310, "box5", "PII out; toxicity; policy classifier"),
        ("Human-in-the-loop",380, "box",  "approve high-risk actions"),
    ]
    for label, y, cls, desc in layers:
        body += f'<rect x="60" y="{y-22}" width="200" height="44" class="{cls}"/>'
        body += f'<text x="160" y="{y+5}" text-anchor="middle" class="mono">{label}</text>'
        body += f'<text x="280" y="{y+5}" class="small">{desc}</text>'
    body += '<text x="40" y="450" class="mono">Defence in depth — assume one layer will fail.</text>'
    body += '<text x="40" y="472" class="small">Prompt injection > 95% bypass any single defence; combine input filters + capability constraints + human gates.</text>'
    return svg(720, 500, body, "Agent Guardrails — Defence in Depth")

def d_orchestration():
    body = ''
    # state graph: nodes + transitions
    body += '<text x="40" y="55" class="label">LangGraph-style state machine (deterministic + LLM-decided edges)</text>'
    nodes = {"start":(120,130),"plan":(280,130),"search":(440,90),"code":(440,170),"verify":(600,130),"end":(600,260)}
    for n,(x,y) in nodes.items():
        body += f'<ellipse cx="{x}" cy="{y}" rx="55" ry="26" class="box2"/>'
        body += f'<text x="{x}" y="{y+5}" text-anchor="middle" class="mono">{n}</text>'
    edges = [("start","plan"),("plan","search"),("plan","code"),("search","verify"),("code","verify"),("verify","end"),("verify","plan")]
    for a,b in edges:
        x1,y1 = nodes[a]; x2,y2 = nodes[b]
        body += f'<path class="arrow" d="M {x1+55} {y1} Q {(x1+x2)/2} {min(y1,y2)-12} {x2-55} {y2}"/>'
    body += '<text x="40" y="330" class="mono">Each node = function over state dict. Edges can be conditional (router LLM).</text>'
    body += '<text x="40" y="352" class="small">Benefits over open agent loops: visible flow, easier debugging, persistent state, branching.</text>'
    return svg(720, 380, body, "Agent Orchestration — State Graph")

diagrams = {
    "05-react-loop":      d_react(),
    "06-plan-execute":    d_planner(),
    "07-multi-agent":     d_multi_agent(),
    "08-memory-layers":   d_memory_layers(),
    "09-tool-flow":       d_tool_call(),
    "10-agent-eval":      d_eval(),
    "11-guardrails":      d_guard(),
    "12-state-graph":     d_orchestration(),
}

for n,b in diagrams.items():
    (OUT/f"{n}.svg").write_text(b, encoding="utf-8"); print("wrote",n)
