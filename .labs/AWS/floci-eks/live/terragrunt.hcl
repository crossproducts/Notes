locals {
  # Fallback path covers TG 0.96 evaluating this root file as a unit itself
  # (env.hcl sits next to it, not in a parent folder).
  env = read_terragrunt_config(find_in_parent_folders("env.hcl", "${get_parent_terragrunt_dir()}/env.hcl")).locals
}

# TG 0.96 treats this root file as a runnable unit during `run --all`.
# Root is config-only — exclude it from all actions.
# true only when TG evaluates this root file as a unit itself; children
# inherit the block but the condition is false for them.
exclude {
  if      = get_terragrunt_dir() == get_parent_terragrunt_dir()
  actions = ["all"]
}

# Local backend — no S3 bucket needed for Floci testing.
remote_state {
  backend = "local"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    path = "${get_terragrunt_dir()}/terraform.tfstate"
  }
}

# Provider targets Floci on localhost:4566 with dummy credentials.
# Swap this block (and remove the endpoints map) to promote to real AWS.
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "aws" {
  region                      = "${local.env.region}"
  access_key                  = "test"
  secret_key                  = "test"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    eks = "http://localhost:4566"
    ec2 = "http://localhost:4566"
    iam = "http://localhost:4566"
    sts = "http://localhost:4566"
    s3  = "http://localhost:4566"
  }

  default_tags {
    tags = {
      Project   = "floci-eks"
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
