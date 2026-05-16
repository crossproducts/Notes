# ArgoCD

> **Status:** 🔴 Pending — skeleton created, content to be filled in.

## Why it matters (2026)

ArgoCD is the most widely used GitOps controller for Kubernetes — it watches Git and
reconciles the cluster to match.

## Planned topics

- [ ] Core objects: Application, ApplicationSet, AppProject
- [ ] App-of-apps / root-app bootstrap pattern
- [ ] Sync policies: manual vs automated, prune, self-heal
- [ ] Sync waves and hooks
- [ ] Helm and Kustomize sources
- [ ] Health and sync status model
- [ ] Multi-cluster management
- [ ] RBAC and SSO integration

## Labs

- [ ] [argocd-k3d](../../../Labs/Local-Kubernetes/argocd-k3d/)
- [ ] [argocd-minikube](../../../Labs/Local-Kubernetes/argocd-minikube/)
- [ ] [eks-terraform](../../../Labs/AWS/eks-terraform/) — ArgoCD bootstrapped on EKS

## See also

- [GitOps](../GitOps/) · [Helm](../Helm/)
