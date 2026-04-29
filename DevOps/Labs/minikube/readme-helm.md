# Helm

## Installation
- `choco install kubernetes-helm -y`

## Helm Commands
- Verify
    - `helm verify`

## Lab - 1
```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install my-nginx bitnami/nginx

helm list
kubectl get pods
kubectl get svc

kubectl port-forward svc/my-nginx 8080:80

# http://localhost:8080

helm uninstall my-nginx
```