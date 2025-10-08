# Sovdev Logger Verification Tools

This directory contains **language-agnostic verification tools** that enable automated testing and validation of sovdev-logger implementations.

## Purpose

These tools abstract away the complexity of:
- Running code in the correct environment (devcontainer vs host)
- Knowing where tools are installed (kubectl=host, language runtimes=devcontainer)
- Understanding language-specific test commands
- Querying monitoring backends (Loki, Prometheus, Tempo)

**Key benefit:** One simple command works for ALL languages.

---

## Prerequisites

Before using these tools, ensure:

1. **DevContainer Toolbox is running:**
   ```bash
   docker ps | grep devcontainer-toolbox
   # Should show: devcontainer-toolbox
   ```

2. **Language implementation follows standard structure** (see `specification/06-test-scenarios.md`):
   ```
   {language}/
   └── test/e2e/company-lookup/
       ├── run-test.sh    # Entry point (REQUIRED)
       ├── company-lookup.*
       ├── .env
       └── logs/
   ```

3. **Monitoring stack is running** (for Loki/Prometheus/Tempo queries):
   ```bash
   kubectl get pods -n monitoring
   ```

---

## Available Tools

### 1. `run-company-lookup.sh`

**Purpose:** Run company-lookup example test (quick application test without backend queries).

**What it does:**
- Runs `test/e2e/company-lookup/run-test.sh` inside devcontainer
- Executes the application and sends telemetry to OTLP endpoints
- **Does NOT** query backends (Loki/Prometheus/Tempo)
- **Fast** - completes in seconds

**Usage:**
```bash
./run-company-lookup.sh <language>
```

**Examples:**
```bash
./run-company-lookup.sh python
./run-company-lookup.sh typescript
./run-company-lookup.sh go
```

**When to use:**
- ✅ Quick smoke test during development
- ✅ Verify code compiles/runs without errors
- ✅ Test OTLP endpoint connectivity
- ❌ NOT for complete verification (use run-company-lookup-validate.sh instead)

**Exit codes:**
- `0` = Test passed
- `1` = Test failed
- `2` = Usage error
- `3` = Devcontainer not running
- `4` = Test script not found

---

### 2. `run-company-lookup-validate.sh`

**Purpose:** Run complete E2E test with backend verification (full verification suite).

**What it does:**
- Runs `test/e2e-test.sh` on the HOST (needs kubectl)
- Installs the library (in devcontainer)
- Executes the application (in devcontainer)
- Waits for telemetry export
- **Queries Loki** to verify logs arrived
- **Queries Prometheus** to verify metrics exist
- **Queries Tempo** to verify traces exist
- **Slower** - completes in ~30 seconds (includes 15s wait time)

**Usage:**
```bash
./run-company-lookup-validate.sh <language>
```

**Examples:**
```bash
./run-company-lookup-validate.sh python
./run-company-lookup-validate.sh typescript
```

**When to use:**
- ✅ Complete verification before release
- ✅ Verify entire telemetry pipeline works
- ✅ Confirm data reaches all backends
- ✅ Official verification for implementation approval

**Requirements:**
- Devcontainer must be running
- Kubernetes cluster with monitoring stack deployed
- kubectl configured and working on host

**Exit codes:**
- `0` = All tests passed
- `1` = Tests failed
- `2` = Usage error
- `3` = Devcontainer not running
- `4` = Test script not found

