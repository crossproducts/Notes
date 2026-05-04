# ArgoCD App-of-Apps

GitOps lab on top of minikube. A single `kubectl apply -k bootstrap/` installs ArgoCD, applies the root `Application`, and applies an Ingress for the ArgoCD UI; from that point on, ArgoCD owns everything — root reconciles `apps/`, each child reconciles its folder under `manifests/` (Deployment + Service + Ingress per app).

```
argocd/
  bootstrap/
    kustomization.yaml   # references upstream install.yaml + namespace + ingress + root-app
    namespace.yaml       # creates the argocd namespace
    argocd-ingress.yaml  # Ingress for the ArgoCD UI (argocd.localhost)
    root-app.yaml        # root Application -> apps/
  apps/
    nginx.yaml           # child Application -> manifests/nginx
    podinfo.yaml         # child Application -> manifests/podinfo
    ollama.yaml          # child Application -> manifests/ollama   (sync-wave 0)
    openwebui.yaml       # child Application -> manifests/openwebui (sync-wave 1)
    pihole.yaml          # child Application -> manifests/pihole
  manifests/
    nginx/               # Deployment + Service + Ingress (nginx.localhost)
    podinfo/             # Deployment + Service + Ingress (podinfo.localhost)
    ollama/              # Deployment + Service + PVC + Ingress (ollama.localhost)
    openwebui/           # Deployment + Service + PVC + Ingress (openwebui.localhost)
    pihole/              # Deployment + Service (web) + Service (DNS LB) + PVC + Ingress (pihole.localhost)
```

Source repo: <https://github.com/crossproducts/Notes>, branch `main`.

---

## Prerequisites

A running cluster — see [minikube setup](../minikube/readme-setup.md).

```powershell
kubectl config current-context

# Enable the nginx ingress addon (one-time per cluster)
minikube addons enable ingress
kubectl wait -n ingress-nginx --for=condition=ready pod -l app.kubernetes.io/component=controller --timeout=180s

# Patch ingress-nginx-controller to LoadBalancer so `minikube tunnel` exposes it
# at 127.0.0.1. The minikube ingress addon ships it as NodePort, which the
# tunnel does NOT bind — without this patch, https://argocd.localhost won't resolve.
kubectl patch svc -n ingress-nginx ingress-nginx-controller --type=merge -p '{\"spec\":{\"type\":\"LoadBalancer\"}}'
```

---

## 1. Bootstrap

One command installs ArgoCD, the UI ingress, and applies the root app:

```powershell
kubectl apply -k bootstrap/
```

If you see a transient error like `no matches for kind "Application"`, run it once more — kubectl orders CRDs before custom resources, but on very fresh clusters the CRD may not be established before the `Application` is admitted. `kubectl apply` is idempotent.

Wait for ArgoCD to come up:

```powershell
kubectl wait -n argocd --for=condition=available deployment --all --timeout=300s
kubectl get applications -n argocd
```

Expected after a minute or two:

```
NAME           SYNC STATUS   HEALTH STATUS
root-app       Synced        Healthy
nginx          Synced        Healthy
podinfo        Synced        Healthy
```

---

## 2. Wire up host-based access

Minikube on the docker driver runs the cluster inside a container, so the ingress LB IP isn't directly routable from Windows. Run `minikube tunnel` in a separate terminal **as Administrator** and leave it running:

```powershell
minikube tunnel
```

This binds the cluster's LoadBalancer / ingress IPs to `127.0.0.1` on the host. (k3d users skip this — `-p "80:80@loadbalancer" -p "443:443@loadbalancer"` on `k3d cluster create` maps ports directly.)

No DNS configuration is needed. Hostnames use `*.localhost`, which RFC 6761 reserves as loopback — Windows, Chrome, Firefox, curl, and `kubectl` all resolve `podinfo.localhost → 127.0.0.1` natively without consulting a DNS server. New apps work the moment their Ingress exists.

If you previously pointed Windows DNS at Pi-hole for an earlier iteration of this lab, reset it:

```powershell
Set-DnsClientServerAddress -InterfaceAlias 'Wi-Fi'    -ResetServerAddresses
Set-DnsClientServerAddress -InterfaceAlias 'Ethernet' -ResetServerAddresses
ipconfig /flushdns
```

Verify:

```powershell
kubectl get ingress -A
Resolve-DnsName podinfo.localhost              # should return 127.0.0.1
curl http://nginx.localhost
curl http://podinfo.localhost
```

---

## 3. Access the ArgoCD UI

Browse to <https://argocd.localhost> (accept the self-signed cert). Username `admin`. Initial password:

```powershell
$initialPw = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(
  (kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}')))
$initialPw
```

The Ingress is annotated `nginx.ingress.kubernetes.io/backend-protocol: HTTPS`, so ingress-nginx speaks HTTPS to argocd-server (which serves a self-signed cert) and the browser sees the same self-signed cert end-to-end. For real deployments, terminate TLS at ingress with a real cert and run argocd-server in `--insecure` mode.

