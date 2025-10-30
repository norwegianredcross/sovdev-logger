---
description: "Guide through the 6-step iterative development workflow for sovdev-logger. Optimized for fast feedback during active development."
version: "1.3.0"
last_updated: "2025-10-30"
references:
  - specification/09-development-loop.md
  - specification/12-code-quality.md
  - specification/11-llm-checklist-template.md
  - specification/tools/README.md
  - .claude/skills/_SHARED.md
---

# Development Loop Skill

When the user is actively developing sovdev-logger and wants to test changes, guide them through the 6-step development loop defined in the specification.

## ⚠️ IMPORTANT: Directory Restrictions

**See:** `.claude/skills/_SHARED.md` → "Directory Restrictions"

**Summary:** Only use `specification/` and `{language}/` directories. Do NOT access `terchris/` or `topsecret/`.

## The Development Loop

**Complete workflow documentation:** `specification/09-development-loop.md`

**Complete validation tool documentation:** `specification/tools/README.md`

**Key Principle:** Validate log files FIRST (fast, local), then validate OTLP SECOND (slow, requires infrastructure)

## The 6 Steps

<!-- Commands below duplicated from specification/09-development-loop.md and specification/tools/README.md for immediate LLM execution convenience -->

### Step 1: Edit Code
Modify source files in `{language}/src/` or test files in `{language}/test/e2e/company-lookup/`

### Step 2: Lint Code (MANDATORY - must pass before build)
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/{language} && make lint"
```
**Must succeed with exit code 0.** If errors (not warnings), fix issues before proceeding.

**See:** `specification/12-code-quality.md` for linting philosophy and rules

**Auto-fix available:**
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/{language} && make lint-fix"
```

### Step 3: Build (when source changed)
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/{language} && ./build-sovdevlogger.sh"
```
**Must succeed.** If fails, fix errors and rebuild.

### Step 4: Run Test
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup.sh {language}"
```
**Must run without errors.** If fails, fix issues, rebuild, retry.

**See:** `specification/tools/README.md` → "run-company-lookup.sh"

### Step 5: Validate Logs FIRST ⚡ (0 seconds)
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log"
```
**Expected:** `✅ PASS` with 17 entries, 13 trace IDs

**See:** `specification/tools/README.md` → "validate-log-format.sh"

**If PASS:** Continue coding or proceed to Step 6
**If FAIL:** Go to Step 1, fix issues, repeat loop

### Step 6: Validate OTLP SECOND 🔄 (after 10s, periodically)
```bash
sleep 10
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-full-validation.sh {language}"
```
**Expected:** Logs in Loki, metrics in Prometheus, traces in Tempo

**Run this:** Every 3-5 iterations or before committing

**Note:** This runs the automated portion (Steps 1-7) of the 8-step validation sequence. For complete validation, also do Step 8 (Grafana dashboard).

**See:** `specification/11-llm-checklist-template.md` → "Phase 5: Validation"

**See:** `specification/tools/README.md` (complete tool documentation)

## Fast vs Thorough Iteration

**Fast iteration (30-60 seconds):**
```
Edit → Lint → Build → Run → Validate logs FIRST
[Repeat immediately]
```

**Thorough validation (1-2 minutes):**
```
Edit → Lint → Build → Run → Validate logs FIRST → Validate OTLP SECOND (8-step sequence)
[Do periodically or before committing]
```
**Note:** Thorough validation means following the complete 8-step sequence in `specification/11-llm-checklist-template.md` Phase 5

## Debugging

**See:** `specification/tools/README.md` → "Common Debugging Scenarios"

**Common issues:**
- Build fails → Check compiler errors, dependencies
- Test fails → Check runtime errors, OTLP config
- Log validation fails → Check field names (snake_case), JSON schema
- OTLP validation fails → Check `Host: otel.localhost` header

## Best Practices

**✅ DO:**
- Always run linting BEFORE build (catches dead code, type errors)
- Always validate log files FIRST (catches 90% of issues)
- Build before testing (after source changes)
- Use validation tools (don't manually inspect)
- Iterate rapidly (fast loop with lint → build → validate logs)
- Run complete 8-step validation before committing

**❌ DON'T:**
- Don't skip linting (prevents dead code accumulation)
- Don't skip log file validation (wastes time)
- Don't wait for OTLP on every change (slow)
- Don't run test without building (tests old code)
- Don't commit without completing ALL 8 validation steps
- Don't describe commands - EXECUTE them using bash tool

## ⚠️ Execute Commands, Don't Describe Them

**See:** `.claude/skills/_SHARED.md` → "Execute Commands, Don't Describe Them"

**Critical Rule:** When you see a command in this skill, EXECUTE it immediately using the Bash tool. Do NOT describe what you "should" or "will" do.

---

**Remember:** Fast feedback = rapid development. See `specification/09-development-loop.md` for complete details and `specification/tools/README.md` for tool documentation.
