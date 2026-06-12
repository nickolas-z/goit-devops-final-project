output "namespace" {
  description = "Namespace where ArgoCD is installed"
  value       = kubernetes_namespace_v1.argocd.metadata[0].name
}

output "release_name" {
  description = "ArgoCD Helm release name"
  value       = helm_release.argocd.name
}

output "server_service_name" {
  description = "ArgoCD server service name"
  value       = "${var.release_name}-server"
}

output "port_forward_command" {
  description = "Command to open the ArgoCD UI locally"
  value       = "kubectl -n ${kubernetes_namespace_v1.argocd.metadata[0].name} port-forward svc/${var.release_name}-server 8080:80"
}

output "initial_admin_password_command" {
  description = "Command to read the initial ArgoCD admin password"
  value       = "kubectl -n ${kubernetes_namespace_v1.argocd.metadata[0].name} get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
}
