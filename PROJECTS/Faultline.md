# Faultline — AI-Assisted QA & Chaos Engineering Platform

**Interview Notes (deep dive). Code-grounded: read from the real repo at `C:\Users\91700\Desktop\Faultline`.**

> One-line pitch: *"Faultline is an AI agent that QA-tests other people's codebases. You point it at a project and a running URL; it maps the code, generates functional tests, fires adversarial 'chaos' HTTP payloads, correlates the crashes it causes with the server logs, scores production-readiness, and proposes patches — all streamed live in a terminal, pausing to ask me before it does anything destructive."*

- Stack: Django REST control plane + **LangGraph agent** ("Aegis-Breaker") + interactive CLI (`faultline.py`) + FAISS + async HTTP engine. Multi-provider LLM (OpenRouter/OpenAI/Anthropic/Google + Claude/Gemini/Codex CLI delegates). Also exposes its tools over **MCP**.

---

## 1. The 30-second story

Testing is the perfect job for an AI agent: it's exploratory, repetitive, and needs both reasoning ("what could break this endpoint?") and tool use ("send this payload, read that log"). But a naive "let the LLM test it" approach has three problems I designed around:

1. **LLMs are expensive and slow.** So Faultline does **cheap deterministic checks first** (a "pipeline" mode with no AI at all) and only spends LLM tokens on the genuinely hard, exploratory part.
2. **LLMs lose the plot on long jobs.** A real campaign produces megabytes of tool output that won't fit in a context window. So I built a **queryable-reference context system** — summarize big outputs inline, store the originals on disk, let the agent fetch them by ID.
3. **An agent that attacks a server and edits code is dangerous.** So every destructive action goes through a **human-in-the-loop** prompt, and the agent runs against a **production-readiness budget** that reserves its last calls for writing the report.

So the core idea: **a deterministic pipeline and an AI agent that share the same toolbelt**, with disciplined context and budget management so it stays cheap, safe, and finishes the job.

---

## 2. Architecture at a glance

```
                 ┌─────────────── faultline.py (Interactive CLI) ───────────────┐
                 │  live streaming · HITL prompts · per-run output folder        │
                 └───────────────┬───────────────────────────┬──────────────────┘
                                 │ pipeline mode             │ agent / hybrid mode
                                 ▼                            ▼
   ┌──────────────┐      ┌───────────────┐         ┌──────────────────────────┐
   │ Control Plane│      │ Deterministic │         │  Aegis-Breaker (LangGraph)│
   │ (Django REST)│◀────▶│  Pipeline     │         │  agent ⇄ tools loop       │
   │ Campaign/    │      │ syntax,imports│         └────────────┬─────────────┘
   │ Finding/     │      │ deps,pytest,  │                      │ LangChain tools
   │ ToolRun (DB) │      │ ruff          │            ┌─────────▼──────────┐
   └──────────────┘      └───────────────┘            │  Skills Library    │
          ▲                                           │  ASTGrapher        │
          │ Vault (AuthFlow) injects session creds    │  Attacker (chaos)  │
          │                                           │  Medic (lifecycle) │
          ▼                                           │  SemanticIndexer   │
     Target Application  ◀──── authenticated HTTP ─────┘  (FAISS)           │
          │  writes server.log                        └────────────────────┘
          └──────────────▶ Log Correlator (watchdog, X-Aegis-Request-ID)
```

**Four domains** (clean separation, like AIAAS):
- **Control Plane (Django)** — persists Campaigns, Findings, ToolRuns; REST API for headless/CI use.
- **Vault** — acquires + injects auth (static token or a login AuthFlow) so the agent can test *secured* endpoints.
- **Execution Engine (LangGraph)** — the Aegis-Breaker agent that reasons and calls tools.
- **Interactive CLI** — the primary human interface; live streaming + approval prompts.

---

## 3. The three modes (the key design decision)

| Mode | What runs | When to use | Cost |
|---|---|---|---|
| **pipeline** | deterministic checks only, **no LLM, no target server needed** | fast CI gate, sanity check | ~free |
| **agent** | model-led investigation with file-read/list tools | exploring an unfamiliar codebase | LLM tokens |
| **hybrid** | deterministic baseline **first**, then agent-led API/chaos attack | full campaign | LLM tokens |

**Why this matters (say this in interview):** "pipeline-first" is a **cost and reliability decision**. Deterministic checks (syntax errors, broken imports, dependency conflicts, pytest-collection failures, Ruff lint, dependency-failure propagation) are O(n) over the code, free, and never hallucinate. I run them *before* spending a single LLM token, and I hand their results to the agent as a starting map so it doesn't waste calls rediscovering basic facts. The agent is reserved for what only it can do: reasoning about *what to attack and how*.

---

## 4. The agent loop (LangGraph) — deliberately simple

The graph is intentionally a **two-node cycle**: `agent → tools → agent → …` until the model returns a message with no tool calls. Conceptually the agent runs the loop **Observe → Plan → Execute → Analyze → Heal**:

