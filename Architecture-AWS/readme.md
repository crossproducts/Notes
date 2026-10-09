# Architecture-AWS

101 AWS architectures, each one distinct, each written to be used rather than admired.

Every architecture gets its own page with a rendered diagram, a component table that
names *the setting that actually matters*, a request/data flow, cost at three scales,
failure modes, security notes, and a **"what people miss"** section — the detail that
turns a working design into one that survives contact with production.

## How to read this

| Field | Meaning |
|---|---|
| **Maturity** | `Production` — well-trodden, safe default · `Growing` — solid but evolving fast · `Specialist` — right for a narrow problem, wrong as a default |
| **Effort** | `S` — days · `M` — weeks · `L` — a quarter or more, usually with more than one team |
| **Cost** | `us-east-1`, on-demand, no commitments, priced at three scales so the *shape* of the curve is visible. Treat as an order of magnitude, not a quote. |

Diagrams are `.drawio.svg` files: GitHub renders them inline, and the same file opens
as an editable diagram in the draw.io VS Code extension. See
[the plugin notes](../Architecture/Diagrams/drawio-plugin.md).

### The visual language

Colour means *type of thing*, line style means *type of relationship* — consistent
across all 101 diagrams.

| Colour | Meaning | | Line | Meaning |
|---|---|---|---|---|
| 🔵 blue | edge, gateway, CDN, DNS | | solid blue | synchronous call |
| 🟢 green | compute | | dashed purple | async / event |
| 🟠 amber | storage and databases | | solid amber | bulk data movement |
| 🟣 purple | queues, topics, streams | | dotted grey | telemetry |
| 🔷 teal | AI/ML | | dashed red | security control |
| ⚪ grey | observability and ops | | | |
| 🔴 red | security services | | | |
| ⬜ white | systems outside AWS | | | |

## Reading paths

Rather than reading 101 pages in order, follow the one that matches what you are
actually doing.

- **Ship a web app on AWS** · [`aws-028`](aws-028-three-tier-vpc.md) → [`aws-010`](aws-010-serverless-crud.md) → [`aws-002`](aws-002-cognito-oidc-spa.md) → [`aws-003`](aws-003-cloudfront-s3-oac.md) → [`aws-066`](aws-066-cloudwatch-core.md) → [`aws-094`](aws-094-budgets-anomaly.md)
- **Expose an API to the outside world** · [`aws-001`](aws-001-lambda-authorizer.md) → [`aws-005`](aws-005-api-abuse-control.md) → [`aws-009`](aws-009-api-canary-deploys.md) → [`aws-008`](aws-008-m2m-auth.md) → [`aws-063`](aws-063-ddos-defense.md)
- **Run containers without regret** · [`aws-019`](aws-019-ecs-fargate-alb.md) → [`aws-020`](aws-020-eks-baseline.md) → [`aws-022`](aws-022-karpenter-spot.md) → [`aws-021`](aws-021-eks-gitops-argocd.md) → [`aws-025`](aws-025-progressive-delivery.md)
- **Build a data platform** · [`aws-037`](aws-037-s3-data-lake.md) → [`aws-041`](aws-041-iceberg-tables.md) → [`aws-038`](aws-038-glue-etl.md) → [`aws-044`](aws-044-cdc-dms.md) → [`aws-046`](aws-046-data-quality-contracts.md) → [`aws-045`](aws-045-quicksight-rls.md)
- **Go real-time** · [`aws-051`](aws-051-clickstream-firehose.md) → [`aws-047`](aws-047-kinesis-lambda.md) → [`aws-050`](aws-050-flink-stateful.md) → [`aws-048`](aws-048-vpc-flow-flink.md)
- **Pass a security audit** · [`aws-057`](aws-057-immutable-audit-trail.md) → [`aws-061`](aws-061-config-compliance.md) → [`aws-060`](aws-060-identity-center-abac.md) → [`aws-055`](aws-055-security-lake.md) → [`aws-064`](aws-064-shift-left-security.md)
- **Stop being paged at 3am** · [`aws-066`](aws-066-cloudwatch-core.md) → [`aws-072`](aws-072-slo-error-budgets.md) → [`aws-065`](aws-065-notification-bus.md) → [`aws-071`](aws-071-self-healing-ops.md) → [`aws-070`](aws-070-chaos-fis.md)
- **Put a model in production** · [`aws-075`](aws-075-llm-gateway.md) → [`aws-073`](aws-073-bedrock-rag.md) → [`aws-077`](aws-077-inference-selection.md) → [`aws-081`](aws-081-mlops-pipelines.md)
- **Survive losing a region** · [`aws-087`](aws-087-dr-pilot-light.md) → [`aws-085`](aws-085-aurora-global.md) → [`aws-086`](aws-086-ddb-global-tables.md) → [`aws-083`](aws-083-s3-replication-worm.md) → [`aws-084`](aws-084-aws-backup-org.md)
- **Get the bill under control** · [`aws-092`](aws-092-finops-cur-pipeline.md) → [`aws-095`](aws-095-rightsizing-waste.md) → [`aws-093`](aws-093-commitment-strategy.md) → [`aws-030`](aws-030-centralized-egress.md) → [`aws-082`](aws-082-s3-lifecycle.md)

