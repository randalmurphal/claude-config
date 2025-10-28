# GitLab CI/CD Pipeline Reference

**Comprehensive examples and advanced patterns for GitLab CI/CD pipelines.**

**See [SKILL.md](./SKILL.md) for quick reference and core patterns.**

---

## Complete Pipeline Templates

### Python API with Full Testing

```yaml
stages:
  - test
  - build
  - security
  - deploy

variables:
  DOCKER_BUILDKIT: "1"
  DOCKER_DRIVER: overlay2
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.pip-cache"
  POSTGRES_DB: test_db
  POSTGRES_USER: test_user
  POSTGRES_PASSWORD: test_pass

cache:
  key:
    files:
      - requirements.txt
  paths:
    - .pip-cache/

# Unit tests with coverage
test:unit:
  stage: test
  image: python:3.11-slim
  parallel: 4
  script:
    - pip install --cache-dir .pip-cache -r requirements.txt
    - pip install pytest pytest-cov pytest-split
    - pytest tests/unit/
      --splits 4
      --group $CI_NODE_INDEX
      --cov=src
      --cov-report=term
      --cov-report=xml
      --cov-fail-under=95
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - htmlcov/
    expire_in: 7 days

# Integration tests with real services
test:integration:
  stage: test
  image: python:3.11-slim
  services:
    - postgres:14
    - redis:7-alpine
  variables:
    DATABASE_URL: "postgresql://test_user:test_pass@postgres:5432/test_db"
    REDIS_URL: "redis://redis:6379/0"
  before_script:
    - pip install --cache-dir .pip-cache -r requirements.txt
    - pip install pytest
  script:
    - pytest tests/integration/ -v
  artifacts:
    when: on_failure
    paths:
      - test-logs/
    expire_in: 3 days

# E2E tests against running API
test:e2e:
  stage: test
  image: python:3.11-slim
  services:
    - postgres:14
    - redis:7-alpine
  before_script:
    - pip install -r requirements.txt
    - pip install pytest requests
    - python app.py &
    - sleep 5  # Wait for app to start
  script:
    - pytest tests/e2e/ -v
  artifacts:
    when: on_failure
    paths:
      - screenshots/
    expire_in: 3 days

# Linting with multiple tools
lint:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install ruff pyright
  script:
    - ruff format --check .
    - ruff check . --config=.ruff.toml
    - pyright --project pyproject.toml
  allow_failure: false

# Type checking
type-check:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install --cache-dir .pip-cache -r requirements.txt
    - pip install pyright
  script:
    - pyright --project pyproject.toml
  allow_failure: false

# Build Docker image with BuildKit
build:
  stage: build
  image: docker:24-cli
  services:
    - docker:24-dind
  variables:
    DOCKER_BUILDKIT: "1"
    BUILDKIT_INLINE_CACHE: "1"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    # Pull previous image for cache
    - docker pull $CI_REGISTRY_IMAGE:latest || true

    # Build with cache
    - docker build
      --cache-from $CI_REGISTRY_IMAGE:latest
      --build-arg BUILDKIT_INLINE_CACHE=1
      --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
      --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG
      --tag $CI_REGISTRY_IMAGE:latest
      .

    # Push all tags
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG
    - docker push $CI_REGISTRY_IMAGE:latest
  only:
    - branches
    - tags

# Security scanning with Trivy
security:trivy:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy image
      --exit-code 0
      --severity LOW,MEDIUM
      --no-progress
      $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

    - trivy image
      --exit-code 1
      --severity HIGH,CRITICAL
      --no-progress
      $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  dependencies:
    - build
  allow_failure: false

# SAST scanning
security:sast:
  stage: security
  image: python:3.11-slim
  before_script:
    - pip install bandit safety
  script:
    - bandit -r src/ -f json -o bandit-report.json
    - safety check --json
  artifacts:
    reports:
      sast: bandit-report.json
    when: always
    expire_in: 30 days
  allow_failure: true

# Deploy to development (automatic)
deploy:dev:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: development
    url: https://dev-api.example.com
    on_stop: stop:dev
  script:
    - kubectl config use-context dev-cluster
    - kubectl set image deployment/myapp myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - kubectl rollout status deployment/myapp --timeout=5m
    - kubectl get pods -l app=myapp
  only:
    - develop

# Stop dev environment
stop:dev:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: development
    action: stop
  script:
    - kubectl config use-context dev-cluster
    - kubectl scale deployment/myapp --replicas=0
  when: manual
  only:
    - develop

# Deploy to staging (manual)
deploy:staging:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: staging
    url: https://staging-api.example.com
  script:
    - kubectl config use-context staging-cluster
    - kubectl set image deployment/myapp myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - kubectl rollout status deployment/myapp --timeout=5m

    # Run smoke tests
    - curl -f https://staging-api.example.com/health || exit 1
    - curl -f https://staging-api.example.com/version || exit 1
  when: manual
  only:
    - develop
    - main

# Deploy to production with blue-green
deploy:production:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: production
    url: https://api.example.com
  script:
    # Determine which environment is active
    - ACTIVE=$(kubectl get svc myapp -o jsonpath='{.spec.selector.version}')
    - if [ "$ACTIVE" = "blue" ]; then TARGET="green"; else TARGET="blue"; fi
    - echo "Active: $ACTIVE, Deploying to: $TARGET"

    # Deploy to inactive environment
    - kubectl set image deployment/myapp-${TARGET} myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - kubectl rollout status deployment/myapp-${TARGET} --timeout=5m

    # Smoke test inactive environment
    - kubectl port-forward service/myapp-${TARGET} 8080:80 &
    - sleep 5
    - curl -f http://localhost:8080/health || exit 1
    - curl -f http://localhost:8080/version || exit 1

    # Switch traffic to new version
    - kubectl patch service myapp -p '{"spec":{"selector":{"version":"'${TARGET}'"}}}'

    # Verify production health
    - sleep 10
    - curl -f https://api.example.com/health || (kubectl patch service myapp -p '{"spec":{"selector":{"version":"'${ACTIVE}'"}}}'; exit 1)

    - echo "Deployment successful! Active environment: $TARGET"
  when: manual
  only:
    - main
  needs:
    - deploy:staging

# Rollback production
rollback:production:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: production
    url: https://api.example.com
  script:
    - ACTIVE=$(kubectl get svc myapp -o jsonpath='{.spec.selector.version}')
    - if [ "$ACTIVE" = "blue" ]; then TARGET="green"; else TARGET="blue"; fi
    - echo "Rolling back from $ACTIVE to $TARGET"
    - kubectl patch service myapp -p '{"spec":{"selector":{"version":"'${TARGET}'"}}}'
    - curl -f https://api.example.com/health || exit 1
    - echo "Rollback successful! Active environment: $TARGET"
  when: manual
  only:
    - main
```

