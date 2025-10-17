# Sovdev Logger Verification Tools

This directory contains **language-agnostic verification tools** that enable automated testing and validation of sovdev-logger implementations.

## Purpose

These tools abstract away the complexity of:
- Testing thet the sovdev-logger has the expected output when developing and maintaining the code.
- Running code in the correct environment (devcontainer vs host)
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

## Quick Reference

**Core Principle:** All scripts run INSIDE the devcontainer (which has kubectl, language runtimes, and all tools).

Complete table of all verification tools:

| Script | Purpose | Inside Container | From Host | Where It Runs |
|--------|---------|------------------|-----------|---------------|
| [**run-company-lookup.sh**](run-company-lookup.sh) | Quick smoke test - run app and send to OTLP | `./run-company-lookup.sh python` | `./in-devcontainer.sh run-company-lookup python` | Devcontainer |
| [**run-full-validation.sh**](run-full-validation.sh) | **RECOMMENDED** - Complete E2E validation | `./run-full-validation.sh python` | `./in-devcontainer.sh run-full-validation python` | Devcontainer |
| [**run-grafana-validation.sh**](run-grafana-validation.sh) | Validate Grafana datasource queries only | `./run-grafana-validation.sh <service> <logfile>` | `./in-devcontainer.sh run-grafana-validation <service> <logfile>` | Devcontainer |
| [**query-loki.sh**](query-loki.sh) | Query Loki directly for service logs | `./query-loki.sh sovdev-test-company-lookup-python` | `./in-devcontainer.sh query-loki sovdev-test-company-lookup-python` | Devcontainer |
| [**query-prometheus.sh**](query-prometheus.sh) | Query Prometheus directly for service metrics | `./query-prometheus.sh sovdev-test-company-lookup-python` | `./in-devcontainer.sh query-prometheus sovdev-test-company-lookup-python` | Devcontainer |
| [**query-tempo.sh**](query-tempo.sh) | Query Tempo directly for service traces | `./query-tempo.sh sovdev-test-company-lookup-python` | `./in-devcontainer.sh query-tempo sovdev-test-company-lookup-python` | Devcontainer |
| [**query-grafana.sh**](query-grafana.sh) | Check Grafana datasource configuration | `./query-grafana.sh` | `./in-devcontainer.sh query-grafana` | Devcontainer |
| [**query-grafana-loki.sh**](query-grafana-loki.sh) | Query Loki THROUGH Grafana proxy | `./query-grafana-loki.sh sovdev-test-company-lookup-python` | `./in-devcontainer.sh query-grafana-loki sovdev-test-company-lookup-python` | Devcontainer |
| [**query-grafana-prometheus.sh**](query-grafana-prometheus.sh) | Query Prometheus THROUGH Grafana proxy | `./query-grafana-prometheus.sh sovdev-test-company-lookup-python` | `./in-devcontainer.sh query-grafana-prometheus sovdev-test-company-lookup-python` | Devcontainer |
| [**query-grafana-tempo.sh**](query-grafana-tempo.sh) | Query Tempo THROUGH Grafana proxy | `./query-grafana-tempo.sh sovdev-test-company-lookup-python` | `./in-devcontainer.sh query-grafana-tempo sovdev-test-company-lookup-python` | Devcontainer |
| [**validate-log-format.sh**](validate-log-format.sh) | Validate log file format against schema | `./validate-log-format.sh python/test/logs/dev.log` | `./in-devcontainer.sh validate-log-format python/test/logs/dev.log` | Devcontainer |
| [**in-devcontainer.sh**](in-devcontainer.sh) | Universal wrapper to run scripts from host | N/A | `./in-devcontainer.sh <script> [args]` | Host → Devcontainer |

**Aliases (shortcuts with in-devcontainer.sh):**
- `loki` → `query-loki.sh`
- `prometheus` / `prom` → `query-prometheus.sh`
- `tempo` → `query-tempo.sh`
- `grafana` → `query-grafana.sh`
- `validate` → `run-full-validation.sh`
- `validate-logs` → `validate-log-format.sh`
- `company-lookup` → `run-company-lookup.sh`

