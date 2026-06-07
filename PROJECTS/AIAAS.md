# AIAAS — Agentic AI Workflow Automation Platform

**Interview Notes (deep dive). Code-grounded: every claim here maps to real backend code.**

> One-line pitch: *"AIAAS is a 'better n8n' — a visual editor where users drag-and-drop nodes to build automations, and a Django backend that compiles that visual graph into an executable LangGraph and runs it with full supervision, live progress over WebSockets, encrypted credentials, and human-in-the-loop approval."*

- Live: aiaas.kaushaljain.com
- Stack: Django REST + Channels (WebSockets) + Celery + LangGraph + React/TypeScript (ReactFlow), PostgreSQL, Redis, AWS.

---

## 1. The 30-second story (say this first in an interview)

There are two hard problems in a workflow automation tool:

1. **Turning a picture into a program.** The user draws boxes and arrows on a canvas. That is just JSON. Something has to check it is valid and turn it into something that actually runs. I call this the **compiler**.
2. **Running that program safely.** Workflows call LLMs, hit APIs, loop, and can run for minutes. They can crash, hang, or cost money. Something has to run it, stream progress, recover from failures, and let a human step in. I call this the **executor**.

My core design decision was to **separate these two completely** — a *compiler/executor split*, exactly like a real programming language has a compiler and a runtime. The compiler does static analysis and produces a runnable graph; the executor just runs graphs and reports what happened. Neither one makes "AI decisions" — that is a third layer, the **orchestrator (King)**.

This separation is the single most important thing to understand about the system, and it is what makes it testable, debuggable, and safe.

---

## 2. Architecture at a glance

```
User draws graph (ReactFlow)  ->  JSON  ->  [COMPILER]  ->  CompiledStateGraph (LangGraph)
                                                  |                     |
                                          static validation       [EXECUTOR/engine]
                                          (DAG, creds, config,          |
                                           types)                  runs the graph,
                                                                   heartbeats, logs
                                                                        |
                                  [ORCHESTRATOR / King] <- hooks ->  per-node closures
                                  (AI supervision: before/after/on_error, HITL)
                                                                        |
                                  WebSocket (Channels) <- live events -> React UI
```

Three layers, three responsibilities — this is the **Supervisor–Worker pattern**:

| Layer | File(s) | Job | Does NOT do |
|---|---|---|---|
| **Compiler** | `compiler/compiler.py`, `compiler/validators.py` | JSON → validated LangGraph | Run anything, call AI |
| **Executor (worker)** | `executor/engine.py` | Run the graph, heartbeat, log, finalize | Decide intent, talk to user |
| **Orchestrator (King / supervisor)** | `executor/king.py`, `orchestrator/` | AI reasoning, HITL, abort/pause/retry | Touch graph internals |

**Why split it this way?** Three reasons I can defend:
- **Testability** — I can unit-test the compiler with plain dicts (no DB, no network). I can test the executor with a fake graph. The AI layer is mockable.
- **Determinism** — the executor is a *deterministic runner*. Given the same compiled graph and state, it does the same thing. AI nondeterminism is quarantined to the orchestrator hooks.
- **Safety** — the AI can only influence execution through three narrow, timeout-protected hook points (`before_node`, `after_node`, `on_error`). It can never corrupt the graph or the state directly.

---

## 3. The Compiler — JSON to an executable graph

`WorkflowCompiler` (`compiler/compiler.py`) does a **single-pass** compile:

```
__init__  -> build index (lookup tables, pre-scan expressions, map edges)
compile() -> validate (DAG -> creds -> config -> types) -> build LangGraph -> return CompiledStateGraph
```

### 3.1 Indexing & pre-analysis (done once, in `__init__`)

Before any validation, I build lookup tables so the rest of compilation and every node execution is fast:

- `_node_map`: `node_id -> node dict` — **O(1)** node lookup instead of scanning the list every time.
- `_label_to_id`: maps user labels / type names / raw ids to a node id (so a `{{ $node['Gmail'] }}` expression can resolve "Gmail" to the real node).
- `_outgoing`: adjacency list `node_id -> [edges]` — built once so edge traversal during graph-building is **O(1)** per node instead of filtering all edges repeatedly.
- `_node_expression_paths`: I **pre-walk** every node's config once and record the exact JSON path of every string containing `{{ }}`. At runtime I only touch those paths instead of re-scanning the whole config on every execution.
- `_loop_body_sources`: a BFS from each loop node to figure out which incoming edges are "loop-back" (body) edges vs the "first feed" edge.

