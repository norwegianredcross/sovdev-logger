# Development Loop

**Version:** 1.6.0
**Last Updated:** 2025-10-15
**Status:** Complete

---

## Purpose

This document describes the **iterative development workflow** for implementing and testing sovdev-logger in any programming language.

**Key Principle:** Validate log files FIRST (fast, local), then validate OTLP backends SECOND (slow, requires infrastructure).

---

## Developer Workflows: Human vs LLM

**For environment architecture diagram**, see `05-environment-configuration.md` → **Architecture Diagram** section. This shows how Host Machine, DevContainer, and Kubernetes Cluster interact.

There are **two different ways** to work with sovdev-logger, depending on whether you're a human or an LLM:

### Human Developers (VSCode + DevContainer Extension)

**Environment:** VSCode with DevContainer extension installed and running

**How it works:**
- Open project in VSCode
- VSCode automatically starts the DevContainer
- **Terminal runs INSIDE the container** (automatically)
- Run commands directly without wrappers

**Example commands:**
```bash
# Run test (terminal is already inside container)
cd typescript/test/e2e/company-lookup
./run-test.sh

# Or use npm/python/go directly
npm test
python -m pytest
go test ./...

# Validate log files
../../../specification/tools/validate-log-format.sh typescript/test/e2e/company-lookup/logs/dev.log
```

**Key difference:** No need for `in-devcontainer.sh` wrapper - you're already inside!

---

### LLM Developers (Host Machine + Bash Tool)

**Environment:** LLM running on host machine, using Bash tool to execute commands

**How it works:**
- LLM edits files on host filesystem (Read/Edit/Write tools)
- LLM uses `in-devcontainer.sh` wrapper for ALL code execution
- Commands run inside container via wrapper
- Results returned to LLM

**Example commands:**
```bash
# Run test (call tool in container)
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup.sh typescript"

# Validate log files (call tool in container)
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh typescript/test/e2e/company-lookup/logs/dev.log"

# Custom commands (any command in container)
./specification/tools/in-devcontainer.sh -e "cd /workspace/typescript && npm install"
```

**Key difference:** ALWAYS use `in-devcontainer.sh -e "command"` - everything inside quotes executes in the container.

---

### Command Comparison

| Task | Human Developer (VSCode Terminal) | LLM Developer (Host + Bash Tool) |
|------|-----------------------------------|----------------------------------|
| **Run TypeScript test** | `cd typescript/test/e2e/company-lookup && ./run-test.sh` | `./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup.sh typescript"` |
| **Run Python test** | `cd python/test/e2e/company-lookup && ./run-test.sh` | `./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup.sh python"` |
| **Install dependencies** | `cd typescript && npm install` | `./specification/tools/in-devcontainer.sh -e "cd /workspace/typescript && npm install"` |
| **Run unit tests** | `cd typescript && npm test` | `./specification/tools/in-devcontainer.sh -e "cd /workspace/typescript && npm test"` |
| **Validate log format** | `validate-log-format.sh logs/dev.log` | `./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh typescript/.../logs/dev.log"` |
| **Query Loki** | `query-loki.sh sovdev-test-company-lookup-typescript` | `./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-loki.sh sovdev-test-company-lookup-typescript"` |

**Note:** LLMs must use `in-devcontainer.sh -e "command"` for ALL commands. Human developers run commands directly (terminal is already inside container).

---

## The Development Loop

The typical development cycle follows this 3-step pattern:

**Note on file editing:** The DevContainer uses a bind mount, so files edited on the host are immediately visible in the container and vice versa. You don't need to think about "where" you edit - it's the same filesystem. The distinction below is only about **where commands execute**.

---

### For LLMs: Track Your Progress with the Checklist

**⚠️ IMPORTANT:** As you work through the development loop, systematically update your implementation checklist.

**Checklist Location:** `{language}/llm-work/llm-checklist-{language}.md`

