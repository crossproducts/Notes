# AWS

## Certifications

| Certification | Level | Focus |
|---|---|---|
| [Cloud Practitioner](./Foundational-Cloud_Practitioner/) | Foundational | Broad AWS overview, billing, support |
| [AI Practitioner](./Foundational-AI_Practitioner/) | Foundational | AI/ML concepts, responsible AI, AWS AI services |
| [Solutions Architect – Associate](./Associate-Solution_Architect/) | Associate | Architecture best practices, resilient & cost-efficient systems |
| [Machine Learning – Associate](./!Associate-Machine_Learning/) | Associate | ML pipeline, SageMaker, data prep, model deployment |
| [Security – Specialty](./!Specialty-Security/) | Specialty | IAM, encryption, threat detection, compliance |

---

## AWS Architecture Patterns

> Architecture patterns are repeatable solutions to common cloud design problems. Each pattern maps to AWS services and solves a specific operational or business challenge.

---

### 🌐 Web & Application Tier

<details>
<summary><strong>Static Website Hosting</strong></summary>

**Use case**: Serve a static frontend (HTML/CSS/JS, React, Vue) globally with low latency and no servers to manage.

```
Users → Route 53 → CloudFront (CDN + HTTPS) → S3 (static assets)
                          ↓
                    WAF (optional DDoS / bot protection)
```

**Key services**: S3, CloudFront, Route 53, ACM (SSL), WAF

**Exam trigger**: "serverless", "static", "global delivery", "no backend"

</details>

---

<details>
<summary><strong>Three-Tier Web Application</strong></summary>

**Use case**: Traditional web app with a presentation layer, application logic, and a database — deployed with high availability across multiple AZs.

```
Users → Route 53 → ALB (public, multi-AZ)
                     ↓
              EC2 Auto Scaling Group (private subnet, app tier)
                     ↓
              RDS Multi-AZ (private subnet, data tier)
```

**Key services**: Route 53, ALB, EC2, Auto Scaling, RDS, VPC (public + private subnets), NAT Gateway

**Exam trigger**: "high availability", "fault tolerant", "web + app + DB tiers"

</details>

---

<details>
<summary><strong>Serverless Web Application</strong></summary>

**Use case**: Event-driven, zero-server-management web app. Scales automatically to zero when idle; cost-effective for variable or unpredictable traffic.

```
Users → CloudFront → API Gateway → Lambda → DynamoDB
                                       ↓
                                   S3 / other AWS services
```

**Key services**: API Gateway, Lambda, DynamoDB, S3, CloudFront, Cognito (auth)

**Exam trigger**: "no servers", "pay per request", "auto-scaling", "spiky traffic"

</details>

---

### 📦 Data & Storage

<details>
<summary><strong>Data Lake on S3</strong></summary>

**Use case**: Centralize raw, structured, and semi-structured data from multiple sources for analytics and ML. Decouple storage from compute.

```
Sources (RDS, Kinesis, DMS, DataSync)
    → S3 (raw / bronze zone)
    → Glue ETL → S3 (processed / silver zone)
    → Redshift / Athena / EMR (analytics / gold zone)
```

**Key services**: S3, AWS Glue, Glue Data Catalog, Athena, Lake Formation, Redshift, QuickSight

**Exam trigger**: "centralized data", "analytics", "ETL", "query in place"

</details>

---

<details>
<summary><strong>Real-Time Data Streaming & Analytics</strong></summary>

**Use case**: Ingest and process high-volume, continuous event streams (clickstreams, IoT telemetry, logs) with sub-second latency.

```
Producers (apps, IoT, logs)
    → Kinesis Data Streams → Lambda / Kinesis Data Analytics (Flink)
    → Kinesis Firehose → S3 / Redshift / OpenSearch
                              ↓
                         QuickSight (dashboards)
```

**Key services**: Kinesis Data Streams, Kinesis Firehose, Kinesis Data Analytics, Lambda, MSK (Kafka), OpenSearch, S3

**Exam trigger**: "real-time", "streaming", "IoT", "clickstream", "millisecond latency"

</details>

---

<details>
<summary><strong>Backup & Disaster Recovery</strong></summary>

