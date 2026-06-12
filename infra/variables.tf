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

variable "vpc_name" {
  description = "VPC name"
  type        = string
  default     = "goit-vpc"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "azs" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "private_subnets" {
  description = "Private subnet CIDRs"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnets" {
  description = "Public subnet CIDRs"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
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

variable "cpu_instance_type" {
  description = "Instance type for CPU node group"
  type        = string
  default     = "t3.small"
}

variable "gpu_instance_type" {
  description = "Instance type for GPU node group"
  type        = string
  default     = "t3.micro"
}

variable "desired_size" {
  description = "Desired number of nodes per group"
  type        = number
  # 3 ноди: на t3.small ліміт VPC CNI ~11 подів/ноду; повний стек (ArgoCD +
  # kube-prometheus-stack + Loki + сервіс + системні) не влазить у 2 ноди.
  default = 3
}

variable "min_size" {
  description = "Minimum number of nodes per group"
  type        = number
  default     = 1
}

variable "max_size" {
  description = "Maximum number of nodes per group"
  type        = number
  default     = 3
}

variable "argocd_namespace" {
  description = "Namespace where ArgoCD will be installed"
  type        = string
  default     = "infra-tools"
}

variable "argocd_chart_version" {
  description = "ArgoCD Helm chart version"
  type        = string
  default     = "9.5.13"
}
