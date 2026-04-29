# K3s on Windows (via k3d)

## Tech Stack

- **Docker Desktop** (or Rancher Desktop) — container runtime
- **kubectl** — talks to the cluster
- **k3d** — wraps k3s images into a multi-node cluster

---

## 1. Install

Administrator PowerShell:

```powershell
choco install -y docker-desktop kubernetes-cli k3d
```

Start Docker Desktop once so the engine is running, then verify:

```powershell
docker version
kubectl version --client
k3d version
```

---

## 2. Create a cluster

```powershell
# single-node
k3d cluster create lab

# multi-node with port mapping for ingress
k3d cluster create lab --servers 1 --agents 2 -p "8080:80@loadbalancer"
```

k3d merges the kubeconfig into `$HOME\.kube\config` and sets the current context. Verify:

```powershell
kubectl get nodes
kubectl cluster-info
```

---

## 3. Common Commands

### Cluster lifecycle

```powershell
k3d cluster list
k3d cluster stop   lab
k3d cluster start  lab
k3d cluster delete lab
```

| Flag | Purpose |
| --- | --- |
| `--servers N` | number of control-plane nodes |
| `--agents N` | number of worker nodes |
| `-p "8080:80@loadbalancer"` | publish a host port to the cluster's load balancer |
| `--k3s-arg "--disable=traefik@server:*"` | disable bundled Traefik ingress |
| `--image rancher/k3s:v1.30.5-k3s1` | pin a specific k3s version |
| `--volume C:/data:/data@all` | mount a host folder into every node |

### Nodes

```powershell
k3d node list
k3d node create extra --cluster lab --role agent
k3d node delete extra
```

### Load a local image into the cluster

```powershell
docker build -t myapp:dev .
k3d image import myapp:dev -c lab
```

---

## 4. Reset Cluster
```powershell
k3d cluster delete --all
docker system prune -a
```

---

## 5. Uninstall

```powershell
k3d cluster delete lab
choco uninstall k3d kubernetes-cli docker-desktop
```