**Use case**: Protect data against accidental deletion, corruption, and regional failures. Meet RPO/RTO requirements.

```
Primary Region                    DR Region
RDS Multi-AZ  ──── replication ──→ RDS Read Replica (promote on failover)
S3            ──── CRR          ──→ S3 (Cross-Region Replication)
EC2 AMIs      ──── copy          ──→ AMI copies
Route 53 health checks → failover routing
```

| DR Strategy | RTO | RPO | Cost |
|---|---|---|---|
| Backup & Restore | Hours | Hours | Lowest |
| Pilot Light | Minutes | Minutes | Low |
| Warm Standby | Minutes | Seconds | Medium |
| Multi-Site Active/Active | Near-zero | Near-zero | Highest |

**Key services**: AWS Backup, S3 CRR, RDS snapshots, Route 53 failover, CloudFormation

**Exam trigger**: "RPO", "RTO", "disaster recovery", "failover", "data durability"

</details>

---

### ⚡ Decoupling & Messaging

<details>
<summary><strong>Event-Driven / Decoupled Architecture</strong></summary>

**Use case**: Decouple producers from consumers so each component scales independently. Tolerate downstream failures without losing events.

```
Producer (app / service)
    → SQS (queue, buffer, dead-letter queue)
    → Lambda / EC2 consumers (poll or event-source mapping)

        OR

    → SNS (fan-out topic)
    → SQS queues (multiple subscribers)
    → Lambda / HTTP endpoints
```

**Key services**: SQS, SNS, EventBridge, Lambda, Step Functions

**Exam trigger**: "decouple", "async", "fan-out", "loose coupling", "retry", "dead-letter queue"

</details>

---

<details>
<summary><strong>Microservices Orchestration</strong></summary>

**Use case**: Coordinate multiple Lambda functions or ECS tasks in a defined workflow with retries, branching, and error handling — without writing orchestration logic in code.

```
API Gateway → Lambda (trigger)
                  ↓
           Step Functions (state machine)
           ├── Lambda A (validate)
           ├── Lambda B (process)
           ├── Choice state (branch on result)
           └── Lambda C (notify via SNS)
```

**Key services**: Step Functions, Lambda, SQS, SNS, API Gateway, ECS/Fargate

**Exam trigger**: "workflow", "orchestrate", "coordinate services", "retry logic", "long-running process"

</details>

---

### 🐳 Containers — ECS & EKS

<details>
<summary><strong>Containerized Microservices on ECS Fargate</strong></summary>

**Use case**: Run Docker containers without managing servers. Each microservice is an independent ECS service that scales, deploys, and fails independently.

```
Users → ALB (path-based routing)
         ├── /api/users  → ECS Service A (Fargate tasks)
         ├── /api/orders → ECS Service B (Fargate tasks)
         └── /api/search → ECS Service C (Fargate tasks)
                               ↓
                     RDS / DynamoDB / ElastiCache
                               ↓
                     ECR (container image registry)
                     Secrets Manager (env credentials)
```

**Key services**: ECS, Fargate, ECR, ALB, IAM Task Roles, Secrets Manager, CloudWatch Container Insights

**Exam trigger**: "containers", "Docker", "no EC2 to manage", "microservices", "task role"

</details>

---

<details>
<summary><strong>Kubernetes Workloads on EKS</strong></summary>

**Use case**: Run Kubernetes-native workloads on AWS with managed control plane. Use when you need Kubernetes ecosystem tooling (Helm, service mesh, custom operators) or are migrating existing K8s workloads.

```
kubectl / CI/CD → EKS Control Plane (managed by AWS)
                       ↓
              Worker Nodes (EC2 or Fargate)
              ├── Pod A (app container)
              ├── Pod B (sidecar / service mesh)
              └── Cluster Autoscaler (scale node groups)
                       ↓
              ALB Ingress Controller → ALB → pods
              EBS CSI Driver → persistent volumes
              IRSA (IAM Roles for Service Accounts) → AWS APIs
```

**Key services**: EKS, EC2 / Fargate node groups, ECR, ALB Ingress Controller, EBS CSI, IRSA, CloudWatch Container Insights

