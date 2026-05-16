# Minikube 

## Setup Instructions

- [Chocolatey](https://chocolatey.org/install)
- [Minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/)
    > Powershell, Run as Administrator   
    > `choco install minikube`
- [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
    > Powershell, Run as Administrator   
    > `choco install virtualbox`
- Start Docker Desktop

---

## Minikube Commands

- Start Cluster
    - `minikube start --driver=docker --nodes=4 --container-runtime=docker --cni=calico`
- Resume Cluster
    - `minikube start`
- Status Cluster
    - `minikube status`
- Dashboard Cluster
    - `minikube dashboard`
- Enable Ingress
    - `minikube addons enable ingress`
    - `kubectl get pods -n kube-system`
    - `minikube tunnel`
- Stop Cluster
    - `minikube stop`
- Delete Cluster
    - `minikube delete`

---

## Powershell Alias
### Termporary
```
Set-Alias k kubectl
```
### Permanent
```
notepad $PROFILE
```
Paste: `Set-Alias k kubectl`
Save   
New Powershell

---

## VSCode Extensons
- Microsoft - Kubernetes
- Red Hat - YAML