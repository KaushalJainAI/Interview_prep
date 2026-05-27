"""Inject diagrams + append Deep Dive / Math / Pitfalls / Interview Qs / References to Transformer cheatsheets."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

PLAN = {
"transformers-cheatsheet.md": (
    ["diagrams/15-transformer-block.png", "diagrams/02-attention-dataflow.svg", "diagrams/16-positional.png"],
r"""

---

## 🔬 Deep dive — why transformers dominate

Three structural wins over RNNs:
1. **Parallel training** — every position computed simultaneously (no sequential dependency), GPUs love this.
2. **Constant path length** — every token can attend to every other in one step → no vanishing gradient over long context.
3. **Inductive bias = flexibility** — attention learns relationships from data instead of hard-coding locality (CNN) or recurrence (RNN).

The cost is **quadratic in sequence length** for vanilla attention (O(N²·d) compute, O(N²) memory). Workarounds: sparse, linear, low-rank, sliding-window, FlashAttention (still O(N²) but memory-efficient and fused).

## 🧮 The attention equation

```
Attention(Q, K, V) = softmax(Q · Kᵀ / √d_k) · V
```

- `Q ∈ R^(N×d_k)`, `K ∈ R^(N×d_k)`, `V ∈ R^(N×d_v)`
- Scale by `√d_k` to keep dot-products from saturating softmax.
- Multi-head: split d_model into h heads, run attention in each, concat → linear.

Encoder block:
```
x ← x + MHA(LN(x))      # pre-norm (modern style)
x ← x + MLP(LN(x))      # MLP = Linear(d, 4d) → GeLU → Linear(4d, d)
```

Decoder adds **causal mask** in self-attention (no peeking ahead) and an additional cross-attention block over the encoder output (in enc-dec models).

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Forgetting causal mask in decoder | Add upper-triangular -inf mask before softmax |
| Pad tokens contribute to softmax | Mask pad positions with -inf |
| Numerical overflow in softmax | Subtract max before exp (already in stable softmax) |
| Position info lost after attention | Add positional encoding (sin, learned, RoPE, ALiBi) |
| Loss not converging on long sequences | Try gradient clipping, lower LR, more warmup |
| OOM on long context | FlashAttention; gradient checkpointing; sequence parallelism |

## 🎤 Interview questions

1. **Why divide by √d_k?** Variance of `Q·Kᵀ` grows with d_k; without scaling softmax saturates and gradients vanish.
2. **What's multi-head attention buying us?** Each head can attend to different subspaces (e.g., syntactic, semantic). Empirically: a single big head ≠ many small ones.
3. **Why pre-norm beats post-norm?** Better gradient flow → easier to train deep stacks; original paper used post-norm.
4. **Encoder vs decoder block diff?** Decoder has masked self-attention + (optionally) cross-attention.
5. **How does the 4× MLP expansion help?** Adds non-linear expressivity per token; attention is essentially linear in V.
6. **Why GeLU and not ReLU?** Smoother gradient, slightly better empirically; ~no extra cost.

## 📚 References
- "Attention Is All You Need" (Vaswani et al., 2017)
- *The Illustrated Transformer* — Jay Alammar
- Andrej Karpathy: "Let's build GPT" YouTube series
"""),

"bert-gpt-cheatsheet.md": (
    ["diagrams/12-bert-gpt-t5.png"],
r"""

---

## 🔬 Deep dive — the three transformer families

| Model | Direction | Objective | Output use |
|-------|-----------|-----------|------------|
| **BERT** | bidirectional | MLM (mask 15% of tokens) + NSP | classification, NER, QA via fine-tune |
| **GPT** | causal (left-to-right) | next-token prediction | generation (zero/few-shot, chat) |
| **T5** | enc-dec | span-corruption to text | translation, summarisation, anything text-to-text |

GPT's autoregressive objective is the simplest and scales beautifully — that's why decoder-only dominates 2023+.

## 🧮 Pretraining objectives

- **MLM (BERT)**: mask 15% of tokens; predict them from bidirectional context.
- **CLM (GPT)**: predict next token given previous.
- **Span corruption (T5)**: replace spans with sentinel tokens, predict span contents.
- **Permutation LM (XLNet)**: bidirectional context but autoregressive prediction.
- **ELECTRA**: replaced-token detection — small generator corrupts, discriminator classifies real/fake. ~4× sample-efficient.

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Using BERT for generation | It's not generative — use GPT/T5 |
| Comparing perplexity across tokeniser vocabs | Convert to bits-per-byte |
| Fine-tuning entire BERT for a tiny dataset | Freeze low layers; or use adapters / LoRA |
| Forgetting [CLS] / [SEP] in BERT inputs | Add them per task format |

