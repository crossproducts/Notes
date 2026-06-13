#!/usr/bin/env bash
# Break-glass access to the ArgoCD UI before the Istio gateway / Keycloak SSO are
# Healthy. Open https://localhost:8080 and log in as `admin` (see
# get-argocd-password.sh). Ctrl-C to stop.
set -euo pipefail
echo "ArgoCD UI -> https://localhost:8080  (user: admin)"
kubectl -n argocd port-forward svc/argocd-server 8080:443
