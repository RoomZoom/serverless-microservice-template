# CI/CD Workflows

This directory contains GitHub Actions workflows for the serverless microservice template.

## Workflows

### main.yml
The main CI/CD pipeline that handles:
- PR validation with code quality checks
- Automatic deployment to staging after PR merge
- Manual production deployment with approval

## Workflow Triggers

- **Pull Request**: Runs validation and dev deployment testing
- **Push to main**: Automatically deploys to staging
- **Manual dispatch**: Allows manual deployment to staging or production

## Required Secrets

### For Full CI/CD Pipeline (Optional for Template Usage)

Configure these in your GitHub repository settings to enable deployment testing and automatic deployments:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `DEV_KAFKA_CLUSTER_ARN`
- `DEV_KAFKA_BOOTSTRAP_SERVERS`
- `STAGING_KAFKA_CLUSTER_ARN`
- `STAGING_KAFKA_BOOTSTRAP_SERVERS`
- `PROD_KAFKA_CLUSTER_ARN`
- `PROD_KAFKA_BOOTSTRAP_SERVERS`

**Note**: The "Validate Code Quality" job runs without AWS credentials. Deployment testing and automatic deployments require AWS credentials to be configured.

## Environment Protection

Set up environment protection rules in GitHub:
- **staging**: Optional approval
- **production**: Required approval from team members

## Jobs Overview

### 1. validate (PR only)
- Code formatting checks (black, isort)
- Linting (flake8)
- Type checking (mypy)
- Security scanning (bandit)
- Unit tests (pytest)
- Build deployment package

### 2. test-dev-deploy (PR only)
- Terraform plan validation for dev environment
- Integration tests against dev
- Validates deployment without applying changes

### 3. deploy-staging (Auto on main push)
- Full test suite execution
- Deploy to staging environment
- Post-deployment verification
- Generate deployment summary

### 4. deploy-production (Manual only)
- Pre-deployment verification
- Deploy to production environment
- Post-deployment health checks
- Generate deployment summary

### 5. deploy-staging-manual (Manual only)
- Manual staging deployment for testing
- Generate deployment summary

## Features

- Code quality gates (formatting, linting, type checking, security)
- Build artifact caching and retention (7 days)
- Deployment monitoring and summaries
- Integration with existing Makefile targets
- Terraform integration for infrastructure deployment
- Environment-specific configuration management

## Usage

### Creating a Pull Request
1. Create feature branch and make changes
2. Push branch and create PR
3. Validation workflow runs automatically
4. Address any code quality issues
5. Merge PR to trigger staging deployment

### Manual Production Deployment
1. Navigate to GitHub Actions tab
2. Select "CI/CD Pipeline" workflow
3. Click "Run workflow"
4. Select "prod" from environment dropdown
5. Click "Run workflow" button
6. Approve deployment if protection rules are configured

### Manual Staging Deployment
1. Navigate to GitHub Actions tab
2. Select "CI/CD Pipeline" workflow
3. Click "Run workflow"
4. Select "staging" from environment dropdown
5. Click "Run workflow" button

## Integration with Existing Infrastructure

The workflows seamlessly integrate with existing repository infrastructure:

- **Makefile Targets**: Uses existing targets without modification
  - `install-dev-deps`, `install-deps`
  - `lint`, `type-check`, `security-check`
  - `test`, `test-integration`
  - `build`
  - `deploy-staging`, `deploy-prod`
  - `terraform-plan`

- **Terraform Configurations**: Works with existing environment configs
  - `terraform/dev/`
  - `terraform/staging/`
  - `terraform/prod/`

- **Test Infrastructure**: Runs existing pytest test suites
  - Unit tests in `tests/`
  - Integration tests via `make test-integration`

## Troubleshooting

### Common Issues

1. **Terraform Plan Failures**
   - Verify AWS credentials are correct
   - Check Kafka cluster ARNs and bootstrap servers
   - Ensure IAM permissions for Terraform operations

2. **Test Failures**
   - Review test logs in GitHub Actions
   - Check environment variables are set correctly
   - Verify test dependencies are installed

3. **Deployment Timeouts**
   - Increase wait times in workflow steps
   - Check AWS service limits
   - Verify network connectivity

### Debugging Steps
1. Check workflow logs in GitHub Actions tab
2. Verify all required secrets are configured
3. Test AWS credentials locally if possible
4. Validate Terraform configurations
5. Run tests locally to isolate issues
