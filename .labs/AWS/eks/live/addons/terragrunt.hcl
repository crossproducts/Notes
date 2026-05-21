include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/addons"
}

dependency "eks" {
  config_path = "../eks"
}

inputs = {
  oidc_provider_arn = dependency.eks.outputs.oidc_provider_arn
  oidc_provider_url = dependency.eks.outputs.oidc_provider_url
}
