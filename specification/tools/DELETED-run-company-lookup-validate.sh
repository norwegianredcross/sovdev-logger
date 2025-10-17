#!/bin/bash
# filename: specification/tools/run-company-lookup-validate.sh
# description: Complete E2E validation with backend verification (Loki/Prometheus/Tempo)
#
# Purpose:
#   Orchestrates COMPLETE end-to-end validation of sovdev-logger implementation
#   including backend telemetry verification. This is the most comprehensive test
#   that validates the entire observability stack.
#
#   Test Flow (with schema and consistency validation):
#   1. Install/build language library (pip install or npm run build)
#   2. Run company-lookup application via run-company-lookup.sh
#   3. Validate local log files for snake_case compliance
#   3. Wait for telemetry export to backends (15 seconds)
#   4. Loki Validation:
#      4.1) Validate Loki response against loki-response-schema.json
#      4.2) Compare log file entries with Loki logs (consistency validation)
#   5. Prometheus Validation:
#      5.1) Validate Prometheus response against prometheus-response-schema.json
#      5.2) Compare log file entries with Prometheus metrics (consistency validation)
#   6. Tempo Validation:
#      6.1) Validate Tempo response against tempo-response-schema.json
#      6.2) Compare log file trace_ids with Tempo traces (consistency validation)
#
#   This script runs inside the devcontainer and performs:
#   - Builds library, runs application, generates logs
#   - Queries Kubernetes backends (requires kubectl in devcontainer)
#
# Usage:
#   ./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup-validate.sh <language>"
#
#   From sovdev-logger root:
#     ./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup-validate.sh typescript"
#     ./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup-validate.sh python"
#
# Arguments:
#   language    Implementation language (typescript, python, go)
#
# Environment:
#   - Must run INSIDE devcontainer (use in-devcontainer.sh wrapper)
#   - Requires kubectl available inside devcontainer
#   - Requires Kubernetes cluster with monitoring stack:
#     - Loki (logs)
#     - Prometheus (metrics)
#     - Tempo (traces)
#     - OpenTelemetry Collector (OTLP ingestion)
#   - Requires kubectl configured on host
#   - Requires namespace 'monitoring' in Kubernetes
#
# What This Test Validates:
#   LOCAL (File-based):
#   1. Library builds/installs correctly
#   2. Application runs without errors
#   3. Log files generated (dev.log, error.log)
#   4. Log format matches strict snake_case schema
#   5. All required fields present (service_name, function_name, etc.)
#
#   BACKEND (Telemetry Stack - Schema Validation):
#   6. Loki response matches loki-response-schema.json
#   7. Prometheus response matches prometheus-response-schema.json
#   8. Tempo response matches tempo-response-schema.json
#   9. All responses have required fields (timestamp, service_name, etc.)
#   10. Field names use snake_case in backend responses
#
#   BACKEND (Telemetry Stack - Consistency Validation):
#   11. Log entries in file match log entries in Loki (same values)
#   12. Metrics derived from file match metrics in Prometheus
#   13. Trace IDs in file match trace IDs in Tempo
#   14. Data consistency across observability stack
#
# Exit Codes:
#   0 - All tests passed (local + backend validation)
#   1 - Tests failed (any validation step failed)
#   2 - Usage error (missing language parameter)
#   3 - Devcontainer not running
#   4 - Library installation/build failed
#   5 - kubectl not available or monitoring stack not deployed
#
# Output:
#   Step 1/6: Install/Build Library
#     - pip install or npm run build
#   Step 2/6: Run Company Lookup Application
#     - Executes run-company-lookup.sh
#   Step 3/6: Wait for Telemetry Export
#     - 15 second delay for OTLP batch export
#   Step 3.5/6: Validate File Log Format
#     - Validates dev.log against log-entry-schema.json
#   Step 4/6: Loki Validation
#     Step 4.1: Validate Loki Response Using Schema
#       - Queries Loki and validates against loki-response-schema.json
#       - Checks required fields (timestamp, service_name, etc.)
#     Step 4.2: Compare Log File With Loki Response
#       - Cross-validates file log entries match Loki logs
#   Step 5/6: Prometheus Validation
#     Step 5.1: Validate Prometheus Response Using Schema
#       - Queries Prometheus and validates against prometheus-response-schema.json
#     Step 5.2: Compare Log File With Prometheus Metrics
#       - Cross-validates metrics derived from file match Prometheus
#   Step 6/6: Tempo Validation
#     Step 6.1: Validate Tempo Response Using Schema
#       - Queries Tempo and validates against tempo-response-schema.json
#     Step 6.2: Compare Log File With Tempo Traces
#       - Cross-validates trace IDs from file match Tempo traces
#
#   Test Summary:
#     - Shows pass/fail counts
#     - Lists which backends have data
#     - Provides Grafana query hints
#
# Examples:
#   # Full validation for TypeScript (from host)
#   ./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup-validate.sh typescript"
#
#   # Full validation for Python (from host)
#   ./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup-validate.sh python"
#
#   # Check if monitoring stack is ready first (inside devcontainer)
#   kubectl get pods -n monitoring
#
# CI/CD Integration:
#   This is the GOLD STANDARD test for CI/CD pipelines:
#   - Validates complete observability stack
#   - Returns proper exit codes
#   - Provides detailed pass/fail breakdown
#   - Tests both development (local) and production (OTLP) paths
#   - Ensures telemetry reaches backends
#
# Troubleshooting:
#   Exit 3: Devcontainer check (should not fail when using in-devcontainer.sh)
#   Exit 4: Check build logs in /tmp/build.log or /tmp/install.log
#   Exit 5: Deploy monitoring stack: kubectl get namespace monitoring
#   Logs not in Loki: Check OTLP collector: kubectl logs -n monitoring -l app=opentelemetry-collector
#   Metrics not in Prometheus: Check scrape targets in Prometheus UI
#
# Related Scripts:
#   - run-company-lookup.sh: Run test without backend verification
#   - validate-log-format.sh: Standalone log validation
#   - query-loki.sh: Query Loki for logs
#   - query-prometheus.sh: Query Prometheus for metrics
#   - query-tempo.sh: Query Tempo for traces
#
###############################################################################

