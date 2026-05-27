# Transformers & Attention -- Deep Notes

## 1. The problem transformers solved

Before transformers, sequence modeling used **RNNs / LSTMs**, which processed tokens *sequentially* -- token `t` had to wait for `t-1`. This meant:
- Training couldn't be parallelized across the sequence axis (slow on GPUs).
- Long-range dependencies decayed through many gating steps (vanishing gradient).
- Translation systems used encoder-decoder LSTMs with attention bolted on for source-side context.

The 2017 paper **"Attention Is All You Need"** (Vaswani et al.) showed you could drop the RNN entirely and rely *only* on attention, getting better results on WMT 2014 En->De translation with far less training time.

## 2. The attention mechanism, step by step

Given input `X in ℝ^{n x d_model}` (n tokens, each a `d_model`-dim vector):

1. **Project to Q, K, V**: `Q = XW_Q`, `K = XW_K`, `V = XW_V`, each `n x d_k` (or `n x d_v` for V; typically `d_k = d_v = d_model / h` per head).
2. **Scores**: `S = QKᵀ / sqrtd_k` shape `n x n`. `S[i, j]` = how much token `i` attends to token `j`.
3. **Mask** (decoder): set `S[i, j] = -inf` for `j > i` so future tokens are invisible.
4. **Softmax row-wise**: `A = softmax(S)`, each row sums to 1.
5. **Weighted sum**: `Out = AV`, shape `n x d_v`.

### Why scale by sqrtd_k?

If `q, k` are i.i.d. with variance 1, the dot product `q * k = Sigma q_i k_i` has variance `d_k`. Large variance pushes the softmax into a near-one-hot regime, where gradients become ~0 for all-but-one entry. Dividing by `sqrtd_k` normalizes variance back to 1.

### Why multi-head?

Instead of one `d_model x d_model` attention, split into `h` heads each of dim `d_model/h`. Each head learns to attend differently -- e.g. one head tracks coreference, another tracks syntactic dependency, another tracks position offsets. Concatenate the `h` outputs and project through `W_O`.

```
MHA(X) = Concat(head_1, ..., head_h) W_O
head_i = Attention(X W_Q^i, X W_K^i, X W_V^i)
```

## 3. The full transformer block (encoder)

```
y = LayerNorm(x + MHA(x))      # Post-LN (original paper)
z = LayerNorm(y + FFN(y))
```

Modern LLMs use **Pre-LN** for stability at depth:
```
y = x + MHA(LN(x))
z = y + FFN(LN(y))
```

The **FFN** is two linear layers with a non-linearity in between, applied per token:
```
FFN(x) = GeLU(x W_1 + b_1) W_2 + b_2
```
where `W_1 in ℝ^{d x 4d}`. Llama-family models replace `GeLU` with **SwiGLU**:
```
FFN(x) = (Swish(x W_gate) (.) x W_up) W_down
```
This needs *three* weight matrices but is empirically better per parameter.

## 4. Residual + normalization

Residuals (`x + sublayer(x)`) give a gradient highway from output back to embedding -- without them, depths >6 don't train. LayerNorm stabilizes activations per-token (mean & variance across feature dim).

**RMSNorm** drops mean subtraction: `RMSNorm(x) = x / sqrt(mean(x^2) + epsilon) * g`. Faster, equally good in practice -> used in Llama, Mistral, GPT-NeoX.

## 5. Positional encoding deep dive

Self-attention is *permutation-equivariant* -- without positions, "dog bites man" = "man bites dog". You inject position somehow:

### Sinusoidal (original)
```
PE(pos, 2i)   = sin(pos / 10000^{2i/d})
PE(pos, 2i+1) = cos(pos / 10000^{2i/d})
```
Added to token embeddings. Different frequencies let the model learn relative offsets via linear combinations.

### Learned absolute (BERT, GPT-2)
`PE = nn.Embedding(max_len, d_model)`. Simpler, but doesn't generalize beyond `max_len`.

### RoPE -- Rotary Positional Embedding (Llama, Mistral, Qwen)
Instead of adding to embeddings, *rotate* Q and K vectors by an angle `m*theta` where `m` is the position. Two key properties:
- Dot product `q_m * k_n` depends only on `m - n` (true relative position).
- Generalizes to positions beyond training (with NTK/YaRN scaling tricks).

### ALiBi (Attention with Linear Biases)
No positional embedding at all. Instead, add a linear penalty to attention scores based on distance: `S[i,j] -= m * (i - j)` where `m` is a per-head slope. Cheap, extrapolates well.

## 6. Encoder vs decoder vs encoder-decoder

