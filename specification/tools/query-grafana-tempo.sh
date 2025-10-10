#!/bin/bash
################################################################################
# query-grafana-tempo.sh - Query Tempo THROUGH Grafana datasource proxy
#
# Purpose: Query Tempo via Grafana's datasource proxy API to validate
#          Grafana can correctly query Tempo traces
#
# Usage:
#   ./query-grafana-tempo.sh <service-name> [options]
#
# Arguments:
#   service-name    Required. The service name to query
#
# Options:
#   --json          Output raw JSON data for parsing/verification
#   --limit N       Limit results to N traces (default: 20)
#   --help          Show this help message
#
# Output:
#   Same JSON format as query-tempo.sh (Tempo API response)
#
# Datasource Proxy:
#   Queries: http://grafana/api/datasources/proxy/3/api/search
#   Where: 3 = Tempo datasource ID in Grafana
#
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default options
LIMIT=20
JSON_MODE=false
SERVICE_NAME=""

# Grafana access (via Traefik ingress)
GRAFANA_HOST="host.docker.internal"
GRAFANA_HEADER="Host: grafana.localhost"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="SecretPassword1"
TEMPO_DATASOURCE_ID="3"  # Tempo is datasource 3 in Grafana

# Parse arguments
show_help() {
    head -n 27 "$0" | grep "^#" | sed 's/^# \?//'
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
            exit 1
            ;;
        *)
            if [[ -z "$SERVICE_NAME" ]]; then
                SERVICE_NAME="$1"
            else
                echo -e "${RED}❌ Multiple service names provided${NC}" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$SERVICE_NAME" ]]; then
    echo -e "${RED}❌ Error: Service name is required${NC}" >&2
    echo "Usage: $0 <service-name> [options]" >&2
    exit 1
fi

# Pre-flight checks
if [[ "$JSON_MODE" == false ]]; then
    echo -e "${BLUE}🔍 Querying Tempo via Grafana datasource proxy${NC}"
    echo -e "${BLUE}   Service: ${SERVICE_NAME}${NC}"
    echo -e "${BLUE}   Limit: ${LIMIT}${NC}"
    echo ""
fi

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ curl not found${NC}" >&2
    exit 1
fi

# Calculate time range (last 1 hour)
NOW=$(date +%s)
START=$((NOW - 3600))

# Build TraceQL query (Tempo search uses service.name attribute)
# Note: Tempo uses 'service.name' internally, but our logs use 'service_name'
TEMPO_QUERY="{.service.name=\"${SERVICE_NAME}\"}"

# Query Tempo through Grafana datasource proxy
if [[ "$JSON_MODE" == false ]]; then
    echo -e "${BLUE}📡 Querying via Grafana datasource proxy...${NC}"
fi

# Grafana datasource proxy URL: /api/datasources/proxy/{datasource-id}/{backend-path}
QUERY_RESULT=$(curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
    -H "${GRAFANA_HEADER}" \
    -G \
    --data-urlencode "q=${TEMPO_QUERY}" \
    --data-urlencode "start=${START}" \
    --data-urlencode "end=${NOW}" \
    --data-urlencode "limit=${LIMIT}" \
    "http://${GRAFANA_HOST}/api/datasources/proxy/${TEMPO_DATASOURCE_ID}/api/search" 2>&1) || {
    echo -e "${RED}❌ Failed to query Tempo via Grafana${NC}" >&2
    exit 1
}

# Check if response is valid JSON
if ! echo "$QUERY_RESULT" | jq empty &> /dev/null 2>&1; then
    if [[ "$JSON_MODE" == false ]]; then
        echo -e "${RED}❌ Invalid JSON response${NC}" >&2
        echo -e "${YELLOW}   Response: ${QUERY_RESULT}${NC}" >&2
    else
        echo '{"error": "Invalid JSON response"}' >&2
    fi
    exit 1
fi

# Check if traces array exists
if ! echo "$QUERY_RESULT" | jq -e '.traces' &> /dev/null; then
    if [[ "$JSON_MODE" == false ]]; then
        echo -e "${RED}❌ No traces field in response${NC}" >&2
        echo -e "${YELLOW}   Response: ${QUERY_RESULT}${NC}" >&2
    else
        echo "$QUERY_RESULT" >&2
    fi
    exit 1
fi

# Output based on mode
if [[ "$JSON_MODE" == true ]]; then
    # JSON mode: output raw JSON (same format as query-tempo.sh)
    echo "$QUERY_RESULT"
else
    # Human-readable mode
    TRACE_COUNT=$(echo "$QUERY_RESULT" | jq -r '.traces | length')

    if [[ "$TRACE_COUNT" == "0" ]]; then
        echo -e "${YELLOW}⚠️  No traces found${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Found ${TRACE_COUNT} traces via Grafana${NC}"

    echo ""
    echo -e "${GREEN}✅ Tempo query via Grafana successful${NC}"
fi

exit 0
