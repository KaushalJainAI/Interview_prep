"""Inject diagrams + Deep Dive / Pitfalls / Interview Qs into agent cheatsheets."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

PLAN = {
"architecture-cheatsheet.md": (
    ["diagrams/01-agent-loop.png", "diagrams/05-react-loop.png", "diagrams/06-plan-execute.png", "diagrams/07-multi-agent.png"],
r"""

---

## 🔬 Deep dive — what makes an "agent"

An *agent* is an LLM in a loop that can take actions in the world (call tools, edit files, browse). The minimum viable loop:

```
while not done:
    response = LLM(messages, tools=available_tools)
    if response.tool_calls:
        for call in response.tool_calls:
            result = run_tool(call)
            messages.append(tool_message(result))
    else:
        done = True; return response.content
```

Beyond ReAct, four major patterns:
1. **Plan-Execute** — LLM writes a plan, executor runs each step, can replan on failure.
2. **Tree-of-Thought** — branch over alternative thoughts, evaluate, pick best.
3. **Reflexion / Self-Critique** — agent reflects on its trace and revises strategy.
4. **Multi-agent** — specialised roles (researcher, coder, reviewer) coordinate via shared state.

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Infinite loop / runaway cost | Hard cap on iterations + token budget |
| Tool-call hallucination | Strict JSON schemas; validate args; retry with error |
| Context overflow over long runs | Compress / summarise; offload to vector store |
| Brittle prompt scaffolding | Use library (LangGraph, Pydantic-AI, smolagents); version prompts |
| Hidden non-determinism | Set temperature=0 for eval; log full traces |
| No human gate on destructive actions | Require approval for FS writes, payments, emails |

## 🎤 Interview questions

1. **ReAct vs Plan-Execute — when each?** ReAct for short interactive tasks; Plan-Execute for long, decomposable workflows where partial failures are okay.
2. **How to keep an agent's context manageable?** Summarise old turns, store full history in vector DB, retrieve on demand. Truncate aggressively.
3. **Why multi-agent over a single big agent?** Specialisation (better prompts per role), parallelism, debuggability. Cost goes up — single agents often win on simple tasks.
4. **What's "agentic" RL?** Train the LLM with RL signals from real or simulated tool environments (e.g., OpenAI o1, DeepSeek-R1).
5. **How would you measure agent quality?** Task success rate, # tool calls, total cost, latency p95; plus regression suite of canned tasks.

## 📚 References
- "ReAct: Synergizing Reasoning and Acting" (Yao et al., 2022)
- "Reflexion: Language Agents with Verbal Reinforcement Learning" (Shinn et al., 2023)
- Anthropic: "Building effective agents" blog post
"""),

"stategraph-cheatsheet.md": (
    ["diagrams/03-langgraph-aiaas.svg", "diagrams/12-state-graph.png"],
r"""

---

## 🔬 Deep dive — why graphs beat free-form loops

A free-form ReAct loop is hard to debug, hard to test, and silently expensive. A **state graph** makes the workflow explicit:
- Each **node** is a pure function over the shared state (`(state) -> partial_state`).
- Each **edge** is either a fixed transition or a conditional router (often itself an LLM).
- The **state** is a typed dict — concrete contract between steps.

Benefits:
- Visual diagram of the pipeline.
- Snapshot / resume at any point.
- Per-node retries / timeouts.
- Easier eval: compare states at boundaries.

## 🧮 LangGraph anatomy (sketch)

```python
from langgraph.graph import StateGraph, END

class State(TypedDict):
    query: str
    plan: list[str]
    results: list[dict]
    answer: str | None

g = StateGraph(State)
g.add_node("plan",   plan_node)
g.add_node("search", search_node)
g.add_node("answer", answer_node)
g.add_edge("plan", "search")
g.add_conditional_edges("search", router, {"more": "search", "done": "answer"})
g.add_edge("answer", END)
g.set_entry_point("plan")
app = g.compile(checkpointer=memory)
```

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| State dict bloat | Keep only needed fields; offload large blobs |
| Long chains of nodes that all call the LLM | Cache; batch when possible |
| Cycles without exit condition | Always include a max-iteration counter in state |
| Conditional router unreliable | Use Pydantic schema for router output |
| Snapshots leak secrets | Redact before persisting |

