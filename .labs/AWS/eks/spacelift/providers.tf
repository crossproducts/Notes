terraform {
  required_version = ">= 1.3.0"

  required_providers {
    spacelift = {
      source  = "spacelift-io/spacelift"
      version = "~> 1.0"
    }
  }
}

# Configured via environment variables:
#   SPACELIFT_API_KEY_ENDPOINT
#   SPACELIFT_API_KEY_ID
#   SPACELIFT_API_KEY_SECRET
provider "spacelift" {}
