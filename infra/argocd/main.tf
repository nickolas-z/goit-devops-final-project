resource "kubernetes_namespace_v1" "argocd" {
  metadata {
    name = var.namespace

    labels = {
      name        = var.namespace
      managed-by  = "terraform"
      application = "argocd"
    }
  }
}

resource "helm_release" "argocd" {
  name       = var.release_name
  repository = var.chart_repository
  chart      = var.chart_name
  version    = var.chart_version
  namespace  = kubernetes_namespace_v1.argocd.metadata[0].name

  create_namespace  = false
  dependency_update = true
  wait              = true
  timeout           = 600

  # Keep chart overrides in a separate file, as required by the task.
  values = [
    file("${path.module}/${var.values_file}")
  ]
}
