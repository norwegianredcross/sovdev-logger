# Sovdev-Logger Implementation Templates

This folder contains templates for implementing and verifying sovdev-logger in new programming languages.

## Templates Available

1. **[implementation-plan-template.md](./implementation-plan-template.md)** - Step-by-step implementation plan with 8 stages
2. **[verification-plan-template.md](./verification-plan-template.md)** - Detailed verification checklist with 10 sections
3. **[verification-summary-template.md](./verification-summary-template.md)** - Executive summary (1-2 pages) for decision-makers

---

## Prerequisites - CRITICAL

**Token usage**
We are on a claude Max plan and we have lots of tokens. The llm is not alowed to decide to stop and write something like: Due to token usage considerations, let me efficiently complete the remaining sections.

⚠️ **ALL verification and testing MUST be performed inside the devcontainer**, not on the host machine.

**Why?** The monitoring stack (Prometheus, Loki, Tempo) and OTLP endpoints are only accessible from inside devcontainer.

**Verify devcontainer before starting:**
```bash
# Check devcontainer is running
docker ps | grep devcontainer-toolbox

# Test workspace access
docker exec devcontainer-toolbox bash -c "ls /workspace"
```

**For complete setup instructions and architecture details, see:**
- `specification/05-environment-configuration.md` - Full DevContainer documentation

**Quick command pattern:**
```bash
docker exec devcontainer-toolbox bash -c "cd /workspace/[language] && [command]"
```

---

## How to Use These Templates

### For Implementing a New Language (Go, Java, C#, PHP, Rust, etc.)

**Step 1: Copy and Customize the Implementation Plan**

```bash
# Copy template to your language folder
cp specification/templates/implementation-plan-template.md [language]/IMPLEMENTATION_PLAN.md

# Example for Go:
cp specification/templates/implementation-plan-template.md go/IMPLEMENTATION_PLAN.md
```

**Step 2: Replace Placeholders**

Edit the copied file and replace:
- `[LANGUAGE]` → Your language name (e.g., "Go", "Java", "C#")
- `[DATE]` → Current date
- `[version-command]` → Command to check language version (e.g., `go version`, `java -version`)
- `[run-test-command]` → Command to run tests (e.g., `go test ./...`, `mvn test`)
- `[compile-command]` → Command to compile (e.g., `go build`, `javac`)

**Step 3: Follow Stages Sequentially**

1. Complete Pre-Flight checklist
2. Work through Stage 1 → Stage 8 in order
3. Update status checkboxes: ❌ → 🔄 → ✅
4. Run ALL verification commands
5. Collect evidence (paste command outputs)
6. **STOP and fix if verification fails** - do NOT proceed to next stage
7. Update the plan document as you progress

**Step 4: After Implementation Complete**

Use the verification template to validate the implementation.

---

### For Verifying an Implementation

**Step 1: Copy BOTH Verification Templates**

```bash
# Copy both templates to your language folder
cp specification/templates/verification-summary-template.md [language]/VERIFICATION_SUMMARY.md
cp specification/templates/verification-plan-template.md [language]/VERIFICATION_REPORT.md

# Example for Go:
cp specification/templates/verification-summary-template.md go/VERIFICATION_SUMMARY.md
cp specification/templates/verification-plan-template.md go/VERIFICATION_REPORT.md
```

**Why two files?**
- **VERIFICATION_SUMMARY.md**: 1-2 page executive summary for decision-makers and stakeholders
- **VERIFICATION_REPORT.md**: Complete detailed evidence (command outputs, field comparisons, etc.)

**Step 2: Replace Placeholders**

Edit both copied files and replace:
- `[LANGUAGE]` → Your language name
- `[DATE]` → Current date
- `[Human/LLM Name]` → Who is performing verification

**Step 3: Systematic Verification**

1. Work through Section 1 → Section 10 in VERIFICATION_REPORT.md
2. Run all verification commands
3. Mark each item: ✅ PASS, ❌ FAIL, or ⏭️ SKIP
4. Collect evidence (query outputs, screenshots)
5. Document ALL failures with details
6. **Update VERIFICATION_SUMMARY.md as you progress** with key findings
7. Compare field-by-field with TypeScript reference
8. Make final approval/rejection decision in BOTH files

**Step 4: Cross-Link the Documents**

- Add link in VERIFICATION_SUMMARY.md to detailed report
- Add link in VERIFICATION_REPORT.md to summary
- Ensure status/decision matches in both files

**Step 5: Evidence Archive**

Store all evidence files:
```bash
mkdir -p [language]/verification/evidence/[date]
# Copy query outputs, logs, test results to archive
```

