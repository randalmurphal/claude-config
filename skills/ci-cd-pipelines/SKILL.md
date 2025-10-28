---
name: ci-cd-pipelines
description: GitLab CI/CD pipeline patterns including testing stages, Docker builds, caching strategies, secrets management, deployment patterns (blue-green, canary, rolling), and rollback procedures. Use when creating .gitlab-ci.yml, optimizing CI performance, setting up deployment pipelines, or troubleshooting CI failures.
allowed-tools:
  - Read
  - Bash
  - Grep
---

# GitLab CI/CD Pipeline Patterns

**Purpose:** Build reliable, fast CI/CD pipelines for automated testing, Docker builds, and deployment.

**When to use:** Creating pipeline configs, optimizing CI performance, setting up deployments, debugging pipeline failures.

**Integrates with:** docker-optimization (image builds), testing-standards (test execution), gitlab-scripts (pipeline automation)

**For detailed examples and complete templates:** See [reference.md](./reference.md)

---

## Quick Reference

| Pattern | Use Case | Typical Impact |
|---------|----------|----------------|
| Parallel testing | Speed up test execution | 15min → 4min |
| Dependency caching | Faster builds | 10min → 2min |
| Docker layer caching | Faster image builds | 8min → 90s |
| Blue-green deploy | Zero-downtime production | <30s rollback |
| Canary deploy | Gradual rollout with monitoring | Risk reduction |

**Typical results:** 20min builds → 5min (with caching), safe deployments, rollback in <30s

---

## 1. GitLab CI Fundamentals

### Pipeline Structure

**Core concepts:**
- **Stages**: Sequential phases (test → build → deploy)
- **Jobs**: Tasks that run in parallel within stages
- **Runners**: Execution environments (shared, group, project)
- **Artifacts**: Files passed between stages

### Minimal .gitlab-ci.yml

```yaml
stages: [test, build, deploy]

test:
  stage: test
  image: python:3.11-slim
  script:
    - pip install -r requirements.txt
    - pytest tests/ --cov=src
  coverage: '/TOTAL.*\s+(\d+%)$/'

build:
  stage: build
  image: docker:24-cli
  services: [docker:24-dind]
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  script:
    - kubectl set image deployment/myapp myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  when: manual
```

---

## 2. Job Control with Rules

**Use `rules` instead of `only/except` (recommended since GitLab 12.3)**

```yaml
# Run on main branch only
deploy:
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# Run on merge requests
test-mr:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

# Complex conditions
deploy-staging:
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"
    - if: $CI_COMMIT_BRANCH =~ /^feature\//
      when: manual

# Skip for specific conditions
test:
  rules:
    - if: $CI_COMMIT_MESSAGE =~ /\[skip-tests\]/
      when: never
    - when: always
```

### Dependency Control

```yaml
# Don't wait for full stage
deploy:
  needs: ["build", "test"]

# Run even if previous stages failed
cleanup:
  when: always

# Manual approval gate
deploy-prod:
  when: manual
  allow_failure: false
```

---

## 3. Testing in CI

**See testing-standards skill for test organization patterns**

### Parallel Test Execution

```yaml
# Split tests across 4 runners
test:unit:
  parallel: 4
  script:
    - pytest tests/unit/ --splits 4 --group $CI_NODE_INDEX
  coverage: '/TOTAL.*\s+(\d+%)$/'

# Different layers in parallel
test:unit:
  script: pytest tests/unit/ -v

test:integration:
  services: [postgres:14, redis:7]
  script: pytest tests/integration/ -v
```

### Coverage Requirements

```yaml
test:
  script:
    - pytest tests/ --cov=src --cov-fail-under=95
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

**Coverage regex patterns:**
- Python: `'/TOTAL.*\s+(\d+%)$/'`
- JavaScript: `'/All files[^|]*\|[^|]*\s+([\d\.]+)/'`
- Go: `'/total:.*\s+(\d+\.\d+)%/'`

---

## 4. Docker Builds in CI

**See docker-optimization skill for Dockerfile patterns**

### Basic Docker Build

```yaml
build:
  image: docker:24-cli
  services: [docker:24-dind]
  variables:
    DOCKER_BUILDKIT: "1"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

