# Observability

> Metrics, logs, traces, and profiles — how you understand a running system and the
> failure mode you did not write a test for. This is the concepts page; the tools
> have their own folders alongside it.

## Mental model

| Signal | Answers | Tooling |
|---|---|---|
| Metrics | What is happening, numerically | [Prometheus](../Prometheus/), [Grafana](../Grafana/) |
| Logs | What happened, as events | Loki |
| Traces | Where time went across services | Tempo / Jaeger |
| Profiles | Where CPU/memory cost went | Pyroscope |
| Alerts | When a human must act | Alertmanager, Grafana Alerting |
| Dashboards | How a human investigates | [Grafana](../Grafana/) |

## Concepts to add

- [ ] OTel Collector pipeline (receive → process → export)
- [ ] Golden signals; RED and USE methods
- [ ] Observability architecture for a multi-service app
- [ ] Cost of observability — cardinality, retention, sampling

## See also

- Tools in this category: [Prometheus](../Prometheus/) · [Grafana](../Grafana/) · [OpenTelemetry](../OpenTelemetry/) · [Alloy](../Alloy/)
- [SRE](../../SRE/) — observability is the input to reliability work
- Labs: [.labs/Observability](../../../.labs/Observability/)
