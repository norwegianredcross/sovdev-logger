# Complete Validation Workflow

This document describes the complete 3-layer validation approach for sovdev-logger.

## Validation Layers

### Layer 1: File Log Validation ✅
**Tool**: `validate-log-format.sh`
**What it validates**: Logs written to files against JSON Schema
**Purpose**: Ensures application writes correct field names (snake_case only)

```bash
# Validate dev.log
./validate-log-format.sh logs/dev.log

# Result: Validates field naming, required fields, forbidden patterns
```

### Layer 2: Backend Response Validation ✅
**Tool**: `validate-loki-response.py`
**What it validates**: Loki API response structure and log entries
**Purpose**: Ensures backend stores logs with correct field names

```bash
# Validate Loki response structure
./query-loki.sh sovdev-test-app --json | python3 validate-loki-response.py -

# Result: Validates response structure, stream labels, log entry fields
```

### Layer 3: Cross-Validation ✅ NEW
**Tool**: `validate-log-consistency.py`
**What it validates**: File logs match backend logs
**Purpose**: Ensures data consistency between file logging and OTLP export

```bash
# Validate file logs match Loki logs
./query-loki.sh sovdev-test-app --json | python3 validate-log-consistency.py logs/dev.log -

# Result: Compares entries, detects mismatches, missing, or extra logs
```

## Complete Validation Pipeline

```bash
#!/bin/bash
# Complete validation for TypeScript implementation

set -e

SERVICE_NAME="sovdev-test-company-lookup-typescript"
LOG_FILE="logs/dev.log"

echo "=== Layer 1: File Log Validation ==="
if ./validate-log-format.sh "${LOG_FILE}"; then
    echo "✅ File logs validated"
else
    echo "❌ File log validation FAILED"
    exit 1
fi

echo ""
echo "=== Layer 2: Backend Response Validation ==="
if ./query-loki.sh "${SERVICE_NAME}" --json | python3 validate-loki-response.py -; then
    echo "✅ Loki response validated"
else
    echo "❌ Loki response validation FAILED"
    exit 1
fi

echo ""
echo "=== Layer 3: Cross-Validation ==="
if ./query-loki.sh "${SERVICE_NAME}" --json | python3 validate-log-consistency.py "${LOG_FILE}" -; then
    echo "✅ Log consistency validated"
else
    echo "❌ Log consistency validation FAILED"
    exit 1
fi

echo ""
echo "✅✅✅ ALL VALIDATIONS PASSED ✅✅✅"
```

## What Each Layer Catches

### Layer 1 Catches:
- ❌ Wrong field names (camelCase, dotted notation)
- ❌ Missing required fields
- ❌ Invalid field types
- ❌ Extra/unknown fields

### Layer 2 Catches:
- ❌ Backend storing logs with wrong field names
- ❌ Stream labels using camelCase
- ❌ Response structure issues
- ❌ Invalid log entry format

### Layer 3 Catches:
- ❌ Data loss during OTLP transmission
- ❌ Field transformation errors
- ❌ Logs in file but not in backend
- ❌ Field value mismatches (e.g., level changed)
- ❌ Extra logs in backend (from previous runs)

## Integration with Developer Workflow

### TypeScript Developers
Add to `package.json`:
```json
{
  "scripts": {
    "test": "npm run test:unit",
    "test:full": "bash -c 'rm -rf logs/*.log && npx tsx company-lookup.ts && ./validate-log-format.sh logs/dev.log && ./validate-log-format.sh logs/error.log'"
  }
}
```

### Python Developers
Add to test script:
```bash
# Clean, run, validate
rm -rf logs/*.log
python3 company-lookup.py
./validate-log-format.sh logs/dev.log
```

### E2E Validation (with Kubernetes cluster)
```bash
# Run application
./run-company-lookup.sh typescript

# Wait for logs to propagate to Loki (5-10 seconds)
sleep 10

# Full validation
./validate-log-format.sh logs/dev.log
./query-loki.sh sovdev-test-app --json | python3 validate-loki-response.py -
./query-loki.sh sovdev-test-app --json | python3 validate-log-consistency.py logs/dev.log -
```

## Exit Codes

All validators use consistent exit codes:
- **0**: Validation passed
- **1**: Validation failed
- **2**: Usage error (missing files, invalid JSON, etc.)

This enables CI/CD integration:
```bash
./validate-log-format.sh logs/dev.log || exit 1
./query-loki.sh app --json | python3 validate-loki-response.py - || exit 1
./query-loki.sh app --json | python3 validate-log-consistency.py logs/dev.log - || exit 1
```

## Benefits

1. **Comprehensive**: Validates entire pipeline from code → file → OTLP → backend
2. **Fast Feedback**: Developers get immediate validation results
3. **Prevents Regressions**: Catches field naming issues before they reach production
4. **CI/CD Ready**: Proper exit codes enable automated testing
5. **Clear Errors**: Specific error messages show exactly what's wrong
6. **Consistent**: All validators use JSON Schema approach
7. **Automatable**: JSON output mode for integration with other tools

## Testing the Validators

All validators are tested and working:

```bash
# Test Layer 1
./validate-log-format.sh logs/dev.log
# ✅ Result: 16/16 logs validated

# Test Layer 2
./query-loki.sh sovdev-test-app --json | python3 validate-loki-response.py -
# ✅ Result: Schema validation passed, 16 entries

# Test Layer 3
./query-loki.sh sovdev-test-app --json | python3 validate-log-consistency.py logs/dev.log -
# ✅ Result: 16 matches, 0 mismatches, 0 missing
```

## Next Steps

1. ✅ **COMPLETED**: File log validation (validate-log-format.sh)
2. ✅ **COMPLETED**: Loki response validation (validate-loki-response.py)
3. ✅ **COMPLETED**: Cross-validation (validate-log-consistency.py)
4. ⏳ **TODO**: Integrate into run-company-lookup-validate.sh
5. ⏳ **TODO**: Create validate-prometheus-response.py (metrics validation)
6. ⏳ **TODO**: Create validate-tempo-response.py (trace validation)
