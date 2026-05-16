# LLMs — Large Language Models

> Reference for LLM model families, context windows, tokenisation, fine-tuning, quantisation, and benchmarks.
> See [ai-ml-dl-readme.md](ai-ml-dl-readme.md) for Transformer architecture internals.
> See [ai-prompt-engineering.md](ai-prompt-engineering.md) for prompting techniques.

## Model Families

| Model Family | Creator | Architecture | Open Source | Context Window | Notes |
|---|---|---|---|---|---|
| GPT-4o / GPT-4 | OpenAI | Decoder-only | ❌ | 128k | Multimodal (text, image, audio) |
| Claude 3.5 / 3 | Anthropic | Decoder-only | ❌ | 200k | Strong reasoning, long context |
| Gemini 1.5 / 2 | Google DeepMind | Decoder-only | ❌ | 1M+ | Multimodal, massive context |
| LLaMA 3 | Meta | Decoder-only | ✅ | 8k–128k | Most popular open-weight base |
| Mistral / Mixtral | Mistral AI | Decoder-only / MoE | ✅ | 32k | Fast, efficient, MoE architecture |
| Gemma 2 | Google | Decoder-only | ✅ | 8k | Lightweight open model |
| Phi-3 | Microsoft | Decoder-only | ✅ | 4k–128k | Small but strong |
| Qwen 2.5 | Alibaba | Decoder-only | ✅ | 128k | Strong multilingual |
| DeepSeek-V3 | DeepSeek | MoE | ✅ | 128k | High capability open MoE |
| Command R+ | Cohere | Decoder-only | ❌ | 128k | Optimised for RAG |

## Tokenisation

```
Text → Tokens → Token IDs → Embeddings

"Hello, world!" → ["Hello", ",", " world", "!"] → [9906, 11, 1917, 0]

Rule of thumb: ~1 token ≈ 0.75 words (English)
               ~100 tokens ≈ 75 words ≈ 1 short paragraph
```

| Algorithm | Used By | Notes |
|---|---|---|
| BPE (Byte-Pair Encoding) | GPT, LLaMA, Mistral | Merges frequent byte pairs |
| WordPiece | BERT | Similar to BPE, different merging criterion |
| SentencePiece | T5, Gemma, many open models | Language-agnostic, works on raw text |
| Tiktoken | OpenAI GPT models | Fast BPE implementation |

## Training Stages

```
1. Pre-training
   └── Next-token prediction on trillions of tokens
   └── Learns language, facts, reasoning
   └── Output: Base Model

2. Supervised Fine-Tuning (SFT)
   └── Train on (instruction, response) pairs
   └── Output: Instruction-following model

3. RLHF — Reinforcement Learning from Human Feedback
   ├── Collect human preference data (A vs B responses)
   ├── Train Reward Model on preferences
   └── Optimise policy with PPO to maximise reward
       └── Output: Helpful, aligned assistant

4. DPO — Direct Preference Optimisation (simpler RLHF alternative)
   └── Directly optimises on preference pairs without separate RM
```

## Fine-Tuning Approaches

| Method | Description | GPU RAM | When to Use |
|---|---|---|---|
| Full Fine-tuning | Update all weights | Very High | Enough data + compute |
| LoRA | Train low-rank decomposition matrices only | Medium | Most common PEFT choice |
| QLoRA | LoRA on 4-bit quantised model | Low | Consumer GPU fine-tuning |
| Prefix Tuning | Prepend trainable token vectors | Low | Limited data |
| Prompt Tuning | Learn soft prompt embeddings only | Very Low | Very limited data |
| Adapter Layers | Small bottleneck modules between frozen layers | Low | Multi-task fine-tuning |

### LoRA Explained
```
Original weight: W (d × k)
LoRA update:     W + BA  where B (d × r), A (r × k), rank r << min(d,k)

Only A and B are trained — reduces trainable params by 100–1000x
```

## Quantisation

| Format | Bits | Memory Reduction | Quality Loss | Tool |
|---|---|---|---|---|
| FP32 | 32-bit | 1× (baseline) | None | Default |
| FP16 / BF16 | 16-bit | 2× | Minimal | PyTorch, transformers |
| INT8 | 8-bit | 4× | Small | bitsandbytes, llm.int8() |
| INT4 (GPTQ) | 4-bit | 8× | Moderate | AutoGPTQ |
| INT4 (GGUF) | 4-bit | 8× | Moderate | llama.cpp |
| 2-bit | 2-bit | 16× | Significant | QuIP#, AQLM |

## Inference Optimisation

| Technique | Description |
|---|---|
| KV Cache | Cache key/value attention states to avoid recomputation |
| Continuous Batching | Dynamic request batching for higher GPU utilisation |
| Paged Attention | Memory-efficient KV cache (vLLM) |
| Speculative Decoding | Draft model proposes tokens, main model verifies in parallel |
| Flash Attention | IO-aware attention kernel — faster, less memory |
| Tensor Parallelism | Split model across multiple GPUs (columns/rows) |
| Pipeline Parallelism | Split model layers across GPUs |

### Inference Frameworks
| Framework | Notes |
|---|---|
| vLLM | Production serving, PagedAttention, OpenAI-compatible API |
| llama.cpp | CPU/GPU inference, GGUF quantised models |
| Ollama | Local model serving (wraps llama.cpp) |
| TGI (HuggingFace) | Text Generation Inference, production-ready |
| TensorRT-LLM | NVIDIA-optimised inference |

## LLM Benchmarks

| Benchmark | Measures |
|---|---|
| MMLU | Massive Multitask Language Understanding — knowledge across 57 subjects |
| HumanEval | Code generation — Python function completion |
| GSM8K | Grade school math reasoning |
| HellaSwag | Commonsense reasoning — sentence completion |
| MATH | Competition-level mathematics |
| ARC-Challenge | Science question answering |
| TruthfulQA | Truthfulness — avoids hallucination |
| BIG-Bench Hard | 23 hard tasks requiring multi-step reasoning |
| LMSYS Chatbot Arena | Human preference ELO ranking |
| SWE-Bench | Real-world software engineering tasks |

## Context Window & Retrieval

```
Short context (≤8k)  → Fit everything in-context (simple)
Long context (128k+) → Still use RAG for precision and cost
Very long docs       → Hierarchical chunking + RAG → see ai-rag.md

"Lost in the middle" phenomenon: LLMs perform worse on
information placed in the middle of long contexts.
→ Put most important context at the start or end.
```

## References

- [ai-ml-dl-readme.md](ai-ml-dl-readme.md) — Transformer architecture, embeddings
- [ai-prompt-engineering.md](ai-prompt-engineering.md) — Prompting techniques
- [ai-rag.md](ai-rag.md) — RAG pipeline
- [ai-agent-readme.md](ai-agent-readme.md) — LLM-based agents
- [!HuggingFace](../!HuggingFace/) — HuggingFace library notes
- [!LangChain](../!LangChain/) — LangChain framework
- [LMSYS Leaderboard](https://chat.lmsys.org/)
- [Open LLM Leaderboard (HuggingFace)](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard)
