# TL;DR

## Cluster Management
```bash
# Create cluster
k3d cluster create dev --api-port 6550 -p "80:80@loadbalancer" -p "443:443@loadbalancer"

# View clusters / contexts
kubectl config get-clusters
kubectl config get-contexts
kubectl config current-context

# Switch context
kubectl config use-context <CONTEXT_NAME>

# Stop cluster
k3d cluster stop dev

# Start (resume) cluster
k3d cluster start dev
```

## Bootstrap
```bash
kubectl apply -k bootstrap/argocd
kubectl apply -k bootstrap/root
```

<details>
<summary>Bootstrap Alt Script</summary>

```bash
kubectl apply -k bootstrap/argocd --server-side --force-conflicts
kubectl wait --for=condition=Established --timeout=60s `  
  crd/applications.argoproj.io `
  crd/applicationsets.argoproj.io `
  crd/appprojects.argoproj.io
kubectl -n argocd rollout status deploy/argocd-server --timeout=120s
kubectl apply -k bootstrap/root --server-side --force-conflicts
```
</details>


## ArgoCD
- http://argocd.localhost
    - Username: `admin`
    - Password:
        ```powershell
        kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | % { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
        ```

## Observability
- Alertmanager  
  http://alertmanager.localhost

- Prometheus  
  http://prometheus.localhost

- Grafana  
  http://grafana.localhost  
  - Username: `admin`
  - Password:
    ```powershell
    kubectl -n monitoring get secret kps-grafana -o jsonpath="{.data.admin-password}" | % { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
    ```

## OpenClaw
Skip (locally)
```bash
# 1. list pending requests (confirm the ID, since pairing requests expire after 5 min)
kubectl exec -n openclaw deploy/openclaw -- openclaw devices list

# 2. approve by requestId
kubectl exec -n openclaw deploy/openclaw -- openclaw devices approve <Request>

# http://openclaw.localhost/chat?session=main
# Token: 5e7a9c3b2f8d1e4a6c8b0d2f5e9a7c3b1f8d4e6a2c9b0d8f5e1a3c7b9d2f6e0a
```

## Ollama
```bash
kubectl exec -n ollama deploy/ollama -- ollama list
```

## MCP
### K8s MCP
Runs in-cluster as the `kubernetes-mcp` ArgoCD app — read-only ServiceAccount on a `kubernetes-mcp-server` pod listening on `:8080` (Streamable HTTP). A Traefik ingress at `http://k8s-mcp.localhost/mcp` exists, but `.localhost` only auto-resolves in browsers — Node-based HTTP clients like Claude Code can't reach it. Use `kubectl port-forward` instead.

Register Claude Code against the in-cluster server:
```bash
# 1. In a dedicated terminal — leave it running:
kubectl port-forward -n kubernetes-mcp svc/kubernetes-mcp-server 8080:8080

# 2. In another terminal — register the MCP server:
claude mcp remove kubernetes -s user
claude mcp add --transport http kubernetes http://localhost:8080/mcp -s user

# 3. VS Code: Ctrl+Shift+P → "Developer: Reload Window"
# The Claude panel restarts and the new MCP tools attach.

# 4. Verify
claude mcp list
```

The port-forward must stay running. If it stops (terminal closed, pod replaced, cluster restarted), Claude Code's MCP tools go offline silently — restart the port-forward and reload the window.

### Helm MCP