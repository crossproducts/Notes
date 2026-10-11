terraform {
  required_version = ">= 1.3"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = var.vpc_name
  }
}

resource "aws_subnet" "this" {
  for_each = {
    "us-east-1a" = cidrsubnet(var.vpc_cidr, 4, 0)
    "us-east-1b" = cidrsubnet(var.vpc_cidr, 4, 1)
  }

  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = each.key

  tags = {
    Name = "${var.vpc_name}-${each.key}"
    "kubernetes.io/role/internal-elb" = "1"
  }
}
