# HolmesGPT Lab — Architecture

## This lab (as deployed)

```
              ┌────────────── you ──────────────┐
              ▼                                 ▼
    Open WebUI :3000                        ask.sh / curl
    (persistent chats,                          │
     Holmes pipe function)                      │
              │                                 │
              │  [pipe: pipe/holmes_pipe.py]     │
              ▼                                 ▼
                       holmes :5050 (/api/chat, SSE)
                                 │
               ┌─────────────────┼──────────────┐
               ▼                 ▼              ▼
         LLM (LiteLLM:     bash toolset    other toolsets
         Anthropic/Ollama) + docker sock   (internet, …)
                            (allow/deny)
                                 │
                       payment-api, report-worker
                       (the patients)
```

### Why the former chain was long — and how the pipe replaced it

The original stack ran four extra containers between the user and Holmes:
`holmes-agui` (AG-UI server) → `holmes-bridge` (OpenAI→AG-UI protocol
translator) → `bridge-shim` (nginx serving the `/v1/models` endpoint the
bridge lacked) → `open-webui`. Each hop existed because Open WebUI only spoke
the OpenAI protocol and the AG-UI path was the only available multi-turn
interface at the time.

An **Open WebUI pipe function** (`pipe/holmes_pipe.py`) replaces the entire
chain. The pipe runs inside Open WebUI's Python process, calls
`holmes:5050/api/chat` directly over SSE, handles multi-turn via Holmes's
native `conversation_history` round-trip, and surfaces tool calls as status
events. The three extra services (`holmes-agui`, `holmes-bridge`,
`bridge-shim`) and the nginx config file (`bridge-shim.conf`) have been
removed.

**Important:** the pipe is stored in Open WebUI's SQLite database
(`openwebui-data` volume, `webui.db`). After wiping that volume, re-run
`./install-pipe.sh` to reinstall it from `pipe/holmes_pipe.py`.

## HolmesGPT in general

A **stateless investigation engine**:

```
input (question | alert webhook)
   → agentic loop: plan tasks → call toolsets (parallel) → read evidence → iterate
   → root-cause analysis with cited evidence
```

- **Toolsets** are declarative YAML: read-only commands + prerequisites
  (e.g. `docker/core` requires the docker CLI). Custom toolsets are a few
  lines of YAML.
- **LLM is pluggable** via LiteLLM — Anthropic, OpenAI, Azure, Bedrock,
  Gemini, Ollama; one-line swap.
- **Deployment modes**: pip/brew CLI, HTTP server via docker compose (this
  lab), Helm chart in-cluster.
- The server holds no conversation state — history travels in each request;
  persistence is the frontend's job (here: Open WebUI's SQLite volume).

## Why use it: alert → auto-investigation

The value proposition over "chat with a model that has tools":

1. AlertManager / PagerDuty / OpsGenie / Slack webhook fires
2. Holmes investigates **immediately, unattended** — pod events, logs,
   metrics, recent deploys
3. The RCA (with evidence) is attached to the alert/ticket before a human
   looks at it
4. Humans start at "here's the root cause, verify and fix" instead of at
   `kubectl get pods`

Investigation stops being interactive labor and becomes infrastructure.

### vs. model + MCP directly

| Concern | DIY model + MCP | HolmesGPT |
|---|---|---|
| Runs where | your laptop, interactive | in-cluster server, API |
| Trigger | you ask | alerts fire investigations automatically |
| Data sources | whatever MCP servers you wire | ~30 curated toolsets, read-only defaults |
| Safety | whatever the MCP server allows | allow/deny lists + approval workflow |
| Methodology | generic assistant prompt | tuned investigation prompt (task planning, five-whys, cited evidence) |
| Model | one vendor | LiteLLM, one-line swap |
| Team use | per-person setup | one deployment, config-as-code, auditable |

Holmes also *consumes* MCP servers as toolsets — it's an opinionated SRE
harness on top of the same primitives, not a competitor to them.

Honest counterpoint: for one person poking at a local Docker host, an agent
with shell access does the same job with less plumbing. Holmes earns its
complexity when investigations run headless, on alerts, against production
observability stacks, with guardrails a team can review.

## What else you'd need (to make this real SRE)

Roughly in order:

1. **An alert source** — Prometheus + AlertManager; webhook →
   `/api/investigate`. (Pairs with the pending `Observability` lab.)
2. **Observability toolsets** — enable `prometheus`, Loki/logs, Grafana so
   investigations use metrics and logs, not just `docker`/`kubectl`.
3. **A destination** — Slack bot or ticket comments; an RCA nobody sees is
   worthless.
4. **Runbooks** — markdown files with tribal knowledge ("if payment-api
   fails, check the gateway config first").
5. **A real cluster** — k3d/minikube to unlock the K8s toolsets, Holmes's
   first-class citizens.
6. **Guardrails hygiene** — read-only RBAC service account, secrets via env
   not config, cost caps (each investigation is ~10–50k tokens).
7. **Eval habit** — periodically break things on purpose (like this lab) and
   check the model still finds the truth.

## Feature list

- **Agentic investigation loop** — plans tasks, runs tools in parallel,
  five-whys, cites evidence
- **~30 built-in toolsets** — Kubernetes, Prometheus, Loki, Grafana, Tempo,
  ArgoCD, Datadog, New Relic, GitHub, AWS, bash, internet fetch, databases…
- **MCP client support** — plug arbitrary MCP servers in as toolsets
- **Custom toolsets** — your own read-only CLI tools in a few lines of YAML
  (like this lab's docker allowlist)
- **Runbooks** — encode org-specific diagnostic procedures
- **Model-agnostic** — LiteLLM: Anthropic, OpenAI, Azure, Bedrock, Gemini,
  Ollama
- **Safety** — read-only by default, allow/deny command lists, human approval
  workflow for unknown commands
- **Interfaces** — CLI (`holmes ask`, interactive TUI), HTTP API (`/api/chat`,
  `/api/investigate`, SSE streaming), K9s plugin, Slack, experimental AG-UI
- **Alert integrations** — AlertManager, PagerDuty, OpsGenie, Jira/GitHub
  issue enrichment
- **Deployment modes** — pip/brew CLI, docker compose, Helm in-cluster
- **Structured output** — JSON responses for piping into automation
- **CNCF sandbox** — open source (MIT), vendor-neutral governance

## Next iteration for this lab

Add Prometheus + AlertManager containers, alert on `payment-api` restarts,
webhook into Holmes, and watch the RCA appear with zero prompting — the
"reason for using" demonstrated end-to-end.
