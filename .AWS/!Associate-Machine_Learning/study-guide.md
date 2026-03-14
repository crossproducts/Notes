# AWS Certified Machine Learning – Associate Study Guide

---

## Content Domain 1: Data Preparation for Machine Learning (ML)

### Data Collection & Ingestion

- **S3**: Primary data lake storage for ML datasets. Supports versioning, lifecycle policies, encryption.
- **S3 Event Notification**: Trigger Lambda, SNS, SQS on new data arrivals.
- **Amazon EventBridge**: Advanced event routing — trigger SageMaker Pipelines, Lambda, Step Functions on S3 events, schedule jobs, react to SageMaker events.
- **AWS Glue**: Serverless ETL — crawl data sources, build Data Catalog, transform data with PySpark/Python.
- **AWS Glue DataBrew**: Visual data preparation and profiling without code.
- **Amazon Kinesis Data Streams**: Real-time streaming ingest; custom consumers, replay capability.
- **Amazon Kinesis Data Firehose**: Fully managed delivery to S3, Redshift, OpenSearch; supports transformations via Lambda.
- **Amazon Kinesis Data Analytics**: Real-time SQL or Apache Flink processing on streaming data.
- **AWS DMS (Database Migration Service)**: Migrate on-prem databases to AWS for ML use.
- **AWS DataSync**: High-speed transfer of on-prem data to S3, EFS, FSx.

### Storage Options for ML

| Service | Best For |
|---|---|
| Amazon S3 | Scalable object store; training datasets, model artifacts |
| Amazon EFS | Shared NFS; multi-instance training access |
| Amazon FSx for Lustre | High-throughput, low-latency access to hundreds of TBs; ideal for large-scale SageMaker training across multiple instances |
| Amazon EBS | Block storage; single-instance, fast local disk |
| Amazon Redshift | Structured data warehouse; SQL-based feature engineering |
| Amazon RDS / Aurora | Relational DB; structured training data |
| Amazon DynamoDB | NoSQL; low-latency feature store lookups |

### Data Exploration & Profiling

- **Amazon SageMaker Data Wrangler**: GUI-based data exploration, transformation, feature engineering; exports to SageMaker Pipelines or Feature Store.
- **AWS Glue DataBrew**: Profile datasets for missing values, duplicates, distributions.
- **Amazon Athena**: Serverless SQL on S3; explore raw datasets without moving data.
- **Amazon QuickSight**: BI visualization with ML-powered insights (anomaly detection, forecasting).

### Feature Engineering

- **Normalization / Standardization**: Scale numerical features (MinMax, Z-score) to prevent feature dominance.
- **One-Hot Encoding**: Convert categorical variables to binary columns.
- **Label Encoding**: Assign integer codes to categories; use only for ordinal data.
- **Binning**: Group continuous values into discrete buckets.
- **Log Transformation**: Reduce skew in distributions.
- **TF-IDF / Bag of Words**: Text feature extraction for NLP.
- **PCA (Principal Component Analysis)**: Dimensionality reduction; removes correlated features.
- **Feature Importance**: Use tree-based models or SHAP to rank feature relevance.

### Handling Missing Data

- **Imputation**: Replace missing values with mean, median, mode, or model-predicted values.
- **Deletion**: Drop rows/columns with excessive missing values.
- **Indicator variable**: Add a binary flag indicating a value was missing.
- **SageMaker Data Wrangler**: Can automate many imputation strategies.

### Handling Imbalanced Data

- **Oversampling (SMOTE)**: Synthesize minority class samples.
- **Undersampling**: Reduce majority class.
- **Class weights**: Penalize misclassification of minority class during training.
- **Stratified split**: Ensure train/test/validation sets preserve class ratios.

### Data Splitting

- **Train / Validation / Test**: Typical split 70/15/15 or 80/10/10.
- **K-Fold Cross Validation**: Rotate folds; better for small datasets.
- **Stratified Sampling**: Preserve label distribution in splits.
- **Time-series split**: Respect temporal order; never use future data to predict the past.

