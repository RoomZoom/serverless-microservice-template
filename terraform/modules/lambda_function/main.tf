# terraform/modules/lambda_function/main.tf
resource "aws_lambda_function" "this" {
  function_name = var.name
  handler       = var.handler
  runtime       = "python3.12"
  role          = var.role_arn
  filename      = var.filename
}