**Exam trigger**: "Kubernetes", "K8s", "EKS", "Helm", "service mesh", "existing K8s workloads"

</details>

---

<details>
<summary><strong>ECS vs EKS — When to Use Which</strong></summary>

| Factor | ECS (Fargate) | EKS |
|---|---|---|
| **Operational overhead** | Low — fully AWS-native | Higher — K8s expertise needed |
| **Kubernetes required** | No | Yes |
| **Ecosystem / tooling** | AWS-native only | Full K8s ecosystem (Helm, Istio, etc.) |
| **Scaling** | Service Auto Scaling | Cluster Autoscaler + HPA |
| **Cost** | Pay per task vCPU/memory | Pay for control plane + nodes |
| **Best for** | Greenfield AWS-native apps | K8s migrations, complex orchestration |

**Exam trigger**: "should we use ECS or EKS" → ECS if AWS-native & simpler; EKS if Kubernetes-specific requirements

</details>

---

### 🤖 Machine Learning

<details>
<summary><strong>End-to-End ML Pipeline on SageMaker</strong></summary>

**Use case**: Build, train, evaluate, and deploy ML models with a fully managed, reproducible pipeline.

```
Data Sources (S3, RDS, Kinesis)
    → SageMaker Data Wrangler / Glue (feature engineering)
    → SageMaker Feature Store
    → SageMaker Training Job (built-in algo or custom container)
    → SageMaker Experiments (track metrics)
    → SageMaker Model Registry (version + approve)
    → SageMaker Endpoint (real-time) / Batch Transform (offline)
    → SageMaker Model Monitor (drift detection)
```

**Key services**: SageMaker (full suite), S3, Glue, ECR, CloudWatch, EventBridge

**Exam trigger**: "ML pipeline", "retrain", "model drift", "feature store", "AutoML"

</details>

---

<details>
<summary><strong>Real-Time ML Inference at Scale</strong></summary>

**Use case**: Serve ML model predictions with low latency to high-traffic applications, with auto-scaling and A/B testing.

```
Client → API Gateway → Lambda
                          ↓
                  SageMaker Real-Time Endpoint
                  (multi-model or multi-variant for A/B)
                          ↓
                  CloudWatch (latency / error metrics)
                  SageMaker Model Monitor (data drift)
```

**Key services**: SageMaker Endpoints, API Gateway, Lambda, CloudWatch, Auto Scaling

**Exam trigger**: "low latency inference", "real-time prediction", "A/B test models"

</details>

---

### 🔒 Security & Compliance

<details>
<summary><strong>Secure Multi-Tier VPC</strong></summary>

**Use case**: Isolate application tiers in separate subnets, restrict traffic with security groups and NACLs, and keep sensitive resources off the public internet.

```
Internet → IGW → Public Subnet (ALB, NAT Gateway, Bastion)
                      ↓ (security group rules)
               Private Subnet (EC2 app servers)
                      ↓
               Private Subnet (RDS, ElastiCache)
                      ↓
               VPC Endpoints → S3, DynamoDB, SSM (no internet)
```

**Key services**: VPC, Subnets, Security Groups, NACLs, IGW, NAT Gateway, VPC Endpoints, PrivateLink

**Exam trigger**: "private", "no public internet", "isolate tiers", "least privilege network"

</details>

---

<details>
<summary><strong>Centralized Logging & Threat Detection</strong></summary>

**Use case**: Aggregate all account activity, network traffic, and DNS logs in one place for security monitoring, compliance auditing, and automated threat response.

```
CloudTrail (API logs) ──┐
VPC Flow Logs        ──┤→ S3 (centralized log bucket)
Route 53 DNS logs    ──┘         ↓
                           GuardDuty (threat detection)
                                 ↓
                        EventBridge → Lambda (auto-remediation)
                        Security Hub (aggregated findings)
```

**Key services**: CloudTrail, VPC Flow Logs, GuardDuty, Security Hub, Macie, Config, EventBridge, SNS

**Exam trigger**: "audit", "compliance", "threat detection", "unauthorized access", "PII detection"

</details>

---

### 📈 Scaling & High Availability

<details>
<summary><strong>Auto-Scaling Behind a Load Balancer</strong></summary>

