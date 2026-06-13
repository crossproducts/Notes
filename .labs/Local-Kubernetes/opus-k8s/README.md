# opus-k8s

A GitOps Kubernetes reference repo for local clusters. ArgoCD drives everything;
Istio provides ingress + mesh; Keycloak provides SSO; Kiali visualizes traffic;
Argo Rollouts does progressive delivery. Runs on **k3d** with three environments
(`dev`, `staging`, `prod`).

## Stack

| Concern | Tool |
|---|---|
| Cluster runtime | k3d (k3s in Docker) |
| GitOps engine | ArgoCD (app-of-appsets + ApplicationSets) |
| Packaging / config | Helm (via Kustomize `helmCharts`) + Kustomize overlays |
| Ingress + TLS + mesh | Istio (Gateway API) + cert-manager |
| SSO | Keycloak (OIDC) |
| Mesh observability | Kiali + kube-prometheus-stack |
| Progressive delivery | Argo Rollouts (canary via Istio traffic split) |
| Preview envs | ApplicationSet pullRequest generator |
| Secret management | Sealed Secrets (encrypted manifests safe to commit) |

## Quick start

```bash
./scripts/bootstrap.sh dev          # create cluster + ArgoCD + hand off to GitOps
./scripts/port-forward-argocd.sh    # break-glass UI at https://localhost:8080
./scripts/get-argocd-password.sh    # admin password
```

ArgoCD then reconciles the platform in wave order (see below). Once it converges,
reach services at `https://<svc>.dev.127.0.0.1.sslip.io` (sslip.io resolves to
127.0.0.1, so no /etc/hosts edits needed in most setups).

Tear down with `./scripts/teardown.sh dev`.

## Layout

```
clusters/      k3d configs per env (Traefik disabled, servicelb kept)
scripts/       bootstrap / teardown / access helpers
bootstrap/     manually-applied ArgoCD install + root app-of-appsets
appsets/       ApplicationSets (platform, apps, preview-envs) + argocd-self app
platform/      infra services (base + dev/staging/prod overlays)
apps/          workloads (podinfo: Rollout + Istio canary)
docs/          architecture, SSO, progressive delivery
```

Each `platform/<component>/overlays/<env>/` and `apps/<app>/overlays/<env>/`
carries a `config.json` (`component/app`, `env`, `wave`, `namespace`) that the
ApplicationSet git generator reads to stamp out one Application per (component × env).

## Bootstrap / sync-wave order

ArgoCD applies the platform via ApplicationSet **RollingSync** (plain sync-wave
annotations do NOT order separate Applications):

| Wave | Component | Why first |
|---|---|---|
| 0 | gateway-api-crds, cert-manager, sealed-secrets | CRDs + CA issuer + secret decryption needed by everything |
| 1 | istio-base | Istio CRDs |
| 2 | istiod | control plane (Gateway API + Prometheus merge enabled) |
| 3 | istio-gateway | Gateway + wildcard Certificate (TLS termination) |
| 4 | prometheus | required by Kiali graph + Rollouts analysis |
| 5 | keycloak | OIDC provider |
| 6 | kiali | reads Prometheus + Istio |
| 7 | argo-rollouts | progressive-delivery controller |
| 10 | apps (podinfo) | workloads |

## Key design decisions

- **k3d keeps servicelb** (only Traefik is disabled). Disabling servicelb would
  leave the Istio ingress-gateway `LoadBalancer` Service stuck `<pending>`.
- **Gateway API CRDs are installed explicitly** (wave 0) — k3s only ships them
  with Traefik, which we disable. istiod runs with `PILOT_ENABLE_GATEWAY_API`.
- **Prometheus is mandatory**, not optional — without it Kiali shows no traffic
  and Rollouts canary analysis fails.
- **App namespaces carry `istio-injection=enabled`**; the `argocd` namespace does
  not (a sidecar can break ArgoCD's gRPC/redis).
- **TLS uses a self-signed cert-manager CA** across all envs (Let's Encrypt can't
  validate private `*.sslip.io` wildcards via HTTP-01). ArgoCD trusts this CA via
  `oidc.config.rootCA` so SSO works over HTTPS. See `docs/sso-setup.md`.
- **First login is break-glass `admin` + port-forward**; ArgoCD is served through
  the very Istio gateway it deploys, and SSO depends on Keycloak (wave 5), so SSO
  only works after the platform converges.
- **Keycloak uses `codecentric/keycloakx`** — the Bitnami Keycloak chart moved to
  a legacy/paid registry in 2025.
- **Secrets are sealed, not plaintext** — a wave-0 Sealed Secrets controller
  decrypts committed `SealedSecret` CRs. They're bound to the cluster's key, so
  they're sealed *after* bootstrap with `scripts/seal-secret.sh`; dev keeps inline
  placeholders so `bootstrap.sh dev` works out of the box. See
  `docs/sealed-secrets.md`.
- **ArgoCD self-manages** — after the day-0 imperative install, the `argocd-self`
  Application reconciles `bootstrap/argocd/` from Git, so ArgoCD config/version
  changes become a `git push`. Scoped to be non-destructive: `prune: false`,
  `selfHeal` with `RespectIgnoreDifferences`, and `argocd-secret` `/data` ignored
  (server writes the admin password + OIDC secret there at runtime).

See `docs/architecture.md` for the full data flow.
