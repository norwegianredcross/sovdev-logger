---
description: "Guide through the iterative 4-step development workflow for sovdev-logger, optimized for fast feedback and rapid iteration during active development."
---

# Development Loop Skill

When the user is actively developing sovdev-logger and wants to test changes, guide them through the optimized 4-step development loop.

## Development Loop Philosophy

**Key Principle**: Validate log files FIRST (instant feedback), then OTLP backends SECOND (slow, requires infrastructure).

**Why this workflow?**

| Benefit | Description |
|---------|-------------|
| ⚡ **Instant Feedback** | File validation: 0 seconds vs OTLP: 5-10 seconds |
| 🔧 **No Dependencies** | Works without Kubernetes cluster running |
| 🎯 **Catches Most Issues** | ~90% of problems are format errors, field naming, missing data |
| 🚀 **Fast Iteration** | Edit → Build → Run → Check logs in seconds |
| 📊 **Full Visibility** | See exact JSON structure and all fields |
| 🐛 **Easy Debugging** | Direct file inspection with standard tools |

## The 4-Step Development Loop

### Step 1: Edit Code

Use Read/Edit/Write tools to modify source files on the host machine.

**Key Files to Edit**:
- `{language}/src/` - Library source code
- `{language}/test/e2e/company-lookup/` - E2E test program

**Important Note**: Because of the bind mount, files edited on the host are immediately visible in the DevContainer. You don't need to think about "where" you edit - it's the same filesystem.

### Step 2: Build Library (When Needed)

**When to build**:
- After modifying library source code
- After pulling updates from git
- After initial clone
- When in doubt, build

**Command** (using LLM execution mode):
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/{language} && ./build-sovdevlogger.sh"
```

**What the build script does**:
- **TypeScript**: Compiles TypeScript to JavaScript, creates dist/
- **Python**: Installs package in editable mode (`pip install -e .`)
- **Go**: Downloads dependencies, verifies build (`go mod tidy && go build`)

**Expected Result**: Build succeeds without errors

**If Build Fails**:
- Review error messages (compiler/linter output)
- Fix syntax or type errors
- Re-run build
- **DO NOT proceed to Step 3 until build succeeds**

### Step 3: Run Test

**Command** (using LLM execution mode):
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup.sh {language}"
```

**What this does**:
- Cleans logs directory
- Runs the E2E test program
- Generates 17 log entries
- Tests all 8 API functions
- Exports logs/metrics/traces to OTLP (if configured)

**Expected Result**: Test runs without errors

**If Test Fails**:
- Review error messages (exceptions, stack traces)
- Fix runtime errors
- Rebuild if needed
- Re-run test
- **DO NOT proceed to Step 4 until test succeeds**

### Step 4a: Validate Log Files FIRST ⚡ (Instant Feedback)

**CRITICAL**: Always validate log files BEFORE checking OTLP backends.

**Command**:
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log"
```

**What it checks automatically**:
- ✅ JSON schema compliance (all required fields present)
- ✅ Log entry count (should be 17)
- ✅ Unique trace IDs (should be 13)
- ✅ Field naming (snake_case: `service_name`, `function_name`, `trace_id`)
- ✅ Log type distribution (11 transaction, 2 job.status, 4 job.progress)
- ✅ Required fields present
- ✅ Correct data types

**Expected Result**: `✅ PASS` with summary statistics

**If PASS**: Proceed to Step 4b (OTLP validation)
**If FAIL**:
- Review error messages (validation tool is detailed)
- Go back to Step 1 (Edit Code)
- Fix issues
- Repeat loop (Edit → Build → Run → Validate)

**Common Issues Caught**:
- ❌ Wrong field names (camelCase instead of snake_case)
- ❌ Missing required fields (trace_id, log_type, service_name)
- ❌ Incorrect log_type values
- ❌ Malformed JSON (syntax errors)
- ❌ Wrong number of log entries
- ❌ Missing trace_id correlation
- ❌ Incorrect timestamp format

### Step 4b: Validate OTLP Backends SECOND 🔄 (After Log Files Pass)

**Only after Step 4a passes**, validate OTLP backends.

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
- Traces found in Tempo

**If PASS**: Iteration complete! ✅
**If FAIL**:
- Check OTLP endpoint configuration
- Verify network connectivity
- Review OTLP exporter initialization
- Go back to Step 1 (Edit Code)

## Complete Loop Example

Here's a complete development iteration:

```bash
# Step 1: Edit code (using Read/Edit/Write tools)
# Modify {language}/src/logger.{ext}

# Step 2: Build library
./specification/tools/in-devcontainer.sh -e "cd /workspace/{language} && ./build-sovdevlogger.sh"
# Output: Build successful

# Step 3: Run test
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup.sh {language}"
# Output: Test program executed, logs generated

