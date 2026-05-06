variable "cluster_name" {
  type = string
}

variable "cluster_version" {
  type    = string
  default = "1.31"
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "fargate_namespaces" {
  description = "Namespaces that get a Fargate profile. Pods scheduled to anything else won't run."
  type        = list(string)
  default     = ["kube-system", "argocd", "default"]
}
