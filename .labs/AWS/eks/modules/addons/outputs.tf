output "ebs_csi_role_arn" {
  description = "IRSA role ARN for EBS CSI driver"
  value       = module.irsa_ebs_csi.role_arn
}

output "efs_csi_role_arn" {
  description = "IRSA role ARN for EFS CSI driver"
  value       = module.irsa_efs_csi.role_arn
}

output "alb_controller_role_arn" {
  description = "IRSA role ARN for ALB Controller"
  value       = module.irsa_alb_controller.role_arn
}

output "external_dns_role_arn" {
  description = "IRSA role ARN for ExternalDNS"
  value       = module.irsa_external_dns.role_arn
}

output "adot_role_arn" {
  description = "IRSA role ARN for ADOT Collector"
  value       = module.irsa_adot.role_arn
}