**Output:**
```
ℹ️  Starting complete E2E test for python

✅ Devcontainer 'devcontainer-toolbox' is running
✅ E2E test script found

═════════════════════════════════════════════════════════════════
  Test: Complete E2E with Backend Verification
  Language: python

  This will:
    1. Install the library (in devcontainer)
    2. Run the application (in devcontainer)
    3. Wait for telemetry export
    4. Query Loki (logs) - uses kubectl on host
    5. Query Prometheus (metrics) - uses kubectl on host
    6. Query Tempo (traces) - uses kubectl on host
═════════════════════════════════════════════════════════════════

🧪 E2E Test: sovdev-logger Python Library
✅ Prerequisites check passed
✅ Library installed successfully
✅ Example executed successfully
✅ Wait completed
✅ Service found in Loki
✅ Found 16 log entries in Loki
✅ Found 5 metric series in Prometheus
✅ Service found in Tempo
✅ Found 16 traces in Tempo

Total Tests: 10
Passed: 10
Failed: 0

✅ E2E test PASSED for python
✅ All backends verified (Loki, Prometheus, Tempo)
```

---

### 3. `query-loki.sh`

**Purpose:** Query Loki backend for logs from a specific service.

**What it does:**
- Queries Loki using kubectl on the HOST
- Supports both human-readable and JSON output modes
- Filters by service name
- Configurable time range and result limit

**Usage:**
```bash
./query-loki.sh <service-name> [options]
```

**Options:**
- `--json` - Output raw JSON for parsing/verification
- `--limit N` - Limit results to N entries (default: 10)
- `--time-range R` - Time range: 1h, 30m, 24h, etc. (default: 1h)
- `--help` - Show usage information

**Examples:**
```bash
# Quick check (human-readable)
./query-loki.sh sovdev-test-company-lookup-python

# Get JSON for field verification
./query-loki.sh sovdev-test-company-lookup-python --json | jq '.data.result[0].stream.timestamp'

# Query last 30 minutes, limit to 5 entries
./query-loki.sh sovdev-test-company-lookup-python --time-range 30m --limit 5

# Save evidence for verification report
./query-loki.sh sovdev-test-company-lookup-python --json > evidence/loki-output.json
```

**Human-readable output:**
```
🔍 Querying Loki for service: sovdev-test-company-lookup-python
   Time range: 1h, Limit: 10

📡 Querying Loki...
✅ Service 'sovdev-test-company-lookup-python' found in Loki
✅ Found 16 log entries

📋 Sample log entry:
   timestamp:    2025-10-07T13:28:38.582959+00:00
   severity:     INFO
   message:      Processing 916201478 (4/4)...
   (23 total fields in stream)

✅ Loki query successful

💡 Tip: Use --json flag to get full JSON output for verification
```

**When to use:**
- ✅ Verify logs reached Loki after running tests
- ✅ Debug missing logs or incorrect fields
- ✅ Extract log data for compliance verification
- ✅ Compose with `run-company-lookup.sh` for quick end-to-end check

---

### 4. `query-prometheus.sh`

**Purpose:** Query Prometheus backend for metrics from a specific service.

**What it does:**
- Queries Prometheus using kubectl on the HOST
- Supports both human-readable and JSON output modes
- Filters metrics by service name
- Calculates total operations across all series

**Usage:**
```bash
./query-prometheus.sh <service-name> [options]
```

**Options:**
- `--json` - Output raw JSON for parsing/verification
- `--metric NAME` - Specific metric to query (default: sovdev_operations_total)
- `--help` - Show usage information

**Examples:**
```bash
# Quick check (human-readable)
./query-prometheus.sh sovdev-test-company-lookup-python

# Get JSON for metric verification
./query-prometheus.sh sovdev-test-company-lookup-python --json | jq '.data.result[0].metric'

# Query specific metric
./query-prometheus.sh sovdev-test-company-lookup-python --metric sovdev_operations_total

# Save evidence
./query-prometheus.sh sovdev-test-company-lookup-python --json > evidence/prometheus-output.json
```

**Human-readable output:**
```
🔍 Querying Prometheus for service: sovdev-test-company-lookup-python
   Metric: sovdev_operations_total

📡 Querying Prometheus...
✅ Found 5 metric series for 'sovdev-test-company-lookup-python'
✅ Total operations: 16

📋 Sample metric labels:
   log_level:    ERROR
   log_type:     transaction
   peer_service: SYS1234567
   (7 total labels)

✅ Prometheus query successful

💡 Tip: Use --json flag to get full JSON output for verification
```

