# Sovdev Logger Multi-Language Specification Strategy

## Purpose

This document outlines the strategy for maintaining consistent behavior across all sovdev-logger implementations (Python, TypeScript, and future languages like Go, Rust, Java, C#).

The goal is to use **specification-driven development** where:
1. A single source of truth defines behavior
2. LLMs can generate/maintain implementations
3. E2E tests verify correctness via Grafana output comparison

## Problem Statement

When maintaining a library across multiple languages, we face:
- **Behavioral drift**: Each implementation interprets requirements differently
- **Maintenance burden**: Bug fixes and new features must be manually ported to each language
- **Quality inconsistency**: Different developers have different standards
- **Onboarding difficulty**: New implementations require deep understanding of existing code

## Solution: LLM-Assisted Specification-First Development

### Core Principle
**If an LLM can read the specification and generate a correct implementation that passes tests, the specification is complete.**

### Key Components

1. **Canonical Specification** - Single source of truth in `/specification/` folder
2. **Reference Examples** - Actual JSON output from Loki/Prometheus/Tempo
3. **Reference Examples** - Actual JSON output to logs
4. **Reference Examples** - Actual output to terminal
5. **Language-Agnostic Tests** - Verify output, not implementation details
6. **LLM-Friendly Format** - Clear, unambiguous, with examples

## Proposed Folder Structure

```
/sovdev-logger/
├── specification/
│   ├── README.md                          # How to use this specification
│   ├── 00-design-principles.md            # Core philosophy and goals
│   ├── 01-api-contract.md                 # Public API (all languages MUST match)
│   ├── 02-field-definitions.md            # Required fields in logs/metrics/traces
│   ├── 03-otlp-mapping.md                 # OpenTelemetry specification compliance
│   ├── 04-error-handling.md               # Exception/error standardization
│   ├── 05-environment-configuration.md    # Environment variables and defaults
│   ├── 06-test-scenarios.md               # Required test cases for acceptance
│   ├── 07-grafana-verification.md         # Expected Grafana dashboard output
│   ├── 08-anti-patterns.md                # Common mistakes to avoid
│   ├── 09-versioning-strategy.md          # How to handle spec changes
│   ├── 10-language-agnostic-testing.md    # Testing strategy (contract tests)
│   ├── examples/
│   │   ├── otlp/
│   │   │   ├── loki-log-examples.json     # Expected Loki output samples
│   │   │   ├── prometheus-metric-examples.json # Expected Prometheus output
│   │   │   └── tempo-trace-examples.json  # Expected Tempo output
│   │   ├── console/
│   │   │   ├── console-info-log.txt       # Expected terminal INFO output
│   │   │   ├── console-error-log.txt      # Expected terminal ERROR output
│   │   │   └── console-transaction-log.txt # Expected terminal transaction output
│   │   ├── file/
│   │   │   ├── json-info-log.json         # Expected JSON file log (INFO)
│   │   │   ├── json-error-log.json        # Expected JSON file log (ERROR)
│   │   │   └── json-transaction-log.json  # Expected JSON file log (transaction)
│   │   └── grafana-dashboard-reference.txt # Expected Grafana dashboard output
│   └── test-contracts/
│       ├── 01-info-log.json               # Test definition for INFO log
│       ├── 02-error-log.json              # Test definition for ERROR log
│       ├── 03-transaction-log.json        # Test definition for transaction log
│       ├── 04-job-status.json             # Test definition for job status
│       ├── 05-job-progress.json           # Test definition for job progress
│       ├── test-validator.sh              # Language-agnostic validator script
│       └── README.md                      # How to run contract tests
├── python/
│   ├── src/
│   ├── test/
│   │   ├── contract/                      # Contract test runner
│   │   │   └── run-contracts.sh           # Calls test-validator.sh
│   │   └── e2e/full-stack-verification/
│   └── test-output/                       # Captured outputs for validation
│       ├── otlp/
│       ├── console/
│       └── file/
├── typescript/
│   ├── src/
│   ├── test/
│   │   ├── contract/                      # Contract test runner
│   │   │   └── run-contracts.sh           # Calls test-validator.sh
│   │   └── e2e/full-stack-verification/
│   └── test-output/                       # Captured outputs for validation
│       ├── otlp/
│       ├── console/
│       └── file/
└── [future-language]/
    ├── src/
    ├── test/
    │   ├── contract/                      # Contract test runner
    │   │   └── run-contracts.sh           # Calls test-validator.sh
    │   └── e2e/full-stack-verification/
    └── test-output/                       # Captured outputs for validation
        ├── otlp/
        ├── console/
        └── file/
```

## Critical Success Factors

### Must Have

#### 1. **Exact Field Names and Types**
No ambiguity about what fields exist and their format.

Example from `02-field-definitions.md`:
```markdown
| Field | Type | Source | Example | Notes |
|-------|------|--------|---------|-------|
| scope_name | string | service name from SYSTEM_ID | "sovdev-test-app" | NOT module name |
| scope_version | string | hardcoded "1.0.0" | "1.0.0" | Library version |
| observed_timestamp | string | nanoseconds since epoch | "1759826062404246784" | When log observed |
| responseJSON | string | JSON.stringify() or "null" | "null" or "{\"data\":...}" | ALWAYS present |
| exceptionType | string | always "Error" | "Error" | NOT language-specific (Python: not "Exception") |
| exceptionMessage | string | exception message | "HTTP 404:" | Standardized format |
| exceptionStack | string | full stack trace | "Traceback..." | Language-specific format acceptable |
```

#### 2. **Output Examples from Real Data**
Include actual output from all three logging destinations, not hand-written examples.

**A. OTLP Examples** (from Loki/Prometheus/Tempo queries)
```json
// examples/otlp/loki-log-examples.json
{
  "python_error_log": {
    "scope_name": "sovdev-test-company-lookup-python",
    "scope_version": "1.0.0",
    "observed_timestamp": "1759826062404246784",
    "responseJSON": "null",
    "exceptionType": "Error",
    "exceptionMessage": "HTTP 404:",
    "exceptionStack": "Traceback (most recent call last):\n  File..."
  },
  "typescript_error_log": {
    "scope_name": "sovdev-test-company-lookup-typescript",
    "scope_version": "1.0.0",
    "observed_timestamp": "1759825978898000000",
    "responseJSON": "null",
    "exceptionType": "Error",
    "exceptionMessage": "HTTP 404:",
    "exceptionStack": "Error: HTTP 404:\n    at IncomingMessage..."
  }
}
```

**B. Console Output Examples** (terminal/stdout)
```text
// examples/console/console-error-log.txt (Python)
2025-10-07 08:34:22 [ERROR] sovdev-test-company-lookup-python
  Function: lookupCompany
  Trace ID: 50ba0e1d-c46d-4dee-98d3-a0d3913f74ee
  Session ID: 18df09dd-c321-43d8-aa24-19dd7c149a56
  Error: HTTP 404:
  Stack: Traceback (most recent call last):
    File "/workspace/python/test/e2e/full-stack-verification/company-lookup.py", line 42, in fetch_company_data
      with urllib.request.urlopen(url) as response:
  ...
```

```text
// examples/console/console-error-log.txt (TypeScript)
2025-10-07 08:32:58 [ERROR] sovdev-test-company-lookup-typescript
  Function: lookupCompany
  Trace ID: c3d75d26-d783-48a2-96c3-1e62a37419c7
  Session ID: eb2f1cce-cfbe-4045-a6fd-c3f293174d66
  Error: HTTP 404:
  Stack: Error: HTTP 404:
    at IncomingMessage.<anonymous> (/workspace/typescript/test/e2e/full-stack-verification/company-lookup.ts:50:20)
  ...
```

**C. File JSON Examples** (dev.log file output)
```json
// examples/file/json-error-log.json (Python)
{
  "timestamp": "2025-10-07T08:34:22.398784+00:00",
  "level": "ERROR",
  "service": {
    "name": "sovdev-test-company-lookup-python",
    "version": "1.0.0"
  },
  "function": {
    "name": "lookupCompany"
  },
  "exception": {
    "type": "Error",
    "message": "HTTP 404:",
    "stack": "Traceback (most recent call last):\n  File..."
  },
  "traceId": "50ba0e1d-c46d-4dee-98d3-a0d3913f74ee",
  "sessionId": "18df09dd-c321-43d8-aa24-19dd7c149a56",
  "peer": {
    "service": "SYS1234567"
  },
  "input": {
    "organisasjonsnummer": "974652846"
  },
  "logType": "transaction"
}
```

**Why All Three Matter:**
- **OTLP**: Operators monitor in Grafana (production)
- **Console**: Developers debug locally (development)
- **File**: Log aggregation and archival (all environments)

All three outputs must be consistent in field names, values, and formatting.

#### 3. **Anti-Patterns Documented**
Explicit "DON'T do this" guidance.

Example from `08-anti-patterns.md`:
```markdown
# Anti-Patterns

## ❌ DON'T: Use module name for scope_name
**Python Bad Example:**
```python
logger = _logs.get_logger(__name__, "1.0.0")  # __name__ = "sovdev_logger.logger"
```

**Correct:**
```python
logger = _logs.get_logger(service_name, "1.0.0")  # service_name = "sovdev-test-app"
```

**Why:** Operators need to see service name, not internal module structure.
```

#### 4. **Version Specification Strategy**
How to handle spec evolution over time.

```markdown
# Versioning Strategy

## Specification Versioning
- Specification has version number: `spec-v1.0.0`
- Breaking changes increment major version
- New fields increment minor version
- Documentation updates increment patch version

## Implementation Compatibility
- Implementations declare which spec version they implement
- Test suite validates against spec version
- Backwards compatibility requirements documented
```

### Nice to Have

#### 1. **Decision Log**
Why specific choices were made.

```markdown
# Decision: Use "Error" for all exception types

**Date:** 2025-10-07
**Context:** Python uses "Exception", TypeScript uses "Error"
**Decision:** Standardize on "Error" for all languages
**Rationale:**
- Operators need consistent alert rules across languages
- "Error" is universally understood
- Language-specific details available in exceptionStack
**Alternatives Considered:**
- Keep language-specific types (rejected: inconsistent alerting)
- Use "Exception" for all (rejected: less familiar to JS/TS developers)
```

#### 2. **OpenTelemetry Compliance Matrix**
Which parts of OTLP spec we follow/diverge from.

#### 3. **Performance Requirements**
Max latency, memory usage, etc.

## Workflow for Adding New Language Implementation

### Step 1: LLM Reads Specification
```
Agent task:
"Read all files in /sovdev-logger/specification/ and understand the requirements
for implementing sovdev-logger in Go."
```

### Step 2: LLM Generates Implementation
```
Agent task:
"Generate a Go implementation of sovdev-logger that:
1. Matches the API contract in 01-api-contract.md
2. Produces output matching examples/log-examples.json
3. Follows the error handling patterns in 04-error-handling.md"
```

### Step 3: Copy E2E Test Structure
```bash
cp -r python/test/e2e/full-stack-verification go/test/e2e/full-stack-verification
# Update test code to call Go implementation
```

### Step 4: Run Tests and Compare Grafana Output
```bash
# Run Python test
cd python/test/e2e/full-stack-verification && ./run-test.sh

# Run Go test
cd go/test/e2e/full-stack-verification && ./run-test.sh

# Export Grafana dashboard (wait 30 seconds for logs to appear)
# Compare "Recent Errors" table - fields must match exactly
```

### Step 5: Iterate Until Tests Pass
- LLM reads test failures
- LLM updates implementation
- Repeat until Grafana output matches specification examples

## Maintenance Workflow: Adding New Feature

### Example: Adding `correlationId` field to all logs

#### Step 1: Update Specification
Update `02-field-definitions.md`:
```markdown
| correlationId | string | UUID v4 | "a1b2c3d4-..." | Links related operations |
```

Update `examples/log-examples.json`:
```json
{
  "python_info_log": {
    "correlationId": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
    ...
  }
}
```

#### Step 2: Run LLM Agent Per Language
```
For each language implementation:
1. "Read updated specification"
2. "Update implementation to include correlationId field"
3. "Update tests to verify correlationId presence"
```

#### Step 3: Verify with E2E Tests
```bash
# Run all language tests
./run-all-tests.sh

# Compare Grafana output
# All implementations must show correlationId field
```

#### Step 4: Update Documentation
```
Update 09-versioning-strategy.md:
- Spec version: v1.1.0 (new field = minor version bump)
- All implementations updated to spec-v1.1.0
```

## Benefits of This Approach

### 1. **Reduced Manual Porting Effort**
- LLM handles translation across languages
- Developer reviews output, not implementation details

### 2. **Consistent Behavior**
- Single source of truth prevents drift
- Tests verify behavior, not code structure

### 3. **Faster New Language Adoption**
- Go, Rust, Java implementations can be generated quickly
- LLM understands specification better than reading existing code

### 4. **Better Documentation**
- Specification forces clarity
- Examples from real output eliminate ambiguity

### 5. **Easier Onboarding**
- New developers read specification, not multiple codebases
- LLM can explain decisions via decision log

## Risks and Mitigations

### Risk 1: Specification Ambiguity
**Mitigation:** Use actual JSON examples, not just text descriptions

### Risk 2: Language-Specific Edge Cases
**Mitigation:** Document these explicitly in anti-patterns section

### Risk 3: Specification Becomes Outdated
**Mitigation:** Version specification, require implementations to declare compliance

### Risk 4: LLM Generates Incorrect Code
**Mitigation:** E2E tests are the final arbiter - if Grafana output matches, code is correct

## Language-Agnostic Testing Strategy

### The "Testing Tests" Problem

When maintaining a library across multiple languages, writing tests in each language's test framework introduces a critical issue:

**Problem:** Each language has its own testing ecosystem (pytest, Jest, Go testing, etc.). If we write tests in each language, we must trust that:
1. The tests themselves are correct
2. The tests are identical in behavior across languages
3. Test frameworks interpret assertions the same way

**This creates a "testing tests" problem** - who validates that the Python test matches the TypeScript test?

### Solution: Three-Level Language-Agnostic Testing

#### Level 1: Contract Tests (Language-Agnostic)

**Purpose:** Verify that implementations produce identical output for identical inputs.

**Approach:** JSON-based test contracts define inputs and expected outputs. A bash script validator compares actual output against golden files.

**Example Contract (`test-contracts/01-info-log.json`):**
```json
{
  "test_id": "01-info-log",
  "description": "Basic INFO log with all required fields",
  "input": {
    "level": "INFO",
    "functionName": "testFunction",
    "message": "Test message",
    "peerService": "test-peer-service"
  },
  "expected_fields": {
    "otlp": [
      "scope_name",
      "scope_version",
      "observed_timestamp",
      "severity_number",
      "severity_text",
      "functionName",
      "peer_service",
      "responseJSON",
      "service_name",
      "service_version"
    ],
    "console": [
      "timestamp_pattern",
      "level_pattern",
      "service_name",
      "function_name",
      "message"
    ],
    "file": [
      "timestamp",
      "level",
      "service.name",
      "service.version",
      "function.name",
      "peer.service",
      "logType"
    ]
  },
  "golden_files": {
    "otlp": "specification/examples/otlp/info-log.json",
    "console": "specification/examples/console/console-info-log.txt",
    "file": "specification/examples/file/json-info-log.json"
  }
}
```

**Validator Script (`test-contracts/test-validator.sh`):**
```bash
#!/bin/bash
# Language-agnostic validator - compares actual output with golden files

CONTRACT_FILE=$1
LANGUAGE=$2
OUTPUT_DIR="${LANGUAGE}/test-output"

# 1. Parse contract definition
TEST_ID=$(jq -r '.test_id' "$CONTRACT_FILE")
EXPECTED_OTLP_FIELDS=$(jq -r '.expected_fields.otlp[]' "$CONTRACT_FILE")

# 2. Validate OTLP output from Loki
ACTUAL_OTLP="${OUTPUT_DIR}/otlp/${TEST_ID}.json"
echo "Validating OTLP output: $ACTUAL_OTLP"

for field in $EXPECTED_OTLP_FIELDS; do
  if ! jq -e ".$field" "$ACTUAL_OTLP" > /dev/null; then
    echo "❌ FAIL: Missing field '$field' in OTLP output"
    exit 1
  fi
done

# 3. Validate console output format
ACTUAL_CONSOLE="${OUTPUT_DIR}/console/${TEST_ID}.txt"
CONSOLE_PATTERNS=$(jq -r '.expected_fields.console[]' "$CONTRACT_FILE")
# ... pattern matching validation ...

# 4. Validate file JSON output
ACTUAL_FILE="${OUTPUT_DIR}/file/${TEST_ID}.json"
# ... JSON schema validation ...

echo "✅ PASS: All outputs match specification"
```

**Benefits:**
- ✅ **No language-specific test code** - bash script validates all languages
- ✅ **Single source of truth** - contract JSON defines expected behavior
- ✅ **Golden file comparison** - exact match verification
- ✅ **No test drift** - all languages validated against same contracts

#### Level 2: Behavioral Tests (Minimal Language-Specific)

**Purpose:** Verify edge cases and error handling that can't be expressed in static contracts.

**Examples:**
- Invalid input rejection (e.g., null functionName)
- Exception handling behavior
- Resource cleanup on shutdown

**Approach:** Small, focused unit tests in each language to verify error paths. These are minimized to reduce drift risk.

#### Level 3: E2E Tests (Language-Agnostic)

**Purpose:** Verify end-to-end integration with OTLP backends (Loki/Prometheus/Tempo).

**Approach:** Query backends directly via kubectl/API, compare field-by-field. Already implemented in current E2E tests.

### Workflow: Running Contract Tests

**Per-Language Test Runner (`python/test/contract/run-contracts.sh`):**
```bash
#!/bin/bash
# Python contract test runner

CONTRACTS_DIR="../../specification/test-contracts"
OUTPUT_DIR="../test-output"

# 1. Run test application and capture outputs
python test-app.py > "$OUTPUT_DIR/console/01-info-log.txt"

# 2. Query Loki for OTLP output
kubectl exec -n monitoring deployment/loki-gateway -- \
  wget -qO- --post-data='...' http://localhost:3100/loki/api/v1/query \
  > "$OUTPUT_DIR/otlp/01-info-log.json"

# 3. Copy file log output
cp dev.log "$OUTPUT_DIR/file/01-info-log.json"

# 4. Run language-agnostic validator
for contract in "$CONTRACTS_DIR"/*.json; do
  bash "$CONTRACTS_DIR/test-validator.sh" "$contract" "python"
done
```

**Benefits:**
- ✅ **Each language just captures output** - no assertion logic
- ✅ **Validator script is shared** - guaranteed consistency
- ✅ **Easy to add new tests** - create contract JSON, validator handles all languages

### Why This Eliminates "Testing Tests" Problem

1. **Single Validator Implementation:** The bash validator script is the only test logic. It validates all languages identically.

2. **No Language-Specific Assertions:** Each language implementation just runs code and captures output. No test framework differences.

3. **Golden File Truth:** Specification examples become the ground truth. Validator compares actual vs. golden files using `diff` and `jq`.

4. **LLM-Friendly:** Contract JSON format is easy for LLMs to understand and generate new tests.

### Integration with Specification-Driven Development

**When adding new feature:**
1. Update specification documents (field definitions, API contract)
2. Update golden files in `specification/examples/`
3. Add new contract test in `specification/test-contracts/`
4. LLM generates implementation for each language
5. Run contract tests - validator ensures all languages produce identical output

**Result:** If contract tests pass, implementations are correct. No need to verify test logic across languages.

---

## Next Steps

### Phase 1: Foundation (Priority 1)
1. ✅ Create `/specification/` folder structure
2. Create `01-api-contract.md` - Define public API surface
3. Create `02-field-definitions.md` - Document all OTLP fields (from today's work)
4. Create `examples/log-examples.json` - Export actual Loki data
5. Create `06-test-scenarios.md` - Document E2E test requirements
6. Create `10-language-agnostic-testing.md` - Detailed testing strategy
7. Create `test-contracts/` folder with initial contract definitions
8. Create `test-contracts/test-validator.sh` - Language-agnostic validator script

### Phase 2: Validation (Priority 2)
9. Implement contract test runners for Python and TypeScript
10. Use specification to verify Python and TypeScript implementations match
11. Document any discovered inconsistencies
12. Add anti-patterns section based on bugs found today

### Phase 3: Proof of Concept (Priority 3)
13. Generate Go implementation using LLM + specification
14. Run contract tests to verify Go matches Python/TypeScript
15. Iterate until all contract tests pass

### Phase 4: Maturity (Future)
16. Add remaining specification documents (03-09)
17. Create decision log for key architectural choices
18. Document versioning strategy
19. Expand contract test coverage to all API functions

## Success Metrics

1. **Time to new language implementation** - Target: < 4 hours from spec to passing tests
2. **Behavioral consistency** - Target: 100% field parity in Grafana across languages
3. **Maintenance velocity** - Target: New feature propagated to all languages in < 2 hours
4. **Documentation quality** - Target: LLM can generate correct implementation without clarification questions

## Conclusion

This specification-first approach leverages LLMs' strength in pattern translation while using E2E tests as the ground truth. By focusing on observable behavior (Grafana output) rather than implementation details, we can maintain consistency across languages with less manual effort.

The key insight is: **If the specification is complete enough for an LLM to generate a correct implementation, it's complete enough for humans too.**

---

**Document Status:** Initial plan
**Last Updated:** 2025-10-07
**Next Review:** After Phase 1 completion
