#!/bin/bash
################################################################################
# query-loki.sh - Query Loki for logs from a specific service
#
# Purpose: Query Loki backend to retrieve and verify logs
#
# Usage:
#   ./query-loki.sh <service-name> [options]
#
# Arguments:
#   service-name    Required. The service name to query (e.g., sovdev-test-python)
#
# Options:
#   --json          Output raw JSON data for parsing/verification
#   --limit N       Limit results to N entries (default: 10)
#   --time-range R  Time range: 1h, 30m, 24h, etc. (default: 1h)
#   --help          Show this help message
#
# Output Modes:
#   Human-readable (default): Color-coded status messages
#     ✅ Service 'sovdev-test-python' found in Loki
#     ✅ Found 16 log entries
#
#   JSON mode (--json): Full structured JSON output
#     {
#       "status": "success",
#       "data": {
#         "resultType": "streams",
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
#   ./query-loki.sh sovdev-test-python
#
#   # Get JSON for field verification
#   ./query-loki.sh sovdev-test-python --json | jq '.data.result[0].values[0][1]'
#
#   # Save evidence
#   ./query-loki.sh sovdev-test-python --json > evidence/loki-output.json
#
#   # Query last 30 minutes, limit to 5 entries
#   ./query-loki.sh sovdev-test-python --time-range 30m --limit 5
#
################################################################################

set -euo pipefail

# Configure kubectl to use kubeconfig from workspace (devcontainer)
if [ -f "/workspace/topsecret/.kube/config" ]; then
    export KUBECONFIG="/workspace/topsecret/.kube/config"
elif [ -f "$HOME/.kube/config" ]; then
    export KUBECONFIG="$HOME/.kube/config"
fi

# Colors for human-readable output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
LIMIT=10
TIME_RANGE="1h"
JSON_MODE=false
SERVICE_NAME=""

# Parse arguments
show_help() {
    head -n 60 "$0" | grep "^#" | sed 's/^# \?//'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --json)
            JSON_MODE=true
            shift
            ;;
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        --time-range)
            TIME_RANGE="$2"
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

# Calculate time range in nanoseconds from now
calculate_time_range() {
    local range="$1"
    local now_ns=$(date +%s%N)
    local duration_seconds=0

    # Parse time range (1h, 30m, 24h, etc.)
    if [[ $range =~ ^([0-9]+)h$ ]]; then
        duration_seconds=$((${BASH_REMATCH[1]} * 3600))
    elif [[ $range =~ ^([0-9]+)m$ ]]; then
        duration_seconds=$((${BASH_REMATCH[1]} * 60))
    elif [[ $range =~ ^([0-9]+)s$ ]]; then
        duration_seconds=${BASH_REMATCH[1]}
    else
        echo -e "${RED}❌ Invalid time range format: $range${NC}" >&2
        echo "Use format like: 1h, 30m, 24h" >&2
        exit 1
    fi

    local start_ns=$((now_ns - (duration_seconds * 1000000000)))
    echo "$start_ns $now_ns"
}

# Pre-flight checks
if [[ "$JSON_MODE" == false ]]; then
    echo -e "${BLUE}🔍 Querying Loki for service: ${SERVICE_NAME}${NC}"
    echo -e "${BLUE}   Time range: ${TIME_RANGE}, Limit: ${LIMIT}${NC}"
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

# Check if Loki pod exists
if ! kubectl get pod -n monitoring loki-0 &> /dev/null; then
    if [[ "$JSON_MODE" == false ]]; then
        echo -e "${RED}❌ Loki pod not found in monitoring namespace${NC}" >&2
        echo -e "${YELLOW}   Make sure the monitoring stack is deployed${NC}" >&2
    else
        echo '{"error": "Loki pod not found in monitoring namespace"}' >&2
    fi
    exit 1
fi

# Calculate time range
read START_NS END_NS <<< $(calculate_time_range "$TIME_RANGE")

# Build LogQL query
LOGQL_QUERY="{service_name=\"${SERVICE_NAME}\"}"

# Query Loki
if [[ "$JSON_MODE" == false ]]; then
    echo -e "${BLUE}📡 Querying Loki...${NC}"
fi

# Execute query using kubectl exec
QUERY_RESULT=$(kubectl exec -n monitoring loki-0 -- \
    wget -q -O - \
    --post-data "query=${LOGQL_QUERY}&start=${START_NS}&end=${END_NS}&limit=${LIMIT}" \
    http://localhost:3100/loki/api/v1/query_range 2>&1) || {
    if [[ "$JSON_MODE" == false ]]; then
        echo -e "${RED}❌ Failed to query Loki${NC}" >&2
        echo -e "${YELLOW}   Error: ${QUERY_RESULT}${NC}" >&2
    else
        echo "{\"error\": \"Failed to query Loki\", \"details\": \"${QUERY_RESULT}\"}" >&2
    fi
    exit 1
}

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
        echo -e "${YELLOW}⚠️  No logs found for service: ${SERVICE_NAME}${NC}"
        echo -e "${YELLOW}   Time range: ${TIME_RANGE}${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Service '${SERVICE_NAME}' found in Loki${NC}"

    # Count total log entries across all streams
    TOTAL_ENTRIES=$(echo "$QUERY_RESULT" | jq -r '[.data.result[].values | length] | add')
    echo -e "${GREEN}✅ Found ${TOTAL_ENTRIES} log entries${NC}"

    # Show sample of first log entry
    # In Loki, OTLP structured fields are stored as stream labels, not in the log line
    FIRST_STREAM=$(echo "$QUERY_RESULT" | jq '.data.result[0].stream' 2>/dev/null)
    FIRST_MESSAGE=$(echo "$QUERY_RESULT" | jq -r '.data.result[0].values[0][1]' 2>/dev/null || echo "")

    if [[ -n "$FIRST_STREAM" && "$FIRST_STREAM" != "null" ]]; then
        echo ""
        echo -e "${BLUE}📋 Sample log entry:${NC}"

        # Extract key fields from stream labels
        TIMESTAMP=$(echo "$FIRST_STREAM" | jq -r '.timestamp // "N/A"')
        SEVERITY=$(echo "$FIRST_STREAM" | jq -r '.severity_text // "N/A"')
        MESSAGE_PREVIEW=$(echo "$FIRST_MESSAGE" | head -c 60)

        echo -e "   timestamp:    ${TIMESTAMP}"
        echo -e "   severity:     ${SEVERITY}"
        echo -e "   message:      ${MESSAGE_PREVIEW}..."

        # Show field count (from stream labels)
        FIELD_COUNT=$(echo "$FIRST_STREAM" | jq 'keys | length')
        echo -e "   (${FIELD_COUNT} total fields in stream)"
    fi

    echo ""
    echo -e "${GREEN}✅ Loki query successful${NC}"
    echo ""
    echo -e "${BLUE}💡 Tip: Use --json flag to get full JSON output for verification${NC}"
fi

exit 0
