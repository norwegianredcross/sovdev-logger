# Sovdev Logger API Contract

## Overview

All sovdev-logger implementations MUST provide these 7 core functions with identical behavior across languages. Function names and parameter names are standardized, but parameter types should follow language conventions (e.g., `string | undefined` in TypeScript, `Optional<String>` in Java, `Option<String>` in Rust).

---

## 1. sovdevInitialize

**Purpose**: Initialize the logger with service information and peer service mappings.

**Signature** (TypeScript reference):
```typescript
sovdevInitialize(
  serviceName: string,
  serviceVersion?: string,
  peerServices?: { [key: string]: string }
): void
```

**Parameters**:
- `serviceName`: Service identifier (from SYSTEM_ID env var or hardcoded)
- `serviceVersion`: Service version (optional, defaults to "1.0.0")
- `peerServices`: Peer service mapping from createPeerServices() (optional)

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
const PEER_SERVICES = createPeerServices({
  BRREG: 'SYS1234567',  // External system (Norwegian company registry)
  ALTINN: 'SYS7654321'   // External system (Government portal)
});

// Initialize at application startup
sovdevInitialize(
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

## 2. sovdevLog

**Purpose**: Log a transaction with optional input/output data and exception.

**Signature** (TypeScript reference):
```typescript
sovdevLog(
  level: SOVDEV_LOGLEVELS,
  functionName: string,
  message: string,
  peerService: string,
  inputJSON?: object | null,
  responseJSON?: object | null,
  exception?: Error | null,
  traceId?: string | null
): void
```

**Parameters**:
- `level`: Log level (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)
- `functionName`: Function/method name where logging occurs
- `message`: Human-readable log message
- `peerService`: Target system/service identifier (from PEER_SERVICES)
- `inputJSON`: Request/input data (optional, will be JSON serialized)
- `responseJSON`: Response/output data (optional, will be JSON serialized)
- `exception`: Exception/error object (optional, will be processed for security)
- `traceId`: Business transaction ID (optional, generates UUID if not provided)

**Behavior**:
- MUST create structured log entry with all fields
- MUST generate traceId if not provided (UUID v4)
- MUST generate eventId (UUID v4)
- MUST serialize inputJSON and responseJSON to JSON strings
- MUST process exception for security (credential removal, stack limit 350 chars)
- MUST create OpenTelemetry span with attributes
- MUST increment metrics (operations.total, errors.total if ERROR/FATAL)
- MUST set logType to "transaction"
- MUST always include responseJSON field (value "null" if not provided)

**Example - Basic Transaction Log**:
```typescript
async function lookupCompany(orgNumber: string): Promise<void> {
  const FUNCTIONNAME = 'lookupCompany';  // Best practice: Define function name as constant
  const input = { organisasjonsnummer: orgNumber };  // Best practice: Define input as variable

  // Simple INFO log with input and response
  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,                     // Use constant (easier to maintain)
    `Looking up company ${orgNumber}`, // Human-readable message
    PEER_SERVICES.BRREG,               // External system
    input,                             // Reuse input variable
    null,                              // No response yet
    null,                              // No exception
    null                               // Auto-generate traceId
  );

  // ... fetch company data ...
  const response = { navn: 'REMA 1000 AS' };  // Best practice: Define response as variable

  sovdevLog(
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
async function lookupCompany(orgNumber: string, traceId?: string): Promise<void> {
  const FUNCTIONNAME = 'lookupCompany';  // Best practice: Define function name as constant
  const txnTraceId = traceId || sovdevGenerateTraceId();  // Use provided or generate new
  const input = { organisasjonsnummer: orgNumber };  // Best practice: Define input as variable

  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    `Looking up company ${orgNumber}`,
    PEER_SERVICES.BRREG,
    input,
    null,
    null,
    txnTraceId  // Same traceId for related logs
  );

  try {
    const companyData = await fetchCompanyData(orgNumber);
    const response = {  // Best practice: Define response as variable
      navn: companyData.navn,
      organisasjonsform: companyData.organisasjonsform?.beskrivelse
    };

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      FUNCTIONNAME,
      `Company found: ${companyData.navn}`,
      PEER_SERVICES.BRREG,
      input,      // Reuse same input variable
      response,   // Use response variable
      null,
      txnTraceId  // SAME traceId links request and response
    );
  } catch (error) {
    // ERROR log with exception handling
    sovdevLog(
      SOVDEV_LOGLEVELS.ERROR,
      FUNCTIONNAME,                       // Same constant
      `Failed to lookup company ${orgNumber}`,
      PEER_SERVICES.BRREG,
      input,                              // Reuse same input variable
      null,                               // No response data
      error,                              // Exception object (will be sanitized)
      txnTraceId                          // SAME traceId for error
    );
  }
}
```

**Example - Trace Correlation**:
```typescript
// This example shows how the same input variable and traceId are reused
// across multiple log calls within a single function - see previous example
// for the complete pattern with FUNCTIONNAME constant, input variable, and
// response variable all following best practices.

// Key benefit: If you need to change the input structure or add fields,
// you only change it in ONE place (the variable definition) rather than
// in every sovdevLog() call.

// In Grafana: {traceId="<uuid>"} shows all logs with the same traceId together
```

---

## 3. sovdevLogJobStatus

**Purpose**: Log batch job status (Started, Completed, Failed).

**Signature** (TypeScript reference):
```typescript
sovdevLogJobStatus(
  level: SOVDEV_LOGLEVELS,
  functionName: string,
  jobName: string,
  status: string,
  peerService: string,
  inputJSON?: object | null,
  traceId?: string | null
): void
```

**Parameters**:
- `level`: Log level (typically INFO or ERROR)
- `functionName`: Function name managing the job
- `jobName`: Human-readable job name
- `status`: Job status ("Started", "Completed", "Failed", etc.)
- `peerService`: Target system or INTERNAL for internal jobs
- `inputJSON`: Job metadata (total items, success count, etc.)
- `traceId`: Job correlation ID (use same ID for all logs in this job)

**Behavior**:
- MUST create structured log entry with job metadata
- MUST set logType to "job.status"
- MUST format message as "Job {status}: {jobName}"
- MUST include job status information in inputJSON
- MUST use provided traceId for job correlation

**Example - Complete Batch Job Tracking**:
```typescript
async function batchLookup(orgNumbers: string[]): Promise<void> {
  const jobName = 'CompanyLookupBatch';  // Best practice: Define job name as constant
  const FUNCTIONNAME = 'batchLookup';    // Best practice: Define function name as constant
  const batchTraceId = sovdevGenerateTraceId();  // Generate ONE traceId for entire batch job
  const jobStartInput = { totalCompanies: orgNumbers.length };  // Best practice: Define input as variable

  // 1. Log job start - internal job
  sovdevLogJobStatus(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,                     // Use constant
    jobName,                          // Use constant
    'Started',                        // Status
    PEER_SERVICES.INTERNAL,           // Internal job (not external system)
    jobStartInput,                    // Use variable
    batchTraceId                      // All job logs share this traceId
  );

  // 2. Process items (see sovdevLogJobProgress for progress tracking)
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
  const jobCompletionInput = {  // Best practice: Define completion input as variable
    totalCompanies: orgNumbers.length,
    successful,
    failed
  };

  sovdevLogJobStatus(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,                     // Same constant
    jobName,                          // Same constant
    'Completed',                      // Status changed
    PEER_SERVICES.INTERNAL,
    jobCompletionInput,               // Use variable
    batchTraceId                      // SAME traceId links start and completion
  );
}

// In Grafana: {traceId="<batch-uuid>"} shows complete job lifecycle
// - Job Started log
// - All progress logs
// - Job Completed log
```

---

## 4. sovdevLogJobProgress

**Purpose**: Log progress for individual items in a batch job.

**Signature** (TypeScript reference):
```typescript
sovdevLogJobProgress(
  level: SOVDEV_LOGLEVELS,
  functionName: string,
  itemId: string,
  current: number,
  total: number,
  peerService: string,
  inputJSON?: object | null,
  traceId?: string | null
): void
```

**Parameters**:
- `level`: Log level (typically INFO)
- `functionName`: Function name processing items
- `itemId`: Identifier for current item being processed
- `current`: Current item number (1-based)
- `total`: Total number of items
- `peerService`: Target system for this item
- `inputJSON`: Item-specific data
- `traceId`: Job correlation ID (same as job status logs)

**Behavior**:
- MUST create structured log entry with progress metadata
- MUST set logType to "job.progress"
- MUST format message as "Processing {itemId} ({current}/{total})"
- MUST calculate progressPercentage: Math.round((current / total) * 100)
- MUST include progress fields in inputJSON (currentItem, totalItems, itemId, progressPercentage)

**Example - Batch Processing with Progress Tracking**:
```typescript
async function batchLookup(orgNumbers: string[]): Promise<void> {
  const jobName = 'CompanyLookupBatch';
  const FUNCTIONNAME = 'batchLookup';  // Best practice: Define function name as constant
  const batchTraceId = sovdevGenerateTraceId();  // ONE traceId for entire batch
  const jobStartInput = { totalCompanies: orgNumbers.length };

  // Log job start (see sovdevLogJobStatus example)
  sovdevLogJobStatus(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    jobName,
    'Started',
    PEER_SERVICES.INTERNAL,
    jobStartInput,
    batchTraceId
  );

  // Process each item with progress tracking
  for (let i = 0; i < orgNumbers.length; i++) {
    const orgNumber = orgNumbers[i];
    const itemTraceId = sovdevGenerateTraceId();  // Unique traceId for each item
    const progressInput = { organisasjonsnummer: orgNumber };  // Best practice: Define input as variable

    // Log progress - tracking BRREG processing
    sovdevLogJobProgress(
      SOVDEV_LOGLEVELS.INFO,
      FUNCTIONNAME,                // Use constant
      orgNumber,                    // Item identifier
      i + 1,                        // Current item (1-based)
      orgNumbers.length,            // Total items
      PEER_SERVICES.BRREG,          // External system for this item
      progressInput,                // Use variable
      batchTraceId                  // Progress logs use batch traceId
    );

    // Process the item (uses separate itemTraceId for request/response)
    await lookupCompany(orgNumber, itemTraceId);
  }

  // Log job completion (see sovdevLogJobStatus example)
  const jobCompletionInput = {
    totalCompanies: orgNumbers.length,
    successful: orgNumbers.length,
    failed: 0
  };

  sovdevLogJobStatus(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    jobName,
    'Completed',
    PEER_SERVICES.INTERNAL,
    jobCompletionInput,
    batchTraceId
  );
}

// Result: Two levels of correlation
// 1. Batch level: {traceId="<batch-uuid>"} shows all progress logs + job status
// 2. Item level: {traceId="<item-uuid>"} shows request/response for specific item
```

---

## 5. sovdevFlush

**Purpose**: Flush all pending OTLP batches to ensure logs/metrics/traces are exported.

**Signature** (TypeScript reference):
```typescript
sovdevFlush(): Promise<void>
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
  sovdevInitialize('company-lookup-service', '1.0.0', PEER_SERVICES.mappings);

  try {
    // Application logic
    await batchLookup(orgNumbers);
  } catch (error) {
    sovdevLog(SOVDEV_LOGLEVELS.FATAL, 'main', 'Application crashed', PEER_SERVICES.INTERNAL, null, null, error);
  } finally {
    // CRITICAL: Flush before exit to ensure final logs are exported
    await sovdevFlush();
  }
}

main();
```

**Example - Signal Handlers (Node.js)**:
```typescript
// Ensure flush on process termination
process.on('SIGINT', async () => {
  console.log('Received SIGINT, flushing logs...');
  await sovdevFlush();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('Received SIGTERM, flushing logs...');
  await sovdevFlush();
  process.exit(0);
});

// Flush before normal exit
process.on('beforeExit', async () => {
  await sovdevFlush();
});
```

---

## 6. sovdevGenerateTraceId

**Purpose**: Generate a UUID v4 for trace correlation.

**Signature** (TypeScript reference):
```typescript
sovdevGenerateTraceId(): string
```

**Behavior**:
- MUST return a UUID v4 string
- MUST be lowercase
- MUST be 36 characters (8-4-4-4-12 format with hyphens)
- MUST be unique (cryptographically random)

**Example - Linking Related Operations**:
```typescript
// Generate ONE traceId for related operations
const companyTraceId = sovdevGenerateTraceId();
// Returns: "c3d75d26-d783-48a2-96c3-1e62a37419c7"

// All these operations share the same traceId - linkable in Grafana
sovdevLog(
  SOVDEV_LOGLEVELS.INFO,
  'lookupCompany',
  'Looking up company',
  PEER_SERVICES.BRREG,
  { orgNumber: '971277882' },
  null,
  null,
  companyTraceId  // Shared traceId
);

sovdevLog(
  SOVDEV_LOGLEVELS.INFO,
  'validateCompany',
  'Validating company data',
  PEER_SERVICES.INTERNAL,
  { orgNumber: '971277882' },
  { valid: true },
  null,
  companyTraceId  // SAME traceId
);

sovdevLog(
  SOVDEV_LOGLEVELS.INFO,
  'saveCompany',
  'Saving to database',
  PEER_SERVICES.INTERNAL,
  { orgNumber: '971277882' },
  { success: true },
  null,
  companyTraceId  // SAME traceId
);

// In Grafana: {traceId="c3d75d26-d783-48a2-96c3-1e62a37419c7"} shows all 3 operations together
```

---

## 7. createPeerServices

**Purpose**: Create type-safe peer service mapping with INTERNAL auto-generation.

**Signature** (TypeScript reference):
```typescript
createPeerServices<T extends Record<string, string>>(
  definitions: T
): {
  [K in keyof T]: string;
} & {
  INTERNAL: string;
  mappings: Record<string, string>;
}
```

**Parameters**:
- `definitions`: Object mapping peer service names to CMDB system IDs

**Behavior**:
- MUST create constants for each defined peer service
- MUST auto-generate INTERNAL constant with value equal to service name
- MUST return mappings object for sovdevInitialize()
- MUST provide type-safe access to peer service IDs

**Example - Type-Safe Peer Service Mapping**:
```typescript
// Define peer services - INTERNAL is auto-generated
const PEER_SERVICES = createPeerServices({
  BRREG: 'SYS1234567',  // Norwegian company registry
  ALTINN: 'SYS7654321', // Government portal
  CRM: 'SYS9876543'     // Customer relationship management system
});

// After creation, PEER_SERVICES provides:
// - Type-safe constants (compile-time validation)
// - Auto-generated INTERNAL (equals service name)
// - Mappings object for sovdevInitialize()

// Type-safe usage - compiler prevents typos:
sovdevLog(
  SOVDEV_LOGLEVELS.INFO,
  'fetchCompany',
  'Fetching from BRREG',
  PEER_SERVICES.BRREG,  // ✅ Valid - IntelliSense autocomplete
  { orgNumber: '971277882' }
);

// Compiler error: Property 'BRRG' does not exist
// sovdevLog(..., PEER_SERVICES.BRRG, ...)  // ❌ Typo caught at compile time

// Internal operations use auto-generated INTERNAL:
sovdevLogJobStatus(
  SOVDEV_LOGLEVELS.INFO,
  'processData',
  'DataProcessingJob',
  'Started',
  PEER_SERVICES.INTERNAL,  // Auto-generated, equals service name
  { totalItems: 100 }
);

// Initialize logger with mappings:
sovdevInitialize(
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

```typescript
enum SOVDEV_LOGLEVELS {
  TRACE = 'trace',   // Severity: 1  (OpenTelemetry)
  DEBUG = 'debug',   // Severity: 5  (OpenTelemetry)
  INFO = 'info',     // Severity: 9  (OpenTelemetry)
  WARN = 'warn',     // Severity: 13 (OpenTelemetry)
  ERROR = 'error',   // Severity: 17 (OpenTelemetry)
  FATAL = 'fatal'    // Severity: 21 (OpenTelemetry)
}
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
- **TypeScript/JavaScript**: camelCase (sovdevLog, sovdevFlush)
- **Python**: snake_case (sovdev_log, sovdev_flush)
- **Go**: PascalCase for exported functions (SovdevLog, SovdevFlush)
- **Java**: camelCase (sovdevLog, sovdevFlush)
- **C#**: PascalCase (SovdevLog, SovdevFlush)
- **PHP**: camelCase or snake_case per PSR standards
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
