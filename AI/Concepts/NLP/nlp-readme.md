# NLP — Natural Language Processing

> Reference for NLP concepts, tokenisation, tasks, models, and benchmarks.
> See [ai-llm-readme.md](ai-llm-readme.md) for LLMs and [ai-ml-dl-readme.md](ai-ml-dl-readme.md) for Transformer architecture.
> See [!HuggingFace](../!HuggingFace/) for the HuggingFace library.

## NLP Task Taxonomy

```
Text Input
    │
    ├── Classification
    │   ├── Sentiment Analysis         (positive/negative/neutral)
    │   ├── Topic Classification       (news category, intent detection)
    │   ├── Spam Detection
    │   └── Language Identification
    │
    ├── Sequence Labelling
    │   ├── Named Entity Recognition (NER)   (person, org, location)
    │   ├── Part-of-Speech (POS) Tagging
    │   └── Chunking / Phrase Detection
    │
    ├── Structured Prediction
    │   ├── Relation Extraction
    │   ├── Coreference Resolution
    │   └── Dependency Parsing
    │
    ├── Generation
    │   ├── Machine Translation        (EN → FR)
    │   ├── Summarisation              (extractive / abstractive)
    │   ├── Text Generation            (GPT-style)
    │   ├── Question Answering (QA)    (extractive / generative)
    │   └── Dialogue / Chatbots
    │
    └── Embedding / Representation
        ├── Semantic Similarity
        ├── Document Retrieval / RAG   → see ai-rag.md
        └── Clustering of Documents
```

## Tokenisation

| Algorithm | Used By | Description |
|---|---|---|
| Whitespace / Word | Classic NLP | Split on spaces |
| BPE (Byte-Pair Encoding) | GPT, LLaMA, RoBERTa | Merges frequent character pairs iteratively |
| WordPiece | BERT | Similar to BPE, uses likelihood criterion |
| SentencePiece | T5, ALBERT, multilingual models | Language-agnostic, treats text as raw Unicode |
| Unigram | XLNet, some multilingual models | Probabilistic subword segmentation |

```python
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
tokens = tokenizer("Hello world!")
# {'input_ids': [101, 7592, 2088, 999, 102], ...}
```

## Classic NLP (Pre-Transformer)

| Technique | Use |
|---|---|
| Bag of Words (BoW) | Text as word count vector |
| TF-IDF | Term frequency × inverse document frequency |
| n-grams | Contiguous sequences of n words |
| Word2Vec | Static word embeddings (skip-gram / CBOW) |
| GloVe | Global co-occurrence word embeddings |
| FastText | Subword embeddings, handles OOV |
| Naive Bayes | Fast text classification baseline |
| Logistic Regression + TF-IDF | Strong baseline for classification |

## Transformer-Based Models for NLP

| Model | Task | Notes |
|---|---|---|
| BERT | Classification, NER, QA | Encoder-only, bidirectional |
| RoBERTa | Classification, NER | BERT with better training |
| DistilBERT | Lightweight classification | 60% size of BERT, 97% performance |
| ALBERT | Classification | Parameter sharing, smaller |
| DeBERTa | Classification, NER | State-of-the-art encoder |
| T5 | Summarisation, translation, QA | Encoder-decoder, "text-to-text" framing |
| BART | Summarisation, translation | Encoder-decoder, denoising pre-training |
| GPT-4 / Claude / Gemini | Generation, QA, chat | Decoder-only, see [ai-llm-readme.md](ai-llm-readme.md) |
| mBERT / XLM-R | Multilingual tasks | Trained on 100+ languages |

## NLP Evaluation Metrics

| Task | Metrics |
|---|---|
| Classification | Accuracy, F1 (macro/micro/weighted), ROC-AUC |
| NER | Entity-level F1 (precision/recall at entity span level) |
| Machine Translation | BLEU, chrF, COMET |
| Summarisation | ROUGE-1/2/L, BERTScore |
| QA (extractive) | Exact Match (EM), F1 |
| QA (generative) | ROUGE, BERTScore, human eval |
| Language Modelling | Perplexity (lower = better) |
| Semantic Similarity | Pearson/Spearman correlation with human labels |

## NLP Benchmarks

| Benchmark | Covers |
|---|---|
| GLUE | 9 classification / NLI tasks |
| SuperGLUE | Harder version of GLUE |
| SQuAD 1.1 / 2.0 | Reading comprehension QA |
| CoNLL-2003 | NER (English, German) |
| WMT | Machine translation |
| CNN/DailyMail | Summarisation |
| MMLU | Multi-domain knowledge (see [ai-llm-readme.md](ai-llm-readme.md)) |

## Key Python Libraries

| Library | Purpose |
|---|---|
| transformers (HuggingFace) | Pre-trained models, tokenisers, pipelines |
| datasets (HuggingFace) | 10,000+ NLP datasets |
| spaCy | Fast NLP pipeline: tokenisation, NER, POS |
| NLTK | Classic NLP tools |
| sentence-transformers | Sentence embeddings for similarity/retrieval |
| Gensim | Word2Vec, topic modelling (LDA) |

## References

- [ai-llm-readme.md](ai-llm-readme.md) — LLMs for NLP
- [ai-ml-dl-readme.md](ai-ml-dl-readme.md) — Transformer architecture
- [ai-rag.md](ai-rag.md) — Retrieval with embeddings
- [!HuggingFace](../!HuggingFace/) — HuggingFace library
- [HuggingFace NLP Course](https://huggingface.co/learn/nlp-course/)
- [spaCy Documentation](https://spacy.io/)