## 🎤 Interview questions

1. **Why is BERT bidirectional but GPT isn't?** Different objectives — MLM allows seeing both sides of mask; CLM cannot peek ahead during training.
2. **Why does GPT generalise to many tasks via prompting?** Next-token prediction is a universal task; large-enough models memorise patterns of how problems map to solutions.
3. **What's wrong with NSP, and why did RoBERTa drop it?** NSP was too easy; dropping it + longer training + bigger batches → better embeddings.
4. **Encoder vs decoder for retrieval embeddings?** Encoder (BERT-style) usually better — bidirectional context yields richer representations for similarity.
5. **Why does T5 cast everything as text-to-text?** Unification simplifies the toolkit; one model, one loss, many tasks.

## 📚 References
- "BERT: Pre-training of Deep Bidirectional Transformers" (Devlin et al., 2018)
- "Improving Language Understanding by Generative Pre-Training" (Radford et al., 2018) — original GPT
- "Exploring the Limits of Transfer Learning with T5" (Raffel et al., 2020)
"""),

"kv-cache-cheatsheet.md": (
    ["diagrams/05-kv-cache.svg", "diagrams/17-inference.png"],
r"""

---

## 🔬 Deep dive — why KV cache exists

During autoregressive generation, the attention K and V for past tokens are **identical at every decoding step** — recomputing them each time is wasteful. The KV cache stores them across calls.

**Without cache**: step t recomputes K,V for all t tokens → O(t·d) per step → O(T²) total to generate T tokens.
**With cache**: step t computes K,V only for the new token → O(d) per step → O(T·d) total. Quadratic → linear.

## 🧮 Memory math

```
KV bytes per request = 2 · n_layers · n_heads · head_dim · seq_len · dtype_bytes
```

LLaMA-7B example:
- n_layers=32, n_heads=32, head_dim=128, dtype=bf16 (2 bytes)
- 4k context: 2·32·32·128·4096·2 ≈ **2.1 GB**
- 32k context: ~17 GB

Per-request! Batch by 8 → 16 GB at 4k context.

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Cache grows linearly with concurrent users | Use PagedAttention / vLLM |
| Long-context blows GPU memory | Quantise KV (int8), or use sliding-window |
| Cache invalidation when context branches | Each branch needs its own cache copy |
| Mixed-precision bugs in cached K | Keep cache in same dtype as model |

## 🚀 Optimisations

1. **PagedAttention (vLLM)** — virtual memory paging for KV → near-zero waste, 2-4× throughput.
2. **GQA / MQA** — fewer K,V heads than Q heads → smaller cache. LLaMA-2 70B uses GQA-8.
3. **Quantise KV** — int8 cuts memory in half with tiny quality loss.
4. **Sliding window attention** — Mistral keeps only last W tokens (W=4096); long context via attention sinks.
5. **Speculative decoding** — small draft model proposes K tokens, big model verifies in parallel.

## 🎤 Interview questions

1. **Why does the KV cache not store Q?** Q is needed only for the current step; never reused.
2. **GQA vs MQA?** Multi-Query = 1 K,V head shared by all Q heads (extreme); GQA = groups of Q heads share K,V (LLaMA-2 70B uses 8 groups).
3. **Trade-off of int8 KV cache?** ~50% memory; small perplexity bump (usually <1%); compute may be slightly slower due to dequant.
4. **What's a "KV cache hit" in serving?** Reusing cache across requests sharing a prefix (e.g., system prompt) — huge speedup.
5. **Why is decode "memory-bandwidth-bound"?** Each step reads the full cache once → memory > compute is the bottleneck.

## 📚 References
- "Efficient Memory Management for LLM Serving with PagedAttention" (Kwon et al., vLLM 2023)
- "Fast Transformer Decoding: One Write-Head is All You Need" (MQA, Shazeer 2019)
"""),

"fine-tuning-cheatsheet.md": (
    ["diagrams/08-lora-finetuning.svg", "diagrams/15-lora-detail.png"],
r"""

---

## 🔬 Deep dive — full fine-tune vs PEFT

