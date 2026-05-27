# MLOps + LLMOps -- Worked Examples

> Production patterns you can actually copy. Provider-agnostic where reasonable.

---

## Example 1 -- Pin model revisions, log every call

```python
import time, json, logging, os, uuid
from openai import OpenAI

log = logging.getLogger("llmops")
client = OpenAI()

# Pin to specific model snapshot; never use a moving alias in prod
MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini-2024-07-18")
PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "v1.3.0")

def call_llm(messages, *, request_id=None):
    request_id = request_id or uuid.uuid4().hex
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=MODEL, messages=messages, temperature=0,
    )
    dt = (time.perf_counter() - t0) * 1000

    log.info(json.dumps({
        "event":          "llm_call",
        "request_id":     request_id,
        "model":          resp.model,
        "system_fp":      resp.system_fingerprint,
        "prompt_version": PROMPT_VERSION,
        "latency_ms":     int(dt),
        "tokens_in":      resp.usage.prompt_tokens,
        "tokens_out":     resp.usage.completion_tokens,
    }))
    return resp.choices[0].message.content
```

---

## Example 2 -- Exact-match response cache (Redis)

```python
import hashlib, json, redis

r = redis.Redis()
TTL = 60 * 60 * 24    # 1 day

def cache_key(messages, model, temperature):
    payload = json.dumps({"m": messages, "model": model, "t": temperature}, sort_keys=True)
    return "llm:" + hashlib.sha256(payload.encode()).hexdigest()

def cached_call(messages, model="gpt-4o-mini", temperature=0):
    k = cache_key(messages, model, temperature)
    hit = r.get(k)
    if hit:
        return hit.decode(), True
    out = call_llm(messages)
    r.setex(k, TTL, out)
    return out, False
```

Only cache when `temperature=0` (or you accept stale outputs).

---

## Example 3 -- Semantic cache (embeddings)

```python
import numpy as np
from openai import OpenAI

emb_client = OpenAI()
THRESHOLD = 0.92        # cosine similarity for a hit

class SemanticCache:
    def __init__(self):
        self.vecs: list[np.ndarray] = []
        self.outs: list[str] = []
        self.queries: list[str] = []

    def _embed(self, q):
        v = emb_client.embeddings.create(input=q, model="text-embedding-3-small").data[0].embedding
        v = np.asarray(v); v /= np.linalg.norm(v) + 1e-9
        return v

    def get(self, q):
        if not self.vecs: return None
        v = self._embed(q)
        sims = np.array(self.vecs) @ v
        i = int(sims.argmax())
        if sims[i] >= THRESHOLD:
            return self.outs[i]
        return None

    def put(self, q, out):
        self.vecs.append(self._embed(q))
        self.outs.append(out); self.queries.append(q)
```

Tighten THRESHOLD upward in high-stakes products; loose semantic caches will serve wrong answers.

---

## Example 4 -- Retry with exponential backoff + jitter

```python
import time, random
from openai import APIError, RateLimitError, APITimeoutError

TRANSIENT = (APIError, RateLimitError, APITimeoutError)

def with_retry(fn, *, max_attempts=4, base=1.0):
    for attempt in range(max_attempts):
        try:
            return fn()
        except TRANSIENT as e:
            if attempt == max_attempts - 1: raise
            wait = base * (2 ** attempt) + random.random()
            time.sleep(min(wait, 30))
```

Retry only on transient errors; never on a logical 4xx.

---

## Example 5 -- Fallback chain across providers

```python
import anthropic, openai

openai_client    = openai.OpenAI()
anthropic_client = anthropic.Anthropic()

def primary(messages):
    r = openai_client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0)
    return r.choices[0].message.content

def fallback(messages):
    r = anthropic_client.messages.create(
        model="claude-haiku-4-5", max_tokens=1024,
        messages=[{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"],
        system=next((m["content"] for m in messages if m["role"]=="system"), None),
    )
    return r.content[0].text

def safe_call(messages):
    try:
        return with_retry(lambda: primary(messages))
    except Exception as e:
        log.warning("primary failed; falling back", extra={"err": str(e)})
        try:
            return with_retry(lambda: fallback(messages))
        except Exception:
            return "Sorry, I am temporarily unavailable. Please try again."
```

---

## Example 6 -- Circuit breaker

```python
import time
from collections import deque

class CircuitBreaker:
    def __init__(self, failures=5, window=60, cooldown=30):
        self.failures = failures; self.window = window; self.cooldown = cooldown
        self._fails = deque(); self._open_until = 0

    def call(self, fn, *a, **kw):
        now = time.time()
        if now < self._open_until:
            raise RuntimeError("circuit open")
        try:
            out = fn(*a, **kw)
            self._fails.clear()
            return out
        except Exception:
            self._fails.append(now)
            while self._fails and self._fails[0] < now - self.window:
                self._fails.popleft()
            if len(self._fails) >= self.failures:
                self._open_until = now + self.cooldown
            raise
```