**How to use it:**
1. **Before starting:** Copy `specification/12-llm-checklist-template.md` to `{language}/llm-work/llm-checklist-{language}.md`
2. **During development:** Update checkboxes as you complete each step
   - Mark items as `in_progress` when you start working on them
   - Mark items as `completed` when finished
3. **Before claiming complete:** Verify ALL completion criteria are checked

**Why this matters:**
- Prevents forgetting critical steps (language toolchain, SDK comparison, Grafana validation)
- Provides workspace for SDK analysis and notes
- Ensures systematic implementation
- Prevents premature "complete" claims

**See:** `12-llm-checklist-template.md` for the complete 7-phase checklist you should be following.

---

### 1. Edit Code

Edit source files using your preferred tools:
- Human developers: Use VSCode editor (works seamlessly with bind mount)
- LLM developers: Use Read/Edit/Write tools on host filesystem

**Important:** Because of the bind mount, there's no difference between "editing on host" vs "editing in container" - they're the same files.

---

### 2. Run Test

**This is where Human vs LLM differs!**

**Human developers (VSCode terminal inside container):**
```bash
# Direct execution - you're already inside!
cd typescript/test/e2e/company-lookup
./run-test.sh

# Or
npm test
python -m pytest
go test ./...
```

**LLM developers (host machine):**
```bash
# Call the test tool (recommended)
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup.sh {language}"

# Or run test script directly:
./specification/tools/in-devcontainer.sh -e "cd /workspace/{language}/test/e2e/company-lookup && ./run-test.sh"
```

---

### 3. Validate Log Files FIRST ⚡ (Fast & Local)

**CRITICAL:** Always validate log files before checking OTLP backends.

**Human developers (VSCode terminal inside container):**
```bash
validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log
```

**LLM developers (host machine - use wrapper):**
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log"
```

**That's it!** The validation tool automatically checks:
- ✅ JSON schema compliance
- ✅ Log entry count (should be 17)
- ✅ Unique trace IDs (should be 13)
- ✅ Field naming (snake_case)
- ✅ Log type distribution (11 transaction, 2 job.status, 4 job.progress)
- ✅ Required fields present
- ✅ Correct data types

**If validation passes, you're ready for Step 4 (OTLP backends).**

**For debugging failures**, see manual inspection commands in the "Debugging Commands" section below.

**Why validate log files first?**

| Benefit | Description |
|---------|-------------|
| ⚡ **Instant feedback** | No waiting for backend propagation (0 seconds vs 5-10 seconds) |
| 🔧 **No dependencies** | Works without Kubernetes cluster running |
| 🎯 **Catches most issues** | ~90% of problems are format errors, field naming, missing data |
| 🚀 **Fast iteration** | Edit → Run → Check logs in seconds |
| 📊 **Full visibility** | See exact JSON structure and all fields |
| 🐛 **Easy debugging** | Direct file inspection with standard tools (jq, grep) |

**Common Issues Caught by Log File Validation:**
- ❌ Wrong field names (camelCase instead of snake_case)
- ❌ Missing required fields (trace_id, log_type, service_name)
- ❌ Incorrect log_type values
- ❌ Malformed JSON (syntax errors)
- ❌ Wrong number of log entries
- ❌ Missing trace_id correlation
- ❌ Incorrect timestamp format

---

### 4. Validate OTLP Backends SECOND 🔄 (After Log Files Pass)

Only after log files are correct, validate that telemetry reaches the observability backends.

**Human developers (VSCode terminal inside container):**
```bash
# Wait 5-10 seconds for logs to propagate to backends
sleep 10

# Run complete backend validation
run-company-lookup-validate.sh {language}
```

**LLM developers (host machine - use wrapper):**
```bash
# Wait 5-10 seconds for logs to propagate to backends
sleep 10

