"""Inject diagrams + deep dive sections across the remaining 5 folders."""
from pathlib import Path
ROOT = Path(r"C:\Users\91700\Desktop\Interview notes")

PLAN = {
"05-Backend-Django/django-full-cheatsheet.md": (
    ["diagrams/02-django-lifecycle.png", "diagrams/03-orm.png", "diagrams/04-drf-jwt.png"],
r"""

---

## 🔬 Deep dive — Django request lifecycle (in detail)

1. **WSGI/ASGI server** (gunicorn/uvicorn) accepts the HTTP request.
2. **Middleware** runs top-to-bottom on the way in: SecurityMiddleware → SessionMiddleware → AuthenticationMiddleware → CSRF → custom.
3. **URL resolver** matches against `urlpatterns`; calls the view.
4. **View** does work, possibly hits **models / ORM** which translate to SQL.
5. **Template or DRF serializer** renders the response object.
6. **Middleware** runs bottom-to-top on the way out (process_response).
7. WSGI server returns the bytes.

## 🧮 ORM essentials (memorise)

```python
# select_related: SQL JOIN (FK / O2O)
Post.objects.select_related("author")  # 1 query

# prefetch_related: separate query + Python join (M2M / reverse FK)
User.objects.prefetch_related("posts")  # 2 queries

# annotate / aggregate
from django.db.models import Count, Avg
User.objects.annotate(post_count=Count("posts"))

# F expressions (SQL-side arithmetic, no race)
from django.db.models import F
Product.objects.filter(stock__gt=0).update(stock=F("stock") - 1)

# only / defer
Post.objects.only("title", "id")    # narrow column projection

# raw SQL escape hatch
User.objects.raw("SELECT * FROM auth_user WHERE ...")
```

## ⚠️ Common pitfalls

| Pitfall | Fix |
|---------|-----|
| N+1 queries | `select_related` / `prefetch_related`; django-debug-toolbar |
| `get()` raising on missing | `filter().first()` or catch `DoesNotExist` |
| Race conditions on counters | `F` expressions or `select_for_update` |
| Migrations conflict on team branches | One person merges; squash periodically |
| `__contains` on huge tables | Add GIN index (Postgres) or full-text search |
| Forgetting `@transaction.atomic` | Multi-write views must be atomic |
| Secret leak via `DEBUG=True` in prod | Always `DEBUG=False`; configure ALLOWED_HOSTS |

## 🎤 Interview questions

1. **Sync vs async views in Django 5?** Async views can `await` IO without blocking; useful for slow upstreams. ORM is partly async via `async for` in Django 4.2+.
2. **Class-based vs function-based views?** CBV reuses logic via mixins (ListView, DetailView). FBV is explicit; pick CBV when patterns repeat.
3. **DRF ViewSet vs APIView?** ViewSet bundles list/retrieve/create/update/delete + auto-routing; APIView is a single endpoint.
4. **Pagination strategies?** Page-number (simple), cursor (consistent under inserts), limit-offset (slow on deep pages).
5. **Caching layers in Django?** Per-view (`@cache_page`), template fragment, low-level (`cache.get/set`), DB-level via `QuerySet` cache.
6. **Background tasks in Django?** Celery (Redis/RabbitMQ broker), Django-Q, or RQ. For light scheduling, `django-cron` / management commands + system cron.

## 📚 References
- Django docs (read these end-to-end once): topics/db, topics/http, topics/auth
- "Two Scoops of Django" — production patterns
- Andrew Pinkham's *Django Unleashed*
"""),

"06-Frontend/react-full-cheatsheet.md": (
    ["diagrams/01-react-lifecycle.png", "diagrams/02-state-management.png", "diagrams/03-rendering.png"],
r"""

---

## 🔬 Deep dive — render → reconcile → commit

React doesn't update the DOM directly. Each render produces a **virtual tree**; React **reconciles** (diffs against previous tree) and **commits** the minimal DOM mutations.

- Same component + same key → element is updated, state preserved.
- Different type/key → element is unmounted + remounted, state lost.
- React 18 introduces **concurrent rendering** — work can be interrupted; renders may be discarded; effects only fire on committed renders.

## 🧮 Hook rules (memorise)

1. Only call hooks at the top level of a component / custom hook.
2. Don't call hooks in loops / conditionals.
3. Custom hooks start with `use`.

Why: React identifies hooks by call order each render.

## ⚠️ Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Re-renders blowing perf | `React.memo` for components, `useMemo`/`useCallback` for values/fns passed to memoised children |
| Stale closure in `useEffect` | Include all deps; lint with eslint-plugin-react-hooks |
| Setting state from previous state without updater fn | Use `setX(prev => prev + 1)` |
| Heavy work in render path | Move to `useMemo`; offload to web worker |
| Effect runs twice in dev (strict mode) | Expected — your effect must be idempotent |
| Forms with controlled + uncontrolled mix | Pick one per field; controlled is the norm |
| Key collisions in lists | Use stable unique IDs, not array indices |

## 🎤 Interview questions

1. **Why keys in lists?** Identity across renders → reconciler reuses DOM nodes + state.
2. **What does `React.memo` do, and when does it NOT help?** Skips re-render if props shallow-equal. Doesn't help if you pass new object/array/function literals every render (use `useMemo`/`useCallback`).
3. **useEffect vs useLayoutEffect?** Layout is synchronous before paint (use for DOM measurement); Effect is after paint (use for most subscriptions / fetches).
4. **Server Components vs Client Components (Next.js)?** Server components run on the server, send HTML/RSC payload, ship zero JS. Client components hydrate. Mix carefully — "use client" boundary.
5. **Suspense?** Lets components declaratively wait for async data; fallback UI in the meantime. Pairs with React Query / Relay / Next.js `loading.tsx`.
6. **How does context cause re-renders?** Any consumer re-renders when the provider value changes; mitigate by splitting contexts or using selector libs (Zustand).

## 📚 References
- React docs (react.dev) — the new official tutorial
- Kent C. Dodds blog on hooks patterns
- "Patterns.dev" — Lydia Hallie
"""),

"07-Deployment/deployment-full-cheatsheet.md": (
    ["diagrams/01-docker-vs-vm.svg", "diagrams/02-docker-layers.png", "diagrams/03-k8s-core.png", "diagrams/04-cicd.png"],
r"""

---

## 🔬 Deep dive — containers vs VMs

Containers share the host kernel; VMs virtualise hardware → each has its own kernel. Containers boot in ms, share I/O, isolate via cgroups + namespaces. VMs offer stronger isolation (security boundary).

## 🐳 Docker — the cheat moves

```dockerfile
# Reproducible, cache-friendly, small
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER 1000        # don't run as root
ENV PYTHONUNBUFFERED=1
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health || exit 1
CMD ["gunicorn","app:app","--bind","0.0.0.0:8000","--workers","4"]
```

## ☸️ Kubernetes — minimum to know

| Object | Role |
|--------|------|
| Pod | smallest deploy unit (1+ containers) |
| Deployment | declarative rollout + history |
| Service | stable virtual IP/DNS for pods |
| Ingress | external HTTP routing + TLS |
| ConfigMap / Secret | runtime configuration |
| HPA | horizontal pod autoscaler (CPU / custom metrics) |
| Job / CronJob | one-shot / scheduled work |
| StatefulSet | stable identity for DBs / queues |

## ⚠️ Common pitfalls

| Pitfall | Fix |
|---------|-----|
| `:latest` tag pinning | Always pin to SHA / version |
| Secrets in image | Use Secret manager + env injection |
| Image bloat (1GB+ Python image) | Multi-stage build, alpine/slim base |
| Single replica = SPOF | min 2 replicas + PDB |
| No resource requests/limits | OOMKilled pods; noisy neighbour |
| Healthcheck = TCP only | Use `/health` endpoint validating dependencies |
| Liveness probe too eager | Restarts loop; use Startup probe for slow boot |

## 🚀 CI/CD pattern

```
PR → lint + test → build image + tag commit SHA → push registry
   → deploy staging → E2E → manual approve → deploy prod
   → smoke + monitor → auto rollback on SLO breach
```

GitHub Actions example:
```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: pytest --cov
```

## 🎤 Interview questions

1. **Blue-green vs canary deploy?** Blue-green: switch all traffic at once. Canary: send small % to new version, ramp.
2. **What's a sidecar?** Helper container in the same Pod (logging, mesh proxy, init).
3. **PVC vs ConfigMap?** PVC for persistent disk (DBs); ConfigMap for non-secret config.
4. **How do you handle stateful workloads on K8s?** StatefulSet + stable PVC; or external managed service (RDS / Spanner).
5. **Service mesh — when do you need one?** Many services + need mTLS / retries / tracing / canarying at the network layer. Adds operational cost.
6. **Container vs Lambda for small APIs?** Lambda: zero-ops, scales to 0, cold starts. Containers: predictable latency, more control, idle cost.

## 📚 References
- *Docker Deep Dive* (Nigel Poulton)
- *Kubernetes in Action* (Marko Lukša)
- "12-factor app" — Heroku's manifesto, still relevant
"""),

"08-VCS-Testing/git-testing-cheatsheet.md": (
    ["diagrams/01-git-branching.png", "diagrams/02-test-pyramid.png"],
r"""

---

## 🔬 Deep dive — what git actually stores

Git is a **content-addressable filesystem**: every file is hashed (SHA-1/SHA-256) into the `.git/objects` store. Four object types:
- **blob** — file contents
- **tree** — directory listing (filename → blob hash)
- **commit** — snapshot pointer (tree + parent + author + msg)
- **tag** — annotated tag with message + signature

A branch is just a movable pointer to a commit hash. Knowing this makes rebases, cherry-picks and reflog recovery intuitive.

## 🧮 Commands to memorise

```bash
# Inspect
git log --oneline --graph --decorate --all
git reflog                          # safety net for "lost" commits
git diff --stat HEAD~3..HEAD        # what changed in last 3 commits

# Branch ops
git switch -c feature/x             # new branch
git rebase -i main                  # interactive: squash, edit, reorder
git cherry-pick <hash>              # bring one commit elsewhere
git revert <hash>                   # safe undo of a public commit

# Recovery
git checkout <hash> -- path/file    # restore one file
git reset --hard ORIG_HEAD          # undo last destructive op
git fsck --lost-found               # find dangling commits
```

## ⚠️ Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Force-push to main | Never. Use `--force-with-lease` on personal branches only |
| Committed secrets | `git filter-repo` / BFG; rotate secret immediately |
| Huge binary in history | Track via Git LFS from the start |
| Merge conflict mishandled | Re-do via `git checkout --ours/theirs path` |
| Mixed line endings on Windows | `core.autocrlf=input`; `.gitattributes` |

## 🧪 Testing pyramid

- **Unit (≥ 80%)**: pure functions, small, fast (<10ms each).
- **Integration (~15%)**: DB / external service mocked or testcontainers.
- **E2E (~5%)**: full app via real browser (Playwright / Cypress).

Plus property-based testing (Hypothesis) and contract tests for service boundaries.

## ⚠️ Testing pitfalls

| Pitfall | Fix |
|---------|-----|
| Slow tests (>10s) | Profile fixtures; parallelise; cut DB I/O |
| Flaky E2E | Wait for elements explicitly, not `sleep`; isolate state |
| Snapshot tests overfit | Use only for stable serialisable output |
| Mocking too deep | Mock at boundary (DB, HTTP); not internals |
| Tests share state | Use fresh fixtures; `pytest --random-order` |
| Coverage as the only metric | Pair with mutation testing (mutmut) |

## 🎤 Interview questions

1. **Merge vs rebase?** Merge preserves history with merge commit; rebase produces linear history but rewrites commits — never rebase shared branches.
2. **TDD — red/green/refactor — does it work in practice?** Best for libraries & algorithmic code; less useful for exploratory UI work.
3. **What's a test double — mock, stub, spy, fake?** Stub returns canned data; mock records calls + verifies; spy wraps real impl; fake is a working lightweight impl.
4. **How do you test concurrent code?** Property-based + race detector + deterministic schedulers (Loom/Stress).
5. **Mutation testing concept?** Introduce small bugs; check if tests catch them. Reveals weak assertions.

## 📚 References
- *Pro Git* (Chacon & Straub) — free online
- Martin Fowler: "Test Pyramid"
- "Working Effectively with Legacy Code" — Michael Feathers
"""),

"09-System-Design-Security/system-design-cheatsheet.md": (
    ["diagrams/06-caching.png", "diagrams/07-db-replication.png"],
r"""

---

## 🔬 Deep dive — the system-design framework

The interviewer wants to see structured thinking, not memorised topology. Standard playbook:

1. **Clarify scope & scale** — DAU, QPS, data volume, geographic distribution.
2. **Functional requirements** — explicit, prioritised user stories.
3. **Non-functional** — availability, latency, consistency, durability.
4. **Capacity estimate** — back-of-envelope (e.g. 100M DAU × 10 reqs ≈ 10k QPS).
5. **API design** — REST/gRPC endpoints, request/response shapes.
6. **Data model** — entities, indexes, sharding key.
7. **High-level architecture** — client → LB → service → cache → DB.
8. **Deep dive on 1-2 components** — usually the one with hardest scale.
9. **Trade-offs** — explicitly say what you're giving up.
10. **Bottlenecks & scaling** — read replicas, sharding, CDN, async queues.

## 📐 Latency / throughput numbers you should know

| Operation | Order of magnitude |
|-----------|-------------------|
| L1 cache | 1 ns |
| RAM access | 100 ns |
| SSD random read | 100 μs |
| Network round-trip in DC | 0.5 ms |
| HDD seek | 10 ms |
| Cross-continent RTT | ~150 ms |
| Read 1 MB from SSD | 1 ms |
| Read 1 MB from network | 10 ms |

## 🧮 Capacity math sketches

- 1M DAU × 10 actions = **10M actions/day** ≈ **115 actions/sec avg**, peak ~5× = **600 QPS**.
- Each action 1KB metadata → **10 GB/day** → **3.6 TB/year** before replication.
- Each user 10MB media → **10 TB total** (cap planning).

## 🚀 Scale patterns

| Bottleneck | Fix |
|------------|-----|
| Read-heavy DB | Read replicas + cache |
| Write-heavy DB | Shard by user_id / hash |
| Hot key | Replicate to N partitions, write to random |
| Cross-region latency | CDN for static, edge functions for compute |
| Sync RPC fan-out | Convert to async queue (Kafka / SQS) |
| Tight consistency required | Single-leader writes (Spanner / Cockroach) |
| Auth bottleneck | Stateless JWT or distributed session cache |

## 🎤 Interview questions

1. **CAP theorem in practice?** During partition, choose consistency (banking) or availability (social feed); modern systems often surface tunable consistency per query.
2. **Hot key problem and mitigations?** Random-write replicas, request coalescing, client-side caching, write-ahead log shedding.
3. **Idempotency on retries?** Idempotency key on writes; dedupe table; client retries safe by design.
4. **Backpressure?** Token bucket / leaky bucket; bounded queues; reject vs degrade.
5. **Design Twitter feed — push vs pull?** Push (fan-out on write) for normal users, pull (fan-in on read) for celebrities — hybrid.

## 📚 References
- *Designing Data-Intensive Applications* (Kleppmann) — must-read
- "The Twelve-Factor App"
- Donne Martin's system-design-primer (GitHub)
"""),

"09-System-Design-Security/security-cheatsheet.md": (
    ["diagrams/03-jwt-auth-flow.svg", "diagrams/04-cors-preflight.svg", "diagrams/05-tls-handshake.svg", "diagrams/08-owasp-top10.png"],
r"""

---

## 🔬 Deep dive — the threat-model mindset

A threat model answers four questions:
1. **What are we building?** (data flow diagram with trust boundaries)
2. **What can go wrong?** (STRIDE: Spoof / Tamper / Repudiate / Info-leak / DoS / Elevate)
3. **What are we doing about it?** (controls)
4. **Did we do a good job?** (test, review, audit)

Do this *before* coding — it's cheaper than fixing later.

## 🔐 Crypto primitives — when to use what

| Primitive | Use |
|-----------|-----|
| Hash (SHA-256) | Integrity, content addressing — NEVER passwords directly |
| HMAC | Message auth — `HMAC-SHA256(key, msg)` |
| Password hashing | Argon2id / scrypt / bcrypt — slow + salted |
| Symmetric encryption | AES-256-GCM (authenticated) |
| Asymmetric | RSA / Ed25519 / X25519 |
| Signatures | Ed25519 |
| KDF | HKDF / PBKDF2 / Argon2 |
| TLS | 1.3 only; auto-rotate certs (LetsEncrypt) |
| JWT | HS256 (shared secret) or RS256 (public key) — beware "none" alg |

## ⚠️ Common security pitfalls

| Pitfall | Fix |
|---------|-----|
| String-concat SQL | Parameterise; ORM with proper escaping |
| MD5/SHA1 for passwords | Use Argon2id with sane params |
| Comparing tokens with `==` | Use `hmac.compare_digest` (constant-time) |
| Logging tokens / PII | Redact in middleware |
| Permissive CORS (`*` + credentials) | List specific origins; deny credentials with `*` |
| Trusting `User-Agent` / `X-Forwarded-For` | Validate at proxy level |
| Missing rate limit on login | Lockout / progressive delay / captcha |
| Permissive S3 buckets | Block public access; bucket policy review |
| Outdated dependencies | Dependabot + Snyk in CI |

## 🔑 Auth tactics

- **Sessions** — server-side store, HttpOnly + Secure + SameSite cookie. Easy revocation.
- **JWT** — stateless; great for distributed; harder to revoke (short TTL + refresh).
- **OAuth2** — delegated auth; PKCE for SPAs; refresh token rotation.
- **MFA** — TOTP, WebAuthn (passkeys preferred).
- **Zero-trust** — assume the network is hostile; authenticate every request.

## 🎤 Interview questions

1. **CSRF vs XSS?** CSRF tricks a logged-in browser to send a request. XSS injects script into a page. Defences differ: CSRF tokens / SameSite for CSRF; CSP + output encoding for XSS.
2. **How does TLS 1.3 differ from 1.2?** Faster handshake (1-RTT, 0-RTT for resumption), modern ciphers only, removed RSA key exchange (forward secrecy default).
3. **Hashing vs encryption for passwords?** Hash — encryption is reversible; we should never be able to recover passwords.
4. **What's a SSRF and how to prevent it?** Server fetches a URL the user controls and hits internal targets (metadata endpoints, internal services). Whitelist domains; block private IP ranges; use a separate egress proxy.
5. **Why HttpOnly + Secure cookies?** HttpOnly hides from JS (XSS can't steal); Secure restricts to HTTPS.
6. **Difference between authentication and authorisation?** Authn proves who you are; authz decides what you can do.

## 📚 References
- OWASP Top 10 + Cheat Sheets
- *Cryptography Engineering* (Ferguson, Schneier, Kohno)
- "Designing Secure Software" (Loren Kohnfelder)
"""),
}

for rel, (imgs, extra) in PLAN.items():
    p = ROOT / rel
    if not p.exists(): print("MISSING:", rel); continue
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
    print("expanded:", rel)
