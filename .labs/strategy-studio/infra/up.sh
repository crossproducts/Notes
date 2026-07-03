#!/usr/bin/env sh
# Bring the whole dev environment up (~20 min, mostly EKS).
# COSTS REAL MONEY while running — see README.md, and tear down with down.sh.
set -eu
cd "$(dirname "$0")/live/dev"

: "${TG_STATE_BUCKET:?set TG_STATE_BUCKET to your tfstate bucket first}"

terragrunt run-all apply --terragrunt-non-interactive

echo ""
echo "Cluster up. Next:"
echo "  aws eks update-kubeconfig --name strategy-studio-dev --region us-east-1"
echo "  kubectl create namespace argocd && kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
echo "  kubectl apply -f ../../k8s/argocd/app-of-apps.yaml"
