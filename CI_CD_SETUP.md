# CI/CD Pipeline Setup Guide

This document provides comprehensive setup instructions for the GitHub Actions CI/CD pipeline.

## Overview

The CI/CD pipeline implements a 3-environment strategy:
- **Dev**: PR validation and testing
- **Staging**: Auto-deploy after PR merge to main
- **Production**: Manual deployment with approval

## Required GitHub Secrets

### For Template Usage (Basic Validation Only)
No secrets are required for basic code quality validation. The "Validate Code Quality" job will run without any configuration.

### For Full CI/CD Pipeline (Deployment Testing & Auto-Deploy)
Configure these secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`) to enable deployment features:

### AWS Credentials
```
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
```

### Environment-Specific Kafka Configuration
```
DEV_KAFKA_CLUSTER_ARN=arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster-dev/uuid
DEV_KAFKA_BOOTSTRAP_SERVERS=broker1.dev.cluster.kafka.us-east-1.amazonaws.com:9092,broker2.dev.cluster.kafka.us-east-1.amazonaws.com:9092

STAGING_KAFKA_CLUSTER_ARN=arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster-staging/uuid
STAGING_KAFKA_BOOTSTRAP_SERVERS=broker1.staging.cluster.kafka.us-east-1.amazonaws.com:9092,broker2.staging.cluster.kafka.us-east-1.amazonaws.com:9092

PROD_KAFKA_CLUSTER_ARN=arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster-prod/uuid
PROD_KAFKA_BOOTSTRAP_SERVERS=broker1.prod.cluster.kafka.us-east-1.amazonaws.com:9092,broker2.prod.cluster.kafka.us-east-1.amazonaws.com:9092
```

## Environment Protection Rules

### Staging Environment
1. Go to `Settings > Environments`
2. Create environment named `staging`
3. Optional: Add deployment notifications

### Production Environment
1. Go to `Settings > Environments`
2. Create environment named `production`
3. Configure protection rules:
   - **Required reviewers**: Add team members
   - **Wait timer**: 5-10 minutes (optional)
   - **Deployment branches**: Restrict to `main` only

## Workflow Triggers

### Automatic Triggers
- **PR Validation**: Runs on PR open/update
- **Staging Deploy**: Runs on push to main branch

### Manual Triggers
- **Production Deploy**: Actions tab > "CI/CD Pipeline" > "Run workflow" > Select "prod"
- **Manual Staging**: Actions tab > "CI/CD Pipeline" > "Run workflow" > Select "staging"

## Workflow Jobs

### 1. Validate (PR only)
- Code formatting (black, isort)
- Linting (flake8)
- Type checking (mypy)
- Security scanning (bandit)
- Unit tests (pytest)
- Build deployment package

### 2. Test Dev Deploy (PR only)
- Terraform plan for dev environment
- Integration tests
- Validates deployment without applying

### 3. Deploy Staging (Auto on main push)
- Full test suite
- Deploy to staging environment
- Post-deployment verification
- Generate deployment summary

### 4. Deploy Production (Manual only)
- Pre-deployment verification
- Deploy to production environment
- Post-deployment health checks
- Generate deployment summary

## Usage Examples

### Creating a Pull Request
```bash
git checkout -b feature/my-feature
# Make changes
git add .
git commit -m "Add new feature"
git push origin feature/my-feature
# Create PR in GitHub - validation runs automatically
```

### Deploying to Production
1. Navigate to GitHub Actions tab
2. Select "CI/CD Pipeline" workflow
3. Click "Run workflow"
4. Select "prod" from environment dropdown
5. Click "Run workflow" button
6. Approve deployment if protection rules are configured

## Troubleshooting

### Common Issues

#### Terraform Plan Failures
- Verify AWS credentials are correct
- Check Kafka cluster ARNs and bootstrap servers
- Ensure IAM permissions for Terraform operations

#### Test Failures
- Review test logs in GitHub Actions
- Check environment variables are set correctly
- Verify test dependencies are installed

#### Deployment Timeouts
- Increase wait times in workflow steps
- Check AWS service limits
- Verify network connectivity

### Debugging Steps
1. Check workflow logs in GitHub Actions
2. Verify all required secrets are configured
3. Test AWS credentials locally
4. Validate Terraform configurations
5. Run tests locally to isolate issues

## Integration with Existing Tools

The CI/CD pipeline integrates seamlessly with existing repository infrastructure:

- **Makefile**: Uses existing targets without modification
- **Terraform**: Works with existing environment configurations
- **Tests**: Runs existing pytest test suites
- **Dependencies**: Uses existing requirements.txt

No changes to existing build or deployment processes are required.

## Monitoring and Notifications

### Deployment Summaries
Each deployment generates a summary with:
- Environment deployed to
- Commit SHA
- Deployment timestamp
- API endpoint URL
- Deployer information

### Notifications
Configure GitHub notifications for:
- Workflow failures
- Deployment completions
- PR status updates

## Security Considerations

- AWS credentials are stored as GitHub secrets
- Environment-specific configurations are isolated
- Production deployments require manual approval
- All deployments are logged and auditable
- Terraform state is managed securely

## Next Steps

1. Configure required GitHub secrets
2. Set up environment protection rules
3. Test the pipeline with a sample PR
4. Configure team notifications
5. Document any custom deployment procedures
