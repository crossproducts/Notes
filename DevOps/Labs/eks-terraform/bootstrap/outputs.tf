output "state_bucket" {
  value = aws_s3_bucket.tf_state.id
}

output "lock_table" {
  value = aws_dynamodb_table.tf_locks.id
}

output "region" {
  value = var.region
}
