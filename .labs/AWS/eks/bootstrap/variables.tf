variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "state_bucket" {
  description = "S3 bucket name for Terraform state"
  type        = string
  default     = "crossproducts-tf-state-eks-prod"
}

variable "lock_table" {
  description = "DynamoDB table name for state locking"
  type        = string
  default     = "terraform-locks-eks-prod"
}
