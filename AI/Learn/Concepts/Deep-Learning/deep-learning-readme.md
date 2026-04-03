# Deep Learning

> Reference for deep learning architectures, embeddings, the Transformer architecture, and LLM foundations.
> See [ai-llm-readme.md](ai-llm-readme.md) for LLM-specific notes and [ai-readme.md](ai-readme.md) for the full taxonomy.

## Neural Network Architectures

```
Input → [Embedding / Feature Extraction] → [Architecture] → Output

Architectures:
  FNN    — Feedforward: tabular data, general-purpose
  CNN    — Convolutional: images, audio spectrograms, local patterns
  RNN    — Recurrent: sequences (replaced by Transformers for most tasks)
  LSTM   — Long Short-Term Memory: long sequences, time series
  GRU    — Gated Recurrent Unit: faster LSTM alternative
  Transformer — Attention-based: NLP, vision, audio, multi-modal
  Autoencoder — Encoder-decoder: compression, anomaly detection, generation
  GAN    — Generative Adversarial Network: image/data generation
  GNN    — Graph Neural Network: graph-structured data
  Diffusion — Iterative denoising: image/audio/video generation
```

## Transformer Architecture

```
Input Tokens
    │
    ▼
Token Embeddings + Positional Encoding
    │
    ▼
┌─────────────────────────────────┐
│         Encoder Block (×N)      │  ← BERT uses encoder only
│  Multi-Head Self-Attention       │
│  Add & Norm                     │
│  Feed-Forward Network           │
│  Add & Norm                     │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│         Decoder Block (×N)      │  ← GPT uses decoder only
│  Masked Multi-Head Self-Attention│
│  Add & Norm                     │
│  Cross-Attention (enc output)   │
│  Add & Norm                     │
│  Feed-Forward Network           │
│  Add & Norm                     │
└─────────────────────────────────┘
    │
    ▼
Linear + Softmax → Output Probabilities
```

### Self-Attention (Scaled Dot-Product)

```
Attention(Q, K, V) = softmax(QKᵀ / √d_k) · V

Q = Query  (what am I looking for?)
K = Key    (what do I have?)
V = Value  (what do I return?)
d_k = dimension of keys (scaling factor)

Multi-Head: run h attention heads in parallel, concatenate, project
```

### Positional Encoding
- Transformers have no inherent sequence order → must inject position
- Sinusoidal (original): fixed, deterministic
- Learned (BERT, GPT): trained embeddings per position
- RoPE (Rotary): used in LLaMA, GPT-NeoX — relative position via rotation
- ALiBi: linear bias on attention scores — better length generalisation

---

## Key Architecture Comparisons

| Architecture | Encoder | Decoder | Best For |
|---|---|---|---|
| BERT | ✅ | ❌ | Classification, NER, QA (understanding) |
| GPT | ❌ | ✅ | Text generation (left-to-right) |
| T5 / BART | ✅ | ✅ | Translation, summarisation, seq2seq |
| ViT | ✅ | ❌ | Image classification (patches as tokens) |
| DALL-E / Stable Diffusion | ✅ | ✅ | Text-to-image generation |
| Whisper | ✅ | ✅ | Speech recognition |

---

## Embeddings

> Numerical vector representations of data (text, images, audio) that capture semantic meaning.
> Used heavily in RAG and vector search — see [ai-rag.md](ai-rag.md), [!Pinecone](../!Pinecone/), [!Chroma](../!Chroma/).

### Common Dimensions
| Use Case | Typical Dimensions |
|---|---|
| Word2Vec / GloVe | 100–300 |
| Sentence-BERT | 384–768 |
| OpenAI text-embedding-3-small | 1536 |
| OpenAI text-embedding-3-large | 3072 |
| CLIP (images) | 512–768 |

### Distance Metrics for Embeddings
| Metric | Formula | Best For |
|---|---|---|
| Cosine Similarity | cos(θ) = A·B / (‖A‖‖B‖) | Text, most embeddings (magnitude-invariant) |
| Dot Product | A · B | When vectors are normalised (= cosine) |
| Euclidean Distance | ‖A - B‖₂ | When magnitude matters |
| Manhattan Distance | Σ|Aᵢ - Bᵢ| | Sparse high-dimensional vectors |

### Embedding Models
| Model | Type | Notes |
|---|---|---|
| Word2Vec | Word | Static embeddings, no context |
| GloVe | Word | Global co-occurrence statistics |
| FastText | Subword | Handles OOV words |
| BERT (CLS token) | Sentence | Contextual, bidirectional |
| Sentence-BERT | Sentence | Fine-tuned for semantic similarity |
| text-embedding-3 (OpenAI) | Sentence | High quality, API-based |
| BGE / E5 | Sentence | Open-source SOTA for retrieval |

