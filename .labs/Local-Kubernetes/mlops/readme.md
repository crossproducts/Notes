# MLOps Lab — k3d + ArgoCD + Full Stack

A self-contained MLOps platform running on a local k3d cluster, managed entirely via ArgoCD GitOps.

## Stack

| Component | Tool | Ingress | Port |
|-----------|------|---------|------|
| GitOps | ArgoCD | argocd.localhost | 80 |
| LLM Serving | Ollama | ollama.localhost | 11434 |
| Object Storage | MinIO | minio.localhost / minio-console.localhost | 9000 / 9001 |
| Experiment Tracking | MLflow | mlflow.localhost | 5000 |
| Notebooks | JupyterLab | jupyter.localhost | 8888 |
| Pipeline Orchestration | Airflow | airflow.localhost | 8080 |
| ML Monitoring | Evidently | evidently.localhost | 8000 |

## Architecture

```
  [JupyterLab] -----> [Ollama]
      |
      v
  [MLflow] ---------> [MinIO]
      ^                  ^
      |                  |
  [Airflow] ------------|
      |
      v
  [Evidently]
```

All services communicate via cluster-internal DNS: `<svc>.<ns>.svc.cluster.local`

## Quickstart

### 1. Create the k3d cluster

```bash
k3d cluster create mlops \
  --port "80:80@loadbalancer" \
  --port "443:443@loadbalancer" \
  --k3s-arg "--disable=traefik@server:0"  # optional: use default traefik
```

Or with Traefik (default k3s behavior):

```bash
k3d cluster create mlops --port "80:80@loadbalancer"
```

### 2. Bootstrap ArgoCD

```bash
# Install ArgoCD
kubectl apply -k bootstrap/argocd/

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=120s

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### 3. Deploy the root app (app-of-apps)

```bash
kubectl apply -f bootstrap/root/root-app.yaml
```

ArgoCD will automatically discover and sync all apps in the `apps/` directory, deploying them in sync-wave order:

1. Ollama (wave 0)
2. MinIO (wave 1)
3. MLflow (wave 2)
4. JupyterLab (wave 3)
5. Airflow (wave 4)
6. Evidently (wave 5)

### 4. Verify

```bash
kubectl get pods -A
```

Visit [argocd.localhost](http://argocd.localhost) to see all apps synced.

## Accessing Services

| Service | URL | Credentials |
|---------|-----|-------------|
| ArgoCD | http://argocd.localhost | admin / (see step 2) |
| MinIO Console | http://minio-console.localhost | minioadmin / minioadmin |
| MLflow | http://mlflow.localhost | (no auth) |
| JupyterLab | http://jupyter.localhost | token: `mlops` |
| Airflow | http://airflow.localhost | admin / (check pod logs) |
| Evidently | http://evidently.localhost | (no auth) |
| Ollama | http://ollama.localhost | (API only) |

Airflow standalone prints the admin password on first start:
```bash
kubectl logs -n airflow deployment/airflow | grep "password"
```

## Demo Workflows

### Interactive (JupyterLab)

1. Open http://jupyter.localhost (token: `mlops`)
2. Navigate to `demos/mlops-demo.py`
3. Run the notebook to train 5 model variants, log to MLflow, and query Ollama
4. Check results at http://mlflow.localhost

### Automated Pipeline (Airflow)

1. Open http://airflow.localhost
2. Enable the `mlops_training_pipeline` DAG
3. Trigger a run
4. Watch tasks: prepare_data -> train_model -> [generate_report, summarize_with_ollama]
5. Check MLflow for logged runs, MinIO for artifacts

## Disabling Components

Rename any app file to disable it (ArgoCD prune will clean up resources):

```bash
# Disable evidently
mv apps/evidently.yaml apps/evidently.yaml.disable

# Re-enable
mv apps/evidently.yaml.disable apps/evidently.yaml
```

## Teardown

```bash
k3d cluster delete mlops
```

## Resource Usage

| Component | Memory Request | Memory Limit | Storage |
|-----------|---------------|--------------|---------|
| Ollama | 1Gi | 8Gi | 20Gi |
| MinIO | 256Mi | 1Gi | 5Gi |
| MLflow | 256Mi | 512Mi | 1Gi |
| JupyterLab | 256Mi | 2Gi | 2Gi |
| Airflow | 512Mi | 2Gi | 1Gi |
| Evidently | 128Mi | 512Mi | - |
| **Total** | **~2.4Gi** | **~14Gi** | **29Gi** |