## 🎤 Interview questions

1. **Why use LangGraph vs writing your own loop?** Checkpointing, conditional edges, retry/timeout, observability come free.
2. **How do you debug a stuck agent?** Inspect state at each node boundary; rerun failed node with cached upstream.
3. **Persisting state across requests?** `Checkpointer` (sqlite, redis, postgres) per thread_id.
4. **Streaming through a graph?** LangGraph supports event streaming per node — emit tokens / state diffs to the client.
5. **Branching workflows?** Multiple outgoing conditional edges; nodes can be marked parallel.

## 📚 References
- LangGraph docs (langchain-ai)
- "Compound AI Systems" — BAIR blog (Zaharia et al., 2024)
"""),

"tools-mcp-cheatsheet.md": (
    ["diagrams/02-mcp-architecture.svg", "diagrams/09-tool-flow.png"],
r"""

---

## 🔬 Deep dive — tool calling, function calling, MCP

**Function calling** = LLM outputs structured JSON conforming to a tool's schema; client runtime executes it. Pattern formalised by OpenAI (2023).

**MCP (Model Context Protocol)** = Anthropic's open standard (2024) for *connecting* LLM apps to external systems. Replaces ad-hoc tool integration with a uniform client/server protocol:
- **Tools** — actions the model can call.
- **Resources** — read-only data the model can request.
- **Prompts** — reusable templates servers can offer.

An MCP server is a small process that speaks the protocol; clients (Claude Desktop, Cursor, agents) discover and use it.

## 🧮 Anatomy

```jsonc
// tool definition (JSON Schema)
{
  "name": "search_web",
  "description": "Search the web for a query",
  "input_schema": {
    "type": "object",
    "properties": { "query": {"type": "string"} },
    "required": ["query"]
  }
}

// LLM emits
{ "type": "tool_use", "name": "search_web", "input": {"query": "Anthropic"} }

// runtime returns
{ "type": "tool_result", "tool_use_id": "...", "content": "..." }
```

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Too many tools → low accuracy | Curate; prefer 5-15 tools per agent |
| Vague tool descriptions | Write like API docs; include examples |
| No schema validation | Validate input before run; return structured error |
| Side effects without idempotency | Make tools safe to retry; use idempotency keys |
| Sensitive tools exposed by default | Allowlist + per-tool human approval |
| Long results blow context | Truncate; offer pagination tool |

## 🎤 Interview questions

1. **Why MCP and not just function calling?** Function calling is a wire format; MCP standardises the *discovery, lifecycle, and capabilities* across vendors. Build once, run on Claude Desktop / Cursor / custom agents.
2. **What goes in a tool description?** What it does, when to use it, when NOT to, expected inputs, common pitfalls. Treat as in-context documentation.
3. **How to handle errors in tool execution?** Return structured error; let the model retry with corrected args; cap retries.
4. **Authentication for MCP servers?** Bearer tokens, OAuth flows, env vars; treat as you would any API.
5. **Tool selection at scale?** Hybrid: route by intent classifier first, then narrow tool list; or retrieve tools by embedding similarity.

## 📚 References
- modelcontextprotocol.io
- OpenAI function calling docs
- "Tool Use with Claude" — Anthropic docs
"""),

"memory-context-cheatsheet.md": (
    ["diagrams/08-memory-layers.png"],
r"""

---

## 🔬 Deep dive — memory architectures

Five memory layers worth distinguishing:
1. **Short-term**: messages in the current context window.
2. **Working memory**: scratchpad notes the model writes (e.g., a TODO list).
3. **Long-term semantic**: vector DB of facts about the user, world, organisation.
4. **Episodic**: previous full task trajectories for retrospective learning.
5. **Procedural**: catalogue of skills / tools / examples the agent can invoke.

