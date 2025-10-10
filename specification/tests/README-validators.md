# Backend Response Validators

JSON Schema-based validators for verifying sovdev-logger compliance in backend systems (Loki, Prometheus, Tempo).

## Overview

These validators use **JSON Schema** (same approach as `log-entry-schema.json`) to ensure telemetry data in backend systems uses correct field naming (snake_case only) and contains all required fields.

**Pattern**:
- JSON Schema files define validation rules declaratively
- Python validators use `jsonschema` library (same as `validate-log-format.py`)
- Consistent, maintainable, industry-standard approach

## Available Validators

### validate-loki-response.py ✅ IMPLEMENTED

Validates Loki query responses using JSON Schema.

**Schema**: `specification/schemas/loki-response-schema.json`

**Usage:**
```bash
# From file
./query-loki.sh sovdev-test-app --json > /tmp/loki.json
python3 validate-loki-response.py /tmp/loki.json

# Piped from query (recommended)
./query-loki.sh sovdev-test-app --json | python3 validate-loki-response.py -

# JSON output for automation
./query-loki.sh sovdev-test-app --json | python3 validate-loki-response.py - --json
```

**Validation Checks:**
- ✅ Response structure (status, data, result)
- ✅ Stream labels: service_name, service_version
- ✅ Log fields: function_name, trace_id, event_id, log_type, message, etc.
- ✅ Forbidden patterns: camelCase (serviceName), dotted notation (service.name)
- ✅ Field naming: ONLY snake_case accepted

**Exit Codes:**
- 0: Validation passed
- 1: Validation failed
- 2: Usage error

**Example Output:**
```
✅ Found 1 log stream(s)
✅ Stream labels validated
✅ Validated 16 log entries
✅ No forbidden field patterns found (all snake_case)

✅ LOKI RESPONSE VALIDATION PASSED

Total streams: 1
Total logs: 16
Services: sovdev-test-company-lookup-typescript
Log types: {'transaction': 10, 'job.status': 2, 'job.progress': 4}
```

### validate-prometheus-response.py ⏳ TODO

Will validate Prometheus query responses for metric naming and labels.

**Planned Checks:**
- Metric naming conventions (snake_case)
- Required labels (service_name, etc.)
- Metric types and values

### validate-tempo-response.py ⏳ TODO

Will validate Tempo trace query responses for span attributes.

**Planned Checks:**
- Span attribute naming (snake_case)
- Required attributes (service.name → service_name)
- Trace structure

### validate-log-consistency.py ✅ IMPLEMENTED

Cross-validates that logs written to files match logs retrieved from Loki backend.

**Usage:**
```bash
# Compare file logs with Loki response
./query-loki.sh sovdev-test-app --json > /tmp/loki.json
python3 validate-log-consistency.py logs/dev.log /tmp/loki.json

# Piped from query (recommended)
./query-loki.sh sovdev-test-app --json | python3 validate-log-consistency.py logs/dev.log -

# JSON output for automation
./query-loki.sh sovdev-test-app --json | python3 validate-log-consistency.py logs/dev.log - --json
```

**Validation Checks:**
- ✅ Matches entries using trace_id + event_id as unique identifiers
- ✅ Compares critical fields: message, function_name, log_type, level
- ✅ Detects missing entries (in file but not Loki)
- ✅ Detects extra entries (in Loki but not file)
- ✅ Reports field mismatches with specific values

**Exit Codes:**
- 0: All logs match (consistency verified)
- 1: Mismatches found (logs don't match)
- 2: Usage error

**Example Output:**
```
✅ Read 16 log entries from file
✅ Read 16 log entries from Loki
✅ 16 entries match perfectly

✅ LOG CONSISTENCY VALIDATION PASSED

Total matches: 16
Total mismatches: 0
Missing in Loki: 0
Extra in Loki: 0
```

**Use Cases:**
- Verify OTLP export is working correctly
- Detect data loss during log transmission
- Ensure field transformations preserve data integrity
- Validate that file logs and backend logs are synchronized

## Integration with Test Scripts

These validators can be integrated into `run-company-lookup-validate.sh`:

```bash
# Validate Loki response structure
if query-loki.sh "${service_name}" --json | python3 validate-loki-response.py -; then
    print_success "Loki response validation PASSED"
else
    print_error "Loki response validation FAILED"
    exit 1
fi

# Validate log consistency (file vs Loki)
if query-loki.sh "${service_name}" --json | python3 validate-log-consistency.py logs/dev.log -; then
    print_success "Log consistency validation PASSED"
else
    print_error "Log consistency validation FAILED"
    exit 1
fi
```

**Complete Validation Pipeline:**
```bash
# 1. Validate file logs against schema
./validate-log-format.sh logs/dev.log || exit 1

# 2. Validate Loki response structure
./query-loki.sh sovdev-test-app --json | python3 validate-loki-response.py - || exit 1

# 3. Validate consistency between file and Loki
./query-loki.sh sovdev-test-app --json | python3 validate-log-consistency.py logs/dev.log - || exit 1

echo "✅ All validations passed"
```

## Benefits

- **Comprehensive**: Validates all required fields, not just a few
- **Reusable**: Single validator works across all test scenarios
- **Maintainable**: Easy to add new validation rules
- **Automatable**: JSON output mode for CI/CD pipelines
- **Clear Errors**: Specific error messages show exactly what's wrong

## Pattern

All validators follow the same pattern as `validate-log-format.py`:

1. Parse JSON input (file or stdin)
2. Validate structure
3. Check required fields
4. Check forbidden patterns (camelCase, dots)
5. Return exit code (0=pass, 1=fail)
6. Support --json mode for automation

## Related Documentation

- `specification/tools/run-company-lookup-validate.sh` - Uses validators
- `specification/tools/query-loki.sh` - Queries Loki for responses
- `specification/tools/query-prometheus.sh` - Queries Prometheus
- `specification/tools/query-tempo.sh` - Queries Tempo
- `specification/schemas/log-entry-schema.json` - File log schema
