# Labs: Security

> **Status:** 🔴 Pending — skeleton created, content to be filled in.

## Goal

Practice the secure software supply chain and Kubernetes hardening hands-on.

## Planned labs

- [ ] Build image → scan with Trivy/Grype → fail on critical CVEs
- [ ] Generate an SBOM and attach it to the image
- [ ] Sign images with Cosign; verify signatures at deploy time
- [ ] Admission policy that only allows signed images (Kyverno / OPA Gatekeeper)
- [ ] Kubernetes RBAC least-privilege walkthrough
- [ ] NetworkPolicy default-deny lab
- [ ] Secret scanning in CI (gitleaks / trufflehog)