**Complexity decision that matters here:** indexing is **O(V + E)** once. The naive alternative — searching the node/edge lists on demand during execution — would make each node lookup O(V) and each expression resolution O(size-of-config), turning a single run into O(V²) or worse. Pre-indexing trades a little memory (the maps) for a big drop in repeated work. The README claims compiles happen in **under ~80 ms**; that is only possible because the expensive scanning is done once and cached.

### 3.2 Multi-layered validation (fail fast, fail loud)

`compile()` runs four validators in order and **stops at the first hard error**:

1. **`validate_dag`** — the most important one.
2. `validate_credentials` — does the user actually own every credential the graph references?
3. `validate_node_configs` — does a handler exist for each node type, and is each node's config valid (delegated to that node's handler)?
4. `validate_type_compatibility` — best-effort static type check on each edge (e.g. don't feed binary into a JSON parser).

**Why validate at compile time, not at run time?** Because failing on node 7 of 10 after already sending 3 emails is unacceptable. Static validation means: if it compiles, the *structure* is sound. This is the same reason compiled languages catch type errors before you ship.

### 3.3 DAG validation — the algorithmic heart (and my "hardest problem" answer)

`validate_dag` (`compiler/validators.py`) checks:

- non-empty graph,
- every edge endpoint references a real node,
- **no illegal cycles**,
- at least one trigger (zero in-degree node) exists,
- **no orphans** (every node reachable from a trigger).

The subtle part is cycles. A normal DAG forbids all cycles — but a *loop node* is a legitimate cycle (`start -> loop -> body -> loop`). So the rule is: **a cycle is legal if and only if its back-edge points at a loop-type node** (the loop is the cycle's "header").

I detect this with an **iterative DFS** tracking three sets — `visited`, `on_stack` (current path), and the `path` list. A back-edge is found when a neighbor is already `on_stack`. If that neighbor is a loop node, it is a legal iteration; otherwise it is an infinite cycle and I reject it, reporting the exact node path so the user can see the loop.

```python
if neighbor in on_stack:                      # back-edge
    if node_types.get(neighbor) not in LOOP_NODE_TYPES:
        # illegal infinite cycle -> reject with the cycle path
```

**Complexity:** DFS cycle detection is **O(V + E)**. Orphan detection is another **O(V + E)** reachability traversal from the triggers.

**A real decision I can talk about: recursion vs iteration.** The obvious way to write DFS is recursively. I wrote it **iteratively with an explicit stack of `(node, neighbor-iterator)` frames** specifically to avoid Python's recursion limit (~1000) blowing up on a deep workflow. That is a concrete "where could this fail and how did I prevent it" story: *a 2,000-node linear workflow would crash a recursive DFS with RecursionError; the iterative version handles it in constant stack space.*

**Determinism touch:** I sort neighbors (`iter(sorted(...))`) so cycle reports and traversal order are reproducible — important for tests and for giving the user a stable error message.

### 3.4 Topological sort — stable, deterministic ordering

`topological_sort` is **Kahn's algorithm** (BFS on in-degrees) with a twist: among ready (zero-in-degree) nodes I always prefer **input order** (the order the user placed them). This makes execution order *deterministic and intuitive* instead of arbitrary. If cycles remain (legal loop-backs), the leftover nodes are appended in input order rather than dropped.

**Complexity:** **O(V + E)** with an O(V log V) sort of the ready set — negligible. The payoff is reproducibility: the same workflow always runs its parallel branches in the same order, which makes logs and tests stable.

### 3.5 Building the LangGraph & the per-node closure

Each node becomes an **async closure** (`_create_node_function`) added to a `langgraph.graph.StateGraph`. Edge wiring:

- **Normal node** → `graph.add_edge(src, tgt)`.
- **Conditional node** (`if`, `switch`, loop) → `graph.add_conditional_edges` with a router that reads a special `_handle_{node_id}` output to pick the branch.
- **Triggers** (zero in-degree) → wired from `START`.
- **Leaf nodes** (no outgoing edges) → wired to `END`.

Two bugs I fixed here are great "attention to detail" stories:

- **Multiple entry points.** The old code called `set_entry_point` in a loop, which only keeps the *last* value — so a workflow with two triggers silently dropped one. I switched to `add_edge(START, n)` for **every** zero-in-degree node, so parallel triggers all fire.
- **END in the path map.** LangGraph requires a conditional router's `path_map` to contain *every* value the router can return, including `END`. The old code let `END` fall through and it crashed at runtime. I now explicitly add `path_map[END] = END`.

### 3.6 What one node actually does at runtime (the closure body)

This is the most important 40 lines in the codebase. Each node, when LangGraph invokes it:

1. Short-circuits if the workflow is already `failed/cancelled/paused`.
2. Builds an `ExecutionContext` (failure here = fatal for the node, caught and recorded).
3. Resolves input items from upstream nodes (once, shared by hook + handler).
4. (FULL supervision only) calls the orchestrator `before_node` hook — AI can **Abort** or **Pause**.
5. Resolves `{{ expressions }}` using the pre-computed paths.
6. Merges any externally-injected input (`_input_{node_id}`).
7. Dispatches to the node's handler **with a timeout** (`asyncio.wait_for`, default 300 s).
8. Syncs mutable state back, logs start/complete with duration.
9. Loop bookkeeping (increment iteration counter).
10. On logical failure → `on_error` hook (AI can decide) or fail directly.
11. Feeds output into a downstream loop's accumulator **only if** this is a body-return edge.
12. (FULL supervision only) calls `after_node` hook.

**Where this could fail and how I prevent it:**

| Failure | Prevention in code |
|---|---|
| Handler hangs forever (bad API) | `asyncio.wait_for(handler.execute, timeout)` — per-node timeout, default 300 s |
| Handler throws | wrapped in try/except → `_fail_node` records `status="failed"`, logs, returns cleanly (no zombie) |
| Orchestrator (AI) hook hangs | `_safe_hook` wraps every hook in `asyncio.wait_for(..., 300s)` + exception isolation; a broken AI hook **cannot** stall the workflow |
| Context init fails | caught → `_fail_node`, never crashes the whole graph |
| Unknown node type | checked before dispatch → clean failure, not an exception |
| State corruption across nodes | `variables`/`loop_stats` are **copied** per node to isolate handler-local mutations; `node_outputs` shared by reference intentionally |

---

## 4. The Executor (engine) — running the graph

`ExecutionEngine.run_workflow` (`executor/engine.py`) is the deterministic worker:

```
compile() -> build initial WorkflowState -> start heartbeat -> graph.ainvoke(state) -> finalize log
```

### 4.1 Heartbeats — detecting dead workers

While the graph runs, an async context manager (`_heartbeat`) pings the DB **every 30 seconds**. A separate Celery cleanup considers an execution a "zombie" if its heartbeat is stale. 

**The decision:** 30 s is short enough that the zombie reaper (5-min cutoff) never false-positives a healthy run, but long enough to avoid hammering the DB. This is the classic *liveness vs overhead* trade-off. Without it, a crashed Celery worker would leave executions stuck in `running` forever — users would see a spinner that never resolves.

### 4.2 Crash safety — no zombie executions

`_invoke_graph` catches three cases explicitly:

- `asyncio.CancelledError` → mark `cancelled`, re-raise (user cancelled).
- any other exception → log `failed` with the message, return `FAILED`.
- normal finish → normalize `running` → `completed`, finalize the log.

**The principle:** *every* path through the engine ends with the execution record finalized. There is no way to leave a run in limbo. This is defensive design against the worst UX in a long-running system: a stuck job.

### 4.3 Why Celery? (horizontal scaling + safe timeouts)

`executor/tasks.py` runs workflows in **Celery workers** (`run_engine_worker_task`), not in the web request. Reasons:

- Workflows can run minutes — you cannot block an HTTP worker or a WebSocket for that.
- Celery gives **horizontal scaling** (add workers) and **retries** (`max_retries=3`).
- Scheduled triggers use **Celery Beat**; polling triggers (email/RSS/Sheets) use `poll_workflow_trigger`.

**A concrete distributed-systems failure I handle: double-polling.** If two beat workers on two hosts both fire the same poll, you'd process the same email twice. I take a **Redis lock** (`lock:poll:{workflow}:{node}`, `blocking=False`) — if another host holds it, this one skips. The lock has a 300 s timeout so a crashed holder can't deadlock the poll forever, and I release it in a `finally`.

### 4.4 Periodic cleanup tasks (self-healing)

- `cleanup_old_executions` — delete logs older than 30 days (node logs first, FK order).
- `cleanup_expired_hitl_requests` — time out pending approvals past their deadline (default 300 s) so a workflow doesn't wait on a human forever.
- `refresh_oauth_tokens` — proactively refresh tokens expiring in the next 10 minutes so a node never executes with a dead token.

---

## 5. Credentials & Security

`credentials/manager.py` + `credentials/models.py`.

### 5.1 Encryption at rest
- API keys, OAuth access & refresh tokens are encrypted with **Fernet (AES-128-CBC + HMAC)** — symmetric, key in `.env` (`CREDENTIAL_ENCRYPTION_KEY`), never in source.
- Stored in a `BinaryField` (avoids text-encoding corruption of ciphertext).

> Honesty note for interviews: the docs say "AES-256"; Fernet is actually AES-128-CBC with HMAC-SHA256 authentication. I'd state the real primitive if pushed — it shows I understand what the library does, not just the marketing.

### 5.2 Multi-tenant isolation (the leak I designed against)
The nightmare in a multi-user secret store is **user A's workflow using user B's credential**. I block this at **two** layers (defense in depth):
- **DB layer:** every `Credential` query filters `user_id=...`. `get_credential` looks up `id=credential_id, user_id=user_id` — a cross-user id simply returns `DoesNotExist`.
- **Compile layer:** `validate_credentials` cross-references every credential id in the graph against the *set of ids the user owns*. A workflow referencing someone else's credential fails to compile with `missing_credential`.

### 5.3 OAuth token lifecycle
`get_credential` auto-refreshes OAuth tokens with a **5-minute buffer** before expiry — so a token never dies mid-request. On refresh I **bust the cache** so I never hand back the stale token. If the refresh response is missing `access_token`, I record `last_error` and fail rather than silently caching a broken credential.

### 5.4 In-memory credential cache — bounded, TTL'd
A 5-minute TTL cache avoids decrypting on every node. **Where it could fail:** an unbounded cache is a memory leak and a stale-secret risk. Prevention: `MAX_CACHE_SIZE = 1000` with **LRU-style eviction** of oldest entries, expired entries purged first, and explicit `clear_cache(user_id)` on credential change.

### 5.5 Audit logging
Every decrypt writes a `CredentialAuditLog` (`accessed`, user, timestamp). The audit write is wrapped in try/except so a logging failure never blocks the actual workflow — *availability of the workflow beats completeness of the audit log*, a deliberate trade-off.

---

## 6. Real-time layer — WebSockets (Django Channels)

`streaming/consumers.py`: `ExecutionConsumer` streams live node progress and drives HITL.

### 6.1 Connection lifecycle (and a subtle bug I fixed)
- **Accept first, authenticate second.** I call `self.accept()` *before* checking auth, then `close(4001)` if unauthenticated. Reason: rejecting before accept makes browsers see a generic HTTP 403 and the JS `onclose` gets no useful code. Accepting first lets me send a **specific close code** (4001 = unauthenticated, 4003 = no access) the frontend can act on.
- **Per-execution authorization:** `_verify_execution_access` confirms the `ExecutionLog` belongs to this `user_id` before joining the `execution_{id}` group. Without this, anyone could subscribe to anyone's execution stream by guessing a UUID.
- **Groups:** joins `execution_{id}` (this run) and `user_{id}` (user-wide notifications). On disconnect, discards all groups — no leaked subscriptions.
- **Initial state sync:** on connect I replay the current node states from the DB, so a user who connects late (or reconnects) immediately sees where the workflow is instead of a blank canvas.

### 6.2 Human-in-the-Loop (HITL)
When a node needs approval, the orchestrator creates a `HITLRequest` (status `pending`) and pushes it over WebSocket. The user responds; `_save_hitl_response` flips it to `approved/rejected/answered` and notifies the executor group to resume. 

**Failure modes covered:**
- User never responds → `cleanup_expired_hitl_requests` times it out (default 300 s) so the workflow doesn't hang forever.
- Response for a non-pending/foreign request → `HITLRequest.objects.get(..., user_id, status='pending')` returns `DoesNotExist` → rejected. You can't approve someone else's gate.
- Flexible payloads → accepts both `{"value": "approve"}` and a bare `"approve"`.

---

## 7. Other subsystems (one line each, for breadth)
- **MCP integration** (`mcp_integration/`): Model Context Protocol client with connection pooling, a tool cache, and **secure credential injection** so an LLM tool call gets the secret without the model ever seeing it.
- **Multi-provider LLM routing**: OpenAI/Gemini/Ollama/Perplexity/OpenRouter behind one handler interface — swap providers without touching the graph.
- **Subworkflows**: a node can run another workflow. I track `nesting_depth` + `workflow_chain` to **prevent infinite recursion** (A calls B calls A).
- **RAG** (`inference/`): hierarchical (file / user / platform level) knowledge base; documents indexed async via Celery (`index_document_async`).
- **Skills/templates**: reusable workflow fragments; template metrics (success rate, avg duration) updated via a rolling average.

---

## 8. Complexity cheat-sheet (memorize for the interview)

| Operation | Complexity | Why it's fine |
|---|---|---|
| Indexing (`_build_index`) | O(V + E) | once per compile |
| DAG validation (cycles + orphans) | O(V + E) | iterative DFS + BFS reachability |
| Topological sort (Kahn) | O(V + E) | + O(V log V) stable ordering |
| Per-node lookup at runtime | O(1) | `_node_map` / `_outgoing` |
| Expression resolution per node | O(#expr-paths) | pre-scanned, not full re-scan |
| Credential fetch | O(1) amortized | TTL cache, bounded to 1000 |
| Whole compile | ~80 ms typical | because all scans are pre-computed |

---

## 9. "Tell me about..." — ready-made answers

- **Hardest technical problem** → the DAG validator: allowing loops (legal cycles) while rejecting infinite cycles, done with iterative DFS to survive deep graphs, with exact cycle reporting.
- **A system you designed** → the compiler/executor/orchestrator split (Supervisor–Worker): why separation of concerns made it testable, deterministic, and safe.
- **A hard bug** → the multiple-entry-point bug (`set_entry_point` overwriting) or the conditional-edge `END`-not-in-path-map crash. Both are "the framework's API had a sharp edge and I read the source to find it."
- **Distributed systems** → Redis lock to stop double-polling across beat workers; heartbeats + zombie reaper to detect dead workers.
- **Security** → two-layer credential isolation (DB filter + compile-time ownership check), Fernet encryption, audit log, OAuth auto-refresh with cache-busting.
- **Designing for failure** → every node call is timeout-wrapped; every engine path finalizes the execution log; AI hooks are sandboxed with timeouts so a bad model can't stall a run.

---

## 10. Likely follow-up questions (and crisp answers)

- *"Why LangGraph instead of writing your own runner?"* — I get battle-tested state-passing, conditional edges, and async invocation for free; my value-add is the compiler (validation + JSON→graph) and the supervision layer on top.
- *"What if two nodes write the same variable?"* — `variables` is copied per node then synced back, so within a node it's isolated; last-writer-wins on sync. For true parallel branches I rely on `node_outputs` keyed by node id (no collision).
- *"How do you stop runaway loops/costs?"* — `max_loop_count` validated to 1–1000 at compile time; loop iteration counter in `loop_stats`; per-node timeout; the AI `on_error` hook can abort.
- *"What happens on server restart mid-run?"* — heartbeat goes stale → zombie reaper marks it failed → user sees a clear failure, not an eternal spinner. (Honest limitation: I don't yet checkpoint-and-resume an in-flight graph; that would need LangGraph's persistence layer — a good "what I'd do next" answer.)
- *"Biggest weakness of the design?"* — no mid-graph checkpointing yet, and the static type-check is best-effort (unknown node types pass through). Both are deliberate scope cuts I can justify.

---

## 11. Testing (code-grounded — this is a real test suite)

Testing is a first-class part of AIAAS, not an afterthought. **41 test files, 348+ test functions**, run under **pytest + Django**, with a documented **multi-stage pre-merge gate** (`develop → main`) that recently passed **96/96 pytest + 93/93 Django runner + 8/8 smoke + 9/9 chaos**.

### 11.1 The testing pyramid I actually built

```
        /\        E2E (real network): real NVIDIA NIM LLM call, real WebSocket frames
       /  \       Contract audit: live responses vs OpenAPI schema (jsonschema)
      /----\      Integration: auth flow, workflow lifecycle, credentials+MCP, adversarial
     /      \     Unit: compiler/validators (no DB), credentials, streaming, nodes, orchestrator
    /--------\
```

- **Unit tests** use Django's `SimpleTestCase` (**no database**) wherever possible — the compiler and validators are pure functions over dicts, so they test in milliseconds. The **node-handler registry is mocked** (`MagicMock`) so a broken handler in `nodes/` can't take the compiler suite down with it. This is the payoff of the compiler/executor split: the hardest logic is the *most* isolated and the *easiest* to test.
- **Integration tests** (`tests/integration/`) exercise real flows end-to-end: `test_auth_flow`, `test_workflow_lifecycle`, `test_credentials_mcp`.
- **E2E tests** (`tests/e2e/`) hit a **real LLM provider** (NVIDIA NIM, `llama-3.3-nemotron-super-49b`) and a **real WebSocket** — register → login → create credential → create workflow → execute → poll to `completed`, and assert the WS `connected` + `execution.state_sync` frames arrive.

### 11.2 Adversarial testing — I attack my own compiler

The compiler is the boundary between **user-supplied JSON** and the runtime, so I wrote a suite (`test_adversarial_compiler.py`, organized as `CompilerHappy / CompilerSad / CompilerAngry`) that throws hostile graphs at the validator. The standout test directly proves a claim from §3.3:

> **`test_huge_node_count_does_not_blow_stack`** builds a **5,000-node** graph fanned out from one trigger and asserts validation completes without a `RecursionError`.

That is the *exact* test that justifies writing the DAG DFS **iteratively** instead of recursively. In an interview I can say: "I didn't just claim it scales — I have a 5,000-node adversarial test that fails if anyone reintroduces recursion." Other adversarial tests: pure cycles rejected, self-loops on non-loop nodes rejected, unknown edge endpoints caught. There are matching `test_adversarial_credentials.py` (cross-user leakage attempts) and `test_adversarial_orchestrator.py` suites.

### 11.3 Security & chaos testing
- **`orchestrator/tests_security.py`** + adversarial credential tests verify the two-layer credential isolation (a workflow referencing another user's credential must fail to compile).
- A separate **chaos / fault-injection campaign** ("faultline" / "aegis-breaker") produced reports under `test-reports/` — smoke, ws, and chaos stages (9/9 chaos) plus API fuzzing probes.

### 11.4 Contract testing (schema drift)
A **contract audit** (`tests/e2e/contract_audit.py`) validates **live API responses against the generated OpenAPI schema** (drf-spectacular) using `jsonschema`. This catches *documentation drift* — when the API and its docs diverge. The last gate found **14 real drift items and fixed all 14**; the 3 remaining are a documented framework limitation (drf-spectacular's list-action auto-wrapping), not a bug.

### 11.5 What I test for each failure mode (ties back to §3–6)

| Failure mode | Test that guards it |
|---|---|
| Infinite cycle / illegal loop | adversarial: pure cycle + self-loop rejected |
| Deep graph crashes DFS | adversarial: 5,000-node no-stack-blow test |
| Orphan / no-trigger graphs | `validate_dag` unit tests |
| Cross-user credential leak | adversarial credentials + `tests_security` |
| WebSocket auth/access | e2e `test_websocket` + streaming unit tests |
| Full execution path | e2e smoke with real LLM, polled to `completed` |
| API/doc drift | contract audit vs OpenAPI schema |

### 11.6 Honest gaps (good "what would you add" answers)
- **Coverage isn't uniform** — the compiler/credentials/MCP/nodes are heavily tested (47 tests in the compiler alone, 73 in MCP services); some peripheral apps have only smoke tests.
- **No formal coverage % gate** in CI yet, and **no property-based testing** (e.g. Hypothesis) — generating random valid/invalid graphs would be the natural next step to harden the validator further.
- The merge gate is **run as a documented manual process**, not yet a fully automated CI pipeline — automating it (GitHub Actions) is the obvious improvement.

### 11.7 How to run it (so you can speak to the workflow)
```bash
pytest                      # full suite (asyncio_mode=auto, Django settings via pytest.ini)
pytest compiler/tests.py    # just the compiler unit tests (fast, no DB)
python manage.py test       # Django test runner path
```
