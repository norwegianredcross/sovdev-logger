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

1. **`specification/11-otel-sdk.md`** ⚠️ CRITICAL
   - OpenTelemetry SDK differences between languages
   - Common pitfalls and how to avoid them

2. **`specification/12-llm-checklist-template.md`** ⚠️ CRITICAL
   - Complete systematic checklist (Phase 0-6)
   - This is your roadmap - copy it to `{language}/llm-work/`

3. **`specification/10-development-loop.md`**
   - 4-step iterative workflow
   - Validation-first approach

4. **`specification/01-api-contract.md`**
   - 8 API functions you must implement

5. **`specification/00-design-principles.md`**
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

**After you implement the code and E2E test, you MUST immediately run validation.**

**DO NOT:**
- ❌ Stop without validation
- ❌ Claim "conversation length constraints"
- ❌ Say "ready for validation" without running validation
- ❌ Suggest "validating in a fresh conversation"

**Validation is PART of implementation, not optional future work.**

### Required Validation Sequence:

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

#### Step 3: Validate Log Files FIRST (0 seconds)
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log"
```
**Expected:** `✅ PASS` with 17 log entries, 13 unique trace IDs

**This tool automatically checks:**
- JSON schema compliance
- Field naming (snake_case)
- Log entry count
- Trace ID correlation
- Required fields

**If fails:** Fix issues, rebuild, run test, validate again.

#### Step 4: Validate OTLP (after 10s wait)
```bash
sleep 10
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-full-validation.sh {language}"
```
**Expected:** Logs in Loki, metrics in Prometheus, traces in Tempo

**If fails:** Debug OTLP configuration (see `specification/11-otel-sdk.md` for common issues).

#### Step 5: Verify Grafana Dashboard

Open http://grafana.localhost and verify ALL 3 panels show data for BOTH TypeScript AND the new language.

**See `specification/11-otel-sdk.md` section "Cross-Language Validation in Grafana" for detailed dashboard verification.**

#### Step 6: Compare Metric Labels

```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-prometheus.sh 'sovdev_operations_total{service_name=~\".*{language}.*\"}'"
```

Verify labels match TypeScript exactly:
- ✅ `peer_service` (underscore, NOT peer.service)
- ✅ `log_type` (underscore, NOT log.type)
- ✅ `log_level` (underscore, NOT log.level)

**See `specification/11-otel-sdk.md` for why underscores are critical.**

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
- **Tool usage:** See `specification/tools/README.md`
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
