# Sovdev Logger Specification

## Purpose

This specification enables **implementation of sovdev-logger in any programming language** while ensuring **identical output** across all implementations.

**Target Audience:**
- LLM assistants implementing sovdev-logger in new languages
- Human developers creating or maintaining language implementations

**Goal:** Any developer (human or LLM) should be able to read this specification, the TypeScript reference implementation, and create a correct implementation in their target language that produces identical output.

---

## Using Claude Code Skills (Recommended for LLM-Assisted Development)

If you're using Claude Code, you can leverage automatic skills that guide you through the implementation process systematically.

### Available Skills

**1. implement-language** - Systematic 7-phase implementation
- **Invoke**: "implement sovdev-logger in {language}"
- Automatically guides through Phase 0-6 with checklist tracking
- Prevents common mistakes (toolchain, SDK comparison, Grafana validation)
- Enforces completion criteria before claiming "complete"

**2. validate-implementation** - Complete validation suite
- **Invoke**: "validate the implementation"
- Runs file logs → OTLP → Grafana → labels sequence
- Ensures ALL 3 Grafana panels show data (often skipped!)
- Compares metric labels with TypeScript

**3. development-loop** - Iterative 4-step workflow
- **Invoke**: "test changes" or "run the development loop"
- Guides: Build → Run → Validate logs FIRST → Validate OTLP SECOND
- Optimized for fast feedback (file validation is instant)

**See**: `.claude/skills/README.md` for complete skills documentation

### When to Use Skills

- ✅ **Implementing new language**: Use `implement-language` skill
- ✅ **Testing changes**: Use `development-loop` skill
- ✅ **Validating implementation**: Use `validate-implementation` skill
- ✅ **First time implementing**: Skills prevent skipping critical steps

**Benefits**: Skills codify the systematic approach from this specification, making it harder to skip steps or claim completion prematurely.

---

## Quick Start: Implementing a New Language

### For Claude Code Users (Easiest)

Simply ask Claude Code:
```
"Implement sovdev-logger in {language}"
```

Claude Code will automatically use the `implement-language` skill to guide you through the 7-phase process systematically, referencing all critical documents and enforcing validation criteria.

### Manual Approach (Without Claude Code Skills)

### The 5-Step Process

1. **Read Critical Documents**
   - ⚠️ **CRITICAL:** `10-otel-sdk.md` - OpenTelemetry SDK differences (prevents major issues)
   - ⚠️ **CRITICAL:** `11-llm-checklist-template.md` - Copy to `{language}/llm-work/llm-checklist-{language}.md`
   - `00-design-principles.md` - Core philosophy
   - `01-api-contract.md` - API requirements
   - `09-development-loop.md` - Iterative workflow

2. **Study the Reference Implementation**
   - Read `typescript/src/logger.ts` - The source of truth
   - Study TypeScript OTEL SDK behavior
   - Compare with target language OTEL SDK documentation

3. **Implement the 8 API Functions**
   - See `01-api-contract.md` for complete specifications
   - Create SDK comparison document in `{language}/llm-work/`

4. **Implement E2E Test**
   - Follow `08-testprogram-company-lookup.md` specification
   - Must produce 17 log entries matching TypeScript structure

5. **Validate**
   - Run: `./specification/tools/run-full-validation.sh {language}`
   - Verify Grafana dashboard shows data in ALL 3 panels
   - Follow checklist in `{language}/llm-work/llm-checklist-{language}.md`

---

## Specification Documents

### Core Documents (Read in Order)

| Document | Purpose |
|----------|---------|
| **[00-design-principles.md](./00-design-principles.md)** | Core philosophy and design goals |
| **[10-otel-sdk.md](./10-otel-sdk.md)** ⚠️ **CRITICAL** | OpenTelemetry SDK differences between languages |
| **[11-llm-checklist-template.md](./11-llm-checklist-template.md)** ⚠️ **CRITICAL** | Systematic implementation checklist |
| **[01-api-contract.md](./01-api-contract.md)** | Public API that all languages MUST implement |
| **[09-development-loop.md](./09-development-loop.md)** | Iterative development workflow |

### Supporting Documents

| Document | Purpose |
|----------|---------|
| **[02-field-definitions.md](./02-field-definitions.md)** | Required fields in all log outputs |
| **[03-implementation-patterns.md](./03-implementation-patterns.md)** | Required patterns (snake_case, directory structure) |
| **[04-error-handling.md](./04-error-handling.md)** | Exception handling, credential removal, stack trace limits |
| **[05-environment-configuration.md](./05-environment-configuration.md)** | Environment variables, DevContainer setup, language toolchain |
| **[06-test-scenarios.md](./06-test-scenarios.md)** | Test scenarios and verification procedures |
| **[07-anti-patterns.md](./07-anti-patterns.md)** | Common mistakes to avoid |
| **[08-testprogram-company-lookup.md](./08-testprogram-company-lookup.md)** | E2E test specification (MUST implement) |

---

## Development Environment

**⚠️ CRITICAL:** All code execution MUST use DevContainer via `in-devcontainer.sh`.

