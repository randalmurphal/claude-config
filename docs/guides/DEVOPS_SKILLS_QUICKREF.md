# DevOps Skills - Quick Reference Tables

**Research Date**: October 17, 2025

---

## Skill Priority Matrix

| Rank | Skill | Setup Time | Weekly Savings | Payback | Difficulty | ROI |
|------|-------|------------|----------------|---------|------------|-----|
| 1 | Parallel Testing (pytest-xdist) | 1 hour | 5 hours | 1 day | Easy | ⭐⭐⭐⭐⭐ |
| 2 | Pre-commit Hooks (ruff + GitLeaks) | 1 hour | 2 hours | < 1 week | Easy | ⭐⭐⭐⭐⭐ |
| 3 | CI/CD Caching | 2 hours | 3 hours | < 1 week | Easy | ⭐⭐⭐⭐⭐ |
| 4 | Coverage Automation | 2 hours | 1 hour | 2 weeks | Easy | ⭐⭐⭐⭐ |
| 5 | Docker Multi-stage | 4 hours | 2 hours | 2 weeks | Medium | ⭐⭐⭐⭐ |
| 6 | Structured Logging | 8 hours | 4 hours | 2 weeks | Medium | ⭐⭐⭐⭐ |
| 7 | Dependency Automation | 4 hours | 2 hours | 2 weeks | Easy | ⭐⭐⭐⭐ |
| 8 | Prometheus Metrics | 8 hours | 3 hours | 3 weeks | Medium | ⭐⭐⭐⭐ |
| 9 | Secrets Management | 8 hours | 1 hour | 8 weeks | Medium | ⭐⭐⭐ |
| 10 | Observability (OpenTelemetry) | 16 hours | 6 hours | 3 weeks | Hard | ⭐⭐⭐⭐ |
| 11 | Deployment Strategies | 16 hours | 4 hours | 4 weeks | Hard | ⭐⭐⭐ |
| 12 | IaC with Pulumi | 16 hours | 4 hours | 4 weeks | Hard | ⭐⭐⭐ |
| 13 | Continuous Profiling | 8 hours | 3 hours | 3 weeks | Medium | ⭐⭐⭐ |
| 14 | Chaos Engineering | 12 hours | 2 hours | 6 weeks | Hard | ⭐⭐ |
| 15 | Feature Flags | 8 hours | 2 hours | 4 weeks | Medium | ⭐⭐⭐ |

---

## Tool Comparison Tables

### Pre-commit Tools (2025)

| Tool | Purpose | Speed | Status |
|------|---------|-------|--------|
| **Ruff** | Linting + formatting | 10-100x faster than Black | ✅ Recommended |
| Black | Formatting only | Baseline | ⚠️ Being replaced |
| Flake8 | Linting only | Slow | ⚠️ Being replaced |
| isort | Import sorting | Moderate | ⚠️ Being replaced |
| **GitLeaks** | Secret detection | Fast | ✅ Essential |
| mypy | Type checking | Moderate | ✅ Keep alongside Ruff |

### CI/CD Platforms

| Platform | Caching | Matrix Builds | Artifacts | Python Support | Cost |
|----------|---------|---------------|-----------|----------------|------|
| **GitHub Actions** | ✅ Excellent | ✅ Native | ✅ Yes | ✅ First-class | Free tier + paid |
| GitLab CI | ✅ Good | ✅ Native | ✅ Yes | ✅ Good | Free tier + paid |
| CircleCI | ✅ Good | ✅ Via config | ✅ Yes | ✅ Good | Free tier + paid |
| Jenkins | ⚠️ Manual | ⚠️ Plugins | ✅ Yes | ✅ Good | Self-hosted |

### Docker Base Images

| Image | Size | Security | Use Case | Python Versions |
|-------|------|----------|----------|-----------------|
| python:3.13 | ~900 MB | Medium | Development | All |
| python:3.13-slim | ~150 MB | Good | **Production** | All |
| python:3.13-alpine | ~50 MB | Good | Size-critical | All (compile issues possible) |
| Distroless Python | ~50 MB | **Excellent** | High-security | Limited |

### Secrets Management

