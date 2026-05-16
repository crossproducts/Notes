# Kubernetes on Windows: Beginner Setup Guide

This guide helps you start learning Kubernetes on a **Windows** machine with a real local cluster.

## Recommended Path (Fastest): Rancher Desktop

You already have Rancher Desktop, so use it first.

### 1. Enable Kubernetes in Rancher Desktop
1. Open Rancher Desktop.
2. Go to `Settings` -> `Kubernetes`.
3. Check `Enable Kubernetes`.
4. Choose the latest stable Kubernetes version.
5. Apply and restart if prompted.

### 2. Confirm required CLI tools
Rancher Desktop usually installs `kubectl` and sets your kubeconfig.

Run in PowerShell:

```powershell
kubectl version --client
kubectl config get-contexts
kubectl config current-context
kubectl get nodes
```

Expected result: at least one node in `Ready` state.

## First Hands-On Commands

### 1. Create a namespace
```powershell
kubectl create namespace learning
```

### 2. Deploy a sample app
```powershell
kubectl -n learning create deployment hello-nginx --image=nginx:stable
kubectl -n learning expose deployment hello-nginx --port=80 --type=ClusterIP
kubectl -n learning get pods
kubectl -n learning get svc
```

### 3. Access the app locally with port-forward
```powershell
kubectl -n learning port-forward svc/hello-nginx 8080:80
```
Open `http://localhost:8080` in your browser.

### 4. Clean up
```powershell
kubectl delete namespace learning
```

## Core Concepts to Practice Next

Work through these in order:
1. Pods and Deployments
2. Services (`ClusterIP`, `NodePort`, `LoadBalancer`)
3. ConfigMaps and Secrets
4. Volumes and PersistentVolumeClaims
5. Ingress
6. Health checks (`livenessProbe`, `readinessProbe`)

## Alternative Local Cluster Options

### Option A: `kind` (Kubernetes in Docker)
Good for repeatable multi-node lab clusters.

Prerequisite: Docker Desktop installed and running.

Install `kind` on Windows (with winget):
```powershell
winget install Kubernetes.kind
```

Create a cluster:
```powershell
kind create cluster --name learning
kubectl cluster-info --context kind-learning
kubectl get nodes
```

Delete cluster:
```powershell
kind delete cluster --name learning
```

### Option B: `minikube`
Good for local learning too, but Rancher Desktop or kind is usually simpler on Windows if you already have Rancher Desktop.

## Do You Need Ansible?

Short answer: **No** for local learning.

Use Ansible only when you want to automate repeated setup of multiple machines or VMs.
For your current goal (learning Kubernetes basics), run `kubectl` commands directly first.

## Suggested Learning Workflow

1. Keep one markdown note per topic (`pods.md`, `services.md`, etc.).
2. For each topic:
   - Read concept briefly.
   - Create a small YAML manifest.
   - Apply it (`kubectl apply -f ...`).
   - Inspect (`kubectl get ...`, `kubectl describe ...`).
   - Delete and recreate.
3. Repeat until the commands feel natural.

## Useful Daily Commands

```powershell
kubectl get nodes
kubectl get pods -A
kubectl get svc -A
kubectl get deploy -A
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>
kubectl config current-context
```

## Troubleshooting on Windows

If `kubectl` fails:
1. Restart Rancher Desktop.
2. Check context:
   ```powershell
   kubectl config get-contexts
   kubectl config use-context rancher-desktop
   ```
3. Verify cluster health:
   ```powershell
   kubectl get nodes
   ```
4. If needed, disable/re-enable Kubernetes in Rancher Desktop settings.

## Next Step

When this local workflow feels easy, the next upgrade is learning on a cloud-managed cluster (EKS, AKS, or GKE) using the same `kubectl` skills.