---

## Example LLM Prompts

### Prompt 1: Implement New Language

```
I want you to implement sovdev-logger in Go.

**Step 0: Verify devcontainer access (CRITICAL)**
docker ps | grep devcontainer-toolbox
docker exec devcontainer-toolbox bash -c "pwd"
# Must show /workspace - if not, stop and fix devcontainer setup

First, read the implementation template instructions:
specification/templates/README.md

Then, copy the implementation plan template:
cp specification/templates/implementation-plan-template.md go/IMPLEMENTATION_PLAN.md

Replace all placeholders:
- [LANGUAGE] → Go
- [DATE] → 2025-10-07
- [version-command] → go version
- [run-test-command] → go test ./...
- [compile-command] → go build

Follow the plan stage-by-stage:
1. Complete Pre-Flight checklist - read ALL specification documents
2. Complete Stage 1 - project structure setup
3. Run verification commands and collect evidence
4. Update status from ❌ to 🔄 to ✅
5. ONLY proceed to next stage when current stage passes
6. Update IMPLEMENTATION_PLAN.md after each stage

CRITICAL: Do NOT skip stages. Do NOT proceed if verification fails.
```

---

### Prompt 2: Verify Implementation

```
I want you to verify the Go implementation of sovdev-logger against the specification.

**Step 0: Verify devcontainer access (CRITICAL)**
docker ps | grep devcontainer-toolbox
docker exec devcontainer-toolbox bash -c "pwd"
# Must show /workspace - if not, stop and fix devcontainer setup

First, copy BOTH verification templates:
cp specification/templates/verification-summary-template.md go/VERIFICATION_SUMMARY.md
cp specification/templates/verification-plan-template.md go/VERIFICATION_REPORT.md

Replace placeholders in BOTH files:
- [LANGUAGE] → Go
- [DATE] → 2025-10-07
- [Verifier] → Claude

Follow the verification plan systematically in VERIFICATION_REPORT.md:
1. Section 1: API Contract - verify all 7 functions exist
2. Section 2: Field Definitions - verify console, file, OTLP output
3. Section 3: Error Handling - verify exception type, stack limiting, credentials
4. Section 4: Environment Configuration - verify env vars, file rotation
5. Section 5: Test Scenarios - run all 11 test scenarios
6. Section 6: Metrics - query Prometheus
7. Section 7: Traces - query Tempo
8. Section 8: Anti-Patterns - verify no anti-patterns present
9. Section 9: Performance - measure logging overhead
10. Section 10: Documentation - check completeness

For each section:
- Run ALL verification commands in VERIFICATION_REPORT.md
- Mark items as ✅ PASS, ❌ FAIL, or ⏭️ SKIP
- Collect evidence (paste command outputs)
- Document failures with details
- Compare with TypeScript reference output
- **Update VERIFICATION_SUMMARY.md with key findings as you progress**

After completing all 10 sections:
- Ensure both files have matching status/decision
- Add cross-links between summary and detailed report
- Make final approval/rejection decision in BOTH files
```

---

### Prompt 3: Complete Implementation with Verification

```
I want you to implement and verify sovdev-logger in Java.

**Step 0: Verify devcontainer access (CRITICAL)**
docker ps | grep devcontainer-toolbox
docker exec devcontainer-toolbox bash -c "pwd"
# Must show /workspace - if not, stop and fix devcontainer setup

Phase 1: Implementation
1. Read specification/templates/README.md
2. Copy implementation-plan-template.md to java/IMPLEMENTATION_PLAN.md
3. Replace placeholders (Java, java -version, mvn test, javac)
4. Follow stages 1-8 sequentially
5. Update IMPLEMENTATION_PLAN.md as you progress

Phase 2: Verification
1. Copy BOTH verification templates:
   - verification-summary-template.md to java/VERIFICATION_SUMMARY.md
   - verification-plan-template.md to java/VERIFICATION_REPORT.md
2. Run all verification sections 1-10 in VERIFICATION_REPORT.md
3. Update VERIFICATION_SUMMARY.md as you progress
4. Collect evidence for each section
5. Compare field-by-field with TypeScript
6. Document any failures in both files
7. Make approval/rejection decision in BOTH files
8. Add cross-links between the two files

Report back:
- Total stages completed: X/8
- Total verification checks passed: Y/N
- Critical issues found: [list]
- Implementation status: APPROVED / APPROVED WITH CONDITIONS / REJECTED
- Summary location: java/VERIFICATION_SUMMARY.md
- Detailed report: java/VERIFICATION_REPORT.md
```

---

## Template Features

### Implementation Plan Template

