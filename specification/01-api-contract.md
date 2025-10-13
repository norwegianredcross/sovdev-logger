# Sovdev Logger API Contract

## Overview

All sovdev-logger implementations MUST provide these 7 core functions with identical behavior across languages. Function names and parameter names are standardized, but parameter types should follow language conventions (e.g., `string | undefined` in TypeScript, `Optional<String>` in Java, `Option<String>` in Rust).

---

## 1. sovdev_initialize

**Purpose**: Initialize the logger with service information and peer service mappings.

**TypeScript Signature**:
```typescript
sovdev_initialize(
  service_name: string,
  service_version?: string,
  peer_services?: { [key: string]: string }
): void
```

**Python Signature**:
```python
def sovdev_initialize(
    service_name: str,
    service_version: str = "1.0.0",
    peer_services: Optional[Dict[str, str]] = None
) -> None:
    """
    Initialize the sovdev-logger.

    Args:
        service_name: Service identifier (from SYSTEM_ID env var)
        service_version: Service version (defaults to "1.0.0")
        peer_services: Peer service mapping from create_peer_services()

    Raises:
        ValueError: If service_name is empty
    """
```

**Parameters**:
- `service_name`: Service identifier (from SYSTEM_ID env var or hardcoded)
- `service_version`: Service version (optional, defaults to "1.0.0")
- `peer_services`: Peer service mapping from create_peer_services() (optional)

**Behavior**:
- MUST be called before any logging operations
- MUST initialize OpenTelemetry SDK with logs, metrics, and traces
- MUST set up all transports (console, file, error file, OTLP)
- MUST generate a unique session ID (UUID v4) for this execution
- MUST store peer service mappings for validation
- MUST be idempotent (safe to call multiple times)

**Example**:
```typescript
// Define peer services - INTERNAL is auto-generated
const PEER_SERVICES = create_peer_services({
  BRREG: 'SYS1234567',  // External system (Norwegian company registry)
  ALTINN: 'SYS7654321'   // External system (Government portal)
});

// Initialize at application startup
sovdev_initialize(
  'company-lookup-service',  // Service name
  '2.1.0',                    // Service version
  PEER_SERVICES.mappings      // Peer service mappings
);

// After initialization, PEER_SERVICES provides type-safe constants:
// - PEER_SERVICES.BRREG = 'SYS1234567'
// - PEER_SERVICES.ALTINN = 'SYS7654321'
// - PEER_SERVICES.INTERNAL = 'company-lookup-service' (auto-generated)
```

---

## 2. sovdev_log

**Purpose**: Log a transaction with optional input/output data and exception.

**TypeScript Signature**:
```typescript
// Type definition
type sovdev_log_level = 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal';

sovdev_log(
  level: sovdev_log_level,  // Accepts: SOVDEV_LOGLEVELS.INFO or 'info'
  function_name: string,
  message: string,
  peer_service: string,
  input_json?: any,
  response_json?: any,
  exception?: Error,
  trace_id?: string
): void
```

**Python Signature**:
```python
def sovdev_log(
    level: str,
    function_name: str,
    message: str,
    peer_service: str,
    input_json: Optional[Any] = None,
    response_json: Optional[Any] = None,
    exception: Optional[BaseException] = None,
    trace_id: Optional[str] = None
) -> None:
    """
    Log a transaction with optional input/output and exception.

    Args:
        level: Log level (use SOVDEV_LOGLEVELS enum or string)
        function_name: Name of the function being logged
        message: Human-readable message
        peer_service: Target system identifier
        input_json: Request data (any JSON-serializable type)
        response_json: Response data (any JSON-serializable type)
        exception: Exception object (if logging error)
        trace_id: UUID for transaction correlation (auto-generated if None)
    """
```

