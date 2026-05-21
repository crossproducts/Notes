variable "argocd_chart_version" {
  description = "ArgoCD Helm chart version"
  type        = string
  default     = "7.7.5"
}

variable "repo_url" {
  description = "Git repository URL for ArgoCD apps"
  type        = string
  default     = "https://github.com/crossproducts/Notes"
}

variable "target_revision" {
  description = "Git branch/tag/commit"
  type        = string
  default     = "main"
}

variable "apps_path" {
  description = "Path in the repo to the ArgoCD Application manifests"
  type        = string
  default     = ".labs/AWS/eks/apps"
}