---

### Node.js Frontend with S3 Deployment

```yaml
stages:
  - test
  - build
  - deploy

variables:
  NODE_ENV: production
  npm_config_cache: "$CI_PROJECT_DIR/.npm"

cache:
  key:
    files:
      - package-lock.json
  paths:
    - .npm/
    - node_modules/

# Unit tests with Jest
test:unit:
  stage: test
  image: node:18-alpine
  before_script:
    - npm ci --cache .npm
  script:
    - npm run test:coverage
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
      junit: junit.xml
    paths:
      - coverage/
    expire_in: 7 days

# Linting with ESLint and Prettier
lint:
  stage: test
  image: node:18-alpine
  before_script:
    - npm ci --cache .npm
  script:
    - npm run lint
    - npm run format:check
  allow_failure: false

# Type checking with TypeScript
type-check:
  stage: test
  image: node:18-alpine
  before_script:
    - npm ci --cache .npm
  script:
    - npm run type-check
  allow_failure: false

# Build production bundle
build:
  stage: build
  image: node:18-alpine
  before_script:
    - npm ci --cache .npm --prefer-offline
  script:
    - npm run build
    - ls -lah dist/
  artifacts:
    paths:
      - dist/
    expire_in: 1 week

# Deploy to S3 + CloudFront
deploy:production:
  stage: deploy
  image: python:3.11-slim
  dependencies:
    - build
  before_script:
    - pip install awscli
  script:
    # Upload to S3
    - aws s3 sync dist/ s3://$S3_BUCKET/ --delete --cache-control "max-age=31536000"

    # Update index.html separately (no cache)
    - aws s3 cp dist/index.html s3://$S3_BUCKET/index.html --cache-control "no-cache"

    # Invalidate CloudFront cache
    - aws cloudfront create-invalidation --distribution-id $CF_DIST_ID --paths "/*"

    # Verify deployment
    - curl -f https://example.com || exit 1
  environment:
    name: production
    url: https://example.com
  when: manual
  only:
    - main
```

