# MLOps — Machine Learning Operations

> The practice of deploying, monitoring, and maintaining ML models in production reliably and efficiently.
> See [!NannyML](../!NannyML/) for model monitoring and [✔MLflow](../✔MLflow/) for experiment tracking notes.

## MLOps Lifecycle

```
Data Collection & Versioning
        │
        ▼
Feature Engineering & Validation
        │
        ▼
Model Training & Experiment Tracking  ←── MLflow, W&B, Comet
        │
        ▼
Model Evaluation & Validation
        │
        ▼
Model Registry  ←── MLflow Model Registry, HuggingFace Hub
        │
        ▼
Deployment  ←── REST API, batch, streaming, edge
        │
        ▼
Monitoring & Drift Detection  ←── NannyML, Evidently, Prometheus → [!NannyML](../!NannyML/)
        │
        ▼
Retraining / Feedback Loop
```

## Experiment Tracking

| Tool | Notes | Repo Link |
|---|---|---|
| MLflow | Open-source, runs/params/metrics/artifacts | [✔MLflow](../✔MLflow/) |
| Weights & Biases (W&B) | Rich UI, sweeps, reports | — |
| Comet ML | Similar to W&B, good versioning | — |
| DVC | Data + model versioning, Git-based | — |
| Neptune.ai | Collaborative experiment management | — |

**Key things to track per experiment:**
- Hyperparameters
- Dataset version / split
- Training metrics (loss curves, val metrics)
- Model artefacts (weights, config)
- Environment (library versions, hardware)
- Tags (run description, hypothesis)

## Model Registry

A central store for versioned, validated models.
```
Stages: Staging → Production → Archived

MLflow Model Registry workflow:
  1. Log model during training: mlflow.sklearn.log_model(model, "model")
  2. Register: mlflow.register_model(run_uri, "MyModel")
  3. Transition to Production via UI or API
  4. Load: mlflow.pyfunc.load_model("models:/MyModel/Production")
```

## Deployment Patterns

| Pattern | Description | Use Case |
|---|---|---|
| REST API | Model wrapped in FastAPI/Flask endpoint | Real-time, low-latency requests |
| Batch inference | Run model on large datasets on schedule | Daily/weekly scoring jobs |
| Streaming | Model consumes event stream (Kafka) | Real-time pipelines → [!Apache-Kafka](../!Apache-Kafka/) |
| Edge deployment | Model on device (ONNX, TFLite, CoreML) | Mobile, IoT, offline |
| Shadow mode | New model runs silently alongside production | Safe rollout / comparison |
| A/B testing | Route % of traffic to new model | Gradual rollout |
| Canary | Gradual traffic shift to new model | Risk-controlled rollout |
| Blue/Green | Full traffic switch with instant rollback | Zero-downtime deploys |

## Feature Stores

Centralised store for computed features shared across training and serving.

| Tool | Notes |
|---|---|
| Feast | Open-source, offline + online store |
| Tecton | Managed, enterprise feature platform |
| Hopsworks | Open-source, end-to-end ML platform |
| Vertex AI Feature Store | Google Cloud managed |
| SageMaker Feature Store | AWS managed |

**Why needed:** Prevents training-serving skew — same feature transformations applied at train time and inference time.

## CI/CD for ML

```
Code PR
  │
  ├── Unit tests (data validation, model code)
  ├── Integration tests (pipeline end-to-end)
  ├── Model quality gate (metrics must exceed threshold)
  └── Deploy to staging
          │
          └── Manual approval → Deploy to production
```

**Tools:** GitHub Actions, Jenkins, GitLab CI, Kubeflow Pipelines, Metaflow, Prefect, Airflow → [!Apache-Airflow](../!Apache-Airflow/)

## Model Monitoring

| What to Monitor | Tool | Notes |
|---|---|---|
| Data/feature drift | NannyML, Evidently | Distribution shift in input features |
| Prediction drift | NannyML CBPE | Output distribution changes |
| Performance degradation | NannyML, Evidently | When ground truth is available |
| Latency & throughput | Prometheus, Grafana | Infrastructure health → [.Prometheus](../.Prometheus/) |
| Error rates | Sentry, Datadog | Failed predictions, exceptions |
| Data quality | Great Expectations | Missing values, schema violations |

See [!NannyML](../!NannyML/) for detailed model monitoring notes.

## Retraining Strategies

| Strategy | Trigger | Notes |
|---|---|---|
| Scheduled | Time-based (weekly, monthly) | Simple, may retrain unnecessarily |
| Drift-triggered | Drift metric exceeds threshold | More precise, requires monitoring |
| Performance-triggered | Metric drops below threshold | Needs ground truth labels |
| Online learning | Continuous incremental updates | Complex, not suitable for all models |

## Infrastructure

| Layer | Tools |
|---|---|
| Containerisation | Docker, Kubernetes → [.Kubernetes](../.Kubernetes/) |
| Compute | AWS SageMaker, GCP Vertex AI, Azure ML, on-prem GPU |
| Orchestration | Airflow → [!Apache-Airflow](../!Apache-Airflow/), Prefect, Kubeflow |
| Serving | FastAPI, BentoML, TorchServe, Triton Inference Server |
| Monitoring | Prometheus → [.Prometheus](../.Prometheus/), Grafana, NannyML → [!NannyML](../!NannyML/) |
| Storage | S3, GCS, Azure Blob (artefacts), PostgreSQL, Redis (features) |

## References

- [!NannyML](../!NannyML/) — Model monitoring and drift detection
- [✔MLflow](../✔MLflow/) — Experiment tracking
- [!Apache-Airflow](../!Apache-Airflow/) — Pipeline orchestration
- [.Kubernetes](../.Kubernetes/) — Container orchestration
- [.Prometheus](../.Prometheus/) — Metrics and alerting
- [!Apache-Kafka](../!Apache-Kafka/) — Streaming inference
- [ai-data-readme.md](ai-data-readme.md) — Data management
- [ai-ethics-and-safety.md](ai-ethics-and-safety.md) — Model cards, bias monitoring
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [Evidently AI](https://www.evidentlyai.com/)
