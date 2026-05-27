# LLM Evaluation -- Worked Examples

> Concrete, runnable patterns. Pair with [llm-evaluation-cheatsheet.md](llm-evaluation-cheatsheet.md) for theory.

---

## Example 1 -- JSON-schema validation as the cheapest eval

```python
from pydantic import BaseModel, ValidationError
import json

class Answer(BaseModel):
    text: str
    citations: list[str]
    confidence: float

def passes_schema(llm_output: str) -> tuple[bool, str | None]:
    try:
        Answer.model_validate_json(llm_output); return True, None
    except ValidationError as e:
        return False, str(e)[:200]

ok, err = passes_schema('{"text":"Paris","citations":["w1"],"confidence":0.9}')
assert ok, err
```

Run before any other check. If the format is wrong, downstream metrics are noise.

---

## Example 2 -- Golden-set runner

```python
# eval/run_golden.py
import json
from pathlib import Path
from app import answer
from collections import Counter

CASES = [json.loads(l) for l in Path("eval/golden/qa.jsonl").open()]

def check(case, output):
    return case["expected_keyword"].lower() in output.lower()

results = []
for c in CASES:
    out = answer(c["input"])
    results.append({"id": c["id"], "ok": check(c, out)})

n = len(results); n_ok = sum(r["ok"] for r in results)
print(f"pass_rate = {n_ok/n:.2%}  ({n_ok}/{n})")
print("failures:", [r["id"] for r in results if not r["ok"]][:10])
```

JSONL format:
```
{"id":"q1","input":"capital of France?","expected_keyword":"Paris"}
```

---

## Example 3 -- Faithfulness check via NLI

```python
from transformers import pipeline
nli = pipeline("text-classification", model="cross-encoder/nli-deberta-v3-base")

def faithful(claim: str, context: str) -> float:
    """Returns 1.0 if context entails claim, 0.0 if contradicts, in between for neutral."""
    label_scores = nli({"text": context, "text_pair": claim}, top_k=None)
    mapping = {x["label"]: x["score"] for x in label_scores}
    return mapping.get("entailment", 0.0)

ans = "The Eiffel Tower is in Paris and was built in 1889."
ctx = "Built 1889 for the World's Fair, the Eiffel Tower stands in Paris."
print(faithful(ans, ctx))   # ~ 0.9
```

Split the answer into atomic claims; faithfulness = fraction of claims entailed by context.

---

## Example 4 -- LLM-as-judge with pairwise + position randomisation

```python
import random, json
from openai import OpenAI

judge = OpenAI()

JUDGE_PROMPT = """Two assistants answer a question. Pick which is better.
Reply with JSON: {"winner": "A" | "B" | "tie", "reason": "<short>"}"""

def pairwise(question, ans1, ans2):
    # randomise to fight position bias
    swap = random.random() < 0.5
    a, b = (ans2, ans1) if swap else (ans1, ans2)
    resp = judge.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        temperature=0,
        messages=[
            {"role":"system","content": JUDGE_PROMPT},
            {"role":"user","content": f"Q: {question}\n\nA:\n{a}\n\nB:\n{b}"},
        ],
    )
    v = json.loads(resp.choices[0].message.content)
    if swap and v["winner"] in ("A","B"):
        v["winner"] = "B" if v["winner"] == "A" else "A"
    return v
```

Average across many seeds + invocations; never use a single call as a verdict.

---

## Example 5 -- Ragas-style RAG eval (manual implementation)

```python
def ctx_precision(question, contexts, answer, judge_llm) -> float:
    """Fraction of retrieved contexts that are relevant to the question."""
    relevant = 0
    for ctx in contexts:
        v = judge_llm.judge_yes_no(
            f"Is this context relevant for answering the question?\nQ: {question}\nCtx: {ctx}")
        relevant += int(v)
    return relevant / max(1, len(contexts))

def faithfulness_simple(answer, contexts, judge_llm) -> float:
    """Fraction of claims in the answer supported by the contexts."""
    claims = split_into_claims(answer)
    supported = 0
    for claim in claims:
        v = judge_llm.judge_yes_no(
            f"Is this claim supported by the contexts?\nClaim: {claim}\nContexts:\n" + "\n---\n".join(contexts))
        supported += int(v)
    return supported / max(1, len(claims))
```

Use Ragas / TruLens in real code -- they implement this with calibrated prompts.

---

## Example 6 -- Win-rate tracker over time

