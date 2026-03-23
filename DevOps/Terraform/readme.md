# Terraform

> [!NOTE]   
> **Status**: Done
---

> Terraform: Infrastructure as Code (IaC) tool - build, change, and manage infrastructure using code.

<table>
<tr>
    <th colspan="2" ><h2 style="margin: 0;">File Structure</h2></th>
</tr>
<tr>
<td style="vertical-align: top;">
<details open><summary>Terraform (standalone)</summary>

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
</td>

<td style="vertical-align: top;">
<details open><summary>Terragrunt (multi-env)</summary>

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
</td>
</tr>
</table>

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