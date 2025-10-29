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
- [ ] Created `sovdev_operations_total` (Counter, Int64)
- [ ] Created `sovdev_errors_total` (Counter, Int64)
- [ ] Created `sovdev_operation_duration` (Histogram, Float64)
  - [ ] Specified description: "Duration of operations in milliseconds"
  - [ ] **CRITICAL:** Specified unit: `"ms"` or equivalent
- [ ] Created `sovdev_operations_active` (UpDownCounter, Int64)
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
- [ ] `sovdev_initialize(service_name, service_version, peer_services)`
- [ ] `sovdev_log(level, function_name, message, peer_service, input_json, response_json, exception, trace_id)`
- [ ] `sovdev_log_job_status(level, function_name, job_name, status, peer_service, input_json, trace_id)`
- [ ] `sovdev_log_job_progress(level, function_name, item_id, current, total, peer_service, input_json, trace_id)`
- [ ] `sovdev_start_span(operation_name, attributes)`
- [ ] `sovdev_end_span(span, error)`
- [ ] `sovdev_flush()`
- [ ] `create_peer_services(definitions)`
- [ ] `SOVDEV_LOGLEVELS` (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)

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

**Test specification:** See [`08-testprogram-company-lookup.md`](./08-testprogram-company-lookup.md) for complete scenario description

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

**CRITICAL:** Follow the 8-step validation sequence exactly as documented in `specification/tools/README.md`.

**See:** **🔢 Validation Sequence (Step-by-Step)** section in `specification/tools/README.md`

This ensures:
- ⛔ Blocking points between steps (don't skip ahead)
- ✅ Progressive confidence building
- 🎯 Clear failure modes and remediation at each step

### Complete Validation Sequence

- [ ] **Read validation guide:** `specification/tools/README.md` → "🔢 Validation Sequence (Step-by-Step)"
- [ ] **Step 1:** Validate Log Files (INSTANT - 0 seconds) ⚡
  - Tool: `validate-log-format.sh`
  - Checks: JSON schema, field naming, log count (17), trace IDs (13)
  - Result: ✅ PASS / ❌ FAIL
- [ ] **Step 2:** Verify Logs in Loki (OTLP → Loki) 🔄
  - Tool: `query-loki.sh`
  - Checks: Logs reached Loki, log count matches
  - Result: ✅ PASS / ❌ FAIL
- [ ] **Step 3:** Verify Metrics in Prometheus (OTLP → Prometheus) 🔄
  - Tool: `query-prometheus.sh`
  - Checks: Metrics reached Prometheus, labels correct (peer_service, log_type, log_level)
  - Result: ✅ PASS / ❌ FAIL
- [ ] **Step 4:** Verify Traces in Tempo (OTLP → Tempo) 🔄
  - Tool: `query-tempo.sh`
  - Checks: Traces reached Tempo
  - Result: ✅ PASS / ❌ FAIL
- [ ] **Step 5:** Verify Grafana-Loki Connection (Grafana → Loki) 🔄
  - Tool: `query-grafana-loki.sh`
  - Checks: Grafana can query Loki
  - Result: ✅ PASS / ❌ FAIL
- [ ] **Step 6:** Verify Grafana-Prometheus Connection (Grafana → Prometheus) 🔄
  - Tool: `query-grafana-prometheus.sh`
  - Checks: Grafana can query Prometheus
  - Result: ✅ PASS / ❌ FAIL
- [ ] **Step 7:** Verify Grafana-Tempo Connection (Grafana → Tempo) 🔄
  - Tool: `query-grafana-tempo.sh`
  - Checks: Grafana can query Tempo
  - Result: ✅ PASS / ❌ FAIL
- [ ] **Step 8:** Verify Grafana Dashboard (Visual Verification) 👁️
  - Manual: Open http://grafana.localhost
  - Navigate to: Structured Logging Testing Dashboard
  - Verify: ALL 3 panels show data for this language
  - Result: ✅ PASS / ❌ FAIL

**⛔ DO NOT skip steps or claim complete until ALL 8 steps pass**

### Quick Validation (Automated Steps 1-7)

- [ ] Ran automated validation: `run-full-validation.sh <language>`
- [ ] All automated steps (1-7) passed: ✅ YES / ❌ NO

**Validation output:**
```
[Paste validation output from run-full-validation.sh]
```

### Step 8: Manual Grafana Dashboard Verification (MOST CRITICAL)

**This step CANNOT be automated - you MUST verify visually**

**Grafana dashboard checklist:**
- [ ] Opened http://grafana.localhost
- [ ] Navigated to Structured Logging Testing Dashboard
- [ ] **Panel 1: Total Operations**
  - [ ] TypeScript shows "Last" value
  - [ ] [LANGUAGE] shows "Last" value
  - [ ] TypeScript shows "Max" value
  - [ ] [LANGUAGE] shows "Max" value
- [ ] **Panel 2: Error Rate**
  - [ ] TypeScript shows "Last %" value
  - [ ] [LANGUAGE] shows "Last %" value
  - [ ] TypeScript shows "Max %" value
  - [ ] [LANGUAGE] shows "Max %" value
- [ ] **Panel 3: Average Operation Duration**
  - [ ] TypeScript shows entries for all peer services
  - [ ] [LANGUAGE] shows entries for all peer services
  - [ ] Values are in milliseconds (e.g., 0.538 ms, NOT 0.000538)

**Grafana validation result:**
```
✅ ALL panels show data for both languages
❌ Missing data in: [specify which panels/languages]

[Paste screenshot or describe what's shown]
```

### Metric Label Verification (Part of Step 3)

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

---

**Template Status:** ✅ v2.0.0 COMPLETE
**Last Updated:** 2025-10-27
**Part of:** sovdev-logger specification v1.1.0

**Version History:**
- v2.0.0 (2025-10-24): Restructured Phase 5 to explicitly reference 8-step validation sequence from tools/README.md with blocking points
- v1.0.0 (2025-10-15): Initial checklist template