**Use case**: Handle variable traffic automatically by adding or removing EC2 instances (or containers) based on demand metrics, while distributing requests evenly.

```
Route 53 → ALB / NLB
               ↓
    EC2 Auto Scaling Group
    ├── Scale-out: CPU > 70% → launch instances
    ├── Scale-in:  CPU < 30% → terminate instances
    └── Health checks → replace unhealthy instances
               ↓
    RDS (Multi-AZ) + ElastiCache (read offload)
```

**Key services**: ALB/NLB, EC2 Auto Scaling, CloudWatch (target tracking), ElastiCache, RDS

**Exam trigger**: "scale automatically", "variable load", "cost-efficient", "replace unhealthy"

</details>

---

<details>
<summary><strong>Multi-Region Active-Active</strong></summary>

**Use case**: Serve global users with the nearest region, eliminate single-region SPOF, and achieve near-zero RTO/RPO.

```
Users → Route 53 (latency-based or geolocation routing)
            ├── Region A: ALB → EC2/ECS → Aurora Global (primary writer)
            └── Region B: ALB → EC2/ECS → Aurora Global (read replica → promote on failover)
                                   ↓
                          DynamoDB Global Tables (multi-region replication)
                          S3 Cross-Region Replication
```

**Key services**: Route 53, Aurora Global Database, DynamoDB Global Tables, S3 CRR, CloudFront, Global Accelerator

**Exam trigger**: "global users", "multi-region", "active-active", "latency routing", "zero downtime"

</details>

---

### 🏗️ Hybrid & On-Premises

<details>
<summary><strong>Hybrid Connectivity — Direct Connect vs VPN</strong></summary>

**Use case**: Extend an on-premises data center into AWS with a private, low-latency network connection for workloads that can't move fully to the cloud.

```
On-Premises DC
    ├── AWS Direct Connect → Direct Connect Gateway → VPC (private, dedicated line)
    │     (1–100 Gbps, consistent latency, no internet)
    └── AWS Site-to-Site VPN → Virtual Private Gateway → VPC
          (encrypted over internet, quick to set up, lower cost)

                Both options:
                VPC ← Private Subnets ← EC2 / RDS / EFS
```

| Factor | Direct Connect | Site-to-Site VPN |
|---|---|---|
| **Bandwidth** | 1–100 Gbps dedicated | Up to 1.25 Gbps |
| **Latency** | Consistent, low | Variable (internet) |
| **Setup time** | Weeks (physical) | Minutes |
| **Cost** | Higher | Lower |
| **Use when** | High throughput, compliance | Quick setup, backup path |

**Key services**: AWS Direct Connect, Direct Connect Gateway, Virtual Private Gateway, Transit Gateway, Site-to-Site VPN

**Exam trigger**: "on-premises", "data center", "dedicated connection", "hybrid", "consistent latency"

</details>

---

<details>
<summary><strong>Hybrid Storage — Storage Gateway</strong></summary>

**Use case**: Allow on-premises applications to use AWS cloud storage without changing existing workflows. Bridge local storage protocols (NFS, SMB, iSCSI) to S3 or EBS.

```
On-Premises App
    ├── File Gateway  (NFS/SMB) → S3 (files stored as objects, cached locally)
    ├── Volume Gateway (iSCSI)  → S3 snapshots / EBS (block storage)
    └── Tape Gateway  (VTL)     → S3 Glacier (virtual tape library for backups)
```

| Gateway Type | Protocol | Backed By | Use Case |
|---|---|---|---|
| File Gateway | NFS / SMB | S3 | File shares, data migration |
| Volume Gateway | iSCSI | S3 + EBS | Block storage, DR snapshots |
| Tape Gateway | VTL | S3 Glacier | Replace physical tape backups |

**Key services**: AWS Storage Gateway, S3, S3 Glacier, EBS

**Exam trigger**: "on-prem file share to cloud", "replace tape backups", "NFS to S3", "iSCSI"

</details>

---

<details>
<summary><strong>Large-Scale Data Migration to AWS</strong></summary>

**Use case**: Move terabytes to petabytes of data from on-premises into AWS when network transfer alone is too slow or costly.

