# ArgoCD App-of-Apps

GitOps lab on top of [k3d](../k3d/readme-setup.md). A single `kubectl apply -k bootstrap/` installs ArgoCD, applies the root `Application`, and applies an Ingress for the ArgoCD UI; from that point on, ArgoCD owns everything — root reconciles `apps/`, each child reconciles its folder under `manifests/` (Deployment + Service + Ingress per app). Ingress is handled by **traefik**, which k3s/k3d ships by default.

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

A running k3d cluster with ports 80/443 mapped from the host into the loadbalancer. Full setup at [../k3d/readme-setup.md](../k3d/readme-setup.md); minimal version:

```powershell
k3d cluster create dev --api-port 6550 -p "80:80@loadbalancer" -p "443:443@loadbalancer"
kubectl config current-context
```

The `-p "80:80@loadbalancer"` and `-p "443:443@loadbalancer"` flags tell Docker to forward those ports from `127.0.0.1` on Windows into k3d's built-in `serverlb`, which fronts traefik. That's what makes `http://*.localhost` reach the cluster — no `minikube tunnel`, no controller patching, no extra services.

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

## 2. Host-based access

No DNS configuration needed. Hostnames use `*.localhost`, which RFC 6761 reserves as loopback — Windows, Chrome, Firefox, curl, and `kubectl` all resolve `podinfo.localhost → 127.0.0.1` natively without consulting any DNS server. Combined with k3d's `-p "80:80@loadbalancer"` mapping, traefik picks up the request and routes by `Host` header to the right Service. New apps work the moment their Ingress exists.

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

[bootstrap/kustomization.yaml](bootstrap/kustomization.yaml) patches `argocd-cmd-params-cm` to set `server.insecure: "true"`, so argocd-server serves plain HTTP on :8080 and traefik terminates TLS at the edge with its built-in self-signed cert. Without this, the browser gets `ERR_TOO_MANY_REDIRECTS`: traefik forwards HTTP, argocd 308-redirects to HTTPS, traefik terminates TLS and forwards HTTP again, loop. The alternative — keep argocd in secure mode and have traefik speak HTTPS upstream — works too, but requires a Traefik `ServersTransport` with `insecureSkipVerify` to accept argocd's self-signed cert and two annotations on the Ingress (`service.serversscheme` + `service.serverstransport`). The patch is simpler. The cert warning you see in the browser is traefik's, not argocd's.

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
- <http://pihole.localhost/admin/> — Pi-hole admin (password `changeme`; bare `/` 404s)

Models are preloaded declaratively. The Ollama Deployment has a `postStart` lifecycle hook that pulls every model listed in the `OLLAMA_PRELOAD_MODELS` env var (space-separated) after the container is ready. Defaults to `llama3.2:3b` (~2 GB, runs reasonably on CPU). To add models, edit [manifests/ollama/deployment.yaml](manifests/ollama/deployment.yaml) and commit:

```yaml
env:
  - name: OLLAMA_PRELOAD_MODELS
    value: "llama3.2:3b qwen2.5:3b phi3:mini"
```

ArgoCD reconciles, the Deployment rolls (Recreate strategy because the PVC is RWO), and the new pod's postStart hook pulls anything not already on the `ollama-models` PVC. `ollama pull` is idempotent, so cached models are a fast no-op.

Watch progress:

```powershell
kubectl logs -n ollama deploy/ollama -f
kubectl exec -n ollama deploy/ollama -- ollama list
```

Larger models work but will be slow without a GPU. The first pull of a 3B model takes ~1–2 minutes depending on bandwidth.

### Pi-hole

- Web UI: <http://pihole.localhost/admin/> — placeholder password is `changeme` (set via `WEBPASSWORD` env in [manifests/pihole/deployment.yaml](manifests/pihole/deployment.yaml); for non-lab use, source from a Secret). Note the trailing `/admin/` — Pi-hole returns 404 on bare `/`.
- DNS: exposed as a `LoadBalancer` Service on `127.0.0.1:53`. Pi-hole is **not** load-bearing for ingress routing in this lab (`*.localhost` resolves natively), so this is optional. To use Pi-hole as your machine's actual DNS for ad-blocking, expose port 53 in your k3d cluster (`-p "53:53@loadbalancer/udp"` on `k3d cluster create`) and then:

  ```powershell
  Set-DnsClientServerAddress -InterfaceAlias 'Wi-Fi' -ServerAddresses 127.0.0.1
  ipconfig /flushdns
  Resolve-DnsName -Server 127.0.0.1 doubleclick.net   # should return 0.0.0.0 (blocked)
  ```

  If port 53 fails to bind on Windows, something else owns it (DNS Client service, WSL, VPN client). Don't point a corporate / VPN-managed adapter at Pi-hole — it'll break split-DNS for work resources.

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
k3d cluster delete dev                      # nuke the whole cluster if you want a clean slate
```

Delete the root-app first so its finalizer can clean up child apps and workloads while ArgoCD is still running. Tearing down ArgoCD before the root-app deletes can leave orphaned resources.
