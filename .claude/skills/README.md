# sovdev-logger Claude Code Skills

This directory contains Claude Code skills for implementing sovdev-logger in new programming languages.

## Overview

These skills codify the systematic implementation guidance from the `specification/` folder into automatically-invoked workflows that guide LLM-assisted development.

## Available Skills

### 1. implement-language
**Invoke**: "implement sovdev-logger in {language}" (e.g., "implement sovdev-logger in Rust")

**Purpose**: Systematic 7-phase implementation guidance following the specification checklist

**Key Features**:
- Automatically references critical documents (tools/README.md, 11-otel-sdk.md, 12-llm-checklist-template.md)
- Enforces Phase 0 (pre-implementation setup) completion before coding
- Updates checklist systematically as work progresses
- Prevents "complete" claims until ALL validation criteria met
- References validation tools documentation

**What it prevents**:
- ❌ Skipping language toolchain verification
- ❌ Not studying OTEL SDK differences
- ❌ Claiming "complete" without Grafana validation
- ❌ Forgetting SDK comparison document

### 2. validate-implementation
**Invoke**: "validate the implementation" or "check if {language} is correct"

**Purpose**: Complete validation suite ensuring file logs, OTLP backends, AND Grafana dashboards all work

**Key Features**:
- Runs file log validation FIRST (fast, local feedback)
- Runs OTLP backend validation SECOND (slow, requires infrastructure)
- Checks Grafana dashboard (the CRITICAL step often missed)
- Compares metric labels with TypeScript exactly
- Cross-references with completion checklist
- References validation tools documentation

**Validation sequence**:
1. File logs (instant) - catches ~90% of issues
2. OTLP backends (10s wait) - tests infrastructure
3. Grafana dashboard (manual) - verifies ALL 3 panels show data
4. Metric labels (comparison) - ensures consistency

### 3. development-loop
**Invoke**: "test changes" or "run the development loop"

**Purpose**: Iterative 4-step workflow for rapid development with fast feedback

**Key Features**:
- Follows specification/10-development-loop.md workflow
- Enforces "validate log files FIRST" (instant feedback)
- Uses `in-devcontainer.sh` for all command execution (LLM mode)
- Handles build step when needed
- Only validates OTLP after file logs pass
- References validation tools documentation

**Development loop steps**:
1. Edit code (Read/Edit/Write tools)
2. Build library (when source changed)
3. Run test (in DevContainer)
4. Validate logs FIRST ⚡ (instant)
5. Validate OTLP SECOND 🔄 (after propagation delay)

### 4. validation-tools
**Invoke**: "which tool should I use?" or "query loki" or "debug validation failure"

**Purpose**: Directs you to comprehensive tool documentation for selecting and using validation/query tools

**Key Features**:
- Points to authoritative tool documentation (`specification/tools/README.md`)
- Provides context for when to consult tools
- No duplication - references single source of truth
- Guides tool selection for debugging

**What it prevents**:
- ❌ Not knowing tools documentation exists
- ❌ Using wrong validation tool
- ❌ Manually inspecting logs instead of using query tools
- ❌ Misunderstanding validation layers

## How Skills Work

Skills are **automatically invoked** by Claude Code when your request matches the skill description. You don't need to explicitly call skills - Claude will use them when appropriate.

**Example conversation**:
```
You: "Implement sovdev-logger in Rust"
Claude: [Automatically uses implement-language skill]
        "I'll guide you through implementing sovdev-logger in Rust
        following the 7-phase systematic process..."
```

## Benefits

### For LLM Implementations
- ✅ **Prevents Common Mistakes**: Enforces documented best practices
- ✅ **Systematic Progress**: Updates checklist as work progresses
- ✅ **Complete Validation**: No premature "complete" claims
- ✅ **References Specification**: Always uses latest docs
- ✅ **Tool Discovery**: Guides you to validation tools documentation

### For Team Collaboration
- ✅ **Shared Workflow**: All team members use same approach
- ✅ **Git Integration**: Skills committed to repo, versioned with code
- ✅ **Self-Documenting**: Skills show "the right way"
- ✅ **Reduced Onboarding**: New developers see structured guidance

### For Project Quality
- ✅ **Consistent Implementations**: All languages follow same process
- ✅ **Documentation Alignment**: Skills reference specification
- ✅ **Quality Gates**: Each phase has verification criteria
- ✅ **No Duplication**: Skills reference tools README, don't duplicate it

## Relationship to Specification

These skills **do not replace** the specification - they **guide** you through it and **reference** the authoritative documentation:

| Specification Document | Used By Skill | Purpose |
|------------------------|---------------|---------|
| `specification/README.md` | implement-language | Overall guidance |
| **`specification/tools/README.md`** | **ALL skills** | **Complete validation tool reference** |
| `specification/12-llm-checklist-template.md` | implement-language | Systematic checklist |
| `specification/11-otel-sdk.md` | implement-language | OTEL SDK differences |
| `specification/10-development-loop.md` | development-loop | Iterative workflow |
| `specification/01-api-contract.md` | implement-language | API requirements |

**Key Principle:** Skills are signposts, not encyclopedias. They point to the right documentation rather than duplicating it.

## Manual Alternative

If not using Claude Code, you can still implement sovdev-logger manually by following:
1. `specification/README.md` - Quick start guide
2. `specification/12-llm-checklist-template.md` - Systematic checklist
3. `specification/10-development-loop.md` - Development workflow
4. `specification/tools/README.md` - Complete validation tool reference

The skills simply make this process automatic and harder to skip steps.

## Skill Development

**Created**: 2025-10-21
**Version**: 1.1.0
**Status**: Production

**Recent Updates (v1.1.0)**:
- Added `validation-tools` skill for tool documentation guidance
- Updated all skills to reference `specification/tools/README.md` instead of duplicating content
- Added "Execute Commands, Don't Describe Them" sections to all skills
- Emphasized single source of truth principle

**Maintenance**:
- Skills should be updated when specification documents change
- Test skills with each new language implementation
- Gather feedback and improve skill guidance
- Keep skills as references, not duplications

## Getting Help

**For skill issues**: Review `.claude/skills/{skill-name}/SKILL.md`
**For implementation issues**: See `specification/` folder
**For tool usage**: See `specification/tools/README.md` ← **COMPLETE TOOL REFERENCE**
**For validation workflow**: See `specification/10-development-loop.md`

---

**Tip**: These skills work best when you let Claude Code invoke them naturally. Just describe what you want to do, and Claude will use the appropriate skill.