---

### Go Microservice with Multi-Arch Builds

```yaml
stages:
  - test
  - build
  - deploy

# Run tests with race detector
test:
  stage: test
  image: golang:1.21-alpine
  script:
    - go test -v -race -coverprofile=coverage.out ./...
    - go tool cover -func=coverage.out
  coverage: '/total:.*\s+(\d+\.\d+)%/'
  artifacts:
    paths:
      - coverage.out
    expire_in: 7 days

# Linting with golangci-lint
lint:
  stage: test
  image: golangci/golangci-lint:latest
  script:
    - golangci-lint run -v
  allow_failure: false

# Build multi-arch Docker images
build:
  stage: build
  image: docker:24-cli
  services:
    - docker:24-dind
  variables:
    DOCKER_BUILDKIT: "1"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker buildx create --use
  script:
    - docker buildx build
      --platform linux/amd64,linux/arm64
      --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
      --tag $CI_REGISTRY_IMAGE:latest
      --push
      .
  only:
    - main

# Deploy to Kubernetes
deploy:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl set image deployment/myservice myservice=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - kubectl rollout status deployment/myservice
  when: manual
  only:
    - main
```

---

## Advanced Caching Patterns

### Docker Registry Cache

```yaml
build:
  stage: build
  image: docker:24-cli
  services:
    - docker:24-dind
  variables:
    DOCKER_BUILDKIT: "1"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    # Pull all possible cache sources
    - docker pull $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG || true
    - docker pull $CI_REGISTRY_IMAGE:main || true
    - docker pull $CI_REGISTRY_IMAGE:latest || true

    # Build with multiple cache sources
    - docker build
      --cache-from $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG
      --cache-from $CI_REGISTRY_IMAGE:main
      --cache-from $CI_REGISTRY_IMAGE:latest
      --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
      .

    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

### BuildKit Cache Mounts

```yaml
build:
  stage: build
  image: docker:24-cli
  services:
    - docker:24-dind
  variables:
    DOCKER_BUILDKIT: "1"
  script:
    - docker build
      --build-arg BUILDKIT_INLINE_CACHE=1
      --secret id=npm_token,env=NPM_TOKEN
      --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
      .
```

**Dockerfile with cache mounts:**
```dockerfile
# syntax=docker/dockerfile:1.4

FROM python:3.11-slim

# Use cache mount for pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Use secret mount for private packages
RUN --mount=type=secret,id=npm_token \
    NPM_TOKEN=$(cat /run/secrets/npm_token) \
    npm install private-package
```

---

## Complex Deployment Scenarios

### Canary with Automated Rollback

```yaml
deploy:canary:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: production-canary
    url: https://api.example.com
  script:
    # Deploy canary (10% traffic via Istio)
    - kubectl apply -f k8s/canary-deployment.yml
    - kubectl set image deployment/myapp-canary myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - kubectl rollout status deployment/myapp-canary

    # Monitor error rate for 5 minutes
    - |
      for i in {1..30}; do
        ERROR_RATE=$(curl -s http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[1m]) | jq '.data.result[0].value[1]' | tr -d '"')
        if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
          echo "Error rate too high: $ERROR_RATE"
          kubectl scale deployment/myapp-canary --replicas=0
          exit 1
        fi
        sleep 10
      done

    # Promote canary to stable
    - kubectl patch deployment myapp-stable --patch "$(cat k8s/canary-promotion.yml)"
    - kubectl scale deployment/myapp-canary --replicas=0
  when: manual
  only:
    - main
