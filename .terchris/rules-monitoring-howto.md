# Monitoring Stack Interaction Rules

**File**: `.terchris/rules-monitoring-howto.md`
**Purpose**: Define patterns for querying and interacting with monitoring backends (Loki, Prometheus, Tempo, OTLP)
**Target Audience**: Developers, DevOps engineers, LLMs debugging sovdev-logger
**Last Updated**: October 07, 2025

## 📋 Overview

This document establishes patterns for interacting with the monitoring stack backends (Loki, Prometheus, Tempo, OTLP Collector) using kubectl and curl from within the Kubernetes cluster. These patterns are based on Ansible playbooks from urbalurba-infrastructure and provide a consistent method for debugging, verification, and data extraction.

## 🏗️ Architecture

```
Application → OTLP Collector → Backend Storage → Grafana
                    ↓
            ├─→ Loki (Logs)
            ├─→ Prometheus (Metrics)
            └─→ Tempo (Traces)
```

**Service Endpoints (Internal Cluster)**:
- **Loki**: `loki-gateway.monitoring.svc.cluster.local:80`
- **Prometheus**: `prometheus-server.monitoring.svc.cluster.local:80`
- **Tempo**: `tempo.monitoring.svc.cluster.local:3200`
- **OTLP Collector**: `otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:4318` (HTTP)
- **Grafana**: `grafana.monitoring.svc.cluster.local:80`

## 🔍 Querying Loki (Logs)

### Basic Pattern
```bash
# Run ephemeral curl pod inside cluster
kubectl run curl-loki-query-[random] \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query={service_name="your-service"}' \
  --data-urlencode "start=${START_TIME}" \
  --data-urlencode "end=${END_TIME}" \
  --data-urlencode 'limit=10' \
  http://loki-gateway.monitoring.svc.cluster.local:80/loki/api/v1/query_range
```

### Query Python Error Logs
```bash
# Calculate time range (last 5 minutes)
END_TIME=$(date +%s)
START_TIME=$((END_TIME - 300))

# Query Python errors
kubectl run curl-loki-python-errors \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query={service_name="sovdev-test-company-lookup-python"} |= "Failed to lookup"' \
  --data-urlencode "start=${START_TIME}" \
  --data-urlencode "end=${END_TIME}" \
  --data-urlencode 'limit=1' \
  http://loki-gateway.monitoring.svc.cluster.local:80/loki/api/v1/query_range
```

### Query TypeScript Error Logs
```bash
END_TIME=$(date +%s)
START_TIME=$((END_TIME - 300))

kubectl run curl-loki-typescript-errors \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query={service_name="sovdev-test-company-lookup-typescript"} |= "Failed to lookup"' \
  --data-urlencode "start=${START_TIME}" \
  --data-urlencode "end=${END_TIME}" \
  --data-urlencode 'limit=1' \
  http://loki-gateway.monitoring.svc.cluster.local:80/loki/api/v1/query_range
```

### Query Specific ERROR Severity Logs
```bash
END_TIME=$(date +%s)
START_TIME=$((END_TIME - 300))

kubectl run curl-loki-errors-only \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query={service_name="sovdev-test-company-lookup-python", severity_text="ERROR"}' \
  --data-urlencode "start=${START_TIME}" \
  --data-urlencode "end=${END_TIME}" \
  --data-urlencode 'limit=5' \
  http://loki-gateway.monitoring.svc.cluster.local:80/loki/api/v1/query_range
```

### Save Raw Loki Data to File
```bash
# Query and save Python error logs
END_TIME=$(date +%s)
START_TIME=$((END_TIME - 300))

kubectl run curl-loki-python-raw \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query={service_name="sovdev-test-company-lookup-python", severity_text="ERROR"}' \
  --data-urlencode "start=${START_TIME}" \
  --data-urlencode "end=${END_TIME}" \
  --data-urlencode 'limit=1' \
  http://loki-gateway.monitoring.svc.cluster.local:80/loki/api/v1/query_range \
  > /Users/terje.christensen/learn/redcross-public/sovdev-logger/terchris/output/loki-python-raw.json

# Pretty print the JSON
cat /Users/terje.christensen/learn/redcross-public/sovdev-logger/terchris/output/loki-python-raw.json | jq . \
  > /Users/terje.christensen/learn/redcross-public/sovdev-logger/terchris/output/loki-python-pretty.json
```

