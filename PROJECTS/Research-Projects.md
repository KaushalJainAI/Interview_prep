# Research Projects — Deep Learning (Academic)

**Interview Notes (deep dive).**

> Note: reconstructed from the project profile (no source code read for this file). The ML reasoning, architecture choices, complexity, and failure modes are accurate to how these problems are correctly approached; verify dataset-specific numbers against your own records before quoting them.

> One-line pitch: *"Three deep-learning research projects, each on a different hard data type — audio (voice disorders), brain time-series (autism fMRI), and faint imaging (ancient scroll ink). Together they show I can pick the right architecture for the data: CNN for images/spectrograms, LSTM for sequences, segmentation for pixel-level tasks."*

These give **academic depth** and prove I understand *why* an architecture fits a problem — not just how to call `model.fit()`.

---

## A. Voice Disorder Classification (FEMH dataset)

**Problem:** classify a voice recording into disorder categories (multi-class) — e.g. healthy vs specific vocal pathologies — from audio.

### Approach
- **Audio → spectrogram.** Raw audio is a 1-D waveform; I convert it to a **spectrogram** (e.g. mel-spectrogram), which is a 2-D time-frequency image. This is the key move: it turns an audio problem into an **image problem** a CNN is great at.
- **CNN** over the spectrogram to learn disorder-specific frequency/time patterns (a damaged voice has characteristic harmonics/noise).
- **Ensemble with metadata.** I combined the CNN's audio features with patient **metadata** (e.g. age/sex) in an **ensemble**, because some signal lives outside the audio. Ensembling two weak-but-different views usually beats either alone.

### Why these decisions
- **Spectrogram + CNN over raw-waveform models:** CNNs exploit local 2-D structure; a mel-spectrogram is perceptually meaningful and compact. Raw-waveform nets (e.g. 1-D CNNs) need far more data and compute.
- **Ensembling:** audio model and metadata model make *different* errors → combining reduces variance.

### Where it could fail / guards
| Failure | Guard |
|---|---|
| **Class imbalance** (rare disorders) | class weighting / resampling; report per-class recall, not just accuracy |
| **Overfitting** to recording conditions (mic, room) | augmentation (time/freq masking, noise), regularization |
| **Leakage** (same speaker in train+test) | split by speaker, not by clip |
| **Misleading accuracy** on imbalanced data | use macro-F1 / confusion matrix |

**Complexity note:** spectrogram conversion is an **FFT — O(n log n)** per window. CNN cost scales with image size × channels × filters; mel-spectrograms keep the "image" small, so training stays tractable.

---

## B. Autism Detection from fMRI (LSTM + Autoencoder)

**Problem:** classify subjects (autistic vs control) from **fMRI** brain-activity time-series.

### The core challenge: dimensionality
fMRI is **huge and noisy** — thousands of brain-region signals over time, with very few subjects. That's the classic **"curse of dimensionality"**: more features than samples → models overfit and memorize noise.

### Approach
- **Autoencoder for dimensionality reduction.** I trained an **autoencoder** to compress the high-dimensional fMRI signal into a small **latent representation** that keeps the important structure and drops noise. This is unsupervised — it learns a compact code without needing labels.
- **LSTM for the sequence.** fMRI is temporal (brain activity over time), so I fed the reduced representation into an **LSTM** that models how activity evolves — temporal patterns differ between groups.

### Why these decisions
- **Autoencoder vs PCA:** PCA only captures *linear* structure; an autoencoder learns **non-linear** compression, which fits brain dynamics better. (If asked, I can contrast: PCA is faster and more interpretable; autoencoder is more expressive but needs more care.)
- **LSTM over a plain feed-forward net:** the data is a sequence; order matters. An LSTM carries state across time steps and handles variable-length sequences.

