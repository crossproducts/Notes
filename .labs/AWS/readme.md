# Labs: AWS

> **Status:** 🟢 Active

Cloud labs that provision real AWS infrastructure as code.

## Labs in this folder

| Lab | What it shows |
|---|---|
| [eks-terraform](eks-terraform/) | EKS cluster via Terraform modules + Terragrunt live envs, with ArgoCD bootstrapped on top |

## Ideas to add

- [ ] 3-tier VPC with public/private subnets
- [ ] ECS service behind an ALB
- [ ] Lambda + API Gateway with a custom authorizer
- [ ] Remote Terraform state (S3 + DynamoDB lock)
- [ ] IRSA — IAM Roles for Service Accounts on EKS
