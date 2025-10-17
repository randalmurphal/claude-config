# Docker Image Optimization for Python

**Name**: docker-optimization
**Description**: Optimize Docker images for Python applications including multi-stage builds (70%+ size reduction), security scanning with Trivy, layer caching, and distroless base images. Use when creating Dockerfiles, reducing image size, or improving build performance.
**Allowed Tools**: Read, Bash
**Last Updated**: 2025-10-17

---

## Quick Reference

| Optimization | Benefit | Complexity |
|-------------|---------|------------|
| Multi-stage builds | 70-90% size reduction | Low |
| Distroless base | Highest security (no shell) | Medium |
| Layer caching | Faster builds (90%+ cache hits) | Low |
| `.dockerignore` | Smaller context, faster uploads | Low |
| Security scanning | Vulnerability detection | Low |

**Typical Results**: 1.2GB → 300MB (75% reduction) with multi-stage slim builds

---

## 1. Multi-Stage Build Pattern (Primary Optimization)

### Concept
Separate build stage (compilers, headers, build tools) from runtime stage (only compiled artifacts and runtime dependencies).

### Benefits
- **70-90% size reduction**: Exclude gcc, make, headers from final image
- **Faster deployments**: Smaller images = faster pulls/pushes
- **Cleaner runtime**: Only production dependencies in final image

### Pattern

```dockerfile
# Stage 1: Build - includes build tools
FROM python:3.11-slim as builder
WORKDIR /app

# Install system build dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies to user site-packages
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime - minimal dependencies only
FROM python:3.11-slim
WORKDIR /app

# Copy only the installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Ensure PATH includes user site-packages
ENV PATH=/root/.local/bin:$PATH

CMD ["python", "app.py"]
```

### Why It Works

**Builder stage**: Has compilers, headers, and build tools needed to compile C extensions in Python packages (numpy, cryptography, lxml, etc.)

**Runtime stage**: Only has compiled wheels and runtime libraries, excludes build tools (typically 500MB-1GB savings)

### Before/After Example

```dockerfile
# BEFORE: Single-stage (1.2GB final image)
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]

# AFTER: Multi-stage (300MB final image)
FROM python:3.11-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]
```

**Size reduction**: 1.2GB → 300MB (75% reduction)

---

## 2. Base Image Selection

### Available Options

| Base Image | Size | Use Case | Pros | Cons |
|-----------|------|----------|------|------|
| `python:3.11-slim` | 45MB | General purpose | Good compatibility, Debian-based | Slightly larger than Alpine |
| `python:3.11-alpine` | 15MB | Size-critical apps | Smallest size | C extension issues (musl vs glibc) |
| `python:3.11-slim-bullseye` | 50MB | Specific Debian version | Version pinning | Slightly larger |
| `gcr.io/distroless/python3` | 50MB | Production security | No shell, minimal attack surface | Hard to debug |

### Recommendation Decision Tree

```
Start here → python:3.11-slim
    ├─ Need smallest possible? → python:3.11-alpine (test thoroughly!)
    ├─ Production deployment? → gcr.io/distroless/python3-debian11
    └─ Compatibility issues? → python:3.11-slim-bullseye
```

### Alpine Caveats

**Problem**: Alpine uses musl libc instead of glibc, causes issues with:
- Packages with C extensions (numpy, scipy, pillow)
- Wheels built for glibc (must compile from source)
- DNS resolution edge cases

**When to use**: Pure Python apps with no/few dependencies

**Example Alpine issue**:
```bash
# This works on slim:
pip install cryptography  # Downloads wheel, installs in seconds

# This on Alpine:
pip install cryptography  # Compiles from source, takes minutes, may fail
```

---

## 3. Distroless Images (2025 Best Practice)

### What Are Distroless Images?

Minimal images containing ONLY:
- Runtime dependencies (Python interpreter, shared libraries)
- Application code

**NOT included**: Shell, package manager, utilities, coreutils

