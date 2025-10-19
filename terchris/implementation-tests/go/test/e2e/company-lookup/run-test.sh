#!/bin/bash
# file: go/test/e2e/company-lookup/run-test.sh
#
# Run the company-lookup E2E test for Go
#

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧪 Running Go company-lookup E2E test..."
echo "Working directory: $(pwd)"

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    echo "✅ Loaded .env file"
else
    echo "⚠️  No .env file found"
fi

# Clean logs
rm -rf logs
mkdir -p logs
echo "✅ Cleaned log directory"

# Build the test program
echo "🔨 Building Go test program..."
cd /workspace/go
go build -o test/e2e/company-lookup/company-lookup test/e2e/company-lookup/main.go
echo "✅ Build complete"

# Run the test
echo "🚀 Running test..."
cd test/e2e/company-lookup
./company-lookup

echo "✅ Test execution complete"
echo "📝 Logs written to: $(pwd)/logs/"
