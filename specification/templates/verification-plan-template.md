# Sovdev-Logger Verification Plan: [LANGUAGE]

**Target Language**: [TypeScript/Python/Go/Java/C#/PHP/Rust/etc.]
**Specification Version**: v1.0.1
**Verification Date**: [DATE]
**Verifier**: [Human/LLM Name]
**Status**: 🟡 IN PROGRESS

---

## Instructions for LLM

**CRITICAL RULES:**
1. ✅ Complete each verification section systematically
2. ✅ Collect actual evidence (command outputs, screenshots, logs)
3. ✅ Mark each item as PASS ✅, FAIL ❌, or SKIP ⏭️
4. ✅ Document ALL failures with details
5. ✅ Compare field-by-field against TypeScript reference implementation
6. ✅ Run ALL verification commands inside `devcontainer-toolbox`

**Verification Legend:**
- ✅ PASS - Verified correct
- ❌ FAIL - Does not match specification
- ⏭️ SKIP - Not applicable or intentionally skipped
- 🔄 IN PROGRESS - Currently verifying

---

## Section 1: API Contract Verification

**Reference**: `specification/01-api-contract.md`
**Status**: ❌ Not started

### 1.1 Function Signatures

Verify all 7 required functions exist with correct parameters:

| Function | Status | Signature Matches Spec | Notes |
|----------|--------|------------------------|-------|
| sovdevInitialize | ❌ | [ ] | |
| sovdevLog | ❌ | [ ] | |
| sovdevLogJobStatus | ❌ | [ ] | |
| sovdevLogJobProgress | ❌ | [ ] | |
| sovdevFlush | ❌ | [ ] | |
| sovdevGenerateTraceId | ❌ | [ ] | |
| createPeerServices | ❌ | [ ] | |

**Evidence**:
```
[Paste function signatures or API documentation here]
```

**Issues Found**:
- [ ] None
- [ ] [Describe any signature mismatches]

---

### 1.2 Best Practices Verification

From `specification/08-anti-patterns.md`:

- [ ] ✅ Functions use `FUNCTIONNAME` constant pattern
- [ ] ✅ Functions define `input` variable and reuse it
- [ ] ✅ Functions define `response` variable and reuse it
- [ ] ✅ `PEER_SERVICES.INTERNAL` auto-generated (equals service name)

**Evidence**:
```
[Paste code examples showing these patterns]
```

**Issues Found**:
- [ ] None
- [ ] [Describe any best practice violations]

---

## Section 2: Field Definitions Verification

**Reference**: `specification/02-field-definitions.md`
**Status**: ❌ Not started

### 2.1 Console Output Fields

Run a simple test and capture console output:

```bash
docker exec devcontainer-toolbox bash -c "cd /workspace/[language]/test && [run-simple-test]"
```

**Required Fields Checklist**:

- [ ] ✅ Timestamp (ISO 8601 format)
- [ ] ✅ Log level (INFO, ERROR, etc.)
- [ ] ✅ Service name
- [ ] ✅ Function name
- [ ] ✅ Message
- [ ] ✅ Trace ID (UUID v4)
- [ ] ✅ Session ID (UUID v4)
- [ ] ✅ Input data (formatted)
- [ ] ✅ Response data (formatted, or "null")
- [ ] ✅ Exception details (if ERROR level)

**Actual Console Output**:
```
[Paste actual console output here]
```

**Issues Found**:
- [ ] None
- [ ] Missing fields: [list]
- [ ] Incorrect format: [describe]

---

### 2.2 File Output Fields (JSON)

Check the JSON log file:

```bash
docker exec devcontainer-toolbox bash -c "cd /workspace/[language] && cat dev.log | head -n 1 | jq ."
```

**Required Fields Checklist**:

- [ ] ✅ `timestamp` (ISO 8601)
- [ ] ✅ `level` (string)
- [ ] ✅ `service.name` (string)
- [ ] ✅ `service.version` (string)
- [ ] ✅ `function.name` (string)
- [ ] ✅ `message` (string)
- [ ] ✅ `traceId` (UUID v4 string)
- [ ] ✅ `sessionId` (UUID v4 string, same for all logs)
- [ ] ✅ `peer.service` (string)
- [ ] ✅ `inputJSON` (string, "null" if no input)
- [ ] ✅ `responseJSON` (string, "null" if no response)
- [ ] ✅ `logType` (transaction/job.status/job.progress)
- [ ] ✅ `exception.type` (always "Error" if exception present)
- [ ] ✅ `exception.message` (string if exception)
- [ ] ✅ `exception.stack` (string if exception, max 350 chars)

**Actual File Output**:
```json
[Paste actual JSON log entry here]
```

**Field Comparison with TypeScript**:

| Field | TypeScript Value | [Language] Value | Match? |
|-------|-----------------|------------------|--------|
| timestamp | [value] | [value] | ✅/❌ |
| level | [value] | [value] | ✅/❌ |
| service.name | [value] | [value] | ✅/❌ |
| ... | ... | ... | ... |

**Issues Found**:
- [ ] None
- [ ] Missing fields: [list]
- [ ] Field type mismatch: [describe]
- [ ] Value format incorrect: [describe]

---

### 2.3 OTLP Output Fields (Loki)

Query Loki for logs:

```bash
# Run E2E test (loads .env with OTLP configuration)
cd specification/tools
./specification/tools/run-company-lookup.sh [language]

# Wait for logs to reach Loki
sleep 10

# Query Loki
./specification/tools/query-loki.sh sovdev-test-company-lookup-[language] --json | \
  jq '.data.result[0].stream' > loki-fields.json
```

**Required OTLP Attributes Checklist**:

- [ ] ✅ `scope_name` (service name, NOT module name)
- [ ] ✅ `scope_version` (string "1.0.0")
- [ ] ✅ `observed_timestamp` (nanoseconds since epoch)
- [ ] ✅ `severity_number` (OpenTelemetry severity number)
- [ ] ✅ `severity_text` (INFO, ERROR, etc.)
- [ ] ✅ `functionName` (string)
- [ ] ✅ `peer_service` (system ID string)
- [ ] ✅ `inputJSON` (string, always present, "null" if no input)
- [ ] ✅ `responseJSON` (string, always present, "null" if no response)
- [ ] ✅ `logType` (transaction/job.status/job.progress)
- [ ] ✅ `traceId` (UUID v4 string)
- [ ] ✅ `sessionId` (UUID v4 string, same for all logs)
- [ ] ✅ `exceptionType` (always "Error" if exception)
- [ ] ✅ `exceptionMessage` (string if exception)
- [ ] ✅ `exceptionStack` (string if exception, max 350 chars)

**Actual Loki Query Result**:
```json
[Paste Loki response here]
```

**Field Comparison with TypeScript**:

| Attribute | TypeScript Value | [Language] Value | Match? |
|-----------|-----------------|------------------|--------|
| scope_name | [value] | [value] | ✅/❌ |
| scope_version | [value] | [value] | ✅/❌ |
| ... | ... | ... | ... |

**Issues Found**:
- [ ] None
- [ ] Missing attributes: [list]
- [ ] Attribute value mismatch: [describe]
- [ ] `scope_name` uses module name instead of service name: ❌

---

## Section 3: Error Handling Verification

**Reference**: `specification/04-error-handling.md`
**Status**: ❌ Not started

### 3.1 Exception Type Standardization

Verify `exceptionType` is always "Error" (not language-specific):

**Test Command**:
```bash
docker exec devcontainer-toolbox bash -c "cd /workspace/[language]/test && [run-error-test]"
```

**Verification**:
- [ ] ✅ `exceptionType` = "Error" (NOT "Exception", "error", "Throwable", etc.)
- [ ] ✅ Applies to all exception types (HTTP errors, validation errors, etc.)

**Actual Exception Log**:
```json
[Paste log entry with exception]
```

**Issues Found**:
- [ ] None
- [ ] Uses language-specific type: [actual value]

---

### 3.2 Stack Trace Limiting

Verify stack traces are limited to 350 characters:

**Test Command**:
```bash
# Generate exception with long stack trace
docker exec devcontainer-toolbox bash -c "cd /workspace/[language]/test && [run-long-stack-test]"

# Check stack length
docker exec devcontainer-toolbox bash -c "cd /workspace/[language] && cat dev.log | jq -r '.exception.stack' | wc -c"
```

**Verification**:
- [ ] ✅ Stack trace ≤ 350 characters
- [ ] ✅ Truncation message appended: "... (truncated)"
- [ ] ✅ Most useful part of stack preserved (top frames)

**Actual Stack Length**: [number] characters

**Issues Found**:
- [ ] None
- [ ] Stack trace exceeds 350 chars: [actual length]
- [ ] No truncation message

---

### 3.3 Credential Removal

Verify credentials are removed from stack traces:

**Test Command**:
```bash
# Create test with Authorization header in exception
docker exec devcontainer-toolbox bash -c "cd /workspace/[language]/test && [run-credential-test]"

# Check for credentials in logs
docker exec devcontainer-toolbox bash -c "cd /workspace/[language] && cat dev.log | grep -i 'authorization\|bearer\|password\|api_key'"
```

**Required Patterns Redacted**:
- [ ] ✅ `Authorization` headers → `Authorization: [REDACTED]`
- [ ] ✅ `Bearer` tokens → `Bearer [REDACTED]`
- [ ] ✅ API keys (`api_key`, `apiKey`, `x-api-key`) → `[REDACTED]`
- [ ] ✅ Passwords (`password`, `pwd`, `pass`) → `[REDACTED]`
- [ ] ✅ JWT tokens → `[REDACTED]`
- [ ] ✅ Session IDs → `[REDACTED]`
- [ ] ✅ Cookie values → `[REDACTED]`

**Verification**:
- [ ] ✅ Credential removal happens BEFORE truncation
- [ ] ✅ No credentials visible in dev.log
- [ ] ✅ No credentials visible in Loki

**Issues Found**:
- [ ] None
- [ ] Credentials visible: [list patterns found]
- [ ] Removal happens after truncation: ❌

---

### 3.4 Graceful Degradation

Verify system continues working when OTLP endpoint unavailable:

**Test Command**:
```bash
# Run test with invalid OTLP endpoint
docker exec devcontainer-toolbox bash -c "cd /workspace/[language]/test && OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://invalid-endpoint:9999 [run-test]"
```

**Verification**:
- [ ] ✅ Application completes successfully (exit code 0)
- [ ] ✅ Logs still written to console
- [ ] ✅ Logs still written to file
- [ ] ✅ No application crash or exception thrown
- [ ] ✅ Warning logged about OTLP failure (optional)

**Issues Found**:
- [ ] None
- [ ] Application crashes when OTLP unavailable: ❌
- [ ] Console/file logging stops: ❌

---

## Section 4: Environment Configuration Verification

**Reference**: `specification/05-environment-configuration.md`
**Status**: ❌ Not started

### 4.1 Environment Variables Support

Verify all required environment variables are read:

| Variable | Supported | Default Value | Notes |
|----------|-----------|---------------|-------|
| SYSTEM_ID | ❌ | [service-name] | Service identifier |
| LOG_TO_CONSOLE | ❌ | true | Console output enabled |
| LOG_TO_FILE | ❌ | true | File output enabled |
| LOG_FILE_PATH | ❌ | ./dev.log | Main log file path |
| ERROR_LOG_PATH | ❌ | ./error.log | Error log file path |
| OTEL_EXPORTER_OTLP_LOGS_ENDPOINT | ❌ | (none) | OTLP logs endpoint |
| OTEL_EXPORTER_OTLP_METRICS_ENDPOINT | ❌ | (none) | OTLP metrics endpoint |
| OTEL_EXPORTER_OTLP_TRACES_ENDPOINT | ❌ | (none) | OTLP traces endpoint |
| OTEL_EXPORTER_OTLP_HEADERS | ❌ | (none) | HTTP headers for routing |

**Issues Found**:
- [ ] None
- [ ] Missing environment variable support: [list]
- [ ] Incorrect default value: [describe]

---

### 4.2 File Rotation Configuration

Verify log file rotation is configured correctly:

**Test Command**:
```bash
# Check file rotation configuration
docker exec devcontainer-toolbox bash -c "cd /workspace/[language] && [check-rotation-config]"
```

**Required Configuration**:

| Log Type | Max Size | Max Files | Total Disk | Configured? |
|----------|----------|-----------|------------|-------------|
| Main log | 50 MB | 5 files | ~250 MB | ❌ |
| Error log | 10 MB | 3 files | ~30 MB | ❌ |

**Verification**:
- [ ] ✅ Main log rotates at 50MB
- [ ] ✅ Keeps 5 rotated files max
- [ ] ✅ Error log rotates at 10MB
- [ ] ✅ Keeps 3 error files max
- [ ] ✅ Old files are deleted automatically

**Issues Found**:
- [ ] None
- [ ] No rotation configured: ❌
- [ ] Incorrect size limits: [actual values]

---

## Section 5: Test Scenarios Verification

**Reference**: `specification/06-test-scenarios.md`
**Status**: ❌ Not started

### 5.1 Scenario Execution Results

Run all 11 test scenarios and record results:

| Scenario | Description | Status | Notes |
|----------|-------------|--------|-------|
| 01 | INFO log - basic logging | ❌ | |
| 02 | ERROR log with exception | ❌ | |
| 03 | Job status tracking | ❌ | |
| 04 | Job progress tracking | ❌ | |
| 05 | Null response handling | ❌ | |
| 06 | Credential removal | ❌ | |
| 07 | Trace correlation | ❌ | |
| 08 | Session correlation | ❌ | |
| 09 | Metrics generation | ❌ | |
| 10 | Traces generation | ❌ | |
| 11 | Grafana dashboard | ❌ | |

**Test Execution Command**:
```bash
cd specification/tools
./run-company-lookup.sh [language]
```

**Test Output**:
```
[Paste test suite output here]
```

**Issues Found**:
- [ ] None
- [ ] Failed scenarios: [list with details]

---

### 5.2 Trace Correlation Verification (Scenario 07)

Verify same `traceId` is reused for related logs:

**Test**: Log request → response → error with same traceId

**Verification Command**:
```bash
# Query Loki for logs and extract traceIds
./specification/tools/query-loki.sh sovdev-test-company-lookup-[language] --json | \
  jq '.data.result[].stream.traceId' | sort | uniq -c
```

**Verification**:
- [ ] ✅ Multiple logs share same `traceId`
- [ ] ✅ Request log has traceId = [value]
- [ ] ✅ Response log has traceId = [same value]
- [ ] ✅ Error log has traceId = [same value]

**Issues Found**:
- [ ] None
- [ ] Different traceIds for related logs: ❌

---

### 5.3 Session Correlation Verification (Scenario 08)

Verify same `sessionId` for all logs in single execution:

**Verification Command**:
```bash
# Query Loki for all logs and extract sessionIds
./specification/tools/query-loki.sh sovdev-test-company-lookup-[language] --json | \
  jq '.data.result[].stream.session_id' | sort -u
```

**Verification**:
- [ ] ✅ All logs have same `sessionId`
- [ ] ✅ SessionId is UUID v4 format
- [ ] ✅ SessionId different from previous execution

**Actual SessionIds Found**: [list unique sessionIds]

**Issues Found**:
- [ ] None
- [ ] Multiple sessionIds in single execution: ❌
- [ ] SessionId not UUID v4 format: ❌

---

## Section 6: Metrics Verification (Prometheus)

**Reference**: `specification/00-design-principles.md` section 5
**Status**: ❌ Not started

### 6.1 Required Metrics

Query Prometheus for all required metrics:

```bash
# Query all metrics (human-readable)
./specification/tools/query-prometheus.sh sovdev-test-company-lookup-[language]

# Get all metrics in JSON for detailed verification
./specification/tools/query-prometheus.sh sovdev-test-company-lookup-[language] --json > prometheus-metrics.json
```

**Required Metrics Checklist**:

- [ ] ✅ `sovdev_operations_total` (Counter)
- [ ] ✅ `sovdev_errors_total` (Counter)
- [ ] ✅ `sovdev_operation_duration` (Histogram)
- [ ] ✅ `sovdev_operations_active` (UpDownCounter)

**Metric Labels Checklist**:

- [ ] ✅ `service_name` label present
- [ ] ✅ `peer_service` label present
- [ ] ✅ `log_type` label present

**Query Results**:
```json
[Paste Prometheus query results here]
```

**Issues Found**:
- [ ] None
- [ ] Missing metrics: [list]
- [ ] Missing labels: [list]

---

## Section 7: Traces Verification (Tempo)

**Reference**: `specification/00-design-principles.md` section 5
**Status**: ❌ Not started

### 7.1 Span Creation

Query Tempo for traces:

```bash
# Search for traces (human-readable)
./specification/tools/query-tempo.sh sovdev-test-company-lookup-[language] --limit 10

# Get traces in JSON for detailed verification
./specification/tools/query-tempo.sh sovdev-test-company-lookup-[language] --json > tempo-traces.json
```

**Verification**:
- [ ] ✅ Traces exist in Tempo
- [ ] ✅ Span created for each `sovdevLog()` call
- [ ] ✅ Span names match function names
- [ ] ✅ Span attributes include: `functionName`, `peer.service`, `logType`, `traceId`, `sessionId`
- [ ] ✅ ERROR-level logs create spans with error status

**Query Results**:
```json
[Paste Tempo search results here]
```

**Issues Found**:
- [ ] None
- [ ] No traces found: ❌
- [ ] Missing span attributes: [list]
- [ ] ERROR spans not marked with error status: ❌

---

## Section 8: Anti-Patterns Check

**Reference**: `specification/08-anti-patterns.md`
**Status**: ❌ Not started

### 8.1 Anti-Pattern Verification

Check implementation does NOT have these anti-patterns:

- [ ] ✅ **NOT** using module/class name for `scope_name` (uses service name ✓)
- [ ] ✅ **NOT** using language-specific exception types (uses "Error" ✓)
- [ ] ✅ **NOT** missing `responseJSON` field (always present ✓)
- [ ] ✅ **NOT** generating new traceId for related logs (reuses traceId ✓)
- [ ] ✅ **NOT** forgetting to flush before exit (calls sovdevFlush() ✓)
- [ ] ✅ **NOT** using different sessionIds in same execution (uses same sessionId ✓)
- [ ] ✅ **NOT** hardcoding function names (uses FUNCTIONNAME constant ✓)
- [ ] ✅ **NOT** using inline objects (defines input/response variables ✓)
- [ ] ✅ **NOT** missing file rotation (configured correctly ✓)

**Issues Found**:
- [ ] None
- [ ] Anti-patterns detected: [list with evidence]

---

## Section 9: Performance Verification

**Status**: ❌ Not started

### 9.1 Logging Overhead Measurement

Measure time per log call:

**Test Command**:
```bash
docker exec devcontainer-toolbox bash -c "cd /workspace/[language]/test && [run-performance-test]"
```

**Target**: < 1ms per log call

**Actual Measurement**: [number] ms per log call

**Verification**:
- [ ] ✅ Logging overhead < 1ms per call
- [ ] ⚠️ Logging overhead 1-5ms per call (acceptable, but consider optimization)
- [ ] ❌ Logging overhead > 5ms per call (needs optimization)

**Issues Found**:
- [ ] None
- [ ] Performance exceeds target: [actual measurement]

---

## Section 10: Documentation Verification

**Status**: ❌ Not started

### 10.1 Documentation Completeness

Check implementation includes adequate documentation:

- [ ] ✅ README.md with setup instructions
- [ ] ✅ Example code provided
- [ ] ✅ Dependencies documented
- [ ] ✅ DevContainer execution instructions
- [ ] ✅ API documentation (function signatures and parameters)
- [ ] ✅ Environment variables documented
- [ ] ✅ Troubleshooting section

**Issues Found**:
- [ ] None
- [ ] Missing documentation: [list]

---

## Final Verification Summary

### Overall Status

**Total Checks**: [number]
**Passed**: [number] ✅
**Failed**: [number] ❌
**Skipped**: [number] ⏭️

**Completion Percentage**: [number]%

### Critical Issues (Must Fix)

1. [Issue description] - **Impact**: [High/Medium/Low]
   - **Location**: [file:line or component]
   - **Expected**: [what should happen]
   - **Actual**: [what happens now]
   - **Fix**: [suggested solution]

2. [Continue for all critical issues]

### Non-Critical Issues (Nice to Fix)

1. [Issue description]
2. [Continue]

### Verification Decision

- [ ] ✅ **APPROVED**: Implementation is specification-compliant
- [ ] ⚠️ **APPROVED WITH CONDITIONS**: Minor issues, but acceptable
- [ ] ❌ **REJECTED**: Critical issues must be fixed before approval

**Verifier Sign-Off**: [Name]
**Date**: [Date]
**Notes**: [Additional comments]

---

## Comparison with Reference Implementation

### Field-by-Field Comparison Table

Compare actual output with TypeScript reference implementation:

| Field/Attribute | TypeScript | [Language] | Match | Notes |
|-----------------|-----------|-----------|-------|-------|
| Console: timestamp | [value] | [value] | ✅/❌ | |
| Console: level | [value] | [value] | ✅/❌ | |
| File: service.name | [value] | [value] | ✅/❌ | |
| File: responseJSON | [value] | [value] | ✅/❌ | |
| OTLP: scope_name | [value] | [value] | ✅/❌ | |
| OTLP: exceptionType | [value] | [value] | ✅/❌ | |
| ... | ... | ... | ... | |

**Mismatches Found**: [number]

**Critical Mismatches** (breaking specification):
- [List any critical mismatches]

**Minor Differences** (acceptable variations):
- [List any minor differences]

---

## Evidence Archive

Store all evidence files in: `[language]/verification/evidence/[date]/`

**Files to Archive**:
- [ ] Console output samples
- [ ] dev.log samples
- [ ] error.log samples
- [ ] Loki query results
- [ ] Prometheus query results
- [ ] Tempo query results
- [ ] Grafana screenshots (optional)
- [ ] Performance benchmark results
- [ ] Test suite output

**Archive Command**:
```bash
mkdir -p [language]/verification/evidence/[date]
# Copy all evidence files to archive directory
```

---

**Template Version**: 1.0.0
**Last Updated**: 2025-10-07
