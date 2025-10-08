# Development Environment Configuration

## Overview

This document describes the **complete development environment** required for developing and testing sovdev-logger implementations. The environment consists of two main components:

1. **DevContainer Toolbox** - Provides all programming language runtimes
2. **Local Kubernetes Cluster** - Runs the observability stack (Loki, Prometheus, Tempo, Grafana)

Both components are **required** for developing and testing any language implementation.

---

## Component 1: DevContainer Toolbox

### Purpose

The DevContainer provides a **standardized development environment** with all programming language runtimes pre-installed. This eliminates "works on my machine" problems and ensures consistent behavior across Mac, Windows, and Linux.

### Architecture

```
Host Machine (Mac/Windows/Linux)
├── Project Files (editable from host)
└── DevContainer (running in Docker)
    ├── All Language Runtimes (Node.js, Python, Go, Java, PHP, C#, Rust)
    ├── Development Tools (git, curl, wget, etc.)
    └── Workspace Mount: /workspace → Host Project Root
```

### Key Specifications

| Property | Value | Notes |
|----------|-------|-------|
| **Container Name** | `devcontainer-toolbox` | Fixed name, always use this |
| **Base Image** | Debian 12 (bookworm) | Stable, well-supported |
| **User** | `vscode` (UID 1000) | Non-root user |
| **Workspace Mount** | `/workspace` → Host project root | Bidirectional read-write; changes on host instantly visible in container and vice versa |
| **Network Mode** | Bridge with host gateway | Can access host services via `host.docker.internal` |

**Critical: Workspace Mount Details**

The `/workspace` directory inside the container is **bind-mounted** to the project root on the host machine. This means:

- **Host path**: `/Users/terje.christensen/learn/redcross-public/sovdev-logger` (example Mac path)
- **Container path**: `/workspace` (always this path regardless of host OS)
- **Bidirectional sync**: Changes made on either side are immediately visible on the other
- **Same filesystem**: Not a copy - literally the same files

**Why This Matters for LLMs:**

This mount configuration enables LLMs to:
1. ✅ **Read/Edit files on host** using native Read/Edit/Write tools (fast, direct access)
2. ✅ **Execute code in container** using `docker exec` commands (consistent runtimes)
3. ✅ **See changes immediately** - edits on host are instantly available in container
4. ✅ **No sync delays** - changes propagate in real-time (not copied, same inode)

**Example Workflow:**
```bash
# LLM edits file on host
Edit /Users/terje.christensen/learn/redcross-public/sovdev-logger/typescript/src/logger.ts

# File is immediately available in container at /workspace/typescript/src/logger.ts
# LLM runs code in container
docker exec devcontainer-toolbox bash -c "cd /workspace/typescript && npm test"

# Test runs with the just-edited file (no sync needed)
```

### Pre-installed Language Runtimes

| Language | Version | Command | Notes |
|----------|---------|---------|-------|
| **Node.js** | 22.20.0 | `node --version` | Includes npm |
| **Python** | 3.11.13 | `python --version` | Includes pip |
| **PowerShell** | 7.5.2 | `pwsh --version` | Cross-platform |
| **Go** | (via install script) | `go version` | Run `.devcontainer/additions/install-go.sh` |
| **Java** | (via install script) | `java -version` | Run `.devcontainer/additions/install-java.sh` |
| **PHP** | (via install script) | `php --version` | Run `.devcontainer/additions/install-php.sh` |
| **C#/.NET** | (via install script) | `dotnet --version` | Run `.devcontainer/additions/install-dotnet.sh` |
| **Rust** | (via install script) | `rustc --version` | Run `.devcontainer/additions/install-rust.sh` |

### Command Execution Pattern

**Template:**
```bash
docker exec devcontainer-toolbox bash -c "cd /workspace/[subdir] && [command]"
```

