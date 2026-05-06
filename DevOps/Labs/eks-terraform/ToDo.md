# ToDo

- AWS Load Balancer Controller (ALB ingress for ArgoCD)
- ArgoCD SSO
- ExternalDNS + Route53
- cert-manager + ACM
- ECR for app images

- IRSA examples (e.g. service-account that reads S3)
- Karpenter (would require switching off pure-Fargate)
- kube-prometheus-stack (note: node-exporter requires nodes -- skip on pure Fargate)
- Loki / Grafana Alloy
- OpenTelemetry Collector

- Falco (DaemonSet -- not Fargate-compatible)
- Trivy Operator
- Kyverno / OPA Gatekeeper

- Backstage
- Crossplane

- Multi-env (dev/stage/prod) via Terragrunt
- GitHub Actions for `terragrunt plan` on PR
