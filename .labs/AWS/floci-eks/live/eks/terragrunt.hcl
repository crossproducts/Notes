include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/eks"
}

dependency "vpc" {
  config_path = "../vpc"

  # Lets validate/plan run before vpc is applied.
  mock_outputs = {
    subnet_ids = ["subnet-mock-a", "subnet-mock-b"]
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan"]
}

inputs = {
  subnet_ids      = dependency.vpc.outputs.subnet_ids
  cluster_version = "1.31"
}
