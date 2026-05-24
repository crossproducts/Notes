# Homelab — Multi-Project K8s Cluster

A single k3d cluster hosting multiple projects in isolated namespaces, managed by ArgoCD.

## Architecture

```
k3d cluster "homelab"
│
├── argocd namespace        ← ArgoCD (bootstrap)
│   └── root-app            ← watches homelab/apps/
│
├── monitoring namespace     ← Observability
│   ├── Prometheus          ← metrics collection + alerting
│   ├── Grafana             ← dashboards (metrics, traces, logs)
│   └── Alertmanager        ← alert routing
│
├── elasticsearch namespace ← Log storage
│   └── Elasticsearch       ← OTel log indexing
│
├── kibana namespace        ← Log UI
│   └── Kibana              ← Elasticsearch query interface
│
├── tempo namespace         ← Trace storage
│   └── Tempo               ← distributed tracing backend
│
├── otel-system namespace   ← Telemetry pipeline
│   └── OTel Collector      ← auto-discovery, logs + traces + metrics
│
├── platform namespace      ← Shared infra
│   └── Ollama              ← local LLM for all projects
│
├── openwebui namespace     ← Chat UI
│   └── Open WebUI          ← web chat interface for Ollama
│
├── agentgateway namespace  ← AI proxy
│   └── AgentGateway        ← LLM/MCP/A2A routing + admin UI
│
├── unsloth namespace       ← Fine-tuning
│   └── Unsloth Studio      ← LLM training UI + Jupyter
│
├── openclaw namespace      ← AI assistant
│   └── OpenClaw            ← personal AI agent gateway
│
└── hermes namespace        ← Hermes Agent project
    ├── Gateway (port 9000) ← API + agent brain
    └── Dashboard (9119)    ← Web UI
```

**Flat app-of-apps**: Root app discovers `apps/` directory. Apps grouped into 3 files:
- `observability.yaml` — kube-prometheus-stack, Elasticsearch, Tempo, OTel Collector, Kibana, Grafana datasources (waves 1-2)
- `ai-platform.yaml` — Ollama, Open WebUI, AgentGateway, Unsloth Studio (waves 0-4)
- `agents.yaml` — Hermes gateway + dashboard, OpenClaw (waves 5-7)

**Disable a project**: Remove or rename its app YAMLs in `apps/` (e.g. `hermes-*.yaml` → `hermes-*.yaml.disable`). ArgoCD prunes the resources.

## Projects

| Project | Namespace | Description |
|---------|-----------|-------------|
| Prometheus + Grafana | monitoring | Metrics, dashboards, alerting (kube-prometheus-stack) |
| Elasticsearch | elasticsearch | Log storage for OTel pipeline |
| Kibana | kibana | Log exploration UI |
| Tempo | tempo | Distributed trace storage |
| OTel Collector | otel-system | Auto-discovery DaemonSet — logs, traces, metrics |
| Ollama | platform | Shared LLM backend (qwen3:0.6b, qwen2.5:3b) |
| Open WebUI | openwebui | Chat UI for Ollama models |
| AgentGateway | agentgateway | LLM/MCP/A2A proxy with admin UI |
| Unsloth Studio | unsloth | LLM fine-tuning UI + Jupyter notebooks |
| Hermes Agent | hermes | Autonomous AI agent by Nous Research |
| OpenClaw | openclaw | Personal AI assistant gateway |

## Ingress URLs

| Service | URL |
|---------|-----|
| ArgoCD | http://argocd.localhost |
| Grafana | http://grafana.localhost |
| Prometheus | http://prometheus.localhost |
| Alertmanager | http://alertmanager.localhost |
| Kibana | http://kibana.localhost |
| Ollama API | http://ollama.localhost |
| Open WebUI | http://chat.localhost |
| AgentGateway Admin | http://gateway.localhost |
| Unsloth Studio | http://unsloth.localhost |
| Unsloth Jupyter | http://jupyter.localhost |
| Hermes Gateway | http://hermes.localhost |
| Hermes Dashboard | http://hermes-ui.localhost |
| OpenClaw | http://openclaw.localhost |

## Setup

### Prerequisites

- Docker + k3d
- kubectl

### 1. Create cluster

```bash
k3d cluster create homelab -p "80:80@loadbalancer" -p "443:443@loadbalancer"
```

### 2. Bootstrap ArgoCD

```bash
kubectl apply -k bootstrap/argocd/
kubectl -n argocd wait --for=condition=available deploy/argocd-server --timeout=120s
```

Get the ArgoCD admin password:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```

### 3. Configure secrets

```bash
cp .env.example .env
# Fill in your API keys

kubectl create namespace hermes
kubectl -n hermes create secret generic hermes-api-keys --from-env-file=.env
```

### 4. Deploy everything

```bash
kubectl apply -f bootstrap/root/root-app.yaml
```

ArgoCD syncs automatically: observability (wave 1-2) -> ollama + openwebui (wave 0-2) -> agentgateway + unsloth (wave 3-4) -> hermes + openclaw (wave 5-7).

### 5. Access

- ArgoCD: http://argocd.localhost
- Grafana: http://grafana.localhost
- Prometheus: http://prometheus.localhost
- Kibana: http://kibana.localhost
- Ollama: http://ollama.localhost
- Open WebUI: http://chat.localhost
- AgentGateway: http://gateway.localhost
- Unsloth Studio: http://unsloth.localhost
- Jupyter: http://jupyter.localhost
- Hermes: http://hermes.localhost
- Hermes UI: http://hermes-ui.localhost
- OpenClaw: http://openclaw.localhost

## Adding a New Project

```bash
# 1. Create manifest directory
mkdir -p projects/newproject

# 2. Add K8s manifests in projects/newproject/
# 3. Add an ArgoCD Application YAML in apps/ pointing to projects/newproject/
# 4. Commit + push — ArgoCD auto-syncs
```

## Teardown

```bash
k3d cluster delete homelab
```

## To add Hermes as an additional connection, do it through the UI:

1. Go to http://chat.localhost
2. Click Admin Panel (gear icon, top right) → Settings → Connections
3. Under OpenAI API, click + to add a new connection:
    - URL: http://hermes-gateway.hermes.svc.cluster.local:9000/v1
    - API Key: pFKVYlGeweBWBee5GqJuDaVSOVlaNpWT
4. Click the checkmark to verify/save