1. **Observe** — map structure & docs (AST + FAISS index).
2. **Plan** — pick endpoints/attacks from the map.
3. **Execute** — run functional tests or chaos payloads.
4. **Analyze** — correlate crashes with server logs.
5. **Heal** — propose code patches.

**Why keep the graph simple instead of a big branching state machine?** Because the *intelligence* lives in the tools and the prompt, not in graph topology. A simple `agent⇄tools` loop is easy to reason about, easy to test, and lets the model decide the order — which is exactly what you want for open-ended exploration. (Same philosophy as AIAAS: keep the runner dumb, put the smarts in well-defined, testable units.)

### The toolbelt (≈18 LangChain tools)
`list_project_files`, `read_project_file`, `run_deterministic_checks`, `analyze_project_structure` (AST), `index_project_documentation` / `query_knowledge_base` (FAISS), `validate_python_code`, `run_functional_test` (writes + runs a temp pytest), `execute_chaos_campaign`, `propose_code_patch`, `save_vulnerability_report`, `generate_dependency_graph` (3D Dash app), `calculate_project_quality`, plus **CLI-delegate** tools (`execute_claude_code_task`, `execute_gemini_cli_task`, `execute_codex_cli_task`) that hand a hard sub-task to a full coding agent.

---

## 5. The skills (the "hands") — and their decisions

- **ASTGrapher** — parses Python with the `ast` module to map classes/functions/imports/calls. **Why AST, not regex or LLM?** It's exact, O(n) over the source, and free. You never want a model guessing the call graph when the parser can tell you the truth.
- **Attacker (chaos engine)** — fires **asynchronous** HTTP payloads. Two decisions: (a) async so it can pound many endpoints concurrently without blocking; (b) every request carries a unique **`X-Aegis-Request-ID`** header.
- **Medic** — manages the target process lifecycle (start / stop / health-check) so a campaign can boot the app, test it, and shut it down cleanly.
- **SemanticIndexer** — **FAISS** vector index over the project's Markdown docs so the agent can semantically search documentation instead of stuffing it all into context.

### The crash-correlation trick (great interview detail)
When the Attacker causes a 500, how do you know *which* request caused *which* log stack-trace? I tag every outgoing request with `X-Aegis-Request-ID`, and a **watchdog**-based Log Correlator tails `server.log`. Matching the ID in the log to the request makes correlation **O(1) per crash** instead of guessing by timestamp (which is unreliable under concurrent load). This is the single cleverest piece of plumbing in the project.

---

## 6. Context-window management (the hard engineering problem)

Long campaigns generate far more text than any context window holds. My solution is a **Queryable Reference system**:

- **Auto-summarize:** any tool output over **~5,000 tokens** is summarized inline in the agent's working context.
- **Persist the original:** the full output is written to disk (`content_store/`) with a `[REF:<id>]` marker, indexed in `memory.md`.
- **Retrieve on demand:** the agent calls `retrieve_stored_content(id)` to pull the original back only when it actually needs the detail (e.g. writing the final report or a patch).

Each model call gets a **compact tiered context** (`build_tiered_context`) — recent activity + status block + the tail of the live plan + reference ledgers — **not** the raw transcript. Full history is still retained losslessly (`checkpoint.json`, session JSONL, `transcript.txt`, `history_vault/`) and is itself retrievable by reference.

**Why this is the right design:** it decouples *what the model sees* (small, cheap, fast) from *what the system remembers* (everything, auditable). It's the same lesson as a CPU cache — keep the hot working set small, page in the rest on demand.

### Budget-aware endgame (designing for the worst case)
LLM call budgets can run out mid-campaign. If the agent naively explores until it's out of budget, you get **no report** — the worst outcome. So:
- `FAULTLINE_REPORTING_RESERVE_CALLS` prunes exploratory tools near the end.
- `FAULTLINE_FINAL_WALKTHROUGH_CALLS` reserves a final **no-tools** window for a human walkthrough.
- `/wrapup` (operator command) forces synthesis in a few calls.
- **If the budget dies before the report is saved, Faultline writes a factual fallback `vulnerability_report.md` from the artifacts it already has.** There is always a report.

---

## 7. Multi-provider + CLI delegation (a cost-engineering idea)

Faultline talks to OpenRouter (default), OpenAI, Anthropic, Google — *and* can delegate a campaign or a hard sub-task to a locally-authenticated **CLI** (`claude -p`, `gemini -p`, `codex exec`). 

**Why CLI delegates?** They run on your existing **subscription**, so you can do expensive multi-file reasoning without paying per-token API spend. It also means Faultline can use a *more capable* agent (a full coding CLI in a sandbox) for tasks its own simple loop isn't ideal for — a pragmatic "use the best tool, even if it's not me" decision. Codex runs `--sandbox read-only` by default — safe by default.

---