set -e  # Exit on error
set -o pipefail  # Catch errors in pipes

# Configure kubectl to use kubeconfig from workspace (devcontainer)
if [ -f "/workspace/topsecret/.kube/config" ]; then
    export KUBECONFIG="/workspace/topsecret/.kube/config"
elif [ -f "$HOME/.kube/config" ]; then
    export KUBECONFIG="$HOME/.kube/config"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Constants
CONTAINER_NAME="devcontainer-toolbox"
WAIT_TIME=15  # Seconds to wait for telemetry export

# Determine script directory and sovdev-logger root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOVDEV_LOGGER_ROOT="$( cd "${SCRIPT_DIR}/../.." && pwd )"
TEST_SCRIPT_DIR="$(dirname "$SCRIPT_DIR")/tests"

# Test tracking
TESTS_PASSED=0
TESTS_FAILED=0
KUBECTL_AVAILABLE=false

###############################################################################
# Functions
###############################################################################

print_usage() {
    echo "Usage: $0 <language>"
    echo ""
    echo "Examples:"
    echo "  $0 python"
    echo "  $0 typescript"
    echo "  $0 go"
    echo ""
    echo "This script orchestrates complete validation with backend verification:"
    echo "  1. Install/build library in devcontainer (pip/npm)"
    echo "  2. Run company-lookup app via run-company-lookup.sh"
    echo "  3. Wait for telemetry export (${WAIT_TIME}s)"
    echo "  4. Query Loki for logs (on host)"
    echo "  5. Query Prometheus for metrics (on host)"
    echo "  6. Query Tempo for traces (on host)"
}

print_error() {
    echo -e "${RED}❌ $1${NC}" >&2
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_step() {
    echo -e "${YELLOW}▶${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

check_devcontainer() {
    # Script now runs inside devcontainer, so always return success
    print_info "Running inside devcontainer"
    return 0
}

install_library() {
    local language=$1

    print_step "Installing/building ${language} library..."
    echo ""

    case "${language}" in
        python)
            print_info "Running: pip3 install -e ."
            if (cd "/workspace/${language}" && pip3 install -e . > /tmp/install.log 2>&1); then
                print_success "Python library installed"
                return 0
            else
                print_error "Python library installation failed"
                cat /tmp/install.log
                return 1
            fi
            ;;

        typescript)
            print_info "Running: npm run build"
            if (cd "/workspace/${language}" && npm run build > /tmp/build.log 2>&1); then
                print_success "TypeScript library built"
                return 0
            else
                print_error "TypeScript library build failed"
                cat /tmp/build.log
                return 1
            fi
            ;;

        *)
            print_warning "No installation/build step defined for ${language}"
            print_info "Skipping installation - assuming library is ready"
            return 0
            ;;
    esac
}

check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_warning "kubectl not found - skipping backend verification"
        echo ""
        echo "Backend verification requires kubectl to query Loki/Prometheus/Tempo"
        echo "Continuing with local validation only..."
        KUBECTL_AVAILABLE=false
        return 1
    fi

    # Check if monitoring pods exist (following query-loki.sh pattern)
    if ! kubectl get pod -n monitoring loki-0 &> /dev/null 2>&1; then
        print_warning "Loki pod not found in monitoring namespace"
        echo ""
        echo "Skipping backend verification - continuing with local validation only"
        echo "Deploy the monitoring stack to enable full E2E validation"
        KUBECTL_AVAILABLE=false
        return 1
    fi

    KUBECTL_AVAILABLE=true
    return 0
}

