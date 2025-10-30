---
description: "Systematically implement sovdev-logger in a new programming language. INCLUDES MANDATORY VALIDATION - you must run validation tools before claiming complete. Use when implementing Python, Go, Rust, C#, PHP, or other languages."
version: "1.4.0"
last_updated: "2025-10-30"
references:
  - specification/11-llm-checklist-template.md
  - specification/12-code-quality.md
  - specification/tools/README.md
  - specification/10-otel-sdk.md
  - specification/09-development-loop.md
  - specification/01-api-contract.md
  - specification/00-design-principles.md
  - .claude/skills/_SHARED.md
---

# Implement Language Skill

When the user asks to implement sovdev-logger in a new programming language, guide them through the systematic process defined in the specification.

## ⚠️ IMPORTANT: Directory Restrictions

**See:** `.claude/skills/_SHARED.md` → "Directory Restrictions"

**Summary:** Only use `specification/`, `typescript/`, `{language}/`, and `.claude/skills/` directories. Do NOT access `terchris/` or `topsecret/`.

## Your Working Checklist

**First step: Create your working checklist**
```bash
mkdir -p {language}/llm-work {language}/test/e2e/company-lookup
cp specification/11-llm-checklist-template.md {language}/llm-work/llm-checklist-{language}.md
```

**This is YOUR plan throughout implementation.** Update checkboxes as you:
- ✅ Complete each phase and task
- 📝 Document issues and workarounds
- 🎯 Track validation progress

**All subsequent phases reference this working checklist** at `{language}/llm-work/llm-checklist-{language}.md`

Now proceed with Phase 0...

---

## The Systematic Process

### Phase 0: Read the Specification Documents

**Read these documents in THIS EXACT ORDER (do not skip):**

1. **`specification/05-environment-configuration.md`** ⚠️ CRITICAL - READ FIRST
   - Explains DevContainer environment
   - Shows how to use `in-devcontainer.sh` wrapper
   - **Action:** Understand that ALL commands must use this wrapper
   - **Time:** 5 minutes
   - **Key Takeaway:** You cannot run commands directly - must use `./specification/tools/in-devcontainer.sh -e "command"`

2. **`specification/tools/README.md`** ⚠️ CRITICAL - READ SECOND
   - Complete reference for ALL validation tools
   - 8-step validation sequence with blocking points
   - When to use Grafana vs CLI tools
   - **Action:** Study tool comparison table and validation workflow
   - **Time:** 10 minutes
   - **Key Takeaway:** Grafana is authoritative, kubectl is optional

3. **`specification/10-otel-sdk.md`** ⚠️ CRITICAL - READ THIRD
   - OpenTelemetry SDK differences between languages
   - Metric naming conventions (underscores not dots)
   - Enum handling patterns
   - **Action:** Note all "⚠️ CRITICAL" sections for your language
   - **Time:** 10 minutes
   - **Key Takeaway:** Cannot translate TypeScript code - must understand BOTH SDKs

4. **`specification/07-anti-patterns.md`** ⚠️ CRITICAL - READ FOURTH
   - Code anti-patterns to avoid in implementation
   - Implementation process pitfalls from Python experience
   - **Action:** Note all implementation process pitfalls
   - **Time:** 10 minutes
   - **Key Takeaway:** Use in-devcontainer.sh, underscores in metrics, enum.value

5. **`specification/11-llm-checklist-template.md`** ⚠️ CRITICAL
   - Complete systematic checklist (Phase 0-7)
   - Create your working copy: `{language}/llm-work/llm-checklist-{language}.md`
   - **Action:** Copy this and update it throughout implementation
   - **Time:** 5 minutes to review structure
   - **Key Takeaway:** This is YOUR plan - update as you progress

6. **`specification/09-development-loop.md`**
   - 6-step iterative workflow
   - Validation-first approach with mandatory linting
   - **Time:** 5 minutes
   - **Key Takeaway:** Edit → Lint → Build → Test → Validate → Iterate

7. **`specification/12-code-quality.md`**
   - Code linting standards and quality rules
   - Strict dead code prevention (prevents LLMs from "going off the rails")
   - Language-specific configuration patterns
   - **Action:** Understand linting is MANDATORY before build
   - **Time:** 5 minutes
   - **Key Takeaway:** Create Makefile with `lint` target, strict rules prevent bad patterns