**When to use:**
- ✅ Verify metrics reached Prometheus after running tests
- ✅ Check operation counters are incrementing correctly
- ✅ Debug missing metrics or incorrect labels
- ✅ Validate metric cardinality (number of series)

---

### 5. `query-tempo.sh`

**Purpose:** Query Tempo backend for traces from a specific service.

**What it does:**
- Queries Tempo using kubectl on the HOST
- Supports both human-readable and JSON output modes
- Filters traces by service name
- Shows trace IDs and span counts

**Usage:**
```bash
./query-tempo.sh <service-name> [options]
```

**Options:**
- `--json` - Output raw JSON for parsing/verification
- `--limit N` - Limit results to N traces (default: 10)
- `--help` - Show usage information

**Examples:**
```bash
# Quick check (human-readable)
./query-tempo.sh sovdev-test-company-lookup-python

# Get JSON for trace verification
./query-tempo.sh sovdev-test-company-lookup-python --json | jq '.traces[0].traceID'

# Limit to 5 traces
./query-tempo.sh sovdev-test-company-lookup-python --limit 5

# Save evidence
./query-tempo.sh sovdev-test-company-lookup-python --json > evidence/tempo-output.json
```

**Human-readable output:**
```
🔍 Querying Tempo for service: sovdev-test-company-lookup-python
   Limit: 10

📡 Querying Tempo...
✅ Service 'sovdev-test-company-lookup-python' found in Tempo
✅ Found 10 traces

📋 Sample trace:
   traceID:      575e9a7266d947af...
   service:      sovdev-test-company-lookup-python
   operation:    lookupCompany
   timestamp:    2025-10-07 15:28:38

✅ Tempo query successful

💡 Tip: Use --json flag to get full JSON output for verification
```

**When to use:**
- ✅ Verify traces reached Tempo after running tests
- ✅ Check distributed tracing is working
- ✅ Debug missing traces or incorrect spans
- ✅ Validate trace context propagation

---

### 6. `validate-log-format.sh`

**Purpose:** Validate log file format against the sovdev-logger specification.

**What it does:**
- Validates JSON log files (NDJSON format) using JSON Schema
- Checks schema compliance (required fields, correct types, formats)
- Verifies custom business rules (stack trace limits, exception types)
- Supports both flat dotted notation (TypeScript) and nested notation (Python)
- Can run from HOST (connects to devcontainer) or inside DEVCONTAINER

**Usage:**
```bash
./validate-log-format.sh <log-file-path> [options]
```

**Options:**
- `--json` - Output JSON format for automation
- `--error-log` - Validate as error.log (ERROR logs only)
- `--help` - Show usage information

**Examples:**
```bash
# Validate dev.log (human-readable)
./validate-log-format.sh python/test/e2e/company-lookup/logs/dev.log

# Validate error.log with JSON output
./validate-log-format.sh python/test/e2e/company-lookup/logs/error.log --error-log --json

# TypeScript logs
./validate-log-format.sh typescript/test/e2e/company-lookup/logs/dev.log
```

**Human-readable output:**
```
🔍 Validating log file: /workspace/typescript/test/e2e/company-lookup/logs/dev.log

ℹ️  Validating 542 log entries...
✅ All 542 log entries match schema
✅ Found 236 unique trace IDs

✅ VALIDATION PASSED

Total logs: 542
Severities: {'UNKNOWN': 542}
Log types: {'transaction': 338, 'job.status': 68, 'job.progress': 136}
Errors: 0
Warnings: 0
```

**Validation checks:**
- ✅ JSON Schema compliance (all required fields, correct types)
- ✅ UUID v4 format for eventId, traceId, sessionId
- ✅ ISO 8601 timestamp format
- ✅ Exception type is "Error" (not "Exception", "Throwable", etc.)
- ✅ Stack traces limited to 350 characters
- ✅ Error logs contain exception fields

