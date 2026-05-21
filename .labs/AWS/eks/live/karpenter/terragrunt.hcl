include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/karpenter"
}

dependency "eks" {
  config_path = "../eks"
}

generate "k8s_provider" {
  path      = "k8s-provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<-EOF
    data "aws_eks_cluster_auth" "cluster" {
      name = "${dependency.eks.outputs.cluster_name}"
    }

    provider "helm" {
      kubernetes {
        host                   = "${dependency.eks.outputs.cluster_endpoint}"
        cluster_ca_certificate = base64decode("${dependency.eks.outputs.cluster_ca_certificate}")
        token                  = data.aws_eks_cluster_auth.cluster.token
      }
    }

    provider "kubectl" {
      host                   = "${dependency.eks.outputs.cluster_endpoint}"
      cluster_ca_certificate = base64decode("${dependency.eks.outputs.cluster_ca_certificate}")
      token                  = data.aws_eks_cluster_auth.cluster.token
      load_config_file       = false
    }
  EOF
}

inputs = {
  cluster_endpoint  = dependency.eks.outputs.cluster_endpoint
  oidc_provider_arn = dependency.eks.outputs.oidc_provider_arn
}