**Parameters**:
- `level`: Log level (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)
- `function_name`: Function/method name where logging occurs
- `message`: Human-readable log message
- `peer_service`: Target system/service identifier (from PEER_SERVICES)
- `input_json`: Request/input data (optional, will be JSON serialized)
- `response_json`: Response/output data (optional, will be JSON serialized)
- `exception`: Exception/error object (optional, will be processed for security)
- `trace_id`: Business transaction ID (optional, generates UUID if not provided)

**Behavior**:
- MUST create structured log entry with all fields
- MUST generate trace_id if not provided (UUID v4)
- MUST generate event_id (UUID v4)
- MUST serialize input_json and response_json to JSON strings
- MUST process exception for security (credential removal, stack limit 350 chars)
- MUST create OpenTelemetry span with attributes
- MUST increment metrics (operations.total, errors.total if ERROR/FATAL)
- MUST set log_type to "transaction"
- MUST always include response_json field (value "null" if not provided)

**Example - Basic Transaction Log**:
```typescript
async function lookupCompany(orgNumber: string): Promise<void> {
  const FUNCTIONNAME = 'lookupCompany';  // Best practice: Define function name as constant
  const input = { organisasjonsnummer: orgNumber };  // Best practice: Define input as variable

  // Simple INFO log with input and response
  sovdev_log(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,                     // Use constant (easier to maintain)
    `Looking up company ${orgNumber}`, // Human-readable message
    PEER_SERVICES.BRREG,               // External system
    input,                             // Reuse input variable
    null,                              // No response yet
    null,                              // No exception
    null                               // Auto-generate trace_id
  );

  // ... fetch company data ...
  const response = { navn: 'REMA 1000 AS' };  // Best practice: Define response as variable

  sovdev_log(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,                     // Same constant
    `Company found: ${response.navn}`,
    PEER_SERVICES.BRREG,
    input,                             // Reuse same input variable
    response,                          // Use response variable
    null,
    null
  );
}
```

**Example - Error Log with Exception**:
```typescript
async function lookupCompany(orgNumber: string, trace_id?: string): Promise<void> {
  const FUNCTIONNAME = 'lookupCompany';  // Best practice: Define function name as constant
  const txn_trace_id = trace_id || sovdev_generate_trace_id();  // Use provided or generate new
  const input = { organisasjonsnummer: orgNumber };  // Best practice: Define input as variable

  sovdev_log(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    `Looking up company ${orgNumber}`,
    PEER_SERVICES.BRREG,
    input,
    null,
    null,
    txn_trace_id  // Same trace_id for related logs
  );

  try {
    const companyData = await fetchCompanyData(orgNumber);
    const response = {  // Best practice: Define response as variable
      navn: companyData.navn,
      organisasjonsform: companyData.organisasjonsform?.beskrivelse
    };

    sovdev_log(
      SOVDEV_LOGLEVELS.INFO,
      FUNCTIONNAME,
      `Company found: ${companyData.navn}`,
      PEER_SERVICES.BRREG,
      input,      // Reuse same input variable
      response,   // Use response variable
      null,
      txn_trace_id  // SAME trace_id links request and response
    );
  } catch (error) {
    // ERROR log with exception handling
    sovdev_log(
      SOVDEV_LOGLEVELS.ERROR,
      FUNCTIONNAME,                       // Same constant
      `Failed to lookup company ${orgNumber}`,
      PEER_SERVICES.BRREG,
      input,                              // Reuse same input variable
      null,                               // No response data
      error,                              // Exception object (will be sanitized)
      txn_trace_id                          // SAME trace_id for error
    );
  }
}
```

**Example - Trace Correlation**:
```typescript
// This example shows how the same input variable and trace_id are reused
// across multiple log calls within a single function - see previous example
// for the complete pattern with FUNCTIONNAME constant, input variable, and
// response variable all following best practices.

// Key benefit: If you need to change the input structure or add fields,
// you only change it in ONE place (the variable definition) rather than
// in every sovdev_log() call.

// In Grafana: {trace_id="<uuid>"} shows all logs with the same trace_id together
```

