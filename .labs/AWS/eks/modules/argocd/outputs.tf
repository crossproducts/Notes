output "argocd_namespace" {
  description = "Namespace where ArgoCD is installed"
  value       = helm_release.argocd.namespace
}

output "argocd_chart_version" {
  description = "ArgoCD Helm chart version deployed"
  value       = helm_release.argocd.version
}
