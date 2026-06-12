output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64-encoded EKS cluster CA data (required by argocd/ standalone mode)"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "kubeconfig_command" {
  description = "Run this after apply to configure kubectl"
  value       = module.eks.kubeconfig_command
}

output "argocd_namespace" {
  description = "Namespace where ArgoCD is installed"
  value       = module.argocd.namespace
}

output "argocd_port_forward_command" {
  description = "Command to open the ArgoCD UI locally"
  value       = module.argocd.port_forward_command
}

output "argocd_initial_admin_password_command" {
  description = "Command to read the initial ArgoCD admin password"
  value       = module.argocd.initial_admin_password_command
}
