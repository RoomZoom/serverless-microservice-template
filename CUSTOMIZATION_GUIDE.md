# Microservice Customization Guide

This guide explains how to use the `create_custom_service.py` script to create fully customized microservices from the serverless-microservice-template.

## Overview

The customization script allows you to create new microservices with:
- Custom service names
- Custom Lambda handler paths
- Custom DynamoDB table names
- Custom SQS queue names
- Custom Kafka topic names
- Custom API Gateway names

## Usage

### Quick Start

```bash
make create-custom-service
```

### Manual Execution

```bash
python3 create_custom_service.py
```

## Customization Options

### Service Name
- **Purpose**: Base identifier for your microservice
- **Format**: Lowercase letters, numbers, and hyphens only
- **Example**: `user-management`, `order-processing`, `notification-service`
- **Impact**: Used as prefix for all AWS resources

### Lambda Handler
- **Purpose**: Entry point for your Lambda function
- **Default**: `main.handler`
- **Format**: `{module}.{function}`
- **Examples**: 
  - `main.handler` (default)
  - `user.handler` (custom module)
  - `handlers.process_request` (nested module)

### DynamoDB Table Name
- **Purpose**: Name of your primary DynamoDB table
- **Default**: `{service-name}-table`
- **Examples**:
  - `users` (simple name)
  - `user-profiles` (descriptive name)
  - `user-management-data` (prefixed name)

### SQS Queue Name
- **Purpose**: Name of your SQS queue for async processing
- **Default**: `{service-name}-queue`
- **Examples**:
  - `user-processing` (descriptive)
  - `user-events` (event-based)
  - `user-management-tasks` (task-based)

### Kafka Topics
- **Main Topic**: Primary event stream
- **DLQ Topic**: Dead letter queue for failed messages
- **Defaults**: `{service-name}-events`, `{service-name}-dlq`
- **Examples**:
  - Main: `user-events`, DLQ: `user-dlq`
  - Main: `order-updates`, DLQ: `order-failures`

### API Gateway Name
- **Purpose**: Name of your API Gateway
- **Default**: `{service-name}-api`
- **Examples**:
  - `user-api` (simple)
  - `user-management-api` (descriptive)

## What Gets Customized

The script processes and updates the following:

### Source Code Files
- `src/main.py` - Lambda handler and configuration
- `src/api/api_handler.py` - FastAPI application
- All Python files in `src/` directory

### Terraform Configuration
- `terraform/dev/main.tf` - Development environment
- `terraform/staging/main.tf` - Staging environment  
- `terraform/prod/main.tf` - Production environment
- All module configurations

### Configuration Files
- `Makefile` - Build and deployment scripts
- `README.md` - Documentation
- `.github/workflows/` - CI/CD pipelines
- Environment configuration examples

### Replacement Patterns

The script performs the following replacements:

| Original Pattern | Replacement | Context |
|------------------|-------------|---------|
| `microservice-template` | `{service-name}` | Service identifiers |
| `main.handler` | `{lambda-handler}` | Lambda configuration |
| `my-table` | `{dynamodb-table}` | DynamoDB references |
| `my-queue` | `{sqs-queue}` | SQS references |
| `microservice-events` | `{kafka-topic}` | Kafka main topic |
| `microservice-dlq` | `{kafka-dlq}` | Kafka DLQ topic |
| `my-microservice` | `{service-name}` | Generic service refs |

## Advanced Usage

### Environment-Specific Names

The script maintains environment suffixes for resources:
- Tables: `{table-name}-{environment}` (e.g., `users-dev`, `users-prod`)
- Queues: `{queue-name}-{environment}` (e.g., `user-processing-dev`)
- Topics: `{topic-name}-{environment}` (e.g., `user-events-dev`)

### Custom Target Directory

You can specify where to create the new service:

```bash
# When prompted for target directory:
Target directory [default: ../user-management]: /path/to/my/services/user-management
```

### Validation Rules

- **Service names**: Must contain only lowercase letters, numbers, and hyphens
- **Handler paths**: Must follow Python module.function format
- **Resource names**: Should follow AWS naming conventions

## Post-Creation Steps

After creating your customized service:

1. **Navigate to the new service**:
   ```bash
   cd ../your-service-name
   ```

2. **Initialize the project**:
   ```bash
   make init
   ```

3. **Configure MSK cluster details** in `terraform/dev/main.tf`:
   ```hcl
   variable "kafka_cluster_arn" {
     default = "arn:aws:kafka:us-east-1:123456789012:cluster/your-cluster-dev/uuid"
   }
   
   variable "kafka_bootstrap_servers" {
     default = "broker1.dev.cluster.kafka.us-east-1.amazonaws.com:9092"
   }
   ```

4. **Deploy to development**:
   ```bash
   make deploy-dev
   ```

5. **Run tests**:
   ```bash
   make test-all
   ```

## Troubleshooting

### Common Issues

**Script fails with permission error**:
```bash
chmod +x create_custom_service.py
```

**Invalid service name**:
- Use only lowercase letters, numbers, and hyphens
- No spaces or special characters
- Examples: ✅ `user-service`, ❌ `User Service`, ❌ `user_service`

**Target directory exists**:
- The script will prompt to overwrite
- Choose 'y' to proceed or 'n' to cancel

**Missing dependencies**:
- Ensure Python 3.6+ is installed
- No additional dependencies required

### Verification

After creation, verify the customization worked:

```bash
# Check service name in Makefile
grep "SERVICE_NAME" Makefile

# Check Lambda handler in Terraform
grep "handler" terraform/dev/main.tf

# Check resource names in source code
grep -r "your-custom-names" src/
```

## Examples

### E-commerce Order Service

```
Service name: order-processing
Lambda handler: orders.process_order
DynamoDB table: orders
SQS queue: order-fulfillment
Kafka topic: order-events
Kafka DLQ: order-failures
API Gateway: orders-api
```

### User Authentication Service

```
Service name: user-auth
Lambda handler: auth.authenticate
DynamoDB table: user-credentials
SQS queue: auth-events
Kafka topic: auth-events
Kafka DLQ: auth-failures
API Gateway: auth-api
```

### Notification Service

```
Service name: notifications
Lambda handler: notify.send_notification
DynamoDB table: notification-templates
SQS queue: notification-queue
Kafka topic: notification-events
Kafka DLQ: notification-dlq
API Gateway: notifications-api
```

## Contributing

To improve the customization script:

1. Edit `create_custom_service.py`
2. Test with various input combinations
3. Update this documentation
4. Submit a pull request

## Support

For issues with the customization script:
1. Check this guide for common solutions
2. Verify your inputs meet the validation rules
3. Create an issue with your specific use case
