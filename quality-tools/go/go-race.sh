#!/bin/bash
# Go Race Condition Detector
# Critical for trading systems with concurrent operations

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🏃 Running Go race detector..."
echo "This is critical for financial applications with concurrent operations"
echo ""

# Run with race detector
echo "Testing with -race flag..."
if go test -race -timeout 30s ./... 2>&1 | tee race_output.txt; then
    echo -e "${GREEN}✅ No race conditions detected${NC}"
    rm -f race_output.txt
else
    echo -e "${RED}❌ Race conditions detected!${NC}"
    echo ""
    echo "Race condition details:"
    grep -A 10 "WARNING: DATA RACE" race_output.txt || true
    exit 1
fi

echo ""
echo "🔍 Running extended race detection with stress testing..."

# Stress test with multiple iterations
STRESS_COUNT=${STRESS_COUNT:-10}
echo "Running $STRESS_COUNT iterations to catch intermittent races..."

for i in $(seq 1 $STRESS_COUNT); do
    echo -n "Iteration $i/$STRESS_COUNT... "
    if go test -race -count=1 -timeout 30s ./... > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Race detected!${NC}"
        go test -race -count=1 -timeout 30s ./... 2>&1 | grep -A 10 "WARNING: DATA RACE"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}✅ All stress tests passed without race conditions${NC}"

# Run specific concurrent tests if they exist
echo ""
echo "🔄 Checking for concurrent test coverage..."

if grep -r "t.Parallel()" . --include="*_test.go" > /dev/null 2>&1; then
    echo "Found parallel tests, running with increased parallelism..."
    go test -race -parallel 8 -timeout 60s ./...
else
    echo -e "${YELLOW}⚠️  No parallel tests found. Consider adding t.Parallel() to test concurrent behavior${NC}"
fi

echo ""
echo "💡 Tips for avoiding race conditions in financial applications:"
echo "  • Use channels instead of shared memory"
echo "  • Protect shared state with mutexes"
echo "  • Use sync/atomic for simple counters"
echo "  • Consider using sync.Once for initialization"
echo "  • Use context for cancellation propagation"
