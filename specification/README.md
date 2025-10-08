# Sovdev Logger Specification

## Overview

This directory contains the **canonical specification** for sovdev-logger - a multi-language structured logging library that produces identical output across all programming languages.

The specification is designed to be read by both humans and LLMs to enable:
1. **Consistent implementations** across TypeScript, Python, Go, Java, C#, PHP, Rust
2. **LLM-assisted development** where an LLM can generate a correct implementation by reading the specification
3. **Cross-language verification** where contract tests validate that all implementations produce identical output

## Development Environment

### ⚠️ Critical: DevContainer Toolbox Required

**This repository uses the DevContainer Toolbox for ALL code execution.**

All programming language runtimes (Node.js, Python, Go, Java, PHP, etc.) are installed **inside the DevContainer only**. The host machine (Mac, Windows, Linux) does not require any language runtimes installed.

**Key Points:**
- ✅ **File operations**: Read/Edit/Write files on host filesystem (fast, direct access)
- ✅ **Code execution**: Run commands inside DevContainer (consistent environment)
- ❌ **Never run code on host**: Language runtimes only exist in DevContainer

**Container Details:**
- **Name**: `devcontainer-toolbox`
- **Base**: Debian 12 (bookworm)
- **Languages**: Node.js 22, Python 3.11, Go, Java, PHP, C#, Rust (via install scripts)
- **Mount**: Host project root → `/workspace` (read-write, bidirectional)

### Running Commands in DevContainer

**Template:**
```bash
docker exec devcontainer-toolbox bash -c "cd /workspace/[subdir] && [command]"
```

**Examples:**
```bash
# Run TypeScript test
docker exec devcontainer-toolbox bash -c "cd /workspace/typescript && npm test"

# Run Python test
docker exec devcontainer-toolbox bash -c "cd /workspace/python && python -m pytest"

# Install dependencies
docker exec devcontainer-toolbox bash -c "cd /workspace/typescript && npm install"
```

**Important**: Do NOT use `-it` flags (causes "input device is not a TTY" error in non-interactive environments like Claude Code).

For complete DevContainer usage patterns, see `.terchris/rules-environment.md`.

### Verification Tools

Language-agnostic verification tools are available in `tools/` to simplify testing:

```bash
# Quick smoke test (runs application, sends to OTLP)
./specification/tools/run-company-lookup.sh python

# Complete E2E test (queries Loki/Prometheus/Tempo)
./specification/tools/run-company-lookup-validate.sh python
```

**Two tools for different purposes:**
- **`run-company-lookup.sh`**: Fast (seconds), runs application only, good for development
- **`run-company-lookup-validate.sh`**: Complete (~30s), verifies all backends, required for official verification

**Benefits:**
- ✅ Abstracts devcontainer complexity (no need for docker exec syntax)
- ✅ Works identically for all languages
- ✅ Pre-flight checks (devcontainer running, test script exists)
- ✅ Clear error messages with guidance

See `tools/README.md` for complete documentation.

## Specification Documents

### Core Specification (v1.0.0 - Complete)

These documents are **essential** for implementing sovdev-logger in any programming language:

1. **[00-design-principles.md](./00-design-principles.md)** (15K, 309 lines)
   - Core philosophy and design goals
   - Key design decisions with rationale
   - Versioning strategy for specification and implementations
   - Success metrics for LLM-assisted development

2. **[01-api-contract.md](./01-api-contract.md)** (21K, 677 lines)
   - Public API that all languages MUST implement
   - Complete function signatures with parameters
   - Best practices: FUNCTIONNAME constant, input/response variables
   - Real-world examples from TypeScript implementation

3. **[02-field-definitions.md](./02-field-definitions.md)** (12K, 295 lines)
   - Required fields in all log outputs (OTLP, console, file)
   - Field types, sources, and validation rules
   - Loggeloven av 2025 compliance mapping

4. **[04-error-handling.md](./04-error-handling.md)** (19K, 725 lines)
   - Exception type standardization (always "Error")
   - Credential removal regex patterns
   - Stack trace limiting (350 chars max)
   - Graceful degradation requirements

