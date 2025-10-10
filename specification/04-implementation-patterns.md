# Implementation Patterns for Sovdev Logger

## Overview

This document defines **required implementation patterns** that all sovdev-logger implementations MUST follow. These patterns ensure consistency across programming languages and guarantee that all implementations produce identical log output.

---

## Code Style Convention

**All sovdev-logger implementations MUST use snake_case naming:**

### Naming Rules

1. **Variables**: `session_id`, `peer_service`, `function_name`, `input_json`
2. **Function parameters**: `function_name`, `input_json`, `response_json`, `exception_object`
3. **Class properties**: `service_name`, `service_version`, `system_ids_mapping`
4. **Method names**: `create_log_entry()`, `process_exception()`, `resolve_peer_service()`
5. **Interface/Type fields**: All fields use snake_case to match log output

### Rationale

- **Cross-language consistency**: Python, Go, Rust, PHP all use snake_case
- **Code-to-log alignment**: Variable names match log field names exactly
- **Copy-paste friendly**: No mental translation needed between code and logs
- **Future-proof**: Easy to add new languages without naming conflicts

### Examples

**TypeScript** (correct):
```typescript
function create_log_entry(
  function_name: string,
  input_json?: any,
  response_json?: any
): StructuredLogEntry {
  const event_id = uuidv4();
  const trace_id = get_trace_id();

  return {
    service_name: this.service_name,
    function_name,
    trace_id,
    event_id,
    input_json,
    response_json
  };
}
```

**Python** (correct):
```python
def create_log_entry(
    self,
    function_name: str,
    input_json: Optional[dict] = None,
    response_json: Optional[dict] = None
) -> dict:
    event_id = str(uuid.uuid4())
    trace_id = self.get_trace_id()

    return {
        "service_name": self.service_name,
        "function_name": function_name,
        "trace_id": trace_id,
        "event_id": event_id,
        "input_json": input_json,
        "response_json": response_json
    }
```

### Migration Note

Existing implementations using camelCase must be refactored to snake_case in version 2.0.0.

---

## Field Naming Convention

### Standard Fields

All log outputs (console, file, OTLP) MUST use snake_case field naming:

- `service_name` - Service identifier
- `service_version` - Service version
- `session_id` - Session grouping ID (UUID for entire execution)
- `peer_service` - Target system identifier
- `function_name` - Function/method name
- `log_type` - Log classification (transaction, session, error, etc.)
- `trace_id` - Transaction correlation ID (UUID)
- `event_id` - Unique log entry ID (UUID)
- `input_json` - Input parameters (JSON serialized)
- `response_json` - Output data (JSON serialized)
- `exception_type` - Exception type (always "Error")
- `exception_message` - Exception message
- `exception_stack` - Exception stack trace (max 350 chars)

### Consistency Across Outputs

The same field names MUST be used in:
1. **Code variables** - `const trace_id = uuidv4()`
2. **Console logs** - `Trace ID: ${trace_id}`
3. **File logs** - `{"trace_id": "..."}`
4. **OTLP export** - `{"trace_id": "..."}`
5. **Backend storage** - Loki stores as `trace_id`

**No transformations** are applied - field names remain unchanged throughout the entire logging pipeline.

---

## Session ID Generation

### Purpose

The `session_id` field groups all logs, metrics, and traces from a single execution/run of the application. This enables correlation of all telemetry data from one session.

### Generation Rules

1. **Generate once** at initialization (in `sovdevInitialize()`)
2. **Use UUID v4** format (lowercase, e.g., `"18df09dd-c321-43d8-aa24-19dd7c149a56"`)
3. **Store in instance** for reuse across all log calls
4. **Include in all logs** - Every log entry MUST have the same `session_id`

### Example Implementation

**TypeScript**:
```typescript
class SovdevLogger {
  private session_id: string;

  constructor(service_name: string, service_version: string) {
    this.session_id = uuidv4(); // Generate once at initialization
  }

  log(function_name: string, message: string, ...args: any[]) {
    // Include session_id in every log
    const log_entry = {
      session_id: this.session_id,  // Same for all logs in this execution
      function_name,
      message,
      // ...
    };
  }
}
```

**Python**:
```python
class SovdevLogger:
    def __init__(self, service_name: str, service_version: str):
        self.session_id = str(uuid.uuid4())  # Generate once at initialization

    def log(self, function_name: str, message: str, **kwargs):
        # Include session_id in every log
        log_entry = {
            "session_id": self.session_id,  # Same for all logs in this execution
            "function_name": function_name,
            "message": message,
            # ...
        }
```

### Verification

Query all logs from a session in Grafana/Loki:
```logql
{service_name="sovdev-test-app"} | json | session_id="18df09dd-c321-43d8-aa24-19dd7c149a56"
```

---

## Trace ID Correlation

### Purpose

The `trace_id` field correlates related operations within a business transaction. Multiple log entries can share the same `trace_id` to track a transaction across services and operations.

### Generation Rules