8. **`specification/01-api-contract.md`**
   - 8 API functions you must implement
   - **Time:** 5 minutes
   - **Key Takeaway:** All 8 functions required, not optional

9. **`specification/00-design-principles.md`**
   - Core philosophy
   - **Time:** 5 minutes
   - **Key Takeaway:** Developer-centric, zero-config, validation-first

**Total Reading Time:** ~60 minutes (DO NOT SKIP THIS)

**After reading, confirm you understand:**
- [ ] How to run commands using `in-devcontainer.sh`
- [ ] The 8-step validation sequence
- [ ] When to use Grafana instead of CLI tools (answer: always if kubectl fails)
- [ ] Critical differences for your target language from 10-otel-sdk.md
- [ ] That metric names MUST use underscores not dots

### Study Reference Implementations

**TypeScript (source of truth):**
- `typescript/src/logger.ts` - Shows HOW to meet requirements

**Example implementations (if helpful):**
- `go/` - Example implementation
- `python/` - Example implementation (if exists)

**Study BOTH the TypeScript AND the target language OTEL SDK before writing code.**

## ⚠️ MANDATORY VALIDATION LOOP - DO NOT SKIP ⚠️

**After you implement the code and E2E test, you MUST immediately run the 8-step validation sequence.**

**AUTHORITATIVE VALIDATION SEQUENCE:** `specification/11-llm-checklist-template.md` → **Phase 5: Validation**