| Architecture | Attention | Pre-trained objective | Best for |
|--------------|-----------|-----------------------|----------|
| **Encoder-only** (BERT) | Bidirectional | Masked LM | Classification, NER, embeddings |
| **Decoder-only** (GPT) | Causal | Next-token prediction | Generation, chat, code |
| **Enc-Dec** (T5, BART) | Bi + Causal + Cross | Span corruption / denoising | Translation, summarization |

**Why is decoder-only the dominant LLM design?** Single training objective (next-token), scales cleanly, and zero-shot generalization is great. Encoder-decoders are still better at machine translation per parameter but rare at >70B scale.

## 7. Complexity & memory

- **Self-attention compute**: O(n^2 * d) -- bottleneck for long context.
- **Memory** for attention scores: O(n^2 * h). At n=8192 and h=64 this is gigabytes per layer.
- **FlashAttention** (Dao 2022): recomputes attention in tiled blocks, never materializing the nxn matrix. Same math, ~3x faster, much less memory.
- **Sliding-window / sparse / linear attention** (Longformer, Mamba): trade exact attention for sub-quadratic cost.

## 8. Training details that get asked

- **Tokenizer**: BPE / WordPiece / SentencePiece, see [tokenizers cheatsheet](tokenizers-cheatsheet.md).
- **Optimizer**: AdamW, beta1=0.9, beta2=0.95-0.999, weight_decay~=0.1.
- **LR schedule**: linear warmup (~2000 steps), then cosine decay to 10% of peak.
- **Gradient clipping**: norm <= 1.0.
- **Mixed precision**: bf16 for weights & activations, fp32 for optimizer state. fp16 can NaN with attention scores.
- **Initialization**: scaled by depth -- e.g. `1/sqrt(2L)` to keep residual variance constant.
- **Dropout**: ~0.1 in original; large models often drop it (data is more limiting than overfitting).

## 9. Inference details

- During generation, you compute attention for the new token against all previous K, V. Cache previous K, V to avoid recompute -> see [kv-cache cheatsheet](kv-cache-cheatsheet.md).
- **Sampling**: greedy, top-k, top-p (nucleus), temperature. Lower T = more deterministic.
- **Speculative decoding**: small "draft" model proposes k tokens, big model verifies in one forward pass.
- **Prefix caching**: same prompt across requests reuses KV. Used heavily for system-prompt-heavy workloads.

## 10. Common pitfalls

- **Forgetting causal mask in decoder** -- model "cheats" by attending to future tokens, train loss looks great, generation is garbage.
- **Sharing positional embedding with very different `max_len`** -- finetune breaks.
- **Mixing pre-LN and post-LN** in the same model -- divergence.
- **fp16 attention** -- softmax overflows; use bf16 or fp32 softmax with fp16 matmul.
- **Not tying input/output embeddings** -- wastes parameters and hurts small-model perf.

---

## Top 25 interview questions (with model answers)

**1. Walk me through self-attention.**
Given input X, project to Q, K, V. Compute QKᵀ/sqrtd_k, mask if causal, softmax over keys, multiply by V. Output is a weighted average of value vectors, with weights = how much each query attends to each key.

**2. Why scale by sqrtd_k?**
Variance of the dot product grows with d_k. Without scaling, softmax saturates -> near-zero gradients on non-max entries. sqrtd_k normalizes variance back to 1.

**3. Why multi-head attention?**
Each head attends in a different subspace, letting the model capture multiple relation types (syntactic, semantic, positional) simultaneously. Concatenating then projecting recombines them.

**4. Computational complexity of attention?**
O(n^2 * d) compute, O(n^2) memory for the score matrix. The quadratic in n is the long-context bottleneck.

**5. What's the FFN inside a transformer block doing?**
Per-token MLP, typically `d -> 4d -> d` with a non-linearity. It's where most parameters live; it's the model's "key-value memory" -- the place where factual associations are stored (Geva et al. 2020).

**6. Why residual connections?**
Gradient highway -- without them, deep (>6 layers) transformers don't train. Also implements ensemble-like effective depth.

**7. Encoder vs decoder?**
Encoder: bidirectional attention, takes whole sequence, outputs one vector per token. Decoder: causal attention, predicts next token given previous tokens. Use encoder for classification/embeddings, decoder for generation.

**8. Why decoder-only models dominate LLMs?**
Single simple training objective (next-token), scales beautifully, and large decoders match enc-dec on most tasks. Generation only needs one direction anyway.

**9. RoPE vs sinusoidal vs learned positional embeddings?**
Sinusoidal: fixed, generalizes a bit. Learned: trainable embedding per position, doesn't generalize past max_len. RoPE: rotates Q/K by angle ∝ position, encodes *relative* positions, generalizes (with YaRN) and is now the default.

