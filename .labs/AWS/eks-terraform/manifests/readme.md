# manifests/

Raw Kubernetes manifests, grouped one folder per app:

```
manifests/
├── nginx/
│   ├── deployment.yaml
│   └── service.yaml
└── podinfo/
    ├── deployment.yaml
    └── service.yaml
```

Each folder is referenced by an ArgoCD `Application` over in `../apps/`.
