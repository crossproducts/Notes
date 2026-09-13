#!/bin/sh
# Deploy Strategy Studio to the local k3s cluster.
# Prereqs: docker build -t strategy-studio/backtest-api:local backtest-api/
#          docker save strategy-studio/backtest-api:local | k3s ctr images import -
#          cp k8s/local/01-secrets.example.yaml k8s/local/01-secrets.yaml && edit real keys in
set -eu
cd "$(dirname "$0")/../.."   # repo root (strategy-studio/)

kubectl apply -f k8s/local/00-namespace.yaml

if [ -f k8s/local/01-secrets.yaml ]; then
  kubectl apply -f k8s/local/01-secrets.yaml
else
  echo "no k8s/local/01-secrets.yaml — applying placeholder keys from 01-secrets.example.yaml"
  echo "(paper trading / options endpoints will 401 until you replace them)"
  kubectl apply -f k8s/local/01-secrets.example.yaml
fi

kubectl create configmap grafana-datasources -n strategy-studio \
  --from-file=grafana/provisioning/datasources/studio.yml \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap grafana-dashboard-provider -n strategy-studio \
  --from-file=grafana/provisioning/dashboards/provider.yml \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl create configmap grafana-dashboards -n strategy-studio \
  --from-file=grafana/dashboards/studio.json \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f k8s/local/02-postgres.yaml
kubectl apply -f k8s/local/03-api.yaml
kubectl apply -f k8s/local/04-grafana.yaml

echo
echo "Waiting for rollout..."
kubectl -n strategy-studio rollout status deployment/postgres --timeout=120s
kubectl -n strategy-studio rollout status deployment/backtest-api --timeout=120s
kubectl -n strategy-studio rollout status deployment/grafana --timeout=120s

echo
echo "Up. Reach it with:"
echo "  kubectl -n strategy-studio port-forward svc/backtest-api 8001:8000   # http://localhost:8001/ui"
echo "  kubectl -n strategy-studio port-forward svc/grafana 3001:3000        # http://localhost:3001"
