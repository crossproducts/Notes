# Kubernetes

## Architecture Mental Model

<details>
<summary>Details: #1</summary>

```
🌍 Internet
(user / browser / API client)
        ↓
Ingress Controller (Traefik / NGINX / etc)
+ Ingress Resource (host/path rules)
        ↓
Service (stable networking abstraction)
- ClusterIP     (internal)
- NodePort      (node exposed)
- LoadBalancer  (external IP)
        ↓
Workload Controller (decides HOW pods run)
- Deployment   (stateless apps)
- StatefulSet  (stateful apps)
- DaemonSet    (1 per node)
- Job          (run once)
- CronJob      (scheduled)
        ↓
ReplicaSet (ONLY for Deployment)
        ↓
Pods (1..N replicas)
        ↓
Containers (your app runtime)
        ↓
Config Injection
- ConfigMap (non-sensitive config)
- Secret    (passwords, keys)

Persistent Storage (survives pod restarts)
- PersistentVolumeClaim (PVC)  → pod's REQUEST for storage
        ↓ binds 1:1
- PersistentVolume (PV)        → the ACTUAL storage
        ↓
real disk / cloud block storage (EBS, Ceph, etc)
```
</details>

<details>
<summary>Details: #2</summary>

![alt text](image.png)
 
</details>

## Persistent Storage: PV & PVC

Storage objects live **outside** the workload's lifecycle. A Deployment/StatefulSet
doesn't *contain* storage — it just *references* a PVC by name. The chain:

```
Pod
 └── volumes:
       claimName: my-app-pvc  ──┐  "I want this PVC"
                                ▼
PersistentVolumeClaim (PVC)        ← a REQUEST for storage (size, accessModes)
       status: Bound ──┐
                       ▼  binds 1:1
PersistentVolume (PV)              ← the ACTUAL storage (provisioned by a StorageClass)
                       ▼
real disk / cloud block storage
```

| Object | Who writes it | Lifecycle |
|---|---|---|
| **PVC** | You (manifest) | Independent — **survives** pod restarts and even Deployment deletion |
| **PV**  | Usually auto-created by a StorageClass (dynamic provisioning) | Bound 1:1 to the PVC |

Because the PVC and PV outlive the Pod, a restarted Pod re-mounts the **same** PVC →
**same** PV → **same** data. That's why storage persists across restarts.

### Does a Deployment with a PVC become "stateful"?

No — not in the K8s sense. "Stateful" is about **per-replica identity**, not merely
*having* storage.

- **Deployment** → Pods are interchangeable. All replicas share the **same** PVC
  (`claimName`). At `replicas: 3` they all fight over one PV → breaks with
  `ReadWriteOnce`. Valid pattern: **`replicas: 1` + one PVC** (e.g. Grafana, a wiki).
- **StatefulSet** → uses `volumeClaimTemplates` to stamp out a **dedicated PVC+PV
  per Pod** (`db-0`→`pvc-db-0`, `db-1`→`pvc-db-1`), plus stable names and ordered
  startup. Use for databases, Kafka, etcd.

**Deciding question:** not "does it use a volume?" but "does each replica need its
**own** identity and its **own** storage?" Yes → StatefulSet. Just need one Pod to
not lose data → Deployment + PVC is fine.