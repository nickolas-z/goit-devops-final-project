output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64-encoded certificate authority data"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "cluster_oidc_issuer_url" {
  description = "OIDC issuer URL"
  value       = module.eks.cluster_oidc_issuer_url
}

output "kubeconfig_command" {
  description = "Command to update kubeconfig"
  value       = "aws eks --region ${var.region} update-kubeconfig --name ${module.eks.cluster_name} --profile ${var.aws_profile}"
}
