# Lab: HolmesGPT (Docker-only)

> **Status:** 🟢 Active

AI SRE agent (CNCF sandbox) investigating **plain Docker containers** — no Kubernetes.
Holmes runs as an HTTP server with the docker socket mounted so it can run read-only
`docker` commands itself while diagnosing. Open WebUI sits on top for persistent
chats, connected through a native pipe function (no bridge containers).

## Goal

Prove that HolmesGPT can root-cause container failures autonomously: you ask a
plain-English question, it decides which docker commands to run, reads the
evidence, and explains the failure. Two broken workloads are included:

| Container | Failure mode |
|---|---|
| `payment-api` | Crashloop — exits 1 on a missing `PAYMENT_GATEWAY_URL` env var |
| `report-worker` | OOM-killed — allocates 64 MB against a 16 MB limit (exit 137) |

## Architecture

> Full picture — diagram, why-Holmes rationale, feature list, roadmap:
> [docs/architecture.md](docs/architecture.md)

```
you ──► Open WebUI :3000 ──[pipe fn]──► holmes :5050 ──► toolsets + LLM
        (persistent chats)                                    │
you ──► ask.sh / curl ────────────────► holmes :5050    payment-api,
                                                        report-worker
```

| Service | Image | Port | Notes |
|---|---|---|---|
| `holmes` | local build (Dockerfile) + docker CLI | 5050 | HTTP API (`/api/chat`), SSE streaming |
| `open-webui` | `ghcr.io/open-webui/open-webui:main` | **3000** | Persistent chat UI; Holmes pipe function (`pipe/holmes_pipe.py`) installed via `./install-pipe.sh` |
| `payment-api`, `report-worker` | busybox / python-alpine | — | Deliberately broken demo workloads |

## Choosing the LLM

Switchable in `docker-compose.yaml` (holmes env) **and** `config/config.yaml`
(`model:` — this one wins, change both):

| Mode | Config | Notes |
|---|---|---|
| **Anthropic** (current) | `MODEL=anthropic/claude-sonnet-4-5` + `ANTHROPIC_API_KEY` in `.env` | Best investigations; ~10–50k tokens each |
| **Fully local** | `MODEL=ollama_chat/qwen3:8b` + `OLLAMA_API_BASE=http://host.docker.internal:11434` | Free, no key; needs `ollama pull qwen3:8b`; prefix prompts with `/no_think` and be imperative |

## Prerequisites

- Docker Desktop (compose v2)
- `jq` (for `ask.sh`)
- Anthropic API key in `.env` — **or** Ollama on the host with `qwen3:8b` pulled

## Steps

```bash
docker compose up -d --build
curl http://localhost:5050/healthz     # {"status":"healthy"}
./install-pipe.sh                      # install Holmes pipe into Open WebUI (idempotent)
```

Then open the **chat UI at http://localhost:3000** (model: `Holmes (SRE)` — tool
calls stream as live status updates), or use the CLI helper:

```bash
./ask.sh "This is a plain Docker host, not Kubernetes. Why does payment-api keep restarting? Investigate and give the root cause and a fix."
./ask.sh "report-worker exits with code 137 - run docker inspect and explain why"
```

## Verify

- `/healthz` returns healthy; chat UI loads at :3000 and lists `Holmes (SRE)`
- Answer for `payment-api` names the missing env var (it must have read the
  logs itself — that's the point)
- Answer for `report-worker` cites `OOMKilled: true` / the 16 MB limit
- Both confirmed working with `claude-sonnet-4-5` and (with more hand-holding)
  `qwen3:8b`

## Persistent chat (Open WebUI)

- Chats live in `webui.db` (SQLite) in the `openwebui-data` volume — they
  survive `compose down`/`up` and rebuilds.
- **Disable per-chat:** toggle **Temporary Chat** in the sidebar before starting.
- **Purge / age-off** (live, no restart):

  ```bash
  ./purge.sh --all                  # delete every stored chat
  ./purge.sh --older-than 30        # delete chats older than 30 days
  ```

- **Full reset:** `docker compose down && docker volume rm holmesgpt_openwebui-data`
  — then re-run `./install-pipe.sh` after the next `up` (the pipe lives in that DB).

## Gotchas learned building this

- **Server mode excludes the `docker/core` toolset** (tagged `cli`; server only
  loads `core`/`cluster` tags). Workaround: grant the `bash` toolset read-only
  docker commands via `allow:` in `config/config.yaml`, destructive commands in `deny:`.
- **The image's default entrypoint is the CLI**, not the server — compose
  overrides it with `python server.py`.
- **Holmes's system prompt assumes Kubernetes.** It will hunt for
  kubectl/kubeconfig first — start prompts with "This is a plain Docker host,
  not Kubernetes."
- **qwen3 thinking mode can swallow the answer** (empty `analysis`). Prefix
  prompts with `/no_think`. Small models also stop early — be imperative.
- **Anthropic auth:** only real API keys (`sk-ant-api03-...`) work. The Claude
  Code OAuth token (`sk-ant-oat01-...`) does NOT, and LiteLLM misreports it as
  a rate-limit error. Non-ASCII prompt chars can 400 through git-bash.
- **Open WebUI snapshots env config into its DB on first boot** and ignores
  later env changes; `ENABLE_PERSISTENT_CONFIG=false` makes env vars always win.
- **`WEBUI_AUTH=false` does NOT disable REST API auth.** A default admin
  (`admin@localhost`/`admin`) exists; `install-pipe.sh` signs in via
  `/api/v1/auths/signin` for a session JWT — nothing stored to disk.
- **The pipe function lives in `webui.db`, not on disk.** Source of truth is
  `pipe/holmes_pipe.py`; re-run `./install-pipe.sh` after wiping the volume.
- (Historical) An earlier iteration chained Open WebUI → nginx shim → ag-ui
  bridge → a second Holmes instance; the pipe function replaced all three
  containers. See [docs/architecture.md](docs/architecture.md).

## Things to try next

- Break something yourself (`docker stop`, bad image tag, port conflict) and
  ask Holmes cold: "something broke in the last 5 minutes, find it"
- Enable more toolsets in `config/config.yaml` (prometheus, github, internet)
- **Alert → auto-investigation:** add Prometheus + AlertManager, alert on
  `payment-api` restarts, webhook into Holmes — RCA with zero prompting
- Graduate to Kubernetes: mount a kubeconfig, enable `kubernetes/core`

## Teardown

```bash
docker compose down --rmi local
# also remove persistent chat data:
docker volume rm holmesgpt_openwebui-data
```