### Amazon SageMaker Feature Store

- **Online Store**: Low-latency real-time inference lookups (DynamoDB-backed).
- **Offline Store**: Batch training data stored in S3 with Glue catalog integration.
- Supports feature groups, ingestion APIs, point-in-time queries.

### Data Labeling

- **Amazon SageMaker Ground Truth**: Human-in-the-loop labeling with auto-labeling using active learning.
- **Amazon SageMaker Ground Truth Plus**: Fully managed labeling workforce.
- **Amazon Mechanical Turk**: Crowdsourced labeling workforce.
- **Private workforce**: Internal team labeling via Ground Truth.

### Decision Tree — Data Source Selection

```
What is your data access pattern?
├── Batch training on large files → S3
├── Low-latency real-time features → SageMaker Feature Store (Online)
├── High-throughput multi-GPU training → FSx for Lustre
├── Multi-instance shared filesystem → EFS
├── SQL queries on S3 data → Athena
└── Structured relational data → RDS / Aurora / Redshift
```

### Decision Tree — Data Ingestion Method

```
How is data arriving?
├── Real-time streaming
│   ├── Need replay/custom consumer → Kinesis Data Streams
│   └── Deliver to S3/Redshift directly → Kinesis Firehose
├── Batch ETL
│   ├── Serverless Spark/Python → AWS Glue
│   └── Visual no-code transforms → Glue DataBrew
├── Event-triggered pipeline
│   ├── S3 new object → Lambda/SQS/SNS → S3 Event Notification
│   └── Complex routing / SageMaker → EventBridge
└── On-prem to AWS
    ├── Database migration → AWS DMS
    └── File transfer → AWS DataSync
```

---

## Content Domain 2: ML Model Development

### SageMaker Core Concepts

- **SageMaker Studio**: Web-based IDE for end-to-end ML — notebooks, experiments, pipelines, model registry.
- **SageMaker Notebooks**: Managed Jupyter instances; can attach to training clusters.
- **SageMaker Training Jobs**: Managed distributed training; supports custom Docker containers or built-in algorithms.
- **SageMaker Experiments**: Track hyperparameters, metrics, artifacts across training runs.
- **SageMaker Debugger**: Real-time training monitoring; detects vanishing gradients, overfitting.
- **SageMaker Clarify**: Bias detection (pre-training and post-training) and model explainability (SHAP values).
- **SageMaker Autopilot**: AutoML — automatically selects algorithm, performs feature engineering, tunes hyperparameters.
- **SageMaker JumpStart**: Pre-built models and solution templates (including foundation models).

### Built-In SageMaker Algorithms

| Algorithm | Type | Use Case |
|---|---|---|
| Linear Learner | Classification / Regression | Baseline linear models |
| XGBoost | Classification / Regression | Tabular data; gradient boosted trees |
| K-Means | Clustering | Grouping unlabeled data |
| PCA | Dimensionality Reduction | Feature reduction |
| Factorization Machines | Classification / Regression | Sparse data, recommendations |
| DeepAR | Time-Series Forecasting | Multiple related time series |
| BlazingText | NLP | Word2Vec, text classification |
| Object Detection | Computer Vision | Bounding box detection |
| Semantic Segmentation | Computer Vision | Pixel-level classification |
| Image Classification | Computer Vision | Multi-class image labels |
| Random Cut Forest (RCF) | Anomaly Detection | Unsupervised outlier scoring |
| IP Insights | Anomaly Detection | Unusual IP/account combinations |
| LDA (Latent Dirichlet Allocation) | NLP | Topic modeling |
| Seq2Seq | NLP | Machine translation, summarization |
| TabTransformer | Tabular | Attention-based tabular model |

### Regularization