| Solution | Complexity | Cost | Best For | 2025 Status |
|----------|-----------|------|----------|-------------|
| .env + python-dotenv | Low | Free | Local dev, simple apps | ✅ Standard |
| HashiCorp Vault | High | Free (OSS) | Enterprise, centralized | ✅ Industry standard |
| Azure Key Vault | Medium | Pay-per-use | Azure-native apps | ✅ Managed service |
| AWS Secrets Manager | Medium | Pay-per-use | AWS-native apps | ✅ Managed service |
| GCP Secret Manager | Medium | Pay-per-use | GCP-native apps | ✅ Managed service |
| python-dotenv-vault | Low | Paid | Encrypted .env files | 🆕 Emerging |

### Observability Stacks

| Stack | Components | Complexity | Cost | Best For |
|-------|-----------|------------|------|----------|
| **ELK** | Elasticsearch, Logstash, Kibana | High | Self-hosted or paid | Log aggregation |
| **Prometheus + Grafana** | Prometheus, Grafana | Medium | Free (OSS) | Metrics & dashboards |
| **OpenTelemetry** | OTel + backends | Medium | Varies | Vendor-neutral |
| **Datadog** | All-in-one platform | Low | Expensive | Enterprise, full platform |
| **New Relic** | All-in-one platform | Low | Expensive | Enterprise, full platform |

### Deployment Strategies

| Strategy | Downtime | Cost | Rollback Speed | Complexity | Risk | Best For |
|----------|----------|------|---------------|------------|------|----------|
| **Blue-Green** | Zero | High (2x infra) | Instant | Low | Low | Critical apps, instant rollback needed |
| **Canary** | Zero | Medium | Fast | Medium | **Lowest** | Large-scale, gradual rollout |
| **Rolling** | Zero | Low | Moderate | Low | Medium | Kubernetes, frequent updates |
| Recreate | High | Low | Fast | Very low | High | Dev environments only |

### Database Migration Tools

| Tool | Language | Auto-generation | Rollback | Best For |
|------|---------|-----------------|----------|----------|
| **Alembic** | Python | ✅ Yes | ✅ Yes | SQLAlchemy projects |
| Flyway | SQL | ❌ No | ✅ Yes | Java, multi-language |
| Liquibase | XML/SQL | ❌ No | ✅ Yes | Enterprise Java |
| Django Migrations | Python | ✅ Yes | ✅ Yes | Django projects |

### Logging Libraries

| Library | Structured | JSON Output | Performance | Async | Learning Curve |
|---------|-----------|-------------|-------------|-------|----------------|
| **structlog** | ✅ Native | ✅ Yes | Fast (Rust core) | ✅ Yes | Medium |
| **Loguru** | ✅ Yes | ✅ serialize=True | Fast | ✅ Yes | Low |
| Standard logging | ⚠️ Manual | ⚠️ Custom formatter | Moderate | ✅ QueueHandler | Low |

### Environment Managers

| Tool | Dependencies | Virtualenv | Packaging | Lock File | 2025 Status |
|------|-------------|-----------|-----------|-----------|-------------|
| venv | ❌ | ✅ | ❌ | ❌ | Basic projects |
| pip | ✅ | ❌ | ❌ | ❌ | Still widely used |
| Pipenv | ✅ | ✅ | ❌ | ✅ Pipfile.lock | ⚠️ Declining |
| **Poetry** | ✅ | ✅ | ✅ | ✅ poetry.lock | ✅ **Recommended** |
| Conda | ✅ | ✅ | ✅ | ❌ (solve on install) | ✅ Data science |

### Dependency Update Tools

| Tool | Platforms | Package Managers | Auto-merge | Grouping | Scheduling | 2025 Status |
|------|-----------|------------------|-----------|----------|------------|-------------|
| **Renovate** | Multi-platform | 90+ | ✅ Yes | ✅ Advanced | ✅ Yes | ✅ Most flexible |
| **Dependabot** | GitHub, Azure | 15+ | ✅ Yes | ✅ Basic | ✅ Yes | ✅ Built-in GitHub |
| PyUp | GitHub | Python only | ✅ Yes | ❌ No | ✅ Yes | ⚠️ Python-specific |

### Profiling Tools