**Examples:**
```bash
# Run TypeScript tests
docker exec devcontainer-toolbox bash -c "cd /workspace/typescript && npm test"

# Run Python tests
docker exec devcontainer-toolbox bash -c "cd /workspace/python && python -m pytest"

# Install TypeScript dependencies
docker exec devcontainer-toolbox bash -c "cd /workspace/typescript && npm install"

# Install Python dependencies
docker exec devcontainer-toolbox bash -c "cd /workspace/python && pip install -e ."

# Check Node.js version
docker exec devcontainer-toolbox node --version

# Check Python version
docker exec devcontainer-toolbox python --version
```

### Important Restrictions

**❌ Never use `-it` flags:**
```bash
# WRONG - will fail with "input device is not a TTY"
docker exec -it devcontainer-toolbox bash

# CORRECT - works in non-interactive environments
docker exec devcontainer-toolbox bash -c "command"
```

**✅ File Operations:**
- **Read/Edit/Write files**: Use host filesystem paths (fast, direct access)
- **Execute code**: Use DevContainer (consistent runtimes)

**Why?** File changes on host are immediately visible in container (same filesystem mount).

### DevContainer Lifecycle

- **Starts**: When user opens project in VSCode with DevContainer extension
- **Stops**: When user closes VSCode (configured via `shutdownAction`)
- **Persists**: Container is recreated from `.devcontainer/devcontainer.json` config
- **Assumption**: Container is running during development sessions

### Network Access to Host

**From inside DevContainer to host services:**

Use `host.docker.internal` DNS name (cross-platform):
```bash
# Access Grafana on Kubernetes cluster (via Traefik ingress)
curl -H 'Host: grafana.localhost' http://host.docker.internal/

# Access OTLP collector (via Traefik ingress - requires Host header)
curl -H 'Host: otel.localhost' http://host.docker.internal/v1/logs
```

**From host machine (Mac/Windows/Linux) to Kubernetes services:**

Use `127.0.0.1` or `localhost` with appropriate port:
```bash
# Access Grafana on Kubernetes cluster (via Traefik ingress on port 80)
curl -H 'Host: grafana.localhost' http://127.0.0.1/

# Access OTLP collector (via Traefik ingress - requires Host header)
curl -H 'Host: otel.localhost' http://127.0.0.1/v1/logs
```

**Important**: Traefik uses the `Host` header to route requests to the correct backend service. **Always include the appropriate `Host` header** whether accessing from:
- DevContainer (use `host.docker.internal`)
- Host machine (use `127.0.0.1` or `localhost`)
- Direct IP (use `172.17.0.1` - Docker bridge gateway)

**All addresses reach the same Traefik ingress and require the `Host` header for routing.**

Without the `Host` header, Traefik cannot determine which service to route to and requests will fail.

**Environment Variable Pattern:**
```typescript
const KUBE_HOST = process.env.KUBE_HOST || 'host.docker.internal';
const OTEL_ENDPOINT = `http://${KUBE_HOST}/v1/logs`;
```

---

## Component 2: Local Kubernetes Cluster

### Purpose

The Kubernetes cluster runs the **observability stack** (Loki, Prometheus, Tempo, Grafana) that receives logs, metrics, and traces from sovdev-logger implementations during testing.

### Architecture

```
Local Kubernetes Cluster (Rancher Desktop)
├── Namespace: monitoring
│   ├── OTLP Collector (receives telemetry)
│   ├── Loki (stores logs)
│   ├── Prometheus (stores metrics)
│   ├── Tempo (stores traces)
│   └── Grafana (visualizes data)
└── Ingress: Traefik
    ├── grafana.localhost → Grafana UI (via Traefik IngressRoute)
    └── otel.localhost → OTLP Collector (via Traefik IngressRoute)

Note: Prometheus and Tempo are accessed via kubectl port-forward (no ingress)
```

### Cluster Specifications

| Property | Value | Notes |
|----------|-------|-------|
| **Kubernetes Distribution** | Rancher Desktop | Includes containerd + kubectl |
| **Context Name** | `rancher-desktop` | Default context |
| **Monitoring Namespace** | `monitoring` | All observability components |
| **Ingress Controller** | Traefik | Routes traffic to services |
| **DNS Pattern** | `*.localhost` | Automatic on Mac/Linux, requires hosts file on Windows |

### Required Services

#### OTLP Collector
**Purpose**: Receives telemetry from applications via OTLP protocol

| Property | Value |
|----------|-------|
| **Service Name** | `otel-collector-opentelemetry-collector.monitoring.svc.cluster.local` |
| **HTTP Port** | 4318 |
| **gRPC Port** | 4317 |
| **Ingress** | `http://otel.localhost/v1/logs` (with Host header) |
| **Health Check** | `http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:13133/` |