### BuildKit with Cache

```yaml
build:optimized:
  variables:
    BUILDKIT_INLINE_CACHE: "1"
  script:
    - docker pull $CI_REGISTRY_IMAGE:latest || true
    - docker build
      --cache-from $CI_REGISTRY_IMAGE:latest
      -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

### Security Scanning

```yaml
security:scan:
  image: aquasec/trivy:latest
  script:
    - trivy image --exit-code 1 --severity CRITICAL,HIGH $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  allow_failure: false
```

---

## 5. Caching Strategies

**Critical for fast builds:** Good caching = 20min → 5min builds

### Cache vs Artifacts

| Feature | Cache | Artifacts |
|---------|-------|-----------|
| **Purpose** | Speed up builds | Pass data between stages |
| **Lifetime** | Persistent across pipelines | One pipeline only |
| **Reliability** | Best effort (may miss) | Guaranteed |

### Dependency Caching

```yaml
# Python
test:
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths: [.pip-cache/]
  before_script:
    - pip install --cache-dir .pip-cache -r requirements.txt

# Node.js
build:
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths: [node_modules/]
  before_script:
    - npm ci
```

### Smart Cache Keys

```yaml
# Per-requirements file (invalidate when deps change)
cache:
  key:
    files: [requirements.txt]
  paths: [.pip-cache/]

# Fallback caching
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths: [node_modules/]
  fallback_keys: [main]
```

---

## 6. Secrets Management

### CI/CD Variables

**Set in:** Settings → CI/CD → Variables

**Types:**
- **Variable**: Available in all jobs
- **File**: Written to temp file, path in `$VARIABLE_FILE`
- **Protected**: Only on protected branches
- **Masked**: Hidden in logs

```yaml
deploy:
  script:
    - echo $DATABASE_PASSWORD       # Use secret directly
    - cat $SSL_CERT_FILE            # Use secret from file
```

### Best Practices

```yaml
# BAD - hardcoded
deploy:
  script: psql -h db.example.com -U admin -p MyP@ssw0rd

# GOOD - use variables
deploy:
  script: psql -h $DB_HOST -U $DB_USER -p $DB_PASSWORD
```

---

## 7. Deployment Patterns

**See reference.md for complete examples**

### Blue-Green Deployment

**Zero-downtime deploys:** Switch traffic between two identical environments.

```yaml
deploy:blue-green:
  script:
    - ACTIVE=$(kubectl get svc myapp -o jsonpath='{.spec.selector.version}')
    - TARGET=$([ "$ACTIVE" = "blue" ] && echo "green" || echo "blue")
    - kubectl set image deployment/myapp-${TARGET} myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - kubectl rollout status deployment/myapp-${TARGET}
    - ./scripts/smoke-test.sh myapp-${TARGET}
    - kubectl patch svc myapp -p '{"spec":{"selector":{"version":"'${TARGET}'"}}}'
  when: manual
```

### Canary Deployment

**Gradual rollout:** Route small percentage of traffic to new version.

```yaml
deploy:canary:
  script:
    - kubectl apply -f k8s/canary-deployment.yml
    - kubectl set image deployment/myapp-canary myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - ./scripts/monitor-canary.sh 300  # Monitor 5 minutes
    - kubectl scale deployment/myapp-canary --replicas=10
  when: manual
```

### Rolling Deployment

```yaml
deploy:rolling:
  script:
    - kubectl set image deployment/myapp myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - kubectl rollout status deployment/myapp --timeout=5m
    - ./scripts/health-check.sh
```

---

## 8. Rollback Procedures

### Automatic Rollback

```yaml
deploy:with-rollback:
  script:
    - kubectl set image deployment/myapp myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - kubectl rollout status deployment/myapp --timeout=5m
    - if ! ./scripts/health-check.sh; then
        kubectl rollout undo deployment/myapp; exit 1;
      fi

