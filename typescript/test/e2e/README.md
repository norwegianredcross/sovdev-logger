# How to Verify TypeScript sovdev-logger Data Flow

This document describes how to verify that the sovdev-logger TypeScript library correctly sends data through the OTLP collector to backend systems (Loki, Prometheus, Tempo) and that the data is queryable from Grafana.

## Quick Start: Automated E2E Test

**Recommended**: Use the automated E2E test script for quick verification:

```bash
# From repository root
cd typescript
npm run test:e2e

# Or from this directory
cd ../..
npm run test:e2e
```

This will:
- Build the library
- Run the example application with proper OTLP configuration
- Wait for telemetry export (15 seconds)
- Verify data in all three backends (Loki, Prometheus, Tempo)
- Report ✅ pass or ❌ fail for each verification step

**Expected output**:
```
✅ ALL E2E TESTS PASSED!
Test service: sovdev-test-e2e-12345
```

After running the test, you can view the data in Grafana at `http://grafana.localhost` using the **Sovdev Logger - Prometheus Metrics (FAST)** dashboard.

---

## Manual Verification (Advanced)

The sections below describe the manual verification process. This is useful for:
- Debugging test failures
- Understanding the complete data flow
- Custom testing scenarios

## Prerequisites

1. **Running Infrastructure**:
   - Kubernetes cluster with Traefik ingress
   - OTLP collector exposed at `http://otel.localhost` (via Traefik)
   - Loki for logs
   - Prometheus for metrics
   - Tempo for traces
   - Grafana for visualization

2. **Built Library**:
   ```bash
   # From repository root
   cd typescript
   npm run build
   ```