| Method | Trainable params | Memory | When |
|--------|------------------|--------|------|
| Full FT | 100% | full model + optimizer states (3-4× model) | enough data + compute; need fundamental behaviour change |
| LoRA | 0.1–1% | base + small adapter | most cases; cheap, swappable, composable |
| QLoRA | 0.1–1% | 4-bit base + adapter | huge models on small GPUs (65B on 48GB) |
| Prefix / Prompt tuning | 0.01% | tiny | task-specific prompts; rarely best quality |
| Adapter layers (Houlsby) | 0.5–3% | small | precursor to LoRA, still used in research |
| BitFit | only biases | tiny | very small adaptations |
| RLHF (PPO) | full model | 6-8× model (policy + value + ref + reward) | alignment after SFT |
| DPO | full model | 2× model | preference learning without RL machinery |
| ORPO / SimPO | full model | 1× | newer one-stage variants of preference tuning |

## 🧮 LoRA math

A LoRA adapter replaces `y = W·x` with:
```
y = W·x + α/r · (A · B) · x        with A: d×r, B: r×d, r ≪ d
```
- Only A and B are trained; W is frozen.
- Trainable params ≈ 2·d·r (e.g. d=4096, r=8 → 64k params instead of 16M).
- At inference, optionally merge: `W' = W + α/r · A·B` → no extra latency.

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Catastrophic forgetting | Lower LR; mix in some pretraining data; use PEFT |
| Overfitting on small data | Early stop on val; regularise; smaller model |
| Wrong LR for fine-tune | Start at 1e-5 to 5e-5 (full FT), 1e-4 to 3e-4 (LoRA) |
| Forgetting to mask labels on prompt | Loss should only count completion tokens for instruction tuning |
| QLoRA + bfloat16 mixed wrongly | Use 4-bit base, bf16 adapters, paged optimisers |
| LoRA r too small | Try 8 → 16 → 32; depends on dataset complexity |

## 🧪 Recipe — instruction fine-tune a 7B model

```
1. Tokenize prompt+completion; mask prompt tokens in loss
2. Base = LLaMA-2-7B (or Mistral, Qwen)
3. LoRA: r=16, α=32, target_modules=[q_proj, k_proj, v_proj, o_proj]
4. LR=2e-4, cosine schedule, warmup 3%, weight decay 0.0
5. Batch size = 128 (use gradient accumulation if needed)
6. Train 1-3 epochs; watch val loss
7. Eval on held-out prompts; sample qualitatively
8. Merge or keep as adapter
```

## 🎤 Interview questions

1. **Why LoRA works (rank-r adaptation theory)?** Empirically, the *update* during fine-tuning lives in a low-rank subspace; we don't need full-rank updates to specialise.
2. **DPO vs RLHF — what's the actual difference?** DPO derives a closed-form loss from the RLHF objective — no separate reward model, no PPO, just a binary cross-entropy. Easier and often as good.
3. **What's catastrophic forgetting and when do you see it?** Model loses pretrained capabilities after fine-tuning on narrow data. Mitigations: replay, PEFT, lower LR.
4. **When to use SFT vs RLHF?** SFT teaches the model *how* to respond; RLHF/DPO teaches it *which* responses are preferred (style, safety, helpfulness).
5. **What does the α scale in LoRA control?** Effective learning rate of the adapter; α/r is the scaling factor. Common: α=2r.

## 📚 References
- "LoRA: Low-Rank Adaptation of Large Language Models" (Hu et al., 2021)
- "QLoRA: Efficient Finetuning of Quantized LLMs" (Dettmers et al., 2023)
- "Direct Preference Optimization" (Rafailov et al., 2023)
"""),

"moe-cheatsheet.md": (
    ["diagrams/11-moe-routing.png"],
r"""

---

## 🔬 Deep dive — sparse experts

MoE replaces the dense MLP in some/all transformer layers with **N experts** (smaller MLPs) and a **router** that selects top-k experts per token. Total parameters scale, but per-token compute does not.

Trade-off:
- **Pros**: dramatic capacity-per-FLOP improvement; bigger model, same compute.
- **Cons**: load balancing (some experts get all the work), all-to-all communication overhead, memory still proportional to total params, harder to deploy.

## 🧮 Top-k routing

```
gates_logits = W_router · x          # x: token, gates: N experts
weights = softmax(top_k(gates_logits, k))
y = Σ_{j ∈ top_k}  weights[j] · expert_j(x)
```

