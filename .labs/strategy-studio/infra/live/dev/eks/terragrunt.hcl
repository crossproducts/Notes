include "root" {
  path = find_in_parent_folders()
}

locals {
  env = read_terragrunt_config(find_in_parent_folders("env.hcl")).locals
}

terraform {
  source = "tfr:///terraform-aws-modules/eks/aws?version=20.24.0"
}

dependency "vpc" {
  config_path = "../vpc"
  mock_outputs = {
    vpc_id          = "vpc-mock"
    private_subnets = ["subnet-mock-a", "subnet-mock-b"]
  }
}

inputs = {
  cluster_name    = local.env.cluster_name
  cluster_version = "1.31" # bump to current at apply time

  vpc_id     = dependency.vpc.outputs.vpc_id
  subnet_ids = dependency.vpc.outputs.private_subnets

  cluster_endpoint_public_access           = true
  enable_cluster_creator_admin_permissions = true

  # Lab cost control: ONE small spot node group. This is a tear-down cluster,
  # not an always-on one — see infra/README.md.
  eks_managed_node_groups = {
    lab = {
      instance_types = ["t3.medium", "t3a.medium"]
      capacity_type  = "SPOT"
      min_size       = 1
      max_size       = 2
      desired_size   = 1
      disk_size      = 30
    }
  }

  cluster_addons = {
    coredns                = {}
    kube-proxy             = {}
    vpc-cni                = {}
    aws-ebs-csi-driver     = {} # PVCs for n8n/grafana
  }
}