| Tool | Type | Overhead | Production-Safe | Language Support | 2025 Status |
|------|------|----------|----------------|------------------|-------------|
| **py-spy** | Sampling | <1% | ✅ Yes | Python only | ✅ Recommended |
| **Pyroscope** | Continuous | <2% | ✅ Yes | Multi-language | ✅ Grafana-backed |
| **Scalene** | CPU + Memory | Higher | ⚠️ Dev only | Python only | ✅ Development |
| cProfile | Deterministic | High | ❌ No | Python only | ✅ Standard library |
| line_profiler | Line-level | Very high | ❌ No | Python only | ✅ Detailed analysis |

### Infrastructure as Code

| Tool | Language | State Management | Multi-cloud | Testing | 2025 Trend |
|------|---------|------------------|------------|---------|------------|
| Terraform | HCL | State files | ✅ Yes | Limited | ➡️ Stable |
| **Pulumi** | Python, TS, Go, C# | State files | ✅ Yes | ✅ Native | ⬆️ Rising |
| CloudFormation | JSON/YAML | AWS-managed | ❌ AWS only | Limited | ➡️ Stable |
| Ansible | YAML | Agentless | ✅ Yes | Playbooks | ➡️ Stable |

### SAST/Security Scanning

| Tool | Languages | Speed | False Positives | IDE Integration | Cost |
|------|-----------|-------|----------------|----------------|------|
| **Bandit** | Python | Fast | Low | ✅ Yes | Free |
| **Semgrep** | Multi-language | Fast | Low | ✅ Yes | Free + paid |
| **SonarQube** | Multi-language | Moderate | Medium | ✅ Yes | Free + paid |
| Snyk Code | Multi-language | Fast | Low | ✅ Yes | Paid |
| Checkmarx | Multi-language | Slow | Medium | ✅ Yes | Enterprise |

---

## Implementation Checklists

### Pre-commit Hooks Setup
```
☐ Install pre-commit: pip install pre-commit
☐ Create .pre-commit-config.yaml
☐ Add ruff for linting/formatting
☐ Add GitLeaks for secret detection
☐ Add mypy for type checking
☐ Add custom validators (project-specific)
☐ Install hooks: pre-commit install
☐ Test: pre-commit run --all-files
☐ Document in README
```

### CI/CD Optimization
```
☐ Add dependency caching (actions/cache@v3)
☐ Configure matrix builds (oldest + newest Python)
☐ Enable parallel test execution (pytest -n auto)
☐ Add coverage reporting (pytest-cov)
☐ Set up PR coverage comments (pytest-coverage-comment)
☐ Add badges to README
☐ Set coverage thresholds (fail below X%)
☐ Optimize Docker layer caching
☐ Review workflow run times (identify bottlenecks)
```

### Docker Optimization
```
☐ Convert to multi-stage build
☐ Order layers: dependencies first, code last
☐ Use python:3.13-slim base image
☐ Add .dockerignore file
☐ Run as non-root user
☐ Set health check endpoint
☐ Optimize for layer caching
☐ Remove unnecessary files
☐ Measure image size reduction
```

### Structured Logging
```
☐ Choose library (structlog recommended)
☐ Configure JSON output
☐ Add context processors (request_id, user_id, etc.)
☐ Replace print() statements
☐ Migrate from standard logging
☐ Add key fields (timestamp, level, logger, message)
☐ Set up log aggregation (ELK/Loki)
☐ Create dashboards
☐ Set up alerts
```

### Observability Setup
```
☐ Install OpenTelemetry SDK
☐ Configure instrumentation
☐ Set up Prometheus exporter
☐ Deploy Prometheus
☐ Configure scrape targets
☐ Set up Grafana
☐ Create dashboards (metrics, traces, logs)
☐ Configure alerting rules
☐ Test end-to-end pipeline
```

---

## Command Quick Reference

### Pre-commit
```bash
# Install
pip install pre-commit

# Set up hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate

# Skip hooks temporarily
SKIP=ruff git commit -m "message"
```

### pytest-xdist (Parallel Testing)
```bash
# Auto-detect CPUs
pytest -n auto

# Specific worker count
pytest -n 4

# Worksteal distribution (recommended)
pytest -n auto --dist worksteal

# With coverage
pytest -n auto --cov=src --cov-report=term-missing
```

### Docker Multi-stage
```dockerfile
# Stage 1: Builder
FROM python:3.13-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels
COPY . /app
WORKDIR /app
CMD ["python", "app.py"]
```

### Alembic
```bash
# Initialize
alembic init alembic

# Create migration (auto)
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one revision
alembic downgrade -1

# Show current revision
alembic current
```

