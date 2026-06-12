variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS CLI profile name"
  type        = string
  default     = "devops"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "goit-eks-cluster"
}

variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.33"
}

variable "vpc_state_path" {
  description = "Path to VPC Terraform state file (used for standalone deployment)"
  type        = string
  default     = "../vpc/terraform.tfstate"
}

variable "use_remote_state" {
  description = "Read VPC outputs from terraform_remote_state. Set to false when deploying from root module."
  type        = bool
  default     = true
}

# These variables override remote_state when deploying from root module
variable "vpc_id" {
  description = "VPC ID. If empty, reads from vpc remote state"
  type        = string
  default     = ""
}

variable "private_subnet_ids" {
  description = "Private subnet IDs. If empty, reads from vpc remote state"
  type        = list(string)
  default     = []
}

variable "cpu_instance_type" {
  description = "Instance type for CPU node group"
  type        = string
  default     = "t3.small"
}

variable "gpu_instance_type" {
  description = "Instance type for GPU node group (t3.micro for Free Tier demo)"
  type        = string
  default     = "t3.micro"
}

variable "desired_size" {
  description = "Desired number of nodes per group"
  type        = number
  default     = 1
}

variable "min_size" {
  description = "Minimum number of nodes per group"
  type        = number
  default     = 1
}

variable "max_size" {
  description = "Maximum number of nodes per group"
  type        = number
  default     = 2
}
