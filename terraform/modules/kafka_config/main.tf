# terraform/modules/kafka_config/main.tf

# This module handles Kafka configuration references since you already have MSK clusters
# It creates SSM parameters for Kafka bootstrap servers and creates topics

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "kafka_cluster_arn" {
  description = "ARN of the existing MSK cluster"
  type        = string
}

variable "bootstrap_servers" {
  description = "Comma-separated list of Kafka bootstrap servers"
  type        = string
}

variable "topics" {
  description = "List of Kafka topics to create"
  type        = list(object({
    name               = string
    partitions         = number
    replication_factor = number
  }))
  default = [
    {
      name               = "microservice-events"
      partitions         = 3
      replication_factor = 2
    }
  ]
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

# Store Kafka bootstrap servers in SSM Parameter Store
resource "aws_ssm_parameter" "kafka_bootstrap_servers" {
  name        = "/kafka/${var.environment}/bootstrap-servers"
  type        = "String"
  value       = var.bootstrap_servers
  description = "Kafka bootstrap servers for ${var.environment} environment"
  tags        = var.tags
}

# Store Kafka cluster ARN in SSM
resource "aws_ssm_parameter" "kafka_cluster_arn" {
  name        = "/kafka/${var.environment}/cluster-arn"
  type        = "String"
  value       = var.kafka_cluster_arn
  description = "Kafka cluster ARN for ${var.environment} environment"
  tags        = var.tags
}

# Create Kafka topics (requires AWS CLI or Kafka admin tools)
# Note: This is a null_resource that runs local commands to create topics
# You might want to replace this with your preferred topic management approach
resource "null_resource" "kafka_topics" {
  count = length(var.topics)

  provisioner "local-exec" {
    command = <<-EOT
      # This is a placeholder for topic creation
      # You can replace this with your preferred method (Terraform Kafka provider, custom scripts, etc.)
      echo "Creating topic: ${var.topics[count.index].name} in ${var.environment}"

      # Example using AWS CLI (uncomment and modify as needed):
      # aws kafka create-configuration \
      #   --name "${var.topics[count.index].name}-config" \
      #   --server-properties "num.partitions=${var.topics[count.index].partitions}"
    EOT
  }

  triggers = {
    topics_hash = md5(jsonencode(var.topics))
  }
}

# Output the SSM parameter names for reference
output "bootstrap_servers_ssm_key" {
  description = "SSM parameter key for Kafka bootstrap servers"
  value       = aws_ssm_parameter.kafka_bootstrap_servers.name
}

output "cluster_arn_ssm_key" {
  description = "SSM parameter key for Kafka cluster ARN"
  value       = aws_ssm_parameter.kafka_cluster_arn.name
}

output "topic_names" {
  description = "List of created topic names"
  value       = [for topic in var.topics : "${topic.name}-${var.environment}"]
}