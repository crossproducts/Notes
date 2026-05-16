# AI Security

> **Status:** 🔴 Pending — skeleton created, content to be filled in.

## Why it matters (2026)

LLM and agent systems add an entirely new attack surface: untrusted text becomes
executable intent. Knowing the failure modes is now table stakes for AI/ML roles.
This is the *concepts* home; the security-program view lives in
[Security/AI-Security](../../../../Security/AI-Security/).

## Planned topics — OWASP LLM Top 10

- [ ] Prompt injection (direct and indirect)
- [ ] Insecure output handling
- [ ] Training data poisoning
- [ ] Model denial of service
- [ ] Supply-chain vulnerabilities
- [ ] Sensitive information disclosure
- [ ] Insecure plugin / tool design
- [ ] Excessive agency
- [ ] Overreliance
- [ ] Model theft

## Planned topics — agent & MCP specific

- [ ] MCP threat model
- [ ] Agent-with-Kubernetes-access threat model
- [ ] Agent-with-AWS-access threat model
- [ ] Least privilege for AI agents; human approval gates
- [ ] Audit logging for AI tool calls
- [ ] Guardrails and output filtering
- [ ] RAG data leakage / document ACL filtering

## See also

- [Governance](../Governance/) · [MCP](../../Infrastructure/MCP/)