### Loki API Endpoints
```bash
# Health check
kubectl run curl-loki-ready --image=curlimages/curl --rm -i --restart=Never \
  -n monitoring -- \
  curl -s http://loki-gateway.monitoring.svc.cluster.local:80/ready

# List available labels
kubectl run curl-loki-labels --image=curlimages/curl --rm -i --restart=Never \
  -n monitoring -- \
  curl -s http://loki-gateway.monitoring.svc.cluster.local:80/loki/api/v1/labels

# List label values for a specific label
kubectl run curl-loki-label-values --image=curlimages/curl --rm -i --restart=Never \
  -n monitoring -- \
  curl -s http://loki-gateway.monitoring.svc.cluster.local:80/loki/api/v1/label/service_name/values
```

### LogQL Query Syntax
```logql
# Basic label matching
{service_name="my-service"}

# Multiple labels
{service_name="my-service", severity_text="ERROR"}

# String matching (contains)
{service_name="my-service"} |= "error"

# String matching (does not contain)
{service_name="my-service"} != "debug"

# JSON field extraction
{service_name="my-service"} | json | exceptionStack != ""

# Regex matching
{service_name="my-service"} |~ "error|exception"
```

## 📊 Querying Prometheus (Metrics)

### Basic Pattern
```bash
kubectl run curl-prometheus-query \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query=your_metric_name' \
  http://prometheus-server.monitoring.svc.cluster.local:80/api/v1/query
```

### Query Specific Metrics
```bash
# Query "up" metrics for all services
kubectl run curl-prometheus-up \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query=up{namespace="monitoring"}' \
  http://prometheus-server.monitoring.svc.cluster.local:80/api/v1/query

# Query sovdev operations metrics
kubectl run curl-prometheus-sovdev \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query=sovdev_operations_total' \
  http://prometheus-server.monitoring.svc.cluster.local:80/api/v1/query
```

### Query Time Range
```bash
# Query metrics over last 5 minutes
END_TIME=$(date +%s)
START_TIME=$((END_TIME - 300))

kubectl run curl-prometheus-range \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query=sovdev_operations_total' \
  --data-urlencode "start=${START_TIME}" \
  --data-urlencode "end=${END_TIME}" \
  --data-urlencode 'step=15' \
  http://prometheus-server.monitoring.svc.cluster.local:80/api/v1/query_range
```

### Prometheus API Endpoints
```bash
# Health check
kubectl run curl-prometheus-health --image=curlimages/curl --rm -i --restart=Never \
  -n monitoring -- \
  curl -s http://prometheus-server.monitoring.svc.cluster.local:80/-/healthy

# List all metric names
kubectl run curl-prometheus-labels --image=curlimages/curl --rm -i --restart=Never \
  -n monitoring -- \
  curl -s http://prometheus-server.monitoring.svc.cluster.local:80/api/v1/label/__name__/values

# Get targets status
kubectl run curl-prometheus-targets --image=curlimages/curl --rm -i --restart=Never \
  -n monitoring -- \
  curl -s http://prometheus-server.monitoring.svc.cluster.local:80/api/v1/targets
```

## 🔍 Querying Tempo (Traces)

### Basic Pattern
```bash
kubectl run curl-tempo-search \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s 'http://tempo.monitoring.svc.cluster.local:3200/api/search?tags=service.name=your-service'
```

### Search for Traces by Service
```bash
# Search for telemetrygen traces
kubectl run curl-tempo-traces \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s 'http://tempo.monitoring.svc.cluster.local:3200/api/search?tags=service.name=telemetrygen-traces'
```

### Get Specific Trace by ID
```bash
# Get trace by trace ID
kubectl run curl-tempo-trace-detail \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s 'http://tempo.monitoring.svc.cluster.local:3200/api/traces/[TRACE_ID]'
```

