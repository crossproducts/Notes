# Observability

> **Status:** 🔴 Pending — umbrella skeleton; deep-dive notes live in sibling folders.

## Why it matters (2026)

Observability is how you understand a system you did not write the failure mode for.
The 2026 mental model spans four signals plus the human layer on top.

## Mental model

| Signal | Answers | Tooling here |
|---|---|---|
| Metrics | What is happening, numerically | [Prometheus](../Prometheus/), [Grafana](../Grafana/) |
| Logs | What happened, as events | Loki |
| Traces | Where time went across services | Tempo / Jaeger |
| Profiles | Where CPU/memory cost went | Pyroscope |
| Alerts | When a human must act | Alertmanager, Grafana Alerting |
| Dashboards | How a human investigates | Grafana |

## Planned topics

- [ ] [OpenTelemetry](../OpenTelemetry/) — vendor-neutral instrumentation
- [ ] OTel Collector pipeline (receive → process → export)
- [ ] [Grafana Alloy](../Alloy/) — unified telemetry agent
- [ ] Golden signals; RED and USE methods
- [ ] Observability architecture for a multi-service app
- [ ] Cost of observability (cardinality, retention, sampling)

## See also

- [SRE](../SRE/) · Labs: [Labs/Observability](../../../Labs/Observability/)
