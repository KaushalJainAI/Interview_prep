# Tokenizers -- Worked Examples

> Companion to [tokenizers-cheatsheet.md](tokenizers-cheatsheet.md). Run these to make BPE/WordPiece concrete.

## 1. Tokenize the same sentence across models

```python
from transformers import AutoTokenizer

sentence = "Kaushal is building AIAAS, an agentic platform."

for name in [
    "bert-base-uncased",                      # WordPiece
    "openai-community/gpt2",                  # byte-level BPE
    "meta-llama/Meta-Llama-3-8B",             # tiktoken-style BPE
    "google/mt5-base",                        # SentencePiece (multilingual)
]:
    tok = AutoTokenizer.from_pretrained(name)
    ids = tok.encode(sentence)
    pieces = tok.convert_ids_to_tokens(ids)
    print(f"\n{name}: {len(ids)} tokens")
    print(pieces)
```

Typical output (token counts):
```
bert-base-uncased   : 15 tokens   ['[CLS]','k','##au','##sha','##l','is','building','ai','##aa','##s',',','an','agent','##ic','platform','.','[SEP]']
openai/gpt2         : 12 tokens   ['Ka','ush','al',' is',' building',' AIA','AS',',',' an',' agent','ic',' platform','.']
meta-llama/Llama-3  : 11 tokens   ['Ka','ush','al',' is',' building',' AI','AAS',',',' an',' agent','ic',' platform','.']
google/mt5-base     : 18 tokens   ['▁Ka','u','sha','l','▁is','▁building','▁A','IA','AS',',','▁an','▁agent','ic','▁platform','.']
```

**Notes**:
- **`##` prefix** in BERT (WordPiece) marks continuation of a previous word.
- **`Ġ` (or space-prefix)** in GPT-2 BPE marks "start of new word" -- `Ġis` is different from `is`.
- **`▁` (U+2581 lower-eighth-block)** in SentencePiece marks word boundary -- language-agnostic.
- **Rare-word "Kaushal"** gets split into 3-4 subwords in every tokenizer because it wasn't in pre-training data as a single token.

## 2. BPE merge process -- toy example

Corpus: `["low", "low", "low", "lower", "newest", "newest", "newest", "widest"]`

### Initial vocab (chars + end-of-word marker `</w>`):
```
{l, o, w, e, r, n, s, t, i, d, </w>}
```

### Pair counts after split:
```
l o w </w>       x 3
l o w e r </w>   x 1
n e w e s t </w> x 3
w i d e s t </w> x 1
```

### Iteration 1 -- most-frequent adjacent pair
| Pair | Count |
|------|-------|
| `(e, s)` | 4 (in "newest" x3 + "widest" x1) |
| `(s, t)` | 4 |
| `(o, w)` | 4 |
| ... | |

Merge `(e, s)` -> new symbol `es`. Corpus becomes:
```
l o w </w>          x 3
l o w e r </w>      x 1
n e w es t </w>     x 3
w i d es t </w>     x 1
```

### Iteration 2
| Pair | Count |
|------|-------|
| `(es, t)` | 4 |
| `(o, w)` | 4 |

Merge `(es, t)` -> `est`. Continue:
```
l o w </w>          x 3
l o w e r </w>      x 1
n e w est </w>      x 3
w i d est </w>      x 1
```

### Iteration 3 -- merge `(o, w)` -> `ow`
```
l ow </w>           x 3
l ow e r </w>       x 1
n e w est </w>      x 3
w i d est </w>      x 1
```

### After enough iterations
Vocab gains: `est`, `ow`, `low`, `est</w>`, `newest`, ...

Common words like `low`, `newest` become single tokens; rare words still decompose.

**That's the entire BPE algorithm.**

## 3. Encoding with the learned merges

