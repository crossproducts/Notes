output "irsa_role_arn" {
  description = "Karpenter controller IRSA role ARN"
  value       = module.karpenter.irsa_arn
}

output "node_iam_role_name" {
  description = "Karpenter node IAM role name"
  value       = module.karpenter.node_iam_role_name
}

output "instance_profile_name" {
  description = "Karpenter instance profile name"
  value       = module.karpenter.instance_profile_name
}

output "queue_name" {
  description = "Karpenter SQS interruption queue name"
  value       = module.karpenter.queue_name
}
