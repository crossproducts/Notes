## TL;DR

# Steps
```
k3d cluster create dev --api-port 6550 -p "80:80@loadbalancer" -p "443:443@loadbalancer"

kubectl config get-clusters                 # List Context
kubectl config get-contexts                 # Current Context
kubectl config use-context <CONTEXT_NAME>   # Switch Context

kubectl apply -k bootstrap/ --server-side
    or
kubectl apply -k bootstrap/ --server-side --force-conflicts

kubectl -n argocd get secret argocd-initial-admin-secret `
  -o jsonpath="{.data.password}" | % { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }

https://127.0.0.1
    or
https://localhost
```