### Set password to `admin` (lab convenience)

After bootstrap, change the admin password to `admin` so you don't have to look it up. Requires the `argocd` CLI (install via `winget install argocd` / `scoop install argocd` / `choco install argocd-cli`):

```powershell
$initialPw = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(
  (kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}')))

argocd login argocd.localhost --username admin --password $initialPw --insecure
argocd account update-password --current-password $initialPw --new-password admin
```

After this, login with `admin` / `admin`. Don't do this on anything that isn't a local lab — `admin/admin` is the first thing every credential scanner tries.

**kubectl-only fallback** (no argocd CLI): generate a bcrypt hash and patch `argocd-secret`:

```powershell
# Generate a bcrypt hash of "admin" using a throwaway httpd container
$hash = (docker run --rm httpd:2.4 htpasswd -nbBC 10 '' admin) -split ':' | Select-Object -Last 1
$hash = $hash.Trim() -replace '\$2y', '$2a'   # ArgoCD expects $2a$, htpasswd emits $2y$

$now = (Get-Date -AsUTC -Format 'yyyy-MM-ddTHH:mm:ssZ')
kubectl -n argocd patch secret argocd-secret --type=merge `
  -p "{\"stringData\":{\"admin.password\":\"$hash\",\"admin.passwordMtime\":\"$now\"}}"
kubectl -n argocd rollout restart deploy argocd-server
```

---

## 4. Verify workloads

```powershell
kubectl get pods -A
kubectl get ingress -A
```

Browse:

- <http://nginx.localhost>
- <http://podinfo.localhost>
- <http://openwebui.localhost> — chat UI; first signup becomes admin
- <http://ollama.localhost> — Ollama HTTP API (e.g. `curl http://ollama.localhost/api/tags`)
- <http://pihole.localhost/admin> — Pi-hole admin (password `changeme`)

After Ollama is up, pull a model before chatting in OpenWebUI:

```powershell
kubectl exec -n ollama deploy/ollama -- ollama pull llama3.2:3b
```

A 3B-parameter model is ~2 GB and runs reasonably on CPU. Larger models will work but be slow without a GPU.

### Pi-hole

- Web UI: <http://pihole.localhost/admin> — placeholder password is `changeme` (set via `WEBPASSWORD` env in [manifests/pihole/deployment.yaml](manifests/pihole/deployment.yaml); for non-lab use, source from a Secret).
- DNS: exposed as a `LoadBalancer` Service on `127.0.0.1:53`. Pi-hole is **not** load-bearing for ingress routing in this lab (`*.localhost` resolves natively), so this is optional. To use Pi-hole as your machine's actual DNS for ad-blocking:

  ```powershell
  Set-DnsClientServerAddress -InterfaceAlias 'Wi-Fi' -ServerAddresses 127.0.0.1
  ipconfig /flushdns
  Resolve-DnsName -Server 127.0.0.1 doubleclick.net   # should return 0.0.0.0 (blocked)
  ```

  If `kubectl get svc -n pihole pihole-dns` stays `<pending>`, `minikube tunnel` isn't running. If port 53 fails to bind, something on Windows owns it (DNS Client service, WSL, VPN client). Don't point a corporate / VPN-managed adapter at Pi-hole — it'll break split-DNS for work resources.

---

## 5. Test the GitOps loop

1. Edit `manifests/nginx/deployment.yaml` — bump `replicas: 1` to `replicas: 3`.
2. Commit and push to `main`.
3. Within ~3 minutes ArgoCD detects the change. Click **Refresh** in the UI to force it.
4. `kubectl get pods -n nginx` should show 3 pods.

`selfHeal: true` is set, so `kubectl edit deploy -n nginx nginx` will be reverted by ArgoCD on the next sync — git is the source of truth.

---

## Sync ordering (waves)

ArgoCD honors the `argocd.argoproj.io/sync-wave` annotation (string integer, lower goes first, default `0`). Annotate the `Application` CR in `apps/` to order between apps, or annotate individual resources in `manifests/<app>/` to order within an app. Useful when one app depends on another (e.g. cert-manager before apps that need certs).

---

## Upgrading ArgoCD

Bump the tag in [bootstrap/kustomization.yaml](bootstrap/kustomization.yaml) (the `v2.13.2` in the install.yaml URL) and re-run `kubectl apply -k bootstrap/`. Latest releases: <https://github.com/argoproj/argo-cd/releases>.

---

## Cleanup

```powershell
kubectl delete -f bootstrap/root-app.yaml   # cascades via finalizer to children + workloads
kubectl delete -k bootstrap/                # tears down ArgoCD itself + namespace + UI ingress
minikube addons disable ingress             # optional — keeps the addon for future labs otherwise
```

Delete the root-app first so its finalizer can clean up child apps and workloads while ArgoCD is still running. Tearing down ArgoCD before the root-app deletes can leave orphaned resources.
