#!/bin/bash

# ============================================================================
# Company-Lookup E2E Test Runner - Python Implementation
# ============================================================================
#
# PURPOSE:
# Standardized test runner for the company-lookup E2E test.
# All validation tools in specification/tools/ execute this script.
#
# WHAT THIS SCRIPT DOES:
# 1. Clean old logs
# 2. Load environment variables from .env
# 3. Execute the Python test script
# 4. Validate log output (unless --skip-validation flag is set)
#
# USAGE:
#   ./run-test.sh                    # Run test with validation
#   ./run-test.sh --skip-validation  # Run test without validation
# ============================================================================

set -e  # Exit on error

# Get script directory (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
SKIP_VALIDATION=false
if [ "$1" == "--skip-validation" ]; then
    SKIP_VALIDATION=true
fi

echo "============================================"
echo "Company-Lookup E2E Test - Python"
echo "============================================"
echo ""

# ============================================================================
# Step 1: Clean Old Logs
# ============================================================================
echo "📁 Cleaning old log files..."
rm -rf logs/*.log 2>/dev/null || true
mkdir -p logs
echo "✅ Log directory ready"
echo ""

# ============================================================================
# Step 2: Load Environment Variables
# ============================================================================
echo "🔧 Loading environment variables from .env..."
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  No .env file found, using defaults"
fi
echo ""

# ============================================================================
# Step 3: Execute Python Test
# ============================================================================
echo "🚀 Running Python test..."
echo ""

# Run the Python test script
python3 company-lookup.py

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ Test program completed successfully"
else
    echo "❌ Test program failed with exit code $TEST_EXIT_CODE"
    exit $TEST_EXIT_CODE
fi

# ============================================================================
# Step 4: Validate Log Output (unless skipped)
# ============================================================================
if [ "$SKIP_VALIDATION" == "false" ]; then
    echo ""
    echo "🔍 Validating log output..."
    echo ""

    # Call validation script (assumes it's in specification/tools/)
    VALIDATION_SCRIPT="../../../../../specification/tools/validate-log-format.sh"

    if [ -f "$VALIDATION_SCRIPT" ]; then
        "$VALIDATION_SCRIPT" logs/dev.log
        VALIDATION_EXIT_CODE=$?

        echo ""
        if [ $VALIDATION_EXIT_CODE -eq 0 ]; then
            echo "✅ Log validation passed"
        else
            echo "❌ Log validation failed"
            exit $VALIDATION_EXIT_CODE
        fi
    else
        echo "⚠️  Validation script not found: $VALIDATION_SCRIPT"
        echo "   Skipping log validation"
    fi
fi

echo ""
echo "============================================"
echo "✅ Test PASSED"
echo "============================================"
