# Root terragrunt.hcl — remote state + provider generation for every unit.
# State bucket/table must exist first (one-time):
#   aws s3 mb s3://<bucket> && aws dynamodb create-table --table-name tg-locks \
#     --attribute-definitions AttributeName=LockID,AttributeType=S \
#     --key-schema AttributeName=LockID,KeyType=HASH --billing-mode PAY_PER_REQUEST
# Then: export TG_STATE_BUCKET=<bucket>

locals {
  env    = read_terragrunt_config(find_in_parent_folders("env.hcl")).locals
  region = local.env.region
}

remote_state {
  backend = "s3"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    bucket         = get_env("TG_STATE_BUCKET", "CHANGE-ME-strategy-studio-tfstate")
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = local.region
    encrypt        = true
    dynamodb_table = "tg-locks"
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "aws" {
  region = "${local.region}"
  default_tags {
    tags = {
      Project   = "strategy-studio"
      Env       = "${local.env.env}"
      ManagedBy = "terragrunt"
    }
  }
}
EOF
}