With k=2 and N=8: each token uses 2 of 8 experts → ~25% of MoE params active per token.

**Aux load-balancing loss** (Switch Transformer):
```
L_aux = α · N · Σ_i  (fraction of tokens to expert_i) · (avg gate prob for expert_i)
```
Encourages uniform expert utilisation.

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Expert collapse (one expert gets all) | Aux loss + capacity factor |
| Router instability early training | Z-loss to keep logits small |
| Inference latency from all-to-all | Co-locate experts; expert parallelism |
| Memory still dominated by total params | Can't shrink — use cheaper experts (smaller hidden) |

## 🎤 Interview questions

1. **Why is MoE compute-efficient but memory-hungry?** FLOPs scale with active params; memory scales with total params.
2. **What's "capacity factor"?** Buffer that lets each expert handle up to `capacity_factor · tokens/N` tokens. >1 avoids dropping tokens at the cost of compute.
3. **Switch Transformer vs MoE (Shazeer)?** Switch = k=1 (single expert per token), Shazeer = k=2. k=1 simpler, k=2 slightly better quality.
4. **Why does Mixtral 8x7B fit in 24 GB at 4-bit?** Total ~47B params; active ~13B; at 4-bit ≈ 23 GB total memory.
5. **Load-balance loss intuition?** Discourages routing all traffic to a few experts; pushes the routing distribution toward uniform.

## 📚 References
- "Outrageously Large Neural Networks: The Sparsely-Gated MoE Layer" (Shazeer et al., 2017)
- "Switch Transformer" (Fedus et al., 2021)
- "Mixtral of Experts" (Jiang et al., 2024)
"""),

"scaling-laws-cheatsheet.md": (
    ["diagrams/10-scaling-laws.png"],
r"""

---

## 🔬 Deep dive — Kaplan vs Chinchilla

**Kaplan (2020)** found loss decreases as a power law in compute, with parameters more important than data → led to scaling up model size aggressively (GPT-3 175B).

**Chinchilla (Hoffmann et al., 2022)** rerun the experiments more carefully and showed the optimal trade-off is `tokens ≈ 20 × params`. Most prior models (GPT-3, PaLM) were undertrained.

Implication: at fixed compute, smaller-but-trained-longer ≥ larger-but-undertrained.

## 🧮 The empirical law

```
L(N, D, C) ≈ A · N^(-α) + B · D^(-β) + L_∞
```
- N = parameters, D = tokens, C = compute (FLOPs ≈ 6·N·D for transformer training)
- α ≈ 0.34, β ≈ 0.28 (Chinchilla fits)
- L_∞ = irreducible loss (data entropy)

Optimal under compute budget C: `N* ∝ C^0.5`, `D* ∝ C^0.5` → keep them balanced.

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Optimising only on a tiny scan | Need ≥ 6 orders of magnitude to fit reliably |
| Forgetting data quality matters | Better data shifts the curve, doesn't just slide along it |
| Assuming laws extrapolate forever | Plateaus emerge as you exhaust data / hit emergent thresholds |
| Comparing models with different architectures | Architecture changes A, α |

## 🎤 Interview questions

1. **Chinchilla's main finding in one sentence?** Most LLMs are undertrained — for a given compute, fewer params + more tokens gives lower loss.
2. **How is compute computed (FLOPs)?** ~6 · N · D for transformer training (forward 2NF + backward 4NF).
3. **What is "emergent ability"?** Capability that appears only above some scale threshold (e.g. chain-of-thought arithmetic). Some researchers argue it's a metric artefact.
4. **Inference scaling vs train scaling?** Recent work (o1, OpenAI Sept 2024) shows test-time compute scales differently — longer thinking traces improve hard reasoning.
5. **Why are scaling laws useful?** Predict how much compute / data to budget; choose between scaling axes; estimate whether a new technique helps beyond scale.

## 📚 References
- "Scaling Laws for Neural Language Models" (Kaplan et al., 2020)
- "Training Compute-Optimal Large Language Models" (Hoffmann et al., 2022)
- "Are Emergent Abilities of Large Language Models a Mirage?" (Schaeffer et al., 2023)
"""),

"tokenizers-cheatsheet.md": (
    ["diagrams/09-bpe-merge.png"],
r"""

---

## 🔬 Deep dive — why subword tokenisation

