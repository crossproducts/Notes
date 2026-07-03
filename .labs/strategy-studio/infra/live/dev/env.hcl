# Environment-level settings (the Terragrunt DRY payoff: prod = copy this dir,
# change these values, nothing else).
locals {
  env          = "dev"
  region       = "us-east-1"
  cluster_name = "strategy-studio-dev"
  vpc_cidr     = "10.60.0.0/16"
}
