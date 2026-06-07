# Statcon Electronics — Software Engineering Internship (Jan–Jun 2025)

**Interview Notes (deep dive).**

> Note: reconstructed from the experience profile (no source code read for this file). The ML reasoning, complexity notes, and failure modes are accurate to how these problems are correctly solved; verify project-specific numbers against your own records before quoting them.

> One-line pitch: *"At Statcon (a power-electronics company) I did two things: built ML models to predict the Remaining Useful Life of lithium-ion batteries from the NASA dataset, and built a Django REST platform for firmware security with OTP access and usage-based billing — plus real-time dashboards for a 48V power plant."*

This internship is my **"real ML + real backend, in industry"** story. It spans three pieces:
1. **RUL prediction** (time-series ML/DL) — the technical depth piece.
2. **Real-time dashboards** for a 48V SMPS power plant — the data-engineering/visualization piece.
3. **Firmware-security Django platform** — flash-count tracking, OTP access, usage-based pricing, billing.

---

## 1. Battery RUL prediction (the ML centerpiece)

**The problem in plain words:** a lithium-ion battery degrades every charge/discharge cycle. **RUL = Remaining Useful Life** = how many cycles are left before the battery is "dead" (capacity drops below a threshold, usually 70–80% of original). Predicting this lets you replace batteries before they fail.

**Data:** the **NASA Battery Dataset** — batteries cycled until end-of-life, logging voltage, current, temperature, and capacity per cycle. It's a **time-series** problem: features evolve over the life of the cell.

### 1.1 Feature engineering (where most of the value was)
Raw sensor logs aren't predictive on their own. The signal lives in **how the curves change over cycles**:
- Capacity fade per cycle (the target driver).
- Internal resistance growth (a strong degradation signal).
- Voltage/temperature curve shape per cycle (e.g. time spent in a voltage band, charge/discharge duration).
- Rolling statistics (moving averages/slopes) to capture *trend*, not just a single noisy reading.

**The decision that matters:** I spent effort on **trend/derivative features** rather than raw readings because a single cycle's voltage is noisy, but the *rate of decline* across cycles is what actually predicts failure. Good features made simple models competitive with complex ones.

### 1.2 Models & evaluation
I compared **classical ML** (e.g. Random Forest / gradient boosting on engineered features) against **deep learning** (sequence models like LSTM that consume the cycle history directly).

**The honest trade-off (great interview material):**

| Approach | Pros | Cons |
|---|---|---|
| Classical ML (RF/GBM) on engineered features | fast, interpretable, strong on tabular data, works with limited data | needs hand-built features; doesn't natively model sequence |
| LSTM / sequence model | learns temporal patterns automatically | data-hungry, slower to train, harder to interpret, overfits small datasets |

**My takeaway:** on a dataset this size, well-engineered features + a tree model often **beat or matched** the LSTM while being far cheaper and more interpretable — a concrete example of "the fancy model isn't always the right answer."

**Evaluation done right:**
- **Metric:** RMSE / MAE on predicted vs actual RUL (regression). I'd also report error *as a function of battery age*, because being wrong near end-of-life matters more.
- **Validation:** split **by battery**, not by random rows. If cycles from the same battery appear in both train and test, the model "cheats" by memorizing that cell → **data leakage**. Splitting by battery gives an honest estimate of performance on a *new* battery.

### 1.3 Where the ML could fail and how I guarded against it
| Failure | Guard |
|---|---|
| **Data leakage** (same battery in train+test) | split by battery/cell, not random rows |
| **Overfitting** (esp. LSTM on small data) | cross-validation, regularization/dropout, prefer simpler model when scores tie |
| **Distribution shift** (new battery chemistry/conditions) | report uncertainty; flag out-of-range inputs |
| **Noisy sensors** | rolling-average smoothing in features |
| **Optimistic metric** | report error near end-of-life separately, not just global RMSE |

**Complexity note:** tree-model inference is effectively **O(trees × depth)** — microseconds, fine for a dashboard. LSTM inference is **O(sequence-length × hidden²)** — heavier; another reason the lighter model was attractive for a real-time dashboard.

---

## 2. Real-time dashboards (48V SMPS power plant)

**What:** live monitoring dashboards for a 48V switched-mode power supply plant — streaming telemetry visualized for operators.

**Engineering concerns I can speak to:**
- **Ingestion cadence vs UI load** — telemetry arrives fast; the UI can't redraw on every sample. Decision: **downsample/aggregate** for the live view (e.g. rolling windows) and keep full-resolution data for drill-down. This is the same liveness-vs-overhead trade-off as AIAAS heartbeats.
- **Failure modes:** sensor dropout → show last-known + a "stale" indicator rather than a frozen chart pretending to be live; backend hiccup → dashboard degrades, doesn't crash.

