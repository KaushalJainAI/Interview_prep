# Career Navigator — AI-Powered Job-Hunt Platform

**Interview Notes (deep dive). Code-grounded: read from the real repo at `C:\Users\91700\Desktop\Carrer Navigator`.**

> One-line pitch: *"Career Navigator automates the whole job hunt: it ingests live job postings, scores how well your resume matches each one, tailors your resume and cover letter with an LLM, and can even apply for you across three trust tiers — assist, autofill, and fully autonomous. It also has an 'Interview Grill' agent that researches the company and runs a live mock interview. The autonomous-apply path is gated by a hard human-approval check that's locked by a canary test."*

- Stack: **Django 5 + DRF + Celery + Channels** (Postgres, Redis) + **React 19 + Zustand + Tailwind** + an **MV3 browser extension** + docker-compose. **15+ Django apps.**
- It deliberately **reuses patterns** from my other two projects: AIAAS (auth/tier system, LangGraph agent, credentials vault, Channels streaming, Google OAuth) and Faultline (plan→execute→observe loop, parallel tool batching, Vault-style AuthFlow). Good talking point: *"I built a library of reusable architecture across projects."*

---

## 1. The 30-second story

A job hunt is a pipeline: discover jobs → match them to you → tailor materials → apply → prep for interviews. Each stage is a clean module here. The two hard, interesting parts:

1. **Letting an AI apply to jobs *for* you is scary.** If the agent submits an application you didn't approve, that's a real-world, irreversible mistake with your name on it. So the autonomous path has a **hard human-in-the-loop gate enforced in two independent places** (defense in depth), and a **canary test** that fails the build if anyone ever weakens it.
2. **Running many AI tools without blowing up cost or latency.** The agent batches tool calls **in parallel with a bounded semaphore**, and tools are **phase-gated** so a low-trust session literally cannot call a high-privilege tool.

---

## 2. Architecture at a glance

```
React SPA (Zustand) ──JWT/HTTPS──▶ daphne (ASGI) Django+DRF ──▶ Postgres
        ▲                              │   15 apps (accounts, jobs, matching, …)
        │  WebSocket                   │
        └──────────────◀── Channels consumers (notifications, interview)
                                       │
                              Redis (Celery broker + Channels layer)
                                       │
                        Celery workers │  ingestion (Adzuna/Greenhouse)
                        Celery beat     │  applications (Playwright autonomous submit)
                                       │  matching (rescore)
MV3 browser extension ──/api/v1/ext/──▶┘
```

**Five production processes** (docker-compose): `backend` (daphne ASGI, serves HTTP+WS), `celery` (async tasks), `celery_beat` (scheduler), `postgres`, `redis`. Five processes is a deliberate, scalable shape — the web tier never does slow work; ingestion and autonomous submits run on workers.

**15 apps, each a self-contained boundary** (own models/views/serializers/urls/tests): `accounts`, `profiles`, `resumes`, `jobs`, `ingestion`, `matching`, `notifications`, `applications`, `tailoring`, `agent`, `interview`, `credentials`, `extension_api`, `vault`, `billing`, `streaming`.

---

## 3. The match scorer (the algorithm to know cold)

`matching/scorer.py` scores a resume against a job description. It's a **weighted hybrid of two signals**:

```python
semantic = cosine(embed(resume_text), embed(jd_text))     # meaning overlap
overlap  = |resume_skills ∩ jd_skills| / |jd_skills|       # concrete skill coverage
score    = round(0.6 * semantic + 0.4 * overlap, 4)
gaps     = sorted(jd_skills − resume_skills)               # what you're missing
```

**Why two signals, weighted 60/40?**
- **Semantic cosine** catches meaning a keyword match misses ("built REST APIs" ≈ "designed web services"). But on its own it's mushy — two vaguely-techy texts look similar.
- **Skill overlap** is concrete and explainable ("JD wants Kubernetes; you don't list it"). But on its own it's brittle to wording.
- Weighting **0.6 semantic + 0.4 skill** leans on meaning for the headline number while keeping a hard, explainable skill signal. And critically, it returns **`gaps`** — the JD skills you're missing — which is *actionable* feedback, not just a score.

**Design decision — deterministic core, optional LLM rerank:** the scorer is pure and **unit-tested without an LLM**. An LLM critique is *pluggable* on top. This keeps the tests fast and the core behavior reproducible (same lesson as everywhere: quarantine nondeterminism).

**Complexity:** embedding is the cost; cosine is O(d) over the vector; skill overlap is **O(|skills|)** set intersection. All cheap and cacheable per (resume, job).

> Note: the architecture doc describes this as "BM25 + skill overlap"; the current code uses **embedding cosine + skill overlap**. Worth knowing both — the *shape* (lexical/semantic signal + explicit skill signal, weighted) is the point.