5. **[05-environment-configuration.md](./05-environment-configuration.md)** (23K, 731 lines)
   - DevContainer Toolbox setup and usage
   - Kubernetes observability stack (Loki, Prometheus, Tempo, Grafana)
   - Environment variables and defaults
   - File rotation configuration (50MB/5 files main, 10MB/3 files error)

6. **[06-test-scenarios.md](./06-test-scenarios.md)** (17K, 707 lines)
   - 11 comprehensive test scenarios
   - Verification procedures for logs, metrics, traces
   - Backend query examples (kubectl, Grafana API)

7. **[08-anti-patterns.md](./08-anti-patterns.md)** (13K, 430 lines)
   - Common mistakes discovered during development
   - Wrong vs. correct examples for each anti-pattern
   - Rationale for best practices

**Total Core Specification**: ~120K, 3,874 lines

### Implementation Templates

**See [templates/README.md](./templates/README.md) for complete usage instructions and example LLM prompts.**

8. **[templates/implementation-plan-template.md](./templates/implementation-plan-template.md)**
   - Step-by-step plan template for implementing sovdev-logger in a new language
   - 8 stages with verification gates: setup → API → console/file → OTLP → metrics → traces → errors → E2E
   - Progress tracking with checkboxes (❌ → 🔄 → ✅)
   - Evidence collection sections for each stage
   - Rollback instructions if verification fails

9. **[templates/verification-plan-template.md](./templates/verification-plan-template.md)**
   - Systematic verification template for checking implementation against specification
   - 10 verification sections covering all specification requirements
   - Field-by-field comparison tables with TypeScript reference
   - Pass/Fail tracking for each requirement
   - Evidence archive structure for compliance records

**Quick Start for LLMs**: Copy template to `[language]/IMPLEMENTATION_PLAN.md`, replace placeholders, follow stages sequentially. See `templates/README.md` for detailed instructions and copy-paste prompts.

### Archived Documents

10. **[archive/plan-specification.md](./archive/plan-specification.md)** (22K, 632 lines)
   - Original working document for specification development
   - Language-agnostic testing strategy details
   - Workflow examples for adding features
   - Archived after vital information was moved to core specification documents

### Future Enhancements (Not Required for v1.0.0)

The following documents may be created if needed for future versions:
- **03-otlp-mapping.md** - Detailed OpenTelemetry specification compliance matrix
- **07-grafana-verification.md** - Expected Grafana dashboard screenshots and queries
- **09-versioning-strategy.md** - Extended version management guide (now in 00-design-principles.md)
- **10-language-agnostic-testing.md** - Contract testing implementation details (overview in plan-specification.md)