---

## 3. Firmware-security Django REST platform

**What it did:** controlled and metered access to firmware operations, with:
- **Flash-count tracking** — count how many times firmware is flashed per device/customer (the billable unit).
- **OTP-based access** — one-time-password gate before sensitive firmware operations.
- **Usage-based pricing + billing** — charge by usage (flash counts), not a flat fee.

**Architecture decisions:**
- **DRF API** with per-customer accounts and roles.
- **Usage metering** — every billable action increments a counter atomically; billing reads those counters.

**Where billing/metering could fail and how to prevent it (this is the sharp part):**

| Failure | Why it's dangerous | Prevention |
|---|---|---|
| **Double counting** (a flash counted twice on retry) | over-bills the customer | **idempotency** — each operation has a unique id; counting is idempotent on that id |
| **Race condition** on the counter (two requests increment together) | lost update → under-billing | atomic DB increment (`F()` expression / `SELECT ... FOR UPDATE`), not read-modify-write in Python |
| **OTP reuse / guessing** | unauthorized firmware access | single-use, short-expiry, rate-limited OTP |
| **Billing without delivery** (charged but op failed) | angry customer | count on **confirmed success**, inside a transaction with the operation |

**The key concept to name in interview:** *idempotency and atomic counters*. Billing systems must never double-charge on a retry and never lose a count under concurrency. That's exactly the same class of problem as the Redis poll-lock in AIAAS — concurrency correctness.

---

## 4. "Tell me about..." — ready answers
- **Real ML experience** → battery RUL: feature engineering on NASA time-series, classical-vs-LSTM comparison, leakage-safe per-battery validation.
- **A time you chose the simpler solution** → tree model over LSTM when scores tied — cheaper, interpretable, real-time-friendly.
- **A data pitfall you caught** → train/test leakage from splitting by row instead of by battery.
- **Backend in industry** → firmware-security DRF platform with OTP, usage metering, billing.
- **Concurrency/correctness** → atomic, idempotent usage counters so billing never double-charges or loses counts.

## 5. Likely follow-ups
- *"How do you know your RUL model generalizes?"* → split by battery, cross-validate, report error near end-of-life.
- *"Why is random train/test split wrong here?"* → temporal/grouped data → leakage → over-optimistic metrics.
- *"How do you make a counter safe under load?"* → DB-level atomic increment + idempotency keys, never Python-side read-modify-write.
- *"LSTM vs Transformer for this?"* → Transformers shine on long sequences with lots of data; for short cycle histories on a small dataset, simpler wins.

---

## 6. Testing

> Strategy section — how each piece should be (and was) validated. Confirm specifics against your records.

**Testing ML is different from testing software** — there are two separate questions: "is the *code* correct?" and "is the *model* good enough?" I treat them separately.

### 6.1 Testing the ML pipeline (RUL)
- **Model evaluation (is the model good?):** RMSE/MAE on a held-out set, **split by battery** (never by row — see §1.2) so the score reflects performance on an unseen cell. k-fold cross-validation, report mean ± std.
- **Pipeline tests (is the code correct?):** unit-test feature engineering (a known input cycle produces the expected rolling-average/derivative features); assert no train/test battery overlap (a guard test that *fails the build* if leakage is introduced); assert the model handles missing/NaN sensor values without crashing.
- **Baseline test:** the model must beat a trivial baseline (e.g. "predict the mean RUL") — otherwise it's not learning anything.

### 6.2 Testing the dashboards
- Test the ingestion/aggregation layer with replayed telemetry; assert a sensor dropout shows a "stale" indicator rather than a frozen-but-live-looking chart.

### 6.3 Testing the firmware-billing platform (the highest-stakes tests)
Billing bugs cost real money, so these get the most rigorous tests:
| What | Test |
|---|---|
| **Idempotency** | fire the same flash operation twice (same id) → counter increments **once** |
| **Concurrency** | simulate two simultaneous increments → no lost update (atomic counter holds) |
| **OTP** | a used OTP is rejected; an expired OTP is rejected; brute-force is rate-limited |
| **Bill-on-success** | a failed operation does **not** increment the billable counter (transaction rolls back together) |

### 6.4 What I'd add
- A property-based / fuzz test that hammers the counter from many concurrent workers to prove the atomicity claim under real load; model-drift monitoring so a deployed RUL model is re-evaluated as new battery data arrives.
