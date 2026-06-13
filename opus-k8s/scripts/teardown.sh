#!/usr/bin/env bash
# Destroy an opus-k8s k3d cluster.
# Usage: ./scripts/teardown.sh [dev|staging|prod]   (default: dev)
set -euo pipefail

ENV="${1:-dev}"
CLUSTER="opus-${ENV}"

case "$ENV" in dev|staging|prod) ;; *) echo "Unknown env: $ENV"; exit 1 ;; esac

read -r -p "Delete k3d cluster ${CLUSTER}? [y/N] " ans
[[ "${ans:-}" == "y" || "${ans:-}" == "Y" ]] || { echo "aborted"; exit 0; }

k3d cluster delete "${CLUSTER}"
echo "Deleted ${CLUSTER}."
