"""Inject diagrams + append Deep Dive / Pitfalls / Math / Interview Qs / References to each ML/DL cheatsheet."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

# Map: file -> (image inserts after first H1, expansion appended at end)
PLAN = {
"dl-basics-cheatsheet.md": (
    ["diagrams/08-activations.png", "diagrams/12-bias-variance.png", "diagrams/17-regularization.png"],
r"""

---

## 🔬 Deep dive — what "deep learning" really is

A deep neural net is a stack of differentiable linear maps + nonlinearities, trained by **gradient descent** on a loss surface. Three things make it work:
1. **Universal approximation** — a single-hidden-layer net with enough units can approximate any continuous function. Depth just makes it efficient.
2. **Compositional features** — early layers learn edges/textures; deeper layers compose them into objects, words, concepts.
3. **End-to-end optimisation** — gradients flow from loss back to every parameter via autograd.

## ⚠️ Common pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Bad weight init | All units saturate or die | Use Xavier (tanh) / He (ReLU) init |
| LR too large | Loss diverges to NaN | Drop LR by 10×; gradient clip |
| LR too small | Loss decreases glacially | Warmup + cosine schedule |
| No normalisation of inputs | Loss zigzags | Standardise: (x − μ)/σ |
| Imbalanced classes | High acc, low recall on minority | Re-weight loss, oversample, focal loss |
| Vanishing gradients in deep nets | Early layers don't update | Residuals, LayerNorm, GeLU/ReLU |
| Train/val gap growing | Overfitting | Dropout, L2, augment, early stop |

## 🧮 Quick math: how a layer computes

Forward:  `y = φ(W·x + b)`  where φ is the activation.
Backward: `∂L/∂W = (∂L/∂y · φ'(z)) · xᵀ`  where `z = Wx + b`.

So each weight gradient is **upstream signal × local derivative × input**.

## 🧪 Universal training recipe

```
1. normalise inputs (mean 0, std 1, or [0,1])
2. init weights (Xavier for tanh, He for ReLU)
3. choose loss (CE for classification, MSE for regression)
4. choose optimiser (Adam(3e-4) by default; SGD+momentum for image nets)
5. warmup few steps + cosine LR schedule
6. monitor train/val loss; stop on val plateau
7. regularise: dropout, weight decay 1e-4, label smoothing 0.1
8. log gradient norms; clip at e.g. 1.0 if RNN/transformer
```

## 🎤 Interview questions

1. **Why is ReLU more popular than sigmoid?** No saturation in the positive region → gradients don't vanish in deep nets. Cheap to compute.
2. **What's "dying ReLU" and how to mitigate?** Neuron stuck at 0 because its input is always negative. Mitigations: Leaky ReLU, lower LR, better init.
3. **Difference between batch norm and layer norm?** BN normalises across the batch dimension per channel — great for CNNs, breaks for batch=1 / RNNs. LN normalises across features per sample — used in transformers.
4. **What does dropout do at inference?** Nothing — it's identity. We compensate by scaling activations by `1/(1-p)` during training (inverted dropout).
5. **When does deeper hurt?** Overfitting on small data, vanishing gradients without residuals, optimisation difficulties.
6. **Why use cross-entropy and not MSE for classification?** Cross-entropy's gradient is `p̂ − y` (no σ' factor) → faster learning; MSE × σ' suffers vanishing gradient near saturation.

## 📚 References
- *Deep Learning* (Goodfellow, Bengio, Courville) — Ch 6–8
- "He et al., Deep Residual Learning for Image Recognition" (2015)
- "Ioffe & Szegedy, Batch Normalization" (2015)
"""),

"gradient-descent-cheatsheet.md": (
    ["diagrams/05-gradient-descent.png", "diagrams/07-optimizers.png"],
r"""

---

## 🔬 Deep dive — why SGD generalises

Counterintuitively, the *noise* in SGD is a feature, not a bug. It biases optimisation toward **flat minima** which empirically generalise better than the sharp minima that exact GD finds. Recent theory (Smith & Le, Wu et al.) treats SGD as a stochastic differential equation; its stationary distribution favours wide basins.

## ⚠️ Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Same LR for all params | Use Adam/Adagrad/RMSprop |
| LR untuned | LR finder (Smith 2017): sweep, plot loss vs LR |
| No warmup → unstable early steps | Linear warmup over first few % of steps |
| Adam diverges on small/sparse data | Try AdamW or SGD+momentum |
| Gradient explosion (RNNs, transformers) | Clip global gradient norm to 1.0 |
| Adam + L2 vs weight decay | They differ! Use AdamW for correct decoupled weight decay |

