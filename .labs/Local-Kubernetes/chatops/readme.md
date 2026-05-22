# ChatOps Bot — Mattermost + MCP Kubernetes Client

A self-hosted ChatOps bot that connects Mattermost to your Kubernetes cluster via the Model Context Protocol (MCP). Ask questions in natural language, get real-time cluster insights.

## How It Works

```
User: @k8s-bot are all pods healthy?
                │
                ▼
┌─ Bot Service ──────────────────────────────┐
│  Mattermost WebSocket ← listens @mentions  │
│       │                                    │
│       ▼                                    │
│  Claude API (message + K8s tools)          │
│       │                                    │
│       ▼                                    │
│  MCP Client → kubernetes-mcp-server        │
│       │         (stdio child process)      │
│       ▼                                    │
│  K8s API (kubeconfig → k3d cluster)        │
└────────────────────────────────────────────┘
                │
                ▼
Bot: ✅ All 42 pods Running across 14 namespaces...
```

1. User @mentions the bot in Mattermost
2. Bot sends the question + K8s tools to Claude API
3. Claude decides which tools to call (list pods, get events, etc.)
4. Bot executes tools via MCP → kubernetes-mcp-server → K8s API
5. Claude summarizes results and bot posts the response

## Stack

| Component | Purpose |
|-----------|---------|
| Mattermost (Docker) | Chat platform with bot support |
| PostgreSQL (Docker) | Mattermost database |
| Bot Service (Node.js) | MCP client + Claude API + Mattermost WS |
| kubernetes-mcp-server | MCP server providing 30+ K8s tools |
| Claude API | Natural language → tool selection → summarization |

## Setup

### Prerequisites

- Docker + Docker Compose
- A running k3d cluster (e.g., the mlops lab)
- Anthropic API key

### 1. Start Mattermost

```bash
cd .labs/Local-Kubernetes/chatops
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

docker compose up -d postgres mattermost
```

### 2. Bootstrap bot account

```bash
bash setup.sh
```

This creates:
- Admin user (`admin` / `Admin1234!`)
- `chatops` team
- `#general` and `#k8s-alerts` channels
- `@k8s-bot` bot account with access token

Copy the `BOT_TOKEN` from the output into your `.env` file.

### 3. Start the bot

```bash
docker compose up -d bot
```

### 4. Use it

Open http://localhost:8065, log in, join the `chatops` team, and try:

```
@k8s-bot hello
@k8s-bot are all pods healthy?
@k8s-bot what pods are in CrashLoopBackOff?
@k8s-bot show me recent warning events
@k8s-bot how much memory is each namespace using?
@k8s-bot health check
```

## Health Checks

The bot automatically posts health summaries to `#k8s-alerts` every 5 minutes (configurable via `HEALTH_CHECK_INTERVAL_MS`). Each report includes:

- Node status and resource usage
- Pod health across all namespaces
- Recent warning/error events
- Pods in problematic states

Set `HEALTH_CHECK_INTERVAL_MS=0` to disable.

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `ANTHROPIC_API_KEY` | (required) | Claude API key |
| `BOT_TOKEN` | (required) | Mattermost bot access token |
| `MATTERMOST_URL` | `http://mattermost:8065` | Mattermost server URL |
| `BOT_USERNAME` | `k8s-bot` | Bot's Mattermost username |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model for responses |
| `KUBECONFIG` | `/home/node/.kube/config` | Path to kubeconfig in container |
| `HEALTH_CHECK_INTERVAL_MS` | `300000` (5 min) | Health check frequency (0 to disable) |
| `HEALTH_CHECK_CHANNEL` | `k8s-alerts` | Channel for health check posts |

## Architecture Details

### MCP Client (Model Context Protocol)

The bot doesn't shell out to `kubectl`. Instead, it uses the **MCP protocol** to communicate with a `kubernetes-mcp-server` process:

- The MCP server is spawned as a **child process** using stdio transport
- The bot discovers available tools via `client.listTools()`
- Tools include: `pods_list`, `pods_log`, `events_list`, `nodes_list`, `resources_get`, `namespaces_list`, etc.
- Tool calls are executed via `client.callTool(name, args)`
- The MCP server reads kubeconfig and talks to the K8s API directly

### Claude Tool-Use Loop

When a user asks a question:

1. Bot sends the message + all MCP tool definitions to Claude
2. Claude picks relevant tools (e.g., "list pods" + "get events")
3. Bot executes each tool via MCP and returns results
4. Claude may call more tools based on results (up to 10 iterations)
5. Claude generates a final summarized response

### Networking

The bot container joins two Docker networks:
- `chatops` — communicates with Mattermost
- `k3d-mlops` (external) — reaches the k3d K8s API server

## Teardown

```bash
docker compose down -v
```

## Troubleshooting

**Bot not responding to @mentions:**
- Check bot logs: `docker compose logs bot`
- Verify `BOT_TOKEN` is set in `.env`
- Ensure the bot is added to the channel (setup.sh handles this)

**MCP connection failed:**
- Check that kubeconfig is mounted: `docker compose exec bot ls /home/node/.kube/`
- Verify the k3d cluster is running: `k3d cluster list`
- Check the k3d network exists: `docker network ls | grep k3d`

**Claude API errors:**
- Verify `ANTHROPIC_API_KEY` in `.env`
- Check rate limits in bot logs
