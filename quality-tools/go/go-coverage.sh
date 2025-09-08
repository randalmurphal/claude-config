#!/bin/bash
# Go Test Coverage Enforcer
# Ensures minimum test coverage for Go projects

set -e

# Configuration
MIN_COVERAGE=${MIN_COVERAGE:-80}
COVERAGE_FILE="coverage.out"
HTML_FILE="coverage.html"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 Running Go tests with coverage..."

# Run tests with coverage
go test -v -race -coverprofile="$COVERAGE_FILE" -covermode=atomic ./...

# Generate HTML report
go tool cover -html="$COVERAGE_FILE" -o "$HTML_FILE"

# Calculate total coverage
COVERAGE=$(go tool cover -func="$COVERAGE_FILE" | grep total | awk '{print $3}' | sed 's/%//')

# Extract integer part for comparison
COVERAGE_INT=${COVERAGE%.*}

echo ""
echo "📊 Coverage Report Generated: $HTML_FILE"
echo "📈 Total Coverage: ${COVERAGE}%"
echo ""

# Check if coverage meets minimum requirement
if [ "$COVERAGE_INT" -lt "$MIN_COVERAGE" ]; then
    echo -e "${RED}❌ Coverage ${COVERAGE}% is below minimum required ${MIN_COVERAGE}%${NC}"
    echo ""
    echo "Uncovered lines by package:"
    go tool cover -func="$COVERAGE_FILE" | grep -v "100.0%" | grep -v "total:" | head -20
    exit 1
else
    echo -e "${GREEN}✅ Coverage ${COVERAGE}% meets minimum requirement of ${MIN_COVERAGE}%${NC}"
fi

# Show top uncovered files (useful even when passing)
echo ""
echo "📝 Files with lowest coverage:"
go tool cover -func="$COVERAGE_FILE" | grep -v "100.0%" | sort -k3 -n | head -10

# Performance metrics
echo ""
echo "⚡ Performance Metrics:"
go test -bench=. -benchmem -run=^$ ./... | grep -E "Benchmark|ns/op|allocs/op" | head -20