**10. What is ALiBi?**
Attention with Linear Biases -- adds a distance-proportional penalty to attention scores per head, no positional embedding at all. Extrapolates well to longer contexts.

**11. Pre-LN vs Post-LN -- which is better and why?**
Pre-LN (`x + sublayer(LN(x))`): better gradient flow at depth, trains stably without warmup tuning. Post-LN: original paper's design, needs careful warmup at depth but slightly better perf if trained well. Modern LLMs use Pre-LN.

**12. RMSNorm vs LayerNorm?**
RMSNorm drops mean centering; just `x / sqrt(mean(x^2)+epsilon) * g`. ~10-30% faster, no quality loss in practice. Standard in Llama family.

**13. What is the KV cache?**
At generation time, K and V for all past tokens are cached so each new token only computes its own Q, K, V and a single attention step over the cache. Without it, generation is O(n^2*t) per step instead of O(n*t).

**14. Memory cost of KV cache?**
`2 * seq_len * n_layers * n_heads * d_head * dtype_bytes`. For Llama-70B at 8k context in fp16: ~10-20 GB per sequence.

**15. What is FlashAttention?**
A fused attention kernel that tiles Q/K/V into SRAM and computes softmax-attention incrementally, never materializing the nxn score matrix. Same math, much faster + less memory.

**16. Why is attention permutation-equivariant?**
Self-attention treats input as a set -- without positional info, shuffling input rows shuffles output rows identically. Positional encoding breaks the symmetry.

**17. What does the softmax + value step compute geometrically?**
Each output token is a convex combination of value vectors, weighted by query-key similarity. It's a learned, content-addressable memory read.

**18. What is causal masking?**
For autoregressive decoding, you can't let token `i` attend to token `j > i`. Set `S[i,j] = -inf` before softmax so those positions contribute 0.

**19. Why does dropping the encoder work for chat models?**
Chat is fundamentally next-token prediction conditioned on a long prompt. The prompt itself plays the role the encoder used to. Cross-attention between encoder and decoder isn't needed.

**20. Compare GeLU vs ReLU vs SwiGLU.**
ReLU: simple, dead-neuron risk. GeLU: smooth, used in BERT/GPT-2/3. SwiGLU: gated linear unit with Swish, slightly more params (3 matrices vs 2) but better quality per parameter; Llama default.

**21. Why does Pre-LN need a final LayerNorm at the output?**
With Pre-LN, the residual stream accumulates un-normalized contributions. A final LN before the output projection rescales it.

**22. How do you parallelize transformer training?**
Data parallel (replicate model, split batch), tensor parallel (shard heads/FFN across GPUs), pipeline parallel (split layers), ZeRO (shard optimizer state). At >70B, you typically combine all three (3D parallelism).

**23. Why are biases often removed in modern LLMs?**
Saves params and slightly improves stability; LayerNorm/RMSNorm already centers. Llama removes them from linear layers.

**24. What's weight tying?**
The input embedding matrix and the output (LM head) matrix share weights. Saves params (~vocab_size x d), and ties the semantics of token -> vector and vector -> token.

**25. What problem does grouped-query attention (GQA) solve?**
KV cache memory is dominated by `n_kv_heads`. GQA uses fewer KV heads than Q heads (e.g. 8 KV vs 32 Q in Llama-2-70B). Same quality, 4x smaller KV cache. **MQA** is the extreme: 1 KV head.

---

## References

- **Paper**: [Attention Is All You Need](https://arxiv.org/abs/1706.03762) (Vaswani et al., 2017)
- **Tutorial**: [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) -- Jay Alammar
- **Video**: [Let's build GPT from scratch](https://www.youtube.com/watch?v=kCc8FmEb1nY) -- Andrej Karpathy
- **Paper**: [RoFormer (RoPE)](https://arxiv.org/abs/2104.09864)
- **Paper**: [FlashAttention](https://arxiv.org/abs/2205.14135) -- Tri Dao
- **Paper**: [GQA: Training Generalized Multi-Query Transformer](https://arxiv.org/abs/2305.13245)
- **Paper**: [Roformer/RoPE explained](https://kexue.fm/archives/8265) -- Su Jianlin's blog (the inventor)
- **Codebase**: [nanoGPT](https://github.com/karpathy/nanoGPT) -- minimal, readable GPT in ~300 lines
- **Codebase**: [llama-from-scratch](https://github.com/bkitano/llama-from-scratch) -- full Llama re-implementation
- **Course**: [Stanford CS25 -- Transformers United](https://web.stanford.edu/class/cs25/)
- **Visual**: [Transformer Explainer](https://poloclub.github.io/transformer-explainer/) -- interactive
