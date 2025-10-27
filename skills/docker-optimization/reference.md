# Docker Image Optimization Reference Guide

**Companion to SKILL.md** - Detailed examples, full Dockerfiles, and advanced patterns.

---

## Table of Contents

1. [Common Dockerfile Patterns](#common-dockerfile-patterns)
2. [M32RIMM-Specific Implementation](#m32rimm-specific-implementation)
3. [Build Performance Details](#build-performance-details)
4. [Health Check Implementation](#health-check-implementation)
5. [Security Scanning Deep Dive](#security-scanning-deep-dive)
6. [Benchmarks and Measurements](#benchmarks-and-measurements)

---

## Common Dockerfile Patterns

### Pattern 1: Flask/FastAPI Web App

Complete production-ready Dockerfile for web applications.

```dockerfile
FROM python:3.11-slim as builder

# Build dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

WORKDIR /app

# Copy dependencies
COPY --from=builder /root/.local /root/.local

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Use case**: REST API, web dashboard, microservice

**Size**: ~300MB

**Features**:
- Multi-stage build (excludes build tools)
- Non-root user for security
- Health check for orchestration
- Optimized layer caching

---

### Pattern 2: Data Processing Script (M32RIMM Use Case)

```dockerfile
FROM python:3.11-slim as builder

# System build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Runtime system dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

WORKDIR /app

# Copy dependencies
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY fisio/ ./fisio/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check (process-based for non-web app)
HEALTHCHECK --interval=60s --timeout=5s --retries=3 \
    CMD pgrep -f "python -m fisio.imports" || exit 1

# Run import (override with docker run command for specific import)
CMD ["python", "-m", "fisio.imports.tenable_sc_refactor.tenable_sc_import"]
```

**Use case**: Scheduled imports, batch processing, ETL jobs

**Size**: ~350MB

**Running different imports**:
```bash
# Tenable SC import
docker run myimport:latest python -m fisio.imports.tenable_sc_refactor.tenable_sc_import --sub-id $SUB1

# NVD import
docker run myimport:latest python -m fisio.imports.nvd_api.nvd_import --sub-id $SUB1
```

---

### Pattern 3: Distroless Production

Maximum security with no shell access.

```dockerfile
FROM python:3.11-slim as builder

# Install dependencies to specific directory
WORKDIR /app
COPY requirements.txt .
RUN pip install --target /app/dependencies --no-cache-dir -r requirements.txt

# Distroless runtime (no shell, highest security)
FROM gcr.io/distroless/python3-debian11

# Set Python path to include dependencies
ENV PYTHONPATH=/app/dependencies \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependencies
COPY --from=builder /app/dependencies /app/dependencies

# Copy application
COPY . /app

# Non-root user (distroless already runs as non-root)
USER nonroot

# Run application (list format, no shell)
CMD ["app.py"]
```

**Use case**: Production deployments with strict security requirements

**Size**: ~250MB

**Security**: No shell, no package manager, minimal attack surface

**Debugging**: Build with `--target builder` to access shell

```bash
# Debug build (has shell)
docker build --target builder -t myapp:debug .
docker run -it myapp:debug /bin/bash

# Production build (distroless, no shell)
docker build -t myapp:prod .
docker run myapp:prod
```

---

### Pattern 4: Multi-Service Application

```dockerfile
# Backend dependencies
FROM python:3.11-slim as backend-builder
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Frontend build
FROM node:18-slim as frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --production
COPY frontend/ .
RUN npm run build

# Final runtime
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

WORKDIR /app

# Copy backend dependencies
COPY --from=backend-builder /root/.local /root/.local

# Copy frontend build artifacts
COPY --from=frontend-builder /app/dist /app/static

# Copy backend code
COPY backend/ ./backend/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0"]
```

**Use case**: Full-stack application, monolithic app with frontend

**Size**: ~400MB

---

## M32RIMM-Specific Implementation

### Containerizing Imports

**Recommended pattern**: Multi-stage slim with mounted volumes

```dockerfile
FROM python:3.11-slim as builder

# Build dependencies (PostgreSQL client libs, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime
FROM python:3.11-slim

# Runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

WORKDIR /app

# Copy dependencies
COPY --from=builder /root/.local /root/.local

# Copy fisio module
COPY fisio/ ./fisio/

# Non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /home/appuser/.m32rimm && \
    chown -R appuser:appuser /app /home/appuser/.m32rimm
USER appuser

CMD ["python", "-m", "fisio.imports.tenable_sc_refactor.tenable_sc_import"]
```

### Volume Mounts (Don't Bake Config Into Image)

```bash
# Mount config file (not baked into image)
docker run \
    -v /etc/fis/fis-config.json:/etc/fis/fis-config.json:ro \
    -v /home/appuser/.m32rimm:/home/appuser/.m32rimm \
    -e SUB1=$SUB1 \
    myimport:latest \
    python -m fisio.imports.tenable_sc_refactor.tenable_sc_import --sub-id $SUB1
```

**Why**:
- Config changes don't require image rebuild
- Same image works for all environments (dev, staging, prod)
- Secrets not baked into image layers

### Secrets Management

**NEVER put in Dockerfile**:
- MongoDB credentials
- Redis passwords
- Tenable SC API keys
- NVD API keys

**Use environment variables at runtime**:
```bash
docker run \
    -e MONGODB_URI=mongodb://user:pass@localhost:27017 \
    -e TENABLE_API_KEY=secret \
    myimport:latest
```

**Or use Docker secrets** (Swarm/Kubernetes):
```bash
# Create secret
echo "mongodb://user:pass@localhost:27017" | docker secret create mongodb_uri -

# Use in service
docker service create \
    --secret mongodb_uri \
    --env MONGODB_URI_FILE=/run/secrets/mongodb_uri \
    myimport:latest
```

### Cache Directory Persistence

```bash
# Mount cache directory to survive container restarts
docker run \
    -v ~/.m32rimm/$SUB1:/home/appuser/.m32rimm/$SUB1 \
    myimport:latest
```

**Why**: Persistent DAA staging DB survives across scan imports

### Distroless for Production

**For production deployments of imports**:
```dockerfile
# Same builder stage as above...

# Production runtime (distroless)
FROM gcr.io/distroless/python3-debian11

ENV PYTHONPATH=/app:/root/.local/lib/python3.11/site-packages \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependencies and app
COPY --from=builder /root/.local /root/.local
COPY fisio/ ./fisio/

USER nonroot

CMD ["fisio/imports/tenable_sc_refactor/tenable_sc_import.py"]
```

**Benefit**: No shell for attackers if container compromised

### M32RIMM-Specific Health Checks

**For imports (non-web apps)**:
```dockerfile
# Option 1: Check process is running
HEALTHCHECK --interval=60s CMD pgrep -f "tenable_sc_import" || exit 1

# Option 2: Check heartbeat file
HEALTHCHECK --interval=60s CMD test $(find /tmp/import_heartbeat -mmin -5) || exit 1
```

**Heartbeat in import code**:
```python
from pathlib import Path
from datetime import datetime

class TenableSCImport:
    def __init__(self):
        self.heartbeat_file = Path('/tmp/import_heartbeat')

    def _update_heartbeat(self):
        """Update heartbeat file to indicate process is alive"""
        self.heartbeat_file.touch()

    def process_scan(self, scan_id):
        self._update_heartbeat()
        # ... process scan ...
```

---

## Build Performance Details

### Enable BuildKit

**What**: Next-generation Docker build system with parallel builds, better caching, and cache mounts.

**Enable globally**:
```bash
# Linux/Mac
export DOCKER_BUILDKIT=1
echo 'export DOCKER_BUILDKIT=1' >> ~/.bashrc

# Docker daemon config (permanent)
# Edit /etc/docker/daemon.json
{
  "features": {
    "buildkit": true
  }
}
```

**Enable per-build**:
```bash
DOCKER_BUILDKIT=1 docker build .
```

### Cache Mounts

**Problem**: Pip downloads same packages on every build

**Solution**: Mount persistent cache directory

```dockerfile
# Without cache mount (downloads every time)
RUN pip install -r requirements.txt
# 2 minutes per build

# With cache mount (reuses downloads)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
# 10 seconds after first build
```

**Other cache mount examples**:

```dockerfile
# Apt cache
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y gcc

# npm cache
RUN --mount=type=cache,target=/root/.npm \
    npm install
```

### Parallel Builds

**BuildKit automatically parallelizes independent stages**:

```dockerfile
# These stages run in parallel
FROM python:3.11-slim as backend-deps
RUN pip install flask sqlalchemy

FROM node:18-slim as frontend-deps
RUN npm install react vue

# Final stage waits for both
FROM python:3.11-slim
COPY --from=backend-deps /root/.local /root/.local
COPY --from=frontend-deps /app/node_modules /app/node_modules
```

### Multi-Platform Builds

**Build for both ARM and x86**:

```bash
# Setup buildx
docker buildx create --name multiarch --use

# Build for multiple platforms
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t myapp:latest \
    --push \
    .
```

**Use case**: Apple Silicon (M1/M2) + AWS EC2 deployment

### Build Performance Checklist

- [ ] Enable BuildKit (`DOCKER_BUILDKIT=1`)
- [ ] Use cache mounts for package managers
- [ ] Order layers for maximum cache hits
- [ ] Use `.dockerignore` to reduce context size
- [ ] Use multi-stage builds to parallelize
- [ ] Build multi-platform only when needed (slower)

**Typical improvements**: 10 minute builds → 30 seconds (with warm cache)

---

## Health Check Implementation

### What Are Health Checks?

Mechanism for Docker/Kubernetes to determine if container is healthy (can serve requests, process data, etc.)

**Purpose**:
- Automatic restart of unhealthy containers
- Load balancer traffic routing (only send to healthy instances)
- Deployment health validation (wait for health before marking complete)

### Dockerfile HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s \
            --timeout=3s \
            --start-period=5s \
            --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"
```

**Parameters**:
- `--interval=30s`: Check every 30 seconds
- `--timeout=3s`: Health check must complete in 3 seconds
- `--start-period=5s`: Grace period before first check (app startup time)
- `--retries=3`: Mark unhealthy after 3 consecutive failures

### Health Check Patterns

**Pattern 1: HTTP endpoint** (web apps)
```dockerfile
# Requires app to expose /health endpoint
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1
```

**Pattern 2: Python script** (web apps without curl)
```dockerfile
HEALTHCHECK CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)" || exit 1
```

**Pattern 3: Process check** (non-web apps)
```dockerfile
# Check if process is running
HEALTHCHECK CMD pgrep -f "python app.py" || exit 1
```

**Pattern 4: File check** (data processing apps)
```dockerfile
# Check if heartbeat file updated recently (5 minutes)
HEALTHCHECK CMD test $(find /tmp/heartbeat -mmin -5) || exit 1

# App writes heartbeat:
# while True:
#     Path('/tmp/heartbeat').touch()
#     do_work()
```

**Pattern 5: Database connection** (database-dependent apps)
```dockerfile
HEALTHCHECK CMD python -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017').server_info()" || exit 1
```

### Implementing /health Endpoint

**Flask**:
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    # Add actual health checks here
    # - Database connection
    # - Redis connection
    # - Disk space
    return jsonify({"status": "healthy"}), 200
```

**FastAPI**:
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

---

## Security Scanning Deep Dive

### CI/CD Integration

**GitHub Actions**:
```yaml
name: Build and Scan

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Run Trivy scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'  # Fail build if vulnerabilities found

      - name: Upload results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
```

**GitLab CI**:
```yaml
trivy-scan:
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - wget -qO - https://github.com/aquasecurity/trivy/releases/download/v0.48.0/trivy_0.48.0_Linux-64bit.tar.gz | tar zxvf -
    - ./trivy image --exit-code 1 --severity CRITICAL $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
```

### Interpreting Trivy Results

**Trivy output example**:
```
myapp:latest (debian 11.7)

Total: 45 (HIGH: 12, CRITICAL: 3)

┌─────────────────┬──────────────┬──────────┬───────────────────┐
│     Library     │ Vulnerability│ Severity │  Installed Ver    │
├─────────────────┼──────────────┼──────────┼───────────────────┤
│ openssl         │ CVE-2023-1234│ CRITICAL │ 1.1.1n-0+deb11u4  │
│ libssl1.1       │ CVE-2023-1234│ CRITICAL │ 1.1.1n-0+deb11u4  │
│ curl            │ CVE-2023-5678│ HIGH     │ 7.74.0-1.3+deb11u7│
└─────────────────┴──────────────┴──────────┴───────────────────┘
```

### Fixing Vulnerabilities

**Step 1**: Update base image
```dockerfile
# Check for newer patch version
FROM python:3.11.8-slim  # instead of 3.11.0-slim
```

**Step 2**: Update dependencies
```bash
# Update requirements.txt with latest secure versions
pip list --outdated
pip install --upgrade <package>
pip freeze > requirements.txt
```

**Step 3**: Rebuild and rescan
```bash
docker build -t myapp:latest .
trivy image --severity HIGH,CRITICAL myapp:latest
```

### Security Scanning Best Practices

1. **Scan base images before using**: `trivy image python:3.11-slim`
2. **Scan during build**: Fail CI/CD on CRITICAL vulnerabilities
3. **Scan regularly**: Scheduled scans of deployed images (weekly)
4. **Monitor advisories**: Subscribe to security mailing lists for dependencies
5. **Use distroless**: Fewer packages = fewer vulnerabilities

---

## Benchmarks and Measurements

### Real-World Size Comparison

**Scenario**: Flask API with PostgreSQL, Redis, 25 Python dependencies

| Configuration | Size | Build Time | Notes |
|--------------|------|------------|-------|
| Basic single-stage | 1.2GB | 180s | Baseline |
| + slim base | 800MB | 120s | 33% reduction |
| + multi-stage | 400MB | 90s | 67% reduction |
| + .dockerignore | 350MB | 60s | 71% reduction |
| + all optimizations | 280MB | 45s | 77% reduction |
| Alpine multi-stage | 150MB | 240s | 87% reduction, slow build, C extension issues |
| Distroless multi-stage | 250MB | 50s | 79% reduction, highest security |

**Recommended**: Multi-stage slim with all optimizations (280MB, 45s builds)

### Build Time Comparison (Warm Cache)

| Configuration | First Build | Rebuild (code change) | Rebuild (dep change) |
|--------------|-------------|----------------------|---------------------|
| Poor layer order | 180s | 180s | 180s |
| Good layer order | 180s | 10s | 120s |
| + BuildKit cache mounts | 180s | 10s | 30s |

**Takeaway**: Good layer order + BuildKit = 94% faster rebuilds

### Network Transfer Impact

**Scenario**: Deploy to 10 instances

| Image Size | Transfer Time (100 Mbps) | Monthly Bandwidth (1 deploy/day) |
|-----------|-------------------------|----------------------------------|
| 1.2GB | 96 seconds × 10 = 16 minutes | 360GB |
| 280MB | 22 seconds × 10 = 3.6 minutes | 84GB |

**Savings**: 13 minutes per deployment, 276GB/month bandwidth

### Real-World Results

**Typical Results**: 1.2GB → 300MB (75% reduction) with multi-stage slim builds

**Scenario**: Fixing a typo in `app.py`
- **Bad approach**: 5 minute rebuild (reinstalls all dependencies)
- **Good approach**: 10 second rebuild (uses cached layers)

---

## Additional Resources

**Documentation**:
- Docker multi-stage builds: https://docs.docker.com/build/building/multi-stage/
- BuildKit: https://docs.docker.com/build/buildkit/
- Distroless images: https://github.com/GoogleContainerTools/distroless
- Trivy security scanner: https://aquasecurity.github.io/trivy/

**Best Practices**:
- Docker best practices: https://docs.docker.com/develop/dev-best-practices/
- Python Docker guide: https://docs.python.org/3/using/docker.html

**Security**:
- CIS Docker Benchmark: https://www.cisecurity.org/benchmark/docker
- OWASP Docker Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html

---

**Last Updated**: 2025-10-27
**Version**: 1.1