## 🧮 Optimiser equations

| Optimiser | Update rule |
|-----------|-------------|
| SGD | `θ ← θ − η·g` |
| Momentum | `v ← βv + g;  θ ← θ − η·v` |
| Nesterov | look-ahead: gradient at `θ − βv` |
| Adagrad | `θ ← θ − η·g/√(Σg²+ε)` |
| RMSprop | `s ← βs + (1-β)g²;  θ ← θ − η·g/(√s+ε)` |
| Adam | `m ← β₁m + (1-β₁)g;  v ← β₂v + (1-β₂)g²;  θ ← θ − η·m̂/(√v̂+ε)` |
| AdamW | Adam + decoupled L2: `θ ← θ − η·(m̂/(√v̂+ε) + λθ)` |
| Lion (2023) | Sign of momentum direction; 2× memory cheaper than Adam |

## 🎤 Interview questions

1. **Why divide by √v in Adam?** Per-parameter step size adaptation — small for high-variance grads, large for stable ones.
2. **Why bias correction (`m̂ = m / (1-β₁ᵗ)`)?** Early in training m and v are biased toward zero; the correction undoes it.
3. **Batch size vs LR coupling?** Bigger batches usually need bigger LR (linear scaling rule, Goyal et al. 2017).
4. **What's a good LR schedule for transformers?** Linear warmup → cosine decay; warmup over ~1-10% of total steps.
5. **When is SGD+momentum preferred to Adam?** Vision (ConvNets), where it often generalises better; finetuning where small steps matter.

## 📚 References
- "Adam: A Method for Stochastic Optimization" (Kingma & Ba, 2014)
- "Decoupled Weight Decay Regularization" (Loshchilov & Hutter, 2017)
- "Super-Convergence" (Smith, 2018) — LR finder, 1-cycle policy
"""),

"ml-algos-cheatsheet.md": (
    ["diagrams/11-ml-tree.png", "diagrams/12-bias-variance.png", "diagrams/14-confusion-metrics.png"],
r"""

---

## 🔬 Deep dive — picking the right model

### Linear / Logistic Regression
- Pros: interpretable, fast, calibrated probabilities.
- Cons: assumes linearity; underfits complex data.
- Key knob: regularisation `C = 1/λ`.
- Use when: features are well-engineered, you need explainability.

### Decision Trees
- Pros: handle mixed types, no scaling, interpretable splits.
- Cons: high variance — small data change ⇒ different tree.
- Key knob: max_depth, min_samples_leaf.

### Random Forest (bagging)
- Pros: low-variance via averaging many decorrelated trees.
- Cons: less interpretable than a single tree; can be memory heavy.
- Key knob: n_estimators, max_features (√p for classification, p/3 for regression).

### Gradient Boosting (XGBoost / LightGBM / CatBoost)
- Pros: state-of-the-art on tabular data; handles missing values; built-in regularisation.
- Cons: tuning is non-trivial; can overfit on small data.
- Key knobs: learning_rate, n_estimators, max_depth, min_child_weight, subsample, colsample_bytree.

### SVM
- Pros: works in high dimensions; kernel trick for nonlinear boundaries.
- Cons: doesn't scale beyond ~50k samples; no native probabilities.
- Key knob: C (regularisation), kernel (rbf, poly, linear), gamma.

### KNN
- Pros: zero training cost; intuitive.
- Cons: slow at inference; curse of dimensionality.
- Use when: small dataset, low dimension, locally smooth target.

### Naive Bayes
- Pros: fast, good for text; works on tiny data.
- Cons: assumes feature independence (often false).

### K-Means / DBSCAN
- K-Means: k known, spherical clusters, sensitive to init.
- DBSCAN: density-based, finds arbitrary shapes, identifies noise.

## ⚠️ Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Class imbalance | `class_weight='balanced'`, oversample (SMOTE), focal loss |
| Data leakage | Fit scaler/encoder ONLY on train; pipeline.pipeline_ |
| Train/test split with time-series | Use TimeSeriesSplit, NOT random |
| Tuning on test set | Use train / val / test; cross-validate on train |
| Calibration ignored | Platt scaling / isotonic for prob-sensitive apps |
| Trusting accuracy on imbalanced data | Use PR-AUC, F1, recall |

## 🧮 Bias-variance and the U-curve

`E[(y − ŷ)²] = Bias² + Variance + IrreducibleError`

- High bias → underfit → simpler model or more features.
- High variance → overfit → more data, regularise, simpler model, ensemble.