1. **Generate per transaction** - Create new `trace_id` for each business transaction
2. **Use UUID v4** format (lowercase)
3. **Reuse across operations** - Pass the same `trace_id` to all related log calls
4. **Auto-generate if missing** - If `trace_id` not provided, generate new UUID

### Example Implementation

**Single Transaction with Multiple Operations**:
```typescript
// Generate trace_id for the entire transaction
const trace_id = sovdevGenerateTraceId();

// Log start of transaction
sovdevLog(
  SOVDEV_LOGLEVELS.INFO,
  'startTransaction',
  'Starting order processing',
  PEER_SERVICES.INTERNAL,
  { order_id: 'ORD-123' },
  null,
  null,
  trace_id  // Same trace_id
);

// Log external API call
sovdevLog(
  SOVDEV_LOGLEVELS.INFO,
  'callPaymentAPI',
  'Processing payment',
  PEER_SERVICES.PAYMENT_GATEWAY,
  { amount: 99.99 },
  { status: 'approved' },
  null,
  trace_id  // Same trace_id
);

// Log completion
sovdevLog(
  SOVDEV_LOGLEVELS.INFO,
  'completeTransaction',
  'Order processing completed',
  PEER_SERVICES.INTERNAL,
  { order_id: 'ORD-123' },
  { status: 'success' },
  null,
  trace_id  // Same trace_id
);
```

### Verification

Query all logs from a transaction in Grafana/Loki:
```logql
{service_name="sovdev-test-app"} | json | trace_id="<uuid>"
```

---

## Peer Service Identification

### Purpose

The `peer_service` field identifies the target system/service being called or interacted with. This enables tracking which external systems are involved in operations.

### Best Practices

1. **Use createPeerServices()** helper to define peer services
2. **Use INTERNAL** for internal operations (auto-generated)
3. **Use system IDs** for external services (e.g., `SYS1234567`)
4. **Type-safe constants** - Define all peer services upfront

### Example Implementation

```typescript
// Define peer services at application startup
const PEER_SERVICES = createPeerServices({
  BRREG: 'SYS1234567',      // External: Norwegian company registry
  ALTINN: 'SYS7654321',     // External: Government portal
  PAYMENT_GATEWAY: 'SYS9999999'  // External: Payment provider
});

// Initialize logger
sovdevInitialize(
  'company-lookup-service',
  '2.1.0',
  PEER_SERVICES.mappings
);

// Use type-safe constants in logging
sovdevLog(
  SOVDEV_LOGLEVELS.INFO,
  'lookupCompany',
  'Looking up company',
  PEER_SERVICES.BRREG,  // Type-safe, validated peer service
  { org_number: '123456789' },
  { name: 'Acme Corp' }
);

sovdevLog(
  SOVDEV_LOGLEVELS.INFO,
  'processInternally',
  'Processing data',
  PEER_SERVICES.INTERNAL,  // Internal operation
  { data: 'value' },
  { result: 'success' }
);
```

---

## JSON Serialization

### Purpose

The `input_json` and `response_json` fields store request/response data as JSON strings for analysis and debugging.

### Serialization Rules

1. **Always serialize to string** - Convert objects to JSON strings
2. **Always include response_json** - Even if `null`, field must be present with value `"null"` (string)
3. **Compact format** - No pretty-printing, single-line JSON
4. **Handle circular references** - Detect and break circular object references
5. **Handle errors gracefully** - If serialization fails, use `"[Serialization Error]"`

### Example Implementation

**TypeScript**:
```typescript
function serialize_json(obj: any): string {
  if (obj === null || obj === undefined) {
    return "null";  // String "null", not JSON null
  }

  try {
    return JSON.stringify(obj);  // Compact serialization
  } catch (error) {
    return "[Serialization Error]";  // Graceful fallback
  }
}

// Usage
const input_json = serialize_json({ org_number: '123456789' });
const response_json = serialize_json(null);  // Returns "null" (string)

const log_entry = {
  input_json: input_json,      // Always string
  response_json: response_json  // Always present, even if "null"
};
```

**Python**:
```python
def serialize_json(obj: Any) -> str:
    if obj is None:
        return "null"  # String "null", not JSON null

    try:
        return json.dumps(obj, ensure_ascii=False)  # Compact serialization
    except Exception:
        return "[Serialization Error]"  # Graceful fallback

# Usage
input_json = serialize_json({"org_number": "123456789"})
response_json = serialize_json(None)  # Returns "null" (string)

log_entry = {
    "input_json": input_json,      # Always string
    "response_json": response_json  # Always present, even if "null"
}
```

---

## Exception Processing

### Purpose

Standardize exception handling to ensure consistent error logging with security and size constraints.

### Processing Rules

1. **Standardize type** - Always use `"Error"` (not language-specific like `"Exception"`, `"TypeError"`)
2. **Remove credentials** - Strip auth headers, passwords, API keys from stack traces
3. **Limit stack size** - Truncate stack traces to 350 characters maximum
4. **Extract details** - Separate type, message, and stack into individual fields

