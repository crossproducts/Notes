# Terragrunt

> **Status:** 🔴 Pending — skeleton created, content to be filled in.

## Why it matters (2026)

Terragrunt keeps Terraform DRY across many environments — it manages remote state,
provider config, and dependency ordering so each env is a thin config file.

## Planned topics

- [ ] `terragrunt.hcl` and the `include` block
- [ ] Remote state backend generation
- [ ] DRY environments: `live/` directory pattern
- [ ] `dependency` blocks and ordering
- [ ] `run-all` apply/plan across stacks
- [ ] Terragrunt vs Terraform workspaces vs plain modules

## Labs

- [ ] [eks-terraform/live](../../../Labs/AWS/eks-terraform/live/) — vpc / eks / argocd live stacks

## See also

- [Terraform](../Terraform/) · [Platform-Engineering](../Platform-Engineering/)