# Manual rollback
rollback:
  script:
    - kubectl rollout undo deployment/myapp
    - kubectl rollout status deployment/myapp
  when: manual
```

### Rollback to Specific Version

```yaml
rollback:to-version:
  script:
    - kubectl rollout history deployment/myapp
    - kubectl rollout undo deployment/myapp --to-revision=${ROLLBACK_REVISION}
  when: manual
```

---

## 9. Performance Optimization

### Fast Pipeline Checklist

- [ ] Use parallel jobs for independent tasks
- [ ] Cache dependencies (pip, npm, docker layers)
- [ ] Use slim Docker images for CI jobs
- [ ] Skip unnecessary jobs with `rules`
- [ ] Use `needs` to start jobs early
- [ ] Split large test suites with `parallel`

### Example Optimization

```yaml
# Start deploy without waiting for all tests
deploy:staging:
  needs: ["build"]  # Don't wait for slow e2e tests

# Skip redundant jobs
lint:
  rules:
    - if: $CI_COMMIT_MESSAGE =~ /\[skip-lint\]/
      when: never
    - changes: ["**/*.py", "**/*.js"]

# Cancel old pipelines
test:
  interruptible: true
```

**Performance impact:**
- Before: test (10m) → build (8m) → deploy (2m) = 20 minutes
- After: test (10m parallel → 2.5m) + build (3m cached) + deploy (2m needs:build) = ~8 minutes

---

## 10. Multi-Environment Pipeline

```yaml
stages: [test, build, deploy-dev, deploy-staging, deploy-production]

deploy:dev:
  environment: {name: development, url: https://dev.example.com}
  script:
    - kubectl config use-context dev
    - kubectl set image deployment/myapp myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only: [develop]

deploy:staging:
  environment: {name: staging, url: https://staging.example.com}
  script:
    - kubectl config use-context staging
    - kubectl set image deployment/myapp myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  when: manual
  only: [develop]

deploy:production:
  environment: {name: production, url: https://example.com}
  script:
    - kubectl config use-context production
    - kubectl set image deployment/myapp myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  when: manual
  only: [main]
  needs: ["deploy:staging"]
```

---

## 11. Troubleshooting Guide

### Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Tests pass locally, fail in CI | Environment differences | Check versions, dependencies |
| Slow builds | No caching | Add dependency/layer caching |
| Docker build fails | Layer cache issues | Use `--no-cache` flag once |
| Random test failures | Flaky tests | Fix isolation, mock time/random |
| Out of disk space | Docker layer buildup | Add cleanup job |

### Debug Job

```yaml
debug:
  script:
    - echo "Runner: $CI_RUNNER_ID, Branch: $CI_COMMIT_BRANCH"
    - env | sort; df -h; docker system df
```

---

## 12. Integration with Other Skills

**docker-optimization:** Multi-stage Dockerfiles (70%+ reduction), BuildKit, Trivy scanning
**testing-standards:** Unit/integration/e2e stages, 95%+ coverage, parallel execution
**gitlab-scripts:** Trigger pipelines via `~/.claude/scripts/gitlab-trigger-pipeline`

---

## Best Practices

**DO:** Use `rules` (not `only/except`), cache aggressively, run jobs in parallel, use slim images, fail fast (lint→unit→integration), add health checks, use manual gates for production

**DON'T:** Hardcode secrets, skip tests, use `latest` tags in production, ignore failed jobs, deploy without rollback plan

---

## Quick Command Reference

```bash
# Validate pipeline locally
gitlab-runner exec docker test

# Trigger pipeline via script (see gitlab-scripts skill)
~/.claude/scripts/gitlab-trigger-pipeline main

# Check pipeline status
curl -H "PRIVATE-TOKEN: $TOKEN" \
  "$GITLAB_API/projects/$PROJECT_ID/pipelines?ref=main" | jq '.[0].status'
```

---

**For comprehensive examples and complete pipeline templates:** See [reference.md](./reference.md)

---

**Last Updated**: 2025-10-27
**Version**: 1.0
