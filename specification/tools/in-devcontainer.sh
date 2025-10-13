#!/bin/bash
################################################################################
# in-devcontainer.sh - Universal wrapper to run any script inside devcontainer
#
# Purpose: Run specification/tools scripts inside devcontainer from host machine
#          Eliminates need for individual -host.sh wrapper files
#
# Usage:
#   ./in-devcontainer.sh <script> [args...]
#   ./in-devcontainer.sh --help
#   ./in-devcontainer.sh --list
#
# Examples:
#   ./in-devcontainer.sh query-loki.sh service-name --json
#   ./in-devcontainer.sh run-full-validation.sh python
#   ./in-devcontainer.sh validate-log-format.sh python/test/logs/dev.log
#
# Shortcuts (auto-add .sh):
#   ./in-devcontainer.sh query-loki service-name
#   ./in-devcontainer.sh run-full-validation python
#
# Common aliases:
#   loki           → query-loki.sh
#   prometheus     → query-prometheus.sh
#   tempo          → query-tempo.sh
#   validate       → run-full-validation.sh
#   validate-logs  → validate-log-format.sh
#
# Options:
#   --help         Show this help message
#   --list         List all available scripts in devcontainer
#   --dry-run      Show command without executing
#   --interactive  Open bash shell in tools directory
#
# Exit Codes:
#   0 - Success
#   1 - Script execution failed
#   2 - Usage error
#   3 - Container not running
#   4 - Script not found
#
################################################################################

set -euo pipefail

# Configuration
CONTAINER_NAME="devcontainer-toolbox"
TOOLS_DIR="/workspace/specification/tools"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
DRY_RUN=false
INTERACTIVE=false

#------------------------------------------------------------------------------
# Helper Functions
#------------------------------------------------------------------------------

show_help() {
    cat << EOF
${BLUE}in-devcontainer.sh${NC} - Universal wrapper to run scripts inside devcontainer

${YELLOW}Usage:${NC}
  ./in-devcontainer.sh <script> [args...]
  ./in-devcontainer.sh [options]

${YELLOW}Examples:${NC}
  ${GREEN}# Query tools${NC}
  ./in-devcontainer.sh query-loki.sh service-name --json
  ./in-devcontainer.sh query-prometheus.sh service-name
  ./in-devcontainer.sh query-tempo.sh service-name --limit 5

  ${GREEN}# Validation tools${NC}
  ./in-devcontainer.sh run-full-validation.sh python
  ./in-devcontainer.sh validate-log-format.sh python/test/logs/dev.log

  ${GREEN}# Test tools${NC}
  ./in-devcontainer.sh run-company-lookup.sh typescript

  ${GREEN}# Shortcuts (auto-add .sh)${NC}
  ./in-devcontainer.sh query-loki service-name
  ./in-devcontainer.sh validate-log-format python/test/logs/dev.log

${YELLOW}Common Aliases:${NC}
  loki, prometheus, tempo   → query-{name}.sh
  validate                  → run-full-validation.sh
  validate-logs             → validate-log-format.sh
  company-lookup            → run-company-lookup.sh

${YELLOW}Options:${NC}
  --help         Show this help message
  --list         List all available scripts in devcontainer
  --dry-run      Show command without executing
  --interactive  Open bash shell in tools directory (cd $TOOLS_DIR)

${YELLOW}Exit Codes:${NC}
  0 - Success
  1 - Script execution failed
  2 - Usage error
  3 - Container not running
  4 - Script not found

${YELLOW}Notes:${NC}
  - Container must be running: docker start $CONTAINER_NAME
  - Scripts run from: $TOOLS_DIR
  - All script arguments are passed through
  - Use quotes for arguments with spaces

${YELLOW}Alternative:${NC}
  For the most common workflow, you can use:
    ./run-full-validation-host.sh python

  (Kept for backward compatibility and convenience)

EOF
}

list_scripts() {
    echo -e "${BLUE}Available scripts in devcontainer:${NC}"
    echo ""

    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        echo -e "${RED}❌ Error: Container '$CONTAINER_NAME' is not running${NC}"
        echo "Start with: docker start $CONTAINER_NAME"
        exit 3
    fi

    # List all .sh files in tools directory
    docker exec "$CONTAINER_NAME" bash -c "
        cd $TOOLS_DIR 2>/dev/null || { echo 'Tools directory not found'; exit 1; }
        ls -1 *.sh 2>/dev/null | while read file; do
            # Get first line of comment (description)
            desc=\$(head -5 \"\$file\" | grep -E '^# [A-Z]' | head -1 | sed 's/^# //')
            printf '  %-35s %s\n' \"\$file\" \"\$desc\"
        done
    " || {
        echo -e "${RED}❌ Error: Could not list scripts${NC}"
        exit 1
    }

    echo ""
    echo -e "${YELLOW}Usage:${NC} ./in-devcontainer.sh <script> [args...]"
}

