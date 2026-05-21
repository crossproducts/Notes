# EKS Lab — Terraform + Terragrunt + Spacelift

Production-grade EKS cluster on AWS, managed with Terraform/Terragrunt for infrastructure and ArgoCD for workloads. Spacelift provides IaC CI/CD.

## Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| IaC | Terraform + Terragrunt | Infrastructure provisioning |
| IaC CI/CD | Spacelift | Plan/apply automation with dependency ordering |
| Cluster | EKS 1.31 | Managed Kubernetes with node groups |
| Autoscaling | Karpenter | Just-in-time node provisioning |
| GitOps | ArgoCD | Kubernetes workload delivery |
| Ingress | AWS Load Balancer Controller | ALB/NLB from Ingress resources |
| DNS | ExternalDNS | Auto Route53 records from ingress |
| TLS | cert-manager | Certificate automation |
| Policy | Kyverno | Admission control and policy enforcement |
| Observability | Prometheus + Grafana | Metrics and dashboards |
| Telemetry | ADOT Collector | Traces to X-Ray, logs to CloudWatch |
| Storage | EBS CSI + EFS CSI | Persistent volumes |
| Identity | IRSA | Pod-level AWS IAM permissions |

## Architecture

```
┌─ Spacelift ──────────────────────────────────────────────┐
│  vpc → eks → addons → karpenter → argocd                │
└──────────────────────────────────────────────────────────┘
        │
        ▼
┌─ AWS (Terraform/Terragrunt) ─────────────────────────────┐
│  VPC (3 AZ, public+private, NAT)                         │
│  EKS 1.31 (managed node group m5.large 2-5)              │
│  Addons: vpc-cni, coredns, kube-proxy, EBS/EFS CSI       │
│  Karpenter: c5/m5/r5, on-demand, 32 vCPU limit           │
│  IRSA: ALB Controller, ExternalDNS, ADOT                 │
└──────────────────────────────────────────────────────────┘
        │
        ▼
┌─ ArgoCD (GitOps) ────────────────────────────────────────┐
│  ALB Controller → ExternalDNS → cert-manager             │
│  Kyverno → kube-prometheus-stack → ADOT Collector        │
│  sample-app (podinfo)                                    │
└──────────────────────────────────────────────────────────┘
```

## Directory Structure

```
eks/
├── bootstrap/          # One-time: S3 state bucket + DynamoDB lock table
├── modules/            # Reusable Terraform modules
│   ├── vpc/            # VPC with 3-AZ subnets, NAT, Karpenter tags
│   ├── eks/            # EKS cluster + managed node group
│   ├── addons/         # EKS addons + IRSA roles for all K8s addons
│   ├── karpenter/      # Karpenter controller + NodePool + EC2NodeClass
│   ├── argocd/         # ArgoCD Helm + root app-of-apps
│   └── irsa/           # Generic IRSA role factory
├── live/               # Terragrunt: one dir per component
│   ├── terragrunt.hcl  # Root config (S3 backend, AWS provider)
│   ├── env.hcl         # Shared vars (region, cluster name, bucket)
│   ├── vpc/
│   ├── eks/
│   ├── addons/
│   ├── karpenter/
│   └── argocd/
├── spacelift/          # Spacelift stack definitions (TF)
├── apps/               # ArgoCD Application CRs
└── manifests/          # K8s manifests for git-sourced apps
    └── sample-app/
```

## Prerequisites

- AWS CLI configured (`aws sts get-caller-identity`)
- Terraform >= 1.3.0
- Terragrunt >= 0.50.0
- kubectl
- Spacelift account (for CI/CD — optional for local apply)

## Quickstart

### 1. Bootstrap state backend (one-time)

```bash
cd bootstrap
terraform init
terraform apply
```

### 2. Deploy infrastructure

```bash
cd live
terragrunt run-all apply
```

This deploys in order: VPC → EKS → Addons → Karpenter → ArgoCD.

### 3. Connect kubectl

```bash
aws eks update-kubeconfig --name eks-prod --region us-east-1
```

### 4. Access ArgoCD

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Open https://localhost:8080
# Username: admin
# Password:
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d
```

ArgoCD will auto-sync all apps from `apps/`.

## Spacelift Setup

The `spacelift/` directory defines 5 Spacelift stacks that mirror the Terragrunt components. To set up:

1. Configure Spacelift API credentials (see `.env.example`)
2. Create an AWS integration in Spacelift console
3. Apply the stack definitions:

```bash
cd spacelift
terraform init
terraform apply -var="aws_integration_id=<your-integration-id>"
```

Spacelift will auto-trigger on pushes to `main`.

| Stack | Depends On |
|-------|-----------|
| eks-prod-vpc | — |
| eks-prod-eks | vpc |
| eks-prod-addons | eks |
| eks-prod-karpenter | eks |
| eks-prod-argocd | karpenter |

## ArgoCD Apps

| App | Wave | Namespace | Chart Version |
|-----|------|-----------|---------------|
| AWS LB Controller | 1 | kube-system | 1.7.2 |
| cert-manager | 1 | cert-manager | v1.14.5 |
| ExternalDNS | 2 | external-dns | 1.14.4 |
| Kyverno | 2 | kyverno | 3.2.0 |
| kube-prometheus-stack | 3 | monitoring | 58.2.2 |
| ADOT Collector | 4 | opentelemetry | 0.86.0 |
| sample-app | 5 | default | — |

## Customization

### Change region or cluster name

Edit `live/env.hcl`:
```hcl
locals {
  region       = "us-west-2"
  cluster_name = "my-cluster"
}
```

### Add a new ArgoCD app

1. Create a YAML file in `apps/` (copy an existing one)
2. Set the sync-wave annotation for ordering
3. Commit and push — ArgoCD auto-syncs

### Add Karpenter node types

Edit `modules/karpenter/main.tf` → `kubectl_manifest.nodepool` → `requirements` to add instance types or architectures.

## Teardown

```bash
# Remove ArgoCD apps first (clean up K8s resources)
kubectl delete applications --all -n argocd

# Destroy infrastructure
cd live
terragrunt run-all destroy

# Remove state backend (optional)
cd bootstrap
terraform destroy
```

## Cost Estimate

| Resource | Estimated Monthly Cost |
|----------|----------------------|
| NAT Gateway | ~$32 |
| EKS Control Plane | ~$73 |
| EC2 m5.large x2 (node group) | ~$140 |
| EBS (PVCs) | ~$10 |
| ALB | ~$16 + data |
| **Total baseline** | **~$271/mo** |

> Karpenter-provisioned nodes add to this based on workload demand.
