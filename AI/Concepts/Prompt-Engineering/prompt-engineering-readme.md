# Prompt Engineering

> Techniques for writing effective prompts for LLMs.
> See [ai-llm-readme.md](ai-llm-readme.md) for model details and [ai-rag.md](ai-rag.md) for retrieval-augmented prompting.

## Core Concepts

```
Prompt = System Prompt + Context + Few-Shot Examples + User Input

Response quality depends on:
  1. Clarity of task instruction
  2. Relevant context provided
  3. Output format specification
  4. Temperature / sampling settings
```

## Prompting Patterns

### Zero-Shot
No examples — just instruction.
```
Classify the sentiment of this review as positive, negative, or neutral:
"The product arrived on time but the quality was disappointing."
```

### Few-Shot
Provide 2–5 input/output examples before the actual query.
```
Q: What is the capital of France? A: Paris
Q: What is the capital of Japan? A: Tokyo
Q: What is the capital of Brazil? A: [model completes]
```

### Chain-of-Thought (CoT)
Instruct the model to reason step-by-step before answering.
```
Solve this step by step:
A train travels 120 km in 2 hours. How long to travel 300 km?

Step 1: Find speed = 120 / 2 = 60 km/h
Step 2: Time = 300 / 60 = 5 hours
Answer: 5 hours
```

### Zero-Shot CoT
Simply add "Let's think step by step." — often enough to trigger reasoning.
```
Q: If I have 5 apples and give away 2, then buy 4 more, how many do I have?
A: Let's think step by step.
```

### Self-Consistency
Generate multiple CoT reasoning paths, take majority vote on the final answer.
Best for: math, logic, factual QA.

### ReAct (Reasoning + Acting)
Interleaves reasoning and tool calls.
```
Thought: I need to find the current population of Tokyo.
Action: search("Tokyo population 2024")
Observation: Tokyo population is approximately 13.96 million.
Thought: I now have the answer.
Answer: ~14 million
```
Used by: [!LangChain](../!LangChain/) agents, [!LangGraph](../!LangGraph/) graphs.

### RAG Prompting
```
You are a helpful assistant. Use only the context below to answer the question.
If the answer is not in the context, say "I don't know."

Context:
{retrieved_chunks}

Question: {user_question}
```
See [ai-rag.md](ai-rag.md) for the full RAG pipeline.

### Role Prompting
```
You are an expert data scientist with 10 years of experience in NLP.
Explain tokenisation to a junior developer.
```

### Structured Output
Force JSON or structured responses.
```
Extract the following fields from the text and return as JSON:
- name (string)
- date (ISO 8601)
- amount (number)

Text: "Invoice from Acme Corp dated January 5th 2024 for $1,250.00"

Return only valid JSON, no commentary.
```

### Tree of Thought (ToT)
Explore multiple reasoning branches, evaluate, and select the best path.
Best for: complex planning, strategy, puzzles.

### Reflection / Self-Critique
```
[Generate initial answer]
Now review your answer. Is it correct? Are there any errors or omissions?
Provide an improved final answer.
```

---

## System Prompt Best Practices

```
GOOD system prompt structure:
  1. Role / persona definition
  2. Task scope and constraints
  3. Output format requirements
  4. Tone / style
  5. What NOT to do

Example:
  You are a senior software engineer specialising in Python.
  Your job is to review code for bugs, security issues, and performance.
  Always provide:
  - A severity rating (low/medium/high/critical)
  - A specific line reference
  - A suggested fix with code
  Never provide opinions on coding style unless asked.
```

## Sampling Parameters

| Parameter | Description | Typical Range |
|---|---|---|
| Temperature | Controls randomness. 0 = deterministic, 1 = creative | 0–2 |
| Top-p (nucleus) | Sample from top-p probability mass | 0.8–1.0 |
| Top-k | Sample from top-k most likely tokens | 20–100 |
| Max tokens | Maximum response length | Task-dependent |
| Stop sequences | Tokens that end generation early | e.g. "\n", "###" |
| Frequency penalty | Reduces repetition of tokens | 0–2 |
| Presence penalty | Encourages new topics | 0–2 |

**Temperature guide:**
- 0.0 — factual QA, extraction, code
- 0.3–0.7 — balanced (default for most tasks)
- 0.8–1.2 — creative writing, brainstorming
- 1.5+ — highly experimental / random

## Prompt Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Vague instruction | "Write something about AI" | Be specific: task, audience, length, format |
| No output format | Model returns free-form text | Specify: "Return as JSON / bullet list / table" |
| Long ambiguous context | Model focuses on wrong part | Chunk context, put key info first or last |
| Asking multiple questions at once | Model answers partially | Ask one thing at a time or number questions |
| No constraints | Model over-generates | Set max length, scope, constraints explicitly |

## Token Efficiency Tips

- Shorter prompts = lower cost + faster responses
- Use abbreviations in system prompts (e.g. "ROI" not "Return on Investment")
- Remove filler phrases ("Please", "Could you possibly")
- Reuse system prompts across turns — don't repeat instructions per message
- Use `max_tokens` to cap response length

## References

- [ai-llm-readme.md](ai-llm-readme.md) — LLM model families and parameters
- [ai-rag.md](ai-rag.md) — RAG pipeline with prompting
- [ai-agent-readme.md](ai-agent-readme.md) — ReAct and agentic prompting
- [!LangChain](../!LangChain/) — Prompt templates in LangChain
- [!LangSmith](../!LangSmith/) — Prompt testing and evaluation
- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