**When to use:**
- ✅ Verify log file format during development
- ✅ Validate logs before committing changes
- ✅ Check logs as part of test suite
- ✅ Verify cross-language consistency

**Exit codes:**
- `0` = Validation passed
- `1` = Validation failed
- `2` = Usage error (missing parameter)
- `3` = Devcontainer not running (when run from host)
- `4` = Log file not found

---

## Composable Workflows

These tools can be combined for powerful verification workflows:

### Example 1: Quick end-to-end verification
```bash
# Run test, then verify all backends
./run-company-lookup.sh python && \
  ./query-loki.sh sovdev-test-company-lookup-python && \
  ./query-prometheus.sh sovdev-test-company-lookup-python && \
  ./query-tempo.sh sovdev-test-company-lookup-python
```

### Example 2: Collect evidence for verification report
```bash
# Run test and save all output
./run-company-lookup.sh python

# Collect evidence from all backends
mkdir -p evidence
./query-loki.sh sovdev-test-company-lookup-python --json > evidence/loki.json
./query-prometheus.sh sovdev-test-company-lookup-python --json > evidence/prometheus.json
./query-tempo.sh sovdev-test-company-lookup-python --json > evidence/tempo.json
```

### Example 3: Field verification
```bash
# Extract specific fields for compliance checking
./query-loki.sh sovdev-test-company-lookup-python --json | \
  jq '.data.result[0].stream | {timestamp, severity_text, service_name, session_id}'
```

### Example 4: Complete validation workflow
```bash
# Run test, validate log files, query backends
./run-company-lookup.sh python && \
  ./validate-log-format.sh python/test/e2e/company-lookup/logs/dev.log && \
  ./validate-log-format.sh python/test/e2e/company-lookup/logs/error.log --error-log && \
  ./query-loki.sh sovdev-test-company-lookup-python
```

### Example 5: Cross-language consistency check
```bash
# Validate TypeScript and Python produce same format
mkdir -p validation-results
./validate-log-format.sh typescript/test/e2e/company-lookup/logs/dev.log --json > validation-results/typescript.json
./validate-log-format.sh python/test/e2e/company-lookup/logs/dev.log --json > validation-results/python.json

# Compare results
diff validation-results/typescript.json validation-results/python.json
```

---

## Future Tools (Planned)

### `verify-devcontainer.sh`

Pre-flight check that verifies environment is ready.

**Usage:**
```bash
./verify-devcontainer.sh
```

**Checks:**
- ✅ Devcontainer running
- ✅ Workspace accessible
- ✅ OTLP endpoints reachable
- ✅ Language runtimes available
- ✅ Monitoring stack responding

### `verify-otlp-output.sh`

Combined workflow: run test + query Loki + verify fields.

**Usage:**
```bash
./verify-otlp-output.sh <language>
```

**Workflow:**
1. Run E2E test
2. Wait for logs to reach Loki
3. Query Loki for recent logs
4. Verify all required OTLP fields present
5. Return structured verification report

---

## Design Principles

### 1. Convention Over Configuration
- Tools rely on standardized paths (`test/e2e/company-lookup/`)
- No need to specify full paths or commands
- Language-specific details hidden in `run-test.sh`

### 2. Language Agnostic
- Same tool command works for all languages
- Tool doesn't need to know about `python3` vs `npx tsx` vs `go run`
- Each language's `run-test.sh` handles execution

### 3. Clear Error Messages
- Tell user exactly what's wrong
- Provide guidance on how to fix
- Reference relevant documentation

### 4. Exit Code Standards
- `0` = Success
- `1` = Test/verification failure
- `2` = Usage error (wrong parameters)
- `3+` = Environment issues (devcontainer, missing files, etc.)

### 5. Self-Documenting
- Script name describes what it does
- Help text with `-h` or `--help`
- Examples in output