check_container() {
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        echo -e "${RED}❌ Error: Container '$CONTAINER_NAME' is not running${NC}" >&2
        echo "" >&2
        echo "Start the container with:" >&2
        echo "  docker start $CONTAINER_NAME" >&2
        echo "" >&2
        echo "Or check container status:" >&2
        echo "  docker ps -a | grep devcontainer" >&2
        exit 3
    fi
}

resolve_script_name() {
    local input="$1"
    local script_name=""

    # Common aliases
    case "$input" in
        loki)
            script_name="query-loki.sh"
            ;;
        prometheus|prom)
            script_name="query-prometheus.sh"
            ;;
        tempo)
            script_name="query-tempo.sh"
            ;;
        grafana)
            script_name="query-grafana.sh"
            ;;
        validate)
            script_name="run-full-validation.sh"
            ;;
        validate-logs)
            script_name="validate-log-format.sh"
            ;;
        company-lookup)
            script_name="run-company-lookup.sh"
            ;;
        *)
            # Not an alias - use as-is
            script_name="$input"
            ;;
    esac

    # Auto-add .sh if missing
    if [[ ! "$script_name" =~ \.sh$ ]]; then
        script_name="${script_name}.sh"
    fi

    echo "$script_name"
}

check_script_exists() {
    local script="$1"

    if ! docker exec "$CONTAINER_NAME" test -f "$TOOLS_DIR/$script" 2>/dev/null; then
        echo -e "${RED}❌ Error: Script not found: $script${NC}" >&2
        echo "" >&2
        echo "Available scripts:" >&2
        docker exec "$CONTAINER_NAME" bash -c "cd $TOOLS_DIR && ls -1 *.sh 2>/dev/null | head -10" >&2
        echo "" >&2
        echo "Use: ./in-devcontainer.sh --list   (to see all scripts)" >&2
        exit 4
    fi
}

run_interactive() {
    echo -e "${BLUE}Opening interactive shell in devcontainer...${NC}"
    echo "Location: $TOOLS_DIR"
    echo "Exit with: Ctrl+D or 'exit'"
    echo ""

    docker exec -it "$CONTAINER_NAME" bash -c "cd $TOOLS_DIR && exec bash"
}

run_script() {
    local script="$1"
    shift
    local args=("$@")

    # Build command
    local cmd="cd $TOOLS_DIR && ./$script"

    # Add arguments (properly quoted)
    if [ ${#args[@]} -gt 0 ]; then
        # Use printf %q for proper shell quoting
        for arg in "${args[@]}"; do
            cmd="$cmd $(printf '%q' "$arg")"
        done
    fi

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}Dry run mode - would execute:${NC}"
        echo "docker exec $CONTAINER_NAME bash -c \"$cmd\""
        exit 0
    fi

    # Execute in container
    docker exec "$CONTAINER_NAME" bash -c "$cmd"
}

#------------------------------------------------------------------------------
# Main Script
#------------------------------------------------------------------------------

# No arguments - show help
if [ $# -eq 0 ]; then
    show_help
    exit 2
fi

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)
            show_help
            exit 0
            ;;
        --list|-l)
            list_scripts
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --interactive|-i)
            INTERACTIVE=true
            shift
            ;;
        -*)
            echo -e "${RED}❌ Error: Unknown option: $1${NC}" >&2
            echo "Use --help for usage information" >&2
            exit 2
            ;;
        *)
            # First non-option argument is the script name
            break
            ;;
    esac
done

# Check container is running
check_container

# Interactive mode
if [ "$INTERACTIVE" = true ]; then
    run_interactive
    exit 0
fi

# Need at least script name
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Error: No script specified${NC}" >&2
    echo "Usage: ./in-devcontainer.sh <script> [args...]" >&2
    echo "Use --help for more information" >&2
    exit 2
fi

# Get script name and resolve aliases
SCRIPT_INPUT="$1"
shift
SCRIPT_NAME=$(resolve_script_name "$SCRIPT_INPUT")

# Verify script exists
check_script_exists "$SCRIPT_NAME"

# Run the script with all remaining arguments
run_script "$SCRIPT_NAME" "$@"
