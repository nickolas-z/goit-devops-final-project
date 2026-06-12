data "terraform_remote_state" "eks" {
  count   = var.use_remote_state ? 1 : 0
  backend = "local"
  config = {
    path = var.eks_state_path
  }
}

locals {
  # Allows this module to run both from the root module and standalone after EKS exists.
  cluster_name                       = var.use_remote_state ? data.terraform_remote_state.eks[0].outputs.cluster_name : var.cluster_name
  cluster_endpoint                   = var.use_remote_state ? data.terraform_remote_state.eks[0].outputs.cluster_endpoint : var.cluster_endpoint
  cluster_certificate_authority_data = var.use_remote_state ? data.terraform_remote_state.eks[0].outputs.cluster_certificate_authority_data : var.cluster_certificate_authority_data
}
