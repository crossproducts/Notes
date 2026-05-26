# Rook Ceph — Learning Guide (Homelab)

Rook Ceph gives the homelab **real distributed storage**: block volumes, a shared
filesystem, and S3-compatible object storage, all self-healing and replicated.
This is the storage layer behind every other PVC in the cluster.

- Manifests: ArgoCD app at [apps/storage.yaml](apps/storage.yaml)
- Dashboard: http://ceph.localhost
- Namespace: `rook-ceph`

---

## 1. What is Rook? What is Ceph?

**Ceph** is a mature, open-source distributed storage system. One Ceph cluster
exposes three storage interfaces at once:

| Interface | Ceph component | Kubernetes use |
|-----------|----------------|----------------|
| **Block** (RBD) | RADOS Block Device | `ReadWriteOnce` PVCs — databases, single-pod volumes |
| **File** (CephFS) | Ceph Filesystem | `ReadWriteMany` PVCs — shared volumes across pods |
| **Object** (RGW) | RADOS Gateway | S3 / Swift API buckets |

All three sit on top of **RADOS** — the object store that actually distributes and
replicates data across disks.

**Rook** is the *operator* that runs Ceph **inside Kubernetes**. You don't run
`ceph` admin commands to build the cluster; you declare Ceph custom resources
(`CephCluster`, `CephBlockPool`, `CephFilesystem`, …) and Rook reconciles them —
deploying daemons, formatting disks, wiring up CSI drivers, and healing failures.

> **Rook = "Ceph, but as Kubernetes CRDs."**

---

## 2. The Ceph daemons (what those pods are)

After install, `kubectl -n rook-ceph get pods` shows several daemon types:

| Daemon | Pod prefix | Job |
|--------|-----------|-----|
| **MON** (monitor) | `rook-ceph-mon-*` | Holds the cluster map / quorum. Odd count (1, 3, 5). The brain's memory. |
| **MGR** (manager) | `rook-ceph-mgr-*` | Metrics, the dashboard, orchestration modules. |
| **OSD** (object storage daemon) | `rook-ceph-osd-*` | **One per disk.** Stores the actual bytes. More OSDs = more capacity + redundancy. |
| **MDS** (metadata server) | `rook-ceph-mds-*` | Only for CephFS — serves filesystem metadata. |
| **RGW** | `rook-ceph-rgw-*` | Only for object storage — the S3 gateway. |
| **operator** | `rook-ceph-operator-*` | Rook itself, reconciling all of the above. |
| **toolbox** | `rook-ceph-tools-*` | A pod with the `ceph`/`rbd` CLIs for you to run commands. |

The data path: **PVC → CSI driver → RBD/CephFS → RADOS → OSDs → disks.**

---

## 3. The Topology feature

"Topology" in Ceph means **where your data physically lives**, and how Ceph uses
that to survive failures. There are two related things people mean by it:

### 3a. CRUSH topology & failure domains (the placement engine)

Ceph never asks a central server "where is object X?" — it *computes* the location
with the **CRUSH algorithm** over a tree called the **CRUSH map**:

```
root default
└── datacenter dc1
    └── rack rack1
        ├── host node-a
        │   ├── osd.0
        │   └── osd.1
        └── host node-b
            ├── osd.2
            └── osd.3
```

A pool's **`failureDomain`** tells CRUSH how far apart to spread the replicas of
each piece of data. With `failureDomain: host` and `replicated.size: 3`, Ceph
guarantees the 3 copies land on **3 different hosts** — so losing a whole node
loses zero data. Common domains: `osd` < `host` < `rack` < `datacenter`.

```yaml
cephBlockPools:
  - name: replicapool
    spec:
      failureDomain: host    # spread copies across nodes
      replicated:
        size: 3
```

> **In this homelab** we use `failureDomain: osd` because k3d is a single node — we
> can only spread copies across the 3 OSD *processes*, not across real hosts. On a
> multi-node cluster you'd switch this to `host`.

### 3b. Topology-aware OSD placement (`topology` labels)

Rook reads standard Kubernetes **topology labels** on your nodes to build the CRUSH
tree automatically. Label your nodes and Rook slots OSDs into the right CRUSH bucket:

```bash
kubectl label node node-a   topology.kubernetes.io/zone=zone-a
kubectl label node node-a   topology.rook.io/rack=rack1
```

Rook recognizes these CRUSH levels from labels:
`topology.kubernetes.io/region`, `topology.kubernetes.io/zone`,
and `topology.rook.io/{datacenter,room,pod,pdu,row,rack,chassis,host}`.

You then steer OSDs onto specific nodes/zones with **placement** rules in the
`CephCluster` (node affinity, tolerations, topology spread constraints):

```yaml
cephClusterSpec:
  storage:
    storageClassDeviceSets:
      - name: zone-a-osds
        placement:
          topologySpreadConstraints:
            - maxSkew: 1
              topologyKey: topology.kubernetes.io/zone
              whenUnsatisfiable: ScheduleAnyway
              labelSelector:
                matchExpressions:
                  - key: app
                    operator: In
                    values: [rook-ceph-osd]
```

This is the lever that makes a Ceph cluster **rack- or zone-aware**: data, MONs,
and MGRs get spread so no single rack/zone outage takes you down.

### 3c. Seeing the topology in the dashboard

The **Ceph Dashboard** (http://ceph.localhost) visualizes all of this:
- **Cluster → Hosts** and **Cluster → OSDs** — the physical inventory.
- **Cluster → CRUSH map** — the live topology tree (root → host → osd) and the
  CRUSH rules each pool uses.
- **Cluster → Physical Disks** — disk-level health.

From the toolbox you can dump the same tree:

```bash
kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- ceph osd tree
kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- ceph osd crush tree
```

---

## 4. How it's deployed here

[apps/storage.yaml](apps/storage.yaml) defines **two** ArgoCD Applications via the
official Rook Helm charts:

1. `storage-rook-ceph` (sync-wave 0) — the **operator** (`rook-ceph` chart): CRDs +
   controller + CSI drivers.
2. `storage-rook-ceph-cluster` (sync-wave 1) — the **cluster** (`rook-ceph-cluster`
   chart): the `CephCluster`, a block pool, a CephFS, the dashboard, and the toolbox.

Wave ordering matters: the CRDs from wave 0 must exist before the cluster CRs in
wave 1 can be applied (hence `SkipDryRunOnMissingResource=true`).

### The k3d disk problem (important)

Ceph wants **raw block devices**. k3d nodes are containers with no spare disks, so
instead of `useAllDevices: true` we use a **`storageClassDeviceSet`** that carves
OSDs out of PVCs from k3d's built-in `local-path` StorageClass:

```yaml
storage:
  useAllNodes: false
  useAllDevices: false
  storageClassDeviceSets:
    - name: local-osd
      count: 3                # 3 OSDs
      volumeClaimTemplates:
        - spec:
            storageClassName: local-path
            volumeMode: Block   # Ceph consumes the PVC as a raw block device
            resources: {requests: {storage: 10Gi}}
```

This is "Ceph on top of local-path" — fine for **learning**, not for production
(you're layering a distributed store over node-local disk, with no real fault
isolation). On real hardware you'd give k3d/k8s nodes actual disks and use
`useAllDevices: true`.

> Want even more disks? Recreate the cluster with extra mounts, e.g.
> `k3d cluster create homelab --volume /dev/sdb:/dev/sdb@server:0` and switch to
> device-based OSDs.

---

## 5. Deploy it

```bash
# ArgoCD is already running (see readme.md). Just sync the new app:
kubectl apply -f bootstrap/root/root-app.yaml      # if not already applied
# ArgoCD discovers apps/storage.yaml and syncs operator → cluster.

# Watch the cluster come up (takes a few minutes):
kubectl -n rook-ceph get pods -w
```

The cluster is healthy once you see `mon`, `mgr`, and 3 `osd` pods `Running`, and:

```bash
kubectl -n rook-ceph exec -it deploy/rook-ceph-tools -- ceph status
# look for: health: HEALTH_OK
```

### Dashboard login

```bash
# URL: http://ceph.localhost   (user: admin)
kubectl -n rook-ceph get secret rook-ceph-dashboard-password \
  -o jsonpath='{.data.password}' | base64 -d; echo
```

*(Reading a Secret's `.data` is fine here — it's the dashboard's own generated
password, not a credential we carry elsewhere. Don't paste it into commits.)*

---

## 6. Using the storage

After sync you get two new StorageClasses:

```bash
kubectl get storageclass
# ceph-block        rook-ceph.rbd.csi.ceph.com       (RWO block)
# ceph-filesystem   rook-ceph.cephfs.csi.ceph.com    (RWX shared)
```

### Block volume (RWO) — e.g. a database

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data
spec:
  storageClassName: ceph-block
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 5Gi
```

### Shared filesystem (RWX) — many pods, same volume

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared
spec:
  storageClassName: ceph-filesystem
  accessModes: [ReadWriteMany]
  resources:
    requests:
      storage: 5Gi
```

### Make Ceph the cluster default (optional)

```bash
kubectl patch storageclass ceph-block \
  -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

You could then re-point existing PVCs (Ollama, Open WebUI, Hermes, etc.) at Ceph
instead of `local-path` to get replication.

---

## 7. The toolbox (your Ceph CLI)

```bash
TOOLS="kubectl -n rook-ceph exec -it deploy/rook-ceph-tools --"

$TOOLS ceph status          # overall health, capacity, daemon counts
$TOOLS ceph osd status      # per-OSD usage
$TOOLS ceph osd tree        # the CRUSH topology tree
$TOOLS ceph df              # capacity per pool
$TOOLS ceph osd pool ls     # list pools
$TOOLS rados df             # raw object stats
$TOOLS ceph health detail   # explain any HEALTH_WARN
```

---

## 8. Object storage (S3) — optional next step

Object storage is disabled by default (`cephObjectStores: []`) to save resources.
To explore the S3 side, add an object store + bucket class in the cluster values:

```yaml
cephObjectStores:
  - name: my-store
    spec:
      metadataPool: {failureDomain: osd, replicated: {size: 3}}
      dataPool:     {failureDomain: osd, replicated: {size: 3}}
      gateway:
        port: 80
        instances: 1
    storageClass:
      enabled: true
      name: ceph-bucket
```

Then create an `ObjectBucketClaim` to get S3 credentials and an endpoint —
turning the homelab into a mini self-hosted S3.

---

## 9. Enable / disable

Like the other homelab apps, Rook Ceph is just YAML in `apps/`:

- **Disable:** rename `apps/storage.yaml` → `apps/storage.yaml.disable` and commit.
  ArgoCD prunes the resources. (Ceph has finalizers — see cleanup below.)
- **Re-enable:** rename it back.

### Clean teardown

Ceph CRs use finalizers and a cluster-protection flag, so a plain delete can hang:

```bash
# 1. let ArgoCD remove the apps, then if the namespace is stuck:
kubectl -n rook-ceph patch cephcluster rook-ceph \
  --type merge -p '{"spec":{"cleanupPolicy":{"confirmation":"yes-really-destroy-data"}}}'
# 2. nuke from orbit if needed:
k3d cluster delete homelab
```

> The PVCs backing the OSDs live on `local-path` (node disk). Deleting the cluster
> reclaims them per each StorageClass's `reclaimPolicy`.

---

## 10. Mental model recap

- **Rook** = operator; **Ceph** = the storage engine it runs.
- Declare CRDs (`CephCluster`, `CephBlockPool`, `CephFilesystem`) → Rook builds it.
- **OSD = one disk.** **MON = quorum/brain.** **MGR = dashboard/metrics.**
- **Topology / CRUSH + `failureDomain`** = how copies are spread to survive failures;
  driven by node **topology labels** and **placement** rules.
- Three interfaces from one cluster: **block (RBD)**, **file (CephFS)**, **object (RGW)**.
- Here it runs on **local-path PVCs** because k3d has no real disks — great for
  learning the model, not for production durability.

### References
- Rook docs: https://rook.io/docs/rook/latest/
- Ceph CRUSH / topology: https://rook.io/docs/rook/latest/CRDs/Cluster/ceph-cluster-crd/#osd-topology
- Dashboard: https://rook.io/docs/rook/latest/Storage-Configuration/Monitoring/ceph-dashboard/
