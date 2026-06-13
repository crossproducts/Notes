# Architecture

## Control flow

```
git push ──► ArgoCD ──► root Application (bootstrap/root)
                          │  applies appsets/*.yaml
                          ▼
              ┌───────────┴────────────┬─────────────────┐
        platform ApplicationSet   apps ApplicationSet   preview-envs ApplicationSet
        (matrix: git × env,        (git × env)          (pullRequest generator)
         RollingSync waves 0–7)                          per open PR
                          │                  │                   │
                          ▼                  ▼                   ▼
            one Application per        podinfo-<env>       preview-pr-<n>
            (component × env)
```

The root is an **app-of-appsets**: a single Application that applies the
ApplicationSet manifests under `appsets/`. Those ApplicationSets use a git
**files** generator over `*/overlays/*/config.json`, so adding an env or
component is just adding a directory with a `config.json`.

## Ingress + TLS

```
client ──https──► k3d :443 ──► servicelb ──► istio ingress gateway
                                              │  (Gateway API `Gateway`,
                                              │   TLS terminated w/ wildcard cert
                                              │   from cert-manager CA)
                                              ▼
                                      HTTPRoute (per app/service)
                                              ▼
                                      in-mesh Service (mTLS via sidecars)
```

cert-manager runs with `ExperimentalGatewayAPISupport=true` and issues a wildcard
`*.<env>.127.0.0.1.sslip.io` cert from the self-signed `opus-ca` ClusterIssuer.
The Istio `Gateway` listener references the resulting secret.

## Progressive delivery (podinfo)

```
new image tag in git
      ▼
ArgoCD syncs Rollout
      ▼
Argo Rollouts: spin canary RS ──► rewrite podinfo VirtualService weights
      │                                    (10 → 25 → 50 → 100)
      ▼
AnalysisTemplate queries Prometheus (istio_requests_total success rate)
      │ pass → next step      │ fail → auto-rollback
      ▼
canary becomes stable
```

Kiali reads the same Prometheus data and renders the live traffic split.

## Preview environments

The `preview-envs` ApplicationSet's `pullRequest` generator creates an ephemeral
Application + namespace per open PR labelled `preview`, building the app from the
PR's head branch. Requires a `github-scm-token` Secret in `argocd` (see
`appsets/preview-envs.yaml`). Closing the PR prunes the namespace.

## Multi-env model

k3d runs one cluster per environment (`opus-dev`, `opus-staging`, `opus-prod`).
You bootstrap an env, and the ApplicationSets deploy the overlays whose
`config.json` matches. Overlays differ by domain (`*.dev` / `*.staging` / `*.prod`)
and resource sizing (replicas, retention, rollout steps).
