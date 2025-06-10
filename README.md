# README.md
# Serverless Python Microservice Template

This is a reusable serverless microservice template built in Python using AWS Lambda, DynamoDB, SQS, and Terraform.

## Features
- ✅ Multi-environment support (dev/staging/prod)
- ✅ Modular infrastructure using Terraform modules
- ✅ Adapter-based architecture (DynamoDB, SQS, Kafka-ready)
- ✅ AWS Secrets support using SSM Parameter Store
- ✅ Built-in test suite with `pytest` and `moto`
- ✅ CI pipeline using GitHub Actions

## Schema Validation
This template uses [Pydantic](https://docs.pydantic.dev/) to define and validate payloads before interacting with AWS services. See:
- `src/models/payload_models.py` for schemas
- `src/models/validation.py` for validators

## API Endpoint
This template uses FastAPI to define application-level routes. When deployed with API Gateway:

```bash
POST /create
Body: {
  "id": "abc123",
  "name": "Test Item",
  "description": "Example"
}
```

The API is deployed using AWS API Gateway HTTP APIs with Lambda proxy integration.

## OpenAPI Documentation Hosting
Generate and deploy documentation using:

```bash
make openapi-docs
```

Docs will be live at:
```
https://<cloudfront-domain>/
```

## Kafka Integration
Kafka support is ready for future use. See `src/adapters/kafka_adapter.py` once implemented.