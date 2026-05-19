# OpenTelemetry (OTel)

> [!NOTE]   
> **Status**: In Progress
---

> You dont *need* OTel   
> Otel Standerdizes the collection of logs, metrics, traces to downstram

<div style="text-align: center;">

```
App / Node
↓
OTEL SDK (inside app OR auto-instrumentation)⭐
↓
OTel Collector (sidecar / daemon / service)⭐
↓
Metrics → Prometheus / AWS Managed Prometheus (AMP)
Logs    → Elasticsearch / AWS OpenSearch  
Traces  → Tempo / Jeager  / AWS X-Ray
↓
Grafana 
```
</div>

<div style="text-align: center;">

```
[OTel Collector]
↓
[Kafka] 
↓
[Elasticsearch(logs)]
[Tempo (traces)]
[Prometheus(metricsviaremotewrite)]
↓
Grafana 
```
</div>