Three reasons subwords beat character-level and word-level:
1. **No OOV** — every word decomposes into known subwords (and ultimately bytes).
2. **Reasonable sequence length** — characters are too granular; sequences become huge.
3. **Captures morphology** — "run-ning" and "play-ing" share suffixes.

Algorithms:
- **BPE (Byte-Pair Encoding)** — iteratively merge most frequent pair. Used by GPT-2, LLaMA, Mistral.
- **WordPiece** — variant of BPE; chooses merges by likelihood gain. Used by BERT.
- **Unigram (SentencePiece)** — top-down: start with big vocab, remove low-likelihood tokens. Used by T5, LLaMA-3.
- **Tiktoken (OpenAI)** — BPE with byte-level fallback; handles any Unicode.

## 🧮 BPE algorithm sketch

```
1. Initialise vocab with all individual bytes (or characters).
2. Repeat until |vocab| = target_size:
     a. Count all adjacent token pairs in corpus.
     b. Merge most frequent pair → new token.
     c. Replace occurrences in corpus.
3. Save vocab + merge rules.
```

Encoding a new sentence: apply merges greedily in order.

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Different tokenisers across train/inference | Always pair the model with its exact tokenizer |
| Counting words vs tokens | English: ~1 token ≈ 0.75 words; code: ~1 token ≈ 1 char |
| Leading-space sensitivity | " hello" and "hello" tokenise differently in BPE |
| Tokenising code with a text tokenizer | Bad compression; use code-specialised tokenisers (Codex, StarCoder) |
| Cross-lingual mismatch | English-heavy vocab → many tokens for Hindi/Chinese; multilingual tokenisers help |

## 🎤 Interview questions

1. **Why byte-level BPE?** Guarantees lossless round-trip for any Unicode; no special UNK token needed.
2. **BPE vs WordPiece — practical diff?** BPE picks merges by frequency, WordPiece by likelihood. Quality near-identical.
3. **What determines vocab size choice?** Bigger vocab = shorter sequences but bigger embedding matrix (50k for GPT-2, 32k for LLaMA, 100k+ for GPT-4o).
4. **Why subword > character LM?** Compute is proportional to seq length; characters explode it.
5. **What's "tokenisation tax" for non-English?** Many languages get 2-5× more tokens per word than English, raising costs.

## 📚 References
- "Neural Machine Translation of Rare Words with Subword Units" (Sennrich et al., 2016) — BPE for NMT
- "SentencePiece" library / paper (Kudo & Richardson, 2018)
- tiktoken — OpenAI's tokeniser library
"""),

"diffusion-cheatsheet.md": (
    ["diagrams/06-diffusion-process.svg"],
r"""

---

## 🔬 Deep dive — forward & reverse diffusion

**Forward (q):** add Gaussian noise gradually over T steps.
```
q(x_t | x_{t-1}) = N(x_t; √(1-β_t)·x_{t-1}, β_t·I)
```
After T steps → pure noise.

**Reverse (p_θ):** model learns to denoise step by step.
```
p_θ(x_{t-1} | x_t) = N(x_{t-1}; μ_θ(x_t, t), Σ_θ(x_t, t))
```
Typically parameterised to predict the **noise ε** that was added; sample by removing predicted noise.

## 🧮 Loss

Simplified (DDPM):
```
L = E_{t, x_0, ε} ||ε − ε_θ(√α̅_t · x_0 + √(1-α̅_t)·ε, t)||²
```
A simple MSE loss — predict noise from noisy input. Surprisingly powerful.

## 🚀 Sampling variants

| Sampler | Steps needed | Notes |
|---------|-------------|-------|
| DDPM | 1000 | original, slow |
| DDIM | 20-50 | deterministic, much faster |
| DPM-Solver / Solver++ | 10-25 | high-order ODE solvers |
| Consistency Models | 1-4 | distilled for one/few-step sampling |
| Flow Matching / Rectified Flow | 1-50 | straight ODE paths; SD3, Flux |

## 🎨 Modern conditioning