### Poetry
```bash
# Create project
poetry new myproject

# Add to existing
poetry init

# Install dependencies
poetry install

# Add package
poetry add requests

# Add dev dependency
poetry add --group dev pytest

# Update dependencies
poetry update

# Show dependency tree
poetry show --tree
```

### Prometheus (Custom Metrics)
```python
from prometheus_client import start_http_server, Counter, Histogram

# Define metrics
requests = Counter('http_requests_total', 'Total HTTP requests')
latency = Histogram('http_request_duration_seconds', 'Request latency')

# Use in code
@latency.time()
def handle_request():
    requests.inc()
    # Your code

# Start metrics server
start_http_server(8000)
```

### Pulumi
```bash
# Create new project
pulumi new python

# Preview changes
pulumi preview

# Deploy infrastructure
pulumi up

# Destroy infrastructure
pulumi destroy

# Export stack output
pulumi stack output bucket_name
```

---

## M32RIMM-Specific Patterns

### Subscription Isolation Validator
```python
# Pre-commit hook: check_subscription_queries.py
def validate_mongo_queries(file_content):
    if 'businessObjects' in file_content:
        if 'info.owner.subID' not in file_content:
            raise Error("Missing subscription isolation in query")
```

### Import Tool Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Define import-specific metrics
dvs_processed = Counter('tenable_dvs_processed_total',
                       'Total DVs processed',
                       ['scan_id', 'sub_id'])

import_duration = Histogram('tenable_import_duration_seconds',
                           'Import execution time',
                           ['scan_id'])

cache_hit_rate = Gauge('tenable_cache_hit_percentage',
                      'Cache effectiveness percentage')

mongo_ops = Counter('tenable_mongo_operations_total',
                   'MongoDB operations',
                   ['operation', 'collection'])
```

### Health Checks
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health/live')
def liveness():
    return jsonify({"status": "alive"}), 200

@app.route('/health/ready')
def readiness():
    checks = {
        'mongodb': check_mongo(),
        'redis': check_redis(),
        'tenable_api': check_tenable(),
        'cache_db': check_sqlite()
    }

    if all(checks.values()):
        return jsonify({"status": "ready", "checks": checks}), 200
    return jsonify({"status": "not ready", "checks": checks}), 503
```

### Configuration Validation
```python
from pydantic import BaseModel, Field

class TenableSCConfig(BaseModel):
    subscription_id: str = Field(..., regex=r'^[0-9a-f]{24}$')
    api_url: str
    username: str
    password: str
    cache_size_mb: int = Field(200, ge=100, le=1000)
    max_workers: int = Field(5, ge=1, le=20)
    batch_size: int = Field(5000, ge=100, le=10000)

    class Config:
        env_file = '.env'

# Fail fast at startup
try:
    config = TenableSCConfig()
except ValidationError as e:
    print(f"Configuration error: {e}")
    sys.exit(1)
```

---

## Performance Benchmarks

### CI/CD Optimization Impact

| Optimization | Before | After | Improvement |
|--------------|--------|-------|-------------|
| Dependency caching | 8 min | 45 sec | **89% faster** |
| Parallel testing | 6 min | 2 min | **67% faster** |
| Matrix reduction | 15 min | 6 min | **60% faster** |
| Docker layer caching | 12 min | 90 sec | **88% faster** |

### Docker Image Sizes

| Approach | Size | Reduction |
|----------|------|-----------|
| Standard python:3.13 | 900 MB | Baseline |
| python:3.13-slim | 150 MB | **83%** |
| Multi-stage slim | 120 MB | **87%** |
| Distroless | 50 MB | **94%** |

### Test Execution Times (M32RIMM scale)

| Test Suite | Sequential | Parallel (4 cores) | Speedup |
|-----------|-----------|-------------------|---------|
| Unit tests (500 tests) | 6 min | 2 min | **3x** |
| Integration (50 tests) | 15 min | 5 min | **3x** |
| Full suite | 21 min | 7 min | **3x** |

---

## Cost-Benefit Analysis

### GitHub Actions (Medium Project)

| Without Optimization | Monthly Cost |
|---------------------|--------------|
| 20 PRs/day, 15 min each | ~$200 |

| With Optimization | Monthly Cost | Savings |
|------------------|--------------|---------|
| 20 PRs/day, 5 min each | ~$70 | **$130/month** |

