---
description: "Run complete validation suite for sovdev-logger implementation, including file logs, OTLP backends, and Grafana dashboard verification. Use when validating any language implementation."
---

# Validate Implementation Skill

When the user asks to validate a sovdev-logger implementation, run the complete validation sequence in the correct order.

## Validation Philosophy

**Key Principle**: Validate log files FIRST (instant, local), then OTLP backends SECOND (slow, requires infrastructure).

**Why this order?**
- ⚡ **Instant Feedback**: File validation takes 0 seconds vs OTLP 5-10 seconds
- 🔧 **No Dependencies**: Works without Kubernetes cluster
- 🎯 **Catches Most Issues**: ~90% of problems are format errors caught by file validation
- 🚀 **Fast Iteration**: Edit → Run → Validate logs in seconds

## Validation Sequence

Follow this sequence exactly. Do NOT skip steps or reorder.

### Step 1: File Log Validation (FAST - Do This First!)

**Command**:
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log"
```

**What it checks automatically**:
- ✅ JSON schema compliance
- ✅ Log entry count (should be 17)
- ✅ Unique trace IDs (should be 13)
- ✅ Field naming (snake_case: `service_name`, `function_name`, `trace_id`)
- ✅ Log type distribution (11 transaction, 2 job.status, 4 job.progress)
- ✅ Required fields present
- ✅ Correct data types

**Expected Result**: `✅ PASS` with summary statistics

**If FAILED**:
- Review error messages (validation tool is detailed)
- Fix issues in code
- Re-run test and validation
- **DO NOT proceed to Step 2 until file validation passes**

### Step 2: OTLP Backend Validation (After File Logs Pass)

**Wait for propagation**:
```bash
sleep 10  # Logs/metrics/traces need time to reach backends
```

**Command**:
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-full-validation.sh {language}"
```

**What it checks**:
- ✅ Logs in Loki (query and count)
- ✅ Metrics in Prometheus (if implemented)
- ✅ Traces in Tempo (if implemented)
- ✅ Field consistency across backends

**Expected Result**:
- Logs found in Loki
- Metrics found in Prometheus
- Traces found in Tempo (if tracing implemented)

**If FAILED**:
- Check OTLP endpoint configuration
- Verify `host.docker.internal` networking
- Check `Host: otel.localhost` header
- Review OTLP exporter initialization
- Query backends directly using individual tools:
  - `query-loki.sh sovdev-test-company-lookup-{language}`
  - `query-prometheus.sh 'sovdev_operations_total{service_name=~".*{language}.*"}'`
  - `query-tempo.sh sovdev-test-company-lookup-{language}`

### Step 3: Grafana Dashboard Validation (MOST CRITICAL - Often Skipped!)

**Why this is critical**: File logs and OTLP can pass, but Grafana dashboard still shows no data due to incorrect metric labels or histogram units.

**Open Grafana**:
```
http://grafana.localhost
```

**Navigate to**: Structured Logging Testing Dashboard

**Verify ALL 3 panels show data for BOTH languages**:

#### Panel 1: Total Operations

Check for both TypeScript AND the new language:
- [ ] TypeScript shows "Last" value (e.g., 17)
- [ ] {Language} shows "Last" value (e.g., 17)
- [ ] TypeScript shows "Max" value
- [ ] {Language} shows "Max" value

**If missing**: Metrics not reaching Prometheus or metric name wrong

#### Panel 2: Error Rate

Check for both TypeScript AND the new language:
- [ ] TypeScript shows "Last %" value
- [ ] {Language} shows "Last %" value
- [ ] TypeScript shows "Max %" value
- [ ] {Language} shows "Max %" value

**If missing**: Error counting not working or metric labels incorrect

#### Panel 3: Average Operation Duration

Check for both TypeScript AND the new language:
- [ ] TypeScript shows entries for all peer services (BRREG, ALTINN, INTERNAL)
- [ ] {Language} shows entries for all peer services
- [ ] Values are in milliseconds (e.g., 0.538 ms, NOT 0.000538)

**If missing**:
- Histogram not configured correctly
- Duration recorded in wrong unit (seconds instead of milliseconds)
- Unit not specified in histogram (`unit: 'ms'`)

**Common Issue**: Go OTEL SDK defaults to seconds, must convert to milliseconds manually.

#### If ANY Panel Missing Data

**DO NOT claim implementation complete.** Debug using these steps:

1. Query Prometheus directly:
   ```bash
   ./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-prometheus.sh 'sovdev_operations_total{service_name=~\".*{language}.*\"}'"
   ```

2. Check metric labels (see Step 4)

3. Review histogram configuration in code:
   - Is unit specified as `'ms'`?
   - Is duration calculated in milliseconds?

4. Check OTEL SDK documentation for target language:
   - How to specify histogram unit?
   - What's the default time unit?

