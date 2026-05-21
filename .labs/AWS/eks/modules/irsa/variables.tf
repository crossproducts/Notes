variable "role_name" {
  description = "IAM role name"
  type        = string
}

variable "oidc_provider_arn" {
  description = "EKS OIDC provider ARN"
  type        = string
}

variable "oidc_provider_url" {
  description = "EKS OIDC provider URL (including https://)"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace for the service account"
  type        = string
}

variable "service_account_name" {
  description = "Kubernetes service account name"
  type        = string
}

variable "policy_arns" {
  description = "List of IAM managed policy ARNs to attach"
  type        = list(string)
  default     = []
}

variable "inline_policy" {
  description = "JSON inline policy document (optional)"
  type        = string
  default     = ""
}