**Test Connectivity:**
```bash
# From host (via Traefik ingress)
curl -H 'Host: otel.localhost' http://127.0.0.1/v1/logs

# From inside cluster
kubectl run curl-test --image=curlimages/curl --rm -i --restart=Never -n monitoring -- \
  curl -s http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:13133/
```

#### Loki (Logs)
**Purpose**: Stores and queries logs

| Property | Value |
|----------|-------|
| **Service Name** | `loki-gateway.monitoring.svc.cluster.local` |
| **Port** | 80 |
| **API Endpoint** | `/loki/api/v1/query_range` |
| **Health Check** | `/ready` |

**Query Logs:**
```bash
END_TIME=$(date +%s)
START_TIME=$((END_TIME - 300))

kubectl run curl-loki-query --image=curlimages/curl --rm -i --restart=Never -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query={service_name="your-service"}' \
  --data-urlencode "start=${START_TIME}" \
  --data-urlencode "end=${END_TIME}" \
  --data-urlencode 'limit=10' \
  http://loki-gateway.monitoring.svc.cluster.local:80/loki/api/v1/query_range
```

#### Prometheus (Metrics)
**Purpose**: Stores and queries metrics

| Property | Value |
|----------|-------|
| **Service Name** | `prometheus-server.monitoring.svc.cluster.local` |
| **Port** | 80 |
| **API Endpoint** | `/api/v1/query` |
| **Health Check** | `/-/healthy` |

**Query Metrics:**
```bash
kubectl run curl-prometheus-query --image=curlimages/curl --rm -i --restart=Never -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query=sovdev_operations_total' \
  http://prometheus-server.monitoring.svc.cluster.local:80/api/v1/query
```

#### Tempo (Traces)
**Purpose**: Stores and queries distributed traces

| Property | Value |
|----------|-------|
| **Service Name** | `tempo.monitoring.svc.cluster.local` |
| **Port** | 3200 |
| **API Endpoint** | `/api/search` |
| **Health Check** | `/ready` |

**Query Traces:**
```bash
kubectl run curl-tempo-search --image=curlimages/curl --rm -i --restart=Never -n monitoring -- \
  curl -s 'http://tempo.monitoring.svc.cluster.local:3200/api/search?tags=service.name=your-service'
```

#### Grafana (Visualization)
**Purpose**: Visualize logs, metrics, and traces

| Property | Value |
|----------|-------|
| **Service Name** | `grafana.monitoring.svc.cluster.local` |
| **Port** | 80 |
| **Ingress** | `http://grafana.localhost` |
| **Default Credentials** | admin/admin |
| **Data Sources** | Loki (logs), Prometheus (metrics), Tempo (traces) |

**Access Grafana:**
```bash
# Via ingress (browser)
open http://grafana.localhost

# Via port-forward
kubectl port-forward -n monitoring svc/grafana 3000:80
open http://localhost:3000
```

**Verify Data Sources:**
```bash
# Check Grafana can reach Loki
kubectl run curl-grafana-loki --image=curlimages/curl --rm -i --restart=Never -n monitoring -- \
  curl -s http://grafana.monitoring.svc.cluster.local:80/api/datasources/proxy/1/loki/api/v1/label

# Check Grafana can reach Prometheus
kubectl run curl-grafana-prom --image=curlimages/curl --rm -i --restart=Never -n monitoring -- \
  curl -s http://grafana.monitoring.svc.cluster.local:80/api/datasources/proxy/2/api/v1/query?query=up

# Check Grafana can reach Tempo
kubectl run curl-grafana-tempo --image=curlimages/curl --rm -i --restart=Never -n monitoring -- \
  curl -s http://grafana.monitoring.svc.cluster.local:80/api/datasources/proxy/3/api/echo
```