---

## 4. The agent + the HITL hard gate (the load-bearing invariant)

`agent/graph.py` runs a **plan → execute → review** loop:

```
loop while not state.halt:
    planner → list of tool calls
    _execute_tools(asyncio.gather, semaphore=8)   # parallel, bounded
        per call:
          spec = registry.get(name)
          if spec.phase > state.phase_cap:        → 'phase-gated' (blocked)
          if HITL_HARD_GATE and no approval_token → HALT (pause for approval)
          else asyncio.to_thread(spec.fn, **args)
    king_review → verdict → maybe halt
```

Three safety mechanisms, all real and all tested:

### 4.1 Phase-gated tools
Every tool is registered with a `phase` (privilege level). A session has a `phase_cap`. If a tool's phase exceeds the cap, it returns **`'phase-gated'`** and never runs. So a low-trust session **cannot** call a high-privilege tool even if the model tries. This is capability-based security for the agent.

### 4.2 Bounded parallelism (semaphore = 8)
Tool calls run concurrently via `asyncio.gather`, but capped at **8 in flight**. **Why cap it?** Unbounded concurrency would hammer external APIs (rate limits, bans), exhaust DB connections, and make cost unpredictable. A semaphore of 8 is the classic throughput-vs-safety knob — fast, but never a thundering herd.

### 4.3 The HITL hard gate (defense in depth)
The autonomous-apply path is the dangerous one. A tool marked `HITL_HARD_GATE` **cannot execute without a valid `approval_token`**. That token is issued only when the user clicks approve (`AutoApplySession.issue_approval_token()`). The gate is enforced in **two independent places**:
- in the **orchestrator** (`agent/graph.py::_execute_tools` halts and sets `paused_for_approval`), **and**
- inside the **tool itself** (`submit_application` re-verifies `approval_token` before setting status to `applied`).

> *"No path bypasses approval. The hard gate is in the orchestrator AND in the tool — defence in depth."*

### 4.4 The canary test that locks it
`agent/tests/test_graph.py` is a **canary**: it asserts a hard-gated tool **pauses without a token** and **only runs with a valid token**, that phase-gating blocks higher-phase tools, and that a basic tool runs and halts. If anyone ever weakens the gate, this test goes red. This is how you make a safety invariant *stay* true over time — you write the test that fails when it's violated.

---

## 5. Tiered auto-apply (assist / autofill / autonomous)

Three trust levels, escalating automation:
- **assist** — generates tailored materials, you apply manually.
- **autofill** — browser extension fills the form, you click submit.
- **autonomous** — server-side Playwright submits — **only after** an approval token.

The flow that guarantees consent:
```
1. create Application(tier='autonomous')
2. user clicks Approve → AutoApplySession.issue_approval_token() → token
3. agent (phase_cap=3) plans submit_application(app_id, approval_token=token)
4. tool verifies token matches → status='applied' → push 'application_submitted'
```
**No path reaches step 3 without step 2.**

---

## 6. Other subsystems (breadth, one line each)
- **Ingestion** — pluggable **adapters** (Adzuna, Greenhouse) on a Celery-beat schedule; the upsert is **idempotent**: `Company.get_or_create` + `JobPosting.update_or_create((source, external_id))`. Re-running ingestion never creates duplicate postings (see §7).
- **Interview Grill agent** — `research(company) → generate_question_bank → per-answer evaluate → summarise into a report + study plan`, streamed over `/ws/interview/<session>`.
- **Notifications** — a subscription **DSL** with `filter_json` matching, plus web-push (VAPID) and Channels broadcast; respects a per-user `stealth_domains` blacklist.
- **Credentials** — **AES-GCM** encrypted vault for provider keys (authenticated encryption — tamper-evident).
- **Accounts** — tiers, JWT, **Google OAuth**, and an **NVIDIA guest-key pool** so new users can try LLM features without their own key.
- **Frontend** — React 19 + **Zustand** stores (one per domain: auth/jobs/applications/interview), axios client with a JWT interceptor, Tailwind.

---

## 7. Where it could fail & how it's prevented

| Failure | Why dangerous | Prevention |
|---|---|---|
| **Agent applies without consent** | irreversible, your name on it | HITL hard gate in **two** places + canary test |
| **Privilege escalation by the model** | low-trust session does high-risk action | **phase-gated** tool registry (`phase > phase_cap` → blocked) |
| **Tool storm** hits external APIs | rate-limit bans, cost blowup, DB exhaustion | `asyncio.gather` capped at **semaphore=8** |
| **Duplicate job postings** on re-ingest | dirty data, duplicate alerts | **idempotent upsert** on `(source, external_id)` |
| **Provider key leak** | account compromise | AES-GCM encrypted credentials vault |
| **Slow work blocking web tier** | timeouts, bad UX | Celery workers for ingestion + Playwright submit; daphne only serves |
| **Resume parse needs an LLM in tests** | flaky, slow tests | parser is **rule-based**; LLM path is the future, injectable |

