# Sovdev Logger Specification

## Purpose

This specification enables **implementation of sovdev-logger in any programming language** while ensuring **identical output** across all implementations.

**Target Audience:**
- LLM assistants implementing sovdev-logger in new languages
- Human developers creating or maintaining language implementations

**Goal:** Any developer (human or LLM) should be able to read this specification, the TypeScript reference implementation, and create a correct implementation in their target language that produces identical output.

---

## How to Implement a New Language

### The Process

1. **Read the Specification Documents**
   - Start with `00-design-principles.md` for philosophy
   - Read `01-api-contract.md` for exact API requirements
   - Review `02-field-definitions.md` for output format
   - Read `10-development-loop.md` for iterative workflow
   - Continue through all specification docs (00-10)

2. **Study the Reference Implementation**
   - Read `typescript/` - This is the source of truth
   - Understand the API: 8 functions with specific signatures
   - See how triple output works (console + file + OTLP)

3. **Implement the API**
   - Create the same 8 functions with identical behavior
   - Match parameter names and types (adapted to your language)
   - Produce identical output format (snake_case fields, same log structure)

4. **Implement the E2E Test**
   - Create `{language}/test/e2e/company-lookup/`
   - Follow `09-testprogram-company-lookup.md` specification
   - Must produce exactly 17 log entries with same structure as TypeScript

5. **Validate Your Implementation**
   - Run automated validation tools
   - Verify output matches reference implementation
   - Check all backends (Loki, Prometheus, Tempo)

**Success Criteria:** When your implementation passes all validation tools, producing identical output to TypeScript for the same inputs, you're done.

---

## Development Environment

### DevContainer Toolbox (Required)

**⚠️ CRITICAL:** All code execution MUST happen inside the DevContainer using the `in-devcontainer.sh` wrapper.

**Why DevContainer?**
- Provides consistent development environment across all machines (Mac, Windows, Linux)
- All programming language runtimes pre-installed
- Host machine requires NO language runtimes - everything runs in the container
- Ensures identical behavior for all developers and LLMs

**Key Operating Principle:**
- ✅ **File operations:** Read/Edit/Write files on host filesystem (fast, direct access)
- ✅ **Code execution:** ALL commands run inside DevContainer (consistent environment)
- ❌ **Never run code on host:** Language runtimes only exist in DevContainer

**For DevContainer setup and details**, see `05-environment-configuration.md`

### Running Commands with in-devcontainer.sh

**IMPORTANT:** Always use the `in-devcontainer.sh` wrapper for ALL command execution.

**Template:**
```bash
./specification/tools/in-devcontainer.sh "cd /workspace/{language} && {command}"
```

**Note:** Validation tools in `specification/tools/` automatically use `in-devcontainer.sh` internally, so you can call them directly without wrapping.

**For complete usage examples and details**, see:
- `specification/tools/README.md` - Tool documentation and examples
- `specification/05-environment-configuration.md` - DevContainer setup and troubleshooting

---

## Available Resources

### 1. Reference Implementation (TypeScript)

**Location:** `typescript/` directory

**What to learn from it:**
- How the 8 API functions work
- Triple output architecture (console + file + OTLP)
- Transaction correlation with explicit trace_id
- Error handling and credential removal
- The company-lookup E2E test implementation

**Key Files:**
- `typescript/src/index.ts` - Public API exports
- `typescript/src/logger.ts` - Core implementation
- `typescript/test/e2e/company-lookup/company-lookup.ts` - E2E test example

### 2. Specification Documents (00-10)

Complete specification for implementing sovdev-logger:

1. **[00-design-principles.md](./00-design-principles.md)** - Core philosophy and design goals
2. **[01-api-contract.md](./01-api-contract.md)** - Public API that all languages MUST implement
3. **[02-field-definitions.md](./02-field-definitions.md)** - Required fields in all log outputs
4. **[04-implementation-patterns.md](./04-implementation-patterns.md)** - Required patterns (snake_case, directory structure, etc.)
5. **[04-error-handling.md](./04-error-handling.md)** - Exception handling, credential removal, stack trace limits
6. **[05-environment-configuration.md](./05-environment-configuration.md)** - Environment variables and configuration
7. **[06-test-scenarios.md](./06-test-scenarios.md)** - Test scenarios and verification procedures
8. **[08-anti-patterns.md](./08-anti-patterns.md)** - Common mistakes to avoid
9. **[09-testprogram-company-lookup.md](./09-testprogram-company-lookup.md)** - E2E test specification (MUST implement this)
10. **[10-development-loop.md](./10-development-loop.md)** - Iterative development workflow (validate logs first, then OTLP)

