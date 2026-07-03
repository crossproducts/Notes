#!/usr/bin/env sh
# Tear EVERYTHING down. Run this at the end of every lab session — an idle
# dev environment here is ~$5-6/day (EKS control plane + NAT + node + RDS).
set -eu
cd "$(dirname "$0")/live/dev"

: "${TG_STATE_BUCKET:?set TG_STATE_BUCKET to your tfstate bucket first}"

# Delete any k8s LoadBalancer services first or their ALB/NLBs orphan and
# block VPC destroy:
#   kubectl delete svc --all-namespaces --field-selector spec.type=LoadBalancer --all || true

terragrunt run-all destroy --terragrunt-non-interactive
echo "Environment destroyed. Verify in the console that no ELBs/EBS volumes linger."
