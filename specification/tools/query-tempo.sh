#!/bin/bash
################################################################################
# query-tempo.sh - Query Tempo for traces from a specific service
#
# Purpose: Query Tempo backend to retrieve and verify traces
#
# Usage:
#   ./query-tempo.sh <service-name> [options]
#
# Arguments:
#   service-name    Required. The service name to query (e.g., sovdev-test-python)
#
# Options:
#   --json          Output raw JSON data for parsing/verification
#   --limit N       Limit results to N traces (default: 10)
#   --help          Show this help message
#
# Output Modes:
#   Human-readable (default): Color-coded status messages
#     ✅ Service 'sovdev-test-python' found in Tempo
#     ✅ Found 8 traces
#
#   JSON mode (--json): Full structured JSON output
#     {
#       "traces": [...],
#       "metrics": {...}
#     }
#
# Exit Codes:
#   0 - Success
#   1 - Error (service not found, query failed, etc.)
#
# Examples:
#   # Quick check (human-readable)
#   ./query-tempo.sh sovdev-test-python
#
#   # Get JSON for trace verification
#   ./query-tempo.sh sovdev-test-python --json | jq '.traces[0].traceID'
#
#   # Limit to 5 traces
#   ./query-tempo.sh sovdev-test-python --limit 5
#
#   # Save evidence
#   ./query-tempo.sh sovdev-test-python --json > evidence/tempo-output.json
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
JSON_MODE=false
SERVICE_NAME=""

# Parse arguments
show_help() {
    head -n 52 "$0" | grep "^#" | sed 's/^# \?//'
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
    echo -e "${BLUE}🔍 Querying Tempo for service: ${SERVICE_NAME}${NC}"
    echo -e "${BLUE}   Limit: ${LIMIT}${NC}"
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

# Check if Tempo service exists
if ! kubectl get svc -n monitoring tempo &> /dev/null; then
    if [[ "$JSON_MODE" == false ]]; then
        echo -e "${RED}❌ Tempo service not found in monitoring namespace${NC}" >&2
        echo -e "${YELLOW}   Make sure the monitoring stack is deployed${NC}" >&2
    else
        echo '{"error": "Tempo service not found in monitoring namespace"}' >&2
    fi
    exit 1
fi

# Query Tempo
if [[ "$JSON_MODE" == false ]]; then
    echo -e "${BLUE}📡 Querying Tempo...${NC}"
fi

# Execute search query using kubectl run with curl
SEARCH_RAW=$(kubectl run curl-tempo-search --image=curlimages/curl --rm -i --restart=Never -n monitoring -- \
    curl -s "http://tempo.monitoring.svc.cluster.local:3200/api/search?tags=service.name=${SERVICE_NAME}&limit=${LIMIT}" 2>&1) || {
    if [[ "$JSON_MODE" == false ]]; then
        echo -e "${RED}❌ Failed to query Tempo${NC}" >&2
        echo -e "${YELLOW}   Error: ${SEARCH_RAW}${NC}" >&2
    else
        echo "{\"error\": \"Failed to query Tempo\", \"details\": \"${SEARCH_RAW}\"}" >&2
    fi
    exit 1
}

# Filter out kubectl pod messages (appended to JSON without newline)
# Common kubectl messages: pod deletion, namespace info, warnings, etc.
SEARCH_RESULT=$(echo "$SEARCH_RAW" | sed 's/pod ".*" deleted//g' | sed 's/If you don.*//g' | sed 's/ from monitoring namespace//g' | sed 's/Error from server.*//g')

# Check if query returned traces
TRACE_COUNT=$(echo "$SEARCH_RESULT" | jq -r '.traces | length' 2>/dev/null || echo "0")

if [[ "$TRACE_COUNT" == "0" || "$TRACE_COUNT" == "null" ]]; then
    if [[ "$JSON_MODE" == false ]]; then
        echo -e "${YELLOW}⚠️  No traces found for service: ${SERVICE_NAME}${NC}"
        exit 1
    else
        # Return valid empty Tempo response instead of error
        # This allows validators to process it properly
        echo "{\"traces\": [], \"metrics\": {\"inspectedTraces\": 0, \"inspectedSpans\": 0, \"inspectedBytes\": 0}}"
        exit 0
    fi
fi

# Output based on mode
if [[ "$JSON_MODE" == true ]]; then
    # JSON mode: output raw JSON
    echo "$SEARCH_RESULT"
else
    # Human-readable mode: parse and display
    echo -e "${GREEN}✅ Service '${SERVICE_NAME}' found in Tempo${NC}"
    echo -e "${GREEN}✅ Found ${TRACE_COUNT} traces${NC}"

    # Get first trace info
    FIRST_TRACE=$(echo "$SEARCH_RESULT" | jq '.traces[0]' 2>/dev/null)

    if [[ -n "$FIRST_TRACE" && "$FIRST_TRACE" != "null" ]]; then
        echo ""
        echo -e "${BLUE}📋 Sample trace:${NC}"

        # Extract key fields
        TRACE_ID=$(echo "$FIRST_TRACE" | jq -r '.traceID // "N/A"')
        ROOT_SERVICE=$(echo "$FIRST_TRACE" | jq -r '.rootServiceName // "N/A"')
        ROOT_TRACE=$(echo "$FIRST_TRACE" | jq -r '.rootTraceName // "N/A"')
        START_TIME=$(echo "$FIRST_TRACE" | jq -r '.startTimeUnixNano // "N/A"')

        # Convert nanoseconds to readable timestamp if available
        if [[ "$START_TIME" != "N/A" && "$START_TIME" != "null" ]]; then
            START_TIME_SEC=$((START_TIME / 1000000000))
            START_TIME_READABLE=$(date -r "$START_TIME_SEC" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "$START_TIME")
        else
            START_TIME_READABLE="N/A"
        fi

        echo -e "   traceID:      ${TRACE_ID:0:16}..."
        echo -e "   service:      ${ROOT_SERVICE}"
        echo -e "   operation:    ${ROOT_TRACE}"
        echo -e "   timestamp:    ${START_TIME_READABLE}"

        # Show span count if available
        SPAN_SETS=$(echo "$FIRST_TRACE" | jq '.spanSets // [] | length' 2>/dev/null || echo "0")
        if [[ "$SPAN_SETS" != "0" ]]; then
            TOTAL_SPANS=$(echo "$FIRST_TRACE" | jq '[.spanSets[].spans | length] | add' 2>/dev/null || echo "0")
            echo -e "   spans:        ${TOTAL_SPANS}"
        fi
    fi

    echo ""
    echo -e "${GREEN}✅ Tempo query successful${NC}"
    echo ""
    echo -e "${BLUE}💡 Tip: Use --json flag to get full JSON output for verification${NC}"
fi

exit 0
