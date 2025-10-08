# Sovdev Logger Field Definitions

## Overview

This document defines **every field** that must appear in log entries across all three output destinations (OTLP, console, file). Field names, types, and formats must be **identical** across all language implementations.

---

## Core Fields (All Log Types)

### Service Identification

| Field | Type | Source | Example | OTLP | Console | File | Notes |
|-------|------|--------|---------|------|---------|------|-------|
| **service.name** | string | SERVICE_NAME env var or init param | "sovdev-test-app" | ✅ | ✅ | ✅ | OpenTelemetry semantic convention |
| **service.version** | string | SERVICE_VERSION env var or init param (default "1.0.0") | "1.0.0" | ✅ | ✅ | ✅ | OpenTelemetry semantic convention |
| **scope_name** | string | service name (NOT module name) | "sovdev-test-app" | ✅ | ❌ | ❌ | OpenTelemetry instrumentation scope |
| **scope_version** | string | hardcoded "1.0.0" | "1.0.0" | ✅ | ❌ | ❌ | Library version |

**Critical**: `scope_name` MUST use service name, NOT module/class name (`__name__` in Python, etc.)

### Correlation IDs

| Field | Type | Source | Example | OTLP | Console | File | Notes |
|-------|------|--------|---------|------|---------|------|-------|
| **traceId** | string | UUID v4 (lowercase, 36 chars) | "c3d75d26-d783-48a2-96c3-1e62a37419c7" | ✅ | ✅ | ✅ | Business transaction correlation |
| **eventId** | string | UUID v4 (lowercase, 36 chars) | "dca7f112-1c94-478f-88f2-ec9805574190" | ✅ | ❌ | ✅ | Unique log entry identifier |
| **session_id** | string | UUID v4 generated at init | "18df09dd-c321-43d8-aa24-19dd7c149a56" | ✅ | ✅ | ✅ | Execution correlation |

### Timestamps

| Field | Type | Source | Example | OTLP | Console | File | Notes |
|-------|------|--------|---------|------|---------|------|-------|
| **timestamp** | string | ISO 8601 format | "2025-10-07T08:34:22.398784+00:00" | ✅ | ✅ | ✅ | When log entry was created |
| **observed_timestamp** | string | nanoseconds since Unix epoch | "1759826062404246784" | ✅ | ❌ | ❌ | When log was observed by OpenTelemetry |

**Format Requirements**:
- **ISO 8601**: `YYYY-MM-DDTHH:mm:ss.ffffff+00:00` (Python) or `YYYY-MM-DDTHH:mm:ss.SSSZ` (TypeScript)
- **Nanoseconds**: 19-digit integer string representing nanoseconds since 1970-01-01 00:00:00 UTC

### Log Metadata

| Field | Type | Source | Example | OTLP | Console | File | Notes |
|-------|------|--------|---------|------|---------|------|-------|
| **level** | string | lowercase log level | "info", "error" | ❌ | ✅ | ✅ | Human-readable level (file/console) |
| **severity_text** | string | uppercase log level | "INFO", "ERROR" | ✅ | ❌ | ❌ | OpenTelemetry severity text |
| **severity_number** | integer | OpenTelemetry severity | 9 (INFO), 17 (ERROR) | ✅ | ❌ | ❌ | OpenTelemetry severity number |

**Severity Number Mapping**:
- TRACE: 1
- DEBUG: 5
- INFO: 9
- WARN: 13
- ERROR: 17
- FATAL: 21

### Business Context

| Field | Type | Source | Example | OTLP | Console | File | Notes |
|-------|------|--------|---------|------|---------|------|-------|
| **functionName** | string | provided by developer | "lookupCompany" | ✅ | ✅ | ✅ | Function where logging occurs |
| **message** | string | provided by developer | "Looking up company 123456789" | ✅ | ✅ | ✅ | Human-readable log message |
| **logType** | string | "transaction", "job.status", "job.progress" | "transaction" | ✅ | ❌ | ✅ | Type of log entry |
| **peer.service** | string | peer service ID or INTERNAL | "SYS1234567" | ✅ | ❌ | ✅ | Target system identifier |

### Data Fields

| Field | Type | Source | Example | OTLP | Console | File | Notes |
|-------|------|--------|---------|------|---------|------|-------|
| **inputJSON** | string | JSON.stringify(input) or "null" | '{"organisasjonsnummer":"123456789"}' | ✅ | ❌ | ✅ | Request/input data (serialized) |
| **responseJSON** | string | JSON.stringify(response) or "null" | '{"name":"Company AS"}' | ✅ | ❌ | ✅ | Response/output data (serialized) |

**Critical**: Both fields MUST ALWAYS be present, even when no data exists (value "null" as string).

