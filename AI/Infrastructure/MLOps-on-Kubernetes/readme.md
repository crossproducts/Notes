# MLOps on Kubernetes

> **Status:** 🔴 Pending — skeleton created, content to be filled in.

## Why it matters (2026)

Kubernetes is becoming the standard substrate for production AI. This folder is the
bridge between the [AI](../../../) and [DevOps](../../../../DevOps/) sections — running
training, serving, and RAG workloads on a cluster.

## Planned topics

- [ ] GPU scheduling on Kubernetes (device plugin, node pools, MIG)
- [ ] KServe — model serving on K8s
- [ ] Ray / Ray Serve for distributed inference
- [ ] Kubeflow pipelines
- [ ] MLflow on Kubernetes (tracking + registry)
- [ ] Vector database on Kubernetes
- [ ] RAG pipeline on Kubernetes
- [ ] AI inference gateway
- [ ] Cost control for AI workloads (idle endpoints, GPU utilization)

## Labs

- [ ] RAG app: FastAPI → vector DB → local LLM/Bedrock → OTel → Grafana, deployed via ArgoCD

## See also

- [Model-Serving](../../Concepts/Model-Serving/) · [MLOps](../../Concepts/MLOps/)
- [Platform-Engineering](../../../../DevOps/Learn/Platform-Engineering/)