**Maintained by**: Google (gcr.io/distroless/*)

### Security Benefits

- **Smaller attack surface**: No shell for attackers to exploit
- **No package manager**: Can't install malware post-compromise
- **CVE reduction**: Fewer binaries = fewer vulnerabilities
- **Compliance**: Meets strict security requirements

### Trade-offs

**Pros**:
- Highest security posture
- Smaller image size (similar to slim)
- Best for production deployments

**Cons**:
- No shell access (can't `docker exec -it` for debugging)
- Harder to troubleshoot runtime issues
- Must use multi-stage builds (can't install packages in runtime stage)

### Pattern

```dockerfile
# Stage 1: Build with full tooling
FROM python:3.11-slim as builder
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Distroless runtime
FROM gcr.io/distroless/python3-debian11
WORKDIR /app

# Copy installed packages
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Set environment
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

# CMD uses list format (no shell)
CMD ["app.py"]
```

### Debugging Distroless Images

**Problem**: No shell means can't debug runtime issues

**Solution**: Use `--target` flag to stop at builder stage

```bash
# Build and run builder stage (has shell)
docker build --target builder -t myapp:debug .
docker run -it myapp:debug /bin/bash

# Production build uses distroless
docker build -t myapp:latest .
```

### Distroless Variants

| Image | Base | Use Case |
|-------|------|----------|
| `gcr.io/distroless/python3-debian11` | Debian 11 | General Python 3.x |
| `gcr.io/distroless/python3-debian12` | Debian 12 | Latest Debian |
| `gcr.io/distroless/python3:debug` | With busybox shell | Debugging (use sparingly) |

**Recommendation**: Use `:debug` tag ONLY in development, never production

---

## 4. Layer Caching Optimization

### How Docker Layer Caching Works

- Each `RUN`, `COPY`, `ADD` creates a layer
- Docker caches layers that haven't changed
- Cache invalidated if ANY file in `COPY` changes
- All subsequent layers rebuild after cache miss

### Order Matters: Least-Changing First

**Cache-friendly order**:
1. System packages (rarely change)
2. `requirements.txt` (change occasionally)
3. Application code (changes frequently)

### Pattern: Optimal Layer Order

```dockerfile
FROM python:3.11-slim

# 1. System packages (cached unless Dockerfile changes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 2. Python dependencies (cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Application code (rebuilt on every code change)
COPY . .

CMD ["python", "app.py"]
```

### Before/After Example

```dockerfile
# BAD: Cache breaks on every code change
FROM python:3.11-slim
COPY . .  # Copies EVERYTHING, including code
RUN pip install -r requirements.txt  # Reinstalls deps on code change
CMD ["python", "app.py"]

# GOOD: Cache survives code changes
FROM python:3.11-slim
COPY requirements.txt .  # Only copies requirements
RUN pip install -r requirements.txt  # Cached unless requirements change
COPY . .  # Code changes don't invalidate deps
CMD ["python", "app.py"]
```

### Real-World Impact

**Scenario**: Fixing a typo in `app.py`

**Bad approach**: 5 minute rebuild (reinstalls all dependencies)
**Good approach**: 10 second rebuild (uses cached layers)

### Advanced: Cache Mounts (BuildKit)

**Requires**: Docker BuildKit (`DOCKER_BUILDKIT=1`)

```dockerfile
# Reuse pip cache across builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Benefits:
# - Pip downloads cached between builds
# - Faster builds when adding new dependencies
# - Doesn't affect image size (mount not persisted)
```

**Enable BuildKit**:
```bash
export DOCKER_BUILDKIT=1
docker build .
```

---

## 5. Dependency Installation Best Practices

### Core Flags

| Flag | Purpose | Savings |
|------|---------|---------|
| `--no-cache-dir` | Don't cache pip downloads | 100-200MB |
| `--user` | Install to user site-packages | Easier multi-stage COPY |
| `-r requirements.txt` | Pin exact versions | Reproducible builds |
| `--no-install-recommends` | Skip suggested apt packages | 50-100MB |

### Pattern: System + Python Dependencies

```dockerfile
# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*  # Clean apt cache

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
```

### Why Clean Apt Cache?

**Without cleanup**:
```dockerfile
RUN apt-get update && apt-get install -y gcc
# Creates layer with 100MB+ of package lists in /var/lib/apt/lists/
```

**With cleanup**:
```dockerfile
RUN apt-get update && apt-get install -y gcc \
    && rm -rf /var/lib/apt/lists/*
# Same packages, but removes 100MB of cached package lists
```

**Critical**: Must be in SAME `RUN` command (separate commands create separate layers, cache still in earlier layer)

### Requirements.txt Best Practices

**Pin exact versions** for reproducibility:
```text
# GOOD: Exact versions
flask==2.3.2
requests==2.31.0
sqlalchemy==2.0.19

# BAD: Unpinned (different builds get different versions)
flask
requests>=2.0
sqlalchemy~=2.0
```

**Generate pinned requirements**:
```bash
# In development environment:
pip freeze > requirements.txt
```

### Multi-Step Install Pattern

```dockerfile
# 1. System packages first
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Python packages that need compilation
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 3. Application code last
COPY . .
```

---

## 6. Image Size Reduction Techniques

### Complete Checklist

- [ ] Use multi-stage builds (exclude build tools)
- [ ] Use slim/alpine base images
- [ ] Add `.dockerignore` file
- [ ] Use `--no-cache-dir` with pip
- [ ] Clean apt cache in same RUN command
- [ ] Combine RUN commands to reduce layers
- [ ] Remove temporary files in same layer

### .dockerignore Pattern

Create `.dockerignore` in same directory as Dockerfile:

```gitignore
# Version control
.git/
.gitignore

# Python artifacts
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environments
venv/
env/
ENV/
.venv/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Documentation
*.md
docs/

# CI/CD
.github/
.gitlab-ci.yml

# Logs
*.log

# OS
.DS_Store
Thumbs.db
```

**Impact**: Reduces build context from 500MB to 50MB (10x reduction)

### Combining RUN Commands

```dockerfile
# BAD: Creates 3 layers, cache remains from earlier layers
RUN apt-get update
RUN apt-get install -y gcc
RUN rm -rf /var/lib/apt/lists/*
# Total: 250MB across 3 layers

# GOOD: Single layer, cleanup removes cache
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*
# Total: 150MB in 1 layer
```

### Real-World Size Comparison

**Scenario**: Flask app with PostgreSQL, 20 dependencies

| Approach | Size | Reduction |
|----------|------|-----------|
| Basic single-stage | 1.2GB | Baseline |
| + slim base | 800MB | 33% |
| + multi-stage | 400MB | 67% |
| + .dockerignore | 350MB | 71% |
| + all optimizations | 280MB | 77% |

---

## 7. Security Scanning with Trivy

### What Is Trivy?

Open-source vulnerability scanner for:
- Docker images (OS packages, language dependencies)
- Filesystems
- Git repositories
- Kubernetes manifests

**Maintained by**: Aqua Security

### Installation

```bash
# macOS
brew install aquasecurity/trivy/trivy

# Linux (binary)
wget https://github.com/aquasecurity/trivy/releases/download/v0.48.0/trivy_0.48.0_Linux-64bit.tar.gz
tar zxvf trivy_0.48.0_Linux-64bit.tar.gz
sudo mv trivy /usr/local/bin/

# Docker
docker run aquasec/trivy image python:3.11-slim
```

### Basic Scanning

```bash
# Scan a base image
trivy image python:3.11-slim

# Scan your built image
docker build -t myapp:latest .
trivy image myapp:latest

# Filter by severity
trivy image --severity HIGH,CRITICAL myapp:latest

# Output JSON for CI/CD
trivy image --format json --output results.json myapp:latest
```

### Interpreting Results

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

### Security Scanning Best Practices

1. **Scan base images before using**: `trivy image python:3.11-slim`
2. **Scan during build**: Fail CI/CD on CRITICAL vulnerabilities
3. **Scan regularly**: Scheduled scans of deployed images (weekly)
4. **Monitor advisories**: Subscribe to security mailing lists for dependencies
5. **Use distroless**: Fewer packages = fewer vulnerabilities

---

## 8. Build Performance Optimization

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

## 9. Python-Specific Optimizations

### Environment Variables

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```

| Variable | Purpose | Benefit |
|----------|---------|---------|
| `PYTHONDONTWRITEBYTECODE=1` | Don't create `.pyc` files | Smaller image, faster startup |
| `PYTHONUNBUFFERED=1` | Force stdout/stderr unbuffered | Better logging, see errors immediately |
| `PYTHONOPTIMIZE=1` | Enable optimizations, create `.pyo` | Faster execution (remove asserts) |
| `PIP_NO_CACHE_DIR=1` | Don't cache pip downloads | Smaller image (100-200MB) |
| `PIP_DISABLE_PIP_VERSION_CHECK=1` | Skip pip version check | Faster pip operations |

### When to Use PYTHONOPTIMIZE

**Use** (PYTHONOPTIMIZE=1):
- Production deployments
- Performance-critical applications
- When you don't rely on assertions

**Don't use** (PYTHONOPTIMIZE=0 or unset):
- Development environments
- When debugging
- If code relies on `assert` statements for logic (bad practice, but exists)

### Byte-Compiled Files

**Without PYTHONDONTWRITEBYTECODE**:
- Python creates `__pycache__/` directories
- `.pyc` files stored on disk
- Adds 20-30% to image size
- Minimal performance benefit in containers (rebuilt on startup anyway)

**With PYTHONDONTWRITEBYTECODE=1**:
- No `__pycache__/` directories
- Cleaner image
- Python compiles to memory on import (negligible performance impact)

### Non-Root User (Security Best Practice)

```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Install dependencies as root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER appuser
WORKDIR /home/appuser/app

# Copy app as non-root user
COPY --chown=appuser:appuser . .

CMD ["python", "app.py"]
```

**Why**: Containers running as root pose security risk if compromised

### Python Dockerfile Template

```dockerfile
FROM python:3.11-slim as builder

# Set build-time env vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Runtime env vars
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/root/.local/bin:$PATH

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy installed packages
COPY --from=builder /root/.local /home/appuser/.local

# Switch to non-root user
USER appuser
WORKDIR /home/appuser/app

# Copy application
COPY --chown=appuser:appuser . .

# Update PATH for non-root user
ENV PATH=/home/appuser/.local/bin:$PATH

CMD ["python", "app.py"]
```

---

## 10. Health Checks

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

## 11. Common Patterns

### Pattern 1: Flask/FastAPI Web App

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

## 12. Benchmarks

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

---

## Anti-Patterns to Avoid

### 1. Using `python:latest`

```dockerfile
# BAD: Non-reproducible, breaks when Python 4.0 releases
FROM python:latest

# GOOD: Pin to specific version
FROM python:3.11-slim

# BETTER: Pin to patch version
FROM python:3.11.8-slim
```

**Why**: `latest` changes over time, breaks builds unpredictably

---

### 2. Installing Dependencies in Final Stage

```dockerfile
# BAD: 1.2GB final image (includes gcc, make, headers)
FROM python:3.11-slim
RUN apt-get update && apt-get install -y gcc
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# GOOD: 300MB final image (build tools excluded)
FROM python:3.11-slim as builder
RUN apt-get update && apt-get install -y gcc
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY . .
```

---

### 3. Not Using .dockerignore

```dockerfile
# Without .dockerignore:
# COPY . . copies 500MB (.git, venv, __pycache__, logs, etc.)

# With .dockerignore:
# COPY . . copies 50MB (only application code)
```

**Impact**: 10x larger build context, slower uploads, larger images

---

### 4. Running as Root

```dockerfile
# BAD: Security risk
FROM python:3.11-slim
COPY . .
CMD ["python", "app.py"]  # Runs as root (UID 0)

# GOOD: Non-root user
FROM python:3.11-slim
RUN useradd -m -u 1000 appuser
USER appuser
COPY --chown=appuser:appuser . .
CMD ["python", "app.py"]  # Runs as appuser (UID 1000)
```

**Why**: Compromised container running as root = full host access (in some configurations)

---

### 5. Putting Secrets in Image Layers

```dockerfile
# BAD: Secret leaked in layer history
FROM python:3.11-slim
COPY .env .  # Contains DATABASE_PASSWORD=secret123
RUN export $(cat .env) && python setup.py
RUN rm .env  # Too late! Secret is in previous layer

# GOOD: Secrets via runtime environment
FROM python:3.11-slim
COPY . .
CMD ["python", "app.py"]

# Pass secrets at runtime:
# docker run -e DATABASE_PASSWORD=secret123 myapp
```

**Why**: Deleted files still exist in earlier layers, anyone with image can extract them

---

### 6. Breaking Cache with Unnecessary Changes

```dockerfile
# BAD: Rebuilds dependencies on every build
FROM python:3.11-slim
COPY . .  # Includes code, requirements.txt, everything
RUN pip install -r requirements.txt  # Cache broken by code changes

# GOOD: Only copy requirements.txt
FROM python:3.11-slim
COPY requirements.txt .  # Only copy what's needed
RUN pip install -r requirements.txt  # Cache survives code changes
COPY . .  # Copy code last
```

---

### 7. Not Cleaning Package Manager Cache

```dockerfile
# BAD: 100MB of apt cache in image
RUN apt-get update
RUN apt-get install -y gcc
RUN rm -rf /var/lib/apt/lists/*  # Separate layer, cache still in earlier layers

# GOOD: Single RUN command
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*  # Same layer, actually removes cache
```

---

## M32RIMM-Specific Notes

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
    -v /home/rmurphy/.m32rimm/$SUB1:/home/appuser/.m32rimm/$SUB1 \
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

---

## Quick Reference Card

### Dockerfile Checklist

```dockerfile
# ✅ Multi-stage build
FROM python:3.11-slim as builder
# ... build stage ...

FROM python:3.11-slim
# ✅ Python env vars
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

# ✅ Copy only dependencies first (cache-friendly)
COPY --from=builder /root/.local /root/.local

# ✅ Non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# ✅ Copy app last
COPY --chown=appuser:appuser . .

# ✅ Health check
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1

# ✅ Explicit CMD
CMD ["python", "app.py"]
```

### Build Commands

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build with tag
docker build -t myapp:latest .

# Build specific stage (debugging)
docker build --target builder -t myapp:debug .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t myapp:latest .

# Scan for vulnerabilities
trivy image --severity HIGH,CRITICAL myapp:latest
```

### Common Patterns Quick Reference

| Use Case | Pattern | Size |
|----------|---------|------|
| Web API | Multi-stage slim | ~300MB |
| Data processing | Multi-stage slim + volumes | ~350MB |
| Production secure | Distroless | ~250MB |
| Size-critical | Alpine (test thoroughly!) | ~150MB |

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

**Last Updated**: 2025-10-17
**Version**: 1.0
**Maintainer**: Claude Code (general-builder agent)
