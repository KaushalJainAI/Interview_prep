# NGU Spices (Nidhi Masala) — Production E-commerce Platform

**Interview Notes (deep dive). Code-grounded: read from the real repo at `C:\Users\91700\Desktop\NGU`.**

> One-line pitch: *"NGU Spices is a real, live e-commerce platform I built for an actual spice brand — Django 5 REST backend, a React storefront and a separate React admin panel, JWT auth, Razorpay payments, Redis caching with signal-based invalidation, and an AI-assisted search that understands regional spice names like 'haldi' and 'manjal' using an LLM to pre-generate synonyms plus fuzzy matching. Real users, real orders, deployed on AWS."*

- Live: nidhimasala.kaushaljain.com
- Stack: **Django 5.2 + DRF + PostgreSQL (RDS) + Redis + AWS S3 + Razorpay + Docker + Nginx + EC2.**
- **The headline:** this is my "have you shipped to real users?" answer. AIAAS/Faultline show depth; NGU shows I can deliver and *operate* production software.

---

## 1. The 30-second story

A spice brand needed an online store. The CRUD (catalog, cart, orders) is routine. The two genuinely interesting problems:

1. **Search that matches how Indians actually name spices.** A customer searches "haldi" (Hindi) or "manjal" (Tamil) for turmeric. Plain keyword search returns nothing. I solved this with an **LLM that pre-generates regional/phonetic synonyms** + **fuzzy matching** at query time.
2. **Speed on cheap hardware.** Running on a small EC2 box, catalog and product pages had to be fast → **Redis caching** with careful **signal-based invalidation** so prices are never stale.

Plus the unglamorous production reality: JWT auth, Razorpay payments, S3 media, Docker/Nginx deployment, env-separated config.

---

## 2. Architecture overview

```
React storefront ─┐
                  ├─> Nginx (TLS, static, reverse proxy) ─> Django REST (DRF) ─> PostgreSQL (RDS)
React admin panel ┘                                            │
                                                               ├─> Redis (django_redis cache)
                                                               ├─> AWS S3 (product images/media)
                                                               └─> Razorpay (payments) + COD
```

**8 Django apps**, one per bounded domain: `users` (auth/profiles), `products` (products/combos/categories + AI search + cache), `cart`, `orders`, `payments`, `reviews`, `support` (per-order chat), `admin_panel` (dashboard/coupons/policies).

**Key decisions:**
- **Separate admin panel from storefront** — two React apps (`nidhi-brand-forge` storefront, `e-commerce-command-center` admin). The store is public and speed-sensitive; the admin is private and feature-heavy. Splitting keeps the public bundle small and means an admin bug can't take down the store.
- **DRF, not plain Django views** — serializers give validation + clean JSON; viewsets give consistent REST; built-in permissions/throttling.
- **Stateless API + JWT** — no server-side sessions, so the API scales horizontally and both React apps talk to it like any SPA.

---

## 3. Authentication & authorization
- **JWT** (access + refresh; `/api/auth/token/refresh/`). Access token short-lived; refresh to renew without re-login.
- **Permission tiers**: products/categories are public-read / admin-write; cart & orders require authentication; dashboard/coupons are admin-only.
- Passwords hashed by Django (PBKDF2), never stored plaintext.

| Risk | Prevention |
|---|---|
| Stolen access token used forever | short access-token lifetime + refresh rotation |
| Customer hitting admin endpoints | DRF permission classes check role per view |
| Brute-force login | throttling on auth endpoints |
| Passwords leaked from DB | PBKDF2 hashing |

---

## 4. AI-assisted spice search (the standout feature — fully code-grounded)

**The problem:** spices have many regional/phonetic names. Turmeric = haldi (Hindi) = manjal (Tamil) = pasupu (Telugu). Exact-match SQL `LIKE` fails completely; so do typos like "halid".

**The real implementation** (`products/recommendations.py`, the `SpiceSearchEngine`):

1. **LLM synonym generation** — uses **Perplexity AI's `sonar` model** (via its OpenAI-compatible Chat API) wrapped with **LangChain** (prompt + JSON output parser) to generate 25+ regional, phonetic, and translated synonyms for each product.
2. **Storage** — synonyms are saved in dedicated `ProductSearchKB` / `ProductComboSearchKB` models as PostgreSQL **`JSONField`** arrays.
3. **Query-time matching** — a user query runs through **FuzzyWuzzy `process.extract` (token-set ratio)** against those stored synonym arrays. So "haldi", "pasupu", or a misspelling all resolve to "turmeric powder" instantly.

