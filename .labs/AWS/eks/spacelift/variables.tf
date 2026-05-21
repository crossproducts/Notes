variable "spacelift_space_id" {
  description = "Spacelift space ID"
  type        = string
  default     = "root"
}

variable "repository" {
  description = "GitHub repository (owner/repo)"
  type        = string
  default     = "crossproducts/Notes"
}

variable "branch" {
  description = "Git branch to track"
  type        = string
  default     = "main"
}

variable "project_root" {
  description = "Root path within the repo for the EKS lab"
  type        = string
  default     = ".labs/AWS/eks"
}

variable "terraform_version" {
  description = "Terraform version for Spacelift runners"
  type        = string
  default     = "1.3.6"
}

variable "aws_integration_id" {
  description = "Spacelift AWS integration ID for assuming IAM roles"
  type        = string
}