**Query via Grafana API:**
```bash
# Query Loki via Grafana (requires auth)
curl -u admin:admin -G http://grafana.localhost/api/datasources/proxy/1/loki/api/v1/query_range \
  --data-urlencode 'query={service_name="sovdev-test-company-lookup-python"}' \
  --data-urlencode 'limit=10'

# Query Prometheus via Grafana
curl -u admin:admin -G http://grafana.localhost/api/datasources/proxy/2/api/v1/query \
  --data-urlencode 'query=sovdev_operations_total'

# Query Tempo via Grafana (search traces)
curl -u admin:admin http://grafana.localhost/api/datasources/proxy/3/api/search
```

---

## Environment Variables

### For Application Code (Inside DevContainer)

**Required for OTLP Export:**
```bash
# OTLP Endpoints (from container to host)
export OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://host.docker.internal/v1/logs
export OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://host.docker.internal/v1/metrics
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://host.docker.internal/v1/traces

# OTLP Headers (Traefik routing)
export OTEL_EXPORTER_OTLP_HEADERS='{"Host":"otel.localhost"}'
```

**Service Identification:**
```bash
# Service name (appears in Grafana)
export SYSTEM_ID="sovdev-test-company-lookup-typescript"

# Or use SERVICE_NAME
export SERVICE_NAME="my-service"
export SERVICE_VERSION="1.0.0"
```

**Logging Configuration:**
```bash
# Enable console logging
export LOG_TO_CONSOLE=true

# Enable file logging
export LOG_TO_FILE=true
export LOG_FILE_PATH=./logs/dev.log
export ERROR_LOG_PATH=./logs/error.log

# Environment mode
export NODE_ENV=development  # or production
```

**File Rotation Configuration:**

All implementations MUST implement log rotation to prevent disk space exhaustion:

| Log Type | Max Size | Max Files | Total Disk Usage |
|----------|----------|-----------|------------------|
| Main log | 50 MB | 5 files | ~250 MB max |
| Error log | 10 MB | 3 files | ~30 MB max |
| **Total** | - | - | **~280 MB max** |

**Implementation Requirements:**
- MUST rotate log files when size limit is reached
- MUST keep only the specified number of rotated files
- MUST delete oldest files when max files limit is reached
- SHOULD use platform-appropriate file rotation libraries

**Language-Specific Implementations:**

**TypeScript/JavaScript (Winston):**
```typescript
new winston.transports.File({
  filename: logFilePath,
  maxsize: 50 * 1024 * 1024, // 50MB
  maxFiles: 5,                // Keep 5 files
  tailable: true              // Use rotating file names
})
```

**Python (logging.handlers.RotatingFileHandler):**
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    filename='logs/dev.log',
    maxBytes=50 * 1024 * 1024,  # 50MB
    backupCount=5                 # Keep 5 backups
)
```

**Go (lumberjack):**
```go
import "gopkg.in/natefinch/lumberjack.v2"

&lumberjack.Logger{
    Filename:   "logs/dev.log",
    MaxSize:    50,    // MB
    MaxBackups: 5,     // files
    MaxAge:     0,     // days (0 = no age limit)
}
```

**Java (Log4j2 RollingFileAppender):**
```xml
<RollingFile name="file" fileName="logs/dev.log"
             filePattern="logs/dev-%i.log.gz">
  <Policies>
    <SizeBasedTriggeringPolicy size="50MB"/>
  </Policies>
  <DefaultRolloverStrategy max="5"/>
</RollingFile>
```

**C# (Serilog FileSizeLimitBytes):**
```csharp
Log.Logger = new LoggerConfiguration()
    .WriteTo.File(
        "logs/dev.log",
        fileSizeLimitBytes: 50 * 1024 * 1024,  // 50MB
        rollOnFileSizeLimit: true,
        retainedFileCountLimit: 5
    )
    .CreateLogger();