---

## 8. Complexity cheat-sheet
| Operation | Cost | Note |
|---|---|---|
| Match score | O(d) cosine + O(skills) overlap | embedding is the real cost; cacheable |
| Agent tool batch | up to 8 concurrent | bounded by semaphore |
| Ingestion upsert | O(postings) with indexed `(source, external_id)` | idempotent |
| Skill-gap diff | O(skills) set difference | actionable output |

---

## 9. "Tell me about..." — ready answers
- **Designing for safety** → the HITL hard gate enforced in two layers + a canary test that locks the invariant. This is my best "I take agent safety seriously" story.
- **A matching/ranking algorithm** → the 60/40 semantic-cosine + skill-overlap hybrid that also returns actionable gaps.
- **Concurrency** → bounded parallel tool execution (semaphore=8): why unbounded concurrency is a footgun.
- **Idempotency** → `update_or_create((source, external_id))` so re-ingestion never duplicates.
- **Reusing architecture** → deliberately copied proven patterns from AIAAS and Faultline instead of reinventing.
- **Real-time** → Channels WebSocket for live interview grilling and push notifications.

## 10. Likely follow-ups
- *"What stops the model from removing the approval check?"* → it's enforced in the orchestrator *and* the tool, and a canary test fails if either is weakened; the model can't edit the gate.
- *"Why semaphore 8, not unlimited?"* → external API rate limits, DB connection pool, predictable cost — bounded concurrency is the safe throughput knob.
- *"Cosine vs BM25 for matching?"* → semantic catches paraphrase; I pair it with explicit skill overlap for an explainable, actionable signal. BM25 is the lexical alternative and was the original plan.
- *"Phase honest about status?"* → Phase 1 (MVP) is wired and tested (131 backend tests pass); Phase 2 (autofill/autonomous prep, network graph) is partial; Phase 3 (server-side Playwright submit, portal AuthFlows, voice interview, Stripe) is pending. I'd represent it as "core works end-to-end, autonomous submit is the in-progress frontier."

---

## 11. Testing

> Code-grounded: `cd backend && pytest -q` → **131 passed**; `cd frontend && npm run test` → 5 passed; `npm run build` passes. Every app ships `tests/test_*.py`.

### 11.1 The testing pyramid
- **Backend unit tests** per app (`<app>/tests/test_*.py`) — models, serializers, services. The **matcher's deterministic core is unit-tested without an LLM**; the resume parser is rule-based specifically so tests don't need a model.
- **Agent graph tests** (`agent/tests/test_graph.py`) — the **canary** suite for the safety invariants (see §4.4): hard-gate pauses without a token, runs with a valid token, phase-gating blocks higher-phase tools, basic tool runs and halts. The fixture clears the tool registry before/after each test so suites don't leak state.
- **Frontend** — vitest + `@testing-library/react` (JSDOM); Zustand store tests under `src/stores/__tests__/`.
- **Test settings** (`config/settings/test.py`) — in-memory SQLite, **eager Celery** (tasks run synchronously so async flows are testable), fast password hasher, a default `CREDENTIAL_ENCRYPTION_KEY`. This is how you make a Celery + Channels app testable without standing up Redis.

### 11.2 What the canary protects (and why it's the most important test)
The autonomous-apply gate is a **load-bearing safety invariant**. A normal test proves a feature works; this canary proves a *dangerous thing stays impossible*. If a refactor ever lets a hard-gated tool run without an approval token, the build goes red before it ships. That's the difference between "we have a safety check" and "we can't accidentally remove our safety check."

### 11.3 Failure-mode → test map
| Failure mode | Guarding test |
|---|---|
| Apply without consent | `test_hitl_hard_gate_pauses_without_approval_token` |
| Consent works | `test_hitl_hard_gate_runs_with_valid_token` |
| Privilege escalation | `test_phase_gating_blocks_higher_phase_tool` |
| Match scoring regressions | deterministic scorer unit tests (no LLM) |
| Duplicate ingestion | upsert idempotency tests on `(source, external_id)` |

### 11.4 Honest gaps
- The browser-extension autofill/submit and server-side Playwright path (Phase 2/3) **need end-to-end validation** — that's the main untested frontier.
- No coverage % gate in CI yet; frontend coverage is light (5 tests). Adding contract tests between the React API client and DRF would prevent silent shape drift.