3. **Traefik Ingress**:
   - OTLP collector is exposed via Traefik at `otel.localhost`
   - Use `127.0.0.1` for endpoints (Node.js doesn't resolve `.localhost` properly)
   - Add `Host: otel.localhost` header for Traefik routing
   - No port forwarding needed

## Verification Steps

### 1. Run Test Application with OTLP Configuration

Run the advanced example with full OTLP configuration:

```bash
# From repository root
cd typescript/examples/advanced

SYSTEM_ID=sovdev-test-manual-verification \
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://127.0.0.1/v1/logs \
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://127.0.0.1/v1/metrics \
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1/v1/traces \
OTEL_EXPORTER_OTLP_HEADERS='{"Host":"otel.localhost"}' \
timeout 15 npx tsx company-lookup.ts
```

**Important**: Use the `sovdev-test-*` prefix for test service names to ensure they appear in the test dashboard and don't mix with production data.

**Note**: Using `127.0.0.1` with `Host: otel.localhost` header because Node.js doesn't resolve `.localhost` domains properly. The Host header routes the request through Traefik to the OTLP collector.

**Expected Console Output**:
```
🚀 Sovdev Logger initialized successfully
📊 Service: sovdev-test-manual-verification
🔢 Version: 1.0.0
🔑 Session ID: abc123-def456-...
📡 OTLP Logs Endpoint: http://127.0.0.1/v1/logs
📡 OTLP Metrics Endpoint: http://127.0.0.1/v1/metrics
📡 OTLP Traces Endpoint: http://127.0.0.1/v1/traces
{"timestamp":"2025-10-05T...","level":"INFO","service.name":"sovdev-test-manual-verification",...}
...
```

**What to Look For**:
- ✅ Logger initialization message with session ID
- ✅ OTLP endpoint URLs printed
- ✅ Structured JSON log entries
- ✅ No timeout errors
- ✅ Clean exit after flush

### 2. Verify Data in OTLP Collector

Check OTLP collector logs to confirm data receipt:

```bash
kubectl logs -n monitoring -l app=otel-collector --tail=50
```

**Expected Output**:
```
2025-10-05T... INFO otlp_receiver Received logs request
2025-10-05T... INFO otlp_receiver Received metrics request
2025-10-05T... INFO otlp_receiver Received traces request
```

**What to Look For**:
- ✅ Log entries showing received requests
- ✅ No HTTP errors (4xx or 5xx)
- ✅ Timestamps matching test execution

### 3. Verify Logs in Loki (via Grafana)

Open Grafana at `http://grafana.localhost` and navigate to **Explore** → **Loki**.

#### Query 1: Find All Logs from Test Session

```logql
{service_name="sovdev-test-manual-verification"}
```

**Expected Results**:
- Multiple log entries from the test run
- Timestamps matching test execution
- Structured JSON fields visible

#### Query 2: Find Job Status Logs

```logql
{service_name="sovdev-test-manual-verification", logType="JobStatus"}
```

**Expected Results**:
- Job started: `CompanyLookupBatch Started`
- Job completed: `CompanyLookupBatch Completed`

#### Query 3: Find Logs by Peer Service

```logql
{service_name="sovdev-test-manual-verification", peer_service="SYS1234567"}
```

**Expected Results**:
- Logs showing company lookups to BRREG (peer service)
- Request and response logs with matching traceIds

#### Query 4: Find Error Logs

```logql
{service_name="sovdev-test-manual-verification", level="ERROR"}
```

**Expected Results**:
- At least one error log (invalid company number 974652846)
- Exception details visible in log fields

**What to Look For**:
- ✅ All required fields present: `service.name`, `service.version`, `peer.service`, `functionName`, `message`, `traceId`, `eventId`, `logType`
- ✅ No `spanId` field (custom spanId removed)
- ✅ Input and response JSON fields populated
- ✅ Timestamps in ISO 8601 format

### 4. Verify Metrics in Prometheus (via Grafana)

Navigate to **Explore** → **Prometheus**.

#### Query 1: Log Level Counts

```promql
sovdev_log_level_total{service_name="sovdev-test-manual-verification"}
```

**Expected Results**:
```
sovdev_log_level_total{level="INFO", service_name="sovdev-test-manual-verification"} = 12
sovdev_log_level_total{level="ERROR", service_name="sovdev-test-manual-verification"} = 1
```

#### Query 2: Logs by Function

```promql
sovdev_logs_by_function_total{service_name="sovdev-test-manual-verification"}
```

**Expected Results**:
```
sovdev_logs_by_function_total{function_name="main", service_name="sovdev-test-manual-verification"} = 3
sovdev_logs_by_function_total{function_name="batchLookup", service_name="sovdev-test-manual-verification"} = 6
sovdev_logs_by_function_total{function_name="lookupCompany", service_name="sovdev-test-manual-verification"} = 4
```

#### Query 3: Logs by Peer Service

```promql
sovdev_logs_by_peer_service_total{service_name="sovdev-test-manual-verification"}
```

**Expected Results**:
```
sovdev_logs_by_peer_service_total{peer_service="SYS1234567", service_name="sovdev-test-manual-verification"} = 8
sovdev_logs_by_peer_service_total{peer_service="INTERNAL", service_name="sovdev-test-manual-verification"} = 5
```

#### Query 4: Error Rate

```promql
rate(sovdev_log_level_total{level="ERROR", service_name="sovdev-test-manual-verification"}[5m])
```

**Expected Results**:
- Non-zero value showing error rate

**What to Look For**:
- ✅ Metrics with correct service name
- ✅ All log levels represented
- ✅ Function names match code
- ✅ Peer service IDs correctly mapped (BRREG → SYS1234567)

### 5. Verify Traces in Tempo

#### Via Direct API (in cluster):

```bash
# Get available tags
kubectl exec -n monitoring tempo-0 -- wget -q -O - 'http://localhost:3200/api/search/tags'

# Get service names
kubectl exec -n monitoring tempo-0 -- wget -q -O - 'http://localhost:3200/api/search/tag/service.name/values'

# Search for traces
kubectl exec -n monitoring tempo-0 -- wget -q -O - 'http://localhost:3200/api/search?tags=service.name%3Dsovdev-test-manual-verification&limit=10'

# Get specific trace (replace TRACE_ID)
kubectl exec -n monitoring tempo-0 -- wget -q -O - 'http://localhost:3200/api/traces/TRACE_ID'
```

**Expected Results**:
```json
{
  "traces": [
    {
      "traceID": "4f7e4caf9ffcc53cf787f84e3ea6ccad",
      "rootServiceName": "sovdev-test-manual-verification",
      "rootTraceName": "main [transaction]",
      "startTimeUnixNano": "1759689917505000000",
      "durationMs": 1
    },
    {
      "traceID": "3d3f98f8b50d1ce6cf87d68fb614d199",
      "rootServiceName": "sovdev-test-manual-verification",
      "rootTraceName": "lookupCompany [transaction]"
    }
  ],
  "metrics": {
    "inspectedTraces": 16
  }
}
```

#### Via Grafana (navigate to **Explore** → **Tempo**):

Search by service name:
```
service.name = sovdev-test-manual-verification
```

**Expected Results**:
- Multiple traces listed (16 total inspected)
- Trace names: "main [transaction]", "lookupCompany [transaction]", "batchLookup [job.progress]"
- Each trace showing spans for different functions

#### Correlate Traces with Logs:

1. Get a trace from Tempo search
2. Copy the `trace.id` attribute from span details
3. Navigate to **Loki** and query:
   ```logql
   {service_name="sovdev-test-manual-verification", traceId="<paste-trace-id>"}
   ```

**Expected Results**:
- All logs related to that specific trace
- Shows complete transaction flow (request → processing → response)

**What to Look For**:
- ✅ Traces contain spans for each log operation
- ✅ Span attributes include: service.name, service.version, peer.service, function.name, log.level, log.type, trace.id, event.id
- ✅ Resource attributes include: session.id, deployment.environment
- ✅ Traces correlate with logs via traceId
- ✅ Span names match function names and log types

### 6. Verify Complete Data Flow

Create a Grafana dashboard combining all three data sources:

#### Panel 1: Log Volume (Loki)
```logql
sum(rate({service_name="sovdev-test-manual-verification"}[1m]))
```

#### Panel 2: Error Rate (Prometheus)
```promql
rate(sovdev_log_level_total{level="ERROR", service_name="sovdev-test-manual-verification"}[5m])
```

#### Panel 3: Trace Count (Tempo)
```
service.name = sovdev-test-manual-verification
```

**Expected Results**:
- All three panels show data from the same time period
- Metrics align (e.g., error spike in Prometheus matches error logs in Loki)
- Traces correlate with log entries

## Troubleshooting

### Problem: No Data in Any Backend

**Symptoms**:
- No logs in Loki
- No metrics in Prometheus
- No traces in Tempo

**Checks**:
1. Verify OTLP collector is running:
   ```bash
   kubectl get pods -n monitoring -l app=otel-collector
   ```

2. Check OTLP collector configuration:
   ```bash
   kubectl get configmap -n monitoring otel-collector-config -o yaml
   ```

3. Verify endpoints are reachable:
   ```bash
   curl -v -H "Host: otel.localhost" http://127.0.0.1/v1/logs
   ```

4. Check library configuration:
   ```bash
   # Print environment variables
   echo $OTEL_EXPORTER_OTLP_LOGS_ENDPOINT
   echo $OTEL_EXPORTER_OTLP_HEADERS
   ```

### Problem: Data in OTLP Collector but Not in Backends

**Symptoms**:
- OTLP collector logs show received data
- But Loki/Prometheus/Tempo have no data

**Checks**:
1. Check OTLP collector exporters configuration:
   ```yaml
   exporters:
     loki:
       endpoint: http://loki:3100/loki/api/v1/push
     prometheus:
       endpoint: http://prometheus:9090/api/v1/write
     tempo:
       endpoint: http://tempo:4317
   ```

2. Verify backend services are running:
   ```bash
   kubectl get pods -n monitoring -l app=loki
   kubectl get pods -n monitoring -l app=prometheus
   kubectl get pods -n monitoring -l app=tempo
   ```

3. Check backend service logs:
   ```bash
   kubectl logs -n monitoring -l app=loki --tail=50
   kubectl logs -n monitoring -l app=prometheus --tail=50
   kubectl logs -n monitoring -l app=tempo --tail=50
   ```

### Problem: Timeout During Flush

**Symptoms**:
- Application hangs at `await sovdevFlush()`
- Timeout command kills process

**Checks**:
1. Verify OTLP endpoints are reachable:
   ```bash
   curl -v -H "Host: otel.localhost" \
     -H "Content-Type: application/json" \
     -d '{"resourceLogs":[]}' \
     http://127.0.0.1/v1/logs
   ```

2. Check network connectivity:
   ```bash
   # Test Traefik routing with Host header
   curl -v -H "Host: otel.localhost" http://127.0.0.1
   ```

3. Reduce flush timeout in code (temporary debugging):
   ```typescript
   // In logger.ts, add timeout to flush
   await Promise.race([
     loggerProvider.forceFlush(),
     new Promise((_, reject) =>
       setTimeout(() => reject(new Error('Flush timeout')), 5000)
     )
   ]);
   ```

### Problem: Data Missing Required Fields

**Symptoms**:
- Logs appear but missing `service.name`, `peer.service`, etc.
- Queries fail to find data

**Checks**:
1. Verify initialization was called:
   ```typescript
   sovdevInitialize('sovdev-test-manual-verification', '1.0.0', {
     BRREG: 'SYS1234567'
   });
   ```

2. Check console output for initialization message:
   ```
   🚀 Sovdev Logger initialized successfully
   ```

3. Verify system ID mapping:
   ```typescript
   // BRREG should map to SYS1234567
   sovdevLog(INFO, 'test', 'message', 'BRREG', null, input, output);
   ```

## Success Criteria

A successful verification shows:

1. ✅ **Console Output**: Clean execution with initialization message and session ID
2. ✅ **OTLP Collector**: Logs showing received requests for logs, metrics, and traces
3. ✅ **Loki**: All log entries queryable with complete fields
4. ✅ **Prometheus**: Metrics available for log levels, functions, and peer services
5. ✅ **Tempo**: Traces available with correct spans and attributes
6. ✅ **Correlation**: Logs and traces linked via traceId
7. ✅ **Zero Manual Work**: Single log call generates logs + metrics + traces automatically

## Example Complete Verification Run

```bash
# 1. Build library (from repository root)
cd typescript
npm run build

# 2. Run test with OTLP (using 127.0.0.1 with Host header for Traefik routing)
cd examples/advanced
SYSTEM_ID=sovdev-test-manual-verification \
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://127.0.0.1/v1/logs \
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://127.0.0.1/v1/metrics \
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1/v1/traces \
OTEL_EXPORTER_OTLP_HEADERS='{"Host":"otel.localhost"}' \
timeout 15 npx tsx company-lookup.ts

# 3. Check OTLP collector
kubectl logs -n monitoring -l app=otel-collector --tail=20

# 4. Open Grafana
open http://grafana.localhost

# 5. Query Loki
{service_name="sovdev-test-manual-verification"}

# 6. Query Prometheus
sovdev_log_level_total{service_name="sovdev-test-manual-verification"}

# 7. Search Tempo
service.name = sovdev-test-manual-verification

# 8. Verify correlation
# - Copy traceId from Tempo trace
# - Query Loki: {traceId="<paste-id>"}
# - Confirm logs match trace operations
```

## Notes

- **Automated Testing**: The E2E test script (`npm run test:e2e`) automates all the manual verification steps above
- **Test Service Naming**: Use `sovdev-test-*` prefix for test services to isolate them from production data in dashboards
- **Session ID**: Generated once per application execution in `sovdevInitialize()`
- **Trace ID**: Generated per transaction/workflow using `sovdevGenerateTraceId()`
- **Event ID**: Generated per log entry automatically
- **Span ID**: Managed by OpenTelemetry SDK (no custom spanId)
- **Peer Service**: Maps friendly names (BRREG) to CMDB IDs (SYS1234567)
- **Backend Agnostic**: Library exports OTLP protocol, backend systems are configured externally
- **Operations Rate**: Dashboard shows 0 ops/s after tests complete - this is expected for burst traffic (use instant queries or gauges for total counts)
