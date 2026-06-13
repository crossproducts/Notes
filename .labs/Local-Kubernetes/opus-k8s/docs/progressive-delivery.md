# Progressive delivery (Argo Rollouts + Istio)

`apps/podinfo` ships as a `Rollout` (not a Deployment) with a canary strategy that
drives an Istio `VirtualService`.

## Pieces

| File | Role |
|---|---|
| `rollout.yaml` | Canary steps (10→25→50→100%), `trafficRouting.istio`, analysis hook |
| `service-stable.yaml` / `service-canary.yaml` | Targets Rollouts shifts weight between |
| `virtual-service.yaml` | The VS Rollouts rewrites; route name `http` |
| `analysis-template.yaml` | Prometheus success-rate gate (auto-rollback on fail) |

## How a release runs

1. Bump the image in `rollout.yaml` (e.g. `podinfo:6.7.0` → `6.7.1`) and push.
2. ArgoCD syncs the Rollout.
3. Argo Rollouts creates a canary ReplicaSet and sets the VirtualService canary
   weight to 10%.
4. Between each step it runs `podinfo-success-rate`, querying Prometheus for the
   istio request success rate of the canary. `>= 0.95` passes; two failures abort
   and roll back.
5. On success it climbs 25 → 50 → 100%, then the canary becomes stable.

## Watch it

```bash
# install the kubectl plugin once: https://argo-rollouts.readthedocs.io
kubectl argo rollouts get rollout podinfo -n podinfo-dev --watch

# manually promote / abort
kubectl argo rollouts promote podinfo -n podinfo-dev
kubectl argo rollouts abort   podinfo -n podinfo-dev
```

The Argo Rollouts dashboard (enabled in `platform/argo-rollouts/base/values.yaml`)
and Kiali's graph both visualize the shifting split in real time.

## Per-env differences

Overlays patch replicas (dev 1 / staging 2 / prod 3). You can also patch the
canary `steps` per env (e.g. longer pauses + a manual `pause: {}` gate in prod)
via the same `patches:` mechanism used in `apps/podinfo/overlays/<env>/kustomization.yaml`.
