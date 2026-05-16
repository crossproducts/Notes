# Helm

> **Status:** 🔴 Pending — skeleton created, content to be filled in.

## Why it matters (2026)

Helm is the package manager for Kubernetes — it templates manifests, versions releases,
and is the unit most GitOps tools and platforms deploy.

## Planned topics

- [ ] Chart structure: `Chart.yaml`, `values.yaml`, `templates/`
- [ ] Templating: `_helpers.tpl`, named templates, built-in objects
- [ ] Values precedence and overrides per environment
- [ ] Releases, revisions, rollbacks
- [ ] Chart dependencies (subcharts, `Chart.lock`)
- [ ] Repositories and OCI registries
- [ ] Helm vs Kustomize — when to use which
- [ ] Testing charts (`helm lint`, `helm test`)

## Labs

- [ ] [hello-py chart](../../../Labs/Local-Kubernetes/argocd-k3d/helm-charts/hello-py/) — custom chart in the k3d lab

## See also

- [ArgoCD](../ArgoCD/) · [GitOps](../GitOps/) · [Kubernetes](../Kubernetes/)
