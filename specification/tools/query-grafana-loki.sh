#!/bin/bash
################################################################################
# query-grafana-loki.sh - Query Loki THROUGH Grafana datasource proxy
#
# Purpose: Query Loki via Grafana's datasource proxy API to validate
#          Grafana can correctly query Loki with snake_case field names
#
# Usage:
#   ./query-grafana-loki.sh <service-name> [options]
#
# Arguments:
#   service-name    Required. The service name to query
#
# Options:
#   --json          Output raw JSON data for parsing/verification
#   --limit N       Limit results to N entries (default: 10)
#   --time-range R  Time range: 1h, 30m, 24h, etc. (default: 1h)
#   --help          Show this help message
#
# Output:
#   Same JSON format as query-loki.sh (Loki API response)
#
# Datasource Proxy:
#   Queries: http://grafana/api/datasources/proxy/2/loki/api/v1/query_range
#   Where: 2 = Loki datasource ID in Grafana
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
LIMIT=10
TIME_RANGE="1h"
JSON_MODE=false
SERVICE_NAME=""

# Grafana access (via Traefik ingress)
GRAFANA_HOST="host.docker.internal"
GRAFANA_HEADER="Host: grafana.localhost"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="SecretPassword1"
LOKI_DATASOURCE_ID="2"  # Loki is datasource 2 in Grafana

# Parse arguments
show_help() {
    head -n 30 "$0" | grep "^#" | sed 's/^# \?//'
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

# Calculate time range in nanoseconds
calculate_time_range() {
    local range="$1"
    local now_ns=$(date +%s%N)
    local duration_seconds=0

    if [[ $range =~ ^([0-9]+)h$ ]]; then
        duration_seconds=$((${BASH_REMATCH[1]} * 3600))
    elif [[ $range =~ ^([0-9]+)m$ ]]; then
        duration_seconds=$((${BASH_REMATCH[1]} * 60))
    elif [[ $range =~ ^([0-9]+)s$ ]]; then
        duration_seconds=${BASH_REMATCH[1]}
    else
        echo -e "${RED}❌ Invalid time range: $range${NC}" >&2
        exit 1
    fi

    local start_ns=$((now_ns - (duration_seconds * 1000000000)))
    echo "$start_ns $now_ns"
}

# Pre-flight checks
if [[ "$JSON_MODE" == false ]]; then
    echo -e "${BLUE}🔍 Querying Loki via Grafana datasource proxy${NC}"
    echo -e "${BLUE}   Service: ${SERVICE_NAME}${NC}"
    echo -e "${BLUE}   Time range: ${TIME_RANGE}, Limit: ${LIMIT}${NC}"
    echo ""
fi

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ curl not found${NC}" >&2
    exit 1
fi

# Calculate time range
read START_NS END_NS <<< $(calculate_time_range "$TIME_RANGE")

# Build LogQL query
LOGQL_QUERY="{service_name=\"${SERVICE_NAME}\"}"

# Query Loki through Grafana datasource proxy
if [[ "$JSON_MODE" == false ]]; then
    echo -e "${BLUE}📡 Querying via Grafana datasource proxy...${NC}"
fi

# Grafana datasource proxy URL: /api/datasources/proxy/{datasource-id}/{backend-path}
QUERY_RESULT=$(curl -s -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
    -H "${GRAFANA_HEADER}" \
    -G \
    --data-urlencode "query=${LOGQL_QUERY}" \
    --data-urlencode "start=${START_NS}" \
    --data-urlencode "end=${END_NS}" \
    --data-urlencode "limit=${LIMIT}" \
    "http://${GRAFANA_HOST}/api/datasources/proxy/${LOKI_DATASOURCE_ID}/loki/api/v1/query_range" 2>&1) || {
    echo -e "${RED}❌ Failed to query Loki via Grafana${NC}" >&2
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
    # JSON mode: output raw JSON (same format as query-loki.sh)
    echo "$QUERY_RESULT"
else
    # Human-readable mode
    RESULT_COUNT=$(echo "$QUERY_RESULT" | jq -r '.data.result | length')

    if [[ "$RESULT_COUNT" == "0" ]]; then
        echo -e "${YELLOW}⚠️  No logs found${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Found ${RESULT_COUNT} streams via Grafana${NC}"

    # Count total entries
    TOTAL_ENTRIES=$(echo "$QUERY_RESULT" | jq -r '[.data.result[].values | length] | add')
    echo -e "${GREEN}✅ Total log entries: ${TOTAL_ENTRIES}${NC}"

    echo ""
    echo -e "${GREEN}✅ Loki query via Grafana successful${NC}"
fi

exit 0
