# bootstrap/

Creates the S3 bucket + DynamoDB table that the rest of the lab uses as a Terraform remote-state backend. Uses **local** state (chicken-and-egg avoidance).

```powershell
terraform init
terraform apply
```

Outputs the bucket and table names. These match defaults in `live/env.hcl`, so no copy-paste is needed unless you change the bucket name (it must be globally unique).
