module "vpc" {
  source = "./vpc"

  region          = var.region
  aws_profile     = var.aws_profile
  vpc_name        = var.vpc_name
  vpc_cidr        = var.vpc_cidr
  azs             = var.azs
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets
  cluster_name    = var.cluster_name
}

module "eks" {
  source = "./eks"

  region             = var.region
  aws_profile        = var.aws_profile
  cluster_name       = var.cluster_name
  kubernetes_version = var.kubernetes_version

  # VPC outputs passed directly from root — remote state not needed
  use_remote_state   = false
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids

  cpu_instance_type = var.cpu_instance_type
  gpu_instance_type = var.gpu_instance_type
  desired_size      = var.desired_size
  min_size          = var.min_size
  max_size          = var.max_size
}

# Wait for EKS access entries to propagate and nodes to be Ready before deploying ArgoCD.
# enable_cluster_creator_admin_permissions creates an access entry asynchronously — without
# this wait the Kubernetes/Helm providers get a 403 when they try to create the namespace.
resource "null_resource" "wait_for_eks" {
  depends_on = [module.eks]

  provisioner "local-exec" {
    command = <<-EOT
      aws eks --region ${var.region} update-kubeconfig \
        --name ${var.cluster_name} \
        --profile ${var.aws_profile}
      kubectl wait --for=condition=Ready node --all --timeout=300s
    EOT
  }
}

# Data sources for root-level kubernetes/helm provider configuration.
# depends_on ensures these are refreshed only after nodes are ready.
data "aws_eks_cluster" "this" {
  name       = module.eks.cluster_name
  depends_on = [null_resource.wait_for_eks]
}

data "aws_eks_cluster_auth" "this" {
  name       = module.eks.cluster_name
  depends_on = [null_resource.wait_for_eks]
}

module "argocd" {
  source = "./argocd"

  region      = var.region
  aws_profile = var.aws_profile

  # Use direct EKS outputs when deploying the full stack from the root module.
  use_remote_state                   = false
  cluster_name                       = module.eks.cluster_name
  cluster_endpoint                   = module.eks.cluster_endpoint
  cluster_certificate_authority_data = module.eks.cluster_certificate_authority_data

  namespace     = var.argocd_namespace
  chart_version = var.argocd_chart_version

  providers = {
    aws        = aws
    kubernetes = kubernetes
    helm       = helm
  }

  depends_on = [null_resource.wait_for_eks]
}
