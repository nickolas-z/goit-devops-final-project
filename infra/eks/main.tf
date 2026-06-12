data "terraform_remote_state" "vpc" {
  count   = var.use_remote_state ? 1 : 0
  backend = "local"
  config = {
    path = var.vpc_state_path
  }
}

locals {
  vpc_id          = var.use_remote_state ? data.terraform_remote_state.vpc[0].outputs.vpc_id : var.vpc_id
  private_subnets = var.use_remote_state ? data.terraform_remote_state.vpc[0].outputs.private_subnet_ids : var.private_subnet_ids
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version

  vpc_id     = local.vpc_id
  subnet_ids = local.private_subnets

  cluster_endpoint_public_access           = true
  enable_cluster_creator_admin_permissions = true

  eks_managed_node_groups = {
    cpu-nodes = {
      min_size     = var.min_size
      max_size     = var.max_size
      desired_size = var.desired_size

      instance_types = [var.cpu_instance_type]

      labels = {
        workload-type = "cpu"
        role          = "worker"
      }

      tags = {
        NodeGroup   = "cpu"
        Project     = "goit-devops"
        Environment = "dev"
      }
    }

    gpu-nodes = {
      min_size     = 0
      max_size     = var.max_size
      desired_size = 0

      instance_types = [var.gpu_instance_type]

      labels = {
        workload-type = "gpu"
        role          = "worker"
      }

      taints = {
        nvidia-gpu = {
          key    = "nvidia.com/gpu"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }

      tags = {
        NodeGroup   = "gpu"
        Project     = "goit-devops"
        Environment = "dev"
      }
    }
  }

  tags = {
    Project     = "goit-devops"
    Environment = "dev"
  }
}
