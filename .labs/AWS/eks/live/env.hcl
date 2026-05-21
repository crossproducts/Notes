locals {
  region       = "us-east-1"
  cluster_name = "eks-prod"
  state_bucket = "crossproducts-tf-state-eks-prod"
  lock_table   = "terraform-locks-eks-prod"
}
