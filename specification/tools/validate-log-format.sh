#!/bin/bash

###############################################################################
# validate-log-format.sh
#
# Purpose: Validate sovdev-logger log file format against specification
#
# This script can run:
# 1. From HOST: Connects to devcontainer and runs Python validator
# 2. Inside DEVCONTAINER: Directly runs Python validator
#
# Usage:   ./validate-log-format.sh <log-file-path> [options]
# Example: ./validate-log-format.sh python/test/.../logs/dev.log
#          ./validate-log-format.sh python/test/.../logs/error.log --error-log
#          ./validate-log-format.sh python/test/.../logs/dev.log --json
#
# Validation checks:
# - JSON Schema compliance (all required fields, correct types)
# - sessionId consistency (same across all logs)
# - responseJSON/inputJSON always present
# - exceptionType is "Error" for cross-language consistency
# - stackTrace limited to 350 characters
# - error.log contains only ERROR severity logs
#
# Exit codes:
# 0   = Validation passed
# 1   = Validation failed
# 2   = Usage error (missing parameter)
# 3   = Devcontainer not running (when run from host)
# 4   = Log file not found
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
VALIDATOR_SCRIPT="/workspace/specification/tests/validate-log-format.py"

# Determine script directory and sovdev-logger root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOVDEV_LOGGER_ROOT="$( cd "${SCRIPT_DIR}/../.." && pwd )"

###############################################################################
# Functions
###############################################################################

print_usage() {
    echo "Usage: $0 <log-file-path> [options]"
    echo ""
    echo "Arguments:"
    echo "  log-file-path    Path to log file (relative to sovdev-logger root)"
    echo ""
    echo "Options:"
    echo "  --json           Output JSON format for automation"
    echo "  --error-log      Validate as error.log (ERROR logs only)"
    echo "  --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 python/test/e2e/company-lookup/logs/dev.log"
    echo "  $0 python/test/e2e/company-lookup/logs/error.log --error-log"
    echo "  $0 typescript/test/e2e/company-lookup/logs/dev.log --json"
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

check_devcontainer() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_error "Devcontainer '${CONTAINER_NAME}' is not running"
        echo ""
        echo "Start the devcontainer first:"
        echo "  docker start ${CONTAINER_NAME}"
        return 1
    fi
    return 0
}

is_in_devcontainer() {
    # Check if we're running inside the devcontainer
    [ -f "/.dockerenv" ] || [ -n "$DEVCONTAINER" ]
}

run_validator() {
    local log_file=$1
    shift
    local options="$@"

    # Convert relative path to absolute path for devcontainer
    if [[ "$log_file" != /* ]]; then
        # Relative path - prepend /workspace/
        log_file="/workspace/${log_file}"
    fi

    if is_in_devcontainer; then
        # Running inside devcontainer - execute directly
        python3 "${VALIDATOR_SCRIPT}" "${log_file}" ${options}
    else
        # Running on host - execute in devcontainer
        docker exec "${CONTAINER_NAME}" bash -c \
            "cd /workspace && python3 ${VALIDATOR_SCRIPT} ${log_file} ${options}"
    fi
}

###############################################################################
# Main
###############################################################################

main() {
    # Check for help flag
    if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
        print_usage
        exit 0
    fi

    # Check parameters
    if [ $# -eq 0 ]; then
        print_error "Missing log file parameter"
        echo ""
        print_usage
        exit 2
    fi

    local log_file=$1
    shift
    local options="$@"

    # If running on host, check devcontainer
    if ! is_in_devcontainer; then
        if ! check_devcontainer; then
            exit 3
        fi
    fi

    # Run validator
    if run_validator "${log_file}" ${options}; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
