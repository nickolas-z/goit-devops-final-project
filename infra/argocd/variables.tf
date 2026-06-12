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
  description = "EKS cluster name. Used when use_remote_state is false."
  type        = string
  default     = "goit-eks-cluster"
}

variable "cluster_endpoint" {
  description = "EKS cluster endpoint. Used when use_remote_state is false."
  type        = string
  default     = ""
}

variable "cluster_certificate_authority_data" {
  description = "Base64-encoded EKS cluster CA data. Used when use_remote_state is false."
  type        = string
  default     = ""
  sensitive   = true
}

variable "eks_state_path" {
  description = "Path to the root or EKS Terraform state file for standalone ArgoCD deployment."
  type        = string
  default     = "../terraform.tfstate"
}

variable "use_remote_state" {
  description = "Read EKS outputs from terraform_remote_state. Set to false when deploying from root module."
  type        = bool
  default     = true
}

variable "namespace" {
  description = "Namespace where ArgoCD will be installed."
  type        = string
  default     = "infra-tools"
}

variable "release_name" {
  description = "Helm release name for ArgoCD."
  type        = string
  default     = "argocd"
}

variable "chart_repository" {
  description = "Helm repository URL for the ArgoCD chart."
  type        = string
  default     = "https://argoproj.github.io/argo-helm"
}

variable "chart_name" {
  description = "ArgoCD Helm chart name."
  type        = string
  default     = "argo-cd"
}

variable "chart_version" {
  description = "ArgoCD Helm chart version."
  type        = string
  default     = "9.5.13"
}

variable "values_file" {
  description = "Path to ArgoCD Helm values, relative to the argocd module."
  type        = string
  default     = "values/argocd-values.yaml"
}
