# Makefile for Go projects with comprehensive quality checks
# Copy this to your project root and customize as needed

.PHONY: all build test lint coverage race benchmark clean help validate security

# Variables
BINARY_NAME := myapp
GO := go
GOLANGCI_LINT := golangci-lint
STATICCHECK := staticcheck
GOPATH := $(shell go env GOPATH)
MIN_COVERAGE := 80

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

## help: Display this help message
help:
	@echo "Available targets:"
	@grep -E '^##' Makefile | sed 's/## //'

## all: Run all quality checks and build
all: validate build

## build: Build the binary
build:
	@echo "$(GREEN)Building $(BINARY_NAME)...$(NC)"
	$(GO) build -v -o $(BINARY_NAME) ./...

## test: Run all tests
test:
	@echo "$(GREEN)Running tests...$(NC)"
	$(GO) test -v -timeout 30s ./...

## coverage: Run tests with coverage and enforce minimum
coverage:
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	@$(GO) test -v -race -coverprofile=coverage.out -covermode=atomic ./...
	@$(GO) tool cover -html=coverage.out -o coverage.html
	@echo "$(GREEN)Coverage report generated: coverage.html$(NC)"
	@coverage=$$(go tool cover -func=coverage.out | grep total | awk '{print $$3}' | sed 's/%//'); \
	if [ $${coverage%.*} -lt $(MIN_COVERAGE) ]; then \
		echo "$(RED)❌ Coverage $${coverage}% is below minimum $(MIN_COVERAGE)%$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)✅ Coverage $${coverage}% meets minimum requirement$(NC)"; \
	fi

## race: Run race condition detector
race:
	@echo "$(GREEN)Running race detector...$(NC)"
	$(GO) test -race -timeout 60s ./...
	@echo "$(GREEN)✅ No race conditions detected$(NC)"

## benchmark: Run benchmarks
benchmark:
	@echo "$(GREEN)Running benchmarks...$(NC)"
	$(GO) test -bench=. -benchmem -run=^$$ ./... | tee benchmark.txt
	@echo "$(GREEN)Benchmark results saved to benchmark.txt$(NC)"

## lint: Run linters (golangci-lint and staticcheck)
lint:
	@echo "$(GREEN)Running golangci-lint...$(NC)"
	$(GOLANGCI_LINT) run --timeout=5m ./...
	@echo "$(GREEN)Running staticcheck...$(NC)"
	$(STATICCHECK) ./...
	@echo "$(GREEN)✅ All linting checks passed$(NC)"

## fmt: Format code
fmt:
	@echo "$(GREEN)Formatting code...$(NC)"
	$(GO) fmt ./...
	gofumpt -l -w .
	@echo "$(GREEN)✅ Code formatted$(NC)"

## vet: Run go vet
vet:
	@echo "$(GREEN)Running go vet...$(NC)"
	$(GO) vet ./...

## mod: Tidy and verify module dependencies
mod:
	@echo "$(GREEN)Tidying modules...$(NC)"
	$(GO) mod tidy
	$(GO) mod verify
	@echo "$(GREEN)✅ Modules verified$(NC)"

## security: Run security checks
security:
	@echo "$(GREEN)Running security checks...$(NC)"
	@which gosec > /dev/null || (echo "Installing gosec..." && go install github.com/securego/gosec/v2/cmd/gosec@latest)
	gosec -fmt json -out security-report.json ./...
	@echo "$(GREEN)Security report generated: security-report.json$(NC)"
	@which nancy > /dev/null || (echo "Installing nancy..." && go install github.com/sonatype-nexus-community/nancy@latest)
	$(GO) list -json -deps ./... | nancy sleuth
	@echo "$(GREEN)✅ Security checks completed$(NC)"

## validate: Run all validation checks (lint, test, coverage, race)
validate: fmt vet lint test coverage race
	@echo "$(GREEN)✅ All validation checks passed!$(NC)"

## clean: Clean build artifacts
clean:
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	rm -f $(BINARY_NAME)
	rm -f coverage.out coverage.html
	rm -f benchmark.txt
	rm -f security-report.json
	rm -rf dist/
	@echo "$(GREEN)✅ Cleaned$(NC)"

## install-tools: Install required development tools
install-tools:
	@echo "$(GREEN)Installing development tools...$(NC)"
	@which golangci-lint > /dev/null || curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(GOPATH)/bin
	@which staticcheck > /dev/null || go install honnef.co/go/tools/cmd/staticcheck@latest
	@which gofumpt > /dev/null || go install mvdan.cc/gofumpt@latest
	@which gosec > /dev/null || go install github.com/securego/gosec/v2/cmd/gosec@latest
	@which nancy > /dev/null || go install github.com/sonatype-nexus-community/nancy@latest
	@echo "$(GREEN)✅ All tools installed$(NC)"

## docker-build: Build Docker image
docker-build:
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t $(BINARY_NAME):latest .

## ci: Run CI pipeline locally
ci: install-tools validate security
	@echo "$(GREEN)✅ CI pipeline completed successfully$(NC)"

# Watch for changes and run tests
watch:
	@which reflex > /dev/null || go install github.com/cespare/reflex@latest
	reflex -r '\.go$$' -s -- sh -c 'clear && make test'
