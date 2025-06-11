# Makefile for Serverless Python Microservice Template

# Variables
SERVICE_NAME ?= microservice-template
ENVIRONMENT ?= dev
AWS_REGION ?= us-east-1
PYTHON_VERSION = 3.12

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[0;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

# Help target
.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)Serverless Python Microservice Template$(NC)"
	@echo "$(YELLOW)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-25s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Setup
.PHONY: init
init: ## Initialize the project (creates .env, installs dependencies)
	@echo "$(BLUE)Initializing project...$(NC)"
	@touch .env
	@echo "SERVICE_NAME=$(SERVICE_NAME)" >> .env
	@echo "ENVIRONMENT=$(ENVIRONMENT)" >> .env
	@echo "AWS_REGION=$(AWS_REGION)" >> .env
	@echo "LOG_LEVEL=INFO" >> .env
	@echo "$(GREEN)Created .env file$(NC)"
	@make install-deps
	@echo "$(GREEN)Project initialized successfully!$(NC)"

.PHONY: install-deps
install-deps: ## Install Python dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@pip install -r requirements.txt
	@echo "$(GREEN)Dependencies installed$(NC)"

.PHONY: install-dev-deps
install-dev-deps: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	@pip install -r requirements.txt
	@pip install black flake8 isort mypy pytest-cov bandit safety
	@echo "$(GREEN)Development dependencies installed$(NC)"

# Code Quality
.PHONY: format
format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	@black src/ tests/
	@isort src/ tests/
	@echo "$(GREEN)Code formatted$(NC)"

.PHONY: lint
lint: ## Run linting checks
	@echo "$(BLUE)Running linting checks...$(NC)"
	@flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
	@echo "$(GREEN)Linting passed$(NC)"

.PHONY: type-check
type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	@mypy src/ --ignore-missing-imports
	@echo "$(GREEN)Type checking passed$(NC)"

.PHONY: security-check
security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	@bandit -r src/ -f json -o security-report.json || true
	@safety check --json --output safety-report.json || true
	@echo "$(GREEN)Security checks completed$(NC)"

.PHONY: check-all
check-all: format lint type-check security-check ## Run all code quality checks
	@echo "$(GREEN)All code quality checks completed$(NC)"

# Testing
.PHONY: test
test: ## Run unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	@pytest tests/unit/ -v
	@echo "$(GREEN)Unit tests completed$(NC)"

.PHONY: test-integration
test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	@pytest tests/integration/ -v
	@echo "$(GREEN)Integration tests completed$(NC)"

.PHONY: test-all
test-all: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	@pytest tests/ -v
	@echo "$(GREEN)All tests completed$(NC)"

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

# Build and Package
.PHONY: clean
clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
	@rm -rf deployment.zip
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Cleaned build artifacts$(NC)"