---

## 3. sovdev_log_job_status

**Purpose**: Log batch job status (Started, Completed, Failed).

**TypeScript Signature**:
```typescript
sovdev_log_job_status(
  level: sovdev_log_level,  // Accepts: SOVDEV_LOGLEVELS.INFO or 'info'
  function_name: string,
  job_name: string,
  status: string,
  peer_service: string,
  input_json?: any,
  trace_id?: string
): void
```

**Python Signature**:
```python
def sovdev_log_job_status(
    level: str,
    function_name: str,
    job_name: str,
    status: str,
    peer_service: str,
    input_json: Optional[Any] = None,
    trace_id: Optional[str] = None
) -> None:
    """
    Log batch job status (Started, Completed, Failed).

    Args:
        level: Log level (typically INFO or ERROR)
        function_name: Function name managing the job
        job_name: Human-readable job name
        status: Job status ("Started", "Completed", "Failed", etc.)
        peer_service: Target system or INTERNAL for internal jobs
        input_json: Job metadata (total items, success count, etc.)
        trace_id: Job correlation ID (use same ID for all logs in this job)
    """
```

**Parameters**:
- `level`: Log level (typically INFO or ERROR)
- `function_name`: Function name managing the job
- `job_name`: Human-readable job name
- `status`: Job status ("Started", "Completed", "Failed", etc.)
- `peer_service`: Target system or INTERNAL for internal jobs
- `input_json`: Job metadata (total items, success count, etc.)
- `trace_id`: Job correlation ID (use same ID for all logs in this job)

**Behavior**:
- MUST create structured log entry with job metadata
- MUST set log_type to "job.status"
- MUST format message as "Job {status}: {job_name}"
- MUST include job status information in input_json
- MUST use provided trace_id for job correlation

**Example - Complete Batch Job Tracking**:
```typescript
async function batchLookup(orgNumbers: string[]): Promise<void> {
  const job_name = 'CompanyLookupBatch';  // Best practice: Define job name as constant
  const FUNCTIONNAME = 'batchLookup';    // Best practice: Define function name as constant
  const batch_trace_id = sovdev_generate_trace_id();  // Generate ONE trace_id for entire batch job
  const job_start_input = { totalCompanies: orgNumbers.length };  // Best practice: Define input as variable

  // 1. Log job start - internal job
  sovdev_log_job_status(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,                     // Use constant
    job_name,                          // Use constant
    'Started',                        // Status
    PEER_SERVICES.INTERNAL,           // Internal job (not external system)
    job_start_input,                    // Use variable
    batch_trace_id                      // All job logs share this trace_id
  );

  // 2. Process items (see sovdev_log_job_progress for progress tracking)
  let successful = 0;
  let failed = 0;
  for (let i = 0; i < orgNumbers.length; i++) {
    try {
      await lookupCompany(orgNumbers[i]);
      successful++;
    } catch (error) {
      failed++;
    }
  }

  // 3. Log job completion - internal job
  const job_completion_input = {  // Best practice: Define completion input as variable
    totalCompanies: orgNumbers.length,
    successful,
    failed
  };

  sovdev_log_job_status(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,                     // Same constant
    job_name,                          // Same constant
    'Completed',                      // Status changed
    PEER_SERVICES.INTERNAL,
    job_completion_input,               // Use variable
    batch_trace_id                      // SAME trace_id links start and completion
  );
}

// In Grafana: {trace_id="<batch-uuid>"} shows complete job lifecycle
// - Job Started log
// - All progress logs
// - Job Completed log
```

---

## 4. sovdev_log_job_progress

**Purpose**: Log progress for individual items in a batch job.

**TypeScript Signature**:
```typescript
sovdev_log_job_progress(
  level: sovdev_log_level,  // Accepts: SOVDEV_LOGLEVELS.INFO or 'info'
  function_name: string,
  item_id: string,
  current: number,
  total: number,
  peer_service: string,
  input_json?: any,
  trace_id?: string
): void
```