### OpenTelemetry Metadata

| Field | Type | Source | Example | OTLP | Console | File | Notes |
|-------|------|--------|---------|------|---------|------|-------|
| **telemetry_sdk_language** | string | OpenTelemetry SDK | "python", "nodejs" | ✅ | ❌ | ❌ | Language runtime identifier |
| **telemetry_sdk_version** | string | OpenTelemetry SDK | "1.37.0", "1.28.0" | ✅ | ❌ | ❌ | OpenTelemetry SDK version |

---

## Exception Fields (ERROR/FATAL logs only)

| Field | Type | Source | Example | OTLP | Console | File | Notes |
|-------|------|--------|---------|------|---------|------|-------|
| **exceptionType** | string | ALWAYS "Error" | "Error" | ✅ | ❌ | ❌ | Standardized across languages |
| **exceptionMessage** | string | exception message | "HTTP 404:" | ✅ | ✅ | ✅ | Exception message |
| **exceptionStack** | string | stack trace (max 350 chars) | "Traceback (most recent call last):\n  File..." | ✅ | ✅ | ✅ | Stack trace with security cleanup |
| **exception.type** | string | ALWAYS "Error" | "Error" | ❌ | ❌ | ✅ | File format uses nested structure |
| **exception.message** | string | exception message | "HTTP 404:" | ❌ | ❌ | ✅ | File format uses nested structure |
| **exception.stack** | string | stack trace (max 350 chars) | "Traceback..." | ❌ | ❌ | ✅ | File format uses nested structure |

**Critical Standardization**:
- **exceptionType**: MUST be "Error" for ALL languages (not "Exception", "Throwable", etc.)
- **Security**: Stack traces MUST have credentials removed (auth headers, passwords, tokens)
- **Limit**: Stack traces MUST be truncated to 350 characters maximum

---

## Job Status Fields (logType: "job.status")

Additional fields present in `inputJSON` for job status logs:

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| **jobName** | string | "CompanyLookupBatch" | Human-readable job name |
| **jobStatus** | string | "Started", "Completed", "Failed" | Job status |

**Message Format**: `"Job {jobStatus}: {jobName}"`

Example inputJSON:
```json
{
  "jobName": "CompanyLookupBatch",
  "jobStatus": "Started",
  "totalCompanies": 4
}
```

---

## Job Progress Fields (logType: "job.progress")

Additional fields present in `inputJSON` for job progress logs:

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| **itemId** | string | "971277882" | Identifier for current item |
| **currentItem** | integer | 25 | Current item number (1-based) |
| **totalItems** | integer | 100 | Total number of items |
| **progressPercentage** | integer | 25 | Math.round((current/total) * 100) |

**Message Format**: `"Processing {itemId} ({currentItem}/{totalItems})"`

Example inputJSON:
```json
{
  "itemId": "971277882",
  "currentItem": 25,
  "totalItems": 100,
  "progressPercentage": 25,
  "organisasjonsnummer": "971277882"
}
```

---

## Console Output Format

### Development Mode (Colored, Human-Readable)
```
2025-10-07 08:34:22 [ERROR] sovdev-test-company-lookup-python
  Function: lookupCompany
  Trace ID: 50ba0e1d-c46d-4dee-98d3-a0d3913f74ee
  Session ID: 18df09dd-c321-43d8-aa24-19dd7c149a56
  Error: HTTP 404:
  Stack: Traceback (most recent call last):
    File "/workspace/python/test/e2e/company-lookup/company-lookup.py", line 42
```

**Format Rules**:
- **Timestamp**: `YYYY-MM-DD HH:mm:ss`
- **Level**: Uppercase in brackets `[ERROR]`
- **Service**: On same line as timestamp and level
- **Indentation**: 2 spaces for details
- **Colors**: Use ANSI color codes (ERROR=red, WARN=yellow, INFO=green, etc.)

### Production Mode (JSON)
```json
{
  "timestamp": "2025-10-07T08:34:22.398784+00:00",
  "level": "error",
  "service": "sovdev-test-company-lookup-python",
  "functionName": "lookupCompany",
  "message": "Failed to lookup company 974652846",
  "traceId": "50ba0e1d-c46d-4dee-98d3-a0d3913f74ee",
  "sessionId": "18df09dd-c321-43d8-aa24-19dd7c149a56",
  "exception": {
    "type": "Error",
    "message": "HTTP 404:",
    "stack": "Traceback..."
  }
}
```

---

## File Output Format (JSON Lines)

Each log entry is a single line of JSON:

```json
{"timestamp":"2025-10-07T08:34:22.398784+00:00","level":"error","service":{"name":"sovdev-test-company-lookup-python","version":"1.0.0"},"function":{"name":"lookupCompany"},"exception":{"type":"Error","message":"HTTP 404:","stack":"Traceback..."},"traceId":"50ba0e1d-c46d-4dee-98d3-a0d3913f74ee","sessionId":"18df09dd-c321-43d8-aa24-19dd7c149a56","peer":{"service":"SYS1234567"},"input":{"organisasjonsnummer":"974652846"},"logType":"transaction"}
```

**Format Rules**:
- **JSON Lines**: One log entry per line (newline-delimited JSON)
- **Nested Objects**: Use nested structure for service, function, exception, peer, input
- **No Pretty Printing**: Compact JSON (no whitespace)

---

## OTLP Output Format

Logs are sent to OpenTelemetry Collector via OTLP protocol. Field structure in Loki:

```json
{
  "scope_name": "sovdev-test-company-lookup-python",
  "scope_version": "1.0.0",
  "observed_timestamp": "1759823543622190848",
  "severity_number": 17,
  "severity_text": "ERROR",
  "service_name": "sovdev-test-company-lookup-python",
  "service_version": "1.0.0",
  "functionName": "lookupCompany",
  "peer_service": "SYS1234567",
  "traceId": "50ba0e1d-c46d-4dee-98d3-a0d3913f74ee",
  "session_id": "18df09dd-c321-43d8-aa24-19dd7c149a56",
  "eventId": "cf115688-513e-48fe-8049-538a515f608d",
  "inputJSON": "{\"organisasjonsnummer\":\"974652846\"}",
  "responseJSON": "null",
  "exceptionType": "Error",
  "exceptionMessage": "HTTP 404:",
  "exceptionStack": "Traceback...",
  "logType": "transaction",
  "telemetry_sdk_language": "python",
  "telemetry_sdk_version": "1.37.0"
}
```

**Format Rules**:
- **Flat Structure**: All fields at root level (no nesting)
- **Underscores**: Use underscores for OpenTelemetry semantic conventions (service_name, peer_service, session_id)
- **Dots**: Use dots only for nested attributes in OpenTelemetry (service.name becomes service_name in Loki)

---

## Field Presence Matrix

Summary of which fields appear in which outputs:

| Field | OTLP | Console | File | Always Present |
|-------|------|---------|------|----------------|
| service.name | ✅ | ✅ | ✅ | ✅ |
| service.version | ✅ | ✅ | ✅ | ✅ |
| scope_name | ✅ | ❌ | ❌ | ✅ (OTLP only) |
| scope_version | ✅ | ❌ | ❌ | ✅ (OTLP only) |
| traceId | ✅ | ✅ | ✅ | ✅ |
| eventId | ✅ | ❌ | ✅ | ✅ |
| session_id | ✅ | ✅ | ✅ | ✅ |
| timestamp | ✅ | ✅ | ✅ | ✅ |
| observed_timestamp | ✅ | ❌ | ❌ | ✅ (OTLP only) |
| level | ❌ | ✅ | ✅ | ✅ |
| severity_text | ✅ | ❌ | ❌ | ✅ (OTLP only) |
| severity_number | ✅ | ❌ | ❌ | ✅ (OTLP only) |
| functionName | ✅ | ✅ | ✅ | ✅ |
| message | ✅ | ✅ | ✅ | ✅ |
| logType | ✅ | ❌ | ✅ | ✅ |
| peer.service | ✅ | ❌ | ✅ | ✅ |
| inputJSON | ✅ | ❌ | ✅ | ✅ (even when "null") |
| responseJSON | ✅ | ❌ | ✅ | ✅ (even when "null") |
| exceptionType | ✅ | ❌ | ❌ | ❌ (ERROR/FATAL only) |
| exceptionMessage | ✅ | ✅ | ✅ | ❌ (ERROR/FATAL only) |
| exceptionStack | ✅ | ✅ | ✅ | ❌ (ERROR/FATAL only) |

---

## Validation Rules

### Required Field Validation
All implementations MUST validate that these fields are present in every log entry:
- service.name, service.version
- traceId, eventId, session_id
- timestamp, observed_timestamp (OTLP)
- level (console/file) OR severity_text + severity_number (OTLP)
- functionName, message, logType
- peer.service
- inputJSON (even if "null")
- responseJSON (even if "null")

### Format Validation
- **UUID Fields**: Must match regex `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`
- **Timestamps**: Must be valid ISO 8601 or nanoseconds since epoch
- **Log Levels**: Must be one of: trace, debug, info, warn, error, fatal (lowercase)
- **Severity Text**: Must be uppercase version of log level
- **Severity Number**: Must map correctly to log level

---

**Document Status**: Complete field definitions based on TypeScript and Python implementations
**Last Updated**: 2025-10-07
**Specification Version**: 1.0.0
