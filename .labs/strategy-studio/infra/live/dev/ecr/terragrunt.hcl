include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "tfr:///terraform-aws-modules/ecr/aws?version=2.3.0"
}

inputs = {
  repository_name         = "strategy-studio/backtest-api"
  repository_force_delete = true # lab: allow destroy with images inside

  repository_lifecycle_policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}
