output "stack_ids" {
  description = "Map of stack name to Spacelift stack ID"
  value       = { for k, v in spacelift_stack.this : k => v.id }
}

output "stack_urls" {
  description = "Map of stack name to Spacelift console URL"
  value = {
    for k, v in spacelift_stack.this : k => "https://app.spacelift.io/stack/${v.id}"
  }
}
