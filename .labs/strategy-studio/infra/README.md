# Strategy Studio — AWS deployment (Terragrunt + EKS + ArgoCD)

The cloud capstone: same studio, deployed to EKS via GitOps. **Local
docker-compose stays the daily driver** — this exists to practice real
IaC/GitOps and is designed to be TORN DOWN after every session.

## Cost reality (us-east-1, while running)

| Component | ~$/day |
|-----------|--------|
| EKS control plane | 2.40 |
| NAT gateway (single) | 1.10 |
| t3.medium spot node | 0.30 |
| RDS db.t4g.micro | 0.40 |
| **Total** | **~$4–6/day** |

Left running a month ≈ $150. **Run `down.sh` at the end of every session.**

## One-time setup

```bash
aws s3 mb s3://<your-tfstate-bucket>
aws dynamodb create-table --table-name tg-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH --billing-mode PAY_PER_REQUEST
export TG_STATE_BUCKET=<your-tfstate-bucket>
```

## Session workflow

```bash
sh up.sh                                   # VPC -> EKS -> ECR -> RDS (~20 min)
aws eks update-kubeconfig --name strategy-studio-dev --region us-east-1

# build & push the api image
aws ecr get-login-password | docker login --username AWS --password-stdin <acct>.dkr.ecr.us-east-1.amazonaws.com
docker build -t <acct>.dkr.ecr.us-east-1.amazonaws.com/strategy-studio/backtest-api:v1 ../backtest-api
docker push <acct>.dkr.ecr.us-east-1.amazonaws.com/strategy-studio/backtest-api:v1

# install ArgoCD + sealed-secrets, then hand over to GitOps
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl apply -f ../k8s/argocd/app-of-apps.yaml   # ArgoCD reconciles api/n8n/grafana

sh down.sh                                 # END OF SESSION — always
```

## Layout (the Terragrunt DRY story)

```
infra/
├── terragrunt.hcl        # root: S3 remote state + provider generation
├── live/dev/
│   ├── env.hcl           # ALL env-specific values live here
│   ├── vpc/  eks/  ecr/  rds/     # thin units wrapping registry modules
├── up.sh / down.sh       # session lifecycle
```
Adding `live/prod/` = copy `dev/`, edit `env.hcl`. That's the Terragrunt payoff.

## Known TODOs (deliberate scaffold gaps)

- RDS uses the VPC default SG — tighten to "5432 from EKS node SG only"
- Module versions pinned to known-good; bump at apply time
- `secret.example.yaml` documents the sealed-secrets flow; never commit raw secrets
- No ingress/ALB yet — `kubectl port-forward` for the lab; AWS LB Controller is a
  natural follow-on exercise