```

**PHP (Monolog RotatingFileHandler):**
```php
use Monolog\Handler\RotatingFileHandler;

$handler = new RotatingFileHandler(
    'logs/dev.log',
    5,                          // maxFiles
    Logger::INFO,
    true,                       // bubble
    null,                       // filePermission
    false                       // useLocking
);
$handler->setFilenameFormat('{filename}-{date}', 'Y-m-d');
```

**Rust (tracing-appender):**
```rust
use tracing_appender::rolling::{RollingFileAppender, Rotation};

let file_appender = RollingFileAppender::new(
    Rotation::NEVER,          // Rotation based on size, not time
    "logs",
    "dev.log"
);
// Note: Rust ecosystem may require custom size-based rotation
```

### Example .env File (TypeScript)

```bash
# Service Configuration
SYSTEM_ID=sovdev-test-company-lookup-typescript
SERVICE_VERSION=1.0.0

# OTLP Configuration (DevContainer → Host → Kubernetes)
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://host.docker.internal/v1/logs
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://host.docker.internal/v1/metrics
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://host.docker.internal/v1/traces
OTEL_EXPORTER_OTLP_HEADERS={"Host":"otel.localhost"}

# Logging Configuration
LOG_TO_CONSOLE=true
LOG_TO_FILE=true
LOG_FILE_PATH=./logs/dev.log
NODE_ENV=development
```

### Example .env File (Python)

```bash
# Service Configuration
SYSTEM_ID=sovdev-test-company-lookup-python
SERVICE_VERSION=1.0.0

# OTLP Configuration
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://host.docker.internal/v1/logs
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://host.docker.internal/v1/metrics
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://host.docker.internal/v1/traces
OTEL_EXPORTER_OTLP_HEADERS={"Host":"otel.localhost"}

# Logging Configuration
LOG_TO_CONSOLE=true
LOG_TO_FILE=true
LOG_FILE_PATH=./logs/dev.log
```

---

## Complete Development Workflow

### 1. Start Development Environment

**Start Kubernetes Cluster (Rancher Desktop):**
- Open Rancher Desktop application
- Ensure Kubernetes is enabled
- Wait for cluster to be ready
- Verify: `kubectl get nodes` shows node in Ready state

**Start DevContainer (VSCode):**
- Open project in VSCode
- VSCode detects `.devcontainer/devcontainer.json`
- Container builds/starts automatically
- Verify: VSCode shows "Dev Container: DevContainer Toolbox" in status bar

### 2. Verify Environment

**Check DevContainer:**
```bash
# Check container is running
docker ps --filter name=devcontainer-toolbox

# Check languages available
docker exec devcontainer-toolbox node --version
docker exec devcontainer-toolbox python --version
```

**Check Kubernetes Cluster:**
```bash
# Check all monitoring pods are running
kubectl get pods -n monitoring

# Expected output:
# NAME                                           READY   STATUS    RESTARTS
# otel-collector-opentelemetry-collector-...     1/1     Running   0
# loki-gateway-...                               1/1     Running   0
# prometheus-server-...                          1/1     Running   0
# tempo-...                                      1/1     Running   0
# grafana-...                                    1/1     Running   0
```

### 3. Run Tests

**Using Verification Tool (Recommended):**
```bash
# Run TypeScript E2E test
cd specification/tools
./run-company-lookup.sh typescript

# Run Python E2E test
./run-company-lookup.sh python
```

**Or directly (using Docker exec):**
```bash
# TypeScript
docker exec devcontainer-toolbox bash -c "cd /workspace/typescript/test/e2e/company-lookup && ./run-test.sh"

# Python
docker exec devcontainer-toolbox bash -c "cd /workspace/python/test/e2e/company-lookup && ./run-test.sh"
```

### 4. Verify Logs in Grafana

**Wait for logs to propagate (5-10 seconds), then:**
```bash
# Open Grafana
open http://grafana.localhost

