variable "region" {
  type    = string
  default = "us-east-1"
}

variable "state_bucket" {
  description = "Globally-unique S3 bucket name for Terraform remote state."
  type        = string
  default     = "crossproducts-tf-state-eks-lab"
}

variable "lock_table" {
  description = "DynamoDB table name for Terraform state locking."
  type        = string
  default     = "terraform-locks"
}