To encode `"lower"`:
1. Split into chars: `l o w e r </w>`
2. Apply merges in *learning order*:
   - `ow` -> `l ow e r </w>`
   - (no further merges apply if `lower` wasn't merged)
3. Token sequence: `[l, ow, e, r, </w>]` -> IDs from the vocab table.

The encode operation is **greedy** and runs in O(n) using a priority-queue or precomputed merge table.

## 4. Why byte-level BPE (GPT-2+) handles ANY string

Start vocab is the 256 bytes (0x00-0xFF). Merges happen on byte pairs, not characters. Result: any Unicode string can be encoded -- no `[UNK]`.

```python
emoji = "हिंदी "
ids = gpt2_tok.encode(emoji)
# Works without errors, even though "हिंदी" wasn't in training vocab
# Devanagari chars decompose into UTF-8 byte pairs that BPE handles
```

Tradeoff: non-English text is **more tokens per character**. `"हिंदी"` (5 chars) might be ~10 GPT-2 tokens.

## 5. Special tokens & chat templates

```python
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("meta-llama/Llama-3-8B-Instruct")

messages = [
    {"role":"system",    "content":"You are a helpful assistant."},
    {"role":"user",      "content":"What's RAG?"},
    {"role":"assistant", "content":"Retrieval-augmented generation..."},
]

prompt = tok.apply_chat_template(messages, tokenize=False)
print(prompt)
```
Produces:
```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>

What's RAG?<|eot_id|><|start_header_id|>assistant<|end_header_id|>

Retrieval-augmented generation...<|eot_id|>
```

Chat formatting is a **separate layer** on top of tokenization. The tokenizer carries the chat template; if you build the prompt wrong, you get garbage outputs even if every token id is "correct".

## 6. Tokenizer cost gotchas (real budget math)

For the same English sentence (~12 words):
- GPT-4 tokenizer (`tiktoken cl100k_base`): ~14 tokens
- Llama-3 tokenizer (128k vocab): ~13 tokens
- Older GPT-2: ~17 tokens

For Hindi "नमस्ते दुनिया" (~5 chars):
- GPT-4: 10-14 tokens
- Llama-3: 7-10 tokens (more Indic in training)
- A specialized Indic tokenizer (Sarvam, BharatGPT): 2-4 tokens

**Implication for NGU AI search**: if you process queries in Hindi/Tamil/regional languages, picking a tokenizer with strong Indic coverage **halves your inference cost** and improves embedding quality (tokens are more meaningful units when not over-split).

## 7. Diagnose a glitch token

```python
tok = AutoTokenizer.from_pretrained("openai-community/gpt2")
# Token ID 22186 in GPT-2 = " SolidGoldMagikarp" (rare Reddit username in training)
print(repr(tok.decode([22186])))   # ' SolidGoldMagikarp'

# Embedding for this token is essentially random -- model produces garbage
# when this token appears in inputs.
```
Modern models train on better-curated data + larger vocabs, but rare-token glitches still exist. Worth knowing if you're debugging weird LLM outputs.

## Interview one-liners
- *Why subword over word?* No OOV + tractable vocab (30-200k) + handles rare/new words via composition.
- *BPE in one sentence?* Repeatedly merge the most-frequent adjacent symbol pair, building up subwords.
- *Byte-level BPE?* Start vocab is 256 bytes -- any Unicode is representable, no `[UNK]`.
- *Why `Ġ`/`▁`?* Encode "this token starts a new word" so the tokenizer is reversible (decode round-trips spacing).
- *Chat template != tokenizer?* Chat template wraps messages in special tokens (`<|user|>`, etc.) before tokenization. Wrong template -> wrong outputs even with correct tokens.
- *Why Llama-3 splits digits?* So `12345` always tokenizes as `1 2 3 4 5` -- consistent arithmetic instead of weird BPE chunks like `123 45`.
- *Tokenizer cost matters?* Yes -- same meaning costs 2-4x more tokens in less-supported languages -> directly hits API bill and effective context.