## 🎤 Interview questions

1. **Why does bagging reduce variance and not bias?** Averaging i.i.d. estimators cuts variance by 1/n; bias is unchanged.
2. **Boosting vs bagging — different bias-variance behaviour?** Boosting reduces bias by sequentially fitting residuals; can overfit.
3. **When trees, when neural nets on tabular data?** Trees usually win on small/medium tabular (≤100k rows). Nets shine when there's structure (images, text, sequences).
4. **Why do RF feature importances mislead?** Biased toward high-cardinality features; use permutation importance for fairness.
5. **L1 vs L2 — when to use which?** L1 for sparsity / feature selection; L2 for stability / small weights.
6. **What's PR-AUC and when is it better than ROC-AUC?** Precision-Recall AUC is more informative when positives are rare.

## 📚 References
- *The Elements of Statistical Learning* (Hastie, Tibshirani, Friedman)
- "XGBoost: A Scalable Tree Boosting System" (Chen & Guestrin, 2016)
- *Hands-On ML* (Aurélien Géron) — practical comparisons
"""),

"cnn-resnet-unet-cheatsheet.md": (
    ["diagrams/04-cnn-feature-hierarchy.svg", "diagrams/01-resnet-skip.svg", "diagrams/02-unet.svg"],
r"""

---

## 🔬 Deep dive — what convolutions buy you

Three properties make CNNs efficient:
1. **Local receptive field** — pixels far apart aren't directly connected → fewer weights than an MLP.
2. **Weight sharing** — same filter scans the whole image → translation equivariance.
3. **Hierarchical features** — stacking conv layers grows receptive field; deeper layers see more context.

For a conv layer with kernel `k`, stride `s`, padding `p` on input `n×n`:
`out = ⌊(n + 2p − k)/s⌋ + 1`. Memorise this; it shows up in every interview.

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Spatial dims collapse to 0 | Track output shape per layer; add padding |
| BatchNorm before residual add | Wrong order — see ResNet v2 |
| Overfitting on small data | Data augmentation, dropout, weight decay |
| Class imbalance in segmentation | Use Dice or focal loss |
| Forgetting to switch model.train()/eval() | BN/Dropout misbehave |

## 🧠 Why ResNets work (skip connections)

Without skip:  `y = F(x)` ⇒ network must learn the identity mapping from scratch as it deepens, which is hard.
With skip:   `y = F(x) + x` ⇒ network only needs `F(x) = 0` to leave x unchanged. Gradients flow directly through the skip path → vanishing-gradient relief.

ResNets enabled **150+ layer** networks for the first time (He et al., 2015).

## 🧠 U-Net (segmentation)

- Encoder downsamples (capture context); decoder upsamples (precise localisation).
- **Skip connections** at each resolution paste high-resolution encoder features into the decoder → sharp boundaries.
- Designed for biomedical images with tiny training sets (Ronneberger et al., 2015).

## 🎤 Interview questions

1. **Receptive field of a stack of 3×3 convs?** After L layers it's `(2L+1)×(2L+1)` (with stride 1, no pooling).
2. **Why 3×3 convs and not 5×5?** Two 3×3s = same RF as one 5×5 but with fewer params and more nonlinearity.
3. **1×1 convolution use?** Channel-mixer; reduces channels (bottleneck) without touching spatial dims.
4. **Why pool? Alternatives?** Pool gives translation invariance + downsamples. Alternatives: strided conv (parametric), atrous/dilated conv (no resolution loss).
5. **GAP vs flatten before classifier?** GAP (global average pool) has 0 params, less overfit; flatten + FC has many params (e.g. AlexNet style).
6. **U-Net vs SegNet vs DeepLab?** U-Net concatenates skips; SegNet stores pool indices; DeepLab uses dilated convs + ASPP for multi-scale context.

## 📚 References
- "Deep Residual Learning for Image Recognition" (He et al., 2015)
- "U-Net: Convolutional Networks for Biomedical Image Segmentation" (Ronneberger et al., 2015)
- "Very Deep Convolutional Networks (VGG)" — Simonyan & Zisserman, 2014
"""),

"rnn-lstm-cheatsheet.md": (
    ["diagrams/03-rnn-lstm.svg", "diagrams/16-lstm-cell.png"],
r"""

---

## 🔬 Deep dive — why RNNs vanish

