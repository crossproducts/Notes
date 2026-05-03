## TL;DR

# Steps
```
k3d cluster create dev --api-port 6550 -p "8080:80@loadbalancer" -p "443:443@loadbalancer"

kubectl config get-clusters                 # List Context
kubectl config get-contexts                 # Current Context
kubectl config use-context <CONTEXT_NAME>   # Switch Context

kubectl apply -k bootstrap/ --server-side
    or
kubectl apply -k bootstrap/ --server-side --force-conflicts

https://argocd.local                        # admin / admin
    or
kubectl port-forward svc/argocd-server -n argocd 8080:443
https://localhost:8080/

```
