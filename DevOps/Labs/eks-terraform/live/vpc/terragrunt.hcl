include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/vpc"
}

inputs = {
  vpc_name = "eks-lab-vpc"
  vpc_cidr = "10.0.0.0/16"
}