### Tempo API Endpoints
```bash
# Health check
kubectl run curl-tempo-ready --image=curlimages/curl --rm -i --restart=Never \
  -n monitoring -- \
  curl -s http://tempo.monitoring.svc.cluster.local:3200/ready

# Get tempo metrics
kubectl run curl-tempo-metrics --image=curlimages/curl --rm -i --restart=Never \
  -n monitoring -- \
  curl -s http://tempo.monitoring.svc.cluster.local:3200/metrics
```

## 📡 OTLP Collector

### Check OTLP Collector Status
```bash
# Get OTLP collector logs
kubectl logs -n monitoring -l app.kubernetes.io/name=opentelemetry-collector --tail=50

# Follow logs in real-time
kubectl logs -n monitoring -l app.kubernetes.io/name=opentelemetry-collector --follow

# Check specific log types (metrics, traces, logs)
kubectl logs -n monitoring -l app.kubernetes.io/name=opentelemetry-collector --tail=100 | grep -i metric
kubectl logs -n monitoring -l app.kubernetes.io/name=opentelemetry-collector --tail=100 | grep -i trace
kubectl logs -n monitoring -l app.kubernetes.io/name=opentelemetry-collector --tail=100 | grep -i log
```

### OTLP Collector Health Check
```bash
# Health endpoint
kubectl run curl-otel-health --image=curlimages/curl --rm -i --restart=Never \
  -n monitoring -- \
  curl -s http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:13133/

# Metrics endpoint
kubectl run curl-otel-metrics --image=curlimages/curl --rm -i --restart=Never \
  -n monitoring -- \
  curl -s http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:8888/metrics
```

### Send Test Data to OTLP Collector
```bash
# Send test logs via telemetrygen
kubectl run telemetrygen-logs-test \
  --image=ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest \
  -n monitoring --restart=Never --rm -i -- \
  logs \
  --otlp-endpoint=otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:4318 \
  --otlp-insecure \
  --otlp-http \
  --duration=30s \
  --rate=5 \
  --logs=100 \
  --otlp-attributes=service.name="test-service" \
  --body="Test log message"
```

## 🎯 Grafana Integration

### Access Grafana API
```bash
# Get dashboard list (requires authentication)
kubectl run curl-grafana-dashboards --image=curlimages/curl --rm -i --restart=Never \
  -n monitoring -- \
  curl -s http://grafana.monitoring.svc.cluster.local:80/api/dashboards/home

# Health check
kubectl run curl-grafana-health --image=curlimages/curl --rm -i --restart=Never \
  -n monitoring -- \
  curl -s http://grafana.monitoring.svc.cluster.local:80/api/health
```

### Port Forward for Browser Access
```bash
# Port forward Grafana
kubectl port-forward -n monitoring svc/grafana 3000:80

# Port forward Prometheus
kubectl port-forward -n monitoring svc/prometheus-server 19090:80

# Port forward Loki
kubectl port-forward -n monitoring svc/loki-gateway 3100:80

# Port forward Tempo
kubectl port-forward -n monitoring svc/tempo 3200:3200
```

Then access via:
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:19090
- **Loki**: http://localhost:3100
- **Tempo**: http://localhost:3200

## 🔧 Debugging Tips

### Check Pod Status
```bash
# Check all monitoring pods
kubectl get pods -n monitoring

# Check specific service pods
kubectl get pods -n monitoring -l app.kubernetes.io/name=loki
kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus
kubectl get pods -n monitoring -l app.kubernetes.io/name=tempo
kubectl get pods -n monitoring -l app.kubernetes.io/name=opentelemetry-collector
```

### Check Service Endpoints
```bash
# List all services
kubectl get svc -n monitoring

# Get service details
kubectl describe svc loki-gateway -n monitoring
kubectl describe svc prometheus-server -n monitoring
kubectl describe svc tempo -n monitoring
```

### Test Connectivity from Application Pod
```bash
# Exec into your application pod
kubectl exec -it <your-pod-name> -- /bin/sh

# Test DNS resolution
nslookup loki-gateway.monitoring.svc.cluster.local

# Test HTTP connectivity
curl -v http://loki-gateway.monitoring.svc.cluster.local:80/ready
curl -v http://prometheus-server.monitoring.svc.cluster.local:80/-/healthy
```