This checklist defines the complete validation workflow with:
- ✅ 8 sequential validation steps (do NOT skip or reorder)
- ✅ Blocking points between steps (don't proceed until each passes)
- ✅ Exact tool commands for each step
- ✅ Expected outputs and pass/fail criteria

**Complete validation tool documentation:** `specification/tools/README.md`

**DO NOT:**
- ❌ Stop without validation
- ❌ Claim "conversation length constraints"
- ❌ Say "ready for validation" without running validation
- ❌ Suggest "validating in a fresh conversation"
- ❌ Skip steps or condense the sequence
- ❌ Describe what you "should" run - ACTUALLY EXECUTE THE COMMANDS

**Validation is PART of implementation, not optional future work.**

---

### Pre-Validation: Build and Test

**Before starting the 8-step validation sequence, ensure:**

<!-- Commands below duplicated from specification/tools/README.md for immediate LLM execution convenience -->

#### Build Successfully
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/{language} && ./build-sovdevlogger.sh"
```
**Must succeed.** If fails, fix and rebuild.

#### Run E2E Test Successfully
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup.sh {language}"
```
**Must run without errors.** If fails, fix, rebuild, and retry.

**See:** `specification/tools/README.md` → "run-company-lookup.sh"

---

### The 8-Step Validation Sequence

**Follow Phase 5 of your checklist (`{language}/llm-work/llm-checklist-{language}.md`) exactly.**

<!-- 8-step sequence and commands below duplicated from specification/11-llm-checklist-template.md Phase 5 for immediate LLM execution convenience -->

**Quick reference of the 8 steps:**

1. **⚡ Step 1: Validate Log Files (INSTANT - 0 seconds)**
   - Tool: `validate-log-format.sh`
   - Checks: JSON schema, field naming, log count (17), trace IDs (13)
   - Command:
     ```bash
     ./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log"
     ```
   - Expected: ✅ PASS with 17 log entries, 13 unique trace IDs
   - If fails: Fix issues, rebuild, run test, validate again

2. **🔄 Step 2: Verify Logs in Loki (OTLP → Loki)**
   - Tool: `query-loki.sh`
   - Checks: Logs reached Loki, log count matches

3. **🔄 Step 3: Verify Metrics in Prometheus (OTLP → Prometheus)**
   - Tool: `query-prometheus.sh`
   - Checks: Metrics reached Prometheus, labels correct (peer_service, log_type, log_level)
   - Verify labels match TypeScript exactly:
     - ✅ `peer_service` (underscore, NOT peer.service)
     - ✅ `log_type` (underscore, NOT log.type)
     - ✅ `log_level` (underscore, NOT log.level)

4. **🔄 Step 4: Verify Traces in Tempo (OTLP → Tempo)**
   - Tool: `query-tempo.sh`
   - Checks: Traces reached Tempo

5. **🔄 Step 5: Verify Grafana-Loki Connection (Grafana → Loki)**
   - Tool: `query-grafana-loki.sh`
   - Checks: Grafana can query Loki

6. **🔄 Step 6: Verify Grafana-Prometheus Connection (Grafana → Prometheus)**
   - Tool: `query-grafana-prometheus.sh`
   - Checks: Grafana can query Prometheus

7. **🔄 Step 7: Verify Grafana-Tempo Connection (Grafana → Tempo)**
   - Tool: `query-grafana-tempo.sh`
   - Checks: Grafana can query Tempo

8. **👁️ Step 8: Verify Grafana Dashboard (Visual Verification - Manual)**
   - Open http://grafana.localhost
   - Navigate to: Structured Logging Testing Dashboard
   - Verify: ALL 3 panels show data for BOTH TypeScript AND {language}
   - **See:** `specification/10-otel-sdk.md` → "Cross-Language Validation in Grafana"

**⛔ DO NOT skip steps or claim complete until ALL 8 steps pass**

---

### Quick Validation: Automated Steps 1-7

<!-- Command below duplicated from specification/tools/README.md for immediate LLM execution convenience -->

**After waiting 10 seconds for OTLP propagation**, you can run automated validation for steps 1-7:

```bash
sleep 10
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-full-validation.sh {language}"
```

**This automates steps 1-7** but you MUST still complete **Step 8 (Grafana Dashboard)** manually.

**Note:** `run-full-validation.sh` is a helper that runs steps 1-7 sequentially. If any step fails, the tool output will show which specific validation layer failed.

**See also:**
- Validation layers: **See:** `specification/tools/README.md` → "Validation Scripts Comparison"
- Debugging: **See:** `specification/tools/README.md` → "Common Debugging Scenarios"
- Tool commands: **See:** `specification/11-llm-checklist-template.md` → "Phase 5"

## ⚠️ Execute Commands, Don't Describe Them

**See:** `.claude/skills/_SHARED.md` → "Execute Commands, Don't Describe Them"

**Critical Rule:** When you see a command in this skill, EXECUTE it immediately using the Bash tool. Do NOT describe what you "should" or "will" do.

## ⛔ Completion Criteria - DO NOT STOP BEFORE THESE ARE MET ⛔

**You have NOT implemented the language until ALL of these are ✅:**

1. ✅ ALL 8 validation steps PASSED (from checklist Phase 5):
   - Step 1: Log file validation ✅
   - Step 2: Logs in Loki ✅
   - Step 3: Metrics in Prometheus ✅
   - Step 4: Traces in Tempo ✅
   - Step 5: Grafana-Loki connection ✅
   - Step 6: Grafana-Prometheus connection ✅
   - Step 7: Grafana-Tempo connection ✅
   - Step 8: Grafana dashboard visual verification ✅
2. ✅ Grafana dashboard shows data in ALL 3 panels for {language}
3. ✅ Metric labels MATCH TypeScript exactly (underscores: peer_service, log_type, log_level)
4. ✅ Checklist `{language}/llm-work/llm-checklist-{language}.md` Phase 5 shows all items checked

**Implementation = Code + Validation. Not just code.**

## Common Pitfalls to Avoid

**Complete list:** See `specification/07-anti-patterns.md`
**OTEL SDK specific:** See `specification/10-otel-sdk.md` section "Common Pitfalls"

Top 5 implementation process pitfalls (from Python experience):
1. ❌ Running commands directly on host instead of using `in-devcontainer.sh`
2. ❌ Using dots in metric names instead of underscores (Prometheus requirement)
3. ❌ Using `str(enum)` instead of `enum.value` for enum conversion
4. ❌ Missing Grafana-required fields (timestamp, severity_text, severity_number)
5. ❌ Wasting time trying to fix kubectl instead of using Grafana

## Getting Help

- **Implementation details:** See `specification/` documents (00-12)
- **Tool usage:** See `specification/tools/README.md` ← **COMPLETE TOOL REFERENCE**
- **Validation workflow:** See `specification/09-development-loop.md`
- **OTEL SDK issues:** See `specification/10-otel-sdk.md`

## Success

When ALL validation steps pass:
1. Update `{language}/llm-work/llm-checklist-{language}.md` - mark all items complete
2. Document issues encountered in checklist
3. Create `{language}/README.md` with quick start guide
4. Celebrate! 🎉

---

**Remember:** The specification documents are the source of truth. This skill guides you through them and enforces validation.
