# TL;DR

## Cluster Management
```powershell
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
```powershell
kubectl apply -k bootstrap/ --server-side
    or
kubectl apply -k bootstrap/ --server-side --force-conflicts
```

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
```
# 1. list pending requests (confirm the ID, since pairing requests expire after 5 min)
kubectl exec -n openclaw deploy/openclaw -- openclaw devices list

# 2. approve by requestId
kubectl exec -n openclaw deploy/openclaw -- openclaw devices approve <Request>

# http://openclaw.localhost/chat?session=main
# Token: 5e7a9c3b2f8d1e4a6c8b0d2f5e9a7c3b1f8d4e6a2c9b0d8f5e1a3c7b9d2f6e0a
```