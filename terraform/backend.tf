# Terraform Remote Backend Configuration
#
# This configuration stores Terraform state in S3 with DynamoDB locking
# for team collaboration and CI/CD pipelines.
#
# Prerequisites:
#   - S3 bucket: theme-park-terraform-state-129875285541
#   - DynamoDB table: theme-park-terraform-locks
#
# To initialize:
#   terraform init -migrate-state

terraform {
  backend "s3" {
    bucket         = "theme-park-terraform-state-129875285541"
    key            = "production/terraform.tfstate"
    region         = "us-east-2"
    dynamodb_table = "theme-park-terraform-locks"
    encrypt        = true
  }
}
