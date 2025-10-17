#!/usr/bin/env bash
#
# Full E2E Validation Script (Run From Host)
#
# Runs complete validation workflow:
# A) Run program that creates log (in devcontainer)
# B) Validate log file using schema (in devcontainer)
# C) Validate Loki response using schema (on host using kubectl)
# D) Compare log file with Loki response (on host using kubectl)
#
# Usage (from host):
#   cd /path/to/sovdev-logger/specification/tools
#   ./run-full-validation-host.sh [typescript|python]
#
# Exit codes:
#   0 - All validations passed
#   1 - Validation failed
#   2 - Usage error
#   3 - Devcontainer not running
#
# Environment:
#   - Must run from HOST (not inside devcontainer)
#   - Requires devcontainer-toolbox running
#   - Requires kubectl configured on host
#   - Requires Kubernetes cluster with monitoring stack

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Constants
CONTAINER_NAME="devcontainer-toolbox"

# Helper functions
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}" >&2
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Parse arguments
LANGUAGE=${1:-typescript}

if [[ "$LANGUAGE" != "typescript" && "$LANGUAGE" != "python" ]]; then
    print_error "Invalid language: $LANGUAGE"
    echo "Usage: $0 [typescript|python]"
    exit 2
fi

# Check devcontainer is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_error "Devcontainer '${CONTAINER_NAME}' is not running"
    echo ""
    echo "Start the devcontainer first:"
    echo "  docker start ${CONTAINER_NAME}"
    exit 3
fi

# Determine paths
if [[ "$LANGUAGE" == "typescript" ]]; then
    SERVICE_NAME="sovdev-test-company-lookup-typescript"
    CONTAINER_LOG_FILE="/workspace/typescript/test/e2e/company-lookup/logs/dev.log"
elif [[ "$LANGUAGE" == "python" ]]; then
    SERVICE_NAME="sovdev-test-company-lookup-python"
    CONTAINER_LOG_FILE="/workspace/python/test/e2e/company-lookup/logs/dev.log"
fi

print_header "FULL E2E VALIDATION - $LANGUAGE"

#
# STEP A: Run program that creates log (in devcontainer)
#
print_header "Step A: Run Program That Creates Log"
print_step "Running test program inside devcontainer..."
echo ""

docker exec "$CONTAINER_NAME" bash -c \
    "cd /workspace/$LANGUAGE/test/e2e/company-lookup && ./run-test.sh"

if [[ $? -ne 0 ]]; then
    print_error "Test program failed"
    exit 1
fi

print_success "Test program completed"

#
# STEP B: Validate log file using schema (in devcontainer)
#
print_header "Step B: Validate Log File Using Schema"
print_step "Validating log file against log-entry-schema.json..."
echo ""

docker exec "$CONTAINER_NAME" bash -c \
    "cd /workspace/specification/tools && ./validate-log-format.sh $CONTAINER_LOG_FILE"

if [[ $? -ne 0 ]]; then
    print_error "Log file validation failed"
    exit 1
fi

print_success "Log file schema validation passed"

#
# STEP C: Validate Loki response using schema (on host)
#
print_header "Step C: Validate Loki Response Using Schema"
print_step "Waiting 3 seconds for logs to reach Loki..."
sleep 3
echo ""

# Count entries in file to determine limit
ENTRY_COUNT=$(docker exec "$CONTAINER_NAME" bash -c "wc -l < $CONTAINER_LOG_FILE" | tr -d ' ')
LIMIT=$((ENTRY_COUNT + 10))  # Add buffer

print_step "Querying Loki and validating against loki-response-schema.json..."
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Query Loki (on host) and validate schema (in devcontainer)
"$SCRIPT_DIR/query-loki.sh" "$SERVICE_NAME" --limit "$LIMIT" --json | \
    docker exec -i "$CONTAINER_NAME" python3 /workspace/specification/tests/validate-loki-response.py -

if [[ $? -ne 0 ]]; then
    print_error "Loki response validation failed"
    exit 1
fi

print_success "Loki response schema validation passed"

#
# STEP D: Compare log file with Loki response (on host + devcontainer)
#
print_header "Step D: Compare Log File With Loki Response"
print_step "Cross-validating file logs match Loki logs..."
echo ""

# Query Loki (on host) and compare (in devcontainer)
"$SCRIPT_DIR/query-loki.sh" "$SERVICE_NAME" --limit "$LIMIT" --json | \
    docker exec -i "$CONTAINER_NAME" python3 /workspace/specification/tests/validate-log-consistency.py "$CONTAINER_LOG_FILE" -

if [[ $? -ne 0 ]]; then
    print_error "Log consistency validation failed"
    exit 1
fi

print_success "Log consistency validation passed"

#
# SUCCESS
#
echo ""
print_header "ALL VALIDATIONS PASSED"
echo -e "${GREEN}✅ E2E TEST SUCCESSFUL${NC}"
echo ""
echo "Summary:"
echo "  Language: $LANGUAGE"
echo "  Service: $SERVICE_NAME"
echo "  Log file: $CONTAINER_LOG_FILE"
echo "  Entries validated: $ENTRY_COUNT"
echo ""
echo "All 4 steps completed successfully:"
echo "  A) ✅ Run program that creates log"
echo "  B) ✅ Validate log file using schema"
echo "  C) ✅ Validate Loki response using schema"
echo "  D) ✅ Compare log file with Loki response"
echo ""

exit 0