- **L1 (Lasso)**: Adds penalty proportional to the **absolute value** of weights. Drives unimportant feature weights to exactly **0** — performs feature selection. Best when many features are irrelevant.
- **L2 (Ridge)**: Adds penalty proportional to the **square** of weights. Shrinks weights but rarely to zero. Best when all features contribute somewhat.
- **Elastic Net**: Combines L1 + L2; good for correlated features.
- **Dropout**: During training, randomly turns off neurons to prevent co-adaptation and overfitting.
- **Early Stopping**: Monitor validation loss; stop training when it stops improving to avoid overfitting.
- **Data Augmentation**: Artificially increase training data variety (flipping, cropping, noise) to reduce overfitting.
- **Batch Normalization**: Normalizes layer inputs during training; stabilizes and accelerates training.

### Hyperparameter Tuning

- **SageMaker Automatic Model Tuning (HPO)**: Bayesian optimization (recommended), Random search, Grid search.
- **Learning rate**: Most impactful hyperparameter; too high = divergence, too low = slow convergence.
- **Number of trees / depth**: Key for tree-based models (XGBoost).
- **Epochs and batch size**: Critical for neural networks.
- **Regularization coefficients**: Lambda (L2), Alpha (L1).
- **Dropout rate**: Controls regularization strength in neural networks.
- **Warm start**: Re-use prior tuning job results to speed up new HPO runs.

### Evaluation Metrics

| Metric | Use When |
|---|---|
| Accuracy | Classes are balanced |
| F1 Score | Dataset is imbalanced |
| Precision | False positives are costly (spam detection) |
| Recall | False negatives are costly (disease detection) |
| AUC-ROC | Evaluating model ranking ability; comparing models across thresholds |
| MAE (Mean Absolute Error) | Regression; interpretable errors in original units |
| RMSE (Root Mean Squared Error) | Regression; penalizes large errors more |
| MAPE | Regression; percentage error for business reporting |
| Log Loss | Probabilistic classification outputs |

### Decision Tree — Choosing Evaluation Metric

```
Regression or Classification?
├── Regression
│   ├── Want interpretable errors in original units → MAE
│   ├── Want to penalize large errors → RMSE
│   └── Want percentage error → MAPE
└── Classification
    ├── Dataset balanced → Accuracy
    ├── Dataset imbalanced
    │   ├── Both FP and FN matter equally → F1
    │   ├── FP is costly → Precision
    │   └── FN is costly → Recall
    └── Need threshold-independent ranking → AUC-ROC
```

### Decision Tree — Algorithm Selection

```
Supervised or Unsupervised?
├── Supervised
│   ├── Tabular data
│   │   ├── Classification or Regression → XGBoost, Linear Learner
│   │   └── Sparse data (recommendations) → Factorization Machines
│   ├── Time-series forecasting → DeepAR
│   ├── NLP
│   │   ├── Text classification / embeddings → BlazingText
│   │   └── Translation / summarization → Seq2Seq
│   └── Computer Vision
│       ├── Classify image → Image Classification
│       ├── Detect objects → Object Detection
│       └── Segment pixels → Semantic Segmentation
└── Unsupervised
    ├── Cluster data → K-Means
    ├── Reduce dimensions → PCA
    ├── Detect anomalies → Random Cut Forest
    └── Topic modeling → LDA
```

### Bias & Fairness (SageMaker Clarify)

- **Pre-training bias**: Measures bias in raw dataset before model is trained (Class Imbalance, Difference in Proportions of Labels).
- **Post-training bias**: Measures bias in model predictions (DPPL, Disparate Impact, Flip Test).
- **Explainability**: SHAP values indicate each feature's contribution to a prediction.
- Use Clarify in SageMaker Pipelines to automate bias checks as a pipeline step.

### Instance Types for Training

| Type | Use Case |
|---|---|
| ml.c5, ml.c6i | Compute-optimized; CPU training, feature processing |
| ml.m5, ml.m6i | General purpose; balanced memory and compute |
| ml.p3, ml.p4d | GPU-powered; deep learning training (NVIDIA V100/A100) |
| ml.g4dn, ml.g5 | GPU inference and lighter training workloads |
| ml.trn1 | AWS Trainium; cost-effective deep learning training |
| ml.inf1, ml.inf2 | AWS Inferentia; high-throughput low-cost inference |
| ml.r5 | Memory-optimized; large dataset training |