```

### Rolling Deployment with Health Checks

```yaml
deploy:rolling:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    # Configure rolling update strategy
    - kubectl patch deployment myapp -p '
      {
        "spec": {
          "strategy": {
            "type": "RollingUpdate",
            "rollingUpdate": {
              "maxSurge": 1,
              "maxUnavailable": 0
            }
          }
        }
      }'

    # Update image
    - kubectl set image deployment/myapp myapp=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

    # Wait for rollout
    - kubectl rollout status deployment/myapp --timeout=10m

    # Verify all pods are healthy
    - |
      READY=$(kubectl get deployment myapp -o jsonpath='{.status.readyReplicas}')
      DESIRED=$(kubectl get deployment myapp -o jsonpath='{.spec.replicas}')
      if [ "$READY" != "$DESIRED" ]; then
        echo "Only $READY/$DESIRED pods ready"
        kubectl rollout undo deployment/myapp
        exit 1
      fi

    # Run smoke tests
    - ./scripts/smoke-test.sh https://api.example.com
  only:
    - main
```

---

## Pipeline Performance Optimization

### Parallel Matrix Builds

```yaml
test:
  stage: test
  parallel:
    matrix:
      - PYTHON_VERSION: ["3.9", "3.10", "3.11"]
        DATABASE: ["postgres:13", "postgres:14", "postgres:15"]
  image: python:${PYTHON_VERSION}-slim
  services:
    - name: $DATABASE
      alias: postgres
  script:
    - pip install -r requirements.txt
    - pytest tests/ -v
```

### Conditional Job Execution

```yaml
# Only run expensive e2e tests on main branch
test:e2e:
  stage: test
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH =~ /^release\//
    - if: $CI_MERGE_REQUEST_LABELS =~ /run-e2e/
  script:
    - pytest tests/e2e/ -v

# Skip build for documentation-only changes
build:
  stage: build
  rules:
    - if: $CI_COMMIT_MESSAGE =~ /\[skip-build\]/
      when: never
    - changes:
      - "src/**/*"
      - "Dockerfile"
      - "requirements.txt"
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
```

### Dynamic Pipeline Generation

```yaml
# Generate child pipelines based on changes
generate:
  stage: .pre
  script:
    - |
      if git diff --name-only $CI_COMMIT_BEFORE_SHA $CI_COMMIT_SHA | grep -q '^frontend/'; then
        echo "frontend-pipeline.yml" > pipeline.txt
      fi
      if git diff --name-only $CI_COMMIT_BEFORE_SHA $CI_COMMIT_SHA | grep -q '^backend/'; then
        echo "backend-pipeline.yml" >> pipeline.txt
      fi
  artifacts:
    paths:
      - pipeline.txt

trigger:frontend:
  stage: build
  trigger:
    include:
      - artifact: pipeline.txt
        job: generate
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## HashiCorp Vault Integration

### Using Vault Secrets

```yaml
deploy:
  stage: deploy
  id_tokens:
    VAULT_ID_TOKEN:
      aud: https://vault.example.com
  secrets:
    DATABASE_PASSWORD:
      vault: production/database/password@secret
      file: false
    SSL_CERTIFICATE:
      vault: production/ssl/cert@secret
      file: true
    API_KEY:
      vault: production/api/key@secret
      file: false
  script:
    - echo "Using DB password: $DATABASE_PASSWORD"
    - cat $SSL_CERTIFICATE
    - curl -H "Authorization: Bearer $API_KEY" https://api.example.com
```

### Dynamic Secrets

```yaml
deploy:
  stage: deploy
  before_script:
    # Authenticate with Vault
    - export VAULT_TOKEN=$(vault write -field=token auth/jwt/login role=gitlab-ci jwt=$CI_JOB_JWT)

    # Get dynamic database credentials
    - export DB_USER=$(vault read -field=username database/creds/myapp)
    - export DB_PASSWORD=$(vault read -field=password database/creds/myapp)
  script:
    - psql -h $DB_HOST -U $DB_USER -p $DB_PASSWORD -c "SELECT version();"
```

---

## Monitoring and Notifications

### Slack Notifications

