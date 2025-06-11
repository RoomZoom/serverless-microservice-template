# Serverless Python Microservice Template

A production-ready, reusable serverless microservice template built with Python, AWS Lambda, DynamoDB, SQS, and Kafka (MSK). This template follows best practices for microservice architecture, including event-driven patterns, proper error handling, comprehensive testing, and multi-environment support.

## 🚀 Features

- ✅ **Multi-environment support** (dev/staging/prod)
- ✅ **Event-driven architecture** with Kafka (MSK) integration
- ✅ **Modular infrastructure** using Terraform modules
- ✅ **Adapter-based architecture** (DynamoDB, SQS, Kafka)
- ✅ **AWS Secrets support** using SSM Parameter Store
- ✅ **Comprehensive test suite** with pytest and moto
- ✅ **Structured logging** with correlation IDs
- ✅ **API documentation** with OpenAPI/FastAPI
- ✅ **CI/CD ready** with GitHub Actions
- ✅ **Code quality tools** (formatting, linting, type checking)
- ✅ **Developer workflow** with comprehensive Makefile

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │────│  Lambda Function │────│    DynamoDB     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌────────┴────────┐
                       │                 │
                ┌─────────────┐    ┌─────────────┐
                │     SQS     │    │  Kafka/MSK  │
                └─────────────┘    └─────────────┘
```

## 📋 Prerequisites

- Python 3.12+
- AWS CLI configured
- Terraform >= 1.0
- Node.js (for OpenAPI documentation)
- Existing MSK (Kafka) clusters set up
- Docker (optional, for local development)

## 🛠️ Quick Start

1. **Initialize the project:**
   ```bash
   make init
   ```

2. **Install development dependencies:**
   ```bash
   make install-dev-deps
   ```

3. **Configure your MSK cluster details in Terraform:**
   ```bash
   # Edit terraform/dev/main.tf
   variable "kafka_cluster_arn" {
     default = "arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster-dev/uuid"
   }

   variable "kafka_bootstrap_servers" {
     default = "broker1.dev.cluster.kafka.us-east-1.amazonaws.com:9092,broker2.dev.cluster.kafka.us-east-1.amazonaws.com:9092"
   }
   ```

4. **Deploy infrastructure:**
   ```bash
   make deploy-dev
   ```

5. **Run tests:**
   ```bash
   make test-all
   ```

6. **Start local development:**
   ```bash
   make run-local
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
SERVICE_NAME=my-microservice
ENVIRONMENT=dev
AWS_REGION=us-east-1
LOG_LEVEL=INFO
DYNAMODB_TABLE_NAME=my-microservice-dev-table
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/.../my-queue-dev
KAFKA_TOPIC=microservice-events-dev
```

### MSK Configuration

Your MSK cluster details are stored in SSM Parameter Store:
- `/kafka/{environment}/bootstrap-servers`
- `/kafka/{environment}/cluster-arn`

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### Create Item
```bash
POST /create
Content-Type: application/json

{
  "id": "item-123",
  "name": "Sample Item",
  "description": "A sample item for testing"
}
```

### Get Item
```bash
GET /item/{item_id}
```

### Get Recent Events (Debug)
```bash
GET /events?limit=10
```

## 🎯 Event Flow

When an item is created, the following events occur:

1. **API Request** → FastAPI validates the request
2. **DynamoDB Storage** → Item is stored in DynamoDB
3. **SQS Message** → Async processing message is sent
4. **Kafka Event** → Structured event is published to Kafka

### Event Schema

All Kafka events follow this structure:

```json
{
  "event_type": "item.created",
  "source_service": "my-microservice",
  "entity_id": "item-123",
  "timestamp": "2025-06-10T10:30:00Z",
  "payload": {
    "id": "item-123",
    "name": "Sample Item",
    "description": "A sample item"
  },
  "version": "1.0",
  "correlation_id": "uuid-correlation-id",
  "metadata": {}
}
```

## 🧪 Testing

The template includes comprehensive testing:

```bash
# Run all tests
make test-all

# Run unit tests only
make test

# Run integration tests
make test-integration

# Run with coverage
make test-coverage
```

### Test Structure

```
tests/
├── unit/
│   ├── test_dynamodb_adapter.py
│   ├── test_kafka_adapter.py
│   └── test_sqs_adapter.py
└── integration/
    └── test_api_endpoints.py
```

## 🔨 Development Workflow

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check

# Security checks
make security-check

# Run all checks
make check-all
```

### Local Development

```bash
# Start local API server
make run-local

# Test local endpoint
curl http://localhost:8080/health

# Stop local processes
make stop-local
```

### Building and Deployment

```bash
# Build deployment package
make build

# Deploy to development
make deploy-dev

# Deploy to staging
make deploy-staging

# Deploy to production
make deploy-prod
```

## 🏗️ Infrastructure

### Terraform Modules

The template uses modular Terraform configuration:

```
terraform/
├── dev/
├── staging/
├── prod/
└── modules/
    ├── api_gateway/
    ├── dynamodb_table/
    ├── iam_roles/
    ├── kafka_config/
    ├── lambda_function/
    ├── openapi_docs/
    ├── secrets_manager/
    └── sqs_queue/
```

### Environment Management

Each environment has its own Terraform state and configuration:

```bash
# Initialize environment
make terraform-init ENVIRONMENT=dev

# Plan changes
make terraform-plan ENVIRONMENT=dev

# Apply changes
make terraform-apply ENVIRONMENT=dev

# Destroy (be careful!)
make terraform-destroy ENVIRONMENT=dev
```

## 📊 Monitoring and Debugging

### Logging

The template uses structured JSON logging with correlation IDs:

```python
from utils.logging import get_logger

logger = get_logger(__name__, correlation_id="req-123")
logger.info("Processing request", extra={"user_id": "user-456"})
```

### AWS CloudWatch

```bash
# View recent logs
make logs

# Invoke Lambda directly
make invoke-lambda
```

### Database Operations

```bash
# Scan DynamoDB table
make dynamodb-scan

# Check SQS messages
make sqs-messages
```

## 🔄 Event-Driven Patterns

### Publishing Events

```python
from adapters.kafka_adapter import send_message
from models.payload_models import ItemCreatedEvent

# Create and send event
event = ItemCreatedEvent.from_create_request(item, "my-service", correlation_id)
result = send_message("my-topic", event.dict(), key=item.id)
```

### Consuming Events

```python
from adapters.kafka_adapter import consume_messages

# Consume messages
messages = consume_messages("my-topic", group_id="my-consumer-group", max_messages=10)
for message in messages:
    process_event(message['value'])
```

## 📚 Documentation

### API Documentation

Generate and deploy OpenAPI documentation:

```bash
make openapi-docs
```

The documentation will be available at your CloudFront distribution URL.

### Adding New Endpoints

1. Add route to `src/api/api_handler.py`
2. Create request/response models in `src/models/payload_models.py`
3. Add business logic to `src/services/core_logic.py`
4. Write tests in `tests/`

## 🔄 Creating New Microservices

### Option 1: Full Customization (Recommended)

Use the interactive script to create a fully customized microservice with custom resource names:

```bash
make create-custom-service
```

This will prompt you for:
- **Service name**: The base name for your microservice (e.g., `user-management`)
- **Lambda handler**: Custom handler path (default: `main.handler`)
- **DynamoDB table name**: Custom table name (default: `{service-name}-table`)
- **SQS queue name**: Custom queue name (default: `{service-name}-queue`)
- **Kafka topic names**: Main topic and DLQ topic names
- **API Gateway name**: Custom API name (default: `{service-name}-api`)
- **Target directory**: Where to create the new service

The script will:
✅ Copy the entire template structure  
✅ Replace all hardcoded resource names throughout the codebase  
✅ Update Terraform configurations with your custom names  
✅ Modify source code to use your custom resource names  
✅ Update documentation and configuration files  

### Option 2: Basic Template Copy (Legacy)

For simple service name replacement only:

```bash
make create-template
# Follow the prompts to create a new service
```

### Example: Creating a User Management Service

```bash
$ make create-custom-service

🚀 Creating a new microservice from serverless-microservice-template
============================================================
Enter new service name (e.g., 'user-management'): user-management
Lambda handler [default: main.handler]: user.handler
DynamoDB table name [default: user-management-table]: users
SQS queue name [default: user-management-queue]: user-processing
Kafka main topic [default: user-management-events]: user-events
Kafka DLQ topic [default: user-management-dlq]: user-dlq
API Gateway name [default: user-management-api]: user-api
Target directory [default: ../user-management]: ../user-management

📋 Configuration Summary:
------------------------------
service_name   : user-management
lambda_handler : user.handler
dynamodb_table : users
sqs_queue      : user-processing
kafka_topic    : user-events
kafka_dlq      : user-dlq
api_gateway    : user-api
target_dir     : ../user-management

Proceed with these settings? [Y/n]: y

📁 Copying template to /path/to/user-management...
🔄 Processing 45 files...
  ✅ Makefile
  ✅ README.md
  ✅ src/main.py
  ✅ src/api/api_handler.py
  ✅ terraform/dev/main.tf
  ... (and more)

🎉 Successfully created 'user-management' service!
📁 Location: /path/to/user-management
📝 Modified 23 files

🚀 Next steps:
1. cd /path/to/user-management
2. make init
3. Configure your MSK cluster details in terraform/dev/main.tf
4. make deploy-dev
```

## 🛡️ Security Best Practices

- ✅ Secrets stored in AWS SSM Parameter Store
- ✅ IAM roles with minimal permissions
- ✅ Input validation with Pydantic
- ✅ Security scanning with bandit
- ✅ Dependency vulnerability checks with safety

## 🚀 Production Considerations

### Environment Configuration

- **Development**: Detailed logging, relaxed timeouts
- **Staging**: Production-like settings for testing
- **Production**: JSON logging, optimized performance, monitoring

### Scaling

- Lambda automatically scales based on demand
- DynamoDB can be configured for auto-scaling
- SQS provides reliable message queuing
- Kafka partitions allow horizontal scaling

### Monitoring

Consider adding:
- CloudWatch custom metrics
- AWS X-Ray tracing
- Application Performance Monitoring (APM)
- Custom dashboards

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks: `make check-all test-all`
5. Submit a pull request

## 📄 License

This template is provided under the MIT License. See LICENSE file for details.

## 📞 Support

For questions or issues:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information

---

**Happy coding! 🎉**

This template provides a solid foundation for building production-ready serverless microservices with event-driven architecture and comprehensive tooling.
