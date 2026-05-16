# AI Agents

> LLM-powered agents that observe, reason, and act in loops.
> See [ai-llm-readme.md](ai-llm-readme.md) for LLM selection, [ai-rag.md](ai-rag.md) for retrieval, [ai-prompt-engineering.md](ai-prompt-engineering.md) for ReAct prompting.
> Framework notes: [!LangChain](../!LangChain/) · [!LangGraph](../!LangGraph/) · [!LangSmith](../!LangSmith/) · [!MCP](../!MCP/)

## Agent Loop

```
                ┌─────────────────────────────────┐
                │           AGENT LOOP            │
                │                                 │
  User Input ──►│  1. OBSERVE  (inputs + memory)  │
                │         │                       │
                │         ▼                       │
                │  2. THINK    (LLM reasoning)    │
                │         │                       │
                │         ▼                       │
                │  3. ACT      (tool call)        │◄──► External Tools
                │         │                       │    (search, code,
                │         ▼                       │     APIs, DB, etc.)
                │  4. UPDATE   (memory + state)   │
                │         │                       │
                │         ▼                       │
                │    Done? ──No──► loop back      │
                │      │                          │
                │     Yes                         │
                └──────┼──────────────────────────┘
                       ▼
                 Final Response
```

## Memory Types

| Type | Description | Scope | Example |
|---|---|---|---|
| In-context (working) | Everything in the current context window | Current session | Chat history, system prompt |
| External / Vector | Embeddings stored in a vector DB | Persistent | Long-term facts, docs → [!Pinecone](../!Pinecone/) |
| Episodic | Stored past interactions / summaries | Persistent | "Last time user asked about X…" |
| Procedural | Rules, instructions, how-to knowledge | Persistent | System prompt, tool descriptions |
| Key-Value Store | Structured facts (Redis, dict) | Persistent | User profile, session state |

## Tool Types

| Tool Category | Examples |
|---|---|
| Search | Tavily, Bing, Google, Wikipedia |
| Code execution | Python REPL, code sandbox |
| Database | SQL queries, vector search |
| APIs | REST APIs, weather, finance |
| File I/O | Read/write files, parse PDFs |
| Browser | Web scraping, Playwright |
| Email / Calendar | Send emails, schedule events |
| RAG retrieval | Chunked doc retrieval → [ai-rag.md](ai-rag.md) |

## Agent Architectures

### ReAct (Reasoning + Acting)
```
Thought → Action → Observation → Thought → ... → Final Answer
```
Simple, widely used. See [ai-prompt-engineering.md](ai-prompt-engineering.md).

### Plan-and-Execute
```
Planner LLM → Step-by-step plan
Executor   → Runs each step with tools
```
Better for multi-step tasks requiring upfront planning.

### Reflection
Agent critiques its own output and iterates until satisfactory.
```
Generate → Critique → Revise → (repeat) → Output
```

### LATS (Language Agent Tree Search)
Monte Carlo Tree Search over reasoning paths. Best quality, most expensive.

## Multi-Agent Patterns

| Pattern | Description | Use Case |
|---|---|---|
| Orchestrator / Worker | Central agent delegates to specialised sub-agents | Complex pipelines |
| Debate | Multiple agents argue, moderator decides | Fact-checking, reasoning |
| Supervisor | Supervisor monitors and re-routes worker agents | Quality control |
| Parallel | Multiple agents run concurrently, results merged | Research, multi-source tasks |

## Frameworks

| Framework | Notes | Repo Link |
|---|---|---|
| LangChain | Tool calling, chains, agents | [!LangChain](../!LangChain/) |
| LangGraph | Stateful agent graphs (recommended for production) | [!LangGraph](../!LangGraph/) |
| LangSmith | Tracing, evaluation, debugging agents | [!LangSmith](../!LangSmith/) |
| AutoGen (Microsoft) | Multi-agent conversation framework | — |
| CrewAI | Role-based multi-agent crews | — |
| MCP (Model Context Protocol) | Standardised tool/context protocol (Anthropic) | [!MCP](../!MCP/) |

## Agent Evaluation

| Metric | Description |
|---|---|
| Task success rate | % of tasks completed correctly end-to-end |
| Steps to completion | Average number of tool calls / LLM turns |
| Tool call accuracy | % of tool calls with correct arguments |
| Hallucination rate | % of responses with unsupported claims |
| Latency / cost | Time and tokens per completed task |

## Common Failure Modes

| Failure | Cause | Fix |
|---|---|---|
| Infinite loops | Agent never decides "done" | Max iterations limit, explicit stop condition |
| Tool misuse | Wrong tool or wrong arguments | Better tool descriptions, few-shot examples |
| Context overflow | Too much history in context | Summarise history, use external memory |
| Hallucinated tool calls | LLM invents tool names | Strict tool schema validation |
| Poor planning | Greedy short-horizon thinking | Plan-and-execute pattern, reflection |

## References

- [ai-llm-readme.md](ai-llm-readme.md) — LLM selection
- [ai-rag.md](ai-rag.md) — RAG retrieval in agents
- [ai-prompt-engineering.md](ai-prompt-engineering.md) — ReAct prompting
- [!LangChain](../!LangChain/) — Agent implementation
- [!LangGraph](../!LangGraph/) — Stateful agent graphs
- [!LangSmith](../!LangSmith/) — Agent tracing and evaluation
- [!MCP](../!MCP/) — Model Context Protocol
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