```python
# eval/winrate.py
import json, pathlib, datetime
LOG = pathlib.Path("eval/winrate.jsonl")

def record_run(label: str, wins: int, losses: int, ties: int):
    row = {
        "date":   datetime.date.today().isoformat(),
        "label":  label,
        "wins":   wins, "losses": losses, "ties": ties,
        "winrate": wins / max(1, wins + losses),
    }
    with LOG.open("a") as f:
        f.write(json.dumps(row) + "\n")

def trend(label):
    rows = [json.loads(l) for l in LOG.open() if json.loads(l)["label"] == label]
    return [(r["date"], r["winrate"]) for r in sorted(rows, key=lambda r: r["date"])]
```

Plot this in your dashboard. Win-rate vs the previous release is the headline metric.

---

## Example 7 -- Inter-rater agreement (Cohen's kappa)

```python
from sklearn.metrics import cohen_kappa_score

# rater_a, rater_b are lists of labels for the same items
rater_a = ["good", "good", "bad", "good", "bad"]
rater_b = ["good", "bad",  "bad", "good", "bad"]
kappa = cohen_kappa_score(rater_a, rater_b)
print(f"kappa = {kappa:.2f}")    # > 0.6 = good agreement
```

Compute quarterly across your human review queue. If kappa drops, recalibrate reviewers before trusting their scores.

---

## Example 8 -- Slice metrics by tag

```python
def report(results: list[dict], by: str):
    from collections import defaultdict
    buckets = defaultdict(lambda: [0, 0])
    for r in results:
        for tag in r.get(by, []):
            buckets[tag][0] += int(r["ok"])
            buckets[tag][1] += 1
    return {k: ok / n for k, (ok, n) in buckets.items()}

# golden case rows include "tags": ["multilingual","numeric","sarcasm"]
rates = report(results, by="tags")
for tag, rate in sorted(rates.items(), key=lambda x: x[1]):
    print(f"{tag:20s} {rate:.0%}")
```

Aggregate scores hide regressions inside slices. Track per-tag pass rate.

---

## Example 9 -- Latency + cost benchmark

```python
import time, json
from app import answer

def bench(cases, n=3):
    out = []
    for c in cases:
        times = []
        for _ in range(n):
            t0 = time.perf_counter(); answer(c["input"]); times.append(time.perf_counter() - t0)
        times.sort()
        out.append({"id": c["id"], "p50": times[len(times)//2], "p95": times[int(len(times)*0.95)]})
    return out

print(json.dumps(bench(CASES), indent=2))
```

In CI, fail the build if p95 latency regresses by more than X% vs baseline.

---

## Example 10 -- Regression diff vs a baseline release

```python
# eval/diff_releases.py
import json, sys
A = {r["id"]: r for r in json.load(open(sys.argv[1]))}
B = {r["id"]: r for r in json.load(open(sys.argv[2]))}

newly_failed = [k for k in A if A[k]["ok"] and k in B and not B[k]["ok"]]
newly_passed = [k for k in A if not A[k]["ok"] and k in B and B[k]["ok"]]

print("regressed:", newly_failed)
print("recovered:", newly_passed)
sys.exit(1 if newly_failed else 0)
```

Run as a release gate. Bisecting a regression is much easier when you have per-case results, not just an aggregate.

---

## Example 11 -- Production sampling into the review queue

```python
import random

def maybe_sample(request_id, response):
    if random.random() < 0.02:        # 2% of traffic
        write_to_review_queue({
            "request_id": request_id, "response": response,
            "sampled_at": time.time(),
        })

# in your call wrapper
out = call_llm(...)
maybe_sample(request_id, out)
return out
```

Stratify by user segment / known-failure signal -- a flat 2% misses long-tail failures.

---

## Example 12 -- Eval CI integration (pytest-friendly)

```python
import pytest, json
CASES = json.load(open("eval/golden_v3.json"))

@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_passes_schema(case, fake_llm):
    fake_llm.complete.return_value = case["expected"]
    out = run_app(case["input"], fake_llm)
    assert Answer.model_validate_json(out)
```

Pair with the test patterns in [ai-system-testing-examples.md](../08-VCS-Testing/ai-system-testing-examples.md).

---

## References

- Ragas, TruLens, deepeval, promptfoo
- "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" (Zheng et al., 2023)
- HELM, AlpacaEval, MT-Bench
- See [llm-evaluation-cheatsheet.md](llm-evaluation-cheatsheet.md) for the explanatory notes
