# Sovdev-Logger Implementation Plan: [LANGUAGE]

**Target Language**: [TypeScript/Python/Go/Java/C#/PHP/Rust/etc.]
**Specification Version**: v1.0.1
**Implementation Start Date**: [DATE]
**Status**: 🟡 IN PROGRESS

---

## Instructions for LLM

**CRITICAL RULES:**
1. ✅ Complete each stage fully before moving to the next stage
2. ✅ Update status checkboxes (❌ → 🔄 → ✅) as you work
3. ✅ Run ALL verification commands and record outputs
4. ✅ If verification fails, STOP and fix before proceeding
5. ✅ Update "Evidence" sections with actual outputs
6. ✅ All code execution MUST happen inside `devcontainer-toolbox`

**Progress Legend:**
- ❌ Not started
- 🔄 In progress
- ✅ Complete and verified
- ⚠️ Failed verification (needs fix)

---

## Pre-Flight Checklist

Complete these before starting Stage 1:

- [ ] **Read Specification Documents** (in order):
  - [ ] `specification/00-design-principles.md` - Core philosophy
  - [ ] `specification/01-api-contract.md` - API to implement
  - [ ] `specification/02-field-definitions.md` - Required fields
  - [ ] `specification/04-error-handling.md` - Security patterns
  - [ ] `specification/05-environment-configuration.md` - DevContainer setup
  - [ ] `specification/06-test-scenarios.md` - Testing approach
  - [ ] `specification/08-anti-patterns.md` - Common mistakes

- [ ] **DevContainer Ready**: Verify `devcontainer-toolbox` is running
  ```bash
  docker ps | grep devcontainer-toolbox
  ```

- [ ] **Language Runtime Available**: Verify [language] runtime exists in DevContainer
  ```bash
  docker exec devcontainer-toolbox bash -c "[version-command]"
  # Examples: node --version, python3 --version, go version, javac -version
  ```

- [ ] **Reference Implementation**: Reviewed TypeScript implementation at `typescript/src/`

**Pre-Flight Status**: ❌ Not started

---

## Stage 1: Project Structure Setup

**Status**: ❌ Not started
**Goal**: Create directory structure and dependency files

### Deliverables

- [ ] Created `[language]/` directory in repository root
- [ ] Created `[language]/src/` for source code
- [ ] Created `[language]/test/` for tests
- [ ] Created `[language]/test/unit/` for unit tests
- [ ] Created `[language]/test/integration/` for integration tests
- [ ] Created `[language]/test/e2e/company-lookup/` directory (REQUIRED - see specification/06-test-scenarios.md)
- [ ] Created `[language]/test/e2e/company-lookup/run-test.sh` script (entry point)
- [ ] Created `[language]/test/e2e/company-lookup/.env` file (OTLP configuration)
- [ ] Created `[language]/test/e2e/company-lookup/logs/` directory (output directory)
- [ ] Created package/dependency file (e.g., package.json, go.mod, pom.xml, composer.json)
- [ ] Added OpenTelemetry SDK dependencies
- [ ] Created basic README.md with setup instructions

### Verification Commands

```bash
# Run inside DevContainer
docker exec devcontainer-toolbox bash -c "cd /workspace/[language] && find . -type d -o -type f | head -20"
```

**Expected Output**:
```
./src/
./test/
./test/unit/
./test/integration/
./test/e2e/
./test/e2e/company-lookup/
./test/e2e/company-lookup/run-test.sh
./test/e2e/company-lookup/.env
./test/e2e/company-lookup/logs/
./[package-file]
./README.md
```

### Success Criteria

✅ All directories created
✅ Dependency file includes OpenTelemetry SDK
✅ Can install dependencies without errors

### Evidence

```
[Paste ls -la output here after completion]
```

**Stage 1 Status**: ❌ → Move to Stage 2 only after all checkboxes complete

---

## Stage 2: API Skeleton

**Status**: ❌ Not started
**Goal**: Create function signatures for all 7 required functions

### Deliverables

From `specification/01-api-contract.md`:

- [ ] **sovdevInitialize**(serviceName, serviceVersion, peerServiceMappings)
- [ ] **sovdevLog**(level, functionName, message, peerService, input, response, exception, traceId)
- [ ] **sovdevLogJobStatus**(level, functionName, jobName, status, peerService, input, traceId)
- [ ] **sovdevLogJobProgress**(level, functionName, itemName, current, total, peerService, input, traceId)
- [ ] **sovdevFlush**() - Returns Promise/Future/equivalent
- [ ] **sovdevGenerateTraceId**() - Returns UUID v4 string
- [ ] **createPeerServices**(definitions) - Returns type-safe peer service object

### Best Practices Checklist

From `specification/08-anti-patterns.md`:

- [ ] Functions use `FUNCTIONNAME` constant pattern
- [ ] Functions define `input` variable and reuse it
- [ ] Functions define `response` variable and reuse it
- [ ] `PEER_SERVICES.INTERNAL` auto-generated (equals service name)
- [ ] All functions documented with comments

### Verification Commands

```bash
# Compile/parse without errors
docker exec devcontainer-toolbox bash -c "cd /workspace/[language] && [compile-command]"
```

### Success Criteria

✅ All 7 functions exist with correct parameter lists
✅ Code compiles/parses without errors
✅ Type signatures match specification (adapted to language idioms)
✅ Best practices constants (FUNCTIONNAME, input, response) used

### Evidence

```
[Paste function signatures or API documentation here]
```

**Stage 2 Status**: ❌ → Move to Stage 3 only after all checkboxes complete

---

## Stage 3: Console and File Output

**Status**: ❌ Not started
**Goal**: Implement logging to console (stdout) and file (JSON)

### Deliverables

From `specification/02-field-definitions.md`:

**Console Output Format:**
- [ ] Timestamp in ISO 8601 format
- [ ] Log level (INFO, ERROR, etc.)
- [ ] Service name
- [ ] Function name
- [ ] Message
- [ ] Trace ID
- [ ] Session ID
- [ ] Input/Response data (formatted)
- [ ] Exception details (if present)

**File Output Format (JSON):**
- [ ] `timestamp` field
- [ ] `level` field
- [ ] `service.name` field
- [ ] `service.version` field
- [ ] `function.name` field
- [ ] `message` field
- [ ] `traceId` field (UUID v4)
- [ ] `sessionId` field (UUID v4, same for all logs in execution)
- [ ] `peer.service` field
- [ ] `inputJSON` field (always present, "null" if no input)
- [ ] `responseJSON` field (always present, "null" if no response)
- [ ] `logType` field (transaction, job.status, job.progress)

**File Rotation Configuration:**
- [ ] Main log: 50MB max size, 5 files
- [ ] Error log: 10MB max size, 3 files (ERROR level only)

### Verification Commands

```bash
# Create simple test
docker exec devcontainer-toolbox bash -c "cd /workspace/[language]/test && [create-test-file]"

# Run test
docker exec devcontainer-toolbox bash -c "cd /workspace/[language] && [run-test-command]"

# Check console output
[Output should appear in terminal]

# Check file output
docker exec devcontainer-toolbox bash -c "cd /workspace/[language] && cat dev.log"
```

### Success Criteria

✅ Console output is human-readable with all required fields
✅ File output is valid JSON with all required fields
✅ `sessionId` is same for all logs in single execution
✅ `traceId` is unique per log (or reused when passed explicitly)
✅ `inputJSON` and `responseJSON` always present (value "null" when no data)
✅ File rotation configured correctly

### Evidence

**Console Output:**
```
[Paste console output here]
```

**File Output (dev.log):**
```json
[Paste JSON log entry here]
```

**Stage 3 Status**: ❌ → Move to Stage 4 only after all checkboxes complete

---

## Stage 4: OTLP Logs Integration (Loki)

**Status**: ❌ Not started
**Goal**: Send logs to OpenTelemetry Collector → Loki

### Deliverables

From `specification/05-environment-configuration.md`:

- [ ] OpenTelemetry Logs SDK integrated
- [ ] OTLP HTTP exporter configured
- [ ] Reads `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` environment variable
- [ ] Reads `OTEL_EXPORTER_OTLP_HEADERS` environment variable (for routing)
- [ ] Batch processor configured (export every 1000 logs or 5 seconds)
- [ ] Graceful degradation when endpoint unavailable

**Required OTLP Attributes:**
- [ ] `scope_name` = service name (NOT module name)
- [ ] `scope_version` = "1.0.0"
- [ ] `observed_timestamp` = nanoseconds since epoch
- [ ] `severity_number` = OpenTelemetry severity number
- [ ] `severity_text` = "INFO", "ERROR", etc.
- [ ] `functionName` attribute
- [ ] `peer_service` attribute
- [ ] `inputJSON` attribute (always present)
- [ ] `responseJSON` attribute (always present, "null" when no response)
- [ ] `logType` attribute (transaction, job.status, job.progress)
- [ ] `traceId` attribute
- [ ] `sessionId` attribute

### Verification Commands

```bash
# Ensure .env file is configured with OTLP endpoints
# File: [language]/test/e2e/company-lookup/.env
# Must contain:
#   SYSTEM_ID=sovdev-test-[language]-verification
#   OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://127.0.0.1/v1/logs
#   OTEL_EXPORTER_OTLP_HEADERS={"Host":"otel.localhost"}

# Run E2E test (loads .env automatically)
cd specification/tools
./specification/tools/run-company-lookup.sh [language]

# Wait 10 seconds for logs to reach Loki
sleep 10

# Query Loki for logs
./specification/tools/query-loki.sh sovdev-test-company-lookup-[language] --limit 10
```

### Success Criteria

✅ Logs appear in Loki query results
✅ `scope_name` = service name (verified)
✅ All required OTLP attributes present
✅ `responseJSON` always present (value "null" when no response)
✅ `sessionId` same for all logs in single execution
✅ System continues working when OTLP endpoint unavailable (graceful degradation)

### Evidence

**Loki Query Result:**
```json
[Paste Loki query response here - verify all fields present]
```

**Field Verification Checklist:**
- [ ] scope_name present and correct
- [ ] scope_version = "1.0.0"
- [ ] observed_timestamp present
- [ ] severity_number present
- [ ] severity_text present
- [ ] functionName present
- [ ] peer_service present
- [ ] inputJSON present (value "null" if no input)
- [ ] responseJSON present (value "null" if no response)
- [ ] logType present
- [ ] traceId present (UUID v4 format)
- [ ] sessionId present (same for all logs)

**Stage 4 Status**: ❌ → Move to Stage 5 only after all checkboxes complete

---

## Stage 5: Metrics Integration (Prometheus)

**Status**: ❌ Not started
**Goal**: Automatic metric generation from log calls

### Deliverables

From `specification/00-design-principles.md`:

- [ ] OpenTelemetry Metrics SDK integrated
- [ ] Reads `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` environment variable
- [ ] **sovdev.operations.total**: Counter for all operations
- [ ] **sovdev.errors.total**: Counter for errors by type
- [ ] **sovdev.operation.duration**: Histogram for operation timings
- [ ] **sovdev.operations.active**: UpDownCounter for active operations

### Verification Commands

```bash
# Ensure .env file includes metrics endpoint
# File: [language]/test/e2e/company-lookup/.env
# Must contain:
#   OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://127.0.0.1/v1/metrics

# Run E2E test
cd specification/tools
./run-company-lookup.sh [language]

# Wait 15 seconds for metrics to reach Prometheus
sleep 15

# Query Prometheus for metrics
./specification/tools/query-prometheus.sh sovdev-test-company-lookup-[language]

# Get JSON for detailed verification
./specification/tools/query-prometheus.sh sovdev-test-company-lookup-[language] --json | \
  jq '.data.result[] | {metric: .metric.__name__, value: .value[1]}'
```

### Success Criteria

✅ `sovdev_operations_total` metric exists in Prometheus
✅ `sovdev_errors_total` metric exists in Prometheus
✅ Metric labels include `service_name`, `peer_service`, `log_type`
✅ Counter values match expected log counts

### Evidence

**Prometheus Query Result (operations_total):**
```json
[Paste Prometheus response here]
```

**Prometheus Query Result (errors_total):**
```json
[Paste Prometheus response here]
```

**Stage 5 Status**: ❌ → Move to Stage 6 only after all checkboxes complete

---

## Stage 6: Traces Integration (Tempo)

**Status**: ❌ Not started
**Goal**: Automatic span creation for every log call

### Deliverables

From `specification/00-design-principles.md`:

- [ ] OpenTelemetry Traces SDK integrated
- [ ] Reads `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` environment variable
- [ ] Span created for each `sovdevLog()` call
- [ ] Span attributes include: `functionName`, `peer.service`, `logType`, `traceId`, `sessionId`
- [ ] Span status set based on log level (ERROR → span error status)

### Verification Commands

```bash
# Ensure .env file includes traces endpoint
# File: [language]/test/e2e/company-lookup/.env
# Must contain:
#   OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1/v1/traces

# Run E2E test
cd specification/tools
./run-company-lookup.sh [language]

# Wait 15 seconds for traces to reach Tempo
sleep 15

# Query Tempo for traces
./specification/tools/query-tempo.sh sovdev-test-company-lookup-[language] --limit 10

# Get JSON for detailed verification
./specification/tools/query-tempo.sh sovdev-test-company-lookup-[language] --json | \
  jq '.traces[] | {traceID, rootTraceName, startTimeUnixNano}'
```

### Success Criteria

✅ Traces appear in Tempo query results
✅ Span names match function names
✅ Span attributes include all required fields
✅ ERROR-level logs create spans with error status

### Evidence

**Tempo Query Result:**
```json
[Paste Tempo search response here]
```

**Stage 6 Status**: ❌ → Move to Stage 7 only after all checkboxes complete

---

## Stage 7: Error Handling and Security

**Status**: ❌ Not started
**Goal**: Implement credential removal and stack trace limiting

### Deliverables

From `specification/04-error-handling.md`:

**Exception Type Standardization:**
- [ ] `exceptionType` always = "Error" (NOT language-specific type)
- [ ] Applies to all languages (Python "Exception" → "Error", Go "error" → "Error")

**Stack Trace Limiting:**
- [ ] Stack traces limited to 350 characters maximum
- [ ] Truncation message appended: "... (truncated)"

**Credential Removal (before truncation):**
- [ ] Remove `Authorization` headers (case-insensitive)
- [ ] Remove `Bearer` tokens
- [ ] Remove API keys (patterns: `api_key`, `apiKey`, `x-api-key`)
- [ ] Remove passwords (patterns: `password`, `pwd`, `pass`)
- [ ] Remove JWT tokens (base64 patterns)
- [ ] Remove session IDs (`sessionid`, `JSESSIONID`, `PHPSESSID`)
- [ ] Remove cookie values

**Graceful Degradation:**
- [ ] Logging continues if OTLP endpoint unavailable
- [ ] Errors logged to console/file even when OTLP fails
- [ ] No application crashes due to logging failures

### Verification Commands

```bash
# Create test with exception containing credentials
docker exec devcontainer-toolbox bash -c "cd /workspace/[language]/test && [create-error-test]"

# Run test
docker exec devcontainer-toolbox bash -c "cd /workspace/[language] && [run-error-test]"

# Check stack trace in dev.log
docker exec devcontainer-toolbox bash -c "cd /workspace/[language] && cat dev.log | grep -i 'authorization\|bearer\|password'"
```

### Success Criteria

✅ `exceptionType` = "Error" (verified in logs)
✅ Stack traces limited to 350 characters
✅ No credentials visible in stack traces (Authorization, Bearer, passwords redacted)
✅ Application continues running when OTLP endpoint unavailable
✅ Credential removal happens BEFORE truncation

### Evidence

**Error Log Entry:**
```json
[Paste error log showing exceptionType="Error", truncated stack, redacted credentials]
```

**Graceful Degradation Test:**
```
[Describe test where OTLP endpoint is unavailable - app should continue working]
```

**Stage 7 Status**: ❌ → Move to Stage 8 only after all checkboxes complete

---

## Stage 8: Complete E2E Test Suite

**Status**: ❌ Not started
**Goal**: Run all 11 test scenarios from specification

### Deliverables

From `specification/06-test-scenarios.md`:

- [ ] **Scenario 01**: INFO log - basic logging
- [ ] **Scenario 02**: ERROR log with exception
- [ ] **Scenario 03**: Job status tracking (Started → Completed)
- [ ] **Scenario 04**: Job progress tracking (batch processing)
- [ ] **Scenario 05**: Null response handling
- [ ] **Scenario 06**: Credential removal from stack traces
- [ ] **Scenario 07**: Trace correlation (same traceId for related logs)
- [ ] **Scenario 08**: Session correlation (same sessionId for all logs in execution)
- [ ] **Scenario 09**: Metrics generation verification
- [ ] **Scenario 10**: Traces generation verification
- [ ] **Scenario 11**: Grafana dashboard verification

### Verification Commands

```bash
# Run complete E2E test with backend verification
cd specification/tools
./run-company-lookup-validate.sh [language]

# This will:
# 1. Run application in devcontainer (all 11 scenarios)
# 2. Wait for telemetry export (15s)
# 3. Query Loki for logs
# 4. Query Prometheus for metrics
# 5. Query Tempo for traces
# 6. Display test summary with pass/fail counts
```

### Success Criteria

✅ All 11 test scenarios pass
✅ No regressions from earlier stages
✅ Field-by-field comparison with TypeScript output matches
✅ Grafana dashboards display data correctly

### Evidence

**Test Suite Output:**
```
[Paste full test suite results here]
```

**Stage 8 Status**: ❌ → Move to Final Sign-Off only after all checkboxes complete

---

## Final Sign-Off

**Status**: ❌ Not started
**Goal**: Confirm implementation is specification-compliant

### Implementation Compliance Checklist

From `specification/00-design-principles.md`:

- [ ] ✅ **JSON Output**: Identical structure to TypeScript reference
- [ ] ✅ **All Transports**: Console, file, error file, and OTLP working simultaneously
- [ ] ✅ **Field Parity**: All required fields present in all log types
- [ ] ✅ **API Consistency**: All 7 functions with identical signatures (language-adapted)
- [ ] ✅ **E2E Tests Pass**: Logs/metrics/traces reach backends with correct structure
- [ ] ✅ **Security**: Credential removal and stack trace limiting work
- [ ] ✅ **Performance**: Logging overhead < 1ms per call (measured)
- [ ] ✅ **Graceful Degradation**: System continues when OpenTelemetry export fails

### Anti-Pattern Verification

From `specification/08-anti-patterns.md`:

- [ ] ✅ Uses service name for `scope_name` (NOT module name)
- [ ] ✅ `exceptionType` always "Error" (NOT language-specific)
- [ ] ✅ `responseJSON` always present (value "null" when no response)
- [ ] ✅ Same `traceId` reused for related logs
- [ ] ✅ `sovdevFlush()` called before exit
- [ ] ✅ Same `sessionId` for all logs in execution
- [ ] ✅ `FUNCTIONNAME` constant pattern used
- [ ] ✅ `input`/`response` variables defined and reused
- [ ] ✅ File rotation configured (50MB/5 files main, 10MB/3 files error)

### Documentation

- [ ] README.md created with setup instructions
- [ ] Example code provided
- [ ] Dependencies documented
- [ ] DevContainer execution instructions included

### Performance Benchmark

```bash
# Measure logging overhead
docker exec devcontainer-toolbox bash -c "cd /workspace/[language]/test && [run-performance-test]"
```

**Expected**: < 1ms per log call

**Actual Performance**: [Record actual measurement]

---

## Implementation Summary

**Total Stages Completed**: 0 / 8
**Overall Status**: 🟡 IN PROGRESS

**Completion Date**: [DATE]
**Final Status**: ❌ NOT COMPLETE

### Known Issues

[List any remaining issues or limitations]

### Next Steps

[List any follow-up work needed]

---

## Rollback Instructions

If a stage verification fails:

1. **Identify the failing verification**: Note which success criterion failed
2. **Review specification section**: Re-read relevant specification document
3. **Compare with TypeScript**: Check TypeScript implementation for pattern reference
4. **Fix the issue**: Update code to match specification
5. **Re-run verification**: Repeat verification commands
6. **Update status**: Change from ⚠️ back to 🔄, then ✅ when passing

**Do NOT proceed to next stage until current stage verification passes.**

---

**Template Version**: 1.0.0
**Last Updated**: 2025-10-07
