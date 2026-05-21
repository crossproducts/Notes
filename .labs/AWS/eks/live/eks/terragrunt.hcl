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
  node_instance_types = ["m5.large"]
  node_min_size      = 2
  node_max_size      = 5
  node_desired_size  = 2
}
