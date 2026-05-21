locals {
  stacks = {
    vpc = {
      description = "VPC — 3-AZ network foundation"
      root        = "live/vpc"
      depends_on  = []
    }
    eks = {
      description = "EKS cluster with managed node groups"
      root        = "live/eks"
      depends_on  = ["vpc"]
    }
    addons = {
      description = "EKS managed addons (CSI drivers, vpc-cni) + IRSA roles"
      root        = "live/addons"
      depends_on  = ["eks"]
    }
    karpenter = {
      description = "Karpenter autoscaler — controller, NodePool, EC2NodeClass"
      root        = "live/karpenter"
      depends_on  = ["eks"]
    }
    argocd = {
      description = "ArgoCD GitOps controller + root app-of-apps"
      root        = "live/argocd"
      depends_on  = ["karpenter"]
    }
  }
}

# ──────────────────────────────────────────────
# Spacelift Stacks
# ──────────────────────────────────────────────

resource "spacelift_stack" "this" {
  for_each = local.stacks

  name        = "eks-prod-${each.key}"
  description = each.value.description
  space_id    = var.spacelift_space_id

  repository = var.repository
  branch     = var.branch

  project_root            = "${var.project_root}/${each.value.root}"
  terraform_workflow_tool = "TERRAGRUNT"
  terraform_version       = var.terraform_version

  autodeploy = true
  labels     = ["eks-lab", each.key]
}

# ──────────────────────────────────────────────
# Stack Dependencies
# ──────────────────────────────────────────────

locals {
  # Flatten the dependency map into a list of (stack, dependency) pairs
  dependencies = flatten([
    for stack_key, stack in local.stacks : [
      for dep in stack.depends_on : {
        stack_key = stack_key
        dep_key   = dep
      }
    ]
  ])
}

resource "spacelift_stack_dependency" "this" {
  for_each = {
    for d in local.dependencies : "${d.stack_key}-${d.dep_key}" => d
  }

  stack_id            = spacelift_stack.this[each.value.stack_key].id
  depends_on_stack_id = spacelift_stack.this[each.value.dep_key].id
}

# ──────────────────────────────────────────────
# AWS Integration (attach to all stacks)
# ──────────────────────────────────────────────

resource "spacelift_aws_integration_attachment" "this" {
  for_each = spacelift_stack.this

  integration_id = var.aws_integration_id
  stack_id       = each.value.id
  read           = true
  write          = true
}
