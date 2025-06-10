# terraform/dev/main.tf
module "dynamodb_table" {
  source     = "../modules/dynamodb_table"
  name       = "my-table-dev"
  hash_key   = "id"
  hash_key_type = "S"
}

module "sqs_queue" {
  source = "../modules/sqs_queue"
  name   = "my-queue-dev"
}

module "secrets_manager" {
  source = "../modules/secrets_manager"
  name   = "/my/service/secret"
  value  = "super-secret-dev-key"
  description = "Secret for dev service"
  tags = {
    env = "dev"
  }
}