# Or via port-forward
kubectl port-forward -n monitoring svc/grafana 3000:80 &
open http://localhost:3000
```

**Navigate to**: Dashboards → Browse → "Structured Logging Testing Dashboard"

**Filter by service**: `systemId =~ /^sovdev-test-.*/`

### 5. Query Backends Directly (Verification)

**Query Loki for recent logs:**
```bash
END_TIME=$(date +%s)
START_TIME=$((END_TIME - 300))

kubectl run curl-loki-verify --image=curlimages/curl --rm -i --restart=Never -n monitoring -- \
  curl -s -G \
  --data-urlencode 'query={service_name="sovdev-test-company-lookup-python"}' \
  --data-urlencode "start=${START_TIME}" \
  --data-urlencode "end=${END_TIME}" \
  --data-urlencode 'limit=5' \
  http://loki-gateway.monitoring.svc.cluster.local:80/loki/api/v1/query_range
```

---

## Troubleshooting

### DevContainer Issues

**Container not running:**
```bash
# Check Docker is running
docker ps

# Rebuild container
# In VSCode: Cmd/Ctrl+Shift+P → "Dev Containers: Rebuild Container"
```

**Cannot execute commands:**
```bash
# Check container name
docker ps --filter name=devcontainer-toolbox

# Test basic command
docker exec devcontainer-toolbox echo "hello"
```

**File changes not visible:**
- File changes on host should be immediately visible in container
- Check mount: `docker exec devcontainer-toolbox ls -la /workspace`

### Kubernetes Cluster Issues

**Pods not running:**
```bash
# Check pod status
kubectl get pods -n monitoring

# Check pod logs
kubectl logs -n monitoring <pod-name>

# Describe pod for events
kubectl describe pod -n monitoring <pod-name>
```

**Services not accessible:**
```bash
# Check services
kubectl get svc -n monitoring

# Check ingress
kubectl get ingressroute -A
```

**OTLP connection fails:**
```bash
# Test OTLP collector from inside cluster
kubectl run curl-otel-test --image=curlimages/curl --rm -i --restart=Never -n monitoring -- \
  curl -v http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:13133/

# Check collector logs
kubectl logs -n monitoring -l app.kubernetes.io/name=opentelemetry-collector --tail=50
```

**Grafana not accessible:**
```bash
# Check Grafana pod
kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana

# Port-forward as alternative
kubectl port-forward -n monitoring svc/grafana 3000:80
open http://localhost:3000
```

### Network Issues

**DevContainer cannot reach host:**
```bash
# Test from inside container
docker exec devcontainer-toolbox curl -v http://host.docker.internal/

# Should return response from Traefik
```

**Logs not appearing in Loki:**
1. Check OTLP collector is receiving data: `kubectl logs -n monitoring -l app.kubernetes.io/name=opentelemetry-collector`
2. Verify OTLP endpoint in application: `echo $OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`
3. Check OTLP headers: `echo $OTEL_EXPORTER_OTLP_HEADERS`
4. Verify application calls `sovdevFlush()` before exit

---

## Summary

### Complete Environment Components

1. **DevContainer** - All language runtimes (Node.js, Python, Go, Java, PHP, C#, Rust)
2. **Kubernetes Cluster** - Observability stack (Loki, Prometheus, Tempo, Grafana)
3. **Traefik Ingress** - Routes traffic to services via `*.localhost` domains
4. **OTLP Collector** - Receives telemetry from applications

### Key Connections

```
Application (DevContainer)
    → OTLP over HTTP (host.docker.internal)
        → Traefik Ingress (127.0.0.1:80)
            → OTLP Collector (Kubernetes)
                → Loki (logs) + Prometheus (metrics) + Tempo (traces)
                    → Grafana (visualization)
```

### Development Loop

1. **Edit code** on host (fast file operations)
2. **Run code** in DevContainer (consistent runtimes)
3. **Logs flow** to Kubernetes cluster (OTLP)
4. **Verify** in Grafana or via backend queries

This environment ensures **consistent behavior** across all developers and **reliable testing** of all language implementations.

---

**Document Status**: Initial version
**Last Updated**: 2025-10-07
**Next Review**: After first Go/Java/PHP implementation
