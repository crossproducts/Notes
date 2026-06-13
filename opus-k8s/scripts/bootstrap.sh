#!/usr/bin/env bash
# Bootstrap an opus-k8s environment on k3d, install ArgoCD, and hand off to GitOps.
# Usage: ./scripts/bootstrap.sh [dev|staging|prod]   (default: dev)
set -euo pipefail

ENV="${1:-dev}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLUSTER="fable-${ENV}"

case "$ENV" in dev|staging|prod) ;; *) echo "Unknown env: $ENV"; exit 1 ;; esac

command -v k3d   >/dev/null || { echo "k3d not found";   exit 1; }
command -v kubectl >/dev/null || { echo "kubectl not found"; exit 1; }

echo ">> [1/4] Creating k3d cluster ${CLUSTER} (Traefik disabled, servicelb kept)"
if k3d cluster list | grep -q "^${CLUSTER}\b"; then
  echo "   cluster ${CLUSTER} already exists, skipping create"
else
  k3d cluster create --config "${REPO_ROOT}/clusters/${ENV}.yaml"
fi
kubectl config use-context "k3d-${CLUSTER}"

echo ">> [2/4] Installing ArgoCD (with Keycloak OIDC + insecure-behind-Istio patches)"
kubectl apply -k "${REPO_ROOT}/bootstrap/argocd" --server-side --force-conflicts

echo "   waiting for ArgoCD CRDs..."
kubectl wait --for=condition=Established --timeout=120s \
  crd/applications.argoproj.io crd/applicationsets.argoproj.io

echo "   waiting for argocd-server..."
kubectl -n argocd rollout status deploy/argocd-server --timeout=180s

echo ">> [3/4] Applying root app-of-appsets (GitOps takes over)"
kubectl apply -k "${REPO_ROOT}/bootstrap/root" --server-side --force-conflicts

echo ">> [4/4] Done. Platform converges in wave order via RollingSync."
echo
echo "First access (before Gateway + Keycloak are Healthy) — use break-glass admin:"
echo "   ${REPO_ROOT}/scripts/port-forward-argocd.sh"
echo "   ${REPO_ROOT}/scripts/get-argocd-password.sh"
echo
echo "Once platform is Healthy, hosts (add to /etc/hosts -> 127.0.0.1 if needed):"
echo "   https://argocd.${ENV}.127.0.0.1.sslip.io"
echo "   https://keycloak.${ENV}.127.0.0.1.sslip.io"
echo "   https://kiali.${ENV}.127.0.0.1.sslip.io"
echo "   https://podinfo.${ENV}.127.0.0.1.sslip.io"
