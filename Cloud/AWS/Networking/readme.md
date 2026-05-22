# AWS Networking

## Notes
- Dual Stack Subnet: Ipv4 & Ipv6
- Elastic IP
- DNS64 / NAT64?
- Route53 vs Elastic IP

## Architectures
- Public Subnet [ EC2 w/ Ipv4 or Ipv6 ] 
    → IGW 
        → Internet
- Public Subnet [ EC2 w/ Ipv4 or Ipv6 ] 
    → Elastic IP 
        → IGW 
            → Internet
- Private Subnet [ EC2 w/ Ipv4 ] 
    → Public Subnet [ NAT Gateway ] 
        → IGW 
            → Internet
- ⚠️Private Subnet [ EC2 w/ Ipv4 ] 
    → Public Subnet [ NAT Gateway ] 
        → Elastic IP 
            → IGW 
                → Internet
- Private Subnet [ EC2 w/ Ipv6 ] 
    →  EIGW 
        → Internet
- Route53
    - → AZ [ NLB → targets ]
    - → AZ [ NLB → targets ]
    - → AZ [ NLB → targets ]


## Abbreviations
- IGW - Internet Gateway
- EIGW - Egress-only Internet Gateway

## Tips
- `Alt` + `26` = `→`

## References
- [Youtube | AWS Events - AWS re:Invent 2024 - Design well-architected networks on AWS (NET202)](https://www.youtube.com/watch?v=Pd5p-fzwsLA)