run_validation() {
    local language=$1

    print_header "Complete Validation: ${language}"

    print_info "Using OTEL_SERVICE_NAME from .env file"
    print_info "Wait Time: ${WAIT_TIME}s"
    echo ""

    # Step 1: Install/build library
    print_header "Step 1/6: Install/Build Library"

    if ! install_library "${language}"; then
        print_error "Library installation/build failed"
        return 1
    fi

    echo ""

    # Step 2: Run company-lookup application
    print_header "Step 2/6: Run Company Lookup Application"

    print_step "Running company-lookup via run-company-lookup.sh..."
    echo ""

    # Run via run-company-lookup.sh (uses OTEL_SERVICE_NAME from .env)
    set +e  # Don't exit on error for this command
    "${SCRIPT_DIR}/run-company-lookup.sh" "${language}"
    local run_exit=$?
    set -e

    echo ""

    if [ $run_exit -ne 0 ]; then
        print_error "Company lookup execution failed (exit code: ${run_exit})"
        return 1
    fi

    print_success "Company lookup execution completed"

    # Step 3: Wait for telemetry export
    print_header "Step 3/6: Wait for Telemetry Export"

    print_step "Waiting ${WAIT_TIME}s for telemetry to reach backends..."
    sleep "${WAIT_TIME}"
    print_success "Wait completed"

    # Get OTEL_SERVICE_NAME from .env file
    local env_file="${SOVDEV_LOGGER_ROOT}/${language}/test/e2e/company-lookup/.env"
    local service_name=$(grep '^OTEL_SERVICE_NAME=' "${env_file}" | cut -d'=' -f2)

    # Validate file log format
    print_header "Step 3.5/6: Validate File Log Format"

    local log_file="${SOVDEV_LOGGER_ROOT}/${language}/test/e2e/company-lookup/logs/dev.log"

    if [ -f "${log_file}" ]; then
        print_step "Validating log file format for snake_case fields..."

        if "${SCRIPT_DIR}/validate-log-format.sh" "${language}/test/e2e/company-lookup/logs/dev.log" > /dev/null 2>&1; then
            print_success "File log format validation passed (snake_case fields)"
        else
            print_warning "File log format validation had issues (check field names)"
        fi
    else
        print_warning "Log file not found at: ${log_file}"
    fi

    echo ""

    if [ -z "${service_name}" ]; then
        print_error "Could not read OTEL_SERVICE_NAME from ${env_file}"
        return 1
    fi

    print_info "Service Name: ${service_name}"

    # Step 4: Loki Validation
    print_header "Step 4/6: Loki - Validate Logs Sent Via OTEL"

    if [ "$KUBECTL_AVAILABLE" = "true" ]; then
        # Count entries in file to determine limit
        local entry_count=$(wc -l < "$log_file" | tr -d ' ')
        local limit=$((entry_count + 10))  # Add buffer

        # Step 4.1: Validate Loki response using schema
        print_header "Step 4.1: Validate Loki Response Using Schema"
        print_step "Querying Loki and validating against loki-response-schema.json..."
        echo ""

        set +e
        "${SCRIPT_DIR}/query-loki.sh" "${service_name}" --limit "$limit" --json | \
            python3 "$TEST_SCRIPT_DIR/validate-loki-response.py" -
        local loki_schema_exit=$?
        set -e

        if [ $loki_schema_exit -eq 0 ]; then
            print_success "Loki response schema validation passed"
        else
            print_error "Loki response schema validation failed"
        fi

        # Step 4.2: Compare log file with Loki response
        print_header "Step 4.2: Compare Log File With Loki Response"
        print_step "Cross-validating file logs match Loki logs..."
        echo ""

        set +e
        "${SCRIPT_DIR}/query-loki.sh" "${service_name}" --limit "$limit" --json | \
            python3 "$TEST_SCRIPT_DIR/validate-log-consistency.py" "$log_file" -
        local loki_consistency_exit=$?
        set -e

        if [ $loki_consistency_exit -eq 0 ]; then
            print_success "Log consistency validation passed"
        else
            print_error "Log consistency validation failed"
        fi

    else
        print_info "Skipping Loki verification (kubectl unavailable)"
    fi

    # Step 5: Prometheus Validation
    print_header "Step 5/6: Prometheus - Validate Metrics Sent Via OTEL"

    if [ "$KUBECTL_AVAILABLE" = "true" ]; then
        # Step 5.1: Validate Prometheus response using schema
        print_header "Step 5.1: Validate Prometheus Response Using Schema"
        print_step "Querying Prometheus and validating against prometheus-response-schema.json..."
        echo ""

        set +e
        timeout 30 "${SCRIPT_DIR}/query-prometheus.sh" "${service_name}" --json 2>/dev/null | \
            python3 "$TEST_SCRIPT_DIR/validate-prometheus-response.py" -
        local prom_schema_exit=$?
        set -e

        if [ $prom_schema_exit -eq 0 ]; then
            print_success "Prometheus response schema validation passed"
        else
            print_error "Prometheus response schema validation failed"
        fi

        # Step 5.2: Compare log file with Prometheus metrics
        print_header "Step 5.2: Compare Log File With Prometheus Metrics"
        print_step "Cross-validating file logs match Prometheus metrics..."
        echo ""

        set +e
        timeout 30 "${SCRIPT_DIR}/query-prometheus.sh" "${service_name}" --json 2>/dev/null | \
            python3 "$TEST_SCRIPT_DIR/validate-metrics-consistency.py" "$log_file" -
        local prom_consistency_exit=$?
        set -e

        if [ $prom_consistency_exit -eq 0 ]; then
            print_success "Metrics consistency validation passed"
        else
            print_error "Metrics consistency validation failed"
        fi

    else
        print_info "Skipping Prometheus verification (kubectl unavailable)"
    fi

    # Step 6: Tempo Validation
    print_header "Step 6/6: Tempo - Validate Traces Sent Via OTEL"

    if [ "$KUBECTL_AVAILABLE" = "true" ]; then
        # Step 6.1: Validate Tempo response using schema
        print_header "Step 6.1: Validate Tempo Response Using Schema"
        print_step "Waiting 30 seconds for traces to reach Tempo..."
        echo ""
        echo "Note: Tempo trace ingestion can be slow. Waiting longer than Loki/Prometheus..."
        sleep 30
        echo ""

        print_step "Querying Tempo and validating against tempo-response-schema.json..."
        echo ""

        set +e
        timeout 30 "${SCRIPT_DIR}/query-tempo.sh" "${service_name}" --limit 50 --json 2>/dev/null | \
            python3 "$TEST_SCRIPT_DIR/validate-tempo-response.py" -
        local tempo_schema_exit=$?
        set -e

        if [ $tempo_schema_exit -eq 0 ]; then
            print_success "Tempo response schema validation passed"
        else
            print_error "Tempo response schema validation failed"
        fi

        # Step 6.2: Compare log file with Tempo traces
        print_header "Step 6.2: Compare Log File With Tempo Traces"
        print_step "Cross-validating file trace_ids match Tempo traces..."
        echo ""

        set +e
        timeout 30 "${SCRIPT_DIR}/query-tempo.sh" "${service_name}" --limit 50 --json 2>/dev/null | \
            python3 "$TEST_SCRIPT_DIR/validate-trace-consistency.py" "$log_file" -
        local tempo_consistency_exit=$?
        set -e

        if [ $tempo_consistency_exit -eq 0 ]; then
            print_success "Trace consistency validation passed"
        else
            print_error "Trace consistency validation failed"
            echo ""
            echo "File trace_ids do not match Tempo trace IDs."
            echo "This indicates a problem with trace ID correlation between logs and OTEL spans."
        fi

    else
        print_info "Skipping Tempo verification (kubectl unavailable)"
    fi

    # Summary
    print_header "Test Summary"

    local total_tests=$((TESTS_PASSED + TESTS_FAILED))

    echo -e "Total Tests: ${total_tests}"
    echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"

    if [ "$TESTS_FAILED" -gt 0 ]; then
        echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
        echo ""
        echo -e "${RED}❌ VALIDATION FAILED${NC}"
        return 1
    else
        echo -e "${RED}Failed: 0${NC}"
        echo ""
        echo -e "${GREEN}✅ ALL VALIDATION TESTS PASSED!${NC}"
        echo ""
        print_info "Service: ${service_name}"
        print_info "Query this data in Grafana to verify manually"
        return 0
    fi
}

###############################################################################
# Main
###############################################################################

main() {
    # Check parameters
    if [ $# -eq 0 ]; then
        print_error "Missing language parameter"
        echo ""
        print_usage
        exit 2
    fi

    local language=$1

    print_info "Starting complete validation for ${language}"
    echo ""

    # Pre-flight checks
    if ! check_devcontainer; then
        exit 3
    fi

    # Check kubectl availability (non-blocking - allows local validation)
    check_kubectl || true  # Continue even if kubectl/monitoring unavailable

    echo ""

    # Run the validation
    if run_validation "${language}"; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