---

## Activation Functions

| Function | Formula | Use Case |
|---|---|---|
| ReLU | max(0, x) | Default for hidden layers |
| Leaky ReLU | max(0.01x, x) | Avoid dying ReLU |
| GELU | x·Φ(x) | Transformers (BERT, GPT) |
| SiLU / Swish | x·σ(x) | LLaMA, EfficientNet |
| Sigmoid | 1/(1+e⁻ˣ) | Binary output layer |
| Softmax | eˣⁱ/Σeˣʲ | Multiclass output layer |
| Tanh | (eˣ-e⁻ˣ)/(eˣ+e⁻ˣ) | RNNs, normalised range [-1,1] |

## Loss Functions

| Loss | Use Case |
|---|---|
| Cross-Entropy | Classification |
| Binary Cross-Entropy | Binary classification |
| MSE | Regression |
| MAE | Regression (robust to outliers) |
| Huber Loss | Regression (combines MSE+MAE) |
| KL Divergence | VAEs, knowledge distillation |
| Contrastive Loss | Metric learning, siamese networks |
| Triplet Loss | Embedding learning (face recognition) |

## Optimisers

| Optimiser | Notes |
|---|---|
| SGD | Classic, use with momentum + LR schedule |
| Adam | Adaptive LR — default for most DL |
| AdamW | Adam + weight decay fix — default for LLMs |
| RMSprop | Good for RNNs |
| Adagrad | Sparse data |
| LAMB | Large-batch training (BERT pre-training) |

## Regularisation Techniques

| Technique | How It Works |
|---|---|
| Dropout | Randomly zero activations during training |
| L1 / L2 Weight Decay | Penalise large weights |
| Batch Normalisation | Normalise layer inputs — faster training |
| Layer Normalisation | Normalise across features — used in Transformers |
| Early Stopping | Stop when validation loss stops improving |
| Data Augmentation | Artificially expand training data |
| Gradient Clipping | Cap gradient norms to prevent exploding gradients |

---

## Pre-training vs Fine-tuning vs PEFT

```
Pre-training
  └── Train from scratch on massive data
  └── Very expensive (GPU weeks/months)
  └── Examples: BERT, GPT, LLaMA

Full Fine-tuning
  └── Update all weights on task-specific data
  └── Expensive, risk of catastrophic forgetting

PEFT (Parameter-Efficient Fine-Tuning)       → see ai-llm-readme.md
  ├── LoRA    — Low-Rank Adaptation: train small rank decomposition matrices
  ├── QLoRA   — LoRA on quantised base model (4-bit)
  ├── Prefix Tuning — Prepend trainable tokens to input
  ├── Prompt Tuning — Learnable soft prompt tokens
  └── Adapter Layers — Small bottleneck layers between frozen layers
```

---

## Vector Databases

> Store and search high-dimensional embeddings at scale.
> See [!Pinecone](../!Pinecone/) and [!Chroma](../!Chroma/) for dedicated notes.

| Database | Notes |
|---|---|
| Pinecone | Managed, production-grade, fast ANN search |
| Chroma | Open-source, lightweight, good for prototyping |
| Weaviate | Open-source, hybrid search, graph capabilities |
| Qdrant | Open-source, Rust-based, high performance |
| FAISS (Meta) | Library (not a DB), exact + approximate search |
| pgvector | Vector extension for PostgreSQL |

---

## KNN vs Vector DB Top-K

| | KNN (Classical ML) | Top-K (Vector DB / RAG) |
|---|---|---|
| Goal | Classification / regression | Retrieve k most similar items |
| Search | Exhaustive (exact) | Approximate Nearest Neighbor (ANN) |
| Scale | Small-medium datasets | Millions–billions of vectors |
| Used in | scikit-learn | [!Pinecone](../!Pinecone/), [!Chroma](../!Chroma/), RAG pipelines |

---

## References

- [ai-readme.md](ai-readme.md) — Full AI taxonomy
- [ai-llm-readme.md](ai-llm-readme.md) — LLM families, fine-tuning, quantisation
- [ai-rag.md](ai-rag.md) — RAG pipeline
- [!Pinecone](../!Pinecone/) — Pinecone vector DB notes
- [!Chroma](../!Chroma/) — Chroma vector DB notes
- [!HuggingFace](../!HuggingFace/) — HuggingFace Transformers library
- [Attention Is All You Need (paper)](https://arxiv.org/abs/1706.03762)
- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)