### Example Implementation

**TypeScript**:
```typescript
function process_exception(error: Error): ExceptionDetails {
  return {
    exception_type: "Error",  // Always "Error"
    exception_message: error.message,
    exception_stack: clean_stack_trace(error.stack || "")
  };
}

function clean_stack_trace(stack: string): string {
  // Remove credentials
  let cleaned = stack
    .replace(/Authorization[:\s]+[^\s,}]+/gi, 'Authorization: [REDACTED]')
    .replace(/password[:\s=]+[^\s,}]+/gi, 'password=[REDACTED]')
    .replace(/api[-_]?key[:\s=]+[^\s,}]+/gi, 'api_key=[REDACTED]')
    .replace(/Bearer\s+[A-Za-z0-9\-._~+/]+=*/gi, 'Bearer [REDACTED]');

  // Limit to 350 characters
  return cleaned.substring(0, 350);
}
```

---

## Output Format Consistency

### Purpose

Ensure all outputs use identical field names for consistency and ease of querying.

### Format Examples

**Console Output** (human-readable):
```
2025-10-08 12:34:56 [INFO] company-lookup-service
  Function: lookupCompany
  Message: Looking up company 123456789
  Trace ID: 50ba0e1d-c46d-4dee-98d3-a0d3913f74ee
  Session ID: 18df09dd-c321-43d8-aa24-19dd7c149a56
```

**File Output** (JSON, one per line):
```json
{"timestamp":"2025-10-08T12:34:56.123456+00:00","level":"info","service_name":"company-lookup-service","service_version":"1.0.0","session_id":"18df09dd-c321-43d8-aa24-19dd7c149a56","peer_service":"SYS1234567","function_name":"lookupCompany","log_type":"transaction","message":"Looking up company 123456789","trace_id":"50ba0e1d-c46d-4dee-98d3-a0d3913f74ee","event_id":"cf115688-513e-48fe-8049-538a515f608d","input_json":"{\"org_number\":\"123456789\"}","response_json":"{\"name\":\"Acme Corp\"}"}
```

**OTLP Output** (sent to collector):
```json
{
  "scope_name": "company-lookup-service",
  "scope_version": "1.0.0",
  "observed_timestamp": "1759823543622190848",
  "severity_number": 9,
  "severity_text": "INFO",
  "service_name": "company-lookup-service",
  "service_version": "1.0.0",
  "session_id": "18df09dd-c321-43d8-aa24-19dd7c149a56",
  "peer_service": "SYS1234567",
  "function_name": "lookupCompany",
  "log_type": "transaction",
  "trace_id": "50ba0e1d-c46d-4dee-98d3-a0d3913f74ee",
  "event_id": "cf115688-513e-48fe-8049-538a515f608d",
  "input_json": "{\"org_number\":\"123456789\"}",
  "response_json": "{\"name\":\"Acme Corp\"}",
  "telemetry_sdk_language": "typescript",
  "telemetry_sdk_version": "1.37.0"
}
```

### Key Requirements

1. **Identical field names** - Same names in all outputs
2. **Snake_case everywhere** - No dots, no camelCase
3. **No transformations** - OTLP collector passes through unchanged
4. **All fields present** - Even optional fields like `response_json` must be present with value `"null"`

---

## Best Practices

### FUNCTIONNAME Constant

Define function name as a constant at the top of each function to avoid typos:

```typescript
async function lookupCompany(org_number: string): Promise<Company> {
  const FUNCTIONNAME = 'lookupCompany';  // Define once

  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,  // Reuse constant
    'Starting company lookup',
    PEER_SERVICES.BRREG,
    { org_number },
    null
  );

  try {
    const company = await fetchCompany(org_number);

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      FUNCTIONNAME,  // Same constant
      'Company lookup successful',
      PEER_SERVICES.BRREG,
      { org_number },
      company
    );

    return company;
  } catch (error) {
    sovdevLog(
      SOVDEV_LOGLEVELS.ERROR,
      FUNCTIONNAME,  // Same constant
      'Company lookup failed',
      PEER_SERVICES.BRREG,
      { org_number },
      null,
      error as Error
    );
    throw error;
  }
}
```

### Variable Reuse

Reuse input/response variables in logging to avoid duplication:

```typescript
async function processOrder(order_data: OrderData): Promise<OrderResult> {
  const FUNCTIONNAME = 'processOrder';
  const input_data = { order_id: order_data.id, amount: order_data.amount };

  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    'Processing order',
    PEER_SERVICES.INTERNAL,
    input_data,  // Reuse variable
    null
  );

  const result = await executeOrder(order_data);

  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    'Order processed',
    PEER_SERVICES.INTERNAL,
    input_data,  // Reuse same variable
    result       // Response variable
  );

  return result;
}
```

---

**Document Status**: Updated for snake_case naming convention (v2.0.0)
**Last Updated**: 2025-10-08
**Specification Version**: 2.0.0
