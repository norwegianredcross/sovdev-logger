#!/bin/bash

###############################################################################
# run-company-lookup.sh
#
# Purpose: Run company-lookup example test for a language implementation
#          Executes test/e2e/company-lookup/run-test.sh inside devcontainer
#          This runs the application and sends telemetry to OTLP endpoints
#          For complete E2E verification with backend queries, use run-company-lookup-validate.sh
#
# Usage:   ./run-company-lookup.sh <language>
# Example: ./run-company-lookup.sh python
#          ./run-company-lookup.sh typescript
#
# Requirements:
# - devcontainer-toolbox container must be running
# - Language implementation must have test/e2e/company-lookup/run-test.sh
#
# Exit codes:
# 0   = Test passed
# 1   = Test failed
# 2   = Usage error (missing parameter)
# 3   = Devcontainer not running
# 4   = Test script not found
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
TEST_PATH="test/e2e/company-lookup"
TEST_SCRIPT="run-test.sh"

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
    echo "This script runs the E2E test for a language implementation by executing:"
    echo "  cd /workspace/<language>/test/e2e/company-lookup && ./run-test.sh"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_devcontainer() {
    print_info "Checking if devcontainer is running..."

    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_error "Devcontainer '${CONTAINER_NAME}' is not running"
        echo ""
        echo "Start the devcontainer first:"
        echo "  docker start ${CONTAINER_NAME}"
        echo ""
        echo "Or create it if it doesn't exist:"
        echo "  docker run -d --name ${CONTAINER_NAME} -v \$(pwd):/workspace <image>"
        return 1
    fi

    print_success "Devcontainer '${CONTAINER_NAME}' is running"
    return 0
}

check_test_script_exists() {
    local language=$1
    local full_path="/workspace/${language}/${TEST_PATH}/${TEST_SCRIPT}"

    print_info "Checking if test script exists: ${full_path}"

    if ! docker exec "${CONTAINER_NAME}" bash -c "test -f ${full_path}"; then
        print_error "Test script not found: ${full_path}"
        echo ""
        echo "Expected file structure:"
        echo "  ${language}/"
        echo "  └── ${TEST_PATH}/"
        echo "      └── ${TEST_SCRIPT}"
        echo ""
        echo "See specification/06-test-scenarios.md for required structure"
        return 1
    fi

    print_success "Test script found"
    return 0
}

run_test() {
    local language=$1
    local test_dir="/workspace/${language}/${TEST_PATH}"

    print_info "Running company-lookup example for ${language}..."
    echo ""
    echo "═════════════════════════════════════════════════════════════════"
    echo "  Test: Company Lookup Example"
    echo "  Language: ${language}"
    echo "  Directory: ${test_dir}"
    echo "  Script: ./${TEST_SCRIPT}"
    echo "═════════════════════════════════════════════════════════════════"
    echo ""

    # Run the test and capture exit code
    # Note: We don't use 'set -e' here because we want to capture the exit code
    docker exec "${CONTAINER_NAME}" bash -c "cd ${test_dir} && ./${TEST_SCRIPT}"
    local exit_code=$?

    echo ""
    echo "═════════════════════════════════════════════════════════════════"

    if [ $exit_code -eq 0 ]; then
        print_success "Test PASSED for ${language}"
        return 0
    else
        print_error "Test FAILED for ${language} (exit code: ${exit_code})"
        return $exit_code
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

    print_info "Starting company-lookup example for ${language}"
    echo ""

    # Pre-flight checks
    if ! check_devcontainer; then
        exit 3
    fi

    if ! check_test_script_exists "${language}"; then
        exit 4
    fi

    echo ""

    # Run the test
    if run_test "${language}"; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
