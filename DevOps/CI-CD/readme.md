# CI/CD

> **Status:** 🔴 Pending — skeleton created, content to be filled in.

## Why it matters (2026)

CI/CD is the backbone of delivery. The bar has moved from "it runs the tests" to
"the pipeline is itself secure, fast, and measurable" — DORA metrics, supply-chain
controls, and ephemeral build environments.

## Planned topics

- [ ] Pipeline stages: build → test → scan → package → deploy
- [ ] GitHub Actions (workflows, reusable workflows, OIDC to cloud)
- [ ] Caching and build speed
- [ ] Environments, approvals, and promotion gates
- [ ] Secrets management in pipelines (no long-lived creds)
- [ ] Supply-chain security: SBOM, signing, provenance — see [Supply-Chain-Security](../../../Security/Supply-Chain-Security/)
- [ ] DORA metrics: deployment frequency, lead time, change failure rate, MTTR
- [ ] Trunk-based development vs GitFlow

## See also

- [GitOps](../GitOps/) · [ArgoCD](../ArgoCD/) · [SRE](../SRE/)