```
Volume < 10 TB / good bandwidth:
    On-Prem → AWS DataSync (agent) → S3 / EFS / FSx

Volume 10 TB – 80 TB:
    On-Prem → AWS Snowball Edge (physical device) → S3

Volume > 80 TB / petabyte-scale:
    On-Prem → AWS Snowmobile (truck) → S3

Ongoing DB replication:
    On-Prem DB → AWS DMS → RDS / Aurora / Redshift
```

**Key services**: AWS DataSync, AWS Snowball Edge, AWS Snowmobile, AWS DMS, S3

**Exam trigger**: "migrate data", "terabytes", "petabytes", "bandwidth limited", "offline transfer"

</details>

---

<details>
<summary><strong>Outposts — AWS Infrastructure On-Premises</strong></summary>

**Use case**: Run AWS services physically inside your own data center for workloads that require ultra-low latency to on-prem systems, local data residency, or cannot be moved to the cloud.

```
Your Data Center
    └── AWS Outpost Rack (AWS-managed hardware)
          ├── EC2 instances (same APIs as cloud)
          ├── ECS / EKS (containers on-prem)
          ├── RDS on Outposts (local database)
          └── S3 on Outposts (local object storage)
                ↓ (private connectivity)
          AWS Region (for management plane, other services)
```

**Key services**: AWS Outposts, EC2, ECS, RDS on Outposts, S3 on Outposts

**Exam trigger**: "on-prem latency", "data residency", "local processing", "Outposts", "same AWS APIs on-prem"

</details>

---

### 💰 Cost Optimization

<details>
<summary><strong>Spot Instance Fleet for Batch Workloads</strong></summary>

**Use case**: Run fault-tolerant, flexible batch jobs (ML training, data processing, CI/CD, rendering) at up to 90% discount vs On-Demand by using spare EC2 capacity.

```
Job Scheduler (AWS Batch / SQS queue)
    → EC2 Spot Fleet (mixed instance types + AZs for capacity)
          ├── Spot interruption → checkpoint to S3 → resume on new instance
          ├── On-Demand instances (small %, baseline guarantee)
          └── Spot Instance Advisor: pick instances with < 5% interruption rate
    → Results → S3 / DynamoDB
```

**Key services**: EC2 Spot Fleet, AWS Batch, SQS, S3 (checkpointing), Auto Scaling (mixed policy)

**Exam trigger**: "cheapest compute", "batch processing", "fault tolerant", "flexible start time", "90% savings"

</details>

---

<details>
<summary><strong>S3 Storage Lifecycle & Intelligent Tiering</strong></summary>

**Use case**: Automatically move objects to cheaper storage classes as they age, or let AWS determine the optimal tier based on access patterns — without changing application code.

```
S3 Object Created (Standard)
    → 30 days  → S3 Standard-IA (infrequent access)
    → 90 days  → S3 Glacier Instant Retrieval
    → 180 days → S3 Glacier Flexible Retrieval
    → 365 days → S3 Glacier Deep Archive (cheapest)

        OR

S3 Intelligent-Tiering (unknown access patterns):
    Frequent Access tier ↔ Infrequent Access tier ↔ Archive tiers
    (AWS moves objects automatically based on 30-day access pattern)
```

| Storage Class | Min Duration | Retrieval | Cost vs Standard |
|---|---|---|---|
| Standard | None | Instant | Baseline |
| Standard-IA | 30 days | Instant | ~58% cheaper |
| Glacier Instant | 90 days | Instant | ~68% cheaper |
| Glacier Flexible | 90 days | Minutes–hours | ~85% cheaper |
| Glacier Deep Archive | 180 days | 12–48 hrs | ~95% cheaper |

**Key services**: S3 Lifecycle Policies, S3 Intelligent-Tiering, S3 Glacier

**Exam trigger**: "reduce storage cost", "old data", "archive", "infrequent access", "lifecycle"

</details>

---

<details>
<summary><strong>Serverless-First for Cost Efficiency</strong></summary>

**Use case**: Replace always-on EC2 instances with pay-per-use serverless services for workloads with variable or intermittent traffic — eliminate idle cost entirely.

