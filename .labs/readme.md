# Labs

> The **proof layer** of this knowledge repo. Notes explain ideas; labs prove you can run
> them. Every lab should be reproducible from scratch and end with a teardown step.

## Index

| Lab area | Status | Focus |
|---|---|---|
| [Local-Kubernetes](Local-Kubernetes/) | 🟢 Active | k3d / minikube clusters, ArgoCD GitOps, Helm charts |
| [AWS](AWS/) | 🟢 Active | EKS provisioned with Terraform + Terragrunt, GitOps on top |
| [AI-Agent-Apps](AI-Agent-Apps/) | 🟢 Active | Agent frameworks, MCP, fine-tuning, GraphRAG |
| [Observability](Observability/) | 🔴 Pending | Prometheus / Loki / Tempo / Grafana / OpenTelemetry stack |
| [Security](Security/) | 🔴 Pending | Image scanning + signing, SBOM, admission policy |
| [FinOps](FinOps/) | 🔴 Pending | Cost dashboard, CUR pipeline, budget alerts |

## Convention

Each lab folder contains a `readme.md` with:

- **Goal** — what the lab demonstrates and why it matters
- **Prerequisites** — tools, versions, accounts
- **Steps** — copy-pasteable, ordered
- **Verify** — how to confirm it worked
- **Teardown** — how to destroy everything cleanly

## Flagship labs (portfolio targets)

- [ ] EKS GitOps platform — Kubernetes + Terraform + ArgoCD + Helm + AWS
- [ ] RAG app on Kubernetes — AI engineering + cloud-native deployment
- [ ] MCP Kubernetes assistant — agent tooling + infra automation
- [ ] AWS mTLS API Gateway platform — security + serverless + networking
- [ ] FinOps cost dashboard — CUR pipeline + Grafana + budget alerts
- [ ] Secure CI/CD pipeline — SBOM + scanning + Cosign signing