**Python Signature**:
```python
def sovdev_log_job_progress(
    level: str,
    function_name: str,
    item_id: str,
    current: int,
    total: int,
    peer_service: str,
    input_json: Optional[Any] = None,
    trace_id: Optional[str] = None
) -> None:
    """
    Log progress for individual items in a batch job.

    Args:
        level: Log level (typically INFO)
        function_name: Function name processing items
        item_id: Identifier for current item being processed
        current: Current item number (1-based)
        total: Total number of items
        peer_service: Target system for this item
        input_json: Item-specific data
        trace_id: Job correlation ID (same as job status logs)
    """
```

**Parameters**:
- `level`: Log level (typically INFO)
- `function_name`: Function name processing items
- `item_id`: Identifier for current item being processed
- `current`: Current item number (1-based)
- `total`: Total number of items
- `peer_service`: Target system for this item
- `input_json`: Item-specific data
- `trace_id`: Job correlation ID (same as job status logs)

**Behavior**:
- MUST create structured log entry with progress metadata
- MUST set log_type to "job.progress"
- MUST format message as "Processing {item_id} ({current}/{total})"
- MUST calculate progress_percentage: Math.round((current / total) * 100)
- MUST include progress fields in input_json (current_item, total_items, item_id, progress_percentage)

**Example - Batch Processing with Progress Tracking**:
```typescript
async function batchLookup(orgNumbers: string[]): Promise<void> {
  const job_name = 'CompanyLookupBatch';
  const FUNCTIONNAME = 'batchLookup';  // Best practice: Define function name as constant
  const batch_trace_id = sovdev_generate_trace_id();  // ONE trace_id for entire batch
  const job_start_input = { totalCompanies: orgNumbers.length };

  // Log job start (see sovdev_log_job_status example)
  sovdev_log_job_status(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    job_name,
    'Started',
    PEER_SERVICES.INTERNAL,
    job_start_input,
    batch_trace_id
  );

  // Process each item with progress tracking
  for (let i = 0; i < orgNumbers.length; i++) {
    const orgNumber = orgNumbers[i];
    const item_trace_id = sovdev_generate_trace_id();  // Unique trace_id for each item
    const progress_input = { organisasjonsnummer: orgNumber };  // Best practice: Define input as variable

    // Log progress - tracking BRREG processing
    sovdev_log_job_progress(
      SOVDEV_LOGLEVELS.INFO,
      FUNCTIONNAME,                // Use constant
      orgNumber,                    // Item identifier
      i + 1,                        // Current item (1-based)
      orgNumbers.length,            // Total items
      PEER_SERVICES.BRREG,          // External system for this item
      progress_input,                // Use variable
      batch_trace_id                  // Progress logs use batch trace_id
    );

    // Process the item (uses separate item_trace_id for request/response)
    await lookupCompany(orgNumber, item_trace_id);
  }

  // Log job completion (see sovdev_log_job_status example)
  const job_completion_input = {
    totalCompanies: orgNumbers.length,
    successful: orgNumbers.length,
    failed: 0
  };

  sovdev_log_job_status(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    job_name,
    'Completed',
    PEER_SERVICES.INTERNAL,
    job_completion_input,
    batch_trace_id
  );
}

// Result: Two levels of correlation
// 1. Batch level: {trace_id="<batch-uuid>"} shows all progress logs + job status
// 2. Item level: {trace_id="<item-uuid>"} shows request/response for specific item
```

---

## 5. sovdev_flush

**Purpose**: Flush all pending OTLP batches to ensure logs/metrics/traces are exported.

**TypeScript Signature**:
```typescript
sovdev_flush(): Promise<void>
```

**Python Signature**:
```python
def sovdev_flush() -> None:
    """
    Flush all pending logs, metrics, and traces.

    Blocks until all data is exported or 30-second timeout occurs.
    Safe to call from signal handlers and atexit hooks.

    Note: Python uses synchronous flush (blocks), unlike TypeScript async.
    """
```