```
Instead of:  EC2 (running 24/7, ~$50-200/mo idle)
Use:         Lambda (pay only per invocation, free tier: 1M req/mo)

Instead of:  RDS always-on instance
Use:         DynamoDB on-demand (pay per read/write)
             Aurora Serverless v2 (scales to zero when idle)

Instead of:  EC2 + Nginx for APIs
Use:         API Gateway (pay per API call)

Instead of:  Self-managed Kafka on EC2
Use:         Kinesis Firehose or MSK Serverless
```

**Key services**: Lambda, API Gateway, DynamoDB on-demand, Aurora Serverless v2, Fargate, MSK Serverless

**Exam trigger**: "variable traffic", "reduce idle cost", "pay per use", "scale to zero", "unpredictable load"

</details>

---

<details>
<summary><strong>Reserved Capacity & Savings Plans</strong></summary>

**Use case**: Commit to consistent, predictable usage to get 30–72% discount vs On-Demand for production workloads that run continuously.

```
Commitment options (choose based on flexibility needed):

Compute Savings Plans (most flexible)
    → 66% discount, applies to any EC2 family/region/OS + Lambda + Fargate

EC2 Instance Savings Plans (less flexible)
    → 72% discount, locked to instance family + region

Reserved Instances (RDS, ElastiCache, Redshift, OpenSearch)
    → 30-60% discount, locked to instance type + region

Spot Instances (interruptible)
    → up to 90% discount, for fault-tolerant batch/flexible jobs
```

| Option | Discount | Flexibility | Commitment |
|---|---|---|---|
| On-Demand | 0% | Maximum | None |
| Compute Savings Plan | ~66% | High | 1–3 yr |
| EC2 Instance Savings Plan | ~72% | Medium | 1–3 yr |
| Reserved Instance | 30–60% | Low | 1–3 yr |
| Spot | ~90% | Low (interruptible) | None |

**Key services**: AWS Cost Explorer, Savings Plans, Reserved Instances, Trusted Advisor, AWS Budgets

**Exam trigger**: "steady-state workload", "predictable usage", "reduce EC2 cost", "1-year commit", "3-year commit"

</details>

---

<details>
<summary><strong>Right-Sizing & Waste Elimination</strong></summary>

**Use case**: Identify and eliminate over-provisioned, idle, or orphaned resources to reduce AWS bills without changing architecture.

```
Discovery → AWS Trusted Advisor (idle EC2, underutilized RDS, unattached EBS)
          → AWS Compute Optimizer (right-size EC2, Lambda, ECS, Auto Scaling)
          → AWS Cost Explorer (per-service spend breakdown, anomaly detection)

Actions:
    Over-provisioned EC2     → downsize instance type or move to Graviton
    Idle RDS instance        → use Aurora Serverless or snapshot + delete
    Unattached EBS volumes   → delete or snapshot + delete
    Old EBS snapshots        → lifecycle policy to expire
    NAT Gateway data charges → use VPC Endpoints for S3/DynamoDB traffic
    Data transfer costs      → use CloudFront, keep traffic within region
```

**Key services**: AWS Trusted Advisor, AWS Compute Optimizer, AWS Cost Explorer, AWS Budgets, CloudWatch

**Exam trigger**: "reduce AWS bill", "idle resources", "right-size", "Trusted Advisor", "Compute Optimizer"

</details>

---

## Architecture Decision Tree

