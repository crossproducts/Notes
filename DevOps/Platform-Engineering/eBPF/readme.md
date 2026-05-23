# eBPF

> **Status:** 🔴 Pending — skeleton created, content to be filled in.

> Running sandboxed programs in the Linux kernel without changing kernel source or
> loading modules. The substrate under modern cloud-native networking, observability,
> and runtime security — this is the canonical concept node; cross-link from the
> Observability and Security trees rather than duplicating.

## Why it matters (2026)

eBPF moved from "kernel curiosity" to the dataplane of cloud-native infrastructure.
Cilium is replacing kube-proxy and powering service meshes; Tetragon and Falco do
runtime security from the kernel; Pixie and Parca give zero-instrumentation
observability. Knowing how it works — and its limits — is a 2026 platform skill.

## Concepts

- [ ] What eBPF is — sandboxed kernel programs, the **verifier**, JIT
- [ ] **Maps** — shared state between kernel and userspace
- [ ] **Hooks** — kprobes/uprobes, tracepoints, XDP, tc, LSM
- [ ] **CO-RE** (Compile Once, Run Everywhere) + BTF — portability across kernels
- [ ] Tooling: bpftrace, libbpf, the BPF CO-RE toolchain
- [ ] Limits & gotchas — verifier constraints, kernel version requirements, observability blind spots

## Tool landscape

- [ ] **Cilium** — eBPF CNI, kube-proxy replacement, network policy
- [ ] **Hubble** — network flow observability on top of Cilium
- [ ] **Tetragon** — runtime security observability & enforcement
- [ ] **Falco** — runtime threat detection (eBPF driver)
- [ ] **Pixie** — auto-instrumented app observability
- [ ] **Parca** — continuous profiling

## Lab idea

- [ ] Install Cilium as the CNI on a local k3d/minikube cluster; enable Hubble and
      watch live service-to-service flows; apply an L7 network policy and observe drops.
- [ ] Run a `bpftrace` one-liner to trace `execve` syscalls cluster-wide.

## See also

- [Kubernetes / ServiceMesh](../Kubernetes/) — Cilium as CNI & mesh dataplane
- [Observability](../../Observability/) — Pixie, Parca, continuous profiling
- [Kubernetes-Security](../../../Security/Kubernetes-Security/) — Tetragon, Falco runtime enforcement
- [SWE/Languages/C — Linux System Programming](../../../SWE/Languages/C/) — the kernel-level foundations
- [GPU-Accelerators](../../../AI/Infrastructure/GPU-Accelerators/) — kernel-level telemetry on GPU nodes
