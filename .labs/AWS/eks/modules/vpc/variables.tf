variable "vpc_name" {
  description = "VPC name"
  type        = string
  default     = "eks-prod-vpc"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "cluster_name" {
  description = "EKS cluster name (used for subnet discovery tags)"
  type        = string
}

variable "azs_count" {
  description = "Number of availability zones"
  type        = number
  default     = 3
}
