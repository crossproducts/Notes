# Terraform & Terragrunt — AWS

> Concise reference for provisioning AWS infrastructure with Terraform and Terragrunt.

---

## AWS Modules

<details>
<summary>VPC Module</summary>

```hcl
# modules/vpc/main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.environment}-vpc"
    Environment = var.environment
  }
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnets)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.environment}-public-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.environment}-igw" }
}
```

```hcl
# modules/vpc/variables.tf
variable "environment" { type = string }
variable "vpc_cidr"    { type = string }
variable "public_subnets" {
  type    = list(string)
  default = ["10.0.1.0/24", "10.0.2.0/24"]
}
variable "azs" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}
```

```hcl
# modules/vpc/outputs.tf
output "vpc_id"         { value = aws_vpc.main.id }
output "public_subnets" { value = aws_subnet.public[*].id }
```

</details>

<details>
<summary>EC2 Module</summary>

```hcl
# modules/ec2/main.tf
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.web.id]
  key_name               = var.key_name

  tags = {
    Name        = "${var.environment}-web"
    Environment = var.environment
  }
}

resource "aws_security_group" "web" {
  name   = "${var.environment}-web-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

```hcl
# modules/ec2/variables.tf
variable "environment"   { type = string }
variable "instance_type" { type = string; default = "t3.micro" }
variable "subnet_id"     { type = string }
variable "vpc_id"        { type = string }
variable "key_name"      { type = string; default = "" }
```

```hcl
# modules/ec2/outputs.tf
output "instance_id"       { value = aws_instance.web.id }
output "public_ip"         { value = aws_instance.web.public_ip }
output "security_group_id" { value = aws_security_group.web.id }
```

</details>

<details>
<summary>RDS Module</summary>

```hcl
# modules/rds/main.tf
resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-db-subnet"
  subnet_ids = var.subnet_ids
}

resource "aws_db_instance" "main" {
  identifier             = "${var.environment}-db"
  engine                 = "postgres"
  engine_version         = "15"
  instance_class         = var.instance_class
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  allocated_storage      = var.storage_gb
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot    = true
  multi_az               = var.multi_az

  tags = { Environment = var.environment }
}

resource "aws_security_group" "rds" {
  name   = "${var.environment}-rds-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.app_cidr]
  }
}
```

```hcl
# modules/rds/variables.tf
variable "environment"    { type = string }
variable "vpc_id"         { type = string }
variable "subnet_ids"     { type = list(string) }
variable "instance_class" { type = string; default = "db.t3.micro" }
variable "db_name"        { type = string }
variable "db_username"    { type = string }
variable "db_password"    { type = string; sensitive = true }
variable "storage_gb"     { type = number; default = 20 }
variable "multi_az"       { type = bool; default = false }
variable "app_cidr"       { type = string }
```

```hcl
# modules/rds/outputs.tf
output "endpoint" { value = aws_db_instance.main.endpoint }
output "db_name"  { value = aws_db_instance.main.db_name }
```

</details>

<details>
<summary>S3 + IAM Module</summary>

```hcl
# modules/s3/main.tf
resource "aws_s3_bucket" "main" {
  bucket = "${var.environment}-${var.bucket_name}"
  tags   = { Environment = var.environment }
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_iam_role" "app" {
  name = "${var.environment}-app-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "s3_access" {
  role = aws_iam_role.app.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
      Resource = "${aws_s3_bucket.main.arn}/*"
    }]
  })
}
```

```hcl
# modules/s3/variables.tf
variable "environment" { type = string }
variable "bucket_name" { type = string }
```

```hcl
# modules/s3/outputs.tf
output "bucket_id"  { value = aws_s3_bucket.main.id }
output "bucket_arn" { value = aws_s3_bucket.main.arn }
output "role_arn"   { value = aws_iam_role.app.arn }
```

</details>