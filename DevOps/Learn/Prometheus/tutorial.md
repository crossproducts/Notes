# Prometheus Tutorial

A hands-on guide to getting started with Prometheus — from installation to writing queries and setting up alerts.

---

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Querying with PromQL](#querying-with-promql)
4. [Alerting](#alerting)
5. [Exporters](#exporters)

---

## Installation

<details>
<summary>Linux (Binary)</summary>

```bash
# Download the latest release
wget https://github.com/prometheus/prometheus/releases/download/v2.51.0/prometheus-2.51.0.linux-amd64.tar.gz

# Extract
tar xvfz prometheus-2.51.0.linux-amd64.tar.gz
cd prometheus-2.51.0.linux-amd64

# Run
./prometheus --config.file=prometheus.yml
```

</details>

<details>
<summary>Docker</summary>

```bash
docker run -d \
  -p 9090:9090 \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

</details>

---

## Configuration

<details>
<summary>Basic prometheus.yml</summary>

```yaml
global:
  scrape_interval: 15s       # How often to scrape targets
  evaluation_interval: 15s   # How often to evaluate rules

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "node_exporter"
    static_configs:
      - targets: ["localhost:9100"]
```

</details>

<details>
<summary>Service Discovery (Kubernetes)</summary>

```yaml
scrape_configs:
  - job_name: "kubernetes-pods"
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: "true"
```

</details>

---

## Querying with PromQL

<details>
<summary>Instant Queries</summary>

```promql
# Current CPU usage per core
rate(node_cpu_seconds_total{mode!="idle"}[5m])

# Total HTTP requests
http_requests_total

# Filter by label
http_requests_total{job="api", status="200"}
```

</details>

<details>
<summary>Range Queries & Aggregation</summary>

```promql
# Average CPU usage over 5 minutes
avg(rate(node_cpu_seconds_total{mode!="idle"}[5m])) by (instance)

# Sum of requests by job
sum(http_requests_total) by (job)

# 95th percentile request latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

</details>

---

## Alerting

<details>
<summary>Alerting Rules (alert.rules.yml)</summary>

```yaml
groups:
  - name: example_alerts
    rules:
      - alert: HighCPUUsage
        expr: avg(rate(node_cpu_seconds_total{mode!="idle"}[5m])) by (instance) > 0.85
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High CPU on {{ $labels.instance }}"
          description: "CPU usage is above 85% for more than 2 minutes."

      - alert: InstanceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{ $labels.instance }} is down"
```

</details>

<details>
<summary>Alertmanager Route Config</summary>

```yaml
route:
  receiver: "slack-notifications"
  group_by: ["alertname", "instance"]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 3h

receivers:
  - name: "slack-notifications"
    slack_configs:
      - api_url: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
        channel: "#alerts"
```

</details>

---

## Exporters

<details>
<summary>Node Exporter (System Metrics)</summary>

```bash
# Run Node Exporter to expose host-level metrics (CPU, memory, disk, etc.)
docker run -d \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  quay.io/prometheus/node-exporter \
  --path.rootfs=/host
```

Metrics available at `http://localhost:9100/metrics`.

</details>

<details>
<summary>Blackbox Exporter (Endpoint Probing)</summary>

```yaml
# prometheus.yml
scrape_configs:
  - job_name: "blackbox"
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://example.com
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - target_label: instance
        source_labels: [__param_target]
      - target_label: __address__
        replacement: localhost:9115
```

</details>