.PHONY: build
build: clean ## Build deployment package
	@echo "$(BLUE)Building deployment package...$(NC)"
	@mkdir -p build
	@cp -r src/* build/
	@pip install -r requirements.txt -t build/ --no-deps
	@cd build && zip -r ../deployment.zip . -x "*.pyc" "*/__pycache__/*"
	@echo "$(GREEN)Deployment package created: deployment.zip$(NC)"

# Local Development
.PHONY: run-local
run-local: ## Run the API locally
	@echo "$(BLUE)Starting local API server...$(NC)"
	@export ENVIRONMENT=local && uvicorn src.api.api_handler:app --host 0.0.0.0 --port 8080 --reload

.PHONY: run-local-background
run-local-background: ## Run the API locally in background
	@echo "$(BLUE)Starting local API server in background...$(NC)"
	@export ENVIRONMENT=local && uvicorn src.api.api_handler:app --host 0.0.0.0 --port 8080 &

.PHONY: stop-local
stop-local: ## Stop local background processes
	@echo "$(BLUE)Stopping local processes...$(NC)"
	@pkill -f "uvicorn src.api.api_handler:app" || true
	@echo "$(GREEN)Local processes stopped$(NC)"

# Documentation
.PHONY: openapi-docs
openapi-docs: ## Generate and deploy OpenAPI documentation
	@echo "$(BLUE)Generating OpenAPI documentation...$(NC)"
	@make run-local-background
	@sleep 3
	@curl -f http://localhost:8080/openapi.json -o openapi.json || (echo "$(RED)Failed to get OpenAPI spec$(NC)" && make stop-local && exit 1)
	@make stop-local
	@npx redoc-cli bundle openapi.json -o index.html
	@aws s3 cp index.html s3://$(SERVICE_NAME)-$(ENVIRONMENT)-openapi-docs/index.html
	@echo "$(GREEN)OpenAPI documentation deployed$(NC)"

# Infrastructure
.PHONY: terraform-init
terraform-init: ## Initialize Terraform for the specified environment
	@echo "$(BLUE)Initializing Terraform for $(ENVIRONMENT)...$(NC)"
	@cd terraform/$(ENVIRONMENT) && terraform init
	@echo "$(GREEN)Terraform initialized$(NC)"

.PHONY: terraform-plan
terraform-plan: terraform-init ## Plan Terraform deployment
	@echo "$(BLUE)Planning Terraform deployment for $(ENVIRONMENT)...$(NC)"
	@cd terraform/$(ENVIRONMENT) && terraform plan
	@echo "$(GREEN)Terraform plan completed$(NC)"

.PHONY: terraform-apply
terraform-apply: terraform-init ## Apply Terraform configuration
	@echo "$(BLUE)Applying Terraform configuration for $(ENVIRONMENT)...$(NC)"
	@cd terraform/$(ENVIRONMENT) && terraform apply
	@echo "$(GREEN)Terraform applied$(NC)"

.PHONY: terraform-destroy
terraform-destroy: terraform-init ## Destroy Terraform infrastructure
	@echo "$(RED)WARNING: This will destroy all infrastructure for $(ENVIRONMENT)$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r && echo && \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cd terraform/$(ENVIRONMENT) && terraform destroy; \
		echo "$(GREEN)Infrastructure destroyed$(NC)"; \
	else \
		echo "$(YELLOW)Operation cancelled$(NC)"; \
	fi

.PHONY: deploy
deploy: build terraform-apply ## Build and deploy the application
	@echo "$(GREEN)Deployment completed for $(ENVIRONMENT)$(NC)"

# Environment-specific targets
.PHONY: deploy-dev
deploy-dev: ## Deploy to development environment
	@make deploy ENVIRONMENT=dev

.PHONY: deploy-staging
deploy-staging: ## Deploy to staging environment
	@make deploy ENVIRONMENT=staging

.PHONY: deploy-prod
deploy-prod: ## Deploy to production environment
	@make deploy ENVIRONMENT=prod

# Kafka Management
.PHONY: kafka-topics-list
kafka-topics-list: ## List Kafka topics
	@echo "$(BLUE)Listing Kafka topics for $(ENVIRONMENT)...$(NC)"
	@aws kafka list-clusters --cluster-name-filter "$(SERVICE_NAME)-$(ENVIRONMENT)" --query 'ClusterInfoList[0].ClusterArn' --output text | \
	xargs -I {} aws kafka describe-cluster --cluster-arn {} --query 'ClusterInfo.ZookeeperConnectString' --output text | \
	xargs -I {} kafka-topics.sh --bootstrap-server {} --list || echo "$(YELLOW)Kafka CLI tools not available$(NC)"

.PHONY: kafka-create-topics
kafka-create-topics: ## Create default Kafka topics
	@echo "$(BLUE)Creating Kafka topics for $(ENVIRONMENT)...$(NC)"
	@echo "$(YELLOW)This requires Kafka CLI tools to be installed$(NC)"
	# Add your topic creation commands here

# Monitoring and Debugging
.PHONY: logs
logs: ## Show recent Lambda logs
	@echo "$(BLUE)Fetching recent logs for $(ENVIRONMENT)...$(NC)"
	@aws logs tail /aws/lambda/$(SERVICE_NAME)-$(ENVIRONMENT)-function --follow

.PHONY: invoke-lambda
invoke-lambda: ## Invoke Lambda function with test payload
	@echo "$(BLUE)Invoking Lambda function...$(NC)"
	@echo '{"id":"test-123","name":"Test Item","description":"Test invocation"}' | \
	aws lambda invoke \
		--function-name $(SERVICE_NAME)-$(ENVIRONMENT)-function \
		--payload file:///dev/stdin \
		response.json
	@cat response.json | jq .
	@rm response.json

# Database Operations
.PHONY: dynamodb-scan
dynamodb-scan: ## Scan DynamoDB table
	@echo "$(BLUE)Scanning DynamoDB table...$(NC)"
	@aws dynamodb scan --table-name $(SERVICE_NAME)-$(ENVIRONMENT)-table --max-items 10

.PHONY: sqs-messages
sqs-messages: ## Receive messages from SQS queue
	@echo "$(BLUE)Receiving messages from SQS...$(NC)"
	@aws sqs receive-message --queue-url $$(aws sqs get-queue-url --queue-name $(SERVICE_NAME)-$(ENVIRONMENT)-queue --query 'QueueUrl' --output text) --max-number-of-messages 10

# Utilities
.PHONY: validate-env
validate-env: ## Validate environment configuration
	@echo "$(BLUE)Validating environment configuration...$(NC)"
	@echo "Service Name: $(SERVICE_NAME)"
	@echo "Environment: $(ENVIRONMENT)"
	@echo "AWS Region: $(AWS_REGION)"
	@if [ -f .env ]; then echo "$(GREEN).env file exists$(NC)"; else echo "$(RED).env file missing$(NC)"; fi
	@echo "$(GREEN)Environment validation completed$(NC)"

.PHONY: create-template
create-template: ## Create a new microservice from this template (legacy - use create-custom-service instead)
	@echo "$(YELLOW)This is the legacy template creation method.$(NC)"
	@echo "$(BLUE)For full customization, use: make create-custom-service$(NC)"
	@read -p "Enter new service name: " service_name && \
	if [ -z "$$service_name" ]; then \
		echo "$(RED)Service name cannot be empty$(NC)"; \
		exit 1; \
	fi && \
	mkdir -p ../$$service_name && \
	cp -r . ../$$service_name && \
	cd ../$$service_name && \
	sed -i.bak "s/microservice-template/$$service_name/g" Makefile README.md && \
	rm -f Makefile.bak README.md.bak && \
	echo "$(GREEN)New microservice '$$service_name' created in ../$$service_name$(NC)"

.PHONY: create-custom-service
create-custom-service: ## Create a fully customized microservice with custom resource names
	@echo "$(BLUE)Creating customized microservice...$(NC)"
	@python3 create_custom_service.py

# Default target
.DEFAULT_GOAL := help
