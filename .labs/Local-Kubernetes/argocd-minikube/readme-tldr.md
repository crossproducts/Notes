## TL;DR

# Steps
```
minikube start

minikube addons enable ingress
minikube addons enable ingress-dns

# Make ingress-nginx a LoadBalancer so `minikube tunnel` binds it to 127.0.0.1
kubectl patch svc -n ingress-nginx ingress-nginx-controller --type=merge -p '{\"spec\":{\"type\":\"LoadBalancer\"}}'

minikube tunnel                             # leave running, in its own admin terminal

kubectl config get-clusters                 # List Context
kubectl config get-contexts                 # Current Context
kubectl config use-context <CONTEXT_NAME>   # Switch Context

kubectl apply -k bootstrap/ --server-side
    or
kubectl apply -k bootstrap/ --server-side --force-conflicts

# Set admin password to "admin" (lab only)
$initialPw = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String(
  (kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}')))
argocd login argocd.local --username admin --password $initialPw --insecure
argocd account update-password --current-password $initialPw --new-password admin

https://argocd.local                        # admin / admin
    or
kubectl port-forward svc/argocd-server -n argocd 8080:443
https://localhost:8080/
    or
minikube service argocd-server -n argocd --url
```