# Run complete backend validation
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup-validate.sh {language}"
```

**This validation checks:**
- ✅ Logs in Loki (query and count)
- ✅ Metrics in Prometheus (if implemented)
- ✅ Traces in Tempo (if implemented)
- ✅ Field consistency across backends

**Or query backends directly:**

**Human developers:**
```bash
query-loki.sh sovdev-test-company-lookup-{language}
query-prometheus.sh sovdev-test-company-lookup-{language}
query-tempo.sh sovdev-test-company-lookup-{language}
```

**LLM developers:**
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-loki.sh sovdev-test-company-lookup-{language}"
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-prometheus.sh sovdev-test-company-lookup-{language}"
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-tempo.sh sovdev-test-company-lookup-{language}"
```

**Why validate OTLP backends second?**
- Requires wait time for backend propagation (5-10 seconds)
- Depends on Kubernetes cluster being available
- Tests network connectivity and OTLP configuration
- Validates observability stack integration

---

## Complete Workflow Examples

**Key Difference:** Only **Step 2 (Run Test)** differs between Human and LLM developers. All other steps (Edit, Validate Logs, Validate OTLP) work the same thanks to the bind mount.

### Example 1: Human Developer (VSCode Terminal)

Working inside VSCode with DevContainer extension - terminal is already inside container:

```bash
# ============================================
# Step 1: Edit code in VSCode
# ============================================
# (use VSCode editor to modify source files)

# ============================================
# Step 2: Run test (terminal is inside container)
# ============================================
cd python/test/e2e/company-lookup
./run-test.sh

# ============================================
# Step 3: Validate log files (FAST - do this first!)
# ============================================
../../../specification/tools/validate-log-format.sh logs/dev.log

# That's it! Validation tool checks everything automatically.
# If it passes, move to Step 4.

# ============================================
# Step 4: If validation passes, check OTLP backends
# ============================================
sleep 10
../../../specification/tools/run-company-lookup-validate.sh python
```

---

### Example 2: LLM Developer (Host Machine)

Working on host machine - must use `in-devcontainer.sh -e "command"` for ALL code execution:

```bash
# ============================================
# Step 1: Edit code on host
# ============================================
# (LLM uses Read/Edit/Write tools to modify source files)

# ============================================
# Step 2: Run test in DevContainer (using wrapper)
# ============================================
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup.sh python"

# Or run test script directly:
# ./specification/tools/in-devcontainer.sh -e "cd /workspace/python/test/e2e/company-lookup && ./run-test.sh"

# ============================================
# Step 3: Validate log files (FAST - do this first!)
# ============================================
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh python/test/e2e/company-lookup/logs/dev.log"

# That's it! Validation tool checks everything automatically.
# If it passes, move to Step 4.

# ============================================
# Step 4: If validation passes, check OTLP backends
# ============================================
sleep 10
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup-validate.sh python"
```

---

## Quick Reference: Development Commands

### Essential Commands

**LLM developers (from host - use wrapper with -e flag for ALL commands):**
```bash
# Run test
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup.sh {language}"

# Validate log files (instant)
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log"

# Validate backends (after 10s wait)
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup-validate.sh {language}"
```

**Human developers (VSCode terminal inside container - run directly):**
```bash
# Run test
cd {language}/test/e2e/company-lookup && ./run-test.sh

# Validate log files (instant)
validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log

# Validate backends (after 10s wait)
run-company-lookup-validate.sh {language}
```


## Best Practices

### ✅ DO

1. **Always validate log files before OTLP backends**
   - Catches 90% of issues instantly
   - No waiting for infrastructure

2. **Use validation tools early and often**
   - Run `validate-log-format.sh` after every change
   - Catch issues immediately, not at the end

3. **Run complete validation before committing**
   - All log file checks pass
   - All backend validations pass

4. **Follow the 4-step loop consistently**
   - Edit → Run → Validate Logs → Validate OTLP
   - Don't skip steps
   - Only Step 2 (Run) differs between Human/LLM developers

### ❌ DON'T

1. **Don't skip log file validation**
   - "Just checking OTLP" wastes time waiting for propagation
   - You'll miss obvious format errors

2. **Don't wait for OTLP when developing**
   - Use log files for fast iteration
   - Only check OTLP periodically