## 8. Safety model (an agent that attacks and edits code)

| Risk | Prevention |
|---|---|
| Agent runs a destructive action unprompted | **HITL** — CLI shows a yellow approval panel; agent has a `request_user_input` tool and must get a credential/permission before acting |
| Agent edits source directly | patches are written to **`.aegis_patches`** (proposals), not applied in place |
| Delegated CLI does damage | Codex defaults to **read-only sandbox** |
| Provider missing/misconfigured | campaign-start API returns a **config error** instead of a broken run |
| Runs overwrite each other | **per-run isolated folder** `reports/<project>_<timestamp>/` — auditable, comparable |
| Target left running after crash | **Medic** stops the process in finalization |

---

## 9. Complexity & cost cheat-sheet

| Operation | Cost | Why it's designed that way |
|---|---|---|
| Deterministic pipeline | O(n) over source, $0 | run first, before any LLM |
| AST mapping | O(n) parse | exact, no hallucination |
| Crash correlation | O(1) per crash via request-ID | timestamp-matching is unreliable under load |
| Doc search | FAISS ANN, sub-linear | beats stuffing all docs in context |
| Context per LLM call | bounded (compact tiered set) | cost/latency control; originals paged in on demand |
| Chaos attacks | async/concurrent | throughput without blocking |

---

## 10. "Tell me about..." — ready answers
- **A system you designed** → pipeline-first + agent: deterministic cheap checks before expensive LLM reasoning, sharing one toolbelt.
- **Hardest problem** → context-window management at scale: the queryable-reference system (summarize inline, store originals, retrieve by ID) + budget-reserved reporting so a campaign *always* produces a report.
- **A clever debugging idea** → `X-Aegis-Request-ID` header + watchdog log tailing to correlate a crash to the exact request that caused it.
- **Designing for failure** → fallback report when the LLM budget dies; read-only sandbox for delegated CLIs; HITL gates on destructive actions; Medic guarantees target cleanup.
- **Cost engineering** → pipeline-first, context compaction, and subscription-backed CLI delegation to avoid per-token spend.
- **Agentic AI depth** → a real LangGraph agent loop with a tool registry, sub-agents (CLI delegates), FAISS RAG over docs, and a 9-component "harness" (iteration engine, context compaction, registry, persistence, hooks, permissions) that mirrors how production coding agents are built.

## 11. Likely follow-ups
- *"Why not just one big LLM prompt?"* → context limits + cost + reliability; deterministic checks are free and exact, so do those first.
- *"How do you stop runaway cost?"* → call budget with reserved endgame, context compaction, summarization threshold, pipeline-first.
- *"How is this different from a fuzzer?"* → a fuzzer blindly mutates input; Faultline *reasons* about endpoints from the AST/doc map, then attacks with context, then correlates and explains crashes and proposes fixes.
- *"Biggest weakness?"* → endpoint schema extraction from DRF serializers/routers is still shallow; richer contract verification (embedding function docstrings) is the next step. The agent graph is simple by design — more complex multi-agent planning is a future direction.

---

## 12. Testing

> Code-grounded: Faultline ships `pytest.ini`, a `scripts/test_tools.py` smoke test, and `python -m compileall` gates.

### 12.1 How it's tested
- **Tool smoke test** (`scripts/test_tools.py`) — exercises every skill/tool in isolation so a broken tool is caught before a campaign relies on it.
- **`compileall` gate** — `python -m compileall campaigns core skills scripts mcp_server.py manage.py` ensures everything imports/compiles (cheap, catches syntax/import breakage fast — the same class of check the product itself runs on *targets*).
- **Django unit tests** (`python manage.py test`) — control-plane models (Campaign/Finding/ToolRun) and API.
- **Dogfooding** — Faultline's whole purpose is testing; the deterministic pipeline (`run_deterministic_checks`) is effectively a test suite it can run on *itself*.

### 12.2 What deserves dedicated tests (and why)
| Area | Why risky | Test |
|---|---|---|
| Context compaction | a bug here silently drops campaign history | assert outputs >5k tokens get a `[REF:id]` and `retrieve_stored_content` returns the original verbatim |
| Budget endgame | worst case = no report | simulate budget exhaustion → assert a fallback `vulnerability_report.md` is still written |
| Crash correlation | wrong attribution = useless finding | inject a known request-ID into a fake log → assert it maps to the right request |
| HITL gate | an agent acting without approval is dangerous | assert a destructive tool halts and waits for `request_user_input` |
| Provider routing | misconfig should fail clean | assert campaign-start returns a config error (not a crash) when no provider is set |

### 12.3 Honest gaps
- No integration test against a **disposable demo target** yet (a known next step) — today's E2E validation is manual against real projects.
- Coverage is uneven: the deterministic pipeline and tools are well-covered; the agent loop is harder to test deterministically (LLM nondeterminism) and leans on smoke tests + manual campaign runs. Property-based tests over the AST mapper would be a strong addition.
