# MLOps Lab — k3d + ArgoCD + Full Stack

A self-contained MLOps platform running on a local k3d cluster, managed entirely via ArgoCD GitOps.

## Stack

| Component | Tool | Ingress | Wave |
|-----------|------|---------|------|
| GitOps | ArgoCD | http://argocd.localhost | - |
| LLM Serving | Ollama | http://ollama.localhost | 0 |
| Object Storage | MinIO | http://minio-console.localhost | 1 |
| Experiment Tracking | MLflow | http://mlflow.localhost | 2 |
| Notebooks | JupyterLab | http://jupyter.localhost | 3 |
| Pipeline Orchestration | Airflow | http://airflow.localhost | 4 |
| ML Monitoring | Evidently | http://evidently.localhost | 5 |
| Observability | Prometheus + Grafana | http://grafana.localhost / http://prometheus.localhost | 6 |
| Data Labeling | Label Studio | http://label-studio.localhost | 7 |
| Model Serving | Seldon Core | http://seldon.localhost | 8 |
| Data Processing | Spark (PySpark) | http://spark.localhost | 9 |
| Data Versioning | LakeFS | http://lakefs.localhost | 10 |
| Feature Store | Feast | http://feast.localhost | 11 |
| ML App Frontend | Streamlit | http://streamlit.localhost | 12 |

## Architecture
<div style="text-align: center;">

```
  [Label Studio] --> [LakeFS] --> [MinIO]
       |                ^            ^
       v                |            |
  [Feast] -------> [Spark] ---------+
       |                |
       v                v
  [JupyterLab] --> [Airflow] -----> [MLflow] --> [Seldon Core]
       |                |               |              |
       v                v               v              v
  [Ollama]        [Evidently]     [MinIO S3]    [seldon.localhost]
       |
       v
  [Streamlit] <--- predictions --- [Seldon / MLflow]

  [Prometheus + Grafana] --- monitors all pods
```
</div>

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
k3d cluster create mlops --api-port 6550 -p "80:80@loadbalancer" -p "443:443@loadbalancer"
```

### 2. Bootstrap ArgoCD

```bash
# Install ArgoCD
kubectl apply -k bootstrap/argocd/

# Wait for ArgoCD to be ready
kubectl apply -f bootstrap/root/

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | % { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
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
7. Prometheus + Grafana (wave 6)
8. Label Studio (wave 7)
9. Seldon Core (wave 8)
10. Spark (wave 9)
11. LakeFS (wave 10)
12. Feast (wave 11)
13. Streamlit (wave 12)

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
| Grafana | http://grafana.localhost | admin / prom-operator |
| Prometheus | http://prometheus.localhost | (no auth) |
| Alertmanager | http://alertmanager.localhost | (no auth) |
| Label Studio | http://label-studio.localhost | admin@mlops.local / mlops2024 |
| Spark Master | http://spark.localhost | (no auth) |
| LakeFS | http://lakefs.localhost | (setup wizard on first visit) |
| Feast | http://feast.localhost | (no auth) |
| Streamlit | http://streamlit.localhost | (no auth) |

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
| MLflow | 256Mi | 2Gi | 1Gi |
| JupyterLab | 256Mi | 2Gi | 2Gi |
| Airflow | 512Mi | 2Gi | 1Gi |
| Evidently | 256Mi | 1Gi | - |
| Prometheus + Grafana | ~400Mi | ~1.5Gi | 10Gi |
| Label Studio | 256Mi | 1Gi | 2Gi |
| Seldon Core Operator | 128Mi | 512Mi | - |
| Spark (master + worker) | 1Gi | 3Gi | - |
| LakeFS | 256Mi | 512Mi | 1Gi |
| Feast | 256Mi | 1Gi | 1Gi |
| Streamlit | 256Mi | 1Gi | - |
| **Total** | **~5Gi** | **~25Gi** | **43Gi** |

> Note: Memory limits are burst capacity, not sustained usage. Actual consumption is typically 30-50% of limits.