### 3. Validation Tools (Automated Verification)

**Location:** `specification/tools/`

**Purpose:** Automatically validate that your implementation produces correct output

**Main validation command:**
```bash
./specification/tools/run-company-lookup-validate.sh {language}
```

**Validation Pipeline:**
```
JSON Schemas (schemas/)
    ↓ (loaded by)
Python Validators (tests/)
    ↓ (called by)
Shell Script Tools (tools/)
```

**For complete tool documentation**, see:
- `specification/tools/README.md` - All validation tools and usage
- `specification/schemas/README.md` - JSON Schema definitions
- `specification/tests/README.md` - Python validation scripts

---

## Development Workflow

**For complete iterative development workflow**, see **[10-development-loop.md](./10-development-loop.md)**.

**Key Best Practice:** Always validate log files FIRST (instant feedback), then validate OTLP backends SECOND (requires infrastructure). This provides 5-10x faster iteration during development.

### Step-by-Step Implementation Guide

**Step 1: Setup**
```bash
# Create language directory (file operation - can run on host)
mkdir -p {language}/test/e2e/company-lookup

# Copy .env template from TypeScript (file operation - can run on host)
cp typescript/test/e2e/company-lookup/.env {language}/test/e2e/company-lookup/
# Edit: Change OTEL_SERVICE_NAME to "sovdev-test-company-lookup-{language}"
```

**Step 2: Implement Core Library**
```bash
# Create your library structure (file operation - can run on host)
{language}/
├── src/               # Your implementation
└── test/
    └── e2e/
        └── company-lookup/
```

Implement these 8 functions (see `01-api-contract.md`):
1. `sovdev_initialize(service_name, service_version, peer_services_map)`
2. `sovdev_log(level, function_name, message, peer_service, input_json, response_json, exception, trace_id)`
3. `sovdev_log_job_status(level, function_name, job_name, job_status, peer_service, input_json)`
4. `sovdev_log_job_progress(level, function_name, item_id, current_item, total_items, peer_service, input_json)`
5. `sovdev_flush()`
6. `sovdev_generate_trace_id()`
7. `SOVDEV_LOGLEVELS` (constants)
8. `create_peer_services(mappings)`

**Step 3: Install Dependencies**
```bash
# Install language-specific dependencies (MUST use in-devcontainer.sh)
./specification/tools/in-devcontainer.sh "cd /workspace/{language} && {install-command}"

# Examples:
./specification/tools/in-devcontainer.sh "cd /workspace/python && pip install -r requirements.txt"
./specification/tools/in-devcontainer.sh "cd /workspace/go && go mod download"
./specification/tools/in-devcontainer.sh "cd /workspace/rust && cargo fetch"
```

**Step 4: Implement E2E Test**

Follow `09-testprogram-company-lookup.md` exactly:
- Must produce 17 log entries
- Must use same 4 organization numbers
- Must demonstrate all 8 API functions
- Output must match TypeScript structure

**Step 5: Run Tests**
```bash
# Run your tests (MUST use in-devcontainer.sh)
./specification/tools/in-devcontainer.sh "cd /workspace/{language} && {test-command}"

# Examples:
./specification/tools/in-devcontainer.sh "cd /workspace/python && pytest"
./specification/tools/in-devcontainer.sh "cd /workspace/go && go test ./..."
./specification/tools/in-devcontainer.sh "cd /workspace/typescript && npm test"
```

**Step 6: Validate**
```bash
# Run quick test (tool automatically uses in-devcontainer.sh)
./specification/tools/run-company-lookup.sh {language}

# Run complete validation (tool automatically uses in-devcontainer.sh)
./specification/tools/run-company-lookup-validate.sh {language}
```

**Step 7: Verify Cross-Language Equivalence**

Your implementation must produce **identical output structure** as TypeScript:
- Same field names (snake_case)
- Same log types (transaction, job.status, job.progress)
- Same trace ID format (32 hex chars)
- Same exception format (type/message/stacktrace)

Use validation tools to verify:
```bash
# Check log format (tool automatically uses in-devcontainer.sh)
./specification/tools/validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log

# Verify in Loki (tool automatically uses in-devcontainer.sh)
./specification/tools/query-loki.sh sovdev-test-company-lookup-{language}
```

