#!/bin/bash
# filename: python/build-sovdevlogger.sh
# description: Build the Python sovdev-logger library
#
# Purpose:
#   Builds the Python sovdev-logger library for distribution.
#   Python is interpreted, but this script handles dependency installation
#   and optional wheel building for distribution.
#
# Usage:
#   ./build-sovdevlogger.sh              # Install in editable mode
#   ./build-sovdevlogger.sh wheel        # Build distribution wheel
#   ./build-sovdevlogger.sh clean        # Clean build artifacts
#
# Environment:
#   - Must run inside devcontainer (uses Python toolchain)
#   - Requires pyproject.toml or setup.py configured
#   - Installs package in editable mode for development
#
# Exit Codes:
#   0 - Build successful
#   1 - Build failed (missing dependencies, configuration errors, etc.)
#
# Examples:
#   # Human developers (VSCode terminal inside container):
#   cd python
#   ./build-sovdevlogger.sh
#
#   # LLM developers (host machine):
#   ./specification/tools/in-devcontainer.sh -e "cd /workspace/python && ./build-sovdevlogger.sh"
#
# Related:
#   - pyproject.toml: Python project configuration
#   - setup.py: Legacy Python setup configuration (if present)
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
BUILD_WHEEL=false
CLEAN_BUILD=false

if [ "$1" == "wheel" ]; then
  BUILD_WHEEL=true
elif [ "$1" == "clean" ]; then
  CLEAN_BUILD=true
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Building Python sovdev-logger${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Clean build if requested
if [ "$CLEAN_BUILD" = true ]; then
  echo -e "${YELLOW}🧹 Cleaning previous build...${NC}"
  rm -rf build/ dist/ *.egg-info .eggs/
  find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
  echo -e "${GREEN}✅ Clean complete${NC}"
  echo ""
  exit 0
fi

# Build wheel if requested
if [ "$BUILD_WHEEL" = true ]; then
  echo -e "${BLUE}🔨 Building distribution wheel...${NC}"
  python -m build
  echo ""

  if [ -d "dist" ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Wheel build successful!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "📂 Distribution directory: dist/"
    echo "📄 Files generated:"
    ls -lh dist/ | tail -n +2 | awk '{print "   - " $9 " (" $5 ")"}'
    echo ""
  else
    echo -e "${RED}❌ Wheel build failed - dist/ directory not created${NC}"
    exit 1
  fi
else
  # Default: Install in editable mode for development
  echo -e "${BLUE}📦 Installing package in editable mode...${NC}"
  pip install -e .
  echo ""

  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${GREEN}✅ Installation successful!${NC}"
  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  echo "📦 Package installed in editable mode"
  echo "🔧 Changes to source files are immediately available"
  echo ""
fi
