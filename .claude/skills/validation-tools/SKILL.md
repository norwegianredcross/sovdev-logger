---
description: "Guide to validation and query tools for debugging sovdev-logger implementations. Directs you to the comprehensive tool documentation and helps select the right tool for your task."
version: "1.2.0"
last_updated: "2025-10-27"
references:
  - specification/tools/README.md
  - specification/11-llm-checklist-template.md
  - specification/09-development-loop.md
  - .claude/skills/_SHARED.md
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

## Quick Examples (Common Commands)

<!-- Commands below duplicated from specification/tools/README.md for immediate LLM execution convenience -->

**For immediate action on the most common tasks:**

### 1. Validate Log Files (Most Common - Do This First)
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log"
```
**Expected:** ✅ PASS with 17 log entries, 13 unique trace IDs
**When:** After every test run during development, before checking OTLP

### 2. Run Full Validation (Complete 8-Step Sequence)
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-full-validation.sh {language}"
```
**Expected:** All 8 validation steps pass (Steps 1-7 automated)
**When:** Before claiming implementation complete, periodically during development
**Note:** Still requires manual Step 8 (Grafana dashboard verification)

### 3. Query Loki for Logs
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-loki.sh 'sovdev-test-company-lookup-{language}'"
```
**Expected:** Shows recent log entries from OTLP export
**When:** Debugging OTLP log export issues, verifying logs reached Loki

### 4. Query Prometheus for Metrics
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-prometheus.sh 'sovdev_operations_total{service_name=~\".*{language}.*\"}'"
```
**Expected:** Shows metric series with labels (peer_service, log_type, log_level)
**When:** Debugging metric export issues, verifying labels are correct

### 5. Run Company Lookup Test
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup.sh {language}"
```
**Expected:** Test runs without errors, generates logs
**When:** After code changes, during development loop

**For all other tools and complete documentation:** See `specification/tools/README.md`

---

## Quick Tool Selection Guide

**Question:** "Which tool should I use?"
**See:** `specification/tools/README.md` → "Quick Reference" table

**Question:** "Why is my validation failing?"
**See:** `specification/tools/README.md` → "Common Debugging Scenarios"

**Question:** "What's the difference between run-company-lookup.sh and run-full-validation.sh?"
**See:** `specification/tools/README.md` → "Validation Scripts Comparison" table

**Question:** "How do I query Loki/Prometheus/Tempo?"
**See:** `specification/tools/README.md` → "Query Scripts" section

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

**See:** `.claude/skills/_SHARED.md` → "Execute Commands, Don't Describe Them"

**Critical Rule:** When you see a command in this skill, EXECUTE it immediately using the Bash tool. Do NOT describe what you "should" or "will" do.

---

**Remember:** `specification/tools/README.md` is your complete reference. Read it when you need tool guidance.
