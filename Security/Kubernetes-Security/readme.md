# Kubernetes Security

> **Status:** 🔴 Pending — skeleton created, content to be filled in.

## Why it matters (2026)

A cluster is a shared multi-tenant control plane. Misconfigured RBAC or open network
paths turn one compromised pod into cluster-wide access.

## Planned topics

- [ ] RBAC — roles, bindings, least privilege, ServiceAccounts
- [ ] NetworkPolicy — default-deny, segmentation
- [ ] Pod Security Standards / admission (non-root, no privilege escalation)
- [ ] Admission controllers — Kyverno, OPA Gatekeeper
- [ ] Secrets handling (encryption at rest, External Secrets)
- [ ] Image provenance — admit only signed images
- [ ] Runtime security (Falco)
- [ ] Supply chain for the cluster itself (add-ons, CRDs)

## See also

- [Kubernetes](../../DevOps/Learn/Kubernetes/) · [Supply-Chain-Security](../Supply-Chain-Security/)