- **Classifier-free guidance**: sample with both conditional and unconditional model; extrapolate `ε = (1+w)ε_c − w·ε_u` for sharper conditioning.
- **Latent diffusion (Stable Diffusion)**: diffuse in compressed latent space (e.g., 64×64×4 instead of 512×512×3) — 50× faster.
- **ControlNet / IP-Adapter**: extra inputs (sketches, depth, pose, reference image) guide generation.

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Cherry-picked seeds in demos | Always show fixed-seed grid |
| Confusing schedules (linear vs cosine) | Cosine schedules are smoother → better quality |
| FID misuse | Compute on the same reference distribution |
| Mode collapse from over-guidance | Lower CFG scale (5-7 typical, 12+ is too much) |

## 🎤 Interview questions

1. **Why predict noise instead of x_0?** Empirically smoother loss; equivalent up to reparameterisation.
2. **DDPM vs DDIM — practical?** DDIM is a deterministic accelerator on top of a DDPM model — same training, faster sampling.
3. **Why does CFG work?** It extrapolates in the direction of "more conditional", at the cost of diversity.
4. **Latent diffusion intuition?** Most pixel structure is redundant; a VAE compresses to a perceptually-equivalent latent where diffusion is much cheaper.
5. **Flow Matching vs diffusion?** Trains a velocity field on straight-line paths between noise and data — fewer sampling steps, simpler theory.

## 📚 References
- "Denoising Diffusion Probabilistic Models" (Ho et al., 2020)
- "High-Resolution Image Synthesis with Latent Diffusion" (Rombach et al., 2022) — Stable Diffusion
- "Flow Matching for Generative Modeling" (Lipman et al., 2023)
"""),

"latest-models-cheatsheet.md": (
    ["diagrams/13-sampling.png", "diagrams/14-quantization.png"],
r"""

---

## 🔬 Deep dive — 2024-2026 landscape

| Model | Org | Release | Notable |
|-------|-----|---------|---------|
| Claude 4 / 4.5 / 4.6 / 4.7 | Anthropic | 2024-2026 | Best reasoning + coding; extended thinking; computer use |
| GPT-4o / o1 / o3 | OpenAI | 2024-2025 | Multimodal native (4o); chain-of-thought RL (o-series) |
| Gemini 2.5 / 2.5 Pro | Google | 2024-2025 | Long-context (2M tokens), multimodal |
| LLaMA-3 / 3.1 / 4 | Meta | 2024-2025 | Open weights, 8B/70B/405B; MoE in LLaMA-4 |
| Mistral / Mixtral 8x22B / Codestral | Mistral | 2024 | Strong open MoE; code-focused variants |
| DeepSeek-V3 / R1 | DeepSeek | 2024-2025 | Open MoE w/ great reasoning; R1 = RL-trained chain-of-thought |
| Qwen 2.5 / 3 | Alibaba | 2024-2025 | Strong multilingual, open weights |
| Grok 3 / 4 | xAI | 2024-2025 | Long-context, integrated search |

## 🧠 Trends to talk about

1. **Reasoning models** — train with RL on chain-of-thought; test-time compute scaling.
2. **Multimodality** — single model processes text + image + audio + video natively (4o, Gemini, Claude 4).
3. **Long context** — 200k (Claude), 1M (Gemini 1.5), 2M (Gemini 2.5). Quality often degrades past 32k.
4. **Open vs closed** — DeepSeek, LLaMA, Qwen close the gap with frontier closed models.
5. **Agents** — tool use, computer use, multi-step planning. Claude 4 popularised structured tool use.
6. **Synthetic data** — model-generated data refined by humans; key to scaling beyond web data.
7. **Speculative decoding + inference-time scaling** — major latency wins; o1-style reasoning trades latency for quality.

## ⚠️ Common interview pitfalls

| Pitfall | Fix |
|---------|-----|
| Citing pricing/specs from memory | Always note "as of [date]"; ranges if unsure |
| Claiming a model is "best" universally | Specify benchmark (MMLU, GPQA, SWE-bench, HumanEval) |
| Confusing context window with retrieval ability | Long-context ≠ uses-context-well (needle-in-haystack) |
| Treating closed and open models as interchangeable | Closed has finetuning APIs but no weight access; open has both |

## 🎤 Interview questions

1. **Why are reasoning models slower at inference?** They generate long internal chain-of-thought tokens before answering; you pay per token.
2. **When pick open weights over a frontier API?** Privacy, custom finetuning, predictable cost, on-prem deployment, latency control.
3. **What's a "frontier" model?** State-of-the-art on broad benchmarks at release time; usually closed, very large, very expensive.
4. **Best model for code generation in 2026?** Depends on task; Claude 4.6/4.7 and GPT o3 score top on SWE-bench, while Codestral/DeepSeek-Coder are strong open options.
5. **Why does benchmark performance plateau?** Saturation (~95% on MMLU), contamination concerns, and tasks no longer discriminate frontier models — push toward harder benchmarks (GPQA, FrontierMath, ARC-AGI).

