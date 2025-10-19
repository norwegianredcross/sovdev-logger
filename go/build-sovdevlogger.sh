#!/bin/bash
# filename: go/build-sovdevlogger.sh
# description: Build the Go sovdev-logger library
#
# Purpose:
#   Builds the Go sovdev-logger library and verifies dependencies.
#   Go is a compiled language, so this script handles dependency installation,
#   compilation verification, and optional binary building.
#
# Usage:
#   ./build-sovdevlogger.sh              # Download dependencies and verify build
#   ./build-sovdevlogger.sh test         # Run tests
#   ./build-sovdevlogger.sh clean        # Clean build cache
#
# Environment:
#   - Must run inside devcontainer (uses Go toolchain)
#   - Requires go.mod configured
#   - Uses Go modules for dependency management
#
# Exit Codes:
#   0 - Build successful
#   1 - Build failed (compilation errors, missing dependencies, etc.)
#
# Examples:
#   # Human developers (VSCode terminal inside container):
#   cd go
#   ./build-sovdevlogger.sh
#
#   # LLM developers (host machine):
#   ./specification/tools/in-devcontainer.sh -e "cd /workspace/go && ./build-sovdevlogger.sh"
#
# Related:
#   - go.mod: Go module definition
#   - go.sum: Dependency checksums
#   - specification/10-development-loop.md: Development workflow documentation

set -e  # Exit on error
set -o pipefail  # Catch errors in pipes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to script directory
cd "$(dirname "$0")"

# Parse command line arguments
RUN_TESTS=false
CLEAN_BUILD=false

if [ "$1" == "test" ]; then
  RUN_TESTS=true
elif [ "$1" == "clean" ]; then
  CLEAN_BUILD=true
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Building Go sovdev-logger${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Clean build if requested
if [ "$CLEAN_BUILD" = true ]; then
  echo -e "${YELLOW}🧹 Cleaning build cache...${NC}"
  go clean -cache -modcache -testcache
  echo -e "${GREEN}✅ Clean complete${NC}"
  echo ""
  exit 0
fi

# Download dependencies
echo -e "${BLUE}📦 Downloading dependencies...${NC}"
go mod download
echo -e "${GREEN}✅ Dependencies downloaded${NC}"
echo ""

# Verify dependencies
echo -e "${BLUE}🔍 Verifying dependencies...${NC}"
go mod verify
echo -e "${GREEN}✅ Dependencies verified${NC}"
echo ""

# Build (verify compilation)
echo -e "${BLUE}🔨 Verifying build...${NC}"
go build ./...
echo -e "${GREEN}✅ Build verification successful${NC}"
echo ""

# Run tests if requested
if [ "$RUN_TESTS" = true ]; then
  echo -e "${BLUE}🧪 Running tests...${NC}"
  go test ./... -v
  echo ""
fi

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Go sovdev-logger ready!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📦 Module: $(go list -m)"
echo "🔧 Go version: $(go version | awk '{print $3}')"
echo ""
