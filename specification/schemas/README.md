# Sovdev Logger JSON Schemas

This directory contains **JSON Schema definitions** (Draft 7) that define the structure and validation rules for log entries and observability backend API responses.

## Purpose

These schemas ensure:
- **Field naming consistency**: All fields use snake_case (service_name, log_type, trace_id, etc.)
- **Type safety**: Correct data types for all fields (strings, numbers, objects)
- **Format validation**: UUIDs, timestamps, hex values follow correct formats
- **Required fields**: Critical fields are always present
- **Forbidden patterns**: Explicitly reject camelCase and dotted notation

**Key benefit:** Machine-readable contracts that validate sovdev-logger data across the entire observability stack.

---

## Prerequisites

These schemas are used by:

1. **Python validators** in `specification/tests/`
2. **Shell script tools** in `specification/tools/`
3. **Development tools** (JSON Schema validators, IDEs)

**Dependencies:**
- JSON Schema Draft 7 compatible validator (e.g., `jsonschema` Python library)

---

## Quick Reference

**Core Principle:** All schemas enforce snake_case field naming and reject camelCase/dotted notation throughout the observability stack.

Complete table of all JSON Schema files:

| Schema | Purpose | Validates | Enforces | Used By |
|--------|---------|-----------|----------|---------|
| [**log-entry-schema.json**](log-entry-schema.json) | File log entry format | NDJSON log files | snake_case fields<br/>exception_type/message/stacktrace<br/>UUID formats<br/>Stack trace 350 char limit | [`validate-log-format.py`](../tests/validate-log-format.py) |
| [**loki-response-schema.json**](loki-response-schema.json) | Loki API response format | Loki query_range responses | snake_case stream labels<br/>Rejects serviceName/logType/etc.<br/>Timestamp nanosecond format | [`validate-loki-response.py`](../tests/validate-loki-response.py) |
| [**prometheus-response-schema.json**](prometheus-response-schema.json) | Prometheus API response format | Prometheus query responses | snake_case metric labels<br/>service_name/log_type/log_level<br/>Metric value format | [`validate-prometheus-response.py`](../tests/validate-prometheus-response.py) |
| [**tempo-response-schema.json**](tempo-response-schema.json) | Tempo API response format | Tempo search responses | traceID hex format (16-32 chars)<br/>spanID hex format (16 chars)<br/>Timestamp nanosecond format | [`validate-tempo-response.py`](../tests/validate-tempo-response.py) |

---


## Integration with Tools

These schemas are the foundation of the validation pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                     JSON Schemas (This Directory)                │
│  log-entry-schema.json │ loki-response-schema.json │ ...        │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ↓ (loaded by)
┌─────────────────────────────────────────────────────────────────┐
│              Python Validators (specification/tests/)            │
│  validate-log-format.py │ validate-loki-response.py │ ...       │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ↓ (called by)
┌─────────────────────────────────────────────────────────────────┐
│         Shell Script Tools (specification/tools/)                │
│  run-full-validation.sh │ validate-log-format.sh │ ...          │
└─────────────────────────────────────────────────────────────────┘
```


## Related Documentation

- **Field definitions:** See `specification/02-field-definitions.md` for detailed field descriptions
- **API contract:** See `specification/01-api-contract.md` for logging API specification
- **Validators:** See `specification/tests/README.md` for Python validators that use these schemas
- **Tools:** See `specification/tools/README.md` for shell scripts that orchestrate validation

---

**Last Updated:** 2025-10-13
**Maintainer:** Claude Code / Terje Christensen
