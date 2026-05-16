locals {
  env = read_terragrunt_config(find_in_parent_folders("env.hcl")).locals
}

remote_state {
  backend = "s3"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    bucket         = local.env.state_bucket
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = local.env.region
    encrypt        = true
    dynamodb_table = local.env.lock_table
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "aws" {
  region = "${local.env.region}"
  default_tags {
    tags = {
      Project   = "eks-terraform"
      ManagedBy = "Terragrunt"
    }
  }
}
EOF
}

inputs = {
  region       = local.env.region
  cluster_name = local.env.cluster_name
}
