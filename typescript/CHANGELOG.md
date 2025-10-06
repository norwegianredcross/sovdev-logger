# Changelog

All notable changes to @sovdev/logger will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Zero-Effort Observability

This release transforms @sovdev/logger from a logging library into a complete observability solution. **Every log entry now automatically generates logs, metrics, and traces** without any code changes.

#### Automatic Prometheus Metrics

- **NEW**: Automatic Prometheus metrics generation from log entries
  - `sovdev_operations_total` - Counter for total operations
  - `sovdev_errors_total` - Counter for errors (ERROR/FATAL levels)
  - `sovdev_operation_duration_milliseconds` - Histogram for operation duration
  - `sovdev_operations_active` - Gauge for active operations
- Metrics include full dimensional labels: `service_name`, `peer_service`, `log_level`, `log_type`
- Cumulative temporality for Prometheus compatibility
- Configured via `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` environment variable

#### Automatic Distributed Tracing

- **NEW**: Automatic trace span creation for every log entry
  - Span name format: `{functionName} [{logType}]`
  - Full span attributes: service.name, peer.service, log.level, log.type, function.name
  - Automatic span events for input/response data
  - Automatic error status based on exceptions and log levels
  - Trace duration tracking from log entry to span end
- Enables service dependency graphs in Tempo
- Full trace correlation with logs via traceId
- Configured via `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` environment variable

#### Session Grouping

- **NEW**: Unique `session.id` generated for each application execution
  - Automatically groups all logs, metrics, and traces from single run
  - Enables filtering by specific execution: `{service_name="my-service"} | session_id="abc123"`
  - Simplifies debugging and testing by isolating specific runs
  - Follows OTEL semantic conventions for execution grouping
  - Session ID printed at startup: `🔑 Session ID: abc123-def456-ghi789`

#### Grafana Dashboard Integration

- **NEW**: Pre-built Grafana dashboards included
  - Fast Metrics Dashboard (`037-grafana-sovdev-metrics.yaml`) - Prometheus-based with sub-second queries
  - Verification Dashboard (`036-grafana-sovdev-verification.yaml`) - TraceId correlation and debugging

### Changed

- Updated configuration examples for all three deployment scenarios
- Enhanced documentation with zero-effort observability examples

### Infrastructure Requirements

- **OTEL Collector**: Updated configuration to process `session.id` resource attribute
  - Add `session_id` to resource processor attributes
  - Add `session_id` to transform processor log statements
- **Tempo**: Enable metrics generator for service graphs
  - Configure `service-graphs` and `span-metrics` processors
  - Enable remote write to Prometheus
- **Grafana**: Deploy included dashboard ConfigMaps

### Configuration

All new features require additional environment variables:

```bash
# Existing LOGS endpoint
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://127.0.0.1/v1/logs

# New METRICS endpoint (for automatic Prometheus metrics)
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://127.0.0.1/v1/metrics

# New TRACES endpoint (for automatic trace spans)
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1/v1/traces
```

**No code changes required** - existing log calls automatically generate metrics and traces.

### Benefits

- **Zero Developer Effort**: Write logs once, get full observability (logs + metrics + traces)
- **Fast Queries**: Prometheus metrics enable sub-second dashboard responses
- **Service Graphs**: Automatic dependency visualization from trace relationships
- **Session Filtering**: Debug specific runs without time-based filtering
- **Full Correlation**: Link logs, metrics, and traces via traceId and session.id

## [1.0.0] - 2025-10-03

### Added

- Initial release of @sovdev/logger
- Structured JSON logging with camelCase field naming
- OpenTelemetry integration for logs
- Multiple transports: Console, File, OTLP
- Winston best practices implementation
- Security-aware credential removal
- Loggeloven av 2025 compliance
- Support for three deployment scenarios (Mac, Kubernetes, Azure/Cloud)
- Batch processing helpers (sovdevLogJobStatus, sovdevLogJobProgress)
- Automatic flush on exit via flushSovdevLogs()

[Unreleased]: https://github.com/terchris/sovdev-logger/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/terchris/sovdev-logger/releases/tag/v1.0.0