### Decision Tree — Instance Type Selection

```
Training or Inference?
├── Training
│   ├── Deep learning (neural networks) → p3/p4d (GPU) or trn1 (Trainium)
│   ├── Traditional ML (XGBoost, Linear) → c5/c6i (Compute)
│   └── Memory-intensive → r5
└── Inference / Hosting
    ├── High-throughput low-cost → inf1/inf2 (Inferentia)
    ├── Real-time GPU inference → g4dn/g5
    └── CPU-based serving → c5/m5
```

---

## Content Domain 3: Deployment and Orchestration of ML Workflows

### SageMaker Deployment Options

| Endpoint Type | Use Case |
|---|---|
| Real-Time Endpoint | Low-latency, synchronous predictions |
| Serverless Inference | Intermittent/unpredictable traffic; no capacity planning |
| Async Inference | Large payloads or long processing times (up to 15 min) |
| Batch Transform | Offline bulk inference on large datasets; no persistent endpoint |
| Multi-Model Endpoint (MME) | Host hundreds of models on single endpoint; cost saving |
| Multi-Container Endpoint | Run different containers on same endpoint (pipeline inference) |

### Deployment Strategies

- **Canary Deployment**: Releases new version to a small percentage of users first; validate before full rollout.
- **Linear Deployment**: Traffic shifts gradually and evenly over time (e.g., 10% more every 10 minutes).
- **Blue/Green Deployment**: Two identical environments; instant traffic switch; easy rollback.
- **Rolling Deployment**: Update one group of servers at a time; reduces downtime.
- **A/B Testing**: Two versions run simultaneously to compare performance (SageMaker supports weighted variant routing).
- **Shadow Mode**: New model receives traffic copy but responses not served to user; safe comparison.

### Decision Tree — Deployment Strategy

```
What is your rollout goal?
├── Minimize risk of bad release
│   ├── Small initial test group → Canary
│   └── Gradual traffic shift → Linear
├── Instant cutover with rollback → Blue/Green
├── Compare two model versions live → A/B Testing (variant weights)
├── Test new model without user impact → Shadow Mode
└── Update fleet progressively → Rolling Deployment
```

### Decision Tree — Inference Endpoint Type

```
What is your inference workload?
├── Low-latency real-time requests → Real-Time Endpoint
├── Infrequent / unpredictable traffic → Serverless Inference
├── Large payloads or slow models → Async Inference
├── Batch offline scoring → Batch Transform
├── Many models, cost saving → Multi-Model Endpoint
└── Sequential container pipeline → Multi-Container Endpoint
```

### SageMaker Pipelines

- Fully managed CI/CD for ML workflows.
- Steps: Data Processing, Training, Evaluation, Model Registration, Condition (gate), Transform, Clarify.
- Integrates with Model Registry for versioned model management.
- Triggered via EventBridge, Lambda, or manual execution.

### MLOps & CI/CD

- **SageMaker Model Registry**: Version, approve/reject, and deploy models; track lineage.
- **SageMaker Projects**: GitOps-based ML project templates with CodePipeline/CodeBuild integration.
- **AWS CodePipeline / CodeBuild**: Automate model build, test, deploy workflows.
- **SageMaker Model Cards**: Document model purpose, training data, evaluation, and intended use.
- **SageMaker Lineage Tracking**: Track data, training jobs, models, and endpoints in a lineage graph.

### Workflow Orchestration

- **SageMaker Pipelines**: Native ML pipeline orchestration.
- **AWS Step Functions**: General-purpose serverless workflow; coordinate SageMaker + other AWS services.
- **Apache Airflow (MWAA)**: Open-source DAG-based workflow scheduling on AWS managed Airflow.
- **AWS Lambda**: Event-driven compute; trigger pipelines, preprocess data, route inference requests.
- **EventBridge**: Trigger workflows on schedule or event (S3 upload, SageMaker job state change).

