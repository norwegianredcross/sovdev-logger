---
description: "Guide through the 4-step iterative development workflow for sovdev-logger. Optimized for fast feedback during active development."
---

# Development Loop Skill

When the user is actively developing sovdev-logger and wants to test changes, guide them through the 4-step development loop defined in the specification.

## ⚠️ IMPORTANT: Directory Restrictions

**DO NOT access these directories:**
- ❌ `terchris/` - Personal working directory
- ❌ `topsecret/` - Contains credentials

**ONLY use these directories:**
- ✅ `specification/` - Specification documents and tools
- ✅ `{language}/` - Implementation being developed

## The Development Loop

**See `specification/10-development-loop.md` for detailed workflow and philosophy.**

**Key Principle:** Validate log files FIRST (0 seconds), then OTLP SECOND (10+ seconds)

## The 4 Steps

### Step 1: Edit Code
Modify source files in `{language}/src/` or test files in `{language}/test/e2e/company-lookup/`

### Step 2: Build (when source changed)
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/{language} && ./build-sovdevlogger.sh"
```
**Must succeed.** If fails, fix errors and rebuild.

### Step 3: Run Test
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup.sh {language}"
```
**Must run without errors.** If fails, fix issues, rebuild, retry.

### Step 4a: Validate Logs FIRST ⚡ (0 seconds)
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log"
```
**Expected:** `✅ PASS` with 17 entries, 13 trace IDs

**If PASS:** Continue coding or proceed to Step 4b
**If FAIL:** Go to Step 1, fix issues, repeat loop

### Step 4b: Validate OTLP SECOND 🔄 (after 10s, periodically)
```bash
sleep 10
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-full-validation.sh {language}"
```
**Expected:** Logs in Loki, metrics in Prometheus, traces in Tempo

**Run this:** Every 3-5 iterations or before committing

## Fast vs Thorough Iteration

**Fast iteration (30-60 seconds):**
```
Edit → Build → Run → Validate logs FIRST
[Repeat immediately]
```

**Thorough validation (1-2 minutes):**
```
Edit → Build → Run → Validate logs FIRST → Validate OTLP SECOND
[Do periodically]
```

## Debugging

**For detailed debugging:** See `specification/10-development-loop.md`

**Common issues:**
- Build fails → Check compiler errors, dependencies
- Test fails → Check runtime errors, OTLP config
- Log validation fails → Check field names (snake_case), JSON schema
- OTLP validation fails → Check `Host: otel.localhost` header

## Best Practices

**✅ DO:**
- Always validate log files FIRST (catches 90% of issues)
- Build before testing (after source changes)
- Use validation tools (don't manually inspect)
- Iterate rapidly (fast loop with log validation)

**❌ DON'T:**
- Don't skip log file validation (wastes time)
- Don't wait for OTLP on every change (slow)
- Don't run test without building (tests old code)
- Don't commit without full validation (must pass both)

---

**Remember:** Fast feedback = rapid development. See `specification/10-development-loop.md` for complete details.
