# Kubernetes

## Architecture Mental Model

<details>
<summary>Details: #1</summary>

```
🌍 Internet
(user / browser / API client)
        ↓
Ingress Controller (Traefik / NGINX / etc)
+ Ingress Resource (host/path rules)
        ↓
Service (stable networking abstraction)
- ClusterIP     (internal)
- NodePort      (node exposed)
- LoadBalancer  (external IP)
        ↓
Workload Controller (decides HOW pods run)
- Deployment   (stateless apps)
- StatefulSet  (stateful apps)
- DaemonSet    (1 per node)
- Job          (run once)
- CronJob      (scheduled)
        ↓
ReplicaSet (ONLY for Deployment)
        ↓
Pods (1..N replicas)
        ↓
Containers (your app runtime)
        ↓
Config Injection
- ConfigMap (non-sensitive config)
- Secret    (passwords, keys)
```
</details>

<details>
<summary>Details: #2</summary>

![alt text](image.png)
 
</details>