The `examples/` directory may contain actual output samples:
- **otlp/** - Real data from Loki, Prometheus, Tempo queries
- **console/** - Terminal output from each language
- **file/** - JSON log file output from each language

**Note**: Current E2E tests already verify output correctness by querying backends directly. Golden files may be added if contract testing is implemented.

## Using This Specification

### For LLM Assistants

**When implementing a new language (e.g., Go):**

1. Read all specification documents in order (00-10)
2. Generate implementation based on API contract and field definitions
3. Run contract tests to verify output matches golden files
4. Query backends (Loki/Prometheus/Tempo) to verify E2E functionality

**Remember:**
- Execute ALL code inside DevContainer
- Use host filesystem for file operations
- Follow language-specific naming conventions while maintaining API parity

### For Human Developers

**When adding a new language:**

1. Set up language runtime in DevContainer (use `.devcontainer/additions/install-*.sh` if needed)
2. Read specification documents
3. Implement the 7 core functions following the API contract
4. Run E2E tests to verify Grafana output matches reference
5. Submit PR with implementation and test results

**When adding a new feature:**

1. Update specification documents first
2. Update golden files in `examples/`
3. Use LLM to update all language implementations
4. Run contract tests to verify consistency

## Key Principles

### 1. Language-Agnostic Consistency
All implementations MUST produce **identical output** when given identical inputs. This ensures:
- Grafana queries work across all languages
- Alert rules work regardless of service language
- Operators see consistent data in dashboards

### 2. Specification-First Development
The specification is the **single source of truth**. Code is generated/maintained to match the specification, not the other way around.

### 3. LLM-Friendly Format
If an LLM can read the specification and generate a correct implementation that passes tests, the specification is complete.

### 4. Contract Testing
Tests verify **output**, not implementation details. This allows language-specific idioms while ensuring behavioral consistency.

## Testing Strategy

### Three-Level Testing

1. **Contract Tests** (Language-Agnostic)
   - JSON test definitions
   - Bash validator script
   - Golden file comparison

2. **Behavioral Tests** (Minimal Language-Specific)
   - Edge cases and error handling
   - Language-specific validation

3. **E2E Tests** (Language-Agnostic)
   - Backend queries via kubectl
   - Grafana dashboard verification

See `plan-specification.md` for detailed testing strategy.

## Backend Verification

All implementations are verified by querying the actual backends using the tools in `specification/tools/`:

**Loki (Logs):**
```bash
# Human-readable output
./specification/tools/query-loki.sh your-service

# JSON output for automated verification
./specification/tools/query-loki.sh your-service --json --limit 20
```

**Prometheus (Metrics):**
```bash
# Human-readable output
./specification/tools/query-prometheus.sh your-service

# JSON output for automated verification
./specification/tools/query-prometheus.sh your-service --json
```

**Tempo (Traces):**
```bash
# Human-readable output
./specification/tools/query-tempo.sh your-service

# JSON output for automated verification
./specification/tools/query-tempo.sh your-service --json --limit 10
```

See `specification/tools/README.md` for complete tool documentation.

## Success Metrics

An implementation is **correct** when:

1. ✅ All 7 API functions work with identical signatures (language-adapted)
2. ✅ JSON output structure matches reference implementations exactly
3. ✅ Contract tests pass with no field differences
4. ✅ E2E tests show data in Loki/Prometheus/Tempo with correct structure
5. ✅ Grafana dashboards display logs with all required fields
6. ✅ Security features work (credential removal, stack trace limiting)

## Version History

- **v1.0.1** (2025-10-07): Documentation and organizational improvements
  - **Directory Refactoring**: Renamed `test/e2e/full-stack-verification/` → `test/e2e/company-lookup/`
  - **Tool Refactoring**: Renamed `run-full-stack-verification.sh` → `run-company-lookup.sh`
  - **Bug Fix**: Updated `python/test/e2e-test.sh` and `typescript/test/e2e-test.sh` to use new directory path
  - **Rationale**: Names now match actual content (company lookup example) instead of describing what it tests
  - **Updated**: All specification documents, templates, and tool scripts (20 files)
  - **Verified**: Both Python and TypeScript complete E2E tests passing (10/10 tests each)
  - **Tools Added**: `validate-log-format.sh` - JSON Schema-based log file validator

- **v1.0.0** (2025-10-07): Complete specification based on TypeScript and Python implementations
  - **Core Documents**: 00, 01, 02, 04, 05, 06, 08 (~120K, 3,874 lines)
  - **API Contract**: 7 functions with complete signatures and best practices examples
  - **Field Definitions**: All required fields for OTLP, console, and file outputs
  - **Error Handling**: Credential removal, stack trace limiting, exception standardization
  - **Environment Setup**: DevContainer Toolbox, Kubernetes stack, file rotation
  - **Test Scenarios**: 11 comprehensive test cases with verification procedures
  - **Anti-Patterns**: Common mistakes with rationale and correct examples
  - **Design Decisions**: Key decisions documented with rationale and alternatives
  - **Versioning Strategy**: Semantic versioning for specification and implementations

## Contributing

When updating the specification:

1. **Breaking changes**: Increment major version
2. **New fields/features**: Increment minor version
3. **Documentation updates**: Increment patch version
4. **Update all implementations**: Use LLM to propagate changes to all languages
5. **Run all tests**: Verify no regressions across languages

---

**Specification Status**: ✅ v1.0.1 COMPLETE
**Last Updated**: 2025-10-07
**Next Review**: After Go or Java implementation begins