**Usage Examples:**

```bash
# From host machine (most common)
./in-devcontainer.sh validate python                         # Complete verification (alias)
./in-devcontainer.sh run-full-validation python              # Complete verification
./in-devcontainer.sh loki sovdev-test-company-lookup-python  # Query Loki (using alias)
./in-devcontainer.sh validate-logs python/test/logs/dev.log  # Validate logs (using alias)

# Inside devcontainer (if you're already in there)
./run-full-validation.sh python
./query-loki.sh sovdev-test-company-lookup-python
./validate-log-format.sh python/test/logs/dev.log

# Common workflow from host
./in-devcontainer.sh run-company-lookup python && \
./in-devcontainer.sh loki sovdev-test-company-lookup-python --json
```

---

## Validation Scripts Comparison

**Which script should I use?** This table shows what each validation and query script does:

### Validation Runner Scripts

| Script | Runs App | File Log Validation | Loki Schema validation | Loki compared to log file validation | Prometheus Schema validation | Prometheus compared to log file validation | Tempo Schema validation | Tempo compared to log file validation | Grafana Proxy | Use Case |
|--------|----------|---------------------|------------------------|--------------------------------------|------------------------------|--------------------------------------------| ------------------------|---------------------------------------|---------------|----------|
| **run-company-lookup.sh** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Quick smoke test - file logs only |
| **run-full-validation.sh** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **RECOMMENDED** - Complete E2E validation |
| **run-grafana-validation.sh** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Grafana proxy validation only (logs must exist) |

**Validation Script Purposes:**
- **run-company-lookup.sh**: Quick smoke test - runs app, validates file logs only (no backend queries)
- **run-full-validation.sh**: Complete validation - file logs + all backends (direct + Grafana proxy)
- **run-grafana-validation.sh**: Grafana-only validation - assumes logs exist, only tests Grafana datasource queries

### Query Scripts (Direct Backend Access)

| Script | Queries Loki | Queries Prometheus | Queries Tempo | Queries Grafana | Validates Schema | Compares to Log File | Output Format | Use Case |
|--------|--------------|-------------------|---------------|-----------------|------------------|----------------------|---------------|----------|
| **query-loki.sh** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | JSON/Text | Query Loki directly - returns raw response |
| **query-prometheus.sh** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | JSON/Text | Query Prometheus directly - returns raw response |
| **query-tempo.sh** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | JSON/Text | Query Tempo directly - returns raw response |
| **query-grafana.sh** | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | JSON/Text | Check Grafana datasource config |
| **query-grafana-loki.sh** | ✅ via Grafana | ❌ | ❌ | ✅ | ❌ | ❌ | JSON/Text | Query Loki through Grafana - returns raw response |
| **query-grafana-prometheus.sh** | ❌ | ✅ via Grafana | ❌ | ✅ | ❌ | ❌ | JSON/Text | Query Prometheus through Grafana - returns raw response |
| **query-grafana-tempo.sh** | ❌ | ❌ | ✅ via Grafana | ✅ | ❌ | ❌ | JSON/Text | Query Tempo through Grafana - returns raw response |

**Query Script Purposes:**
- **Query scripts DO NOT validate** - they only query backends and return raw responses
- **To validate responses**: Pipe query output to Python validators in `specification/tests/`
- **Direct query scripts** (query-loki.sh, query-prometheus.sh, query-tempo.sh): Query backends directly using kubectl port-forward
- **Grafana proxy scripts** (query-grafana-*.sh): Query backends through Grafana datasource proxy (tests Grafana integration)
- **query-grafana.sh**: Checks Grafana datasource configuration without querying data
- **Use `--json` flag** for JSON output (pipeable to validators or jq)

**Example - Manual Validation:**
```bash
# 1. Query Loki (returns raw response)
./query-loki.sh sovdev-test-company-lookup-python --json > /tmp/loki.json

# 2. Validate schema (manually pipe to validator)
python3 ../tests/validate-loki-response.py /tmp/loki.json

# 3. Compare to log file (manually pipe to validator)
python3 ../tests/validate-log-consistency.py logs/dev.log /tmp/loki.json
```