## The 101

[Edge, API & Identity](#01) (9) · [Serverless Application Patterns](#02) (9) · [Containers & Orchestration](#03) (9) · [Networking & Connectivity](#04) (9) · [Data Engineering & Analytics](#05) (10) · [Streaming & Real-Time](#06) (8) · [Security, Detection & Response](#07) (10) · [Observability & Operations](#08) (8) · [AI/ML & Generative AI](#09) (9) · [Storage, Backup & Resilience](#10) (8) · [Cost, Governance & Multi-Account](#11) (6) · [Migration, Hybrid & Edge](#12) (6)

### <a id="01"></a>01 · Edge, API & Identity

*Everything in front of your compute: who is calling, are they allowed, and how fast.*

| ID | Architecture | What it gives you | Maturity | Effort |
|---|---|---|---|---|
| `001` | [API Gateway + Lambda Authorizer](aws-001-lambda-authorizer.md) | Custom token/context auth at the edge, with the policy cache that makes or breaks its cost. | Production | S |
| `002` | [Cognito OIDC for SPA + API](aws-002-cognito-oidc-spa.md) | Hosted-UI login, federated IdPs, JWT authorizer - the default identity stack for a web app. | Production | S |
| `003` | [CloudFront + S3 static site with OAC](aws-003-cloudfront-s3-oac.md) | Private bucket, Origin Access Control, cert in us-east-1, and cache invalidation discipline. | Production | S |
| `004` | [Edge personalization: CloudFront Functions vs Lambda@Edge](aws-004-edge-personalization.md) | Where to run edge logic, what each tier can and cannot do, and how cache keys explode. | Growing | S |
| `005` | [Public API abuse control: WAF + usage plans + Shield](aws-005-api-abuse-control.md) | Layered rate limiting, bot control, and getting WAF logs somewhere you can tune rules from. | Production | M |
| `006` | [Private API Gateway for internal consumers](aws-006-private-api-gateway.md) | execute-api VPC endpoints, resource policies and split-horizon DNS, with no internet path. | Production | M |
| `007` | [mTLS partner API with ACM Private CA](aws-007-mtls-partner-api.md) | Client-certificate auth for B2B, truststore rotation, and mapping a cert subject to a tenant. | Specialist | M |
| `008` | [Machine-to-machine auth: client credentials vs SigV4](aws-008-m2m-auth.md) | When to use OAuth client_credentials, when to use IAM, and why mixing them is usually right. | Production | S |
| `009` | [API versioning, canary and blue-green at the gateway](aws-009-api-canary-deploys.md) | Stage variables, canary splits, Lambda aliases and automatic rollback on a 5xx alarm. | Production | M |

### <a id="02"></a>02 · Serverless Application Patterns

*Lambda-shaped application topologies - the ones worth copying, and their sharp edges.*

| ID | Architecture | What it gives you | Maturity | Effort |
|---|---|---|---|---|
| `010` | [Serverless CRUD: HTTP API + Lambda + DynamoDB single-table](aws-010-serverless-crud.md) | The reference three-tier serverless app, including the single-table design people avoid. | Production | S |
| `011` | [Step Functions saga for long-running workflows](aws-011-step-functions-saga.md) | Distributed transactions with compensation, and why Express vs Standard changes everything. | Production | M |
| `012` | [Async job submission with SQS + status polling](aws-012-async-job-submission.md) | Accept-202 APIs, idempotency keys, DLQs, and giving clients a job status they can trust. | Production | S |
| `013` | [Fan-out / fan-in with SNS + SQS + aggregation](aws-013-fanout-fanin.md) | Topic-per-event-type, per-consumer queues, and rejoining parallel results without a race. | Production | M |
| `014` | [Scheduled workloads with EventBridge Scheduler](aws-014-eventbridge-scheduler.md) | One-shot and recurring schedules at millions of targets - the cron replacement people miss. | Production | S |
| `015` | [Upload pipeline: presigned URLs + S3 events](aws-015-s3-upload-pipeline.md) | Direct-to-S3 uploads that skip your compute, with virus scanning and a post-process chain. | Production | S |
| `016` | [Serverless WebSockets with API Gateway](aws-016-serverless-websockets.md) | Connection tables, broadcast fan-out, and the stale-connection cleanup nobody plans for. | Growing | M |
| `017` | [AppSync GraphQL with subscriptions](aws-017-appsync-graphql.md) | Managed GraphQL, direct resolvers that skip Lambda, and real-time subscriptions over WS. | Growing | M |
| `018` | [Lambda + RDS Proxy for relational-backed serverless](aws-018-lambda-rds-proxy.md) | Surviving connection storms, IAM auth to the database, and when Aurora Serverless v2 wins. | Production | M |

### <a id="03"></a>03 · Containers & Orchestration

*ECS and EKS from the boring default to multi-tenant platform engineering.*

| ID | Architecture | What it gives you | Maturity | Effort |
|---|---|---|---|---|
| `019` | [ECS Fargate service behind an ALB](aws-019-ecs-fargate-alb.md) | The boring default that is right far more often than EKS - deploys, scaling, and health checks. | Production | S |
| `020` | [EKS cluster baseline: node groups, IRSA, add-ons](aws-020-eks-baseline.md) | A cluster you can actually hand to a team: identity, networking, add-on lifecycle, upgrades. | Production | M |
| `021` | [EKS GitOps with Argo CD app-of-apps](aws-021-eks-gitops-argocd.md) | Declarative delivery, drift detection, and the bootstrap chicken-and-egg problem. | Production | M |
| `022` | [Karpenter autoscaling with Spot and consolidation](aws-022-karpenter-spot.md) | Right-sized nodes in seconds, Spot interruption handling, and consolidation that actually saves. | Production | M |
| `023` | [EKS multi-tenancy: namespaces, quotas, network policy](aws-023-eks-multi-tenancy.md) | Soft tenancy done properly - and an honest account of where it stops being enough. | Growing | L |
| `024` | [Service mesh on EKS for mTLS and traffic shifting](aws-024-service-mesh.md) | Sidecar vs ambient, what a mesh buys you over an ALB, and the latency you pay for it. | Specialist | L |
| `025` | [Progressive delivery: canary and blue-green containers](aws-025-progressive-delivery.md) | Argo Rollouts / CodeDeploy traffic shifting driven by real SLO metrics, not a timer. | Growing | M |
| `026` | [Batch compute at scale with AWS Batch on Spot](aws-026-aws-batch.md) | Job queues, array jobs, fair-share scheduling, and 70-90% savings on interruptible work. | Production | M |
| `027` | [Container supply chain: ECR scanning, signing, admission](aws-027-container-supply-chain.md) | SBOMs, image signing, and an admission controller that refuses unsigned or critical-CVE images. | Growing | M |

### <a id="04"></a>04 · Networking & Connectivity

*VPC design, cross-account reach, hybrid links, and the NAT Gateway bill.*

| ID | Architecture | What it gives you | Maturity | Effort |
|---|---|---|---|---|
| `028` | [Multi-AZ three-tier VPC](aws-028-three-tier-vpc.md) | Public/private/isolated subnets, route tables, and sizing CIDRs you will not regret. | Production | S |
| `029` | [Transit Gateway hub-and-spoke](aws-029-transit-gateway-hub.md) | Cross-account and cross-region routing with route-table segmentation instead of peering mesh. | Production | M |
| `030` | [Centralized egress VPC with inspection](aws-030-centralized-egress.md) | One NAT path for the whole org, traffic inspection, and the cost model that justifies it. | Production | M |
| `031` | [PrivateLink service exposure](aws-031-privatelink.md) | Publishing a service to other accounts/VPCs with no routing, no peering, no overlapping-CIDR pain. | Production | M |
| `032` | [Hybrid connectivity: Direct Connect + VPN failover](aws-032-hybrid-dx-vpn.md) | Resilient on-prem links, BGP path preference, and testing the failover before it tests you. | Production | L |
| `033` | [Route 53 routing strategies and private DNS](aws-033-route53-strategies.md) | Failover, latency, weighted and geo routing, plus private hosted zones across accounts. | Production | S |
| `034` | [Global Accelerator anycast front door](aws-034-global-accelerator.md) | Static anycast IPs, TCP/UDP acceleration, and fast regional failover for non-HTTP workloads. | Specialist | S |
| `035` | [IPAM-managed address planning and IPv6](aws-035-ipam-ipv6.md) | Stopping CIDR collisions before they happen, and dual-stack without the NAT bill. | Growing | M |
| `036` | [Egress filtering with AWS Network Firewall](aws-036-network-firewall-egress.md) | Domain allow-lists, Suricata rules, and proving data cannot walk out of the VPC. | Growing | M |

### <a id="05"></a>05 · Data Engineering & Analytics

*Batch-shaped data: lakes, catalogs, warehouses, transforms and BI.*

| ID | Architecture | What it gives you | Maturity | Effort |
|---|---|---|---|---|
| `037` | [S3 data lake with medallion layout + Lake Formation](aws-037-s3-data-lake.md) | Bronze/silver/gold zoning, partitioning that Athena likes, and fine-grained table permissions. | Production | M |
| `038` | [Glue ETL with Data Catalog and crawlers](aws-038-glue-etl.md) | Serverless Spark for batch transforms, catalog hygiene, and when crawlers stop being a good idea. | Production | M |
| `039` | [Athena federated query and ad-hoc analytics](aws-039-athena-federated.md) | Querying RDS, DynamoDB and the lake in one SQL statement - and controlling the scan bill. | Growing | S |
| `040` | [Redshift Serverless + zero-ETL ingestion](aws-040-redshift-zero-etl.md) | A warehouse with no cluster to babysit, fed from Aurora without a pipeline you maintain. | Growing | M |
| `041` | [Apache Iceberg tables on S3](aws-041-iceberg-tables.md) | ACID, schema evolution and time travel on object storage - plus compaction you must schedule. | Growing | M |
| `042` | [EMR Serverless for heavy Spark batch](aws-042-emr-serverless.md) | When Glue runs out of room: tuned Spark, custom runtimes, and per-second capacity. | Production | M |
| `043` | [Pipeline orchestration with MWAA (Airflow)](aws-043-mwaa-orchestration.md) | DAGs over Step Functions, dependency-heavy schedules, and the baseline cost you accept for it. | Production | M |
| `044` | [Change data capture from Aurora with DMS](aws-044-cdc-dms.md) | Replicating operational changes into the lake continuously, including the schema-drift trap. | Production | M |
| `045` | [QuickSight BI with row-level security](aws-045-quicksight-rls.md) | Dashboards non-engineers trust, SPICE refresh economics, and per-tenant data isolation. | Growing | S |
| `046` | [Data quality gates and contracts](aws-046-data-quality-contracts.md) | Glue Data Quality rules that fail a pipeline loudly instead of poisoning the gold layer quietly. | Growing | M |

### <a id="06"></a>06 · Streaming & Real-Time

*Data in motion - Kinesis, MSK, Flink, and the latency/cost trade they force.*

| ID | Architecture | What it gives you | Maturity | Effort |
|---|---|---|---|---|
| `047` | [Kinesis Data Streams -> Lambda consumer](aws-047-kinesis-lambda.md) | Shard math, batching, parallelization factor, and the poison-pill failure every team hits once. | Production | S |
| `048` | [VPC Flow Logs -> Kinesis -> Managed Flink real-time analytics](aws-048-vpc-flow-flink.md) | Windowed network analytics in seconds: top talkers, rejected flows, exfil-shaped egress spikes. | Specialist | L |
| `049` | [MSK (Kafka) with MSK Connect](aws-049-msk-kafka.md) | When you genuinely need Kafka semantics, what it costs, and sink connectors without custom code. | Production | L |
| `050` | [Managed Flink stateful stream processing](aws-050-flink-stateful.md) | Event-time windows, watermarks, exactly-once sinks, and checkpoint/savepoint operations. | Specialist | L |
| `051` | [Clickstream ingestion with Firehose](aws-051-clickstream-firehose.md) | Buffer-to-S3 in Parquet, dynamic partitioning, and the zero-ops path for high-volume events. | Production | S |
| `052` | [IoT Core telemetry to Timestream](aws-052-iot-telemetry.md) | Device identity at scale, rules-engine routing, and a time-series store that does not melt. | Specialist | M |
| `053` | [DynamoDB Streams to materialized views](aws-053-ddb-streams-views.md) | CQRS on DynamoDB: derived read models, search indexes, and ordering guarantees per key. | Production | M |
| `054` | [Real-time counters and leaderboards](aws-054-realtime-counters.md) | ElastiCache sorted sets plus a durable backing store, and avoiding the hot-partition cliff. | Growing | M |

### <a id="07"></a>07 · Security, Detection & Response

*Preventive guardrails, detective controls, and what happens at 3am.*

| ID | Architecture | What it gives you | Maturity | Effort |
|---|---|---|---|---|
| `055` | [Amazon Security Lake with OCSF normalization](aws-055-security-lake.md) | Org-wide security telemetry normalized to one schema in your own S3, queryable from Athena. | Growing | L |
| `056` | [GuardDuty + Detective with automated containment](aws-056-guardduty-response.md) | Finding to containment in under a minute, with a human approval gate where it belongs. | Production | M |
| `057` | [Organization CloudTrail with an immutable archive](aws-057-immutable-audit-trail.md) | Tamper-evident audit logs in a separate account, Object Lock, and detecting trail tampering. | Production | M |
| `058` | [Secrets Manager rotation and Parameter Store](aws-058-secrets-rotation.md) | Automatic rotation that does not break the app, and the cost reason to split the two stores. | Production | S |
| `059` | [KMS key hierarchy and envelope encryption](aws-059-kms-key-hierarchy.md) | Key-per-domain design, grants vs policies, multi-region keys, and the request-cost surprise. | Production | M |
| `060` | [IAM Identity Center with permission sets and ABAC](aws-060-identity-center-abac.md) | Human access that scales past 20 accounts without a per-account IAM user in sight. | Production | M |
| `061` | [Config conformance packs for continuous compliance](aws-061-config-compliance.md) | Continuous evidence instead of an annual scramble, with auto-remediation where it is safe. | Production | M |
| `062` | [Incident response automation with SSM](aws-062-ir-automation.md) | Instance isolation, memory capture and credential revocation as a runbook, not a hero. | Growing | M |
| `063` | [WAF + Shield Advanced DDoS defense](aws-063-ddos-defense.md) | Layer 3-7 protection, cost protection, and the response-team escalation path. | Specialist | M |
| `064` | [Pre-deploy security gates: IaC scan, Inspector, SBOM](aws-064-shift-left-security.md) | Catching the misconfiguration in the PR, not in the CSPM dashboard three weeks later. | Growing | M |

### <a id="08"></a>08 · Observability & Operations

*Knowing the system is sick before your users tell you, and reacting without a human.*

| ID | Architecture | What it gives you | Maturity | Effort |
|---|---|---|---|---|
| `065` | [Notification bus: EventBridge -> SNS/SQS -> Lambda -> Slack/Mattermost](aws-065-notification-bus.md) | One event spine for every alert, with routing, dedupe, severity and a chat destination. | Production | M |
| `066` | [CloudWatch done properly: metrics, Logs Insights, composite alarms](aws-066-cloudwatch-core.md) | Escaping alert fatigue with composite alarms and metric filters, and controlling ingest cost. | Production | S |
| `067` | [OpenTelemetry with ADOT to X-Ray / Prometheus / Grafana](aws-067-otel-adot.md) | One instrumentation standard, three backends, and keeping the collector from becoming the SPOF. | Growing | M |
| `068` | [Centralized logging to OpenSearch with ISM](aws-068-centralized-logging.md) | Org-wide log aggregation, index lifecycle to keep it affordable, and when to use S3 instead. | Production | M |
| `069` | [Synthetic canaries and RUM for user-facing SLOs](aws-069-synthetics-rum.md) | Knowing the site is broken before a user tells you, from both outside and inside the browser. | Growing | S |
| `070` | [Chaos engineering with Fault Injection Service](aws-070-chaos-fis.md) | Proving the failover works by breaking it on purpose, with a stop condition wired to an alarm. | Specialist | M |
| `071` | [Self-healing operations with SSM + EventBridge](aws-071-self-healing-ops.md) | Common incidents resolved by automation, with every action auditable and reversible. | Growing | M |
| `072` | [SLO and error-budget dashboards with on-call routing](aws-072-slo-error-budgets.md) | Alerting on burn rate rather than thresholds, and routing by service ownership. | Growing | M |

### <a id="09"></a>09 · AI/ML & Generative AI

*Bedrock, SageMaker, RAG and the operational scaffolding production models need.*

| ID | Architecture | What it gives you | Maturity | Effort |
|---|---|---|---|---|
| `073` | [Bedrock RAG with Knowledge Bases and a vector store](aws-073-bedrock-rag.md) | Chunking, embeddings, retrieval quality and the evaluation loop most RAG builds skip. | Growing | M |
| `074` | [Bedrock Agents with action groups and tool use](aws-074-bedrock-agents.md) | Letting a model call your APIs safely: schemas, confirmation gates, and session state. | Growing | M |
| `075` | [LLM gateway: quotas, caching, guardrails, cost attribution](aws-075-llm-gateway.md) | One front door for every model call, so you can rate-limit, cache, log and bill per team. | Growing | M |
| `076` | [SageMaker training to model registry to endpoint](aws-076-sagemaker-training.md) | A training path that produces a versioned, approvable, redeployable artifact. | Production | L |
| `077` | [Choosing an inference mode: real-time, serverless, async, batch](aws-077-inference-selection.md) | The four SageMaker inference options, their cold-start and cost profiles, and how to pick. | Production | M |
| `078` | [Feature store and training/serving skew control](aws-078-feature-store.md) | One definition of a feature for both training and inference, with point-in-time correctness. | Specialist | L |
| `079` | [Document intelligence: Textract + Comprehend + human review](aws-079-document-intelligence.md) | Extraction with a confidence threshold that routes the hard 5% to a person, not to production. | Production | M |
| `080` | [Multimodal media pipeline: Transcribe, Rekognition, Translate](aws-080-media-pipeline.md) | Turning audio and video into searchable, moderated, translated text with Step Functions glue. | Growing | M |
| `081` | [MLOps: SageMaker Pipelines with drift monitoring](aws-081-mlops-pipelines.md) | CI/CD for models, automatic retraining triggers, and catching drift before the business does. | Growing | L |

### <a id="10"></a>10 · Storage, Backup & Resilience

*Durability, lifecycle, multi-region, and DR you have actually tested.*

| ID | Architecture | What it gives you | Maturity | Effort |
|---|---|---|---|---|
| `082` | [S3 storage classes, lifecycle and Intelligent-Tiering](aws-082-s3-lifecycle.md) | Matching class to access pattern, and the retrieval/transition costs that eat the savings. | Production | S |
| `083` | [Cross-region replication and Object Lock (WORM)](aws-083-s3-replication-worm.md) | Compliance-grade immutability, replication lag reality, and the ransomware recovery story. | Production | M |
| `084` | [Organization-wide AWS Backup with vault lock](aws-084-aws-backup-org.md) | Centrally enforced backup policy no account can opt out of, plus restore testing. | Production | M |
| `085` | [Aurora Global Database multi-region](aws-085-aurora-global.md) | Sub-second cross-region replication, managed failover, and the write-latency truth. | Production | L |
| `086` | [DynamoDB global tables active-active](aws-086-ddb-global-tables.md) | Multi-region writes, last-writer-wins conflict resolution, and designing around it. | Production | M |
| `087` | [Pilot light / warm standby DR with Route 53 ARC](aws-087-dr-pilot-light.md) | Picking an RTO/RPO you can afford, and proving it with a routing control you rehearse. | Production | L |
| `088` | [Shared file storage: EFS vs FSx vs S3](aws-088-shared-file-storage.md) | Choosing by access pattern and protocol instead of by habit, with the throughput-mode trap. | Production | S |
| `089` | [Bulk data transfer: DataSync, Snowball, Transfer Family](aws-089-bulk-data-transfer.md) | Moving petabytes without saturating your link, and the sneakernet math that still wins. | Production | M |

### <a id="11"></a>11 · Cost, Governance & Multi-Account

*Landing zones, guardrails, and making spend legible to the people who cause it.*

| ID | Architecture | What it gives you | Maturity | Effort |
|---|---|---|---|---|
| `090` | [Control Tower landing zone and account factory](aws-090-landing-zone.md) | A new account that is compliant on minute one, and the OU structure to put it in. | Production | L |
| `091` | [SCPs, OU design and preventive guardrails](aws-091-scp-guardrails.md) | Making the wrong thing impossible rather than detectable, without bricking your builders. | Production | M |
| `092` | [FinOps pipeline: CUR 2.0 + Athena + tag enforcement](aws-092-finops-cur-pipeline.md) | Turning the billing export into per-team answers, and enforcing the tags that make it possible. | Production | M |
| `093` | [Savings Plans and RI portfolio strategy](aws-093-commitment-strategy.md) | Laddered commitments sized to a baseline you measured, not to last month's peak. | Production | M |
| `094` | [Budgets, anomaly detection and showback](aws-094-budgets-anomaly.md) | Catching a runaway spend in hours, and giving teams a number they recognize as theirs. | Production | S |
| `095` | [Right-sizing and waste elimination](aws-095-rightsizing-waste.md) | Compute Optimizer, idle resource sweeps, and non-prod that switches itself off at night. | Production | S |

### <a id="12"></a>12 · Migration, Hybrid & Edge

*Getting workloads in, keeping one foot out, and pushing compute to the physical edge.*

| ID | Architecture | What it gives you | Maturity | Effort |
|---|---|---|---|---|
| `096` | [Migration assessment and rehost with MGN](aws-096-migration-7rs.md) | Discovery, the 7Rs decision, wave planning, and a cutover with a rollback that works. | Production | L |
| `097` | [Heterogeneous database migration with DMS + SCT](aws-097-heterogeneous-db-migration.md) | Oracle/SQL Server to PostgreSQL: schema conversion, CDC cutover, and validating correctness. | Production | L |
| `098` | [On-prem hybrid with Outposts](aws-098-outposts-hybrid.md) | Real AWS APIs in your data centre for data-residency and latency constraints you cannot move. | Specialist | L |
| `099` | [Local Zones and Wavelength for latency-bound workloads](aws-099-local-zones-wavelength.md) | Single-digit-millisecond compute near users or on the 5G edge, and what is missing there. | Specialist | M |
| `100` | [Greengrass edge inference with cloud sync](aws-100-greengrass-edge-ml.md) | Running models on devices that are offline half the time, and updating them safely. | Specialist | L |
| `101` | [Legacy modernization with the strangler fig pattern](aws-101-strangler-fig.md) | Routing traffic feature-by-feature off the monolith, with a seam you can retreat through. | Production | L |

> **Status:** 101 / 101 pages written.


## On non-overlap

These 101 are deliberately disjoint. Where two architectures touch the same service
they do so from different angles — `aws-001` is about *authorising* a request at the
gateway, `aws-005` about *surviving* too many of them, `aws-009` about *changing* what
is behind it, and `aws-006` about never exposing it publicly at all. Where one
architecture is a prerequisite for another, the page says so under **See also**
instead of repeating it.

## Regenerating

```bash
python Architecture-AWS/_generator/manifest.py       # validate the 101
python Architecture-AWS/_generator/gen_diagrams.py   # rebuild every diagram
python Architecture-AWS/_generator/gen_readme.py     # rebuild this index
```

Add an architecture by appending to `manifest.py`, adding its diagram spec under
`_generator/specs/`, then writing the doc. The index picks it up automatically and
flags it as `TODO` until both the doc and the diagram exist.

## See also

- [Architecture/Reference-Architectures](../Architecture/Reference-Architectures/) — long-form blueprints
- [Architecture/ADRs](../Architecture/ADRs/) — decisions actually taken
- [Architecture/Tradeoff-Analysis](../Architecture/Tradeoff-Analysis/) — the comparisons behind them
- [.labs/AWS](../.labs/AWS/) — labs that provision some of these for real