## 📝 Common Patterns

### Full Pipeline Test (From OTLP to Query)
```bash
# 1. Send test logs via OTLP
kubectl run telemetrygen-test \
  --image=ghcr.io/open-telemetry/opentelemetry-collector-contrib/telemetrygen:latest \
  -n monitoring --restart=Never --rm -i -- \
  logs \
  --otlp-endpoint=otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:4318 \
  --otlp-insecure \
  --otlp-http \
  --duration=10s \
  --rate=1 \
  --logs=10 \
  --otlp-attributes=service.name="pipeline-test" \
  --body="Pipeline validation test"

# 2. Wait for processing
sleep 5

# 3. Query Loki for the test logs
END_TIME=$(date +%s)
START_TIME=$((END_TIME - 60))

kubectl run curl-loki-pipeline-test \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query={service_name="pipeline-test"}' \
  --data-urlencode "start=${START_TIME}" \
  --data-urlencode "end=${END_TIME}" \
  http://loki-gateway.monitoring.svc.cluster.local:80/loki/api/v1/query_range
```

### Save Multiple Backend Queries to Files
```bash
# Set time range
END_TIME=$(date +%s)
START_TIME=$((END_TIME - 300))

# Output directory
OUTPUT_DIR="/Users/terje.christensen/learn/redcross-public/sovdev-logger/terchris/output"

# Query Python logs
kubectl run curl-loki-python-backend \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query={service_name="sovdev-test-company-lookup-python", severity_text="ERROR"}' \
  --data-urlencode "start=${START_TIME}" \
  --data-urlencode "end=${END_TIME}" \
  --data-urlencode 'limit=1' \
  http://loki-gateway.monitoring.svc.cluster.local:80/loki/api/v1/query_range \
  > "${OUTPUT_DIR}/backend-python-raw.json"

# Query TypeScript logs
kubectl run curl-loki-typescript-backend \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query={service_name="sovdev-test-company-lookup-typescript", severity_text="ERROR"}' \
  --data-urlencode "start=${START_TIME}" \
  --data-urlencode "end=${END_TIME}" \
  --data-urlencode 'limit=1' \
  http://loki-gateway.monitoring.svc.cluster.local:80/loki/api/v1/query_range \
  > "${OUTPUT_DIR}/backend-typescript-raw.json"

# Query Prometheus metrics
kubectl run curl-prometheus-backend \
  --image=curlimages/curl \
  --rm -i --restart=Never \
  -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query=sovdev_operations_total' \
  http://prometheus-server.monitoring.svc.cluster.local:80/api/v1/query \
  > "${OUTPUT_DIR}/backend-prometheus-raw.json"
```

## 📚 References

Based on Ansible playbooks from urbalurba-infrastructure:
- **Loki Setup**: `ansible/playbooks/032-setup-loki.yml`
- **Prometheus Setup**: `ansible/playbooks/030-setup-prometheus.yml`
- **Tempo Setup**: `ansible/playbooks/232-setup-tempo.yml`
- **OTLP Collector**: `ansible/playbooks/031-setup-otel-collector.yml`
- **Testdata Generator**: `ansible/playbooks/035-setup-testdata.yml`

Official API Documentation:
- **Loki API**: https://grafana.com/docs/loki/latest/api/
- **Prometheus API**: https://prometheus.io/docs/prometheus/latest/querying/api/
- **Tempo API**: https://grafana.com/docs/tempo/latest/api_docs/
- **OTLP Specification**: https://opentelemetry.io/docs/specs/otlp/

## ⚠️ Important Notes

1. **Ephemeral Pods**: All curl commands use `--rm` which automatically deletes the pod after execution
2. **Random Names**: Use random suffixes (e.g., `-$(date +%s)`) when running multiple queries to avoid name conflicts
3. **Time Format**: Timestamps must be in seconds (Unix epoch format)
4. **Namespace**: All monitoring services are in the `monitoring` namespace
5. **URL Encoding**: Use `--data-urlencode` for query parameters with special characters
6. **Cluster Context**: Commands assume `rancher-desktop` context (default)