**8 Stages with Verification Gates:**
1. **Project Structure** - Folder layout, dependencies
2. **API Skeleton** - 7 functions with correct signatures
3. **Console & File Output** - Structured logging with rotation
4. **OTLP Logs (Loki)** - OpenTelemetry logs integration
5. **Metrics (Prometheus)** - Automatic metric generation
6. **Traces (Tempo)** - Automatic span creation
7. **Error Handling** - Credential removal, stack limiting
8. **E2E Test Suite** - All 11 test scenarios

**Each Stage Includes:**
- ✅ Deliverables checklist
- ✅ Verification commands (copy-paste ready)
- ✅ Success criteria (when to proceed)
- ✅ Evidence collection sections
- ✅ Rollback instructions

---

### Verification Templates (Two Files)

**Why Two Files?**
- **VERIFICATION_SUMMARY.md** - Executive summary (1-2 pages) for decision-makers and stakeholders
- **VERIFICATION_REPORT.md** - Complete detailed evidence for implementers and auditors

This separation allows:
- Executives to quickly understand compliance status and issues
- Technical teams to access detailed evidence when debugging
- Clear decision trail without overwhelming with details

**Verification Summary Template Features:**
- Quick stats table (compliance score, issues count)
- Section status overview (10 sections at a glance)
- Critical findings (strengths, issues, recommendations)
- Approval decision (APPROVED / APPROVED WITH CONDITIONS / REJECTED)
- Code quality assessment
- Fix instructions with estimated time
- Link to detailed report

**Verification Report Template Features:**

**10 Verification Sections:**
1. **API Contract** - Function signatures, best practices
2. **Field Definitions** - Console, file, OTLP output fields
3. **Error Handling** - Exception type, stack traces, credentials
4. **Environment Config** - Env vars, file rotation
5. **Test Scenarios** - 11 required test cases
6. **Metrics** - Prometheus queries and validation
7. **Traces** - Tempo queries and validation
8. **Anti-Patterns** - Check for common mistakes
9. **Performance** - Logging overhead measurement
10. **Documentation** - README, examples, API docs

**Each Section Includes:**
- ✅ Checklist with PASS/FAIL/SKIP tracking
- ✅ Verification commands (kubectl, curl, test runners)
- ✅ Evidence collection sections (paste command outputs)
- ✅ Field comparison tables (vs TypeScript reference)
- ✅ Issue documentation with exact locations and fixes
- ✅ Link to summary at top

---

## Why Use These Templates

### Benefits:

1. **Structured Progress** - 8 stages prevent ad-hoc implementation
2. **Verification Gates** - Cannot proceed if stage fails
3. **Evidence Collection** - All outputs documented for audit
4. **Prevents Skipping** - Checklist format ensures completeness
5. **Rollback Support** - Instructions for fixing failures
6. **LLM-Friendly** - Clear instructions for autonomous work
7. **Consistency** - Same process for all languages

### Without Templates:

❌ LLMs skip steps
❌ Incomplete implementations
❌ Missing verification
❌ No evidence trail
❌ Hard to debug failures
❌ Inconsistent across languages

### With Templates:

✅ Systematic approach
✅ Complete implementations
✅ Verified at each stage
✅ Evidence documented
✅ Easy to identify failures
✅ Consistent quality

---

## Success Criteria

An implementation is **complete** when:

1. ✅ All 8 implementation stages marked complete (✅)
2. ✅ All stage verification commands passed
3. ✅ IMPLEMENTATION_PLAN.md updated with evidence
4. ✅ All 10 verification sections marked PASS (✅)
5. ✅ VERIFICATION_REPORT.md shows field parity with TypeScript
6. ✅ No critical issues documented
7. ✅ Final verification decision: APPROVED

---

## Tips for LLMs

### DO:
- ✅ Read ALL specification documents before starting
- ✅ Update status checkboxes in real-time
- ✅ Paste actual command outputs as evidence
- ✅ Stop and fix when verification fails
- ✅ Compare field-by-field with TypeScript
- ✅ Document ALL failures clearly

### DON'T:
- ❌ Skip stages "because they seem simple"
- ❌ Proceed to next stage when verification fails
- ❌ Leave checkboxes empty
- ❌ Skip evidence collection
- ❌ Assume implementation is correct without verification
- ❌ Mark items as PASS without running commands

---

## Questions?

For specification questions, see:
- `specification/README.md` - Overview
- `specification/00-design-principles.md` - Core philosophy
- `specification/01-api-contract.md` - API to implement
- `specification/08-anti-patterns.md` - Common mistakes

---

**Template Version**: 1.0.0
**Last Updated**: 2025-10-07