**Architecture Overview:**
- **Host Machine:** Where you edit files (LLM tools or VSCode)
- **DevContainer:** Where code executes (language runtimes, tests, OTLP export)
- **Kubernetes Cluster:** Monitoring stack (Loki, Prometheus, Tempo, Grafana via Traefik)

**For architecture diagram and complete details**, see:
- `05-environment-configuration.md` → **Architecture Diagram** section (visual overview)
- `05-environment-configuration.md` → Component 1 & 2 (detailed configuration)
- `tools/README.md` - Validation tool usage and examples

**Key principle:** File operations on host, code execution in DevContainer.

---

## Implementation Workflow

**For detailed workflow**, see `09-development-loop.md` and `11-llm-checklist-template.md`.

### Quick Reference

**1. Pre-Implementation Setup**
```bash
# Create workspace
mkdir -p {language}/llm-work {language}/test/e2e/company-lookup

# Copy checklist
cp specification/11-llm-checklist-template.md {language}/llm-work/llm-checklist-{language}.md

# Copy .env template
cp typescript/test/e2e/company-lookup/.env {language}/test/e2e/company-lookup/
```

**Read before coding:**
- `10-otel-sdk.md` - Understand OTEL SDK differences
- `05-environment-configuration.md` - Verify language toolchain installed
- TypeScript reference: `typescript/src/logger.ts`
- Target language OTEL SDK documentation

**2. Implementation**
- Follow `01-api-contract.md` for 8 API functions
- Document SDK differences in `{language}/llm-work/otel-sdk-comparison.md`
- Update checklist as you progress

**3. Testing**
- Implement E2E test per `08-testprogram-company-lookup.md`
- Validate: `./specification/tools/run-full-validation.sh {language}`

---

## Validation & Success Criteria

### Main Validation Command
```bash
./specification/tools/run-full-validation.sh {language}
```

### Success Criteria

An implementation is **complete and correct** when:

1. ✅ All validation tools pass
2. ✅ **CRITICAL:** Grafana dashboard shows data in ALL 3 panels (TypeScript + new language)
3. ✅ Metric labels match TypeScript exactly (peer_service, log_type, log_level with underscores)
4. ✅ Duration values in milliseconds (histogram unit specified)
5. ✅ Output structure identical to TypeScript reference
6. ✅ Complete checklist (`{language}/llm-work/llm-checklist-{language}.md`) shows all items checked

**For detailed validation procedures**, see:
- `09-development-loop.md` - Validation workflow
- `10-otel-sdk.md` - Cross-language Grafana validation
- `11-llm-checklist-template.md` - Phase 5: Validation section

---

## Key Resources

### 1. Claude Code Skills (For LLM-Assisted Development)
- **Location:** `.claude/skills/`
- **Documentation:** `.claude/skills/README.md`
- **Main skills:** `implement-language`, `validate-implementation`, `development-loop`
- **Purpose:** Automatic guidance through implementation process

### 2. Reference Implementation
- **Location:** `typescript/` directory
- **Key files:** `typescript/src/logger.ts`, `typescript/test/e2e/company-lookup/company-lookup.ts`
- **Purpose:** Shows HOW to meet specification requirements

### 3. Validation Tools
- **Location:** `specification/tools/`
- **Documentation:** `specification/tools/README.md`
- **Main tool:** `run-full-validation.sh {language}`

### 4. JSON Schemas
- **Location:** `specification/schemas/`
- **Documentation:** `specification/schemas/README.md`
- **Purpose:** Defines exact log format structure

---

## Key Principles

1. **Language-Agnostic Consistency** - All implementations MUST produce identical output
2. **Specification is Source of Truth** - TypeScript shows HOW, specification defines WHAT
3. **OTEL SDK Differences** - Each language SDK behaves differently; study both before coding
4. **Grafana Validation is Critical** - File logs passing ≠ implementation complete
5. **Systematic Progress Tracking** - Use the checklist to prevent premature "complete" claims
6. **DevContainer for All Execution** - Ensures consistent environment across all developers

---

## Common Pitfalls

**For complete list**, see `10-otel-sdk.md` Common Pitfalls section.

**Top 3 issues from Go implementation:**
1. ❌ Not verifying language toolchain installed first
2. ❌ Using semantic convention defaults (dots) instead of underscores (peer_service, log_type, log_level)
3. ❌ Claiming "complete" without Grafana dashboard validation (all 3 panels must show data)

**Prevention:** Read `10-otel-sdk.md` and follow `11-llm-checklist-template.md` systematically.

---

## Getting Help

- **Specification issues:** Check `specification/` documents (00-12)
- **Tool usage:** See `specification/tools/README.md`
- **DevContainer problems:** See `05-environment-configuration.md`
- **OTEL SDK issues:** See `10-otel-sdk.md` Language-Specific Known Issues

---

**Specification Status:** ✅ v1.1.0 COMPLETE
**Last Updated:** 2025-10-15
**Reference Implementation:** TypeScript (`typescript/`)
**Development Environment:** DevContainer Toolbox (required)
**New in v1.1.0:** OTEL SDK implementation guide (`10-otel-sdk.md`) and systematic checklist (`11-llm-checklist-template.md`) based on Go implementation experience
