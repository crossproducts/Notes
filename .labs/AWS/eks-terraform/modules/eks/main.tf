terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.24"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  cluster_endpoint_public_access           = true
  enable_cluster_creator_admin_permissions = true

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids

  # Pure-Fargate cluster: only CoreDNS addon, patched to schedule on Fargate.
  # kube-proxy and vpc-cni are intentionally not installed -- Fargate doesn't use them.
  cluster_addons = {
    coredns = {
      configuration_values = jsonencode({
        computeType = "Fargate"
        resources = {
          limits = {
            cpu    = "0.25"
            memory = "256M"
          }
          requests = {
            cpu    = "0.25"
            memory = "256M"
          }
        }
      })
    }
  }

  fargate_profiles = {
    for ns in var.fargate_namespaces : ns => {
      name = ns
      selectors = [
        { namespace = ns }
      ]
    }
  }
}
