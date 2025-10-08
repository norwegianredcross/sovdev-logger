# [LANGUAGE] Implementation Verification Summary

**Language**: [TypeScript/Python/Go/Java/C#/PHP/Rust/etc.]
**Specification Version**: v1.0.1
**Verification Date**: [YYYY-MM-DD]
**Verifier**: [Human/LLM Name]
**Overall Status**: 🟢 **APPROVED** / 🟡 **APPROVED WITH CONDITIONS** / 🔴 **REJECTED**

---

## Quick Stats

| Metric | Result |
|--------|--------|
| **API Contract** | ❌ X/7 functions implemented |
| **Best Practices** | ❌ X/4 patterns followed |
| **Field Definitions** | ❌ Console/File formats |
| **Exception Handling** | ❌ Status |
| **Documentation** | ❌ Status |
| **Compliance Score** | ❌ **X%** |

---

## Verification Status by Section

| Section | Status | Notes |
|---------|--------|-------|
| 1. API Contract | ❌ | |
| 2. Field Definitions | ❌ | |
| 3. Error Handling | ❌ | |
| 4. Environment Config | ❌ | |
| 5. Test Scenarios | ❌ | |
| 6. Metrics (Prometheus) | ❌ | |
| 7. Traces (Tempo) | ❌ | |
| 8. Anti-Patterns | ❌ | |
| 9. Performance | ❌ | |
| 10. Documentation | ❌ | |

**Legend**: ✅ PASS | ⚠️ PARTIAL | ❌ FAIL | ⏳ PENDING | ⏭️ SKIPPED

---

## Critical Findings

### ✅ Strengths

1. **[Strength 1]** - [Description]
2. **[Strength 2]** - [Description]
3. **[Strength 3]** - [Description]

### ⚠️ Areas Requiring Verification

1. **[Area 1]** - [What needs verification and why]
2. **[Area 2]** - [What needs verification and why]

### ❌ Issues Found

#### Critical Issues (Must Fix)

1. **[Issue Title]** - `[file.ext:line-range]`
   - **Severity**: HIGH/MEDIUM/LOW
   - **Issue**: [What's wrong]
   - **Impact**: [Why it matters]
   - **Current**: [Current behavior]
   - **Required**: [Expected behavior]
   - **Fix**: [How to fix it]

2. **[Continue for all issues]**

---

## Code Quality Assessment

### Positive Observations

1. **[Quality aspect 1]** - [Evidence]
2. **[Quality aspect 2]** - [Evidence]
3. **[Quality aspect 3]** - [Evidence]

### Language-Specific Patterns

- ✅ [Pattern 1 specific to this language]
- ✅ [Pattern 2 specific to this language]
- ✅ [Pattern 3 specific to this language]

---

## Comparison with Reference Implementation

| Aspect | Reference (TypeScript) | [This Language] | Match? |
|--------|------------------------|-----------------|--------|
| Function naming | camelCase | [naming] | ❌ |
| API signatures | ✅ | ❌ | ❌ |
| Field names (file) | nested objects | ❌ | ❌ |
| Field names (OTLP) | flat structure | ❌ | ❌ |
| Exception type | "Error" | ❌ | ❌ |
| Best practices | ✅ | ❌ | ❌ |

---

## Recommendation

### Decision: [APPROVED / APPROVED WITH CONDITIONS / REJECTED]

**Rationale**: [1-2 paragraph explanation of why this decision was made]

### Required Fixes (Before Production Use)

**If APPROVED**: List any optional improvements

**If APPROVED WITH CONDITIONS**: List required fixes:

1. **[Priority] [Issue Title]**
   - [One-line description]
   - Estimated effort: [X minutes/hours]

2. **[Continue for all required fixes]**

**If REJECTED**: List blocking issues that prevent approval

### Approval Conditions

**Can be used immediately for:**
- ✅ [Use case 1]
- ✅ [Use case 2]

**Requires fixes before:**
- ❌ [Blocked use case 1]
- ❌ [Blocked use case 2]

### Additional Verification Needed

To complete verification (move from X% to 100%):

1. **[Task 1]** - [Why it's needed]
2. **[Task 2]** - [Why it's needed]
3. **[Task 3]** - [Why it's needed]

### Confidence Level

**Confidence**: [High/Medium/Low] ([X]%) - [Explanation of confidence level]

---

## Next Steps

### Priority 1: Fix Issues (Estimated: [X] minutes)

1. **[Issue 1]** in `[file.ext]`:
   ```[language]
   # [Code showing how to fix]
   ```

2. **[Issue 2]** in `[file.ext]`:
   ```[language]
   # [Code showing how to fix]
   ```

3. **Re-run verification** [Which sections to re-verify]

### Priority 2: Complete Runtime Verification

1. **For implementers**: [Guidance]
2. **For verification**: [Next steps]
3. **For users**: [Usage recommendations]

---

## Evidence Location

Full detailed verification report with all evidence: [VERIFICATION_REPORT.md](./VERIFICATION_REPORT.md)

---

**Verification Completed**: [YYYY-MM-DD]
**Report Generated**: [Human/LLM Name]
**Specification Version**: v1.0.1
