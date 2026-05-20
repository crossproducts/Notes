# Production MLOps Architecture: AWS-Native vs. Open-Source/Kubernetes — A Comprehensive Comparison (2025–2026)

## TL;DR
- **AWS-native MLOps is a vertically integrated, managed stack** centered on Amazon SageMaker AI (Studio, Pipelines, HyperPod, Feature Store, Endpoints, Model Monitor, Clarify) and Amazon Bedrock (AgentCore, Knowledge Bases, Guardrails); it minimizes operational burden and is the right default for AWS-committed teams that prioritize time-to-production over portability.
- **The Kubernetes/OSS stack** assembles best-of-breed components — Kubeflow/Argo/Flyte/Ray for orchestration and training, MLflow for tracking and registry, KServe + vLLM/llm-d and Ray Serve for serving, Feast for features, Milvus/Qdrant/Weaviate for vectors, LangGraph/CrewAI/AutoGen for agents, Langfuse + Evidently/Arize Phoenix for observability — and is preferred where portability, deep customization, multi-cloud, GPU-density economics, or cutting-edge LLM serving optimizations matter most.
- **For the three workload classes** (classical/tabular batch, low-latency real-time, LLM/GenAI), the two stacks map cleanly stage-for-stage; the largest divergences are in foundation-model fine-tuning (SageMaker HyperPod recipes vs. Kubeflow Trainer + Ray Train on KubeRay) and in generative inference (Bedrock managed APIs vs. KServe LLMInferenceService + vLLM/llm-d).

---

## Key Findings

