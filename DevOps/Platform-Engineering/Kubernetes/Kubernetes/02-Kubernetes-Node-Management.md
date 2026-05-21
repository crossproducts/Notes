## Node Management

<details>
<summary>Details: #1</summary>

```
Taint        = mark on a NODE that repels pods
Toleration   = mark on a POD that lets it ignore a matching taint
Cordon       = mark node Unschedulable (no NEW pods land here)
Drain        = cordon + evict existing pods so node is safe to remove
Uncordon     = reverse cordon, node accepts new pods again
```

Taints and tolerations work as a pair:
- A taint alone keeps pods OFF a node.
- A toleration alone does NOT force a pod onto a tainted node — it only permits it.
- To pull a pod TOWARD a specific node, combine toleration with `nodeAffinity` or `nodeSelector`.

Taint effects:
- `NoSchedule`       — new pods without a matching toleration are not scheduled
- `PreferNoSchedule` — soft version; scheduler tries to avoid but may place
- `NoExecute`        — also evicts already-running pods that don't tolerate
</details>

<details>
<summary>Details: #2 — Taint commands</summary>

```bash
# Add a taint (key=value:effect)
kubectl taint nodes <node> dedicated=gpu:NoSchedule

# Remove a taint (trailing minus)
kubectl taint nodes <node> dedicated=gpu:NoSchedule-

# Inspect taints on a node
kubectl describe node <node> | grep -i taint
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.taints}{"\n"}{end}'
```

Pod toleration (YAML):

```yaml
spec:
  tolerations:
    - key: "dedicated"
      operator: "Equal"
      value: "gpu"
      effect: "NoSchedule"
```
</details>

<details>
<summary>Details: #3 — Cordon / Drain / Uncordon</summary>

```bash
# Stop scheduling new pods to a node (existing pods stay)
kubectl cordon <node>

# Safely evict pods before maintenance / node removal
kubectl drain <node> \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --grace-period=60 \
  --timeout=5m

# Put the node back in rotation
kubectl uncordon <node>

# Verify
kubectl get nodes        # STATUS shows SchedulingDisabled when cordoned
```

Common drain flags:
- `--ignore-daemonsets`     — DaemonSet pods can't be evicted; skip them
- `--delete-emptydir-data`  — required if pods use `emptyDir` (data is lost)
- `--force`                 — evict pods not managed by a controller (data is lost)
- `--grace-period`          — override pod terminationGracePeriodSeconds
- `--disable-eviction`      — use DELETE instead of eviction API (skips PDBs — dangerous)

PodDisruptionBudgets (PDBs) can block a drain. If `kubectl drain` hangs, check:

```bash
kubectl get pdb -A
kubectl describe pdb <name> -n <ns>
```
</details>

<details>
<summary>Details: #4 — Typical workflows</summary>

```
Node maintenance (kernel patch, reboot):
  1. kubectl cordon <node>
  2. kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
  3. perform maintenance
  4. kubectl uncordon <node>

Dedicated workload pool (e.g., GPU nodes):
  1. kubectl taint nodes gpu-1 dedicated=gpu:NoSchedule
  2. add matching toleration + nodeSelector/affinity to GPU pods only
  3. non-GPU pods stay away; GPU pods land here

Control-plane isolation:
  - control-plane nodes carry node-role.kubernetes.io/control-plane:NoSchedule by default
  - only system pods with a matching toleration run there
```
</details>