# LLM Implementation Checklist - [LANGUAGE]

**Copy this file to:** `<language>/llm-work/llm-checklist-<language>.md`

**Update checkboxes as you complete each step. This ensures systematic implementation.**

---

## Phase 0: Pre-Implementation Setup

### Language Toolchain
- [ ] Checked if language is installed: `<language-command> --version`
- [ ] If not installed: Ran `.devcontainer/additions/install-dev-<language>.sh`
- [ ] Verified installation successful

### OpenTelemetry SDK Verification
- [ ] Visited https://opentelemetry.io/docs/languages/
- [ ] Verified SDK exists for language: **[SDK Status: Stable/Beta/Alpha]**
- [ ] Verified SDK supports: Logs ✅ Metrics ✅ Traces ✅
- [ ] If Beta/Alpha: Documented limitations

### TypeScript Reference Study
- [ ] Read `typescript/src/logger.ts` completely
- [ ] Read TypeScript OTEL SDK docs: https://opentelemetry.io/docs/languages/js/
- [ ] Understood how TypeScript:
  - [ ] Initializes providers (log, metric, trace)
  - [ ] Configures OTLP exporters
  - [ ] Sets headers (`Host: otel.localhost`)
  - [ ] Creates metric instruments
  - [ ] Sets metric attributes (underscore notation)
  - [ ] Records duration (milliseconds via Date.now())
  - [ ] Specifies histogram unit (`unit: 'ms'`)

### Target Language SDK Study
- [ ] Read Getting Started guide for language
- [ ] Read Logs API documentation
- [ ] Read Metrics API documentation
- [ ] Read Traces API documentation
- [ ] Read OTLP HTTP Exporter documentation

### Critical Questions Answered

| Question | TypeScript Answer | [LANGUAGE] Answer | Issue? | Workaround? |
|----------|-------------------|-------------------|---------|-------------|
| HTTP headers work? | Yes via `headers` | | | |
| Attribute notation? | Underscores | | | |
| Time unit? | Milliseconds | | | |
| Histogram unit? | `unit: 'ms'` | | | |
| Semantic conventions? | Manual | | | |

### SDK Comparison Document
- [ ] Created `<language>/llm-work/otel-sdk-comparison.md`
- [ ] Documented HTTP client behavior
- [ ] Documented metric attribute patterns
- [ ] Documented duration/time handling
- [ ] Documented histogram configuration
- [ ] Documented known issues and workarounds

---

## Phase 1: Basic OTLP Setup

