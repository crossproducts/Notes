output "state_bucket" {
  description = "S3 bucket for Terraform state"
  value       = aws_s3_bucket.state.id
}

output "lock_table" {
  description = "DynamoDB table for state locking"
  value       = aws_dynamodb_table.locks.name
}

output "region" {
  description = "AWS region"
  value       = var.region
}
