# GitOps

> **Status:** 🔴 Pending — skeleton created, content to be filled in.

## Why it matters (2026)

GitOps makes Git the single source of truth for infrastructure and apps: the cluster
continuously reconciles to what the repo declares. It is the default deployment model
for Kubernetes platforms.

## Planned topics

- [ ] Declarative desired state vs imperative `kubectl apply`
- [ ] Reconciliation loop and drift detection
- [ ] App-of-apps pattern
- [ ] Environment promotion (dev → staging → prod) via Git
- [ ] Repo structure: config repo vs app repo
- [ ] Secrets in GitOps (Sealed Secrets, External Secrets, SOPS)
- [ ] Rollbacks = `git revert`

## Labs

- [ ] [argocd-k3d](../../../Labs/Local-Kubernetes/argocd-k3d/) — working app-of-apps lab

## See also

- [ArgoCD](../ArgoCD/) · [Helm](../Helm/) · [CI-CD](../CI-CD/)