### Project Structure
- [ ] Created `<language>/src/` directory
- [ ] Created `<language>/test/e2e/company-lookup/` directory
- [ ] Created `<language>/llm-work/` directory (this file's location)
- [ ] Created `<language>/docs/` directory (optional, for final documentation)

### OTLP Logs Export (Test First)
- [ ] Implemented provider initialization
- [ ] Implemented OTLP HTTP exporter for logs
- [ ] Configured endpoint: `http://host.docker.internal/v1/logs`
- [ ] Configured header: `Host: otel.localhost`
- [ ] **If HTTP client issue:** Implemented custom transport/client
- [ ] Created simple test that emits one log
- [ ] Ran test
- [ ] Verified log appears in Loki: `query-loki.sh '<service-name>'`

**Notes on OTLP setup:**
```
[Document any issues encountered and solutions]
```

---

## Phase 2: Metrics Export

### Metric Instruments Creation
- [ ] Created meter
- [ ] Created `sovdev.operations.total` (Counter, Int64)
- [ ] Created `sovdev.errors.total` (Counter, Int64)
- [ ] Created `sovdev.operation.duration` (Histogram, Float64)
  - [ ] Specified description: "Duration of operations in milliseconds"
  - [ ] **CRITICAL:** Specified unit: `"ms"` or equivalent
- [ ] Created `sovdev.operations.active` (UpDownCounter, Int64)
- [ ] Set temporality: CUMULATIVE (for Prometheus compatibility)

### Metric Attributes Configuration
- [ ] **CRITICAL:** Used underscore notation for all attributes:
  - [ ] `peer_service` (NOT peer.service)
  - [ ] `log_type` (NOT function.name or log.type)
  - [ ] `log_level` (NOT log.level)
  - [ ] `service_name`
  - [ ] `service_version`

### Duration Recording
- [ ] **CRITICAL:** Duration recorded in **milliseconds** (NOT seconds)
- [ ] Verified conversion from language's native time unit to milliseconds

**Duration implementation:**
```
[Document how duration is calculated and recorded in milliseconds]
```

### Metrics Export Test
- [ ] Ran test that generates metrics
- [ ] Verified metrics appear in Prometheus: `query-prometheus.sh 'sovdev_operations_total{service_name=~".*<language>.*"}'`
- [ ] **CRITICAL:** Verified metric labels match TypeScript exactly

**Metric label verification:**
```
[Paste output showing peer_service, log_type, log_level with underscores]
```

---

## Phase 3: Full Implementation

### All 8 API Functions
- [ ] `SovdevInitialize(serviceName, serviceVersion, peerServices)`
- [ ] `SovdevLog(level, functionName, message, peerService, input, response, error, traceId)`
- [ ] `SovdevLogJobStatus(level, functionName, jobName, status, peerService, metadata, traceId)`
- [ ] `SovdevLogJobProgress(level, functionName, itemName, current, total, peerService, metadata, traceId)`
- [ ] `SovdevGenerateTraceID()`
- [ ] `SovdevFlush()`
- [ ] `CreatePeerServices(mappings)`
- [ ] `SOVDEV_LOGLEVELS` (DEBUG, INFO, WARN, ERROR, FATAL)

### File Logging
- [ ] Implemented file output (using appropriate library)
- [ ] Implemented log rotation:
  - [ ] Main log: 50 MB max, 5 files
  - [ ] Error log: 10 MB max, 3 files
- [ ] Tested file logging works

### Console Logging
- [ ] Implemented console output
- [ ] Respects `LOG_TO_CONSOLE` environment variable

### Configuration
- [ ] Reads environment variables:
  - [ ] `OTEL_SERVICE_NAME`
  - [ ] `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`
  - [ ] `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT`
  - [ ] `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`
  - [ ] `OTEL_EXPORTER_OTLP_HEADERS`
  - [ ] `LOG_TO_CONSOLE`
  - [ ] `LOG_TO_FILE`
  - [ ] `LOG_FILE_PATH`
  - [ ] `ERROR_LOG_PATH`

---

## Phase 4: E2E Test Implementation

### Test Program
- [ ] Created `<language>/test/e2e/company-lookup/main.<ext>`
- [ ] Implements company lookup test (matches specification)
- [ ] Uses all 8 API functions
- [ ] Tests:
  - [ ] Transaction correlation (trace IDs)
  - [ ] Job tracking (batch operations)
  - [ ] Error handling
  - [ ] All log levels

### Test Script
- [ ] Created `<language>/test/e2e/company-lookup/run-test.sh`
- [ ] Script cleans logs directory
- [ ] Script builds/compiles if needed
- [ ] Script runs test program
- [ ] Script outputs success/failure

### Environment Configuration
- [ ] Created `<language>/test/e2e/company-lookup/.env`
- [ ] Configured all required environment variables
- [ ] Verified OTLP endpoints use `host.docker.internal`
- [ ] Verified `Host: otel.localhost` header configured

---

## Phase 5: Validation

### File Log Validation
- [ ] Ran test: `<language>/test/e2e/company-lookup/run-test.sh`
- [ ] Ran validation: `validate-log-format.sh <language>/test/e2e/company-lookup/logs/dev.log`
- [ ] **Result:** ✅ PASS / ❌ FAIL
- [ ] If failed: Fixed issues and re-validated

**Validation output:**
```
[Paste validation output]
```

### OTLP Validation
- [ ] Ran full validation: `run-full-validation.sh <language>`
- [ ] Verified logs in Loki
- [ ] Verified metrics in Prometheus
- [ ] Verified traces in Tempo (if applicable)

**Query results:**
```
[Paste query outputs]
```

### Grafana Dashboard Validation (MOST CRITICAL)

**Step 1: Run both tests**
- [ ] Ran TypeScript test: `run-full-validation.sh typescript`
- [ ] Ran language test: `run-full-validation.sh <language>`

**Step 2: Open Grafana**
- [ ] Opened http://grafana.localhost
- [ ] Navigated to Structured Logging Testing Dashboard

**Step 3: Verify ALL panels show data for BOTH languages**
- [ ] Panel 1: Total Operations
  - [ ] TypeScript shows "Last" value
  - [ ] [LANGUAGE] shows "Last" value
  - [ ] TypeScript shows "Max" value
  - [ ] [LANGUAGE] shows "Max" value
- [ ] Panel 2: Error Rate
  - [ ] TypeScript shows "Last %" value
  - [ ] [LANGUAGE] shows "Last %" value
  - [ ] TypeScript shows "Max %" value
  - [ ] [LANGUAGE] shows "Max %" value
- [ ] Panel 3: Average Operation Duration
  - [ ] TypeScript shows entries for all peer services
  - [ ] [LANGUAGE] shows entries for all peer services
  - [ ] Values are in milliseconds (e.g., 0.538 ms, NOT 0.000538)

**Grafana validation result:**
```
✅ ALL panels show data for both languages
❌ Missing data in: [specify which panels/languages]

[Paste screenshot or describe what's shown]
```

### Metric Label Comparison
- [ ] Queried TypeScript metrics: `query-prometheus.sh 'sovdev_operations_total{service_name=~".*typescript.*"}' > ts.txt`
- [ ] Queried language metrics: `query-prometheus.sh 'sovdev_operations_total{service_name=~".*<language>.*"}' > lang.txt`
- [ ] Compared: `diff ts.txt lang.txt`
- [ ] **Result:** Labels IDENTICAL ✅ / Labels DIFFERENT ❌

**Label comparison result:**
```
[Paste diff output or confirm identical labels]

Expected labels:
✅ peer_service (underscore)
✅ log_type (underscore)
✅ log_level (underscore)
✅ service_name
✅ service_version
```

---

## Phase 6: Documentation

### SDK Comparison Document
- [ ] Completed `<language>/llm-work/otel-sdk-comparison.md`
- [ ] Documented all differences from TypeScript
- [ ] Documented all workarounds implemented
- [ ] Included code examples for each workaround

### Known Issues Documented
- [ ] Listed all issues encountered
- [ ] For each issue: symptom, cause, solution
- [ ] Referenced code locations

### README
- [ ] Created/updated `<language>/README.md`
- [ ] Documented how to run tests
- [ ] Documented dependencies
- [ ] Documented any language-specific setup

---

## Phase 7: Final Checks

### Code Quality
- [ ] Code follows language conventions
- [ ] No hardcoded values (uses environment variables)
- [ ] Error handling implemented
- [ ] Comments explain workarounds

### Cleanup
- [ ] Removed debug/test code
- [ ] Removed unused dependencies
- [ ] Cleaned up commented code

### Cross-Language Verification
- [ ] Compared output with TypeScript implementation
- [ ] Verified same number of log entries
- [ ] Verified same metrics count
- [ ] Verified same trace structure

---

## Completion Criteria

**DO NOT claim implementation complete until ALL of these are checked:**

- [ ] ✅ Language toolchain installed and verified
- [ ] ✅ OTEL SDK verified (Stable/Beta, supports logs/metrics/traces)
- [ ] ✅ TypeScript reference studied and understood
- [ ] ✅ Target language SDK studied and understood
- [ ] ✅ SDK comparison document created and complete
- [ ] ✅ All 8 API functions implemented
- [ ] ✅ File logging works with rotation
- [ ] ✅ OTLP export works (logs, metrics, traces)
- [ ] ✅ E2E test implemented and passes
- [ ] ✅ File log validation PASSES
- [ ] ✅ OTLP validation PASSES
- [ ] ✅ Grafana dashboard shows data in ALL 3 panels for this language
- [ ] ✅ Metric labels IDENTICAL to TypeScript (underscores, correct names)
- [ ] ✅ Duration values in milliseconds
- [ ] ✅ Histogram has unit specification
- [ ] ✅ Documentation complete

**Only when ALL items above are checked can you claim: "Implementation COMPLETE ✅"**

---

## Issues Encountered

**Document any issues here for future reference:**

### Issue 1: [Title]
- **When:** [Phase/step where encountered]
- **Symptom:** [What happened]
- **Cause:** [Why it happened]
- **Solution:** [How you fixed it]
- **Code:** [Reference to fix location]

### Issue 2: [Title]
[Repeat pattern]

---

## LLM Work Notes

**Use this section for any temporary notes, code snippets, or reminders:**

```
[Your working notes here]
```

---

**Checklist Status:** In Progress / Complete
**Language:** [LANGUAGE]
**Started:** [DATE]
**Completed:** [DATE]
