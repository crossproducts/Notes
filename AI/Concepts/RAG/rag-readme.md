# RAG — Retrieval-Augmented Generation

> RAG grounds LLM responses in external knowledge, reducing hallucinations and enabling up-to-date answers.
> See [ai-llm-readme.md](ai-llm-readme.md) for LLM details and [ai-prompt-engineering.md](ai-prompt-engineering.md) for RAG prompting.
> Vector DB notes: [!Pinecone](../!Pinecone/) · [!Chroma](../!Chroma/)

## RAG Pipeline

```
INDEXING (offline)
  Documents
      │
      ▼
  Chunking  ──────────────────────────────────────────────┐
      │                                                    │
      ▼                                                    │
  Embedding Model                                          │
  (text → dense vector)                                    │
      │                                                    │
      ▼                                                    │
  Vector Store  (Pinecone / Chroma / Weaviate / FAISS)    │
  (store vector + metadata + original chunk text) ◄────────┘

QUERYING (online / real-time)
  User Query
      │
      ▼
  Query Embedding
      │
      ▼
  Vector Search  (ANN: cosine / dot product)
      │
      ▼
  Top-K Retrieved Chunks
      │
      ▼
  (Optional) Re-ranking
      │
      ▼
  Prompt Assembly
  ┌────────────────────────────┐
  │ System: Answer from context│
  │ Context: [chunk1][chunk2]  │
  │ User: {question}           │
  └────────────────────────────┘
      │
      ▼
  LLM Generation
      │
      ▼
  Response (grounded in retrieved docs)
```

## Chunking Strategies

| Strategy | Description | Best For |
|---|---|---|
| Fixed-size | Split every N characters/tokens | Simple baseline |
| Sentence splitter | Split on sentence boundaries | General text |
| Recursive character | Split on paragraphs → sentences → words | Structured docs |
| Semantic chunking | Embed sentences, group by similarity | High-quality retrieval |
| Document-aware | Respect doc structure (headings, sections) | PDFs, HTML |
| Parent-child | Store small chunks, retrieve parent context | Precision + context |

**Chunk size trade-off:**
- Small chunks (128–256 tokens) → precise retrieval, less context per chunk
- Large chunks (512–1024 tokens) → more context, noisier retrieval
- Typical sweet spot: 256–512 tokens with 10–20% overlap

## Embedding Model Selection

| Model | Dims | Notes |
|---|---|---|
| text-embedding-3-small (OpenAI) | 1536 | Good quality, API-based |
| text-embedding-3-large (OpenAI) | 3072 | Best OpenAI quality |
| BGE-M3 | 1024 | Open-source SOTA, multilingual |
| E5-mistral-7b | 4096 | Strong open model |
| all-MiniLM-L6-v2 | 384 | Fast, lightweight |
| BAAI/bge-large-en-v1.5 | 1024 | Strong English retrieval |

## Retrieval Strategies

| Strategy | Description |
|---|---|
| Dense retrieval | Semantic vector similarity search |
| Sparse retrieval | BM25 / TF-IDF keyword matching |
| Hybrid search | Combine dense + sparse (Reciprocal Rank Fusion) |
| Multi-query | Generate multiple query reformulations, merge results |
| HyDE | Generate hypothetical answer, embed it, search with that |
| Re-ranking | Cross-encoder re-scores top-K candidates for precision |

## Advanced RAG Patterns

### Parent-Document Retrieval
```
Index: small child chunks (for precise matching)
Retrieve: parent document chunk (for full context)
```

### Self-RAG
Model decides when retrieval is needed, critiques retrieved docs, and self-reflects on output.

### Corrective RAG (CRAG)
Evaluates retrieved doc relevance; if poor, triggers web search for fresh context.

### Agentic RAG
RAG inside an agent loop — see [ai-agent-readme.md](ai-agent-readme.md) and [!LangGraph](../!LangGraph/).

## RAG Evaluation (RAGAS Metrics)

| Metric | Measures |
|---|---|
| Faithfulness | Are all claims in the answer supported by the retrieved context? |
| Answer Relevancy | Is the answer relevant to the question? |
| Context Precision | What fraction of retrieved chunks were actually useful? |
| Context Recall | Did retrieval find all necessary information? |
| Answer Correctness | End-to-end correctness vs. ground truth |

```bash
pip install ragas
```

## Common Failure Modes

| Failure | Cause | Fix |
|---|---|---|
| Hallucination | LLM ignores context | Stronger system prompt, lower temperature |
| Missing relevant chunks | Poor chunking or embedding | Tune chunk size, better embedding model |
| Irrelevant retrieval | Semantic mismatch | Hybrid search, query rewriting |
| Context too long | Too many chunks retrieved | Lower top-K, re-rank, parent-doc retrieval |
| Stale knowledge | Index not updated | Incremental indexing, metadata filtering by date |

## References

- [ai-llm-readme.md](ai-llm-readme.md) — LLM selection and context windows
- [ai-prompt-engineering.md](ai-prompt-engineering.md) — RAG prompt templates
- [ai-agent-readme.md](ai-agent-readme.md) — Agentic RAG
- [ai-ml-dl-readme.md](ai-ml-dl-readme.md) — Embeddings and vector DBs
- [!Pinecone](../!Pinecone/) — Pinecone vector DB notes
- [!Chroma](../!Chroma/) — Chroma vector DB notes
- [!LangChain](../!LangChain/) — RAG chains in LangChain
- [!LangGraph](../!LangGraph/) — Agentic RAG graphs
- [RAGAS Documentation](https://docs.ragas.io/)
