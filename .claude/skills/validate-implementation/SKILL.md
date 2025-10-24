---
description: "Run complete validation suite for sovdev-logger implementation. Validates file logs, OTLP backends, and Grafana dashboard. Use when validating any language implementation."
---

# Validate Implementation Skill

When the user asks to validate a sovdev-logger implementation, run the complete validation sequence defined in the specification.

## ⚠️ IMPORTANT: Directory Restrictions

**DO NOT access these directories:**
- ❌ `terchris/` - Personal working directory
- ❌ `topsecret/` - Contains credentials

**ONLY use these directories:**
- ✅ `specification/` - Validation tools and documentation
- ✅ `typescript/` - Reference for comparison
- ✅ `{language}/` - Implementation being validated

## Validation Workflow

**See `specification/10-development-loop.md` for detailed validation workflow.**

**Key Principle:** Validate log files FIRST (instant), then OTLP SECOND (slow).

## Required Validation Sequence

### Step 1: Validate Log Files FIRST (0 seconds)
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log"
```

**Expected:** `✅ PASS` with 17 log entries, 13 unique trace IDs

**What it checks:** JSON schema, field naming (snake_case), log count, trace correlation

**If fails:** Fix issues, rebuild, run test, validate again. **DO NOT proceed until this passes.**

### Step 2: Validate OTLP (after 10s wait)
```bash
sleep 10
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-full-validation.sh {language}"
```

**Expected:** Logs in Loki, metrics in Prometheus, traces in Tempo

**If fails:** See `specification/11-otel-sdk.md` for OTLP debugging

### Step 3: Verify Grafana Dashboard

Open http://grafana.localhost → Structured Logging Testing Dashboard

**Verify ALL 3 panels show data for BOTH TypeScript AND {language}**

**See `specification/11-otel-sdk.md` section "Cross-Language Validation in Grafana" for detailed panel verification.**

**If ANY panel missing data:** Implementation is NOT complete. Debug using query tools.

### Step 4: Compare Metric Labels

```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-prometheus.sh 'sovdev_operations_total{service_name=~\".*{language}.*\"}'"
```

**Verify labels match TypeScript:**
- ✅ `peer_service` (underscore, NOT peer.service)
- ✅ `log_type` (underscore, NOT log.type)
- ✅ `log_level` (underscore, NOT log.level)

**If different:** See `specification/11-otel-sdk.md` for why underscores are critical.

### Step 5: Check Checklist

Verify `{language}/llm-work/llm-checklist-{language}.md` Phase 5 items are ALL checked.

## Success Criteria

Implementation is validated when:
- ✅ `validate-log-format.sh` PASSED
- ✅ `run-full-validation.sh` PASSED
- ✅ Grafana shows data in ALL 3 panels
- ✅ Metric labels identical to TypeScript
- ✅ Checklist Phase 5 complete

## Debugging

**For detailed debugging:** See `specification/10-development-loop.md` and `specification/11-otel-sdk.md`

**Common issues:**
- File logs pass but Grafana empty → Metric labels using dots instead of underscores
- Duration wrong unit → See `specification/11-otel-sdk.md` for conversion
- OTLP not reaching backends → Check `Host: otel.localhost` header

**Individual query tools:**
- `query-loki.sh sovdev-test-company-lookup-{language}`
- `query-prometheus.sh 'sovdev_operations_total'`
- `query-tempo.sh sovdev-test-company-lookup-{language}`

---

**Remember:** Grafana dashboard validation is CRITICAL. File logs passing ≠ implementation complete.
