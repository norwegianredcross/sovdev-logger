---
description: "Systematically implement sovdev-logger in a new programming language. INCLUDES MANDATORY VALIDATION - you must run validation tools before claiming complete. Use when implementing Python, Go, Rust, C#, PHP, or other languages."
---

# Implement Language Skill

When the user asks to implement sovdev-logger in a new programming language, guide them through the systematic process defined in the specification.

## ⚠️ IMPORTANT: Directory Restrictions

**DO NOT access these directories:**
- ❌ `terchris/` - Personal working directory (not part of specification)
- ❌ `topsecret/` - Contains credentials (never access)

**ONLY use these directories:**
- ✅ `specification/` - Specification documents (source of truth)
- ✅ `typescript/` - Reference implementation
- ✅ `go/`, `python/` - Example implementations (if needed for reference)
- ✅ `{language}/` - Where you'll create the new implementation
- ✅ `.claude/skills/` - These skills

**If you find code in `terchris/` or any personal folders, IGNORE IT.** Only use the official specification and reference implementations.

## The Systematic Process

### Phase 0: Read the Specification Documents

**Read these documents in order:**

1. **`specification/tools/README.md`** ⚠️ CRITICAL - READ FIRST
   - Complete reference for ALL validation tools
   - Explains which tools to use when
   - Shows validation workflow and tool comparison
   - **Action:** Read this before running ANY validation commands

2. **`specification/11-otel-sdk.md`** ⚠️ CRITICAL
   - OpenTelemetry SDK differences between languages
   - Common pitfalls and how to avoid them

3. **`specification/12-llm-checklist-template.md`** ⚠️ CRITICAL
   - Complete systematic checklist (Phase 0-6)
   - This is your roadmap - copy it to `{language}/llm-work/`

4. **`specification/10-development-loop.md`**
   - 4-step iterative workflow
   - Validation-first approach

5. **`specification/01-api-contract.md`**
   - 8 API functions you must implement

6. **`specification/00-design-principles.md`**
   - Core philosophy

### Follow the Checklist

**Copy the checklist:**
```bash
mkdir -p {language}/llm-work {language}/test/e2e/company-lookup
cp specification/12-llm-checklist-template.md {language}/llm-work/llm-checklist-{language}.md
```

**Then follow it systematically.** The checklist contains all the details - don't skip steps.

### Study Reference Implementations

**TypeScript (source of truth):**
- `typescript/src/logger.ts` - Shows HOW to meet requirements

**Example implementations (if helpful):**
- `go/` - Example implementation
- `python/` - Example implementation (if exists)

**Study BOTH the TypeScript AND the target language OTEL SDK before writing code.**

## ⚠️ MANDATORY VALIDATION LOOP - DO NOT SKIP ⚠️

**Complete validation tool documentation:** `specification/tools/README.md`

This README explains:
- Which tools to use for each validation step
- Complete command syntax
- What each tool validates
- How to interpret results

**After you implement the code and E2E test, you MUST immediately run validation.**

**DO NOT:**
- ❌ Stop without validation
- ❌ Claim "conversation length constraints"
- ❌ Say "ready for validation" without running validation
- ❌ Suggest "validating in a fresh conversation"
- ❌ Describe what you "should" run - ACTUALLY EXECUTE THE COMMANDS

**Validation is PART of implementation, not optional future work.**

### Required Validation Sequence:

Follow the steps below. **For complete command syntax and troubleshooting,** see `specification/tools/README.md`.

#### Step 1: Build Successfully
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/{language} && ./build-sovdevlogger.sh"
```
**Must succeed.** If fails, fix and rebuild.

#### Step 2: Run E2E Test Successfully
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup.sh {language}"
```
**Must run without errors.** If fails, fix, rebuild, and retry.

**For tool details:** See `specification/tools/README.md` → "run-company-lookup.sh"

#### Step 3: Validate Log Files FIRST (0 seconds)
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log"
```
**Expected:** `✅ PASS` with 17 log entries, 13 unique trace IDs

**For detailed explanation of what this validates:** See `specification/tools/README.md` → "validate-log-format.sh"

**If fails:** Fix issues, rebuild, run test, validate again.

#### Step 4: Validate OTLP (after 10s wait)
```bash
sleep 10
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-full-validation.sh {language}"
```
**Expected:** All validations pass (Logs in Loki, metrics in Prometheus, traces in Tempo)

**For detailed explanation of validation layers:** See `specification/tools/README.md` → "Validation Scripts Comparison"

**If fails:** See `specification/tools/README.md` → "Common Debugging Scenarios"

#### Step 5: Verify Grafana Dashboard

Open http://grafana.localhost and verify ALL 3 panels show data for BOTH TypeScript AND the new language.

**For detailed Grafana verification steps:** See `specification/11-otel-sdk.md` → "Cross-Language Validation in Grafana"

#### Step 6: Compare Metric Labels

```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-prometheus.sh 'sovdev_operations_total{service_name=~\".*{language}.*\"}'"
```

Verify labels match TypeScript exactly:
- ✅ `peer_service` (underscore, NOT peer.service)
- ✅ `log_type` (underscore, NOT log.type)
- ✅ `log_level` (underscore, NOT log.level)

**For query tool usage:** See `specification/tools/README.md` → "Query Scripts" section

**For why underscores are critical:** See `specification/11-otel-sdk.md`

## ⚠️ Execute Commands, Don't Describe Them

When you see a validation command, you MUST execute it using your bash tool.

**Wrong:** ❌
```
"I should now run validate-log-format.sh to check the logs..."
```

**Correct:** ✅
```
[Actually invoke bash_tool with the command shown above]
```

**Every validation step MUST be a real tool call, not a description.**

If you find yourself typing "I should..." or "Next, I'll...", STOP and execute the command instead.

## ⛔ Completion Criteria - DO NOT STOP BEFORE THESE ARE MET ⛔

**You have NOT implemented the language until ALL of these are ✅:**

1. ✅ `validate-log-format.sh` PASSED
2. ✅ `run-full-validation.sh` PASSED
3. ✅ Grafana dashboard shows data in ALL 3 panels
4. ✅ Metric labels MATCH TypeScript exactly (underscores)
5. ✅ Checklist `{language}/llm-work/llm-checklist-{language}.md` shows all items checked

**Implementation = Code + Validation. Not just code.**

## Common Pitfalls to Avoid

**See `specification/11-otel-sdk.md` section "Common Pitfalls" for detailed list.**

Top 3:
1. ❌ Using semantic convention defaults (dots) instead of underscores
2. ❌ Not verifying language toolchain installed first
3. ❌ Claiming complete without Grafana validation

## Getting Help

- **Implementation details:** See `specification/` documents (00-12)
- **Tool usage:** See `specification/tools/README.md` ← **COMPLETE TOOL REFERENCE**
- **Validation workflow:** See `specification/10-development-loop.md`
- **OTEL SDK issues:** See `specification/11-otel-sdk.md`

## Success

When ALL validation steps pass:
1. Update `{language}/llm-work/llm-checklist-{language}.md` - mark all items complete
2. Document issues encountered in checklist
3. Create `{language}/README.md` with quick start guide
4. Celebrate! 🎉

---

**Remember:** The specification documents are the source of truth. This skill guides you through them and enforces validation.
