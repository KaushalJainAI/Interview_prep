# FitGenius AI — Context-Aware Hybrid Health Recommender

**Interview Notes (deep dive). Code-grounded: read from the real repo at `C:\Users\91700\Desktop\RS\Project`.**

> One-line pitch: *"FitGenius is a health recommender that builds you a personalized diet + workout plan. The clever part is it's medically safe by design — it won't recommend something dangerous for your condition (e.g. a high-sugar diet to a diabetic). It's a cascade: medical safety first, then content-based templates, then K-nearest-neighbor collaborative filtering, then context adjustments from your daily check-in, then an LLM/RAG layer that explains the plan in plain language."*

- Stack: **Offline ML pipeline** (4 datasets → 18-feature schema → KNN/SVD → `.pkl`) + **Django/DRF backend** (loads models into memory on startup) + **React SPA**. Final-year research/capstone project.

---

## 1. The 30-second story

Most fitness apps ask your age and BMI and hand you a generic plan. Two things are wrong with that:
1. **They ignore medical context.** A purely "people like you also did this" (collaborative) system can recommend something *actively harmful* to someone with diabetes or hypertension, just because similar users liked it. That's the cold-start + safety failure I designed against.
2. **They ignore daily context.** Whether you slept badly or barely moved today should change today's workout intensity.

