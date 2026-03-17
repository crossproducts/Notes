# Prometheus

Prometheus is an open-source systems monitoring and alerting toolkit originally built at SoundCloud. It is now a standalone project maintained by the Cloud Native Computing Foundation (CNCF).

## Key Features

- **Multi-dimensional data model** — time series identified by metric name and key/value label pairs
- **PromQL** — a powerful and flexible query language to query and aggregate metrics
- **Pull-based collection** — scrapes metrics from targets over HTTP at configurable intervals
- **No external storage dependency** — operates as a standalone single binary
- **Service discovery** — supports Kubernetes, Consul, DNS, static configs, and more
- **Alerting** — integrates with Alertmanager for flexible alert routing and notification

## Architecture

Prometheus scrapes metrics from instrumented jobs (exporters or direct instrumentation), stores all scraped samples locally, and runs rules over the data to aggregate time series or trigger alerts.

## References

- [Youtube: PavanEithepu - PromQL](https://youtu.be/FLT0d8fyhK4?si=8pGxWCLPCbyZ4-CX)
- [Prometheus Official Docs](https://prometheus.io/docs/)