3. **Don't run tests on host machine** (LLM developers)
   - Always use `in-devcontainer.sh` wrapper
   - Ensures consistent runtime environment
   - Note: Human developers work inside container already (VSCode terminal)

4. **Don't commit without full validation**
   - Both log files AND backends must pass
   - Use `run-company-lookup-validate.sh {language}`

### ⚠️ For LLMs Specifically

**CRITICAL:** Follow the examples in this document exactly, with no variations.

1. **Update your checklist as you work**
   - Checklist location: `{language}/llm-work/llm-checklist-{language}.md`
   - Mark items `in_progress` when starting, `completed` when done
   - Prevents forgetting critical steps
   - See "For LLMs: Track Your Progress with the Checklist" section above

2. **Use tool commands EXACTLY as shown in examples**
   - Do NOT add parameters (like `--limit`) unless example shows them
   - Do NOT use manual inspection tools (`jq`, `python -m json.tool`, `cat`)
   - Copy the command patterns character-for-character

3. **Trust the validation tools**
   - `validate-log-format.sh` checks everything automatically (schema, fields, types, trace IDs)
   - If you think you need to manually inspect, you're wrong
   - The tools give you all the information you need

4. **Follow the sequence**
   - Edit → Run → Validate Logs → Validate OTLP
   - Don't query backends before running tests (query tools READ data, they don't GENERATE data)
   - Run tests FIRST, then query results

5. **When in doubt, re-read the examples**
   - The examples in this document are complete and correct
   - If your command doesn't match an example, you're doing it wrong

---

## Integration with Validation Tools

All validation tools support this workflow:

| Tool | Purpose | Speed | When to Use |
|------|---------|-------|-------------|
| `validate-log-format.sh` | Check log file structure | Instant | After every test run |
| `run-company-lookup.sh` | Run test program | 2-5 seconds | During development |
| `run-company-lookup-validate.sh` | Complete validation | 15-20 seconds | Before committing |
| `query-loki.sh` | Query Loki backend | 5-10 seconds | Debugging OTLP issues |
| `query-prometheus.sh` | Query Prometheus | 5-10 seconds | Debugging metrics |
| `query-tempo.sh` | Query Tempo | 5-10 seconds | Debugging traces |

**For complete tool documentation**, see `specification/tools/README.md`.

---

## Related Documentation

- **[05-environment-configuration.md](./05-environment-configuration.md)** - DevContainer setup and configuration
- **[06-test-scenarios.md](./06-test-scenarios.md)** - Test scenarios and verification procedures
- **[09-testprogram-company-lookup.md](./09-testprogram-company-lookup.md)** - Company-lookup E2E test specification
- **[tools/README.md](./tools/README.md)** - Complete validation tool documentation

---

**Document Status:** ✅ v1.7.0 COMPLETE
**Last Updated:** 2025-10-15
**Part of:** sovdev-logger specification v1.1.0

**Version History:**
- v1.7.0 (2025-10-15): Added "For LLMs: Track Your Progress with the Checklist" section and updated "⚠️ For LLMs Specifically" to reference systematic checklist tracking
- v1.6.0 (2025-10-15): Added "⚠️ For LLMs Specifically" section with explicit anti-patterns (no --limit, no manual inspection, follow examples exactly)
- v1.5.0 (2025-10-14): Changed to Mode 2 pattern - ALL commands use `in-devcontainer.sh -e "command"` for consistency
- v1.4.0 (2025-10-14): Clarified LLMs MUST use `in-devcontainer.sh` wrapper for ALL commands (tools and custom commands)
- v1.3.0 (2025-10-14): Emphasized validation tools over manual commands - use `validate-log-format.sh` (does everything)
- v1.2.0 (2025-10-14): Clarified bind mount behavior - file editing works same for both, only code execution differs
- v1.1.0 (2025-10-14): Added distinction between Human vs LLM developer workflows
- v1.0.0 (2025-10-14): Initial release with 4-step development loop