## 📚 References
- Stanford AI Index (annual)
- Artificial Analysis benchmarks
- Vellum LLM Leaderboard
"""),

"rag-hnsw-cheatsheet.md": (
    ["diagrams/03-rag-pipeline.svg", "diagrams/04-hnsw-graph.svg", "diagrams/18-rag-arch.png"],
r"""

---

## 🔬 Deep dive — what makes a RAG system good

Four orthogonal quality axes; tune each:
1. **Recall** — does the retriever find relevant chunks? Measured by Recall@k.
2. **Precision** — are top-k mostly relevant? Reranker fixes this.
3. **Faithfulness** — does the LLM stay within retrieved context? Prompt engineering + lower temperature.
4. **Latency** — vector search, rerank, LLM all add ms. Budget per stage.

## 🧮 HNSW (Hierarchical Navigable Small World)

Approximate nearest-neighbour graph with **logarithmic search**.

Construction:
- Each point inserted at a random max-level L ~ exponential.
- At each level, connect to M nearest existing points.
- Higher levels are sparse highways; lower levels are dense local connections.

Search:
- Start at top level entry point; greedy walk toward query.
- Descend a level; repeat with wider search beam.
- Bottom level: collect k candidates.

Recall vs speed tuned by `ef` parameter (search beam width).

## ⚠️ Pitfalls

| Pitfall | Fix |
|---------|-----|
| Wrong chunk size | Tune per data: 200-800 tokens typical; smaller for QA, larger for narrative |
| No overlap → information at chunk boundary lost | Add 10-15% overlap |
| Same embedding for query and doc | Asymmetric embeddings (e5, BGE) often better for retrieval |
| Forgetting to normalise vectors | Cosine ≡ dot only when ||v||=1 |
| Indexing PDFs as one chunk | Parse tables, headings, images separately |
| Ignoring metadata filters | Hybrid: BM25 + vector + filter clauses |
| Using vector search alone for keyword queries | Hybrid (BM25 + vector) wins |

## 🚀 Production patterns

1. **Hybrid retrieval**: BM25 ∪ dense vector → reciprocal-rank fusion → rerank.
2. **Reranker**: cross-encoder (e.g. bge-reranker-large) scores (query, doc) pairs jointly.
3. **Query rewriting**: LLM expands / rewrites the user query before retrieval.
4. **Multi-query**: generate N rewrites; union results.
5. **HyDE**: generate a hypothetical answer, embed *that*, retrieve documents similar to it.
6. **Multi-vector / ColBERT**: store multiple embeddings per chunk (one per token-cluster) for finer-grained matching.

## 🎤 Interview questions

1. **Vector DB choices and trade-offs?** FAISS (lib, CPU/GPU), pgvector (Postgres extension), Pinecone (managed), Weaviate, Qdrant, Milvus, Chroma. Pick by infra, scale, filter needs.
2. **HNSW vs IVF-PQ?** HNSW: higher recall, more RAM. IVF-PQ: smaller memory via product quantisation, slightly lower recall.
3. **How do you evaluate RAG?** Ragas / TruLens style: faithfulness, answer relevance, context relevance + traditional Recall@k.
4. **When NOT to use RAG?** Tasks needing reasoning over the whole corpus (e.g. "summarise everything"); use fine-tuning or long-context instead.
5. **Chunk boundary problem?** Important info split across chunks → retrieval misses. Mitigations: overlap, sliding window, parent-doc retrieval.
6. **HyDE intuition?** Search for the *answer* shape, not the query — bridges the query/document distribution gap.

## 📚 References
- "Efficient and robust approximate nearest neighbor search using HNSW graphs" (Malkov & Yashunin, 2018)
- "Dense Passage Retrieval" (Karpukhin et al., 2020)
- Ragas docs; LlamaIndex / LangChain RAG patterns
"""),
}

for fname, (imgs, extra) in PLAN.items():
    p = ROOT / fname
    if not p.exists():
        print("MISSING:", fname); continue
    text = p.read_text(encoding="utf-8")
    lines = text.split("\n"); out = []; inserted = False
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