**Validation scripts DO this automatically** - `run-full-validation.sh` calls query scripts AND validators together

**Legend:**
- **Runs App**: Installs/builds library, runs company-lookup app to generate log files
- **File Log Validation**: Validates log files (dev.log, error.log) against log-entry-schema.json
- **Schema validation**: Validates backend response structure and required fields (timestamp, service_name, etc.)
- **compared to log file validation**: Compares backend response with log file content (same entries, same values, same counts)
- **Grafana Proxy**: Queries backends through Grafana datasource proxy (tests Grafana integration)

**Validation Layers:**
1. **Layer 1 - Schema Validation** ✅ Checks structure: Is JSON valid? Are required fields present? Are field types correct?
2. **Layer 2 - compared to log file validation** ✅ Checks values: Do backend response values match log file content? Same counts?
3. **Layer 3 - Business Logic** ⏳ Checks semantics: Is duration > 0? Are error rates acceptable? (future work)

**Recommendations:**

**For Development (Most Common - Use This!):**
```bash
# Use run-full-validation.sh or the "validate" alias
./in-devcontainer.sh validate typescript
# or
./in-devcontainer.sh run-full-validation typescript
```
- ✅ Validates file logs + all backends (Loki, Prometheus, Tempo)
- ✅ Schema + consistency validation (compares backend with log files)
- ✅ Validates Grafana datasource configuration
- ✅ Catches all implementation issues
- **This is what you want for complete validation**

**For Quick Smoke Test:**
```bash
# Use run-company-lookup.sh - just run the app
./in-devcontainer.sh run-company-lookup typescript
```
- No backend queries
- Just validates file log format
- Use when testing code changes locally (fast feedback)

**For Grafana-Only Testing:**
```bash
# Use run-grafana-validation.sh - validates Grafana queries only
./in-devcontainer.sh run-grafana-validation sovdev-test-company-lookup-typescript logs/dev.log
```
- Assumes app already ran and logs exist
- Only validates Grafana datasource queries
- Use when testing Grafana dashboard changes

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

## Integration with Validators

These tools orchestrate the complete validation pipeline by calling validators and querying backends:

```
┌─────────────────────────────────────────────────────────────────┐
│         Shell Script Tools (This Directory)                      │
│  run-full-validation.sh │ query-loki.sh │ ...                   │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ↓ (calls validators)
┌─────────────────────────────────────────────────────────────────┐
│              Python Validators (specification/tests/)            │
│  validate-log-format.py │ validate-loki-response.py │ ...       │
└─────────────┬───────────────────────────────────────────────────┘
              │
              ↓ (loads schemas)
┌─────────────────────────────────────────────────────────────────┐
│              JSON Schemas (specification/schemas/)               │
│  log-entry-schema.json │ loki-response-schema.json │ ...        │
└─────────────────────────────────────────────────────────────────┘
```

**Validation workflow:**

1. **Tools query backends**: `query-loki.sh`, `query-prometheus.sh`, `query-tempo.sh` fetch data from observability stack
2. **Tools call validators**: Response data piped to Python validators in `specification/tests/`
3. **Validators load schemas**: JSON schemas from `specification/schemas/` define validation rules
4. **Results reported**: Validators output pass/fail with detailed error messages

**Example: Full validation pipeline**
```bash
# 1. Tool runs test
./run-company-lookup.sh python

# 2. Tool queries Loki backend
./query-loki.sh sovdev-test-company-lookup-python --json > /tmp/loki-response.json

# 3. Tool calls validator (which loads schema)
python3 ../tests/validate-loki-response.py /tmp/loki-response.json

# All orchestrated by run-full-validation.sh
./run-full-validation.sh python  # Runs all steps automatically
```

**Related Documentation:**
- **Validators**: See `specification/tests/README.md` for Python validators that these tools call
- **Schemas**: See `specification/schemas/README.md` for JSON schemas that validators use

---


**Last Updated:** 2025-10-16
**Maintainer:** Claude Code / Terje Christensen
