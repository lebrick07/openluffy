terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    bucket         = "openluffy-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "openluffy-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = "production"
      Project     = "openluffy"
      ManagedBy   = "terraform"
    }
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "openluffy-prod"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# Networking
module "networking" {
  source = "../../modules/networking"

  cluster_name       = var.cluster_name
  availability_zones = var.availability_zones
  vpc_cidr          = "10.0.0.0/16"
}

# EKS Cluster
module "eks" {
  source = "../../modules/eks"

  cluster_name    = var.cluster_name
  cluster_version = "1.31"
  vpc_id          = module.networking.vpc_id
  subnet_ids      = concat(
    module.networking.public_subnet_ids,
    module.networking.private_subnet_ids
  )

  node_groups = {
    general = {
      desired_size   = 2
      min_size       = 1
      max_size       = 4
      instance_types = ["t3.medium"]
    }
    compute = {
      desired_size   = 1
      min_size       = 0
      max_size       = 10
      instance_types = ["t3.large"]
    }
  }
}

# Database
module "database" {
  source = "../../modules/database"

  cluster_name      = var.cluster_name
  vpc_id            = module.networking.vpc_id
  subnet_ids        = module.networking.private_subnet_ids
  instance_class    = "db.t4g.small"
  allocated_storage = 50
}

# IAM
module "iam" {
  source = "../../modules/iam"

  cluster_name      = var.cluster_name
  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_provider_url = module.eks.oidc_provider_url
  github_repo       = "lebrick07/openluffy"
}

# Outputs
output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --name ${var.cluster_name} --region ${var.aws_region}"
}

output "github_actions_role_arn" {
  description = "ARN for GitHub Actions role"
  value       = module.iam.github_actions_role_arn
}

output "openluffy_service_role_arn" {
  description = "ARN for Luffy service role"
  value       = module.iam.openluffy_service_role_arn
}

output "database_endpoint" {
  description = "RDS endpoint"
  value       = module.database.db_endpoint
}

output "database_secret_arn" {
  description = "Secrets Manager ARN for DB credentials"
  value       = module.database.db_secret_arn
}
