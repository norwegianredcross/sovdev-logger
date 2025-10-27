---
description: "Run complete validation suite for sovdev-logger implementation. Validates file logs, OTLP backends, and Grafana dashboard. Use when validating any language implementation."
---

# Validate Implementation Skill

When the user asks to validate a sovdev-logger implementation, run the complete validation sequence defined in the specification.

## ⚠️ IMPORTANT: Directory Restrictions

**DO NOT access these directories:**
- ❌ `terchris/` - Personal working directory
- ❌ `topsecret/` - Contains credentials

**ONLY use these directories:**
- ✅ `specification/` - Validation tools and documentation
- ✅ `typescript/` - Reference for comparison
- ✅ `{language}/` - Implementation being validated

## Validation Workflow

**CRITICAL:** Follow the complete 8-step validation sequence.

**AUTHORITATIVE VALIDATION GUIDE:** `specification/11-llm-checklist-template.md` → **Phase 5: Validation**

This section contains:
- ✅ Complete 8-step validation sequence (Steps 1-8)
- ✅ Blocking points between steps (don't skip ahead)
- ✅ What each step checks and which tool to use
- ✅ Pass/Fail checkboxes for tracking progress
- ✅ Automated validation (Steps 1-7) vs Manual validation (Step 8)

**The 8 steps are:**
1. Validate Log Files (INSTANT) ⚡
2. Verify Logs in Loki (OTLP → Loki) 🔄
3. Verify Metrics in Prometheus (OTLP → Prometheus) 🔄
4. Verify Traces in Tempo (OTLP → Tempo) 🔄
5. Verify Grafana-Loki Connection (Grafana → Loki) 🔄
6. Verify Grafana-Prometheus Connection (Grafana → Prometheus) 🔄
7. Verify Grafana-Tempo Connection (Grafana → Tempo) 🔄
8. Verify Grafana Dashboard (Visual Verification) 👁️

**⛔ DO NOT skip steps or proceed until each step passes**

**For tool details:** See `specification/tools/README.md` → "🔢 Validation Sequence (Step-by-Step)"

## Quick Validation Commands

**Automated validation (Steps 1-7):**
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-full-validation.sh {language}"
```

**Manual Step 8: Grafana Dashboard**
- Open http://grafana.localhost
- Navigate to Structured Logging Testing Dashboard
- Verify ALL 3 panels show data for BOTH TypeScript AND {language}

**For complete step-by-step instructions:** Follow `specification/11-llm-checklist-template.md` Phase 5 exactly.

## Success Criteria

Implementation is validated when:
- ✅ ALL 8 steps from Phase 5 checklist are complete
- ✅ Each step shows ✅ PASS
- ✅ Grafana dashboard shows data in ALL 3 panels
- ✅ `{language}/llm-work/llm-checklist-{language}.md` Phase 5 fully checked

## Debugging

**For complete debugging workflows:** See `specification/tools/README.md` → "Common Debugging Scenarios"

**For OTLP SDK issues:** See `specification/10-otel-sdk.md`

**Individual query tools (for debugging):**
- `query-loki.sh sovdev-test-company-lookup-{language}`
- `query-prometheus.sh 'sovdev_operations_total'`
- `query-tempo.sh sovdev-test-company-lookup-{language}`

**All query tool documentation:** See `specification/tools/README.md` → "Query Scripts" section

## ⚠️ Execute Commands, Don't Describe Them

When you see a validation command, you MUST execute it using your bash tool.

**Wrong:** ❌
```
"I should run the validation tools to check the implementation..."
```

**Correct:** ✅
```
[Actually invoke bash_tool with the commands shown above]
```

**Every validation step MUST be a real tool call, not a description.**

---

**Remember:** Follow the 8-step sequence in `specification/11-llm-checklist-template.md` Phase 5. See `specification/tools/README.md` for complete tool reference.
