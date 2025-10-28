---
description: "Run complete validation suite for sovdev-logger implementation. Validates file logs, OTLP backends, and Grafana dashboard. Use when validating any language implementation."
version: "1.2.0"
last_updated: "2025-10-27"
references:
  - specification/11-llm-checklist-template.md
  - specification/tools/README.md
  - specification/10-otel-sdk.md
  - .claude/skills/_SHARED.md
---

# Validate Implementation Skill

When the user asks to validate a sovdev-logger implementation, run the complete validation sequence defined in the specification.

## ⚠️ IMPORTANT: Directory Restrictions

**See:** `.claude/skills/_SHARED.md` → "Directory Restrictions"

**Summary:** Only use `specification/`, `typescript/`, and `{language}/` directories. Do NOT access `terchris/` or `topsecret/`.

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

**See:** `specification/tools/README.md` → "🔢 Validation Sequence (Step-by-Step)"

## Quick Validation Commands

<!-- Commands below duplicated from specification/tools/README.md for immediate LLM execution convenience -->

**Automated validation (Steps 1-7):**
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-full-validation.sh {language}"
```

**Manual Step 8: Grafana Dashboard**
- Open http://grafana.localhost
- Navigate to Structured Logging Testing Dashboard
- Verify ALL 3 panels show data for BOTH TypeScript AND {language}

**See:** `specification/11-llm-checklist-template.md` → "Phase 5" (complete step-by-step instructions)

## Success Criteria

Implementation is validated when:
- ✅ ALL 8 steps from Phase 5 checklist are complete
- ✅ Each step shows ✅ PASS
- ✅ Grafana dashboard shows data in ALL 3 panels
- ✅ `{language}/llm-work/llm-checklist-{language}.md` Phase 5 fully checked

## Debugging

**See:** `specification/tools/README.md` → "Common Debugging Scenarios" (complete debugging workflows)

**See:** `specification/10-otel-sdk.md` (OTLP SDK issues)

<!-- Tool names below duplicated from specification/tools/README.md for quick reference -->

**Individual query tools (for debugging):**
- `query-loki.sh sovdev-test-company-lookup-{language}`
- `query-prometheus.sh 'sovdev_operations_total'`
- `query-tempo.sh sovdev-test-company-lookup-{language}`

**All query tool documentation:** See `specification/tools/README.md` → "Query Scripts" section

## ⚠️ Execute Commands, Don't Describe Them

**See:** `.claude/skills/_SHARED.md` → "Execute Commands, Don't Describe Them"

**Critical Rule:** When you see a command in this skill, EXECUTE it immediately using the Bash tool. Do NOT describe what you "should" or "will" do.

---

**Remember:** Follow the 8-step sequence in `specification/11-llm-checklist-template.md` Phase 5. See `specification/tools/README.md` for complete tool reference.