**Behavior**:
- MUST flush all pending log records to OTLP endpoint
- MUST flush all pending metrics to OTLP endpoint
- MUST flush all pending spans to OTLP endpoint
- MUST be called before application exit (including error exits)
- MUST be awaited in async contexts
- SHOULD complete within reasonable timeout (30 seconds recommended)

**Critical**: Without flushing, the final batch of logs (including job completion status) will be lost when application exits. OpenTelemetry uses batching for performance.

**Example - Application Shutdown**:
```typescript
async function main() {
  // Initialize logger
  sovdev_initialize('company-lookup-service', '1.0.0', PEER_SERVICES.mappings);

  try {
    // Application logic
    await batchLookup(orgNumbers);
  } catch (error) {
    sovdev_log(SOVDEV_LOGLEVELS.FATAL, 'main', 'Application crashed', PEER_SERVICES.INTERNAL, null, null, error);
  } finally {
    // CRITICAL: Flush before exit to ensure final logs are exported
    await sovdev_flush();
  }
}

main();
```

**Example - Signal Handlers (Node.js)**:
```typescript
// Ensure flush on process termination
process.on('SIGINT', async () => {
  console.log('Received SIGINT, flushing logs...');
  await sovdev_flush();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('Received SIGTERM, flushing logs...');
  await sovdev_flush();
  process.exit(0);
});

// Flush before normal exit
process.on('beforeExit', async () => {
  await sovdev_flush();
});
```

---

## 6. sovdev_generate_trace_id

**Purpose**: Generate a UUID v4 for trace correlation.

**TypeScript Signature**:
```typescript
sovdev_generate_trace_id(): string
```

**Python Signature**:
```python
def sovdev_generate_trace_id() -> str:
    """
    Generate UUID v4 for trace correlation.

    Returns:
        Lowercase UUID string with hyphens (36 characters)

    Example:
        >>> sovdev_generate_trace_id()
        '50ba0e1d-c46d-4dee-98d3-a0d3913f74ee'
    """
```

**Behavior**:
- MUST return a UUID v4 string
- MUST be lowercase
- MUST be 36 characters (8-4-4-4-12 format with hyphens)
- MUST be unique (cryptographically random)

**Example - Linking Related Operations**:
```typescript
// Generate ONE trace_id for related operations
const company_trace_id = sovdev_generate_trace_id();
// Returns: "c3d75d26-d783-48a2-96c3-1e62a37419c7"

// All these operations share the same trace_id - linkable in Grafana
sovdev_log(
  SOVDEV_LOGLEVELS.INFO,
  'lookupCompany',
  'Looking up company',
  PEER_SERVICES.BRREG,
  { orgNumber: '971277882' },
  null,
  null,
  company_trace_id  // Shared trace_id
);

sovdev_log(
  SOVDEV_LOGLEVELS.INFO,
  'validateCompany',
  'Validating company data',
  PEER_SERVICES.INTERNAL,
  { orgNumber: '971277882' },
  { valid: true },
  null,
  company_trace_id  // SAME trace_id
);

sovdev_log(
  SOVDEV_LOGLEVELS.INFO,
  'saveCompany',
  'Saving to database',
  PEER_SERVICES.INTERNAL,
  { orgNumber: '971277882' },
  { success: true },
  null,
  company_trace_id  // SAME trace_id
);

// In Grafana: {trace_id="c3d75d26-d783-48a2-96c3-1e62a37419c7"} shows all 3 operations together
```

---

## 7. create_peer_services

**Purpose**: Create type-safe peer service mapping with INTERNAL auto-generation.

**TypeScript Signature**:
```typescript
create_peer_services<T extends Record<string, string>>(
  definitions: T
): {
  [K in keyof T]: string;
} & {
  INTERNAL: string;
  mappings: Record<string, string>;
}
```