### Decision Tree — Workflow Orchestration Tool

```
What kind of orchestration do you need?
├── Pure ML pipeline (training → eval → deploy) → SageMaker Pipelines
├── Multi-service serverless workflow → Step Functions
├── Complex DAG scheduling with dependencies → MWAA (Airflow)
├── Event-triggered lightweight function → Lambda
└── Schedule or event-based trigger → EventBridge
```

### Containers & Frameworks

- SageMaker supports **custom Docker containers** for training and inference.
- Pre-built containers: TensorFlow, PyTorch, MXNet, Scikit-learn, Hugging Face, XGBoost.
- **AWS Deep Learning Containers (DLCs)**: Optimized pre-built containers for DL frameworks.
- **SageMaker Neo**: Compile models for edge/cloud targets; optimizes for hardware (also deploys to IoT Greengrass).
- Store container images in **Amazon ECR** (Elastic Container Registry).

### Edge Deployment

- **AWS IoT Greengrass**: Deploy models to edge devices; run inference locally.
- **SageMaker Neo**: Optimize and compile models for specific hardware targets (ARM, x86, NVIDIA Jetson).
- **SageMaker Edge Manager**: Monitor model performance on edge devices; update models OTA.

---

## Content Domain 4: ML Solution Monitoring, Maintenance, and Security

### Model Monitoring (SageMaker Model Monitor)

| Monitor Type | What It Detects |
|---|---|
| Data Quality Monitor | Statistical drift in input features vs. baseline |
| Model Quality Monitor | Degradation in prediction accuracy vs. ground truth |
| Bias Drift Monitor | Changes in bias metrics post-deployment |
| Feature Attribution Drift | Changes in SHAP-based feature importance over time |

- Schedules continuous monitoring jobs against a **baseline** (captured during training).
- Sends alerts to **CloudWatch** and **EventBridge** when violations occur.
- **SageMaker Clarify** runs inside Model Monitor for bias and explainability monitoring.

### Data Capture & Baseline

- Enable **Data Capture** on real-time endpoints to log inputs and outputs to S3.
- Run a **baseline job** (on training data) to generate statistics and constraints.
- Monitor compares live traffic against baseline to detect drift.

### Drift Types

- **Data Drift (Covariate Shift)**: Input feature distribution shifts from training data.
- **Concept Drift**: Relationship between features and labels changes over time.
- **Label Drift (Prior Probability Shift)**: Distribution of target labels changes.
- **Feature Attribution Drift**: Which features drive predictions changes significantly.

### Retraining Strategies

- **Scheduled retraining**: Retrain on a time-based cadence (weekly/monthly).
- **Trigger-based retraining**: Retrain when Model Monitor detects violations or accuracy degrades.
- **Continuous learning**: Incrementally update model with new data as it arrives.
- Use **SageMaker Pipelines + EventBridge** to automate triggered retraining workflows.

### Decision Tree — When to Retrain

```
Is model performance degrading?
├── Yes — what type?
│   ├── Input features drifting → Data Quality Monitor alert → Retrain with new data
│   ├── Prediction accuracy dropping → Model Quality Monitor → Retrain + re-evaluate
│   ├── Bias metrics shifting → Bias Drift Monitor → Investigate + retrain
│   └── Feature importance changing → Attribution Drift → Review features + retrain
└── No → Schedule periodic retraining as preventive maintenance
```

### CloudWatch & Observability

- **Amazon CloudWatch**: Collect endpoint metrics (InvocationErrors, Latency, ModelLatency, CPUUtilization).
- **CloudWatch Logs**: Capture container logs from training and inference.
- **CloudWatch Alarms**: Alert on threshold breaches (e.g., error rate > 5%).
- **AWS X-Ray**: Distributed tracing for inference request paths.
- **SageMaker Experiments**: Compare training runs; track loss curves and metrics over time.

### Security — IAM & Permissions

