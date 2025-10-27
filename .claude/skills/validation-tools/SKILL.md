---
description: "Guide to validation and query tools for debugging sovdev-logger implementations. Directs you to the comprehensive tool documentation and helps select the right tool for your task."
---

# Validation Tools Skill

When you need to validate outputs, query backends, or debug issues, this skill guides you to the right tools.

## 📚 Complete Tool Documentation

**AUTHORITATIVE SOURCE:** `specification/tools/README.md`

This README contains:
- **🔢 Validation Sequence (Step-by-Step)** - The 8-step sequence with blocking points
- Complete list of ALL validation and query tools
- Detailed comparison tables (which tool for which purpose)
- Command syntax and examples
- Validation layer explanations (schema vs. consistency)
- Troubleshooting workflows

**Before using ANY tool, read this README to understand your options.**

**For validation:** Start with the 8-step sequence section

---

## When to Use Tools

### During Active Development
**Read:** `specification/09-development-loop.md` (explains the workflow)
**Primary tools:** `validate-log-format.sh`, `run-company-lookup.sh`

### For Complete Validation
**Read:** `specification/11-llm-checklist-template.md` Phase 5
**Primary tool:** `run-full-validation.sh`

### For Debugging Issues
**Read:** `specification/tools/README.md` → "Common Debugging Scenarios" section
**Tools vary** based on the issue (Loki query tools, Prometheus query tools, etc.)

---

## Quick Tool Selection Guide

**Question:** "Which tool should I use?"
**Answer:** Read `specification/tools/README.md` → "Quick Reference" table

**Question:** "Why is my validation failing?"
**Answer:** Read `specification/tools/README.md` → "Common Debugging Scenarios"

**Question:** "What's the difference between run-company-lookup.sh and run-full-validation.sh?"
**Answer:** Read `specification/tools/README.md` → "Validation Scripts Comparison" table

**Question:** "How do I query Loki/Prometheus/Tempo?"
**Answer:** Read `specification/tools/README.md` → "Query Scripts" section

---

## Critical Principle

**Tools are documentation-driven, not skill-driven.**

This skill tells you WHERE to look. The tools README tells you WHAT to do.

If you find yourself asking "which command do I run?", the answer is:
1. Open `specification/tools/README.md`
2. Find the relevant table or section
3. Execute the command shown

---

## ⚠️ Execute Commands, Don't Describe Them

When you find the right command in `specification/tools/README.md`, you MUST execute it using your bash tool.

**Wrong:** ❌
```
"I should run validate-log-format.sh to check the logs..."
```

**Correct:** ✅
```
[Actually invoke bash_tool with the command]
```

**Every validation step MUST be a real tool call, not a description.**

---

**Remember:** `specification/tools/README.md` is your complete reference. Read it when you need tool guidance.
