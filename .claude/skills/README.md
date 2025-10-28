# sovdev-logger Claude Code Skills

This directory contains Claude Code skills for implementing sovdev-logger in new programming languages.

## Overview

These skills codify the systematic implementation guidance from the `specification/` folder into automatically-invoked workflows that guide LLM-assisted development.

## Available Skills

### 1. implement-language
**Invoke**: "implement sovdev-logger in {language}" (e.g., "implement sovdev-logger in Rust")

**Purpose**: Systematic 7-phase implementation guidance following the specification checklist

**Key Features**:
- Automatically references critical documents (tools/README.md, 10-otel-sdk.md, 11-llm-checklist-template.md)
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
- Follows specification/09-development-loop.md workflow
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

## Shared Components

**To avoid duplication, common content is maintained in `_SHARED.md`:**

### What's Shared
- **Directory Restrictions**: Access rules for terchris/, topsecret/, specification/, etc.
- **Execute Commands Warning**: Critical reminder to execute commands, not describe them
- **Common Cross-References**: Frequently referenced specification documents

### Why Share
- **Single Source of Truth**: Update once, applies to all skills
- **Consistency**: All skills use identical wording for critical guidance
- **Maintainability**: Changes to common patterns only need one edit

### How Skills Reference Shared Content
Each skill includes:
```markdown
## ⚠️ IMPORTANT: Directory Restrictions

**See:** `.claude/skills/_SHARED.md` → "Directory Restrictions"

**Summary:** [Brief inline summary for quick reference]
```

This pattern:
- ✅ Eliminates ~95 lines of duplication
- ✅ Provides quick summary inline
- ✅ Points to complete details in _SHARED.md
- ✅ Makes maintenance easier

## Strategic Duplication Policy

**Some duplication is intentional and documented for LLM execution convenience.**

### What We Duplicate

Validation commands (bash commands) appear in BOTH:
- `specification/tools/README.md` (authoritative documentation)
- Skills (for immediate LLM execution)

### Why We Duplicate

**Purpose:** Skills guide immediate action. When Claude Code sees a command in a skill, it should execute immediately without context-switching to another file.

**Philosophy:**
- **Specification documents** = Reference documentation (should have NO duplication)
- **Skills** = Action workflows (can duplicate commands for usability)

### How We Mark Duplication

Every duplicated command section includes an HTML comment:
```html
<!-- Commands below duplicated from specification/tools/README.md for immediate LLM execution convenience -->
```

This makes the duplication:
- ✅ **Visible**: Anyone reading the skill sees it's duplicated
- ✅ **Intentional**: Clearly marked as design decision, not oversight
- ✅ **Traceable**: References the authoritative source

### Maintenance Process

When updating commands in `specification/tools/README.md`:
1. Check if the command is duplicated in skills (look for HTML comments)
2. Update the duplicated commands in skills to match
3. Skills with duplicated commands:
   - `implement-language/SKILL.md`: Build, test, validation commands
   - `development-loop/SKILL.md`: Development loop commands
   - `validate-implementation/SKILL.md`: Quick validation commands
   - `validation-tools/SKILL.md`: 5 common commands

### Lines Duplicated

- **Estimated:** ~100 lines across all skills
- **Trade-off:** Accepted for LLM execution convenience
- **Alternative considered:** Centralize commands (rejected - too slow for LLM workflow)

**This duplication is intentional, documented, and maintained.**

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
| `specification/11-llm-checklist-template.md` | implement-language | Systematic checklist |
| `specification/10-otel-sdk.md` | implement-language | OTEL SDK differences |
| `specification/09-development-loop.md` | development-loop | Iterative workflow |
| `specification/01-api-contract.md` | implement-language | API requirements |

**Key Principle:** Skills are signposts, not encyclopedias. They point to the right documentation rather than duplicating it.

## Manual Alternative

If not using Claude Code, you can still implement sovdev-logger manually by following:
1. `specification/README.md` - Quick start guide
2. `specification/11-llm-checklist-template.md` - Systematic checklist
3. `specification/09-development-loop.md` - Development workflow
4. `specification/tools/README.md` - Complete validation tool reference

The skills simply make this process automatic and harder to skip steps.

## Skill Development

**Created**: 2025-10-21
**Version**: 1.4.0
**Status**: Production

**Recent Updates**:

**v1.4.0** (2025-10-28):
- **Checklist Workflow Clarity**: Improved implement-language skill
  - Added prominent "Your Working Checklist" section immediately after directory restrictions
  - Clarified that checklist copy is the FIRST concrete action
  - Emphasized checklist is working plan updated throughout implementation
  - Removed duplicate "Follow the Checklist" section from Phase 0
  - Updated implement-language skill to version 1.3.0

**v1.3.0** (2025-10-27):
- **Phase 3 (Strategic Duplication)**: Documented intentional command duplication
  - Added HTML comments marking duplicated commands (source: specification/tools/README.md)
  - Created Strategic Duplication Policy in README
  - Accepted ~100 lines of command duplication for LLM execution convenience
- **Phase 1 (Standardization)**: Added metadata and standardized references
  - Added version, last_updated, references to all skill frontmatter
  - Standardized 14 cross-reference patterns to consistent **See:** format
  - All skills now at version 1.2.0 with clear dependencies listed

**v1.2.0** (2025-10-27):
- **Phase 5 (Checklist Alignment)**: Fixed validation sequence inconsistency
  - implement-language now references 8-step sequence from checklist Phase 5
  - validation-tools now provides quick examples for common commands
  - All skills consistently reference checklist Phase 5 as authoritative
- **Phase 2 (Content Deduplication)**: Created shared components pattern
  - Added `_SHARED.md` with common content (Directory Restrictions, Execute Commands warning)
  - Updated all 4 skills to reference shared components
  - Eliminated ~95 lines of duplication across skills

**v1.1.0** (2025-10-21):
- Added `validation-tools` skill for tool documentation guidance
- Updated all skills to reference `specification/tools/README.md` instead of duplicating content
- Added "Execute Commands, Don't Describe Them" sections to all skills
- Emphasized single source of truth principle

**Maintenance**:
- **Common content**: Update `_SHARED.md` (applies to all skills automatically)
- **Duplicated commands**: When updating `specification/tools/README.md`, check HTML comments in skills and update matching commands
- **Specification changes**: Skills should be updated when specification documents change
- **Testing**: Test skills with each new language implementation
- **Feedback**: Gather feedback and improve skill guidance
- **Philosophy**: Keep skills as action guides (can duplicate for usability), not encyclopedias

## Getting Help

**For skill issues**: Review `.claude/skills/{skill-name}/SKILL.md`
**For implementation issues**: See `specification/` folder
**For tool usage**: See `specification/tools/README.md` ← **COMPLETE TOOL REFERENCE**
**For validation workflow**: See `specification/09-development-loop.md`

---

**Tip**: These skills work best when you let Claude Code invoke them naturally. Just describe what you want to do, and Claude will use the appropriate skill.