- **IAM Roles**: Assign least-privilege roles to SageMaker execution roles.
- **Resource-based policies**: Control who can invoke endpoints or access S3 buckets.
- **SageMaker Role**: Needs permissions for S3, ECR, CloudWatch, and specific SageMaker APIs.
- **Condition keys**: Restrict actions by VPC, tag, or request source.

### Security — Network Isolation

- **VPC**: Run SageMaker training jobs and endpoints in a private VPC.
- **PrivateLink / VPC Endpoints**: Keep traffic between SageMaker and S3/ECR within AWS network (no public internet).
- **Network Isolation mode**: Training containers cannot make outbound network calls.
- **Security Groups & NACLs**: Control inbound/outbound traffic for SageMaker resources.

### Security — Encryption

- **Encryption at rest**: S3 (SSE-S3, SSE-KMS), EBS, EFS all support KMS encryption.
- **Encryption in transit**: TLS for all SageMaker API calls and endpoint invocations.
- **AWS KMS**: Manage encryption keys; use customer-managed keys (CMK) for compliance.
- **SageMaker inter-container traffic encryption**: Enable for distributed training jobs.

### Security — Compliance & Governance

- **AWS Macie**: Detect sensitive/PII data in S3 buckets used for ML datasets.
- **AWS Config**: Track configuration changes to SageMaker and associated resources.
- **AWS CloudTrail**: Log all SageMaker API calls for audit; detect unauthorized access.
- **Service Control Policies (SCPs)**: Org-level guardrails preventing non-compliant ML deployments.
- **SageMaker Model Cards**: Document data provenance, fairness, and intended use for governance.

### Decision Tree — Security Concern

```
What is your security requirement?
├── Restrict who can access endpoints/models → IAM Roles + Resource Policies
├── Keep traffic off public internet → VPC + PrivateLink + VPC Endpoints
├── Encrypt sensitive training data → S3 KMS + EBS KMS + inter-container encryption
├── Audit all API activity → CloudTrail
├── Detect PII in datasets → Amazon Macie
├── Prevent bias / ensure fairness → SageMaker Clarify + Bias Drift Monitor
└── Document model for compliance → SageMaker Model Cards
```

### Cost Optimization

- Use **Spot Instances** for training jobs (up to 90% savings); enable checkpointing for fault tolerance.
- Use **Serverless Inference** for infrequent workloads to avoid idle endpoint costs.
- Use **Multi-Model Endpoints** to consolidate many models on shared infrastructure.
- Use **SageMaker Savings Plans** for committed usage discounts on training and hosting.
- Right-size instance types: use Compute (C) for CPU-bound, GPU (P/G) only when needed.
- Use **Batch Transform** instead of persistent endpoints for offline scoring.
- Monitor with **AWS Cost Explorer** and set **Budgets** alerts.

### Key AWS Services Quick Reference

| Service | Purpose |
|---|---|
| Amazon S3 | Dataset storage, model artifacts |
| AWS Glue | ETL, Data Catalog |
| Amazon Athena | SQL on S3 |
| Amazon Kinesis | Real-time data streaming |
| SageMaker Studio | ML IDE |
| SageMaker Pipelines | ML CI/CD orchestration |
| SageMaker Feature Store | Feature storage (online + offline) |
| SageMaker Clarify | Bias detection + explainability |
| SageMaker Model Monitor | Drift + quality monitoring |
| SageMaker Autopilot | AutoML |
| SageMaker Neo | Model compilation + optimization |
| SageMaker Ground Truth | Data labeling |
| Amazon ECR | Container registry |
| AWS Step Functions | General workflow orchestration |
| Amazon EventBridge | Event-driven triggers |
| AWS Lambda | Serverless event-driven compute |
| AWS CloudTrail | API audit logging |
| Amazon CloudWatch | Metrics, logs, alarms |
| AWS KMS | Encryption key management |
| Amazon Macie | PII/sensitive data detection |
| AWS IAM | Access control |
| Amazon FSx for Lustre | High-throughput training storage |
| Amazon EFS | Shared file system for multi-instance |