Fail fast during provider outages; protect upstream services from retry storms.

---

## Example 7 -- Per-tenant token budgets

```python
class TokenBudget:
    def __init__(self, redis_client, daily_limit_tokens):
        self.r = redis_client; self.limit = daily_limit_tokens

    def _key(self, tenant):
        return f"budget:{tenant}:{time.strftime('%Y-%m-%d')}"

    def remaining(self, tenant):
        used = int(self.r.get(self._key(tenant)) or 0)
        return max(0, self.limit - used)

    def consume(self, tenant, tokens):
        if self.remaining(tenant) < tokens:
            raise PermissionError("daily token budget exhausted")
        self.r.incrby(self._key(tenant), tokens)
        self.r.expire(self._key(tenant), 60*60*36)
```

Wire this into the LLM call wrapper so a runaway agent cannot drain a tenant's quota.

---

## Example 8 -- OpenTelemetry trace around an LLM call

```python
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

def traced_llm(messages, *, request_id):
    with tracer.start_as_current_span("llm.complete") as span:
        span.set_attribute("model", MODEL)
        span.set_attribute("prompt_version", PROMPT_VERSION)
        span.set_attribute("request_id", request_id)
        span.set_attribute("messages.count", len(messages))
        try:
            out = call_llm(messages, request_id=request_id)
            span.set_attribute("response.length", len(out))
            return out
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise
```

Spans show up alongside DB and HTTP spans -- one trace tells the full story.

---

## Example 9 -- A/B canary on candidate model

```python
import random

CANDIDATE_FRACTION = 0.05     # 5% to candidate

def routed_call(messages):
    use_candidate = random.random() < CANDIDATE_FRACTION
    model = "gpt-4o-2024-08-06" if use_candidate else MODEL
    out = call_llm_with_model(messages, model=model)
    log.info(json.dumps({
        "event":  "ab_call",
        "variant": "candidate" if use_candidate else "control",
        "model":   model,
    }))
    return out
```

Log enough metadata to compute success rate, latency, and cost per variant.

---

## Example 10 -- Daily drift report (cron)

```python
"""Compare today's golden-set outputs to last week's; alert on regression."""
import json
from pathlib import Path
import numpy as np

today = json.loads(Path("eval/today.json").read_text())
baseline = json.loads(Path("eval/baseline_7d_avg.json").read_text())

regressed = []
for key in baseline:
    diff = today[key]["pass_rate"] - baseline[key]["pass_rate"]
    if diff < -0.02:        # 2 percentage points
        regressed.append((key, diff))

if regressed:
    msg = "Eval regression detected:\n" + "\n".join(f"- {k}: {d:+.2%}" for k,d in regressed)
    alert_slack(msg)
```

Make the alert specific and actionable. "Score went down" without context wastes pager time.

---

## Example 11 -- Idempotent write tool

```python
def send_email(args: dict, *, idempotency_key: str):
    """Tool: send a single transactional email.
    Skip if we already processed this idempotency_key in the last 24h."""
    if r.exists(f"idemp:email:{idempotency_key}"):
        return {"status": "skipped", "reason": "already sent"}
    provider.send(to=args["to"], subject=args["subject"], body=args["body"])
    r.setex(f"idemp:email:{idempotency_key}", 86400, "1")
    return {"status": "sent"}
```

Pair each agent retry with a stable idempotency key. Side effects must not double-fire.

---

## Example 12 -- Cost meter (per call)

```python
PRICE = {
    "gpt-4o-mini-2024-07-18": {"in": 0.150/1e6, "out": 0.600/1e6},   # $ / token
    "gpt-4o-2024-08-06":      {"in": 2.500/1e6, "out": 10.00/1e6},
    "claude-haiku-4-5":       {"in": 1.000/1e6, "out": 5.000/1e6},
}

def usd(resp):
    p = PRICE.get(resp.model)
    if not p: return None
    return resp.usage.prompt_tokens * p["in"] + resp.usage.completion_tokens * p["out"]
```

Price book is data, not code -- review it on a schedule. Compute cost at call time; you cannot reconstruct it from logs later if you lose token counts.

---

## References
- OpenAI / Anthropic SDK docs (production usage patterns)
- "Designing Machine Learning Systems" -- Chip Huyen
- LangSmith / Langfuse / Helicone / Phoenix for LLM tracing
- See [mlops-llmops-cheatsheet.md](mlops-llmops-cheatsheet.md) for the explanatory notes