```
What is the primary workload type?
│
├── Web / API serving
│   ├── Static content only → S3 + CloudFront + Route 53
│   ├── Dynamic, server-based → EC2 (ASG) + ALB + RDS Multi-AZ
│   └── Serverless / event-driven → API Gateway + Lambda + DynamoDB
│
├── Containers
│   ├── Need Kubernetes / existing K8s workloads → EKS
│   ├── AWS-native Docker containers, no K8s → ECS Fargate
│   └── Containers + on-prem local processing → ECS on Outposts
│
├── Data & Analytics
│   ├── Batch ETL + ad-hoc queries → S3 + Glue + Athena
│   ├── Real-time streaming → Kinesis Streams + Lambda/Flink + Firehose
│   ├── Data warehouse (structured, BI) → Redshift + QuickSight
│   └── ML pipeline → SageMaker + S3 + Feature Store
│
├── Messaging & Decoupling
│   ├── Point-to-point async queue → SQS
│   ├── Fan-out / pub-sub → SNS → SQS (fan-out pattern)
│   ├── Event routing / cross-service → EventBridge
│   └── Complex workflow with branching → Step Functions
│
├── Storage
│   ├── Object storage (datasets, backups, static) → S3
│   ├── Block storage (single EC2 fast disk) → EBS
│   ├── Shared file system (multi-instance NFS) → EFS
│   ├── High-throughput ML training → FSx for Lustre
│   └── NoSQL low-latency lookups → DynamoDB
│
├── Hybrid / On-Premises
│   ├── Dedicated high-bandwidth connection → Direct Connect
│   ├── Quick / backup VPN connection → Site-to-Site VPN
│   ├── On-prem file share → cloud → Storage Gateway (File)
│   ├── Replace tape backups → Storage Gateway (Tape) + Glacier
│   ├── Migrate TBs of data (network ok) → DataSync
│   ├── Migrate TBs offline → Snowball Edge
│   ├── Migrate petabytes → Snowmobile
│   └── Run AWS APIs on-prem → Outposts
│
├── Security & Compliance
│   ├── Isolate tiers from internet → VPC + Private Subnets + NAT GW
│   ├── Audit all API activity → CloudTrail + S3
│   ├── Detect threats automatically → GuardDuty + EventBridge + Lambda
│   ├── Detect PII/sensitive data → Macie
│   └── Centralize findings → Security Hub
│
├── Cost Optimization
│   ├── Batch / fault-tolerant workloads → EC2 Spot Fleet
│   ├── Aging / infrequent data → S3 Lifecycle + Glacier
│   ├── Variable / spiky traffic → Serverless (Lambda + DynamoDB + API GW)
│   ├── Steady-state 24/7 workloads → Savings Plans / Reserved Instances
│   └── Idle / over-provisioned resources → Trusted Advisor + Compute Optimizer
│
└── High Availability & Scale
    ├── Variable traffic, single region → EC2 ASG + ALB + RDS Multi-AZ
    ├── Global users, low latency → CloudFront + Global Accelerator + Route 53
    ├── Multi-region failover (active-passive) → Aurora Global + Route 53 failover
    └── Multi-region active-active → DynamoDB Global Tables + Aurora Global + Route 53 latency
```

---

## AWS Well-Architected Framework — Quick Reference

The six pillars to evaluate any architecture against:

| Pillar | Core Question | Key AWS Tools |
|---|---|---|
| **Operational Excellence** | Can you run and monitor systems effectively? | CloudWatch, CloudTrail, Config, Systems Manager |
| **Security** | Are workloads protected at every layer? | IAM, KMS, GuardDuty, Security Hub, WAF, Shield |
| **Reliability** | Can the system recover from failures? | Multi-AZ, Auto Scaling, Route 53, AWS Backup |
| **Performance Efficiency** | Are you using resources optimally? | EC2 right-sizing, ElastiCache, CloudFront, SageMaker |
| **Cost Optimization** | Are you avoiding unnecessary spend? | Spot Instances, Savings Plans, S3 lifecycle, Trusted Advisor |
| **Sustainability** | Are you minimizing environmental impact? | Graviton instances, serverless, right-sizing |

---

## Common Anti-Patterns to Avoid

| Anti-Pattern | Problem | Better Approach |
|---|---|---|
| Single AZ deployment | One hardware failure kills everything | Multi-AZ for all stateful resources |
| Hardcoded credentials in code | Security breach if code is exposed | IAM roles + Secrets Manager |
| Polling instead of events | Wasted compute, higher cost | SQS / SNS / EventBridge |
| One giant monolith Lambda | Cold starts, timeout limits, hard to debug | Break into smaller focused functions |
| Public S3 bucket | Data exposure | Block public access + bucket policies |
| Over-provisioned EC2 | Cost waste | Right-size + Auto Scaling + Spot |
| No data encryption | Compliance failure | KMS at rest + TLS in transit |