### Where it could fail / guards
| Failure | Guard |
|---|---|
| **Overfitting** (few subjects, many features) | autoencoder compression + dropout + heavy regularization + cross-validation |
| **Leakage** (same subject's scans in train+test) | split by subject |
| **Tiny dataset → unstable metrics** | k-fold CV, report mean ± std, not a single number |
| **Autoencoder discards signal** | tune latent size; validate that downstream accuracy holds |

**Complexity note:** LSTM is **O(T × H²)** (T = time steps, H = hidden size) — the squared hidden term is why reducing input dimensionality first (autoencoder) matters: it shrinks the effective work and the overfitting surface.

---

## C. Ink Detection — Vesuvius Challenge (CNN Segmentation)

**Problem:** detect **ink** on carbonized, rolled-up ancient papyrus scrolls from **3-D X-ray (CT) scans** — find which pixels are ink vs blank. The ink is nearly invisible (extremely **low contrast**, multi-layer volume).

### Approach
- **Segmentation, not classification.** The task is per-pixel ("is *this* pixel ink?"), so it's a **semantic segmentation** problem — a **U-Net-style CNN** (encoder-decoder with skip connections) that outputs a mask the same size as the input.
- **Multi-layer input.** The scroll is a 3-D volume; I use multiple depth layers as input channels so the model sees through the material.

### Why these decisions
- **U-Net for segmentation:** the encoder captures context ("where are we on the scroll"), the decoder restores resolution, and **skip connections** preserve fine detail — essential for faint, thin ink strokes that a plain CNN would blur away.
- **Patch-based training:** the scans are gigantic; I train on **patches/tiles** rather than the whole image (which wouldn't fit in GPU memory), then stitch predictions.

### Where it could fail / guards
| Failure | Guard |
|---|---|
| **Extreme class imbalance** (ink is a tiny fraction of pixels) | Dice / focal loss instead of plain cross-entropy; these focus on the rare positive class |
| **Low contrast → model sees nothing** | normalization/contrast enhancement; use multiple depth layers |
| **Patch-edge artifacts** when stitching | overlapping patches + blending at borders |
| **Overfitting to one scroll fragment** | augmentation (rotation/flip), train across fragments |

**Complexity note:** segmentation cost scales with **image area × channels**; CT volumes are massive, so **patching** isn't optional — it's the only way to fit in memory. The decision to tile is a direct memory/compute constraint, a good "space complexity in practice" example.

---

## D. The unifying theme (say this to tie it together)

> *"Each project taught me to match architecture to data shape: 2-D structure → CNN; sequence → LSTM; high-dimensional + noisy → reduce first (autoencoder); per-pixel output → U-Net segmentation. And across all three, the same disciplines mattered most: prevent leakage (split by speaker/subject/fragment), handle class imbalance with the right loss/metric, and fight overfitting because the datasets are small."*

## E. Likely follow-ups
- *"Why spectrogram + CNN instead of a 1-D audio model?"* → 2-D local structure, perceptually meaningful, data-efficient.
- *"Autoencoder vs PCA?"* → non-linear vs linear compression; autoencoder more expressive, PCA faster/interpretable.
- *"Why U-Net for ink?"* → skip connections preserve fine detail needed for faint thin strokes.
- *"Your datasets are small — how do you trust results?"* → grouped splits to stop leakage, k-fold CV with mean±std, right metrics for imbalance (macro-F1, Dice).
- *"Biggest lesson?"* → architecture follows the data; and rigorous validation matters more than model fanciness on small datasets.

---

## F. Testing & validation (the part that separates good research from misleading research)

> Strategy section — how these models should be validated. On small academic datasets, *validation rigor matters more than the model*, so this is worth talking about confidently.

**The single biggest risk in all three projects is reporting a number that doesn't generalize.** My testing discipline is built around preventing that:

| Discipline | Voice (audio) | Autism (fMRI) | Ink (segmentation) |
|---|---|---|---|
| **Grouped split (no leakage)** | split by **speaker** | split by **subject** | split by **scroll fragment** |
| **Right metric for imbalance** | macro-F1, per-class recall, confusion matrix | balanced accuracy + AUC | **Dice / IoU** (not pixel accuracy) |
| **Small-data honesty** | k-fold CV, mean ± std | k-fold CV, mean ± std | cross-fragment validation |
| **Overfitting guard** | augmentation, dropout | autoencoder compression + dropout | augmentation, patch overlap |

**Why "test split by group" is the headline:** if the same speaker/subject/fragment appears in both train and test, the model memorizes that individual and the score is fake. Splitting by group is the test that makes the result *trustworthy*. I'd happily explain this as my "a metric that looks great can still be wrong" story.

**Why accuracy is the wrong metric (and what I use instead):**
- Voice/autism: classes are imbalanced, so 90% accuracy can mean "always predict the majority class." → macro-F1 / per-class recall.
- Ink: ink is a tiny fraction of pixels, so a model predicting "no ink" everywhere scores ~99% pixel accuracy but is useless. → **Dice/IoU**, which only reward correctly finding the rare ink pixels.

**Sanity tests I run on the code (not just the model):**
- Overfit a single batch on purpose — if the model *can't* drive training loss to ~0 on one batch, there's a bug in the model/loss wiring.
- Beat a trivial baseline (majority-class / random) — otherwise the model isn't learning.
- Check input pipelines: spectrogram shapes, fMRI normalization, patch stitching at borders.

**What I'd add:** statistical significance testing across CV folds (so I can claim model A > model B with confidence), and ablations (remove the autoencoder / remove metadata ensemble) to prove each component actually helps.