```yaml
notify:success:
  stage: .post
  image: alpine:latest
  before_script:
    - apk add --no-cache curl
  script:
    - |
      curl -X POST $SLACK_WEBHOOK_URL \
        -H 'Content-Type: application/json' \
        -d '{
          "text": "✅ Pipeline succeeded for '$CI_PROJECT_NAME'",
          "attachments": [{
            "color": "good",
            "fields": [
              {"title": "Branch", "value": "'$CI_COMMIT_REF_NAME'", "short": true},
              {"title": "Commit", "value": "'$CI_COMMIT_SHORT_SHA'", "short": true},
              {"title": "Author", "value": "'$GITLAB_USER_NAME'", "short": true},
              {"title": "Pipeline", "value": "<'$CI_PIPELINE_URL'|View>", "short": true}
            ]
          }]
        }'
  when: on_success
  only:
    - main

notify:failure:
  stage: .post
  image: alpine:latest
  before_script:
    - apk add --no-cache curl
  script:
    - |
      curl -X POST $SLACK_WEBHOOK_URL \
        -H 'Content-Type: application/json' \
        -d '{
          "text": "❌ Pipeline failed for '$CI_PROJECT_NAME'",
          "attachments": [{
            "color": "danger",
            "fields": [
              {"title": "Branch", "value": "'$CI_COMMIT_REF_NAME'", "short": true},
              {"title": "Commit", "value": "'$CI_COMMIT_SHORT_SHA'", "short": true},
              {"title": "Failed Job", "value": "'$CI_JOB_NAME'", "short": true},
              {"title": "Pipeline", "value": "<'$CI_PIPELINE_URL'|View>", "short": true}
            ]
          }]
        }'
  when: on_failure
  only:
    - main
```

### Prometheus Metrics

```yaml
deploy:
  stage: deploy
  after_script:
    # Record deployment metric
    - |
      echo "deployment_timestamp{environment=\"production\",version=\"$CI_COMMIT_SHA\"} $(date +%s)" | \
      curl --data-binary @- http://pushgateway:9091/metrics/job/deployments
```

---

## CI/CD Variables Best Practices

### Variable Hierarchy

**GitLab variable precedence (highest to lowest):**
1. Trigger variables
2. Scheduled pipeline variables
3. Manual pipeline run variables
4. Project variables
5. Group variables
6. Instance variables

### Protected Variables

```yaml
deploy:production:
  stage: deploy
  script:
    # $PROD_API_KEY only available on protected branches
    - curl -H "Authorization: Bearer $PROD_API_KEY" https://api.example.com/deploy
  only:
    variables:
      - $CI_COMMIT_REF_PROTECTED == "true"
```

### File Variables

```yaml
deploy:
  stage: deploy
  script:
    # SSL_CERT is a file variable
    - cp $SSL_CERT /etc/ssl/certs/app.crt
    - chmod 600 /etc/ssl/certs/app.crt

    # KUBECONFIG is a file variable
    - kubectl --kubeconfig=$KUBECONFIG get pods
```

---

## Cleanup Jobs

### Docker Layer Cleanup

```yaml
cleanup:docker:
  stage: .post
  image: docker:24-cli
  services:
    - docker:24-dind
  script:
    - docker system prune -af --volumes
    - docker builder prune -af
  when: always
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

### Artifact Cleanup

```yaml
cleanup:artifacts:
  stage: .post
  image: alpine:latest
  before_script:
    - apk add --no-cache curl jq
  script:
    # Delete artifacts older than 7 days
    - |
      CUTOFF=$(date -d '7 days ago' +%s)
      curl -H "PRIVATE-TOKEN: $CI_JOB_TOKEN" \
        "$CI_API_V4_URL/projects/$CI_PROJECT_ID/jobs?per_page=100" | \
      jq -r '.[] | select(.artifacts_file != null) | select(.created_at < "'$(date -d '7 days ago' --iso-8601)'") | .id' | \
      while read job_id; do
        curl -X DELETE -H "PRIVATE-TOKEN: $CI_JOB_TOKEN" \
          "$CI_API_V4_URL/projects/$CI_PROJECT_ID/jobs/$job_id/artifacts"
      done
  when: always
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

---

**Last Updated**: 2025-10-27
**Version**: 1.0