# Step 4a: Validate log files FIRST (instant)
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log"
# Output: ✅ PASS - 17 entries, 13 trace IDs

# Step 4b: Validate OTLP SECOND (after 10s wait)
sleep 10
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-full-validation.sh {language}"
# Output: ✅ Logs in Loki, metrics in Prometheus, traces in Tempo

# ✅ Iteration complete!
```

## When to Use Each Step

### Always Run:
- **Step 1**: Edit Code (every iteration)
- **Step 3**: Run Test (every iteration)
- **Step 4a**: Validate Logs (every iteration)

### Run When Needed:
- **Step 2**: Build Library (only after source code changes)
- **Step 4b**: Validate OTLP (periodically, not every iteration)

### Suggested Frequency:
- **Edit → Build → Run → Validate Logs**: Every small change (fast iteration)
- **+ Validate OTLP**: Every 3-5 iterations, or before committing
- **+ Grafana Dashboard Check**: Before claiming phase complete

## Optimizing for Speed

### Fast Iteration Pattern (30-60 seconds)
```
1. Edit code (small change)
2. Build (if source changed)
3. Run test
4. Validate logs FIRST ⚡
[Repeat immediately if issues found]
```

### Thorough Validation Pattern (1-2 minutes)
```
1. Edit code
2. Build
3. Run test
4. Validate logs FIRST ⚡
5. Wait 10 seconds
6. Validate OTLP SECOND 🔄
[Only do this periodically]
```

### Complete Validation Pattern (2-3 minutes)
```
1. Edit code
2. Build
3. Run test
4. Validate logs FIRST ⚡
5. Wait 10 seconds
6. Validate OTLP SECOND 🔄
7. Open Grafana dashboard
8. Verify ALL 3 panels show data
[Do before claiming phase complete]
```

## Debugging Tips

### Issue: Build Fails

**Symptoms**: Compiler/linter errors, missing dependencies

**Debug Steps**:
1. Read error messages carefully
2. Check syntax and types
3. Verify dependencies installed
4. Compare with TypeScript reference
5. Check language-specific build requirements

### Issue: Test Fails

**Symptoms**: Runtime errors, exceptions, crashes

**Debug Steps**:
1. Review stack trace
2. Check OTLP endpoint configuration
3. Verify environment variables set
4. Test individual API functions
5. Add debug logging

### Issue: Log Validation Fails

**Symptoms**: Wrong field names, missing fields, wrong log count

**Debug Steps**:
1. Read validation error messages (very detailed)
2. Inspect `{language}/test/e2e/company-lookup/logs/dev.log` directly
3. Compare with TypeScript logs
4. Check field naming (snake_case vs camelCase)
5. Verify all 8 API functions called in test

### Issue: OTLP Validation Fails

**Symptoms**: No logs in Loki, no metrics in Prometheus

**Debug Steps**:
1. Check OTLP endpoint configuration
2. Verify `host.docker.internal` resolves
3. Verify `Host: otel.localhost` header set
4. Query backends directly:
   ```bash
   ./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-loki.sh sovdev-test-company-lookup-{language}"
   ```
5. Check OTLP exporter initialization in code

## Best Practices

### ✅ DO

1. **Always validate log files FIRST** (catches 90% of issues instantly)
2. **Build before testing** (after source code changes)
3. **Use validation tools** (don't manually inspect unless debugging)
4. **Follow the sequence** (Edit → Build → Run → Validate)
5. **Iterate rapidly** (fast loop with log validation only)

### ❌ DON'T

1. **Don't skip log file validation** (wastes time waiting for OTLP)
2. **Don't wait for OTLP when developing** (use log files for fast iteration)
3. **Don't run test without building** (will test old code)
4. **Don't commit without full validation** (both file logs AND OTLP must pass)
5. **Don't manually inspect files** (use validation tools first)

## Integration with Other Skills

### Used by `implement-language` Skill
The development loop is part of Phase 1-6 implementation:
- Use during active coding
- Iterate until Phase validation passes
- Complete loop before moving to next phase

### Precedes `validate-implementation` Skill
- Use development loop during implementation
- Use validate-implementation when claiming complete
- Development loop = fast iteration
- Validate-implementation = thorough validation

## Success Indicators

You're using the development loop correctly when:
- ✅ Getting fast feedback (seconds, not minutes)
- ✅ Catching issues early (in file validation)
- ✅ Iterating rapidly (multiple loops per hour)
- ✅ Not waiting for OTLP on every change
- ✅ Only checking OTLP periodically

You need to adjust workflow when:
- ❌ Waiting for OTLP on every change
- ❌ Manually inspecting files instead of using validation tools
- ❌ Forgetting to build after source changes
- ❌ Committing without OTLP validation

---

**Remember**: Fast feedback loop = rapid development. Use log file validation for speed, OTLP validation for confidence.