### Developer Time Savings (Annual)

| Optimization | Weekly Savings | Annual Savings |
|--------------|----------------|----------------|
| Pre-commit hooks | 2 hours | 104 hours |
| Parallel testing | 5 hours | 260 hours |
| CI/CD caching | 3 hours | 156 hours |
| Automated coverage | 1 hour | 52 hours |
| Docker optimization | 2 hours | 104 hours |
| Structured logging | 4 hours | 208 hours |
| **Total** | **17 hours** | **884 hours** |

**Value at $100/hour**: $88,400/year in developer time saved

### Incident Reduction

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Security vulnerabilities | 100/year | 60/year | **40% reduction** |
| Deployment failures | 20/year | 5/year | **75% reduction** |
| Production incidents | 50/year | 20/year | **60% reduction** |
| MTTR (Mean Time to Recovery) | 2 hours | 30 min | **75% faster** |

---

## Quick Decision Trees

### "Should I use Poetry or venv?"

```
New project? → Poetry
Existing venv project? → Stay with venv (or migrate if time permits)
Team collaboration? → Poetry (lock files)
Simple script? → venv
Package publishing? → Poetry
```

### "Which deployment strategy?"

```
Zero downtime required? → Blue-Green or Canary
2x infrastructure cost acceptable? → Blue-Green
Gradual user testing needed? → Canary
Kubernetes environment? → Rolling Updates
Dev/staging environment? → Recreate (simple)
```

### "Which secrets management?"

```
Local dev only? → .env + python-dotenv
Enterprise scale? → HashiCorp Vault
AWS-native? → AWS Secrets Manager
Azure-native? → Azure Key Vault
Simple encryption? → python-dotenv-vault
```

### "Which observability stack?"

```
Vendor-neutral? → OpenTelemetry + Prometheus + Grafana
Existing Grafana? → Prometheus + Loki + Tempo
All-in-one platform? → Datadog or New Relic
Log aggregation focus? → ELK Stack
Budget-conscious? → Prometheus + Grafana (OSS)
```

---

## Common Pitfalls & Solutions

| Pitfall | Solution |
|---------|----------|
| **Pre-commit hooks too slow** | Run only on changed files, use fast tools (Ruff) |
| **CI/CD cache invalidation** | Use correct cache key (hash of requirements.txt) |
| **Docker images too large** | Multi-stage builds, slim base image, .dockerignore |
| **Parallel tests failing** | Check for shared state, use isolated fixtures |
| **Secrets in version control** | GitLeaks pre-commit hook, .gitignore .env files |
| **Log aggregation performance** | Use structured JSON, sampling for high-volume |
| **Prometheus high cardinality** | Limit label values, use histograms not gauges |
| **Migration downtime** | Blue-green deployment, backward-compatible schemas |
| **Dependency conflicts** | Use lock files (poetry.lock), version pinning |
| **Production profiling overhead** | Use py-spy (<1% overhead), avoid cProfile |

---

## 2025 Tool Trends Summary

### Rising
- **Ruff** (replacing Black/Flake8/isort)
- **Poetry** (replacing Pipenv)
- **OpenTelemetry** (vendor-neutral observability)
- **Pulumi** (Python IaC over Terraform)
- **Pyroscope** (continuous profiling)
- **Renovate** (advanced dependency updates)

### Stable
- **GitHub Actions** (CI/CD leader)
- **Prometheus + Grafana** (metrics/dashboards)
- **Docker** (containerization)
- **Alembic** (Python DB migrations)
- **pytest** (testing framework)

### Declining
- **Black** (Ruff replacement)
- **Flake8** (Ruff replacement)
- **Pipenv** (Poetry replacement)
- **Jenkins** (GitHub Actions/GitLab CI)

### Emerging
- **AI-powered observability** (anomaly detection)
- **Distroless containers** (security)
- **Chaos engineering** (resilience testing)
- **Feature flags** (progressive delivery)

---

## Related Documentation

- **Full Guide**: `DEVOPS_SKILLS_GUIDE.md` (1,679 lines, comprehensive)
- **Executive Summary**: `DEVOPS_SKILLS_SUMMARY.md` (552 lines, prioritization)
- **This Document**: Quick reference tables and checklists

---

**Last Updated**: October 17, 2025
