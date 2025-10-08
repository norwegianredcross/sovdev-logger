#!/bin/bash
################################################################################
# query-prometheus.sh - Query Prometheus for metrics from a specific service
#
# Purpose: Query Prometheus backend to retrieve and verify metrics
#
# Usage:
#   ./query-prometheus.sh <service-name> [options]
#
# Arguments:
#   service-name    Required. The service name to query (e.g., sovdev-test-python)
#
# Options:
#   --json          Output raw JSON data for parsing/verification
#   --metric NAME   Specific metric to query (default: sovdev_operations_total)
#   --help          Show this help message
#
# Output Modes:
#   Human-readable (default): Color-coded status messages
#     ✅ Found 5 metric series for 'sovdev-test-python'
#     ✅ Total operations: 16
#
#   JSON mode (--json): Full structured JSON output
#     {
#       "status": "success",
#       "data": {
#         "resultType": "vector",
#         "result": [...]
#       }
#     }
#
# Exit Codes:
#   0 - Success
#   1 - Error (service not found, query failed, etc.)
#
# Examples:
#   # Quick check (human-readable)
#   ./query-prometheus.sh sovdev-test-python
#
#   # Get JSON for metric verification
#   ./query-prometheus.sh sovdev-test-python --json | jq '.data.result[0].metric'
#
#   # Query specific metric
#   ./query-prometheus.sh sovdev-test-python --metric sovdev_operations_total
#
#   # Save evidence
#   ./query-prometheus.sh sovdev-test-python --json > evidence/prometheus-output.json
#
################################################################################

set -euo pipefail

# Colors for human-readable output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
METRIC_NAME="sovdev_operations_total"
JSON_MODE=false
SERVICE_NAME=""

# Parse arguments
show_help() {
    head -n 54 "$0" | grep "^#" | sed 's/^# \?//'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --json)
            JSON_MODE=true
            shift
            ;;
        --metric)
            METRIC_NAME="$2"
            shift 2
            ;;
        --help)
            show_help
            ;;
        -*)
            echo -e "${RED}❌ Unknown option: $1${NC}" >&2
            echo "Use --help to see available options" >&2
            exit 1
            ;;
        *)
            if [[ -z "$SERVICE_NAME" ]]; then
                SERVICE_NAME="$1"
            else
                echo -e "${RED}❌ Multiple service names provided. Only one allowed.${NC}" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$SERVICE_NAME" ]]; then
    echo -e "${RED}❌ Error: Service name is required${NC}" >&2
    echo "" >&2
    echo "Usage: $0 <service-name> [options]" >&2
    echo "Use --help for more information" >&2
    exit 1
fi

# Pre-flight checks
if [[ "$JSON_MODE" == false ]]; then
    echo -e "${BLUE}🔍 Querying Prometheus for service: ${SERVICE_NAME}${NC}"
    echo -e "${BLUE}   Metric: ${METRIC_NAME}${NC}"
    echo ""
fi

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    if [[ "$JSON_MODE" == false ]]; then
        echo -e "${RED}❌ kubectl not found${NC}" >&2
    else
        echo '{"error": "kubectl not found"}' >&2
    fi
    exit 1
fi

# Check if Prometheus service exists
if ! kubectl get svc -n monitoring prometheus-server &> /dev/null; then
    if [[ "$JSON_MODE" == false ]]; then
        echo -e "${RED}❌ Prometheus service not found in monitoring namespace${NC}" >&2
        echo -e "${YELLOW}   Make sure the monitoring stack is deployed${NC}" >&2
    else
        echo '{"error": "Prometheus service not found in monitoring namespace"}' >&2
    fi
    exit 1
fi

# Build PromQL query
PROMQL_QUERY="${METRIC_NAME}{service_name=\"${SERVICE_NAME}\"}"

# Query Prometheus
if [[ "$JSON_MODE" == false ]]; then
    echo -e "${BLUE}📡 Querying Prometheus...${NC}"
fi

# Execute query using kubectl run with curl
QUERY_RAW=$(kubectl run curl-prometheus-query --image=curlimages/curl --rm -i --restart=Never -n monitoring -- \
    curl -s -G \
    --data-urlencode "query=${PROMQL_QUERY}" \
    http://prometheus-server.monitoring.svc.cluster.local:80/api/v1/query 2>&1) || {
    if [[ "$JSON_MODE" == false ]]; then
        echo -e "${RED}❌ Failed to query Prometheus${NC}" >&2
        echo -e "${YELLOW}   Error: ${QUERY_RAW}${NC}" >&2
    else
        echo "{\"error\": \"Failed to query Prometheus\", \"details\": \"${QUERY_RAW}\"}" >&2
    fi
    exit 1
}

# Filter out kubectl pod deletion messages (appended to JSON without newline)
QUERY_RESULT=$(echo "$QUERY_RAW" | sed 's/pod ".*" deleted//g' | sed 's/If you don.*//g')

# Check if query was successful
if ! echo "$QUERY_RESULT" | jq -e '.status == "success"' &> /dev/null; then
    if [[ "$JSON_MODE" == false ]]; then
        echo -e "${RED}❌ Query failed${NC}" >&2
        echo -e "${YELLOW}   Response: ${QUERY_RESULT}${NC}" >&2
    else
        echo "$QUERY_RESULT" >&2
    fi
    exit 1
fi

# Output based on mode
if [[ "$JSON_MODE" == true ]]; then
    # JSON mode: output raw JSON
    echo "$QUERY_RESULT"
else
    # Human-readable mode: parse and display
    RESULT_COUNT=$(echo "$QUERY_RESULT" | jq -r '.data.result | length')

    if [[ "$RESULT_COUNT" == "0" ]]; then
        echo -e "${YELLOW}⚠️  No metrics found for service: ${SERVICE_NAME}${NC}"
        echo -e "${YELLOW}   Metric: ${METRIC_NAME}${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Found ${RESULT_COUNT} metric series for '${SERVICE_NAME}'${NC}"

    # Calculate total operations (sum of all metric values)
    TOTAL_OPS=$(echo "$QUERY_RESULT" | jq -r '[.data.result[].value[1] | tonumber] | add')
    echo -e "${GREEN}✅ Total operations: ${TOTAL_OPS}${NC}"

    # Show sample of first metric
    FIRST_METRIC=$(echo "$QUERY_RESULT" | jq '.data.result[0].metric' 2>/dev/null)

    if [[ -n "$FIRST_METRIC" && "$FIRST_METRIC" != "null" ]]; then
        echo ""
        echo -e "${BLUE}📋 Sample metric labels:${NC}"

        # Extract key labels (Prometheus uses snake_case)
        LOG_LEVEL=$(echo "$FIRST_METRIC" | jq -r '.log_level // "N/A"')
        LOG_TYPE=$(echo "$FIRST_METRIC" | jq -r '.log_type // "N/A"')
        PEER_SERVICE=$(echo "$FIRST_METRIC" | jq -r '.peer_service // "N/A"')

        echo -e "   log_level:    ${LOG_LEVEL}"
        echo -e "   log_type:     ${LOG_TYPE}"
        echo -e "   peer_service: ${PEER_SERVICE}"

        # Show label count
        LABEL_COUNT=$(echo "$FIRST_METRIC" | jq 'keys | length')
        echo -e "   (${LABEL_COUNT} total labels)"
    fi

    echo ""
    echo -e "${GREEN}✅ Prometheus query successful${NC}"
    echo ""
    echo -e "${BLUE}💡 Tip: Use --json flag to get full JSON output for verification${NC}"
fi

exit 0