**Python Signature**:
```python
class PeerServices:
    """Type-safe peer service constants."""
    mappings: Dict[str, str]
    INTERNAL: str
    # Dynamic attributes for each defined service

def create_peer_services(definitions: Dict[str, str]) -> PeerServices:
    """
    Create peer service mapping with INTERNAL auto-generation.

    Args:
        definitions: Dictionary mapping service names to system IDs

    Returns:
        PeerServices object with:
        - Attribute access (PEER_SERVICES.BRREG returns 'BRREG')
        - Mapping access (PEER_SERVICES.mappings returns full dict)
        - Auto-generated INTERNAL constant

    Example:
        >>> PEER_SERVICES = create_peer_services({
        ...     'BRREG': 'SYS1234567',
        ...     'ALTINN': 'SYS7654321'
        ... })
        >>> PEER_SERVICES.BRREG  # Returns 'BRREG' (constant name)
        'BRREG'
        >>> PEER_SERVICES.mappings  # Returns full mapping
        {'BRREG': 'SYS1234567', 'ALTINN': 'SYS7654321'}
    """
```

**Parameters**:
- `definitions`: Object mapping peer service names to CMDB system IDs

**Behavior**:
- MUST create constants for each defined peer service
- MUST auto-generate INTERNAL constant with value equal to service name
- MUST return mappings object for sovdev_initialize()
- MUST provide type-safe access to peer service IDs

**Example - Type-Safe Peer Service Mapping**:
```typescript
// Define peer services - INTERNAL is auto-generated
const PEER_SERVICES = create_peer_services({
  BRREG: 'SYS1234567',  // Norwegian company registry
  ALTINN: 'SYS7654321', // Government portal
  CRM: 'SYS9876543'     // Customer relationship management system
});

// After creation, PEER_SERVICES provides:
// - Type-safe constants (compile-time validation)
// - Auto-generated INTERNAL (equals service name)
// - Mappings object for sovdev_initialize()

// Type-safe usage - compiler prevents typos:
sovdev_log(
  SOVDEV_LOGLEVELS.INFO,
  'fetchCompany',
  'Fetching from BRREG',
  PEER_SERVICES.BRREG,  // ✅ Valid - IntelliSense autocomplete
  { orgNumber: '971277882' }
);

// Compiler error: Property 'BRRG' does not exist
// sovdev_log(..., PEER_SERVICES.BRRG, ...)  // ❌ Typo caught at compile time

// Internal operations use auto-generated INTERNAL:
sovdev_log_job_status(
  SOVDEV_LOGLEVELS.INFO,
  'processData',
  'DataProcessingJob',
  'Started',
  PEER_SERVICES.INTERNAL,  // Auto-generated, equals service name
  { totalItems: 100 }
);

// Initialize logger with mappings:
sovdev_initialize(
  'company-lookup-service',
  '1.0.0',
  PEER_SERVICES.mappings  // Includes all defined peers + INTERNAL
);

// PEER_SERVICES object structure:
// {
//   BRREG: 'BRREG',           // String constant (not the system ID)
//   ALTINN: 'ALTINN',         // String constant (not the system ID)
//   CRM: 'CRM',               // String constant (not the system ID)
//   INTERNAL: 'INTERNAL',     // String constant 'INTERNAL'
//   mappings: {
//     BRREG: 'SYS1234567',    // Original CMDB system ID
//     ALTINN: 'SYS7654321',   // Original CMDB system ID
//     CRM: 'SYS9876543'       // Original CMDB system ID
//   }
// }
//
// Note: The logger will resolve 'BRREG' to 'SYS1234567' internally using mappings.
//       For 'INTERNAL', the logger replaces it with the actual service name.
```

---

## Log Levels

All implementations MUST support these 6 log levels:

**TypeScript**:
```typescript
// Constants object
export const SOVDEV_LOGLEVELS = {
  TRACE: 'trace',   // Severity: 1  (OpenTelemetry)
  DEBUG: 'debug',   // Severity: 5  (OpenTelemetry)
  INFO: 'info',     // Severity: 9  (OpenTelemetry)
  WARN: 'warn',     // Severity: 13 (OpenTelemetry)
  ERROR: 'error',   // Severity: 17 (OpenTelemetry)
  FATAL: 'fatal'    // Severity: 21 (OpenTelemetry)
} as const;

// Type definition (string literal union)
export type sovdev_log_level = typeof SOVDEV_LOGLEVELS[keyof typeof SOVDEV_LOGLEVELS];
// Resolves to: 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal'

// Usage: Both constants and strings work
sovdev_log(SOVDEV_LOGLEVELS.INFO, ...)  // Recommended (type-safe with autocomplete)
sovdev_log('info', ...)                  // Also works (string literal)
```

**Python**:
```python
from enum import Enum

class SOVDEV_LOGLEVELS(str, Enum):
    """
    Log levels matching OpenTelemetry severity numbers.

    Subclasses str to allow use as string literals.
    """
    TRACE = "trace"   # Severity: 1  (OpenTelemetry)
    DEBUG = "debug"   # Severity: 5  (OpenTelemetry)
    INFO = "info"     # Severity: 9  (OpenTelemetry)
    WARN = "warn"     # Severity: 13 (OpenTelemetry)
    ERROR = "error"   # Severity: 17 (OpenTelemetry)
    FATAL = "fatal"   # Severity: 21 (OpenTelemetry)

# Usage: Both enum and string work
sovdev_log(SOVDEV_LOGLEVELS.INFO, ...)  # Type-safe
sovdev_log("info", ...)  # Also works (string literal)
```

**Mapping to OpenTelemetry Severity**:
- TRACE → 1 (TRACE)
- DEBUG → 5 (DEBUG)
- INFO → 9 (INFO)
- WARN → 13 (WARN)
- ERROR → 17 (ERROR)
- FATAL → 21 (FATAL)

---

## Language-Specific Adaptations

### Naming Conventions
- **TypeScript/JavaScript**: snake_case (sovdev_log, sovdev_flush)
- **Python**: snake_case (sovdev_log, sovdev_flush)
- **Go**: snake_case for exported functions (sovdev_log, sovdev_flush) or PascalCase wrappers
- **Java**: snake_case (sovdev_log, sovdev_flush) or camelCase wrappers
- **C#**: snake_case (sovdev_log, sovdev_flush) or PascalCase wrappers
- **PHP**: snake_case (sovdev_log, sovdev_flush) per PSR standards
- **Rust**: snake_case (sovdev_log, sovdev_flush)

### Optional Parameters
- **TypeScript**: `param?: Type`
- **Python**: `param: Optional[Type] = None`
- **Go**: Pointer types `*string` or variadic parameters
- **Java**: Method overloading or `Optional<Type>`
- **C#**: Nullable types `Type?` or default parameters
- **Rust**: `Option<Type>`

### Return Types
- **Async Operations**: Use language-native async/await patterns
- **sovdevFlush**: Return Promise/Future/Task depending on language

---

## Error Handling

All functions MUST:
- Handle OpenTelemetry failures gracefully (log to console, continue execution)
- Validate required parameters (throw/return error if missing)
- Never throw exceptions that break user code
- Log initialization errors to console if OTLP export fails

---

## Version Compatibility

This API contract is **version 1.0.0**.

**Breaking Changes** (require major version bump):
- Removing or renaming functions
- Changing required parameters
- Changing parameter order
- Changing function behavior that breaks existing code

**Non-Breaking Changes** (minor version bump):
- Adding new optional parameters
- Adding new functions
- Adding new log levels

---

**Document Status**: Initial version based on TypeScript implementation
**Last Updated**: 2025-10-07
**Specification Version**: 1.0.0