### 6. Composable
- Simple tools that do one thing well
- Can be combined for complex workflows
- Can be called from CI/CD pipelines

---

## Integration with Verification Templates

These tools are referenced in verification templates to simplify verification instructions.

**Before (without tools):**
```bash
# Quick test
docker exec devcontainer-toolbox bash -c "cd /workspace/python/test/e2e/company-lookup && ./run-test.sh"

# Complete E2E test
cd python && ./test/e2e-test.sh
```

**After (with tools):**
```bash
# Quick test (company-lookup example)
./specification/tools/run-company-lookup.sh python

# Complete E2E test (with backend queries)
./specification/tools/run-company-lookup-validate.sh python
```

**Choosing the right tool:**
- Development/quick checks → `run-company-lookup.sh` (fast, no kubectl needed)
- Official verification → `run-company-lookup-validate.sh` (complete, queries all backends)

---

## Using Tools in CI/CD

These tools are designed to work in automated environments:

```yaml
# .github/workflows/verify-python.yml
name: Verify Python Implementation

on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start devcontainer
        run: docker start devcontainer-toolbox || echo "Container already running"
      - name: Run company-lookup example
        run: ./specification/tools/run-company-lookup.sh python
      - name: Query Loki
        run: ./specification/tools/query-loki.sh sovdev-test-company-lookup-python
      - name: Query Prometheus
        run: ./specification/tools/query-prometheus.sh sovdev-test-company-lookup-python
      - name: Query Tempo
        run: ./specification/tools/query-tempo.sh sovdev-test-company-lookup-python
```

---

## Troubleshooting

### Error: "Devcontainer not running"

**Solution:**
```bash
docker ps | grep devcontainer-toolbox
# If not running:
docker start devcontainer-toolbox
```

### Error: "Test script not found"

**Solution:**
Verify the language implementation has the required structure:
```bash
ls -la {language}/test/e2e/company-lookup/
# Should show: run-test.sh
```

See `specification/06-test-scenarios.md` for required structure.

### Error: "kubectl: command not found"

**Cause:** `query-loki.sh` and similar tools run kubectl on the HOST, not in devcontainer.

**Solution:** Install kubectl on your host machine.

---

## Development Guidelines

When creating new tools:

1. **Start with one language** - Test thoroughly with Python/TypeScript
2. **Verify language-agnostic** - Must work identically for all languages
3. **Clear error messages** - Tell user exactly what's wrong and how to fix
4. **Document parameters** - Usage, examples, output format
5. **Return structured output** - JSON when possible for parsing
6. **Handle edge cases** - Container not running, files missing, timeouts
7. **Update this README** - Add tool to "Available Tools" section

---

## Status

**Implemented tools:**
- ✅ `run-company-lookup.sh` - Quick smoke test (runs app, sends to OTLP)
- ✅ `run-company-lookup-validate.sh` - Complete backend verification (includes all query checks)
- ✅ `query-loki.sh` - Standalone Loki query tool (dual-mode output)
- ✅ `query-prometheus.sh` - Standalone Prometheus query tool (dual-mode output)
- ✅ `query-tempo.sh` - Standalone Tempo query tool (dual-mode output)
- ✅ `validate-log-format.sh` - Log file format validator using JSON Schema

**Planned tools:**
- ⏳ `verify-devcontainer.sh` - Pre-flight environment checks
- ⏳ `verify-otlp-output.sh` - Combined workflow: test + query + field verification

**Notes:**
- `run-company-lookup-validate.sh` orchestrates a complete test (includes internal backend queries)
- The standalone query tools (`query-*.sh`) are useful for:
  - Ad-hoc debugging during development
  - Field-level verification in reports
  - CI/CD pipeline integration
  - Evidence collection for compliance

---

**Last Updated:** 2025-10-07
**Maintainer:** Claude Code / Terje Christensen
