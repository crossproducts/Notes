variable "cluster_name" {
  type = string
}

variable "cluster_endpoint" {
  type = string
}

variable "cluster_ca_certificate" {
  description = "Base64-encoded cluster CA cert (as returned by the EKS module)."
  type        = string
}

variable "oidc_provider_arn" {
  description = "Reserved for future IRSA roles wired into ArgoCD components."
  type        = string
  default     = ""
}

variable "argocd_chart_version" {
  type    = string
  default = "7.7.5"
}

variable "repo_url" {
  type    = string
  default = "https://github.com/crossproducts/Notes"
}

variable "target_revision" {
  type    = string
  default = "main"
}

variable "apps_path" {
  description = "Repo path the root-app syncs from (an app-of-apps directory)."
  type        = string
  default     = "DevOps/Labs/eks-terraform/apps"
}
