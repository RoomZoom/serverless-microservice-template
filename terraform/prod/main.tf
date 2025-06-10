# terraform/prod/main.tf

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "service_name" {
  description = "Name of the microservice"
  type        = string
  default     = "microservice-template"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

# Replace these with your actual MSK cluster details
variable "kafka_cluster_arn" {
  description = "ARN of your existing MSK cluster for prod"
  type        = string
  # Example: "arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster-prod/uuid"
}

variable "kafka_bootstrap_servers" {
  description = "Bootstrap servers for your MSK cluster"
  type        = string
  # Example: "broker1.prod.cluster.kafka.us-east-1.amazonaws.com:9092,broker2.prod.cluster.kafka.us-east-1.amazonaws.com:9092"
}

# Local values
locals {
  common_tags = {
    Environment = var.environment
    Service     = var.service_name
    ManagedBy   = "terraform"
  }

  resource_prefix = "${var.service_name}-${var.environment}"
}

# DynamoDB Table
module "dynamodb_table" {
  source        = "../modules/dynamodb_table"
  name          = "${local.resource_prefix}-table"
  hash_key      = "id"
  hash_key_type = "S"

  tags = local.common_tags
}

# SQS Queue
module "sqs_queue" {
  source = "../modules/sqs_queue"
  name   = "${local.resource_prefix}-queue"

  tags = local.common_tags
}

# Kafka Configuration
module "kafka_config" {
  source = "../modules/kafka_config"

  environment         = var.environment
  kafka_cluster_arn   = var.kafka_cluster_arn
  bootstrap_servers   = var.kafka_bootstrap_servers

  topics = [
    {
      name               = "microservice-events"
      partitions         = 3
      replication_factor = 2
    },
    {
      name               = "microservice-dlq"
      partitions         = 1
      replication_factor = 2
    }
  ]

  tags = local.common_tags
}

# Secrets Manager for service secrets
module "secrets_manager" {
  source      = "../modules/secrets_manager"
  name        = "/${var.service_name}/${var.environment}/secret"
  value       = "super-secret-prod-key"
  description = "Secret for ${var.service_name} ${var.environment} service"
  tags        = local.common_tags
}

# IAM Role for Lambda
module "lambda_iam_role" {
  source = "../modules/iam_roles"

  role_name     = "${local.resource_prefix}-lambda-role"
  service_name  = var.service_name
  environment   = var.environment

  # DynamoDB permissions
  dynamodb_table_arn = module.dynamodb_table.table_arn

  # SQS permissions
  sqs_queue_arn = module.sqs_queue.queue_arn

  # Kafka permissions
  kafka_cluster_arn = var.kafka_cluster_arn

  tags = local.common_tags
}

# Lambda Function
module "lambda_function" {
  source = "../modules/lambda_function"

  function_name = "${local.resource_prefix}-function"
  handler       = "main.handler"
  runtime       = "python3.12"
  role_arn      = module.lambda_iam_role.role_arn
  filename      = "../../deployment.zip"  # Created by build process

  environment_variables = {
    ENVIRONMENT          = var.environment
    SERVICE_NAME         = var.service_name
    DYNAMODB_TABLE_NAME  = module.dynamodb_table.table_name
    SQS_QUEUE_URL        = module.sqs_queue.queue_url
    KAFKA_TOPIC          = "microservice-events-${var.environment}"
  }

  tags = local.common_tags
}

# API Gateway (optional - for HTTP API)
module "api_gateway" {
  source = "../modules/api_gateway"

  name         = "${local.resource_prefix}-api"
  lambda_arn   = module.lambda_function.function_arn

  tags = local.common_tags
}

# OpenAPI Documentation Hosting
module "openapi_docs" {
  source = "../modules/openapi_docs"

  bucket_name = "${local.resource_prefix}-openapi-docs"

  tags = local.common_tags
}

# Outputs
output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = module.dynamodb_table.table_name
}

output "sqs_queue_url" {
  description = "SQS queue URL"
  value       = module.sqs_queue.queue_url
}

output "kafka_bootstrap_servers_ssm" {
  description = "SSM parameter for Kafka bootstrap servers"
  value       = module.kafka_config.bootstrap_servers_ssm_key
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = module.lambda_function.function_name
}

output "openapi_docs_url" {
  description = "OpenAPI documentation URL"
  value       = module.openapi_docs.openapi_docs_url
}