So FitGenius is a **cascade recommender**: **medical safety is a hard gate that overrides everything**, and personalization (similar users, your preferences, today's check-in) is layered on top of a safe base. The plan is then **explained** by an LLM grounded in health literature (RAG) so the user understands *why*.

---

## 2. Architecture: three components

```
┌─ OFFLINE (notebooks/train_model.py) ─────────────┐
│ 4 health datasets → clean & merge → 18-feature   │
│ schema → train KNN + SVD → export .pkl + preproc │
└───────────────────────┬──────────────────────────┘
                        │ loaded ONCE on startup (apps.py)
                        ▼
┌─ DJANGO/DRF BACKEND ──────────────────────────────┐
│ models held in memory → RecommendationEngine.     │
│ generate(profile, checkin) → JSON plan            │
└───────────────────────┬──────────────────────────┘
                        ▼
              React SPA (onboarding wizard + dashboard)
```

**The key backend decision: load `.pkl` models into memory once at startup** (in `apps.py`'s `RecommendationsConfig`), not per request. **Why?** Loading a model from disk + deserializing is slow (tens-to-hundreds of ms). Doing it on every request would dominate latency. Loading once at boot makes each recommendation a fast in-memory inference. The trade-off: higher baseline memory and a slower cold start — the right call for a read-heavy inference API.

---

## 3. The cascade engine (the thing to know cold)

`RecommendationEngine.generate(profile, checkin)` runs steps in a deliberate order. **Order is the whole design** — safety brackets everything:

```
0. assess_medical_safety(profile, checkin)
       └─ if blocks_plan → return build_safety_only_recommendation()   ← HARD STOP
1. Content-based template selection  (WORKOUT_TEMPLATES[goal][equipment],
                                       DIET_TEMPLATES[goal][diet_pref])
2. Calorie estimation                (Mifflin–St Jeor BMR × activity × goal)
3. Static medical health notes
4. KNN top-K aggregation (k=20)      (similarity-weighted votes)
5. Rank top-3 diet / exercise candidates
6. Collaborative filtering           (real similar users ⊕ synthetic CF)
7. Re-ranker                         (CF scores + user preference memory)
8. Context adjustments from check-in (sleep / activity today)
9. Experience-level tuning           (beginner ↓ sets/reps, advanced ↑)
10. Truncate to days-per-week
11. apply_medical_safety_filter()    ← SAFETY AGAIN, must override everything
12. RAG + LLM explanation
13. Build human-readable explanation + confidence
```

### 3.1 Medical safety is a *bracket*, not a step (the headline design)
Notice safety appears **twice**: an `assess_medical_safety` **hard stop at the very start** (step 0), and `apply_medical_safety_filter` **at the very end** (step 11) that strips any unsafe exercise the personalization layers may have re-introduced. This is **defense in depth** — exactly like the credential gate in AIAAS and the HITL gate in Career Navigator. 

**Why bracket it?** Because steps 4–8 (collaborative filtering, re-ranking, context) can pull in items from *similar users* who don't share your medical constraints. If safety were only checked at the start, a later layer could re-introduce something harmful. Checking again at the end guarantees the final plan is safe no matter what the middle did. *"Safety is the outer layer; personalization happens inside it."*

### 3.2 Content-based templates (the safe base)
`WORKOUT_TEMPLATES[goal][equipment]` and `DIET_TEMPLATES[goal][diet_pref]` give a hand-authored, sensible base plan keyed on goal (muscle_gain / weight_loss / endurance / maintenance) and what equipment/diet the user has. **Why templates?** They solve **cold-start** — even a brand-new user with no similar profiles gets a coherent, safe plan immediately. The ML layers *refine* this base; they don't start from nothing.

### 3.3 KNN collaborative filtering (the "people like you" signal)
`knn_top_k_aggregate(profile, k=20)`:
- Convert the profile to an **18-feature vector** (`profile_to_vector`) — age, BMI, activity, goal, conditions (diabetes/hypertension as 0/1), sleep, etc.
- Transform via the saved **preprocessor**, find **k=20** nearest neighbors with the saved KNN model.
- **Cosine similarity = 1 − distance**; keep only matches with **similarity > 0.3** (a quality threshold so weak matches don't pollute votes).
- **Similarity-weighted voting**: each neighbor's diet/exercise gets a vote equal to its similarity, then `select_top_ranked` takes the top-3.

**Why similarity-weighted votes, not a plain majority?** A neighbor 0.9 similar to you should count far more than one that's 0.31 similar. Weighting by similarity makes a closer match matter more — a simple, defensible ranking choice.

### 3.4 Synthetic CF for cold-start (a neat trick)
Real collaborative filtering dies when there aren't enough users yet (the cold-start problem). So CF scores are a **blend**: `merge_cf_scores((1.0, real_scores), (0.35, synthetic_scores))`. Real users dominate (weight 1.0); **synthetic** scores (weight 0.35) fill the gap when real data is sparse. As the platform gets real users, the real signal naturally outweighs the synthetic.

### 3.5 Calorie math (deterministic, not ML)
`estimate_daily_calories` uses the **Mifflin–St Jeor** BMR equation × an activity multiplier (1.2–1.9) + a goal adjustment (−500 for weight loss, +300 muscle gain, etc.), then a macro split by goal. **Why a formula, not a model?** It's an established clinical equation — accurate, explainable, and you'd never want a black-box model guessing calorie targets when a validated formula exists. (Know your tools: use ML where patterns are fuzzy, use formulas where the science is settled.)

---

## 4. The RAG / LLM explanation layer (be honest about this)

`_generate_rag_insights` produces the conversational "here's why I chose this" text. **Important honesty point for interviews:**

- The **concept** is RAG: retrieve relevant health-literature chunks, then have an LLM weave them into a personalized explanation.
- The **current implementation** in `recommendations/engine.py` is a **rule-based simulation** of RAG: a small hard-coded `knowledge_base` of literature chunks, selected by **explicit `if` rules** (e.g. `if profile.diabetes: add the low-GI chunk`), then assembled into a templated message — *not* an embedding similarity search.
- The repo **does** contain a real embedding model (`Qwen3-Embedding-0.6B` under `chat/`) and a chat knowledge base, so true vector RAG exists elsewhere in the system / is the upgrade path.

**How I'd say it:** *"The recommendation explainer is a rule-based RAG today — semantic chunk selection by clinical rules, which is actually safer and fully predictable for medical content. The infrastructure for embedding-based retrieval (Qwen3 embeddings, a chunked KB) is in the codebase; swapping the rule-based selector for vector similarity is the next step."* That's honest, shows I know the difference, and frames the rule-based version as a *defensible choice* for safety-critical text rather than a shortcut.

---

## 5. Where it could fail & how it's prevented

| Failure | Why dangerous | Prevention in code |
|---|---|---|
| **Harmful recommendation** (e.g. high-sugar to diabetic) | health risk — the whole point | safety **bracket**: `assess_medical_safety` hard-stop at start **and** `apply_medical_safety_filter` at end |
| **KNN model errors / missing model** | 500 error, no plan | `knn_top_k_aggregate` wrapped in try/except → falls back to template-based plan with a clear explanation |
| **Cold-start** (no similar users) | empty or bad recs | content-based templates as the base + synthetic CF blend (0.35) |
| **Missing/invalid profile fields** | crashes, garbage vector | defaults in `profile_to_vector` (e.g. BMI→24.2) and `estimate_daily_calories` (weight/height/age fallbacks) |
| **Weak similarity matches polluting votes** | irrelevant recs | similarity **> 0.3** threshold before a neighbor votes |
| **Slow per-request model load** | high latency | models loaded **once** into memory at startup |
| **Over-personalization re-introduces unsafe items** | safety regression | final medical filter overrides all personalization layers |

---

## 6. Complexity & evaluation

**Complexity:**
- Feature vector: fixed **18 dims** → O(1) to build.
- KNN `kneighbors`: ~**O(N·D)** brute-force (or O(log N) with a tree index) over N reference rows; k=20. Done once per recommendation.
- Voting/ranking: O(k) to tally + O(m log m) to sort candidates — tiny.
- Inference is fast because the model is **in memory** (no disk/deserialize cost per call).

**Evaluation (from the proposal/validation plan):** RMSE for the SVD matrix-factorization component; **Precision/Recall/F-score on Top-K** recommendation; **intra-list diversity** (Jaccard) + catalog coverage to avoid a filter bubble; and RAG factuality vs the retrieved source chunks. **Why diversity matters:** a recommender that only ever suggests the same popular plan traps users — measuring intra-list diversity catches that.

---

## 7. "Tell me about..." — ready answers
- **A system you designed** → the cascade recommender with medical safety as an outer bracket around the personalization layers.
- **Designing for safety** → safety checked twice (start hard-stop + end filter) so no personalization layer can sneak in a harmful item — defense in depth.
- **Cold-start** → content-based templates as a safe base + synthetic-CF blend so new users still get good recs.
- **Hybrid recommenders** → content-based + KNN collaborative + re-ranker + context, and *why* each layer exists.
- **When NOT to use ML** → Mifflin–St Jeor for calories: use the validated formula, not a black box.
- **Honesty / RAG** → the explainer is rule-based RAG today; real embedding infra (Qwen3) is in the repo as the upgrade path.

## 8. Likely follow-ups
- *"Why KNN over a neural recommender?"* → interpretable, no big training infra, works on a modest dataset, and "nearest similar profiles" is a naturally explainable story for users. A neural CF model is the scale-up path.
- *"Why cosine similarity?"* → it compares profile *shape* regardless of magnitude and maps cleanly to `1 − distance`; the >0.3 threshold filters weak matches.
- *"Is your RAG real?"* → (answer from §4 — be upfront) rule-based selection today, embedding infra present for the upgrade.
- *"How do you know it's safe?"* → safety is enforced structurally (bracketed), not as a single fallible step; and it's the first thing tested (see §9).
- *"Biggest weakness?"* → the RAG explainer is rule-based; KNN is brute-force (fine at this scale, would need ANN indexing to scale); synthetic CF weights are hand-tuned, not learned.

---

## 9. Testing

> Strategy + code-grounded. The repo has `recommendations/management/commands`, a `notebooks/evaluation_assets` folder, and evaluation charts (precision-vs-k, similarity heatmaps, hybrid-weights) — i.e. the model was evaluated, not just shipped.

### 9.1 Two kinds of testing (ML vs software)
- **Is the model good?** Offline evaluation on held-out splits: RMSE (SVD), Precision/Recall/F-score @ Top-K, intra-list diversity (Jaccard), catalog coverage. The `task2_precision_vs_k.png` / `task1_similarity_heatmaps.png` / `task3_hybrid_weights.png` artifacts are exactly this — tuning k and the hybrid weights with evidence.
- **Is the code correct?** Unit/integration tests on the engine and API.

### 9.2 The tests that matter most (safety-critical)
| What | Test |
|---|---|
| **Medical hard-stop** | a diabetic profile that should block → assert `build_safety_only_recommendation` is returned, not a normal plan |
| **Final safety filter** | inject an unsafe exercise into a plan → assert `apply_medical_safety_filter` removes it (proves the end-bracket works even if earlier layers misbehave) |
| **KNN fallback** | with the model unloaded → assert `generate()` still returns a template plan (no 500) |
| **Cold-start** | profile with no similar users → assert templates + synthetic CF still produce a coherent plan, `confidence='low'` |
| **Missing fields** | profile with null BMI/weight → assert defaults kick in, no crash |
| **Calorie math** | known profile → assert Mifflin–St Jeor output matches the hand-computed number |

### 9.3 Evaluation rigor (the research-grade discipline)
- **Tune k with evidence** (precision-vs-k curve), don't just pick 20 arbitrarily.
- **Measure diversity**, not just accuracy, to prove the system doesn't trap users in a filter bubble.
- **RAG factuality** — check the generated explanation only uses facts present in the retrieved chunks (no hallucinated medical claims). This is the safety-critical eval for the LLM layer.

### 9.4 Honest gaps
- The "RAG" explainer is rule-based, so its "factuality" is trivially safe but its flexibility is limited — true embedding-based RAG would need its own retrieval-quality eval.
- KNN is brute-force; at dataset scale-up it needs an ANN index (FAISS) and a re-eval of latency.
- Synthetic-CF weights (1.0 / 0.35) are hand-tuned — an ablation showing they beat alternatives would strengthen the claim.
