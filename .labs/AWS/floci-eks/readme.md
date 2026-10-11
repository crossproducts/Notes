# floci-eks

Validate EKS infrastructure-as-code locally and for free using
[Floci](https://floci.io) (MIT-licensed LocalStack replacement).

## Goal

Run the same Terragrunt module layout used in `../eks-terraform` against a local
Floci endpoint. Floci spins up a **real k3s cluster** inside Docker and exposes
a live Kubernetes API, while mocking the AWS control-plane APIs (EKS, IAM, EC2,
STS, S3). No real AWS account, no cost.

## What Floci emulates vs what is real

| Layer | Real | Mocked |
|-------|------|--------|
| Kubernetes API | Yes — k3s (v1.34) running in Docker | n/a |
| `kubectl` workloads | Yes — pods run on a real k3s node | n/a |
| AWS EKS control-plane API | Mocked — returns plausible responses | IAM policy enforcement |
| IAM roles / policy attachments | Created and stored by Floci | Policies are not enforced |
| EC2/VPC resources | Created and stored by Floci | No real network wiring |
| Node group | Object created in Floci state | Backed by k3s, not EC2 |

Auth model: the k3s cluster uses mutual TLS (client certificate), not
`aws eks get-token`. `kubeconfig.sh` extracts the admin kubeconfig from the k3s
Docker container and rewrites the server address to `localhost:<port>`.

## Prerequisites

- Docker Desktop (with Compose v2 and `/var/run/docker.sock` accessible)
- Terraform >= 1.3
- Terragrunt >= 0.96
- kubectl >= 1.25
- No AWS CLI required

## Steps

### 1. Start Floci (+ dashboard)

```sh
docker compose up -d
# wait for healthy
curl http://localhost:4566/_localstack/health | grep '"eks":"running"'
```

The **floci-ui dashboard** is at http://localhost:4500 — browse the emulated
resources (EKS cluster, VPC/subnets, IAM roles) as you apply them.

### 2. Apply infrastructure

```sh
cd live
# Terragrunt 0.96 syntax: pass terraform flags after --
terragrunt run --all --non-interactive apply -- -auto-approve
```

Both units (vpc, eks) apply in order. Expect ~30 s for `aws_eks_cluster` creation
while Floci starts the k3s container.

### 3. Build kubeconfig

```sh
cd ..
bash kubeconfig.sh
```

This script reads `cluster_name` from Terragrunt output, finds the Docker
container named `floci-eks-<cluster-name>`, extracts `/etc/rancher/k3s/k3s.yaml`,
and rewrites the server URL to match the published Docker port.

## Verify

```sh
export KUBECONFIG=$PWD/kubeconfig

kubectl get nodes
# NAME           STATUS   ROLES           AGE   VERSION
# <id>           Ready    control-plane   ...   v1.34.x+k3s1

kubectl create deployment nginx --image=nginx
kubectl rollout status deployment/nginx --timeout=120s
kubectl get pods
# nginx-...   1/1   Running   0   ...
```

## Teardown

```sh
# Delete workloads first
kubectl delete deployment nginx

# Destroy everything (dependency order handled by Terragrunt)
cd live
terragrunt run --all --non-interactive destroy -- -auto-approve

# Stop Floci; manually remove leftover ECR registry container if present
cd ../..
docker compose down
docker rm -f floci-ecr-registry 2>/dev/null || true
```

## Path to real AWS

The only change required is swapping the `generate "provider"` block in
`live/terragrunt.hcl`:

- Remove `access_key`, `secret_key`, `s3_use_path_style`, `skip_*` flags, and the
  `endpoints {}` map.
- Add a real `region` and let the AWS provider resolve credentials normally.

See `../eks-terraform` for a production-ready version using Fargate.

## Quirks

- **Terragrunt 0.96 CLI redesign**: `run-all` is gone; use `terragrunt run --all`.
  Terraform flags must come after `--`.
- **Root unit included in run --all**: Terragrunt 0.96 treats
  `live/terragrunt.hcl` as a runnable unit itself. Fixed in this lab with an
  `exclude` block scoped via `get_terragrunt_dir() == get_parent_terragrunt_dir()`
  (a bare `exclude { if = true }` is inherited by children and excludes
  everything) plus a fallback path in `find_in_parent_folders("env.hcl", ...)`.
  `run --all destroy` works cleanly with this in place.
- **Pre-apply validate/plan**: the eks unit's vpc dependency uses
  `mock_outputs` so `validate`/`plan` work before the first apply.
- **floci-ui port**: the dashboard image serves everything on `$PORT`
  (default mapping here: 4500). Setting `PORT` moves the whole UI, not just
  an API component.
- **Floci ECR registry sidecar**: Floci launches a `registry:2` container named
  `floci-ecr-registry` alongside k3s. It is not stopped by `docker compose down`
  because it is not in the compose file. Remove it manually after teardown.
- **Static token rejected**: Floci's k3s API requires the mTLS client cert from
  `/etc/rancher/k3s/k3s.yaml`, not a bearer token. `kubeconfig.sh` handles this.
- **Health endpoint**: `/_localstack/health` (LocalStack-compatible). `/health`
  also responds but returns less detail.
