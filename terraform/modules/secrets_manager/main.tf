
# terraform/modules/secrets_manager/main.tf
resource "aws_ssm_parameter" "secret_param" {
  name        = var.name
  type        = "SecureString"
  value       = var.value
  description = var.description
  tags        = var.tags
}