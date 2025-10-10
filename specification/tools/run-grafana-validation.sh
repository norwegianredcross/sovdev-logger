#!/usr/bin/env bash
################################################################################
# run-grafana-validation.sh - Validate Grafana datasource queries
#
# Purpose: Query through Grafana's datasource proxy API and validate against
#          log file to ensure Grafana can correctly query all backends
#
# Usage (from inside devcontainer):
#   cd /workspace/specification/tools
#   ./run-grafana-validation.sh <service-name> <log-file>
#
# Arguments:
#   service-name    Service name to query (e.g., sovdev-test-company-lookup-typescript)
#   log-file        Path to log file for comparison
#
# This validates that:
#   1. Grafana can query Loki via datasource proxy
#   2. Grafana can query Prometheus via datasource proxy
#   3. Grafana can query Tempo via datasource proxy
#   4. Data retrieved via Grafana matches log file (same as direct backend queries)
#
# Exit codes:
#   0 - All validations passed
#   1 - Validation failed
#   2 - Usage error
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Parse arguments
if [[ $# -lt 2 ]]; then
    print_error "Usage: $0 <service-name> <log-file>"
    exit 2
fi

SERVICE_NAME="$1"
LOG_FILE="$2"

# Validate log file exists
if [[ ! -f "$LOG_FILE" ]]; then
    print_error "Log file not found: $LOG_FILE"
    exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_SCRIPT_DIR="$(dirname "$SCRIPT_DIR")/tests"

# Count entries in file
ENTRY_COUNT=$(wc -l < "$LOG_FILE" | tr -d ' ')
LIMIT=$((ENTRY_COUNT + 10))  # Add buffer

print_header "TASK 3.4: GRAFANA DATASOURCE QUERY VALIDATION"

#
# STEP 3.4.1-3: Loki via Grafana
#
print_header "Step 3.4.1: Query Loki Via Grafana Datasource Proxy"
print_step "Querying Loki through Grafana..."
echo ""

./query-grafana-loki.sh "$SERVICE_NAME" --limit "$LIMIT" --json | \
    python3 "$TEST_SCRIPT_DIR/validate-loki-response.py" -

if [[ $? -ne 0 ]]; then
    print_error "Loki query via Grafana failed"
    exit 1
fi

print_success "Loki query via Grafana validated"

print_header "Step 3.4.2: Compare Grafana-Loki With Log File"
print_step "Cross-validating Grafana-Loki logs match file logs..."
echo ""

./query-grafana-loki.sh "$SERVICE_NAME" --limit "$LIMIT" --json | \
    python3 "$TEST_SCRIPT_DIR/validate-log-consistency.py" "$LOG_FILE" -

if [[ $? -ne 0 ]]; then
    print_error "Grafana-Loki consistency check failed"
    exit 1
fi

print_success "Grafana-Loki consistency validated"

#
# STEP 3.4.3-4: Prometheus via Grafana
#
print_header "Step 3.4.3: Query Prometheus Via Grafana Datasource Proxy"
print_step "Querying Prometheus through Grafana..."
echo ""

timeout 30 ./query-grafana-prometheus.sh "$SERVICE_NAME" --json 2>/dev/null | \
    python3 "$TEST_SCRIPT_DIR/validate-prometheus-response.py" -

if [[ $? -ne 0 ]]; then
    print_error "Prometheus query via Grafana failed"
    exit 1
fi

print_success "Prometheus query via Grafana validated"

print_header "Step 3.4.4: Compare Grafana-Prometheus With Log File"
print_step "Cross-validating Grafana-Prometheus metrics match file logs..."
echo ""

timeout 30 ./query-grafana-prometheus.sh "$SERVICE_NAME" --json 2>/dev/null | \
    python3 "$TEST_SCRIPT_DIR/validate-metrics-consistency.py" "$LOG_FILE" -

if [[ $? -ne 0 ]]; then
    print_error "Grafana-Prometheus consistency check failed"
    exit 1
fi

print_success "Grafana-Prometheus consistency validated"

#
# STEP 3.4.5-6: Tempo via Grafana
#
print_header "Step 3.4.5: Query Tempo Via Grafana Datasource Proxy"
print_step "Querying Tempo through Grafana..."
echo ""

timeout 30 ./query-grafana-tempo.sh "$SERVICE_NAME" --limit 50 --json 2>/dev/null | \
    python3 "$TEST_SCRIPT_DIR/validate-tempo-response.py" -

if [[ $? -ne 0 ]]; then
    print_error "Tempo query via Grafana failed"
    exit 1
fi

print_success "Tempo query via Grafana validated"

print_header "Step 3.4.6: Compare Grafana-Tempo With Log File"
print_step "Cross-validating Grafana-Tempo traces match file trace_ids..."
echo ""

timeout 30 ./query-grafana-tempo.sh "$SERVICE_NAME" --limit 50 --json 2>/dev/null | \
    python3 "$TEST_SCRIPT_DIR/validate-trace-consistency.py" "$LOG_FILE" -

if [[ $? -ne 0 ]]; then
    print_error "Grafana-Tempo consistency check failed"
    exit 1
fi

print_success "Grafana-Tempo consistency validated"

#
# SUCCESS
#
echo ""
print_header "GRAFANA VALIDATION COMPLETE"
echo -e "${GREEN}✅ ALL GRAFANA DATASOURCE QUERIES VALIDATED${NC}"
echo ""
echo "Summary:"
echo "  Service: $SERVICE_NAME"
echo "  Log file: $LOG_FILE"
echo "  Entries: $ENTRY_COUNT"
echo ""
echo "Validation steps completed:"
echo "  3.4.1) ✅ Query Loki via Grafana datasource proxy"
echo "  3.4.2) ✅ Compare Grafana-Loki with log file"
echo "  3.4.3) ✅ Query Prometheus via Grafana datasource proxy"
echo "  3.4.4) ✅ Compare Grafana-Prometheus with log file"
echo "  3.4.5) ✅ Query Tempo via Grafana datasource proxy"
echo "  3.4.6) ✅ Compare Grafana-Tempo with log file"
echo ""
echo "✅ Grafana can correctly query all backends with snake_case fields"
echo ""

exit 0