### 4.1 The decision that matters: *when* to do the expensive LLM work
Generating 25+ permutations via an external LLM takes **several seconds**. Doing that **synchronously inside the `post_save` signal** when an admin saves a product would hang the admin request. My solution:

- On `post_save`, the signal delegates synonym generation to a **native Python background daemon thread** (`products/utils.py::run_in_background`) — **deliberately avoiding Celery**.
- The HTTP response returns **immediately** (no delay for the admin).
- In the background thread, `asyncio` drives LangChain's `ainvoke()` over the network; results are stored in `ProductSearchKB`; then the thread calls **`django.db.close_old_connections()`** to avoid leaking/exhausting Postgres connections.

**Why this is a good interview story (with an honest trade-off):**
- The win: the *expensive, slow, unreliable* LLM call is off the request path, and *query-time search* is just a fast fuzzy match over pre-computed data — so search stays fast and works even if the LLM API is down.
- **Why threads instead of Celery?** To avoid running a broker + worker for a single async task on a small box. The honest cost: a background thread has **no retry/durability** (if the process dies mid-generation the synonyms just don't get created until the next save) and you **must** manage DB connections manually (hence `close_old_connections()`). I'd say in an interview: *"For one fire-and-forget task, a thread was the pragmatic choice; if this grew to many task types or needed retries, I'd move it to Celery — which is exactly what I did do in AIAAS."*

**Complexity:** FuzzyWuzzy token-set ratio is ~O(n·m) per candidate comparison (query length × candidate length). It stays cheap because I match against a bounded synonym set, not the whole catalog text.

**Failure modes:**
| Failure | Prevention |
|---|---|
| LLM API down at save time | synonyms generated async; if it fails, search still works on existing data; regenerates next save |
| Fuzzy match too loose (junk results) | token-set-ratio score threshold filters weak matches |
| Background thread leaks DB connections | explicit `close_old_connections()` after the work |
| No match at all | graceful "no results", never a 500 |

> "Why not vector embeddings?" — semantic embeddings + a vector DB is the scale-up path. For this catalog, LLM-generated synonyms + fuzzy matching delivers the regional-name win with far less infrastructure. A deliberate cost/complexity trade-off.

---

## 5. Caching strategy (Redis) — the performance story (code-grounded)

`products/cache.py` + `products/signals.py`.

**Setup:** `django_redis` as the cache backend, with a **graceful fallback to `LocMemCache`** if `REDIS_URL` isn't set (so local dev needs no Redis). Default TTL 300s.

**Namespaced keys** — keys are prefixed by entity (`products:`, `categories:`, `combos:`, `sections:`) via `make_cache_key()`, which also **md5-hashes** keys longer than 200 chars to keep them tidy. Namespacing lets me invalidate one entity type without nuking the whole cache.

**Tiered TTLs** — Short 60s (volatile), Medium 300s (product/combo lists — default), Long 900s (categories — rarely change). Matching TTL to volatility is the core caching judgement call.

**Signal-based invalidation** — Django `post_save`/`post_delete` signals in `signals.py` purge the right namespace the instant data changes:

| Action | Invalidated |
|---|---|
| Save `Product` | `products:*` + `sections:*` (and refreshes AI synonyms in a thread) |
| Save `ProductCombo` | `combos:*` + `sections:*` |
| Save `Category` | `categories:*` |
| Save `ProductSection` | `sections:*` |

Redis invalidation uses **`cache.delete_pattern('ngu:<prefix>:*')`** (pattern delete).

### Why signal-based, not just TTL (the core decision)
A pure TTL cache means after an admin edits a price, customers see the **old price** until expiry — unacceptable for commerce. Signal-based invalidation makes correctness **event-driven**: the moment the DB changes, the relevant keys die. I keep TTL as a safety net for anything a signal might miss.

| Strategy | Pro | Con | My choice |
|---|---|---|---|
| TTL only | simple | serves stale data until expiry | safety net only |
| Write-through | always fresh | every write pays cache cost | overkill |
| **Signal invalidation** | fresh after writes, cheap reads | must cover every write path | **primary** |

**Failure modes & honest limitation:**
- Stale price after edit → signal invalidation.
- **`LocMemCache` can't pattern-match** — `delete_pattern` only works on Redis; the code logs and no-ops on LocMemCache. So in local dev without Redis, prefix invalidation is a known no-op (acceptable; dev only).
- **I delete keys rather than overwrite** them on change — the next read repopulates from the DB (source of truth). Deleting is safer than writing a possibly-wrong value.
- Redis down → reads fall back to recomputing from Postgres (cache is an optimization, not a dependency).

---

## 6. Core commerce features (breadth)
Catalog, combos, cart, orders (full lifecycle + status tracking), reviews, favorites, **per-order support chat**, admin dashboard (sales stats, coupons, policies). Two worth a sentence:
- **Cart/checkout** — server-side cart; **prices and totals are recomputed server-side** at checkout (never trust client-sent prices → prevents tampering).
- **Payments** — **Razorpay** integration plus **Cash-on-Delivery**; order status is a forward-only state machine.

---

## 7. Deployment & operations (the "I can ship" story)

```
GitHub → Docker image → EC2
Nginx (TLS, static, gzip, reverse proxy) → Django (DRF)
PostgreSQL on RDS (managed backups) | Redis (cache) | S3 (media)
env-separated config: .env.local / .env.production
```

- **Docker** — reproducible builds.
- **Nginx** (`nginx.conf` / `ngu.conf`) — TLS, static, reverse proxy.
- **RDS Postgres** — managed backups / PITR; not a hand-run DB.
- **S3** — product images off the app server (`USE_S3` flag, `ap-south-1`).
- **Multiple compose files** — `docker-compose.yml` (dev), `.prod.yml`, `.test.yml` — environment separation.
- There's a `TROUBLESHOOTING_AWS_MIGRATION.md` and `DEPLOYMENT.md` — I've actually operated and migrated this in production.

**Production failure modes designed against:** EC2 reboot → containers restart, RDS separate so data survives; disk fill → media on S3; bad deploy → image rollback; secrets → env-var only, never in source.

---

## 8. "Tell me about..." — ready answers
- **Have you shipped to real users?** → Yes — NGU is live for a real spice brand with real orders and Razorpay payments.
- **A performance optimization** → Redis caching with namespaced keys + signal-based invalidation; reads from cache, correctness preserved by evicting on write.
- **A caching/consistency problem** → event-driven invalidation over TTL, and why I *delete* keys rather than update them.
- **An AI feature in production** → Perplexity-`sonar` LLM pre-generates regional/phonetic spice synonyms (off the request path in a background thread); FuzzyWuzzy matches them at query time — fast and resilient to the LLM being down.
- **A pragmatic engineering trade-off** → native background thread vs Celery for the one async task (with the honest retry/connection caveats).
- **Full-stack ownership** → storefront + admin + API + deployment + ops + a production AWS migration.

## 9. Likely follow-ups
- *"Why not Elasticsearch for search?"* → small catalog; LLM synonyms + FuzzyWuzzy + Postgres covers it without a search cluster. ES/vector search is the scale-up.
- *"Why threads not Celery?"* → one fire-and-forget task on a small box; honest cost is no retries + manual connection cleanup. Celery if it grew (as in AIAAS).
- *"JWT logout/revocation?"* → short access-token TTL limits exposure; a Redis denylist is the full instant-revocation solution.
- *"What would you improve?"* → move search to semantic embeddings + vector DB; CDN in front of S3; observability (metrics/alerts); migrate synonym generation to Celery for durability.

---

## 10. Testing

> Code-grounded: the backend ships `pytest.ini` + `conftest.py`; tests run via `pytest` / `pytest --cov=.`. Each app has `tests.py`.

**The testing pyramid for a commerce app:**
```
E2E: place an order end-to-end (cart → checkout → order created → payment)
Integration: API endpoints with a test DB (DRF APITestCase / pytest-django)
Unit: cache key/invalidation helpers, fuzzy-search matching, serializers
```

### 10.1 Backend
- **DRF endpoint tests** for auth, catalog, cart, checkout, orders — status codes, JSON shape, permissions (a customer token must be rejected from admin endpoints).
- **The money path gets the most tests:** checkout **recomputes totals server-side** — a test sends a tampered client price and asserts the server ignores it; stock re-validated at checkout.
- **Razorpay** — payment verification (signature check) tested with mocked gateway responses so tests don't hit the real API.

### 10.2 The two features that *need* dedicated tests
| Feature | Why risky | Test |
|---|---|---|
| **Cache invalidation** | stale price after edit = wrong charge | save a product → assert `invalidate_product_cache` drops `products:*`/`sections:*` and the next read is fresh; assert Redis-down falls back to Postgres |
| **AI/fuzzy search** | regional names + typos | table-driven: "haldi"/"manjal"/"halid" all resolve to turmeric via the stored synonym KB; junk query → no results (not a 500); threshold filters weak matches |

### 10.3 What I'd add
- A test that the **background synonym thread** doesn't leak DB connections (assert `close_old_connections` is called).
- Coverage gate in CI; load-test the cached endpoints to quantify the Redis win; contract tests between each React app and the DRF API so a backend shape change can't silently break the storefront or admin.
