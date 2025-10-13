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
| [**run-company-lookup-validate.sh**](run-company-lookup-validate.sh) | Complete E2E test with backend queries | `./run-company-lookup-validate.sh python` | `./in-devcontainer.sh run-company-lookup-validate python` | Devcontainer |
| [**run-full-validation.sh**](run-full-validation.sh) | Full E2E validation - all backends + Grafana | `./run-full-validation.sh python` | `./in-devcontainer.sh run-full-validation python` | Devcontainer |
| [**run-full-validation-host.sh**](run-full-validation-host.sh) | Legacy wrapper - runs validation from host | N/A | `./run-full-validation-host.sh python` | Host wrapper (deprecated) |
| [**run-grafana-validation.sh**](run-grafana-validation.sh) | Validate Grafana datasource queries | `./run-grafana-validation.sh <service> <logfile>` | `./in-devcontainer.sh run-grafana-validation <service> <logfile>` | Devcontainer |
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
./in-devcontainer.sh run-company-lookup-validate python          # Complete verification
./in-devcontainer.sh loki sovdev-test-company-lookup-python      # Query Loki (using alias)
./in-devcontainer.sh validate-logs python/test/logs/dev.log      # Validate logs (using alias)

# Inside devcontainer (if you're already in there)
./run-company-lookup-validate.sh python
./query-loki.sh sovdev-test-company-lookup-python
./validate-log-format.sh python/test/logs/dev.log

# Common workflow from host
./in-devcontainer.sh run-company-lookup python && \
./in-devcontainer.sh loki sovdev-test-company-lookup-python --json
```

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


**Last Updated:** 2025-10-07
**Maintainer:** Claude Code / Terje Christensen
