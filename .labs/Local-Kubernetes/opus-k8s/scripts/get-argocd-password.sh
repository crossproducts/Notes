#!/usr/bin/env bash
# Print the initial ArgoCD admin password (break-glass login before SSO is up).
set -euo pipefail
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d
echo
