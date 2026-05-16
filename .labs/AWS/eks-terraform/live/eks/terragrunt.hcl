include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/eks"
}

dependency "vpc" {
  config_path = "../vpc"
}

inputs = {
  vpc_id             = dependency.vpc.outputs.vpc_id
  private_subnet_ids = dependency.vpc.outputs.private_subnet_ids
  cluster_version    = "1.31"
  fargate_namespaces = ["kube-system", "argocd", "default"]
}
