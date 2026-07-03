include "root" {
  path = find_in_parent_folders()
}

locals {
  env = read_terragrunt_config(find_in_parent_folders("env.hcl")).locals
}

terraform {
  source = "tfr:///terraform-aws-modules/vpc/aws?version=5.8.1"
}

inputs = {
  name = "${local.env.cluster_name}-vpc"
  cidr = local.env.vpc_cidr

  azs              = ["${local.env.region}a", "${local.env.region}b"]
  private_subnets  = ["10.60.1.0/24", "10.60.2.0/24"]
  public_subnets   = ["10.60.101.0/24", "10.60.102.0/24"]
  database_subnets = ["10.60.201.0/24", "10.60.202.0/24"]

  create_database_subnet_group = true

  # One NAT gateway (not per-AZ) — lab cost control, ~$32/mo if left running
  enable_nat_gateway = true
  single_nat_gateway = true

  # Tags EKS needs for subnet discovery / load balancers
  public_subnet_tags  = { "kubernetes.io/role/elb" = 1 }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = 1 }
}
