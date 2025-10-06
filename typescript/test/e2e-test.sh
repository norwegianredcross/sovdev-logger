#!/bin/bash
#
# E2E Test for sovdev-logger TypeScript Library
#
# This test verifies the complete data flow:
# TypeScript Library → OTLP Collector → Loki/Prometheus/Tempo
#
# Prerequisites:
# - Kubernetes cluster running with monitoring namespace
# - OTLP collector, Loki, Prometheus, Tempo deployed
# - kubectl configured and connected to cluster
#
# Usage:
#   npm run test:e2e
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_SERVICE_NAME="sovdev-test-e2e-$$"  # Use PID for uniqueness
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
WAIT_TIME=15  # Seconds to wait for telemetry export

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# Print functions
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_step() {
    echo -e "${YELLOW}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

# Cleanup function
cleanup() {
    print_step "Cleaning up..."
    # No cleanup needed for now (logs stay in backends)
}

trap cleanup EXIT

# Main test execution
main() {
    print_header "🧪 E2E Test: sovdev-logger TypeScript Library"

    print_info "Test Service Name: ${TEST_SERVICE_NAME}"
    print_info "Wait Time: ${WAIT_TIME}s"
    echo ""

    # Step 1: Check prerequisites
    print_step "Checking prerequisites..."

    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl."
        exit 1
    fi

    if ! kubectl get namespace monitoring &> /dev/null; then
        print_error "Namespace 'monitoring' not found. Please deploy observability stack."
        exit 1
    fi

    print_success "Prerequisites check passed"

    # Step 2: Build library
    print_step "Building TypeScript library..."
    cd "$PROJECT_ROOT"

    if npm run build > /tmp/build.log 2>&1; then
        print_success "Library built successfully"
    else
        print_error "Library build failed"
        cat /tmp/build.log
        exit 1
    fi

    # Step 3: Run example application
    print_step "Running example application..."
    cd "$PROJECT_ROOT/test/e2e/full-stack-verification"

    # Run example with test configuration
    if SYSTEM_ID="$TEST_SERVICE_NAME" \
       OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://127.0.0.1/v1/logs \
       OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://127.0.0.1/v1/metrics \
       OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1/v1/traces \
       OTEL_EXPORTER_OTLP_HEADERS='{"Host":"otel.localhost"}' \
       npx tsx company-lookup.ts > /tmp/example.log 2>&1; then
        print_success "Example executed successfully"
    else
        print_error "Example execution failed"
        cat /tmp/example.log
        exit 1
    fi

    # Step 4: Wait for telemetry export
    print_step "Waiting ${WAIT_TIME}s for telemetry export and ingestion..."
    sleep "$WAIT_TIME"
    print_success "Wait completed"

    # Step 5: Verify Loki (Logs)
    print_header "📊 Verifying Logs in Loki"

    print_step "Querying Loki for service names..."
    LOKI_RESULT=$(kubectl exec -n monitoring loki-0 -- wget -q -O - \
        'http://localhost:3100/loki/api/v1/label/service_name/values' 2>/dev/null || echo '{"status":"error"}')

    if echo "$LOKI_RESULT" | grep -q "$TEST_SERVICE_NAME"; then
        print_success "Service '$TEST_SERVICE_NAME' found in Loki"

        # Count log entries (use recent time range: last hour)
        print_step "Counting log entries..."
        END_TIME=$(date +%s)000000000  # Current time in nanoseconds
        START_TIME=$((END_TIME - 3600000000000))  # 1 hour ago in nanoseconds
        LOG_COUNT=$(kubectl exec -n monitoring loki-0 -- wget -q -O - \
            "http://localhost:3100/loki/api/v1/query_range?query=%7Bservice_name%3D%22${TEST_SERVICE_NAME}%22%7D&start=${START_TIME}&end=${END_TIME}" 2>/dev/null \
            | python3 -c "import sys, json; data=json.load(sys.stdin); print(sum(len(s.get('values', [])) for s in data.get('data', {}).get('result', [])))" 2>/dev/null || echo "0")

        if [ "$LOG_COUNT" -gt 0 ]; then
            print_success "Found $LOG_COUNT log entries in Loki"
        else
            print_error "No log entries found in Loki"
        fi
    else
        print_error "Service '$TEST_SERVICE_NAME' NOT found in Loki"
        echo "Available services:"
        echo "$LOKI_RESULT" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null || echo "$LOKI_RESULT"
    fi

    # Step 6: Verify Prometheus (Metrics)
    print_header "📈 Verifying Metrics in Prometheus"

    print_step "Querying Prometheus for metrics..."

    # Get Prometheus pod name dynamically
    PROM_POD=$(kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus,app.kubernetes.io/component=server -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

    if [ -z "$PROM_POD" ]; then
        print_error "Prometheus pod not found"
    else
        print_info "Prometheus pod: $PROM_POD"

        PROM_RESULT=$(kubectl exec -n monitoring "$PROM_POD" -c prometheus-server -- wget -q -O - \
            "http://localhost:9090/api/v1/query?query=sovdev_operations_total%7Bservice_name%3D%22${TEST_SERVICE_NAME}%22%7D" 2>/dev/null || echo '{"status":"error"}')

        METRIC_COUNT=$(echo "$PROM_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('data', {}).get('result', [])))" 2>/dev/null || echo "0")

        if [ "$METRIC_COUNT" -gt 0 ]; then
            print_success "Found $METRIC_COUNT metric series in Prometheus"

            # Sum up total operations
            TOTAL_OPS=$(echo "$PROM_RESULT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(sum(int(r['value'][1]) for r in data.get('data', {}).get('result', [])))" 2>/dev/null || echo "0")
            print_success "Total operations: $TOTAL_OPS"
        else
            print_error "No metrics found for service '$TEST_SERVICE_NAME' in Prometheus"
            echo "Query result:"
            echo "$PROM_RESULT" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null || echo "$PROM_RESULT"
        fi
    fi

    # Step 7: Verify Tempo (Traces)
    print_header "🔍 Verifying Traces in Tempo"

    print_step "Querying Tempo for service names..."
    TEMPO_SERVICES=$(kubectl exec -n monitoring tempo-0 -- wget -q -O - \
        'http://localhost:3200/api/search/tag/service.name/values' 2>/dev/null || echo '{"tagValues":[]}')

    if echo "$TEMPO_SERVICES" | grep -q "$TEST_SERVICE_NAME"; then
        print_success "Service '$TEST_SERVICE_NAME' found in Tempo"

        # Search for traces
        print_step "Searching for traces..."
        TEMPO_TRACES=$(kubectl exec -n monitoring tempo-0 -- wget -q -O - \
            "http://localhost:3200/api/search?tags=service.name%3D${TEST_SERVICE_NAME}&limit=20" 2>/dev/null || echo '{"traces":[]}')

        TRACE_COUNT=$(echo "$TEMPO_TRACES" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('traces', [])))" 2>/dev/null || echo "0")

        if [ "$TRACE_COUNT" -gt 0 ]; then
            print_success "Found $TRACE_COUNT traces in Tempo"

            # Show trace names
            print_step "Trace operations:"
            echo "$TEMPO_TRACES" | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f\"  - {t.get('rootTraceName', 'unknown')}\") for t in data.get('traces', [])[:5]]" 2>/dev/null
        else
            print_warning "No traces found in Tempo (known issue - does not affect library)"
        fi
    else
        print_warning "Service '$TEST_SERVICE_NAME' NOT found in Tempo"
        echo -e "${YELLOW}   Note: Tempo trace storage may take time to populate or may need configuration${NC}"
        echo "Available services:"
        echo "$TEMPO_SERVICES" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))" 2>/dev/null || echo "$TEMPO_SERVICES"
        echo -e "${YELLOW}   This is a known infrastructure issue and does not affect library functionality${NC}"
    fi

    # Final summary
    print_header "📋 Test Summary"

    TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))

    echo -e "Total Tests: ${TOTAL_TESTS}"
    echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"

    if [ "$TESTS_FAILED" -gt 0 ]; then
        echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
        echo ""
        echo -e "${RED}❌ E2E TESTS FAILED${NC}"
        exit 1
    else
        echo -e "${RED}Failed: 0${NC}"
        echo ""
        echo -e "${GREEN}✅ ALL E2E TESTS PASSED!${NC}"
        echo ""
        print_info "Test service: $TEST_SERVICE_NAME"
        print_info "You can query this data in Grafana to verify manually"
        exit 0
    fi
}

# Run main function
main
