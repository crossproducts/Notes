include "root" {
  path = find_in_parent_folders()
}

locals {
  env = read_terragrunt_config(find_in_parent_folders("env.hcl")).locals
}

terraform {
  source = "tfr:///terraform-aws-modules/rds/aws?version=6.9.0"
}

dependency "vpc" {
  config_path = "../vpc"
  mock_outputs = {
    database_subnet_group_name = "mock-db-subnets"
    default_security_group_id  = "sg-mock"
    vpc_cidr_block             = "10.60.0.0/16"
  }
}

inputs = {
  identifier = "${local.env.cluster_name}-pg"

  engine               = "postgres"
  engine_version       = "16"
  family               = "postgres16"
  major_engine_version = "16"
  instance_class       = "db.t4g.micro" # smallest; lab only

  allocated_storage = 20
  storage_type      = "gp3"

  db_name  = "backtests"
  username = "studio"
  # Master password managed in AWS Secrets Manager; retrieve with:
  #   aws secretsmanager get-secret-value --secret-id <arn from output>
  manage_master_user_password = true

  db_subnet_group_name   = dependency.vpc.outputs.database_subnet_group_name
  # TODO(tighten): create a dedicated SG allowing 5432 from the EKS node SG only.
  vpc_security_group_ids = [dependency.vpc.outputs.default_security_group_id]

  # Lab: make destroy painless
  skip_final_snapshot = true
  deletion_protection = false

  backup_retention_period = 0
  multi_az                = false
}
