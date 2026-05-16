# apps/

ArgoCD `Application` CRs live here. The Terraform-installed `root-app` watches this folder and reconciles whatever Applications it finds.

## Pattern (mirrors argocd-k3d)
Each app gets one `Application` here that points to its raw manifests under `../manifests/<app>/`. Example:

```yaml
# apps/nginx.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nginx
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/crossproducts/Notes
    targetRevision: main
    path: DevOps/Labs/eks-terraform/manifests/nginx
  destination:
    server: https://kubernetes.default.svc
    namespace: nginx
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

Adding a namespace via `CreateNamespace=true` requires a matching Fargate profile. The default profiles cover `kube-system`, `argocd`, and `default`. To run apps in their own namespace, add it to `fargate_namespaces` in `live/eks/terragrunt.hcl` and re-apply `live/eks`.