### Step 4: Metric Label Comparison

**Purpose**: Verify metric labels are IDENTICAL to TypeScript (prevents dashboard breakage).

**Query TypeScript metrics**:
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-prometheus.sh 'sovdev_operations_total{service_name=~\".*typescript.*\"}'"
```

**Query new language metrics**:
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-prometheus.sh 'sovdev_operations_total{service_name=~\".*{language}.*\"}'"
```

**Compare labels - must be IDENTICAL**:

Expected labels:
```
✅ peer_service (underscore, NOT peer.service)
✅ log_type (underscore, NOT log.type or function.name)
✅ log_level (underscore, NOT log.level)
✅ service_name
✅ service_version
```

**Common mistake**: Using OTEL semantic convention defaults (dots) instead of manual attributes (underscores).

**If labels different**:
- Review metric attribute setting in code
- Check if using semantic conventions (change to manual attributes)
- Verify attribute names use underscores
- Compare with TypeScript implementation in `typescript/src/logger.ts`

### Step 5: Cross-Reference with Checklist

**Open checklist**: `{language}/llm-work/llm-checklist-{language}.md`

**Verify Phase 5 (Validation) items are ALL checked**:
- [ ] File log validation PASSES
- [ ] OTLP validation PASSES
- [ ] Grafana dashboard shows data in ALL 3 panels
- [ ] Metric labels IDENTICAL to TypeScript
- [ ] Duration values in milliseconds
- [ ] Histogram has unit specification

**If any item unchecked**: Implementation is NOT complete. Go back and fix.

## Validation Results Summary

After completing all steps, document results:

### ✅ Complete Validation (All Pass)
```
✅ File log validation: PASS (17 entries, 13 trace IDs)
✅ OTLP validation: PASS (logs/metrics/traces in backends)
✅ Grafana Panel 1: PASS (Total Operations shows data)
✅ Grafana Panel 2: PASS (Error Rate shows data)
✅ Grafana Panel 3: PASS (Duration in milliseconds)
✅ Metric labels: IDENTICAL to TypeScript
✅ Checklist Phase 5: ALL items checked

🎉 Implementation is COMPLETE and VALIDATED!
```

### ❌ Incomplete Validation (Issues Found)
```
✅ File log validation: PASS
✅ OTLP validation: PASS
❌ Grafana Panel 3: FAIL - Values in seconds instead of milliseconds
❌ Metric labels: Using log.level instead of log_level

⚠️ Implementation NOT complete. Issues to fix:
1. Convert duration to milliseconds
2. Change metric labels to underscore notation
```

## Common Issues and Solutions

### Issue 1: File Logs Pass, But Grafana Shows No Data

**Symptom**: `validate-log-format.sh` passes, but Grafana panels empty

**Causes**:
- Metric labels using dots instead of underscores
- Histogram unit not specified
- Duration in wrong unit (seconds instead of milliseconds)
- Metrics not exported to OTLP

**Solution**:
1. Query Prometheus directly (Step 4)
2. Compare metric labels with TypeScript
3. Fix attribute naming in code
4. Rebuild and retest

### Issue 2: Duration Shows as 0.000538 Instead of 0.538 ms

**Symptom**: Grafana Panel 3 shows very small values (microseconds or seconds)

**Causes**:
- Duration recorded in seconds (Go default)
- Histogram unit not specified as `'ms'`

**Solution**:
1. Convert duration to milliseconds in code
2. Specify histogram unit: `unit: 'ms'` (or language equivalent)
3. Rebuild and retest

### Issue 3: Grafana Shows TypeScript But Not New Language

**Symptom**: Only TypeScript shows in Grafana panels

**Causes**:
- Metrics not reaching Prometheus
- Service name filter doesn't match
- OTLP endpoint configuration wrong

**Solution**:
1. Verify OTLP endpoints in test environment config
2. Check `host.docker.internal` resolution
3. Verify `Host: otel.localhost` header
4. Query Prometheus for service name directly

## Debugging Commands

If validation fails, use these tools:

### Query Loki Logs
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-loki.sh sovdev-test-company-lookup-{language}"
```

### Query Prometheus Metrics
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-prometheus.sh 'sovdev_operations_total'"
```

### Query Tempo Traces
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-tempo.sh sovdev-test-company-lookup-{language}"
```

### Validate Grafana API Connection
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-grafana.sh"
```

## Success Criteria

Implementation is validated when:
- ✅ All 5 validation steps pass
- ✅ Grafana shows data in ALL 3 panels
- ✅ Metric labels identical to TypeScript
- ✅ Duration values in milliseconds
- ✅ Checklist Phase 5 complete

**Only then**: Implementation is COMPLETE ✅

---

**Remember**: Grafana dashboard validation is the MOST CRITICAL step. File logs and OTLP passing does NOT mean implementation is complete.
