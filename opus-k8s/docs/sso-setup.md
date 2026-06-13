# SSO setup (ArgoCD + Kiali via Keycloak)

Keycloak imports the `opus` realm on startup from the ConfigMap in
`platform/keycloak/base/realm-configmap.yaml`. It pre-creates:

- OIDC client `argocd` (redirect `https://argocd.<env>.127.0.0.1.sslip.io/auth/callback`)
- OIDC client `kiali`
- groups `argocd-admins`, `developers`
- a `groups` protocol mapper (emits the `groups` claim)
- test user `devadmin` / `devadmin` in `argocd-admins`

## 1. Client secret

`bootstrap/argocd/argocd-cm-patch.yaml` references `$oidc.keycloak.clientSecret`.
Create a matching key in the `argocd-secret`:

```bash
kubectl -n argocd patch secret argocd-secret \
  -p '{"stringData":{"oidc.keycloak.clientSecret":"argocd-client-secret-CHANGEME"}}'
```

Use the same value as the `argocd` client `secret` in the realm JSON. **Change
both from the placeholder for any real use.**

## 2. Trust the CA (HTTPS to Keycloak)

ArgoCD talks to Keycloak over HTTPS with a cert from the self-signed `opus-ca`.
Paste the CA into `oidc.config.rootCA` in `argocd-cm-patch.yaml`:

```bash
kubectl -n cert-manager get secret opus-ca-key-pair \
  -o jsonpath='{.data.tls\.crt}' | base64 -d
```

Dev-only fallback (skip verification instead of pinning the CA): add
`oidc.tls.insecure.skip.verify: "true"` to `argocd-cmd-params-cm`.

## 3. RBAC

`bootstrap/argocd/argocd-rbac-cm-patch.yaml` maps Keycloak groups to roles:

```
g, argocd-admins, role:admin
g, developers, role:readonly
```

## 4. First login

SSO only works once Keycloak (wave 5) and the Istio gateway are Healthy. Until
then use break-glass `admin`:

```bash
./scripts/port-forward-argocd.sh        # https://localhost:8080
./scripts/get-argocd-password.sh
```

Then log in via "Keycloak" at `https://argocd.<env>.127.0.0.1.sslip.io`.

## 5. (Optional) Kiali OIDC in prod

Kiali ships with `auth.strategy: anonymous` here (see
`platform/kiali/base/values.yaml`). To require Keycloak login, set in that values
file (or a prod-overlay copy of the chart values):

```yaml
auth:
  strategy: openid
  openid:
    issuer_uri: "https://keycloak.<env>.127.0.0.1.sslip.io/realms/opus"
    client_id: "kiali"
    scopes: ["openid", "profile", "email"]
```

and supply the `kiali` client secret via the `kiali` Secret. Kept anonymous by
default to avoid shipping a patch over the Helm-rendered Kiali ConfigMap.
