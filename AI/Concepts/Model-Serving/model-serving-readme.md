# Model Serving

> **Status:** 🔴 Pending — skeleton created, content to be filled in.

## Why it matters (2026)

Training a model is half the job; serving it reliably and cheaply is the other half.
Model serving is where AI engineering meets cloud-native infrastructure.

## Planned topics

- [ ] Batch vs real-time (online) inference
- [ ] Inference servers: vLLM, Triton, TGI, KServe, Ray Serve
- [ ] Model autoscaling and scale-to-zero
- [ ] GPU scheduling, node pools, taints/tolerations, NVIDIA device plugin
- [ ] Fractional / time-sliced GPUs
- [ ] AI inference gateways and routing
- [ ] Quantization and serving-time optimization
- [ ] Latency vs throughput vs cost trade-offs
- [ ] Cost control for AI workloads

## See also

- [MLOps-on-Kubernetes](../../Infrastructure/MLOps-on-Kubernetes/)
- [MLOps](../MLOps/) · Decision tree: [Bedrock vs SageMaker vs Self-Hosted](../../../../Architecture/Decision-Trees/)
