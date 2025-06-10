# terraform/modules/dynamodb_table/main.tf
resource "aws_dynamodb_table" "this" {
  name           = var.name
  hash_key       = var.hash_key
  billing_mode   = "PAY_PER_REQUEST"
  attribute {
    name = var.hash_key
    type = var.hash_key_type
  }
}
