# Terraform & Terragrunt — AWS

> Concise reference for provisioning AWS infrastructure with Terraform and Terragrunt.

---

## Table of Contents
- [File Structure](#file-structure)
- [Core Concepts](#core-concepts)
- [Terraform Commands](#terraform-commands)
- [Terragrunt](#terragrunt)
- [AWS Modules](#aws-modules)

---

## File Structure

<details>
<summary>Terraform (standalone)</summary>

```
infra/
├── main.tf          # Root resources
├── variables.tf     # Input variables
├── outputs.tf       # Output values
├── providers.tf     # Provider config (AWS)
├── terraform.tfvars # Variable values
└── modules/
    ├── vpc/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── ec2/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── rds/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

</details>

<details>
<summary>Terragrunt (multi-env)</summary>

```
infra/
├── terragrunt.hcl          # Root config (remote state, provider)
├── modules/                # Reusable Terraform modules
│   ├── vpc/
│   ├── ec2/
│   └── rds/
└── live/
    ├── dev/
    │   ├── vpc/
    │   │   └── terragrunt.hcl
    │   ├── ec2/
    │   │   └── terragrunt.hcl
    │   └── rds/
    │       └── terragrunt.hcl
    └── prod/
        ├── vpc/
        │   └── terragrunt.hcl
        ├── ec2/
        │   └── terragrunt.hcl
        └── rds/
            └── terragrunt.hcl
```

</details>

---

## Core Concepts

<details>
<summary>Providers & Backend</summary>

```hcl
# providers.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "my-tf-state"
    key    = "global/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}
```

</details>

<details>
<summary>Variables & Outputs</summary>

```hcl
# variables.tf
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

# outputs.tf
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}
```

</details>

---

## Terraform Commands

<details>
<summary>Common Workflow</summary>

| Command | Description |
|---|---|
| `terraform init` | Initialize working directory |
| `terraform plan` | Preview changes |
| `terraform apply` | Apply changes |
| `terraform destroy` | Destroy infrastructure |
| `terraform fmt` | Format code |
| `terraform validate` | Validate config |
| `terraform output` | Show outputs |
| `terraform state list` | List managed resources |

</details>

<details>
<summary>Targeting & Importing</summary>

```bash
# Target a specific resource
terraform apply -target=module.vpc

# Import existing resource
terraform import aws_instance.web i-1234567890abcdef0

# Plan with var file
terraform plan -var-file="prod.tfvars"
```

</details>

---

## Terragrunt

<details>
<summary>Root terragrunt.hcl</summary>

```hcl
# infra/terragrunt.hcl
locals {
  region      = "us-east-1"
  environment = path_relative_to_include()
}

remote_state {
  backend = "s3"
  config = {
    bucket         = "my-tf-state"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = local.region
    encrypt        = true
    dynamodb_table = "tf-lock"
  }
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite"
  contents  = <<EOF
provider "aws" {
  region = "${local.region}"
}
EOF
}
```

</details>

<details>
<summary>Child terragrunt.hcl (per-module)</summary>

```hcl
# live/dev/vpc/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../../modules/vpc"
}

inputs = {
  environment = "dev"
  vpc_cidr    = "10.0.0.0/16"
}
```

</details>

<details>
<summary>Terragrunt Commands</summary>

| Command | Description |
|---|---|
| `terragrunt init` | Init with remote state auto-config |
| `terragrunt plan` | Plan single module |
| `terragrunt apply` | Apply single module |
| `terragrunt run-all plan` | Plan all modules |
| `terragrunt run-all apply` | Apply all modules in dependency order |
| `terragrunt run-all destroy` | Destroy all modules |

</details>

---

## AWS Modules

<details>
<summary>VPC Module</summary>

```hcl
# modules/vpc/main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.environment}-vpc"
    Environment = var.environment
  }
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnets)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.environment}-public-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.environment}-igw" }
}
```

```hcl
# modules/vpc/variables.tf
variable "environment" { type = string }
variable "vpc_cidr"    { type = string }
variable "public_subnets" {
  type    = list(string)
  default = ["10.0.1.0/24", "10.0.2.0/24"]
}
variable "azs" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}
```

```hcl
# modules/vpc/outputs.tf
output "vpc_id"         { value = aws_vpc.main.id }
output "public_subnets" { value = aws_subnet.public[*].id }
```

</details>

<details>
<summary>EC2 Module</summary>

```hcl
# modules/ec2/main.tf
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.web.id]
  key_name               = var.key_name

  tags = {
    Name        = "${var.environment}-web"
    Environment = var.environment
  }
}

resource "aws_security_group" "web" {
  name   = "${var.environment}-web-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

```hcl
# modules/ec2/variables.tf
variable "environment"   { type = string }
variable "instance_type" { type = string; default = "t3.micro" }
variable "subnet_id"     { type = string }
variable "vpc_id"        { type = string }
variable "key_name"      { type = string; default = "" }
```

```hcl
# modules/ec2/outputs.tf
output "instance_id"       { value = aws_instance.web.id }
output "public_ip"         { value = aws_instance.web.public_ip }
output "security_group_id" { value = aws_security_group.web.id }
```

</details>

<details>
<summary>RDS Module</summary>

```hcl
# modules/rds/main.tf
resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-db-subnet"
  subnet_ids = var.subnet_ids
}

resource "aws_db_instance" "main" {
  identifier             = "${var.environment}-db"
  engine                 = "postgres"
  engine_version         = "15"
  instance_class         = var.instance_class
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  allocated_storage      = var.storage_gb
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot    = true
  multi_az               = var.multi_az

  tags = { Environment = var.environment }
}

resource "aws_security_group" "rds" {
  name   = "${var.environment}-rds-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.app_cidr]
  }
}
```

```hcl
# modules/rds/variables.tf
variable "environment"    { type = string }
variable "vpc_id"         { type = string }
variable "subnet_ids"     { type = list(string) }
variable "instance_class" { type = string; default = "db.t3.micro" }
variable "db_name"        { type = string }
variable "db_username"    { type = string }
variable "db_password"    { type = string; sensitive = true }
variable "storage_gb"     { type = number; default = 20 }
variable "multi_az"       { type = bool; default = false }
variable "app_cidr"       { type = string }
```

```hcl
# modules/rds/outputs.tf
output "endpoint" { value = aws_db_instance.main.endpoint }
output "db_name"  { value = aws_db_instance.main.db_name }
```

</details>

<details>
<summary>S3 + IAM Module</summary>

```hcl
# modules/s3/main.tf
resource "aws_s3_bucket" "main" {
  bucket = "${var.environment}-${var.bucket_name}"
  tags   = { Environment = var.environment }
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_iam_role" "app" {
  name = "${var.environment}-app-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "s3_access" {
  role = aws_iam_role.app.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
      Resource = "${aws_s3_bucket.main.arn}/*"
    }]
  })
}
```

```hcl
# modules/s3/variables.tf
variable "environment" { type = string }
variable "bucket_name" { type = string }
```

```hcl
# modules/s3/outputs.tf
output "bucket_id"  { value = aws_s3_bucket.main.id }
output "bucket_arn" { value = aws_s3_bucket.main.arn }
output "role_arn"   { value = aws_iam_role.app.arn }
```

</details>