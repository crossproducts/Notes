#!/usr/bin/env bash
# Encrypt a plain Secret manifest into a SealedSecret using the in-cluster
# controller's public key. The output is safe to commit to Git; only the
# controller running in THIS cluster can decrypt it.
#
# Usage:
#   ./scripts/seal-secret.sh secret.yaml > sealed-secret.yaml
#   kubectl create secret generic foo --from-literal=k=v --dry-run=client -o yaml \
#     | ./scripts/seal-secret.sh > sealed-secret.yaml
#
# Note: SealedSecrets are bound to the controller's key, which is generated per
# cluster on first start. Re-seal after recreating a cluster, or back up and
# restore the sealing key (see docs/sealed-secrets.md).
set -euo pipefail

command -v kubeseal >/dev/null || { echo "kubeseal not found (https://github.com/bitnami-labs/sealed-secrets/releases)"; exit 1; }

kubeseal \
  --controller-name sealed-secrets-controller \
  --controller-namespace sealed-secrets \
  --format yaml < "${1:-/dev/stdin}"
