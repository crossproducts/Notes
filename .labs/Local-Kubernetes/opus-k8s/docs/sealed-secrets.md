# Sealed Secrets

GitOps means everything lives in Git — but plaintext `Secret` manifests must
not. [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) closes the
gap: you commit an encrypted `SealedSecret` CR, and the in-cluster controller
decrypts it into a native `Secret`. Only the controller's private key can
decrypt, so the ciphertext is safe in a public repo.

## How it fits here

- Controller: `platform/sealed-secrets/` — Helm chart `sealed-secrets`, deployed
  to the `sealed-secrets` namespace as `sealed-secrets-controller`.
- Sync wave **0**, alongside `gateway-api-crds` and `cert-manager`, so it is
  Running before any component (e.g. Keycloak, wave 5) consumes a Secret.
- Encrypt with `scripts/seal-secret.sh`, which calls `kubeseal` pre-pointed at
  the controller's name + namespace.

## The per-cluster caveat

The controller generates its key pair on first start, and it stays in the
cluster. A `SealedSecret` is therefore bound to **the cluster that sealed it** —
you cannot pre-bake valid sealed manifests into a reference repo. The workflow is
always: bootstrap the cluster → controller comes up → `kubeseal` → commit the
output. After a `teardown.sh` + fresh `bootstrap.sh`, re-seal (or restore the
key, below).

## Sealing a secret

```bash
# from a literal
kubectl create secret generic github-scm-token \
  --namespace argocd \
  --from-literal=token=ghp_xxx \
  --dry-run=client -o yaml \
  | ./scripts/seal-secret.sh > platform/.../github-scm-token.sealed.yaml

# or from an existing plaintext manifest
./scripts/seal-secret.sh secret.yaml > secret.sealed.yaml
```

Commit only the `*.sealed.yaml`. The controller recreates the `Secret` in the
namespace encoded in the SealedSecret. For ArgoCD to find SCM creds the resulting
Secret still needs its label, so include it in the source manifest:

```yaml
metadata:
  labels:
    argocd.argoproj.io/secret-type: scm-creds
```

## What to seal in this repo

| Secret | Today | Sealed-secret path |
|---|---|---|
| `github-scm-token` (preview envs) | manual `kubectl create secret` (out of band) | add a `SealedSecret` to a platform/app component synced into `argocd` |
| Keycloak admin password | inline `admin` in `platform/keycloak/base/values.yaml` | seal a Secret, switch `extraEnv` to `valueFrom.secretKeyRef` |
| OIDC client secrets (`*-CHANGEME`) | inline in the realm ConfigMap + `argocd-secret` patch | seal the `argocd-secret` key; inject into the realm via env substitution |

The lab keeps the dev defaults inline so `bootstrap.sh dev` works with zero extra
steps. For staging/prod, replace them with sealed equivalents.

## Back up the sealing key

Losing the controller's private key means every committed `SealedSecret` becomes
undecryptable. Back it up after bootstrap:

```bash
kubectl -n sealed-secrets get secret \
  -l sealedsecrets.bitnami.com/sealed-secrets-key -o yaml > sealed-secrets-key.bak.yaml
```

Store that file in a real secret manager (NOT Git). Restore by applying it before
the controller starts, then restarting the controller.
