# TL;DR

## One-time: state backend
```powershell
cd bootstrap
terraform init
terraform apply
cd ..
```

## Bring up the cluster (Terragrunt)
```powershell
cd live
terragrunt run-all apply
```

Order it walks: `vpc` → `eks` → `argocd` (deps are wired in `terragrunt.hcl`).

## Kubeconfig
```powershell
aws eks update-kubeconfig --name eks-lab --region us-east-1
kubectl get pods -A
```

## ArgoCD
```powershell
# Port-forward (no LB cost)
kubectl -n argocd port-forward svc/argocd-server 8080:443
```
- https://localhost:8080
  - Username: `admin`
  - Password:
    ```powershell
    kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | % { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
    ```

## Tear down
```powershell
cd live
terragrunt run-all destroy

# Then (optional) the state backend itself
cd ../bootstrap
terraform destroy
```