1. **AWS Well-Architected re:Invent 2025 update.** AWS now publishes three AI lenses — Machine Learning, Generative AI, and Responsible AI — with explicit guidance for SageMaker HyperPod foundation-model training, agentic AI patterns, and *"eight architecture scenarios covering common generative AI-powered business applications such as autonomous call centers, knowledge worker co-pilots"* (AWS Architecture Blog, Nov 19, 2025). This is the AWS-native reference against which the OSS stack is compared.
2. **KServe pivoted to "generative-first."** With v0.15 (June 2025) and v0.16, KServe added the `LLMInferenceService` CRD, integration with vLLM and llm-d for prefill/decode disaggregation and KV-cache-aware routing, KEDA-based scaling on LLM-specific metrics, and Envoy AI Gateway for token-rate limiting. This now constitutes the canonical Kubernetes-native LLM serving control plane.
3. **Foundation-model training.** AWS introduced SageMaker HyperPod recipes (GA late 2024) for distributed fine-tuning of Llama, Mistral, Mixtral, DeepSeek, and GPT-OSS with Slurm or EKS orchestration, SMDDP/SMP libraries, and auto-resume. The OSS equivalent is Kubeflow Trainer plus Ray Train on KubeRay (or NeMo/Megatron on Slurm) with DeepSpeed/FSDP.
4. **Agentic AI.** Amazon Bedrock AgentCore became GA on October 13, 2025 (AWS What's New: *"Posted on: Oct 13, 2025 · Amazon Bedrock AgentCore is now generally available"*), providing managed Runtime, Identity, Memory, Gateway, Code Interpreter, Browser Use, and Observability primitives — framework-agnostic and compatible with LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, and AWS Strands. OSS leaders are LangGraph (stateful graph workflows, durable execution), CrewAI (role-based crews), and AutoGen/Microsoft Agent Framework (conversational multi-agent).
5. **LLMOps tooling has consolidated** around Langfuse (open-source LLM tracing, prompt management, evaluations) and MLflow (now with full LLM/agent support — tracing, prompt registry, LLM-as-judge). For RAG evaluation, Ragas + DeepEval + TruLens are the OSS triad: Ragas for development iteration, DeepEval for CI/CD unit-test-style gates, and TruLens for production tracing-coupled monitoring.
6. **Open table formats.** Apache Iceberg has emerged as the cross-engine ML/lakehouse standard. Per Bloomberg (TechCrunch, Aug 14, 2024), *"Analytics and AI giant Databricks reportedly paid nearly $2 billion when it acquired Tabular in June"* (Databricks CEO Ali Ghodsi separately confirmed to CNBC the price was "over $1 billion"). AWS launched S3 Tables with built-in Iceberg support and Snowflake open-sourced the Polaris catalog. SageMaker Feature Store offline store now supports Iceberg.
7. **TorchServe is deprecated.** Per GitHub issue #3396 on pytorch/serve, *"This repository was archived by the owner on Aug 7, 2025. It is now read-only."* Production OSS serving now centers on KServe + vLLM/llm-d, Ray Serve, NVIDIA Triton, BentoML, and Seldon Core v2 with MLServer.
8. **Vector databases for RAG.** Milvus (broadest features, billion-scale), Qdrant (Rust, filter-heavy workloads), Weaviate (graph+vector hybrid), Chroma (developer-friendly small-scale), and pgvector (Postgres-embedded) are the OSS leaders. On AWS the managed equivalents are Amazon OpenSearch Serverless (vector engine), Aurora PostgreSQL pgvector, and Amazon Kendra; Bedrock Knowledge Bases orchestrates ingestion-to-retrieval.

---

## Component Mapping Table

| MLOps Lifecycle Stage | AWS-Native Service | Open-Source / Kubernetes Equivalent |
|---|---|---|
| Raw / lake storage | Amazon S3, S3 Tables (Iceberg) | MinIO (S3-compatible), Ceph; Iceberg / Delta Lake / Hudi on object storage |
| Catalog / governance | AWS Glue Data Catalog, AWS Lake Formation | Apache Hive Metastore, Project Nessie, Apache Polaris (Snowflake-donated), Unity Catalog OSS (Databricks-donated 2024) |
| Data processing / ETL | AWS Glue, Amazon EMR (Spark/Hive/Presto), AWS Glue DataBrew | Apache Spark on K8s (Spark Operator), Apache Flink, dbt, Dask, Ray Data |
| Feature engineering UI | SageMaker Data Wrangler (in Unified Studio) | Pandas/Polars/Spark notebooks; Hopsworks UI |
| Feature store | SageMaker Feature Store (online=DynamoDB <10ms, offline=S3 Parquet/Iceberg, append-only) | Feast (offline: BigQuery/Snowflake/Spark/Iceberg; online: Redis/DynamoDB/Postgres/MongoDB), Hopsworks |
| Notebook / IDE | SageMaker Studio, SageMaker Unified Studio, SageMaker Canvas | JupyterHub on K8s, Kubeflow Notebooks, VSCode + devcontainers |
| Experiment tracking | SageMaker Experiments, SageMaker with managed MLflow | MLflow, W&B (OSS components), Aim, DVC, Neptune |
| Distributed training | SageMaker Training jobs, SageMaker HyperPod (Slurm or EKS) + HyperPod Recipes | Kubeflow Trainer (PyTorchJob/TFJob/JAX/DeepSpeed), Ray Train + KubeRay, MPI Operator, NVIDIA NeMo |
| Hyperparameter tuning | SageMaker AMT | Katib (Kubeflow), Ray Tune, Optuna |
| Foundation-model fine-tuning | HyperPod recipes (Llama, Mixtral, DeepSeek, GPT-OSS), SageMaker JumpStart, Bedrock Custom Models / Nova Forge | HF PEFT + Accelerate, Axolotl, NeMo Framework, Megatron-LM, Ray Train + DeepSpeed/FSDP |
| Model registry | SageMaker Model Registry | MLflow Model Registry, Kubeflow Model Registry |
| Pipeline orchestration | SageMaker Pipelines, AWS Step Functions, Amazon MWAA (Airflow) | Kubeflow Pipelines, Argo Workflows, Flyte, Metaflow, Prefect, Dagster, Apache Airflow |
| CI/CD for ML | CodePipeline/CodeBuild/CodeCommit, SageMaker Projects, GitHub Actions integration | ArgoCD, GitHub Actions, GitLab CI, Jenkins, Tekton |
| Real-time serving | SageMaker Real-Time Endpoints, Multi-Model/Multi-Container Endpoints, Inference Components (2024), Async, Serverless | KServe `InferenceService`, Seldon Core v2 + MLServer, BentoML/Yatai, Ray Serve, NVIDIA Triton |
| Batch inference | SageMaker Batch Transform | Spark batch, Ray Data batch inference, Argo CronWorkflow + KServe |
| Streaming inference | Kinesis + Lambda → SageMaker endpoint | Flink/Kafka Streams → KServe/Ray Serve |
| LLM serving | Bedrock managed FMs, SageMaker JumpStart, SageMaker Endpoints w/ LMI containers (vLLM/TGI/DJL) | KServe `LLMInferenceService` + vLLM + llm-d, Ray Serve LLM, NVIDIA Triton + TensorRT-LLM, HF TGI, Ollama |
| LLM gateway / routing | Amazon Bedrock Runtime | LiteLLM, Envoy AI Gateway, Portkey, Helicone (now in maintenance mode) |
| Vector / retrieval | OpenSearch Serverless (vector), Aurora pgvector, Amazon Kendra, S3 Vectors | Milvus, Weaviate, Qdrant, Chroma, pgvector, OpenSearch (OSS) |
| RAG orchestration | Bedrock Knowledge Bases (ingest/chunk/embed/retrieve/cite) | LangChain, LlamaIndex, Haystack |
| Agent frameworks | Bedrock Agents, AWS Strands Agents, Bedrock AgentCore (runtime/memory/identity/gateway/observability) | LangGraph, CrewAI, AutoGen / Microsoft Agent Framework, OpenAI Agents SDK, Google ADK, MetaGPT, OpenAgents |
| Prompt management | Bedrock Prompt Management, SageMaker-managed MLflow Prompt Registry | Langfuse, MLflow Prompt Registry, Helicone (maintenance), PromptLayer |
| LLM evaluation | Bedrock Model Evaluation, SageMaker Clarify FM Evaluations | Ragas, DeepEval, TruLens, MLflow LLM-as-judge, Arize Phoenix |
| Guardrails / safety | Amazon Bedrock Guardrails | NVIDIA NeMo Guardrails (Colang), Guardrails AI, Meta Llama Guard |
| Drift / quality monitoring | SageMaker Model Monitor (data quality, model quality, bias drift, feature attribution drift) + SageMaker Clarify | Evidently AI, WhyLabs (whylogs OSS), Arize Phoenix, NannyML, Fiddler OSS |
| LLM observability | Bedrock + CloudWatch + X-Ray, SageMaker MLflow Tracing | Langfuse, Arize Phoenix, OpenLLMetry/Traceloop, OpenTelemetry GenAI semconv |
| Metrics / logs / traces | Amazon CloudWatch, AWS X-Ray | Prometheus + Grafana, Loki, Jaeger/Tempo, OpenTelemetry Collector, ELK/EFK |
| Compute / runtime | EC2, Lambda, ECS, EKS, Fargate, Trainium/Inferentia | Kubernetes (EKS/GKE/AKS/on-prem), Knative, KubeRay, Slurm |
| Service mesh / networking | App Mesh, VPC Lattice | Istio, Linkerd, Envoy AI Gateway, Kubernetes Gateway API |
| Security & IAM | IAM, KMS, VPC, PrivateLink, Secrets Manager | K8s RBAC, OPA/Gatekeeper, Kyverno, Vault, SPIFFE/SPIRE |
| Lineage / metadata | SageMaker ML Lineage Tracking, Model Cards | OpenLineage, MLflow lineage, Marquez, DataHub, Amundsen |

---

## Architecture Diagram 1 — AWS-Native Reference (all three workload types)

```
                              ┌─────────────────────────────────────────────────────────────┐
                              │                  GOVERNANCE & SECURITY                      │
                              │  IAM • KMS • VPC • PrivateLink • Lake Formation • CloudTrail │
                              └─────────────────────────────────────────────────────────────┘

  ┌──────────────────┐    ┌──────────────────┐    ┌────────────────────┐    ┌─────────────────────┐
  │   DATA SOURCES   │    │   DATA STORAGE   │    │   DATA PROCESSING  │    │   FEATURE PLATFORM  │
  │ DBs, Streams,    │───▶│  Amazon S3       │───▶│  AWS Glue ETL      │───▶│ SageMaker Feature   │
  │ SaaS, IoT,       │    │  S3 Tables       │    │  Amazon EMR (Spark)│    │ Store (Online=Dynamo│
  │ Kinesis, MSK     │    │  (Iceberg)       │    │  SM Data Wrangler  │    │ DB, Offline=S3/Iceb)│
  └──────────────────┘    │ Glue Data Catalog│    │  AWS Glue DataBrew │    └──────────┬──────────┘
                          └──────────────────┘    └─────────┬──────────┘               │
                                                            │                          │
                              ┌─────────────────────────────┴──────────────────────────┴──────────────┐
                              │                  AMAZON SAGEMAKER AI (Unified Studio)                  │
                              │  ┌───────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │
                              │  │ Studio / IDE  │  │ SM Experiments / │  │ SM Pipelines (DAG)   │   │
                              │  │ Canvas/JumpSt │  │ Managed MLflow   │  │                      │   │
                              │  └───────┬───────┘  └────────┬─────────┘  └──────────┬───────────┘   │
                              │          │                   │                       │               │
                              │  ┌───────▼───────────────────▼───────────────────────▼───────────┐   │
                              │  │ TRAINING                                                       │   │
                              │  │  • SM Training Jobs (classical / tabular)                      │   │
                              │  │  • SM AMT (HPO)                                                │   │
                              │  │  • SM HyperPod (Slurm or EKS) + HyperPod Recipes               │   │
                              │  │      for FM training/fine-tuning (Llama, Mixtral, DeepSeek)    │   │
                              │  │  • SMDDP / SMP libraries; Trainium / GPU clusters              │   │
                              │  └───────┬────────────────────────────────────────────────────────┘   │
                              │          │                                                            │
                              │  ┌───────▼─────────────────┐    ┌────────────────────────────────┐   │
                              │  │ SM Model Registry       │───▶│ SM Clarify (bias/explainability)│  │
                              │  └───────┬─────────────────┘    └────────────────┬────────────────┘  │
                              │          │                                       │                   │
                              │  ┌───────▼────────────────────────────────┐      │                   │
                              │  │ INFERENCE                              │      │                   │
                              │  │  • Real-Time Endpoints (auto-scaling)  │      │                   │
                              │  │  • Multi-Model / Multi-Container       │      │                   │
                              │  │  • Inference Components (2024)         │      │                   │
                              │  │  • Async / Serverless Inference        │      │                   │
                              │  │  • Batch Transform                     │      │                   │
                              │  └───────┬────────────────────────────────┘      │                   │
                              │          │                                       │                   │
                              │  ┌───────▼────────────────────────────────┐      │                   │
                              │  │ SM Model Monitor                       │◀─────┘                   │
                              │  │ (data quality, model quality,          │                          │
                              │  │  bias drift, feature attribution drift)│                          │
                              │  └────────────────────────────────────────┘                          │
                              └─────────────────────────────────────────────────────────────────────┘
                                              ▲                                              ▲
              ┌───────────────────────────────┴────────────────┐                ┌────────────┴──────────────┐
              │           CI/CD & ORCHESTRATION                │                │   LLM / GENERATIVE AI     │
              │  • CodePipeline / CodeBuild / CodeCommit       │                │  ┌─────────────────────┐  │
              │  • SageMaker Projects (templates)              │                │  │ Amazon Bedrock      │  │
              │  • GitHub Actions / GitLab integration         │                │  │  • FMs (Claude,Nova,│  │
              │  • AWS Step Functions, Amazon MWAA (Airflow)   │                │  │     Llama, Mistral) │  │
              └────────────────────────────────────────────────┘                │  │  • Knowledge Bases  │──┼──▶ OpenSearch
              ┌────────────────────────────────────────────────┐                │  │     (managed RAG)   │  │   Serverless,
              │           OBSERVABILITY                        │                │  │  • Guardrails       │  │   Aurora pgvector,
              │  • Amazon CloudWatch (metrics, logs, alarms)   │◀───────────────│  │  • Bedrock Agents + │  │   Kendra, S3 Vectors
              │  • AWS X-Ray (tracing)                         │                │  │    AgentCore (GA    │  │
              │  • SM Model Monitor → CloudWatch alarms        │                │  │    Oct 13 2025):    │  │
              └────────────────────────────────────────────────┘                │  │    runtime, memory, │  │
                                                                                │  │    identity, gw,    │  │
                                                                                │  │    code interp,     │  │
                                                                                │  │    browser, obs     │  │
                                                                                │  └─────────────────────┘  │
                                                                                └───────────────────────────┘

  WORKLOAD-TYPE DATA FLOWS:
  ────────────────────────────────────
  (A) CLASSICAL/TABULAR BATCH:  Kinesis/DB → S3 → Glue/EMR → Feature Store offline → SM Training Job
                                → SM Model Registry → SM Batch Transform → S3 results / Athena
  (B) REAL-TIME ONLINE INFER:   App → API Gateway/ALB → SM Real-Time Endpoint (auto-scaling)
                                ← Feature Store online (DynamoDB) ←  Model Monitor captures traffic
  (C) LLM / GENAI:
       RAG:     User → API GW → Lambda → Bedrock Knowledge Base → OpenSearch Serverless vector
                                                  → Bedrock FM → Guardrails → user
       Fine-tune: S3 dataset → SM HyperPod recipe (PEFT/LoRA on Llama/Mixtral) → S3 artifact
                  → SM Endpoint (LMI container) OR Bedrock Custom Model
       Agentic:  User → Bedrock Agent (orchestrator) → Action Groups (Lambda tools)
                  → AgentCore primitives → KB retrieval / APIs → Guardrails → response
```

---

## Architecture Diagram 2 — Open-Source / Kubernetes Reference

```
                           ┌─────────────────────────────────────────────────────────────┐
                           │                  PLATFORM / SECURITY LAYER                  │
                           │  Kubernetes (EKS/GKE/AKS/on-prem) • Istio/Linkerd •         │
                           │  OPA/Gatekeeper • cert-manager • Vault • SPIFFE • Knative   │
                           └─────────────────────────────────────────────────────────────┘

  ┌───────────────────┐   ┌────────────────────┐   ┌──────────────────────┐   ┌────────────────────────┐
  │  DATA SOURCES     │   │   LAKEHOUSE STORE  │   │   PROCESSING ENGINE  │   │   FEATURE STORE        │
  │  DBs, Kafka,      │──▶│  MinIO / S3 +      │──▶│ Spark on K8s         │──▶│  Feast                 │
  │  Streams, SaaS    │   │  Apache Iceberg /  │   │ (Spark Operator),    │   │   Offline: Parquet/    │
  │                   │   │  Delta / Hudi      │   │ Flink, Ray Data,     │   │     Iceberg/Snowflake  │
  └───────────────────┘   │  Hive Metastore /  │   │ dbt, Dask            │   │   Online: Redis/Dynamo │
                          │  Nessie / Polaris  │   └──────────┬───────────┘   │     /Postgres/Mongo    │
                          └────────────────────┘              │               │   Feature Server (REST)│
                                                              │               └──────────┬─────────────┘
                                                              │                          │
              ┌───────────────────────────────────────────────┴──────────────────────────┴────────────┐
              │              DEV / EXPERIMENT / TRACKING                                              │
              │  Kubeflow Notebooks • JupyterHub • VSCode                                              │
              │  MLflow Tracking Server (Postgres + S3/MinIO artifacts) • Model Registry              │
              │  W&B / Aim / DVC for dataset & experiment versioning                                  │
              └──────────────────────────────┬────────────────────────────────────────────────────────┘
                                             │
              ┌──────────────────────────────▼───────────────────────────────────────────────────────┐
              │              PIPELINE ORCHESTRATION                                                  │
              │  Kubeflow Pipelines • Argo Workflows • Flyte • Metaflow • Prefect • Dagster •        │
              │  Apache Airflow                                                                      │
              └──────────────────────────────┬───────────────────────────────────────────────────────┘
                                             │
       ┌─────────────────────────────────────┴───────────────────────────────────────────┐
       │  TRAINING LAYER                                                                 │
       │   • Kubeflow Trainer (PyTorchJob, TFJob, MPIJob, JAX, DeepSpeed)                │
       │   • Ray Train + KubeRay (RayJob/RayCluster) — multi-framework, FSDP/DeepSpeed   │
       │   • Katib / Ray Tune — hyperparameter optimization                              │
       │   • NVIDIA NeMo / Megatron / Axolotl — LLM fine-tuning, LoRA/QLoRA              │
       │   • GPU/Trainium scheduling via NVIDIA device plugin, Volcano, KAI Scheduler    │
       └─────────────────────────────────────┬───────────────────────────────────────────┘
                                             │
       ┌─────────────────────────────────────▼───────────────────────────────────────────┐
       │  MODEL REGISTRY: MLflow Model Registry (artifacts in MinIO/S3; Dev/Staging/Prod)│
       └─────────────────────────────────────┬───────────────────────────────────────────┘
                                             │
       ┌─────────────────────────────────────▼───────────────────────────────────────────┐
       │  INFERENCE LAYER                                                                │
       │  PREDICTIVE / CLASSICAL:                                                        │
       │     KServe InferenceService → MLServer / Triton / sklearn-server / XGBoost      │
       │     Seldon Core v2 (multi-model serving, Envoy data plane, MLServer/Triton)     │
       │     BentoML Bentos → Yatai (K8s)                                                │
       │     Ray Serve (Python-first composition, multi-model)                           │
       │                                                                                 │
       │  GENERATIVE (LLM):                                                              │
       │     KServe LLMInferenceService + vLLM + llm-d                                   │
       │       • PagedAttention, continuous batching, prefill/decode disaggregation      │
       │       • KV-cache aware routing, prefix-cache reuse                              │
       │       • LeaderWorkerSet (LWS) for multi-node TP/PP hosting of 70B+ models       │
       │       • KEDA scaling on token metrics; Envoy AI Gateway routing                 │
       │     Ray Serve LLM (vLLM, OpenAI-compatible)                                     │
       │     HF TGI, NVIDIA Triton + TensorRT-LLM, Ollama                                │
       │                                                                                 │
       │  Autoscaling:  Knative scale-to-zero • KEDA (request/token metrics) • HPA       │
       └─────────────────────────────────────┬───────────────────────────────────────────┘
                                             │
       ┌─────────────────────────────────────▼───────────────────────────────────────────┐
       │  MONITORING & OBSERVABILITY                                                     │
       │   Classical ML:  Evidently AI (drift, data quality), WhyLabs (whylogs),         │
       │                  NannyML (estimated performance), Fiddler OSS                   │
       │   LLM/Agent:     Langfuse (tracing, prompts, evals), Arize Phoenix (OTel),      │
       │                  OpenLLMetry / Traceloop, MLflow Tracing                        │
       │   Infra:         Prometheus + Grafana, Loki, Jaeger/Tempo, OTel Collector       │
       └─────────────────────────────────────────────────────────────────────────────────┘

       ┌─────────────────────────────────────────────────────────────────────────────────┐
       │  CI/CD                                                                          │
       │   GitHub Actions / GitLab CI / Jenkins → build → push image →                   │
       │   ArgoCD (GitOps) syncs InferenceService/Workflow YAML;                         │
       │   Tekton for K8s-native pipelines; cosign/SLSA for supply-chain                 │
       └─────────────────────────────────────────────────────────────────────────────────┘

       ┌─────────────────────────────────────────────────────────────────────────────────┐
       │  LLM / GENAI SPECIFIC                                                           │
       │   Vector DBs:    Milvus • Weaviate • Qdrant • Chroma • pgvector                 │
       │   RAG framework: LangChain • LlamaIndex • Haystack                              │
       │   RAG eval:      Ragas (dev iteration) • DeepEval (CI gate) • TruLens (prod)    │
       │   Guardrails:    NVIDIA NeMo Guardrails (Colang) • Guardrails AI • Llama Guard  │
       │   Agents:        LangGraph (v1.0 Oct 22 2025; stateful graphs, durable) •       │
       │                  CrewAI (role crews) • AutoGen/MS Agent Framework •             │
       │                  OpenAI Agents SDK • Google ADK • MetaGPT • OpenAgents          │
       │   Gateway:       LiteLLM • Envoy AI Gateway • Portkey • Helicone (maintenance)  │
       └─────────────────────────────────────────────────────────────────────────────────┘

  WORKLOAD-TYPE DATA FLOWS:
  ─────────────────────────
  (A) CLASSICAL/TABULAR BATCH:  Kafka/DB → MinIO+Iceberg → Spark-on-K8s → Feast offline
                                → Kubeflow Pipeline (train, eval) → MLflow Registry
                                → Argo cron: KServe batch / Ray Data batch → MinIO results
  (B) REAL-TIME ONLINE INFER:   App → Istio Gateway → KServe InferenceService (Triton/MLServer)
                                ← Feast online (Redis) ← Evidently drift monitor on capture logs
  (C) LLM / GENAI:
       RAG:     User → API → LangChain orchestrator → embed → Milvus/Qdrant retrieval
                  → vLLM via KServe LLMInferenceService → NeMo Guardrails → user
                  → Langfuse traces every span; Ragas evals scheduled in CI
       Fine-tune: S3/MinIO dataset → Kubeflow Trainer PyTorchJob OR Ray Train on KubeRay
                  (FSDP/DeepSpeed/LoRA) → MLflow artifact → KServe LLMInferenceService rollout
       Agentic:  User → LangGraph state machine on K8s → tool nodes (HTTP/MCP) →
                  vector retrieval → vLLM/llm-d → Guardrails → checkpoint state to Postgres
                  → Langfuse + Phoenix traces; OTel GenAI semconv spans
```

---

## Details

### A. Data ingestion, storage, and processing
**AWS-native.** Amazon S3 is the canonical landing zone; **S3 Tables** add managed Apache Iceberg buckets. AWS Glue Data Catalog is the metastore. AWS Lake Formation enforces fine-grained row/column-level permissions across S3, Glue, EMR, Athena, Redshift, and SageMaker. Amazon EMR runs managed Spark/Presto/Flink. SageMaker Data Wrangler offers a visual no-code interface inside SageMaker Studio that imports from S3, Athena, Redshift, Lake Formation, and Feature Store, and applies many built-in Spark-backed transforms before exporting to Feature Store or Pipelines.

**OSS/K8s.** MinIO (or any S3-compatible store) holds the lakehouse on top of Iceberg / Delta Lake / Hudi. Iceberg has consolidated as the de facto standard — every major engine (Spark, Trino, Flink, Snowflake, Athena, BigQuery) reads it. Apache Hive Metastore, **Project Nessie**, **Apache Polaris** (Snowflake-donated), or **Unity Catalog OSS** (Databricks-donated 2024) serve as the catalog. Apache Spark on Kubernetes (via the Spark Operator), Apache Flink, dbt-core, Dask, and **Ray Data** cover ETL/feature engineering at scale.

### B. Feature Store
**AWS.** SageMaker Feature Store provides an online store (DynamoDB-backed, sub-10 ms reads) and an offline store (S3 in Parquet, optionally Iceberg) with append-only history. `PutRecord` writes synchronously to the online store and asynchronously replicates to the offline store within minutes; this enables point-in-time-correct training data via Athena queries while serving low-latency predictions.

**OSS.** **Feast** is the dominant choice: it manages a registry, ingestion via batch materialization or push-based streaming, an offline store (Spark, BigQuery, Snowflake, Redshift, file), an online store (Redis, DynamoDB, Postgres, SQLite, MongoDB), and a FastAPI-based Feature Server for low-latency serving. Feast added native vector search and MongoDB support in 2025. **Hopsworks** is an alternative with a richer UI and built-in storage tier.

### C. Experiment Tracking & Model Registry
**AWS.** SageMaker Experiments is built into Studio. AWS offers **SageMaker with MLflow** — a fully managed MLflow tracking server inside SageMaker — and **SageMaker Model Registry** integrates with Pipelines, Clarify, and Endpoints for approval-based deployment.

**OSS.** MLflow is the industry standard: tracking server (Postgres metadata + S3/MinIO artifacts), Model Registry with stages (Dev/Staging/Prod) and aliases, plus newer GenAI features (tracing, prompt registry, LLM-as-judge evaluations). DVC versions datasets alongside code; Weights & Biases offers OSS components for tracking. Kubeflow now ships its own cloud-native Model Registry that overlaps with MLflow.

### D. Training and Distributed/Fine-Tuning
**AWS classical ML.** SageMaker Training Jobs spin up ephemeral training clusters in any framework with built-in algorithms or BYOC containers; SageMaker AMT handles HPO.

**AWS foundation-model training/fine-tuning.** SageMaker HyperPod provides persistent, self-healing GPU/Trainium clusters with Slurm or Amazon EKS orchestration, SageMaker Data Parallelism (SMDDP) and Model Parallelism (SMP) libraries, automatic checkpointing, and node auto-resume. **HyperPod recipes** (GA late 2024) are pre-validated training stacks for Llama 3.1 405B, Llama 3.2 90B, Mixtral 8x22B, Mistral, DeepSeek, GPT-OSS, etc. Bedrock Custom Models / Nova Forge offer fully managed fine-tuning.

**OSS K8s.** **Kubeflow Trainer** (the 2025 rewrite, formerly Kubeflow Training Operator) supports PyTorch, JAX, DeepSpeed, Megatron, HuggingFace, MLX, XGBoost as Kubernetes-native CRDs. **Ray Train + KubeRay** offers Python-first multi-node multi-GPU training with autoscaling Ray clusters. **NVIDIA NeMo Framework**, **Megatron-LM**, and **Axolotl** layer on top for LLM pre-training and fine-tuning. **Katib** and **Ray Tune** handle hyperparameter optimization.

### E. Pipeline Orchestration & CI/CD
**AWS.** SageMaker Pipelines is the SageMaker-native DAG; Step Functions for cross-service workflows; Amazon MWAA for managed Airflow. SageMaker Projects bootstrap end-to-end CI/CD using CodeCommit/CodePipeline/CodeBuild with two repos (model-build, model-deploy) and CloudFormation-based environments.

**OSS.** A rich landscape: **Kubeflow Pipelines** (K8s-native container-step DAGs) is the most-used Kubeflow component (90% of users per the 2023 Kubeflow user survey). **Argo Workflows** (CNCF, YAML, K8s-native). **Flyte** (Python-typed, K8s-native, ML-focused, used at Lyft/Spotify). **Metaflow** (Netflix-origin, Python-first). **Prefect** and **Dagster** for dynamic Python-native workflows; Dagster's asset-centric model is especially strong for ML+data lineage. **Apache Airflow** remains the broadest-installed orchestrator. CI/CD is handled by GitHub Actions / GitLab CI / Jenkins with **ArgoCD** for GitOps deployment of model serving manifests and **Tekton** for K8s-native pipelines.

### F. Model Deployment / Serving

**Classical / tabular (batch + real-time).**
- *AWS.* Batch Transform handles scheduled batch scoring. Real-Time Endpoints provide auto-scaling HTTPS endpoints; Multi-Model Endpoints host hundreds of models on shared infrastructure; the 2024 Inference Components feature gives finer-grained co-location and auto-scaling per model on the same instance; Async Inference handles long-running large-payload requests; Serverless Inference avoids cold infrastructure for sparse traffic.
- *OSS.* **KServe** is the K8s-native serving control plane: an `InferenceService` CRD wraps autoscaling (Knative scale-to-zero or HPA), traffic splitting/canary, transformer/predictor/explainer microservices, and pluggable runtimes (Triton, MLServer, sklearn-server, XGBoost-server). **Seldon Core v2** offers a similar model with stronger multi-model serving by design via MLServer + Triton, an Envoy data plane, and full data-plane availability when control-plane services are down. **BentoML / Yatai** packages models as portable Bentos with adaptive batching, model parallelism, and one-click K8s deployment. **NVIDIA Triton** is the highest-throughput multi-framework inference server with dynamic batching, model ensembles, and concurrent execution. **Ray Serve** is Python-first and excels at model composition.

**LLM / generative inference.**
- *AWS.* **Amazon Bedrock** offers managed access to Anthropic Claude, Amazon Nova, Meta Llama, Mistral, AI21, Cohere, and Stability with serverless or provisioned throughput, plus Knowledge Bases, Agents, Guardrails, and Prompt Management. For self-hosted LLMs, **SageMaker JumpStart** and **SageMaker Endpoints** with LMI (Large Model Inference) containers running vLLM/TGI/DJL provide managed deployment.
- *OSS.* The 2025–2026 reference stack is **KServe `LLMInferenceService` + vLLM + llm-d + Envoy AI Gateway**. This combination provides PagedAttention and continuous batching in vLLM; **llm-d** for cluster-wide intelligence — prefill/decode disaggregation, KV-cache-aware request routing, prefix-cache reuse; **LeaderWorkerSet (LWS)** for multi-node tensor/pipeline parallel hosting of 70B+ models; KEDA scaling on LLM-specific metrics; Envoy AI Gateway for token-rate limits, multi-tenant routing, and unified OpenAI-compatible APIs. Alternatives include **Ray Serve LLM** (vLLM under the hood, OpenAI-compatible, simpler), **Hugging Face TGI**, **NVIDIA Triton + TensorRT-LLM**, and **Ollama**.

### G. Monitoring (Data Drift, Model Drift, Quality, Latency)
**AWS.** SageMaker Model Monitor provides four monitor types: **data quality** (schema/statistical drift on inputs), **model quality** (accuracy/precision when ground truth arrives), **bias drift** (via SageMaker Clarify, DPPL etc.), and **feature attribution drift** (SHAP feature-importance shift). Captured inference traffic flows to S3, baselines are generated from training data, and violations publish to CloudWatch. Custom monitors (e.g., NLP embedding cosine-similarity drift) are supported.

**OSS.** For classical ML, **Evidently AI** is the de facto OSS choice with 100+ metrics across drift, data quality, and model performance; it produces HTML reports or runs a UI service. **WhyLabs / whylogs** offers privacy-preserving statistical profiling. **NannyML** uniquely estimates performance pre-ground-truth. **Fiddler** has an OSS edition. For LLMs, **Arize Phoenix** (OpenTelemetry-based, OSS) and **Langfuse** dominate; **Evidently** added LLM evals. Production telemetry is unified via Prometheus + Grafana, Loki, Jaeger/Tempo, and the OpenTelemetry GenAI semantic conventions emerging in 2025.

### H. LLM/GenAI Specific Components

**Vector / retrieval.**
- AWS: Amazon OpenSearch Serverless (vector engine), Aurora PostgreSQL pgvector, Amazon Kendra, and S3 Vectors. Bedrock Knowledge Bases orchestrates ingestion → chunking → embedding → indexing → retrieval with hybrid (vector + keyword) search and source attribution.
- OSS: Milvus / Zilliz (broadest features, billion-scale), Weaviate (graph + vector hybrid, GraphQL), Qdrant (Rust, filter-heavy workloads), Chroma (developer-friendly small-scale), pgvector for Postgres-embedded use. Independent benchmarks place Milvus/Zilliz and Qdrant at sub-100 ms latency on 1M–10M-vector datasets.

**RAG orchestration.**
- AWS: Bedrock Knowledge Bases (fully managed RAG with semantic, hierarchical, and fixed-size chunking; multi-modal parsing via Bedrock Data Automation; agentic retrieval with parallel subqueries).
- OSS: LangChain, LlamaIndex, Haystack — LlamaIndex is particularly strong for advanced retrieval patterns.

**RAG / LLM evaluation.**
- AWS: Bedrock Model Evaluation and SageMaker Clarify FM Evaluations support human, automated, and LLM-as-judge evals.
- OSS: **Ragas** (reference-free RAG metrics: faithfulness, answer relevance, context precision/recall), **DeepEval** (50+ metrics, pytest-style CI integration), **TruLens** (feedback functions + OpenTelemetry tracing for production monitoring). Recommended pattern: Ragas during development iteration, DeepEval as a CI quality gate, TruLens/Langfuse on sampled production traffic.

**Guardrails.**
- AWS: Amazon Bedrock Guardrails (denied topics, content filters, PII redaction, contextual grounding, prompt-injection detection).
- OSS: **NVIDIA NeMo Guardrails** (Colang DSL, programmable input/output/dialog/retrieval/execution rails, integrates with LangChain/LangGraph/LlamaIndex; NVIDIA reports ~1.4× detection-rate uplift with ~0.5 s latency at 5 parallel rails). **Guardrails AI** (RAIL specs, output validators for PII/toxicity/format). **Meta Llama Guard** for content classification.

**Prompt management & observability.**
- AWS: Bedrock Prompt Management, SageMaker-managed MLflow Prompt Registry, CloudWatch + X-Ray.
- OSS: **Langfuse** (open-source, self-hostable; *"used by 2,300+ companies and processes billions of observations per month"* per its own marketing). **MLflow** (Linux Foundation, GenAI features in 2025). **Helicone** went into maintenance mode after Mintlify's March 3, 2026 acquisition; per Mintlify's blog post *"Mintlify acquires Helicone"*: *"Helicone will continue operating in maintenance mode—security updates, bug fixes, and new models will keep shipping."* **Arize Phoenix** for OpenTelemetry-based tracing.

**Agent frameworks.**
- AWS: **Amazon Bedrock Agents** for managed agents with action groups; **AWS Strands Agents** SDK for modular agents; **Amazon Bedrock AgentCore** (GA October 13, 2025) — framework-agnostic managed runtime providing serverless session-isolated execution, persistent Memory, Identity, Gateway (tool access, MCP-compatible), Code Interpreter, Browser Use, and Observability primitives. AgentCore supports LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, and Strands.
- OSS: **LangGraph** — per LangChain changelog, *"After more than a year of powering agents at companies like Uber, LinkedIn, and Klarna, LangGraph is officially v1"* (released October 22, 2025); Replit and Elastic are also confirmed production users. Graph-based, durable execution, default LangChain agent runtime. **CrewAI** (role-based "crews", fastest time-to-prototype). **AutoGen / Microsoft Agent Framework** (conversational multi-agent, async event-driven, GAIA benchmark leader). **OpenAI Agents SDK** (handoffs, OpenAI-only). **Google ADK** (hierarchical agent tree). **Anthropic Claude Agent SDK**. **MetaGPT**, **OpenAgents** (A2A + MCP protocol, cross-framework interop).

### I. Observability, Security, Lineage
**AWS.** CloudWatch unifies metrics/logs/alarms; X-Ray traces requests across Lambda/ECS/SageMaker. IAM, KMS, VPC, PrivateLink, and Secrets Manager secure the stack. SageMaker ML Lineage Tracking and Model Cards document data → training → deployment lineage and model behavior for governance (SR 11-7, EU AI Act, GDPR audit needs).

**OSS.** Prometheus + Grafana, Loki, and Jaeger/Tempo deliver metrics/logs/traces via the OpenTelemetry Collector. Kubernetes RBAC + OPA/Gatekeeper + Kyverno + Vault + cert-manager handle policy and secrets. **OpenLineage** (LFAI&Data) and **Marquez** track ML pipeline lineage; **DataHub** / **Amundsen** provide catalog/lineage UIs.

---

## Workload-Type Architecture Views

### View 1 — Classical ML / Tabular (batch training, batch + real-time scoring)

**AWS-native flow.**
```
S3 (raw) → Glue / EMR (ETL & feature eng) → SageMaker Feature Store (offline=S3, online=DynamoDB)
        → SageMaker Pipelines (training) → SageMaker AMT (HPO) → SM Model Registry (approval)
        → SM Clarify (bias / explainability)
        → (a) SM Batch Transform on schedule → S3 / Redshift
        → (b) SM Real-Time Endpoint (auto-scaling), online features from Feature Store
              → CloudWatch + SM Model Monitor (data quality, model quality, bias drift)
```

**OSS/K8s flow.**
```
MinIO/S3 + Iceberg → Spark on K8s / Ray Data (ETL) → Feast (offline=Iceberg, online=Redis)
        → Kubeflow Pipelines / Flyte / Argo (training DAG) → Katib (HPO) → MLflow Registry
        → (a) Argo CronWorkflow → Ray Data / Spark batch inference → MinIO results
        → (b) KServe InferenceService (MLServer/Triton predictor), Istio routing, HPA on QPS
              → Evidently drift report scheduled from production capture logs;
                Prometheus + Grafana dashboards
```

### View 2 — Real-Time / Online Inference (low-latency, autoscaling)

**AWS-native.** Client → CloudFront/API Gateway/ALB → SageMaker Real-Time Endpoint (multi-AZ, auto-scaling, optional Inference Components for fine-grained scaling) ← Online features from SM Feature Store DynamoDB (sub-10 ms p99). Data Capture writes a sampled stream of requests+responses to S3; SM Model Monitor compares against baselines hourly/daily; alerts via CloudWatch + EventBridge. For very low cold-start: Serverless Inference; for spiky/large payloads: Async Inference.

**OSS/K8s.** Client → Istio/Envoy ingress → KServe `InferenceService` (Knative scale-to-zero or HPA) → predictor pod (Triton/MLServer/BentoML) with optional transformer for pre/post ← Feast Feature Server (Redis online store). Captured logs to MinIO; Evidently / Arize Phoenix compute drift on schedule; Prometheus scrapes latency/throughput. Canary/blue-green via KServe traffic split or Argo Rollouts.

### View 3 — LLM / GenAI Workflows

#### 3a. RAG Pipeline
**AWS.**
```
Docs → S3 → Bedrock Knowledge Base (parse via Bedrock Data Automation; chunk
   [semantic/hierarchical/fixed]; embed with Titan/Cohere) → OpenSearch Serverless vector
   or Aurora pgvector or S3 Vectors
User → API Gateway → Lambda → Bedrock RetrieveAndGenerate API
   → Bedrock FM (Claude, Nova, Llama, Mistral) with retrieved context + citations
   → Bedrock Guardrails (denied topics, PII redaction, contextual grounding)
   → response
Observability: CloudWatch + Bedrock model-invocation logs + optional Langfuse layered on top.
```

**OSS/K8s.**
```
Docs → MinIO → LangChain/LlamaIndex ingestion DAG (Argo/Flyte) → embed (sentence-transformers
   or vLLM-served embedding model) → Milvus / Qdrant / Weaviate / pgvector
User → FastAPI → LangChain/LlamaIndex retriever → vLLM via KServe LLMInferenceService
   (prefix-cache aware routing for repeated context) → NeMo Guardrails (input + output)
   → response
Observability: Langfuse traces every step; Ragas evals nightly against golden set;
   DeepEval/pytest CI gate; TruLens or Phoenix on sampled prod traffic.
```

#### 3b. Fine-Tuning Pipeline
**AWS.**
```
Dataset on S3 (Parquet/JSONL) → SageMaker HyperPod (Slurm or EKS) provisioned cluster
   → HyperPod Recipe (e.g., llama-3-70b-LoRA, mixtral-8x22b-SFT, deepseek-r1-qwen-14b)
   → SMDDP/SMP libraries, auto-resume on node failure, automatic checkpointing to S3
   → Evaluation step (ROUGE/BLEU or LLM-judge via Bedrock)
   → Merged model artifact in S3 → SM Model Registry
   → Deploy: SM Real-Time Endpoint with LMI container (vLLM/TGI) OR import to Bedrock
     Custom Models / Nova Forge for managed inference.
```

**OSS/K8s.**
```
Dataset on MinIO → Kubeflow Trainer PyTorchJob (or Ray Train on KubeRay) with FSDP/DeepSpeed
   and HuggingFace PEFT/LoRA, or NeMo Framework / Megatron / Axolotl recipe
   → Volcano / KAI Scheduler / NVIDIA device plugin handles GPU scheduling and gang scheduling
   → MLflow logs metrics; checkpoint shards to MinIO
   → Eval step using Ragas/DeepEval or lm-evaluation-harness
   → Adapter merged + uploaded to MLflow Registry / HuggingFace Hub
   → KServe LLMInferenceService rolls the new model version with canary traffic split.
```

#### 3c. Agentic Pipeline
**AWS.**
```
User → API Gateway → Bedrock Agent (orchestrator FM) → Action Groups (Lambda tools)
   → Bedrock AgentCore primitives (GA Oct 13, 2025):
       • Runtime (serverless session-isolated, long-running)
       • Memory (persistent context across sessions)
       • Identity (OAuth/IAM-backed credentials for tools)
       • Gateway (managed tool invocation, MCP-compatible)
       • Code Interpreter / Browser Use
       • Observability (traces to CloudWatch)
   → Knowledge Base retrieval / external APIs → Guardrails → user
Multi-agent: A2A protocol or Strands sub-agents orchestrated by AgentCore.
```

**OSS/K8s.**
```
User → FastAPI/Streamlit → LangGraph state machine (StateGraph, conditional edges,
   checkpointer = Postgres/Redis for durable execution and human-in-the-loop)
   → Tool nodes call HTTP/MCP servers, vector retrieval, code-exec sandboxes (Firecracker)
   → vLLM/llm-d via KServe for the FM calls; KV-cache aware routing for multi-step tool loops
   → NeMo Guardrails or Guardrails AI on each step
   → Langfuse instrumentation captures every span; Phoenix shows traces; DeepEval CI runs
     agent-specific evals (tool-call correctness, plan quality)
Multi-agent: LangGraph subgraphs, CrewAI crews, or AutoGen GroupChat;
   A2A or MCP for cross-framework interop.
```

---

## Commentary: Trade-offs and When Each Fits

### Trade-offs at a glance

| Dimension | AWS-Native | OSS / Kubernetes |
|---|---|---|
| Operational burden | Low — managed everything | High — you run the control plane, GPU schedulers, registries |
| Time-to-production | Days to weeks for a baseline | Weeks to months for a comparable platform |
| Vendor lock-in | High — proprietary APIs (SageMaker Pipelines, Bedrock) | Low — Kubernetes/OCI/MLflow are portable |
| Portability / multi-cloud | Limited (SageMaker is AWS-only) | Native via Kubernetes; same stack runs on EKS/GKE/AKS/on-prem |
| Flexibility / customization | Constrained to AWS service surface | Unlimited — swap any component |
| LLM serving cutting-edge | Bedrock managed FMs are SOTA; self-hosted is via LMI containers (vLLM inside) | KServe + vLLM + llm-d is the bleeding edge for self-hosted optimizations |
| GPU economics at scale | HyperPod is best-in-class for AWS GPUs/Trainium | Better when you control hardware (on-prem, colocated GPUs) |
| Talent requirements | SageMaker generalists | Kubernetes + ML platform engineers (scarcer) |
| Compliance | Inherits AWS compliance posture | Requires careful component selection and platform engineering |
| Ecosystem velocity | Fast (re:Invent yearly drops) | Faster (CNCF + LFAI + Linux Foundation cycle in weeks) |

### When to choose AWS-native
- Already an AWS-committed enterprise.
- Small ML platform team (1–10 people) that wants to ship models, not run K8s.
- Heavy use of foundation models via Bedrock and managed agents (AgentCore).
- Regulated industries that benefit from inherited AWS compliance.
- Workloads where Trainium / Inferentia economics matter.

### When to choose Kubernetes/OSS
- Multi-cloud or hybrid (cloud + on-prem GPU) is a strategic requirement.
- Cutting-edge LLM serving optimizations matter (prefill/decode disaggregation, KV-cache aware routing, custom inference graphs).
- Heavy customization needs (custom training loops, novel parallelism strategies, custom guardrails policies).
- Existing Kubernetes platform investment with strong platform engineering.
- Cost optimization at large scale where you can amortize platform engineering against many models or massive inference workloads.

### Common hybrid patterns
1. **EKS + Kubeflow/KServe + AWS data services.** Run Kubeflow Pipelines, KServe, vLLM on EKS while using S3, Glue, Lake Formation, OpenSearch, IAM, and CloudWatch as the substrate. AWS publishes reference architectures for SageMaker components from Kubeflow Pipelines (submit Processing/Training/HPO jobs from KFP) and for HyperPod orchestrated by EKS.
2. **SageMaker + managed MLflow.** Use SageMaker Studio and Training jobs but log/track to managed MLflow inside SageMaker (avoids running an MLflow server yourself while keeping portable artifacts).
3. **Bedrock + OSS agent framework.** Use Bedrock as the FM provider but build agents in LangGraph/CrewAI/AutoGen, hosting them on AgentCore Runtime — framework portability with managed infrastructure.
4. **OSS vector DB on AWS.** Run Milvus or Qdrant on EKS while consuming Bedrock FMs for embeddings + generation.
5. **Hybrid orchestration.** Amazon MWAA (managed Airflow) calling SageMaker Pipelines for AWS-native steps and Argo Workflows for K8s-native steps via Step Functions glue.

---

## Recommendations

**Stage 0 — Profile your team and workloads (1 week).**
- If team size ≤ 10 ML engineers and AWS-only: default to AWS-native. Move to Stage 1A.
- If team size ≥ 15 and multi-cloud / on-prem / heavy LLM: default to Kubernetes/OSS. Move to Stage 1B.
- If unsure: pilot one workload of each type on both stacks for 4 weeks.

**Stage 1A — AWS-native baseline (4–6 weeks).**
- Adopt SageMaker Unified Studio + Pipelines + Model Registry + Model Monitor.
- Standardize the data layer on S3 + Glue Data Catalog + Lake Formation; use S3 Tables (Iceberg) for new feature data.
- For LLMs: Bedrock first (Knowledge Bases + Guardrails), AgentCore for agents.
- *Threshold to revisit:* if you hit Bedrock quota limits, need a model not on Bedrock, or need sub-X-ms p99 below what Bedrock or SageMaker Endpoints can deliver, evaluate self-hosted vLLM on SageMaker Endpoints LMI or move to OSS.

**Stage 1B — OSS/K8s baseline (12–16 weeks).**
- Foundation: EKS (or equivalent) + Istio + cert-manager + ArgoCD + OPA.
- Storage: MinIO/S3 + Iceberg + Apache Polaris (or Glue catalog if on AWS).
- Workflow: pick Kubeflow Pipelines (broadest), Flyte (typed/ML-focused), or Argo Workflows (most generic) — one only.
- Training: Kubeflow Trainer + Ray Train on KubeRay; Katib for HPO.
- Registry/tracking: MLflow.
- Features: Feast.
- Serving: KServe + Triton/MLServer for classical; KServe LLMInferenceService + vLLM + llm-d for LLMs.
- Monitoring: Evidently (classical) + Langfuse + Arize Phoenix (LLM) + Prometheus/Grafana/Loki.
- LLM stack: LangChain or LlamaIndex; Milvus or Qdrant; Ragas + DeepEval + TruLens; NeMo Guardrails.
- *Threshold to revisit:* if platform-engineer headcount/utilization exceeds 30% of ML org effort, or if a managed alternative now matches your need, reconsider hybrid.

**Stage 2 — Hybridize where it pays.**
- Add managed MLflow on SageMaker if running MLflow ops is painful.
- Adopt Bedrock for FM access on AWS even if the rest is OSS (cheaper than running 70B+ vLLM clusters for low-volume use cases).
- Move flat-traffic, low-skill-team workloads to SageMaker Endpoints; keep custom LLM serving on KServe.

**Stage 3 — Govern and harden (ongoing).**
- Lineage: OpenLineage (or SageMaker Lineage) on every pipeline.
- Evaluations as CI gates: DeepEval pytest tests on every PR for LLM apps; Evidently drift tests for classical models.
- Guardrails: Bedrock Guardrails or NeMo Guardrails in production for all customer-facing LLM endpoints.
- Cost guardrails: token-level quotas via Envoy AI Gateway or Bedrock provisioned throughput.

**Benchmarks/thresholds that should change the recommendation.**
- If p99 token latency requirements drop below ~80 ms for streaming LLMs: invest in self-hosted vLLM + llm-d.
- If monthly Bedrock spend > $50K and traffic is predictable: evaluate provisioned throughput or migrate hot paths to KServe + vLLM on dedicated GPUs.
- If model count > 200 in production: invest in multi-model serving (Seldon Core v2 / Triton / SageMaker Multi-Model / Inference Components).
- If you regularly fine-tune models above ~13B parameters: justify HyperPod or a dedicated KubeRay GPU cluster; ad-hoc training jobs become uneconomical.

---

## Caveats
- **Tooling velocity is high.** KServe v0.16 (LLMInferenceService), Bedrock AgentCore (GA Oct 13, 2025), HyperPod recipes, and Iceberg table-store integrations are all under 18 months old; specific feature sets will shift. Verify current GA status before architectural commitments.
- **TorchServe is deprecated.** Per GitHub issue #3396 on pytorch/serve, "This repository was archived by the owner on Aug 7, 2025. It is now read-only." Existing deployments will continue to work but new projects should use Triton, vLLM, MLServer, BentoML, or Ray Serve.
- **TensorFlow Serving** is not formally deprecated but development cadence has slowed materially; not recommended for greenfield builds.
- **Helicone** went into maintenance mode after Mintlify's March 3, 2026 acquisition; Langfuse migration guides have been published. Treat any "Helicone-as-platform" architecture as legacy.
- **AgentCore vs. open agent frameworks** is not either/or — AgentCore is designed to run LangGraph, CrewAI, AutoGen, OpenAI Agents SDK, and Strands as the agent code, with AWS providing only the managed primitives. Architecturally similar to KServe being a control plane for vLLM as the runtime.
- **Vendor performance/cost claims** in this report (e.g., BentoCloud compute-cost reductions, llm-d throughput numbers, NVIDIA's "1.4× detection rate" for NeMo Guardrails) come from vendor marketing or selected benchmarks and should be validated against your workload.
- **Diagrams are reference architectures**, not implementation guides; production architectures must add multi-account/multi-region patterns (especially on AWS), zero-trust networking, secrets rotation, and disaster recovery — which this comparison intentionally treats lightly given its architectural-mapping focus.
- **Where sources conflicted** (e.g., the Databricks-Tabular acquisition price — TechCrunch/Bloomberg reported "nearly $2 billion" while Databricks CEO Ali Ghodsi told CNBC "over $1 billion," or the "best" agent framework), this report cites the highest-quality available source or notes the disagreement explicitly rather than silently picking one.