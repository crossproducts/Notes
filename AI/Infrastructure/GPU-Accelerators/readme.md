# GPU & Accelerator Infrastructure

> **Status:** 🔴 Pending — skeleton created, content to be filled in.

> The *fleet/cluster* side of accelerated computing. [Nvidia-Cuda](../Nvidia-Cuda/)
> stays the programming-model node; this folder covers the hardware, interconnect,
> collective communication, and telemetry that make multi-GPU/multi-node training work.

## Why it matters (2026)

Training and large-scale inference are bottlenecked less by raw FLOPs and more by
**how GPUs talk to each other**. Understanding NCCL, the interconnect fabric
(NVLink → InfiniBand/EFA), and GPU telemetry (DCGM) is the difference between a
cluster that scales linearly and one that stalls on communication. This is core
NCA AIIO ("AI Infrastructure & Operations") material.

## Concepts

- [ ] **NVIDIA GPU families** — A100, H100/H200, Blackwell (B200/GB200); memory (HBM), FP8/FP4
- [ ] **MIG** (Multi-Instance GPU) — partitioning one GPU into isolated slices
- [ ] **NVLink / NVSwitch** — intra-node GPU-to-GPU fabric
- [ ] **NCCL** — collective comms (all-reduce, all-gather); topology awareness, the backbone of data/tensor/pipeline parallelism
- [ ] **DCGM** — GPU health & telemetry; `dcgm-exporter` → Prometheus → Grafana
- [ ] **RDMA** — kernel-bypass networking (the general concept)
- [ ] **InfiniBand** — the on-prem/HPC RDMA fabric; GPUDirect RDMA
- [ ] **EFA** (Elastic Fabric Adapter) — AWS's RDMA-style interconnect for distributed training
- [ ] GPU scheduling on Kubernetes — device plugin, node pools, MIG (see MLOps-on-Kubernetes)
- [ ] GPU utilization & cost — idle detection, right-sizing, MIG packing

## Lab idea

- [ ] Stand up `dcgm-exporter` + Prometheus + Grafana on the local cluster; visualize
      GPU utilization, memory, and SM clocks while running a small training job.
- [ ] NCCL all-reduce bandwidth test across two GPUs (or two nodes) and compare
      NVLink vs PCIe vs network paths.

## See also

- [Nvidia-Cuda](../Nvidia-Cuda/) — CUDA programming model
- [MLOps-on-Kubernetes](../MLOps-on-Kubernetes/) — GPU scheduling, KServe, distributed inference
- [Model-Serving](../../Concepts/Model-Serving/) · [MLOps](../../Concepts/MLOps/)
- [SageMaker](../../../Cloud/AWS/Services/SageMaker/) — EFA-backed training; [AI-FinOps](../../../Cloud/AWS/FinOps/AI-FinOps.md)
- [eBPF](../../../DevOps/Platform-Engineering/eBPF/) — kernel-level observability for the same nodes
