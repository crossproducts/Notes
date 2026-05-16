include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/argocd"
}

dependency "eks" {
  config_path = "../eks"
}

inputs = {
  cluster_endpoint       = dependency.eks.outputs.cluster_endpoint
  cluster_ca_certificate = dependency.eks.outputs.cluster_ca_certificate
  oidc_provider_arn      = dependency.eks.outputs.oidc_provider_arn

  repo_url        = "https://github.com/crossproducts/Notes"
  target_revision = "main"
  apps_path       = "DevOps/Labs/eks-terraform/apps"
}