---

## Validation Requirements

### Required Validations

Your implementation MUST pass all of these:

1. **✅ Log Format Validation**
   - All log entries conform to JSON Schema
   - Fields use snake_case naming
   - Trace IDs are 32 hex characters
   - Exception fields present when errors occur

2. **✅ E2E Test Output**
   - Produces exactly 17 log entries
   - Log types: 11 transaction, 2 job.status, 4 job.progress
   - 13 unique trace IDs for correlation
   - Company 3 fails (intentional error demonstration)

3. **✅ Backend Verification**
   - All logs appear in Loki with correct fields
   - Metrics appear in Prometheus
   - Traces appear in Tempo
   - Data queryable from Grafana

4. **✅ Cross-Language Equivalence**
   - Output structure identical to TypeScript
   - Same field names and types
   - Same error handling behavior

### Validation Tools Output

**Expected success output:**
```bash
$ ./specification/tools/run-company-lookup-validate.sh {language}

✅ All 17 log entries match schema
✅ Found 13 unique trace IDs
✅ All logs found in Loki
✅ Metrics found in Prometheus
✅ Traces found in Tempo
✅ VALIDATION PASSED
✅ Test PASSED for {language}
```

---

## Implementation Checklist

Use this checklist when implementing a new language:

### Project Structure
- [ ] Created `{language}/test/e2e/company-lookup/` directory
- [ ] Created `run-test.sh` script
- [ ] Created `.env` configuration
- [ ] Service name: `sovdev-test-company-lookup-{language}`

### API Implementation
- [ ] `sovdev_initialize()` - Logger initialization
- [ ] `sovdev_log()` - General purpose logging
- [ ] `sovdev_log_job_status()` - Job status tracking
- [ ] `sovdev_log_job_progress()` - Job progress tracking
- [ ] `sovdev_flush()` - Force export of batched telemetry
- [ ] `sovdev_generate_trace_id()` - Generate correlation ID
- [ ] `SOVDEV_LOGLEVELS` - Log level constants
- [ ] `create_peer_services()` - Peer service helper

### Output Formats
- [ ] Console output (human-readable)
- [ ] File output (JSON Lines format)
- [ ] OTLP output (OpenTelemetry Protocol)

### E2E Test (company-lookup)
- [ ] Implements exact test scenario from `09-testprogram-company-lookup.md`
- [ ] Uses same 4 organization numbers
- [ ] Produces 17 log entries
- [ ] Demonstrates all 8 API functions
- [ ] Handles intentional error (company 3 fails)

### Validation
- [ ] `run-company-lookup.sh {language}` passes
- [ ] `run-company-lookup-validate.sh {language}` passes
- [ ] All logs visible in Loki
- [ ] Metrics visible in Prometheus
- [ ] Traces visible in Tempo

---

## Key Principles

### 1. Language-Agnostic Consistency
All implementations MUST produce **identical output** when given identical inputs.

### 2. Specification is Source of Truth
The specification documents define requirements. TypeScript is the reference implementation showing HOW to meet those requirements.

### 3. Interface Consistency
Function names, parameters, and behavior must match across languages (adapted to language conventions).

### 4. Output Consistency
Log format, field names (snake_case), and structure must be identical across languages.

### 5. Automated Validation
Validation tools verify correctness - if they pass, implementation is correct.

### 6. DevContainer for All Execution
ALL code execution must happen in the DevContainer using `in-devcontainer.sh` to ensure consistent environment.

---

## Success Metrics

An implementation is **complete and correct** when:

1. ✅ All 8 API functions implemented with correct signatures
2. ✅ E2E test produces exactly 17 log entries matching specification
3. ✅ Validation tools pass (`run-company-lookup-validate.sh`)
4. ✅ Output visible in all backends (Loki, Prometheus, Tempo)
5. ✅ Output structure identical to TypeScript reference
6. ✅ Snake_case field naming throughout
7. ✅ Security features work (credential removal, stack trace limiting)

**Final Validation Command:**
```bash
./specification/tools/run-company-lookup-validate.sh {language}
```

If this passes, your implementation is ready for production use.

---

**Specification Status:** ✅ v1.0.1 COMPLETE
**Last Updated:** 2025-10-14
**Reference Implementation:** TypeScript (`typescript/`)
**Development Environment:** DevContainer Toolbox (required)
