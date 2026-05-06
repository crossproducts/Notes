# EKS Fargate + Terraform/Terragrunt + ArgoCD

A starter lab that stands up a pure-Fargate EKS cluster on AWS, installs ArgoCD via Terraform, and hands off ongoing app delivery to GitOps.

## Layout

```
eks-terraform/
├── bootstrap/               # one-time: S3 + DynamoDB for remote TF state (local state)
├── live/                    # Terragrunt units (per-component remote state)
│   ├── terragrunt.hcl       # root: backend + AWS provider
│   ├── env.hcl              # shared inputs (region, cluster name, bucket, lock table)
│   ├── vpc/
│   ├── eks/
│   └── argocd/
├── modules/                 # Terraform modules consumed by Terragrunt units
│   ├── vpc/
│   ├── eks/
│   └── argocd/              # helm_release + kubectl_manifest (root-app)
├── apps/                    # ArgoCD Application CRs (root-app syncs from here)
└── manifests/               # raw K8s manifests grouped per app
```

## Prereqs
- AWS account + credentials (`aws configure` or SSO)
- Terraform >= 1.5
- Terragrunt >= 0.55
- kubectl, helm
- An S3 bucket name that's globally unique (default: `crossproducts-tf-state-eks-lab`)

## Apply order
1. **Bootstrap state backend** — creates the S3 bucket and DynamoDB lock table:
   ```powershell
   cd bootstrap
   terraform init
   terraform apply
   ```
2. **Bring up the cluster**:
   ```powershell
   cd ../live
   terragrunt run-all apply
   ```
   Terragrunt walks `vpc → eks → argocd` based on the declared dependencies.
3. **Wire up kubectl**:
   ```powershell
   aws eks update-kubeconfig --name eks-lab --region us-east-1
   ```
4. **Reach ArgoCD** — port-forward (no LB cost):
   ```powershell
   kubectl -n argocd port-forward svc/argocd-server 8080:443
   ```
   Then https://localhost:8080. Initial admin password:
   ```powershell
   kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | % { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
   ```

## How GitOps is wired
Terraform installs ArgoCD via `helm_release`, then applies a single `root-app` `Application` that points at `apps/` in this repo. Anything you drop into `apps/` (as an ArgoCD `Application`) gets reconciled. Those `Application`s in turn point at folders under `manifests/`. From here on, app changes are git-driven; Terraform stays out.

## Fargate constraints to know
- **No DaemonSets** run. Anything that wants a node-level agent (node-exporter, Falco, Cilium-as-CNI) won't deploy without adding a managed node group.
- **All pods land in private subnets** behind a single NAT gateway (~$32/mo + data transfer).
- **CoreDNS** is patched via the EKS addon `configuration_values` to run on Fargate.
- The `kube-proxy` and `vpc-cni` addons are intentionally **not** installed — Fargate doesn't use them.

## Cost rough-cut (us-east-1, idle)
- EKS control plane: $0.10/hr ≈ $73/mo
- NAT gateway: ~$32/mo + data
- Fargate pods (CoreDNS + ArgoCD): a few cents/hr depending on size
No LBs, no EBS — port-forward keeps it minimal.

## Tear down
```powershell
cd live
terragrunt run-all destroy

cd ../bootstrap
terraform destroy   # only if you also want to delete the state bucket / lock table
```