The agent assembles a fresh context each turn by **pulling** from each layer; layers persist across turns.

## 🧮 Context window budget

Typical budget for a 200k-token model in a real agent run:
```
system prompt           ~ 2k
tool definitions        ~ 4k
retrieved docs          ~ 16k
chat history            ~ 8k
scratchpad / state      ~ 2k
response budget         ~ 8k
                        ────
                          40k  (leaves headroom)
```

Compression strategies as runs grow:
- Summarise oldest N turns into a paragraph.
- Replace verbose tool outputs with file refs ("see /tmp/output.json").
- Hierarchical summaries (chunk → section → run).

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Stuffing the whole DB into context | Retrieve, don't dump |
| Lossy summarisation removes critical detail | Keep verbatim items flagged "important" |
| Memory leaks (sensitive data persists) | TTL on stores; redact on write |
| Stale facts in long-term memory | Versioned writes; "as of" timestamps |
| User asks about past session; agent has no memory | Persist by thread_id / user_id |

## 🎤 Interview questions

1. **What's the lost-in-the-middle problem?** Models attend better to the start and end of context; middle facts are missed. Mitigations: chunking + retrieval; restate critical facts late in the prompt.
2. **Vector DB for memory — collisions?** Use namespaces / metadata filters per user; encrypt at rest.
3. **How do you decide what to remember?** Explicit "save this" tool the agent calls; or scheduled summariser at session end.
4. **Episodic memory use case?** Reflexion: agent reads its own past failures and adjusts strategy.
5. **Cost of memory at scale?** Per-user vector index storage + retrieval; cache embeddings; consider in-process LRU.

## 📚 References
- "Lost in the Middle: How Language Models Use Long Contexts" (Liu et al., 2023)
- MemGPT / Letta — operating-system-style memory paging for LLMs
"""),

"pydantic-cheatsheet.md": (
    [],  # already 248 lines; just append
r"""

---

## 🔬 Deep dive — why structured outputs

LLMs return strings; we want **typed objects** to chain them into reliable software. Pydantic gives:
- Schema-as-Python-class (readable, IDE-friendly).
- Validation with clear error messages.
- JSON Schema export → goes straight to function-calling tools.
- Coercion (`"3" → 3`) where safe; refusal where not.

Pair with **Instructor** / **outlines** / **JSON-mode** to constrain the LLM's output to the schema.

## 🧮 Patterns

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class Citation(BaseModel):
    url: str
    quote: str = Field(..., min_length=10)

class Answer(BaseModel):
    text: str
    confidence: Literal["low","medium","high"]
    citations: list[Citation]

    @field_validator("citations")
    @classmethod
    def at_least_one(cls, v):
        if not v: raise ValueError("need at least one citation")
        return v