In a vanilla RNN, `h_t = tanh(W h_{t-1} + U x_t)`. Unrolling, the gradient w.r.t. an early hidden state involves the product `∏ Wᵀ · diag(tanh')` over many time steps. If the spectral radius of W is < 1, the product shrinks exponentially → **vanishing**. If > 1 → **exploding** (mitigated by gradient clipping).

**LSTM fix:** the cell state `c_t = f_t ⊙ c_{t-1} + i_t ⊙ g_t` is **additive**. Gradients flow through the cell state with multiplicative weights only when gates close — far gentler than the dense matrix product.

**GRU** simplifies LSTM to two gates (reset, update); often comparable performance with 25% fewer parameters.

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Sequence too long | Truncated BPTT (typical window 100-500) |
| Padding messes up loss | Mask padding tokens explicitly |
| Bidirectional in decoders | Don't — can't see future at inference |
| Sequence length affects batching | Bucket by length or use pad+pack |
| Vanishing on tasks > 1000 steps | Replace with transformer / state-space model |

## 🧮 LSTM equations (memorise!)

```
f_t = σ(W_f · [x_t, h_{t-1}] + b_f)            forget
i_t = σ(W_i · [x_t, h_{t-1}] + b_i)            input
g_t = tanh(W_g · [x_t, h_{t-1}] + b_g)         candidate
o_t = σ(W_o · [x_t, h_{t-1}] + b_o)            output
c_t = f_t ⊙ c_{t-1} + i_t ⊙ g_t                cell update
h_t = o_t ⊙ tanh(c_t)                          hidden
```

## 🎤 Interview questions

1. **Why does LSTM solve vanishing gradients?** Additive cell-state path bypasses the multiplicative chain.
2. **GRU vs LSTM?** GRU merges cell and hidden state, no output gate — fewer params, comparable performance on most tasks.
3. **What does sequence-to-sequence with attention do that vanilla seq2seq doesn't?** Lets decoder look back at *all* encoder states, not just the final hidden.
4. **When use RNNs in 2026?** Streaming low-latency contexts where small models matter; mostly transformers dominate.
5. **Teacher forcing — pros/cons?** Faster convergence; train-test mismatch; mitigations: scheduled sampling.

## 📚 References
- Colah's blog: "Understanding LSTMs" (must-read)
- "Empirical Evaluation of Gated Recurrent Neural Networks" (Chung et al., 2014)
"""),

"embeddings-nlp-cheatsheet.md": (
    ["diagrams/10-embeddings.png", "diagrams/09-attention.png"],
r"""

---

## 🔬 Deep dive — embeddings as geometry

An embedding is a learned map from discrete tokens to ℝᵈ such that **semantic similarity ≈ vector similarity** (cosine or dot product).
- **Word2Vec (skip-gram)**: predict surrounding words from centre — captures syntagmatic regularities, supports analogies via vector arithmetic.
- **GloVe**: factorise word-word co-occurrence matrix → similar quality with explicit optimisation target.
- **FastText**: subword n-grams → handles OOV and morphology.
- **Contextual (BERT, GPT)**: same word → different vector per context (polysemy resolved).
- **Sentence embeddings** (Sentence-BERT, OpenAI text-embedding-3): pool token embeddings or use a [CLS]-style aggregator + contrastive fine-tune.

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Cosine vs dot — different rankings | Normalise vectors before cosine; pick one and stick with it |
| Comparing across models | Embeddings live in different spaces; no direct comparison |
| Stale embeddings on changing vocabulary | Periodic re-embedding |
| Bias in word2vec ("doctor" → male) | Debiasing (Bolukbasi et al.) or use larger contextual model |
| Tokeniser mismatch in retrieval | Same tokeniser for query and corpus |

## 🧮 Useful math

- **Cosine similarity**: `cos(u,v) = (u·v)/(||u||·||v||)`.
- **Analogy by arithmetic**: `king − man + woman ≈ queen`. Often the closest vector in the corpus is *king* or *queen* — small details matter.
- **Contrastive loss (InfoNCE)**: pull positives close, push hard negatives apart in batch.

## 🎤 Interview questions

1. **Why log-bilinear (GloVe) instead of pure skip-gram?** Direct factorisation of the global co-occurrence statistics — more efficient batch training.
2. **Why contextual embeddings beat static ones?** Words with multiple senses (bank, lead) need different vectors per usage.
3. **How would you evaluate an embedding model?** Intrinsic: word similarity datasets, analogy tests. Extrinsic: downstream task accuracy.
4. **What's the curse of dimensionality for embeddings?** Distances concentrate; cosine becomes less discriminative beyond ~1000d unless training penalises it.
5. **Pooling strategy for sentence embeddings?** Mean-pool > [CLS] for BERT (Reimers & Gurevych 2019); attention pooling for some tasks.

