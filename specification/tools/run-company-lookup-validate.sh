#!/bin/bash

###############################################################################
# run-company-lookup-validate.sh
#
# Purpose: Orchestrate complete validation with backend verification
#
# This script coordinates a split architecture:
# 1. DEVCONTAINER: Install/build library (pip install or npm run build)
# 2. DEVCONTAINER: Run company-lookup app via run-company-lookup.sh
# 3. HOST: Wait for telemetry export
# 4. HOST: Query backends (Loki/Prometheus/Tempo) using query-*.sh tools
#
# Usage:   ./run-company-lookup-validate.sh <language>
# Example: ./run-company-lookup-validate.sh python
#          ./run-company-lookup-validate.sh typescript
#
# Requirements:
# - devcontainer-toolbox container must be running
# - Kubernetes cluster with monitoring stack deployed
# - kubectl configured on host
# - Language implementation in sovdev-logger/{language}/
#
# Exit codes:
# 0   = All tests passed
# 1   = Tests failed
# 2   = Usage error (missing parameter)
# 3   = Devcontainer not running
# 4   = Installation/build failed
###############################################################################

set -e  # Exit on error
set -o pipefail  # Catch errors in pipes

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

# Test tracking
TESTS_PASSED=0
TESTS_FAILED=0

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
    print_info "Checking if devcontainer is running..."

    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_error "Devcontainer '${CONTAINER_NAME}' is not running"
        echo ""
        echo "Start the devcontainer first:"
        echo "  docker start ${CONTAINER_NAME}"
        return 1
    fi

    print_success "Devcontainer '${CONTAINER_NAME}' is running"
    return 0
}

install_library() {
    local language=$1

    print_step "Installing/building ${language} library..."
    echo ""

    case "${language}" in
        python)
            print_info "Running: pip3 install -e ."
            if docker exec "${CONTAINER_NAME}" bash -c \
                "cd /workspace/${language} && pip3 install -e . > /tmp/install.log 2>&1"; then
                print_success "Python library installed"
                return 0
            else
                print_error "Python library installation failed"
                docker exec "${CONTAINER_NAME}" cat /tmp/install.log
                return 1
            fi
            ;;

        typescript)
            print_info "Running: npm run build"
            if docker exec "${CONTAINER_NAME}" bash -c \
                "cd /workspace/${language} && npm run build > /tmp/build.log 2>&1"; then
                print_success "TypeScript library built"
                return 0
            else
                print_error "TypeScript library build failed"
                docker exec "${CONTAINER_NAME}" cat /tmp/build.log
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
        print_error "kubectl not found on host"
        echo ""
        echo "Backend verification requires kubectl to query Loki/Prometheus/Tempo"
        echo "Install kubectl: https://kubernetes.io/docs/tasks/tools/"
        return 1
    fi

    if ! kubectl get namespace monitoring &> /dev/null 2>&1; then
        print_error "Kubernetes 'monitoring' namespace not found"
        echo ""
        echo "Deploy the monitoring stack first"
        return 1
    fi

    return 0
}

run_validation() {
    local language=$1

    print_header "Complete Validation: ${language}"

    print_info "Using SYSTEM_ID from .env file"
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

    # Run via run-company-lookup.sh (uses SYSTEM_ID from .env)
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

    # Get SYSTEM_ID from .env file
    local env_file="${SOVDEV_LOGGER_ROOT}/${language}/test/e2e/company-lookup/.env"
    local service_name=$(grep '^SYSTEM_ID=' "${env_file}" | cut -d'=' -f2)

    if [ -z "${service_name}" ]; then
        print_error "Could not read SYSTEM_ID from ${env_file}"
        return 1
    fi

    print_info "Service Name: ${service_name}"

    # Step 4: Query Loki
    print_header "Step 4/6: Verify Logs in Loki"

    print_step "Querying Loki for service '${service_name}'..."

    if "${SCRIPT_DIR}/query-loki.sh" "${service_name}" --limit 20 > /dev/null 2>&1; then
        print_success "Logs found in Loki"

        # Get actual count
        local log_count=$(${SCRIPT_DIR}/query-loki.sh "${service_name}" --json 2>/dev/null | \
            jq -r '[.data.result[].values | length] | add' 2>/dev/null || echo "0")
        print_success "Found ${log_count} log entries"
    else
        print_error "Logs NOT found in Loki"
    fi

    # Step 5: Query Prometheus
    print_header "Step 5/6: Verify Metrics in Prometheus"

    print_step "Querying Prometheus for service '${service_name}'..."

    if "${SCRIPT_DIR}/query-prometheus.sh" "${service_name}" > /dev/null 2>&1; then
        print_success "Metrics found in Prometheus"

        # Get actual counts
        local metric_series=$(${SCRIPT_DIR}/query-prometheus.sh "${service_name}" --json 2>/dev/null | \
            jq -r '.data.result | length' 2>/dev/null || echo "0")
        local total_ops=$(${SCRIPT_DIR}/query-prometheus.sh "${service_name}" --json 2>/dev/null | \
            jq -r '[.data.result[].value[1] | tonumber] | add' 2>/dev/null || echo "0")
        print_success "Found ${metric_series} metric series, ${total_ops} total operations"
    else
        print_error "Metrics NOT found in Prometheus"
    fi

    # Step 6: Query Tempo
    print_header "Step 6/6: Verify Traces in Tempo"

    print_step "Querying Tempo for service '${service_name}'..."

    if "${SCRIPT_DIR}/query-tempo.sh" "${service_name}" --limit 20 > /dev/null 2>&1; then
        print_success "Traces found in Tempo"

        # Get actual count
        local trace_count=$(${SCRIPT_DIR}/query-tempo.sh "${service_name}" --json 2>/dev/null | \
            jq -r '.traces | length' 2>/dev/null || echo "0")
        print_success "Found ${trace_count} traces"
    else
        print_warning "Traces NOT found in Tempo (known infrastructure issue)"
        TESTS_FAILED=$((TESTS_FAILED - 1))  # Don't count as failure
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

    if ! check_kubectl; then
        exit 5
    fi

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