```

Schema-driven prompting:
```
schema = Answer.model_json_schema()
prompt = f"Reply with JSON matching this schema:\n{json.dumps(schema)}"
raw = llm(prompt)
answer = Answer.model_validate_json(raw)   # raises on bad output
```

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Free-form prompts then hope for JSON | Force JSON mode + schema |
| Allowing too many optional fields | Model fills them sloppily; constrain |
| Long descriptions on every field | Tokens cost money; keep descriptions short |
| No retry on validation failure | Pass error back to LLM with original output |
| Pydantic v1 vs v2 confusion | `model_validate` is v2; `parse_obj` is v1 |

## 🎤 Interview questions

1. **Why Pydantic over `json.loads`?** Validation + types + helpful error messages.
2. **What if the LLM refuses to obey the schema?** Use JSON mode (OpenAI), tool-calling, or grammar-constrained decoding (outlines / vllm guided).
3. **How to handle partial / streaming structured output?** Use `instructor` partial parsing; emit fields as they arrive.
4. **Pydantic vs dataclasses?** Pydantic adds validation + JSON Schema + serialisation; dataclasses are zero-runtime.
5. **Forward references in models?** `from __future__ import annotations` + `model_rebuild()`.

## 📚 References
- Pydantic v2 docs
- `instructor` library — JSON-mode + retries
- "Constrained Decoding" — outlines library
"""),

"guardrails-sandbox-hitl-cheatsheet.md": (
    ["diagrams/11-guardrails.png", "diagrams/04-rlhf-dpo.svg"],
r"""

---

## 🔬 Deep dive — defence in depth

Single-layer defences fail. Stack:
1. **Input filters** — PII redaction, prompt-injection detectors (Lakera, NVIDIA NeMo Guardrails).
2. **System prompt hardening** — explicit refusal patterns, role separation.
3. **Capability constraints** — tool allowlists, scoped credentials, dry-run mode.
4. **Sandbox execution** — containers (Docker / gVisor), WebAssembly, restricted FS, network egress controls.
5. **Output filters** — toxicity, PII, secrets scanner.
6. **Human-in-the-loop (HITL)** — approval for high-risk actions (file write, payment, email).
7. **Rate / budget limits** — per-user max tokens, max tool calls, max cost.
8. **Audit logging** — full trace storage + diff review on release.

## ⚠️ Prompt injection — the open problem

Direct, indirect (via retrieved doc), and multi-turn injections still bypass most defences. Mitigations:
- Don't render untrusted text directly into the system prompt.
- Strip / quote retrieved content.
- Use a *separate* model for guardrails when stakes are high.
- Never let untrusted input grant tool access (delimit instructions from data clearly).
- Constrain output via JSON schemas — harder to smuggle commands.

## ⚠️ Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Trusting model's own refusal | Add external classifier |
| Allowing arbitrary shell commands | Whitelist; static analysis |
| Sandbox escape via file mounts | Mount RO; minimal capabilities |
| Logging PII for "debugging" | Hash / drop on write |
| Approval fatigue → users approve all | Group by risk; only prompt for high-risk |

## 🎤 Interview questions

1. **What's prompt injection and why is it hard?** Untrusted text gets concatenated into the prompt; model can't distinguish data from instructions. Hard because LLMs are designed to follow instructions wherever they appear.
2. **Sandbox options for agent code execution?** Docker, gVisor, Firecracker, WebAssembly (Wasmtime), e2b, Modal. Trade-off: isolation vs latency.
3. **HITL: when to gate?** Cost ≥ threshold, irreversible actions, sensitive data access, unfamiliar tool combos.
4. **RLHF vs Constitutional AI?** RLHF uses human-labelled preferences. CAI uses a written constitution + LLM-generated critiques to bootstrap preferences (less human labour).
5. **How to evaluate guardrails?** Red-team suite of known attacks; track bypass rate per release.

## 📚 References
- "Universal and Transferable Adversarial Attacks on Aligned Language Models" (Zou et al., 2023)
- OWASP Top 10 for LLM Applications
- NVIDIA NeMo Guardrails docs
"""),

"agent-code-examples.md": (
    ["diagrams/05-react-loop.png", "diagrams/12-state-graph.png"],
""),
}

for fname, (imgs, extra) in PLAN.items():
    p = ROOT / fname
    if not p.exists(): print("MISSING:", fname); continue
    text = p.read_text(encoding="utf-8")
    lines = text.split("\n"); out = []; inserted = False
    for ln in lines:
        out.append(ln)
        if not inserted and ln.startswith("# "):
            for img in imgs:
                if f"![Diagram]({img})" not in text:
                    out.append(""); out.append(f"![Diagram]({img})")
            inserted = True
    text = "\n".join(out)
    if extra and "## 🔬 Deep dive" not in text:
        if not text.endswith("\n"): text += "\n"
        text += extra
    p.write_text(text, encoding="utf-8")
    print("expanded:", fname)