## 📚 References
- "Efficient Estimation of Word Representations" (Mikolov et al., 2013)
- "GloVe" (Pennington, Socher, Manning, 2014)
- "Sentence-BERT" (Reimers & Gurevych, 2019)
- "MTEB" leaderboard — benchmark for embedding models
"""),

"rl-cheatsheet.md": (
    ["diagrams/13-rl-mdp.png"],
r"""

---

## 🔬 Deep dive — RL formalism

An MDP is a tuple `(S, A, P, R, γ)`:
- **S** states, **A** actions
- **P(s'|s,a)** transition, **R(s,a)** reward
- **γ ∈ [0,1)** discount factor

Goal: find policy π that maximises `V^π(s) = E[Σ_{t≥0} γᵗ R(sₜ,aₜ)]`.

Two value functions:
- **State value** `V(s)` — expected return starting from s.
- **Action value** `Q(s,a)` — expected return after taking a in s.

**Bellman optimality:**
```
V*(s) = max_a [R(s,a) + γ Σ P(s'|s,a) V*(s')]
Q*(s,a) = R(s,a) + γ Σ P(s'|s,a) max_a' Q*(s',a')
```

## 🧮 Method matrix

| Method | Type | Update | Notes |
|--------|------|--------|-------|
| Dynamic Programming | Model-based | full sweep | Requires P,R known |
| Monte Carlo | Model-free | episode-end | Unbiased; high variance |
| TD(0) | Model-free | per step | Biased; low variance |
| Q-learning | Off-policy TD | `Q ← Q + α[r + γ max Q'-Q]` | Learns greedy policy |
| SARSA | On-policy TD | `Q ← Q + α[r + γ Q(s',a')-Q]` | Learns ε-greedy |
| Policy gradient (REINFORCE) | Model-free | `∇θ J = E[∇log π · G]` | High variance |
| Actor-Critic (A2C, A3C) | Hybrid | actor=policy, critic=value | Lower variance |
| PPO | Policy gradient | clipped surrogate | Stable, default for LLM RLHF |
| DQN | Off-policy + NN | experience replay, target net | Atari breakthrough |

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Sparse rewards | Reward shaping, curriculum, intrinsic motivation |
| Bootstrap divergence (deadly triad) | Target network + experience replay |
| Policy collapse | Entropy bonus in objective |
| Stale critic | Slow-tracking target network (τ=0.005) |
| Reward hacking | Constrain or use RLHF preferences |

## 🎤 Interview questions

1. **On-policy vs off-policy?** On-policy (SARSA, PPO) updates the policy that's generating the data. Off-policy (Q-learning, DQN) can learn from any past data.
2. **Why a target network in DQN?** Stabilises bootstrapping — without it, Q chases a moving target.
3. **What is the policy gradient theorem?** `∇θ J(θ) = E_τ[Σ ∇θ log π(a|s) · R(τ)]` — gradient of expected return w.r.t. policy params equals expectation of log-prob-grad weighted by return.
4. **What's PPO's "clip" about?** Penalises updates that move the policy more than ε from the previous one — improves stability vs. vanilla policy gradient.
5. **RLHF in LLMs — pipeline?** SFT on demonstrations → reward model from human pairwise prefs → PPO against reward model with KL penalty to base.

## 📚 References
- *Reinforcement Learning: An Introduction* (Sutton & Barto, 2nd ed.)
- "Playing Atari with Deep RL" (DQN, Mnih et al. 2013)
- "Proximal Policy Optimization" (Schulman et al., 2017)
"""),

"backprop-gradient-examples.md": (
    ["diagrams/06-backprop.png"],
""),  # already long; just add image

"embeddings-examples.md": (
    ["diagrams/10-embeddings.png"],
""),
}

for fname, (imgs, extra) in PLAN.items():
    p = ROOT / fname
    if not p.exists():
        print("MISSING:", p); continue
    text = p.read_text(encoding="utf-8")
    # insert images after first H1
    lines = text.split("\n")
    out = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if not inserted and ln.startswith("# "):
            for img in imgs:
                if f"![Diagram]({img})" not in text:
                    out.append("")
                    out.append(f"![Diagram]({img})")
            inserted = True
    text = "\n".join(out)
    if extra and "## 🔬 Deep dive" not in text:
        if not text.endswith("\n"): text += "\n"
        text += extra
    p.write_text(text, encoding="utf-8")
    print("expanded:", fname)
