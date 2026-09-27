# Observability runbook

## Scope

CrowdSmarter emits structured request logs, request IDs, health probes, and Prometheus-format HTTP metrics. The optional local observability profile centralises them in Loki and Prometheus, displays them in Grafana, and evaluates alerts through Alertmanager.

The local receiver deliberately sends no external notification. A production owner must configure and test a monitored email, paging, or webhook receiver before launch.

## Start the local stack

```bash
docker compose up -d --build
docker compose -f docker-compose.yml -f docker-compose.observability.yml \
  --profile observability up -d
```

Open these loopback-only services:

- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`
- Alertmanager: `http://localhost:9093`
- Alloy diagnostics: `http://localhost:12345`

The provisioned **CrowdSmarter overview** dashboard shows request rate, server errors, average latency, and recent structured application logs.

## Smoke test

```bash
curl --fail http://localhost:8000/health/live/
curl --fail http://localhost:8000/health/ready/
curl --fail http://localhost:8000/health/metrics/ | grep crowdsmarter_http
curl --fail http://localhost:9090/-/ready
curl --fail http://localhost:9093/-/ready
curl --fail http://localhost:3100/ready
curl --fail http://localhost:3000/api/health
```

Prometheus should show `crowdsmarter-backend` as `UP`. Alertmanager should list the three provisioned rules:

- backend metrics unavailable for one minute (critical);
- more than 5% HTTP 5xx responses for five minutes (warning);
- average HTTP latency above two seconds for ten minutes (warning).

## Privacy and access

Request logs contain a request ID, method, route template, status, duration, and authenticated user UUID. They do not record request bodies, query strings, passwords, tokens, file names, or malware signatures. Route templates prevent record identifiers becoming metric labels.

The production Nginx configuration blocks `/health/metrics/`. Prometheus must scrape the backend over a private Docker or service network. Do not publish Prometheus, Loki, Alloy, Alertmanager, or an anonymously accessible Grafana endpoint to the internet.

Loki retains local logs for seven days. The Grafana and monitoring ports are bound to `127.0.0.1` in the development profile.

## Local evidence

On 2026-08-30 the complete profile started successfully. Prometheus reported
`up{job="crowdsmarter-backend"}=1`; all three alert rules reported `health=ok`;
Grafana returned the provisioned `crowdsmarter-overview` dashboard; and Loki
returned fresh structured backend request logs with route, level, status,
duration, and request ID. A synthetic `CrowdSmarterLocalPipelineTest` alert
was routed to `local-dashboard`, confirmed through Alertmanager's API, and
immediately resolved without contacting an external recipient.

## Production receiver checklist

1. Put the receiver secret in deployment-specific secret storage, not in this repository.
2. Route critical alerts to an actively monitored on-call destination.
3. Send a controlled test alert and record receipt, acknowledgement, and resolution time.
4. Add disk, database, certificate-expiry, backup-failure, and host-resource alerts at the infrastructure layer.
5. Review alert noise after the first week and after significant traffic changes.

## Known scaling boundary

The built-in HTTP metric collector is intentionally dependency-free and process-local. It is fully testable for the single-process development server. A multi-worker or multi-replica production deployment must replace it with a multiprocess-aware metrics exporter or scrape every worker/replica before using rate and latency values for service-level reporting. Health alerts and centralised container logs do not have this limitation.
