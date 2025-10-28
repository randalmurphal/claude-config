---
name: kubernetes-patterns
description: Kubernetes deployment patterns including Deployments, Services, Ingress, ConfigMaps, Secrets, resource management, health checks, and horizontal pod autoscaling. Covers kubectl commands, YAML manifests, and GitOps workflows. Use when deploying to Kubernetes, managing containers, setting up services, or troubleshooting pod issues.
allowed-tools: [Read, Bash, Grep]
---

# Kubernetes Patterns Skill

## Overview
This skill provides comprehensive patterns for Kubernetes deployments, including manifest examples, kubectl commands, resource management, and troubleshooting strategies.

## Kubernetes Fundamentals

### Core Resources

| Resource | Purpose | Scope | Typical Use |
|----------|---------|-------|-------------|
| Pod | Container runtime | Smallest unit | Runs containers |
| Deployment | Pod management | Namespace | Stateless apps |
| StatefulSet | Ordered pods | Namespace | Databases, ordered apps |
| DaemonSet | One pod per node | Namespace | Logging, monitoring |
| Service | Networking | Namespace | Load balancing |
| Ingress | HTTP routing | Namespace | External access |
| ConfigMap | Configuration | Namespace | App config |
| Secret | Sensitive data | Namespace | Credentials |
| Namespace | Isolation | Cluster | Environment separation |
| PersistentVolume | Storage | Cluster | Data persistence |

### Pod Lifecycle

```
Pending → Running → Succeeded/Failed
         ↓
      Terminating
```

**Pod States:**
- **Pending**: Waiting for scheduling or image pull
- **Running**: At least one container running
- **Succeeded**: All containers terminated successfully
- **Failed**: At least one container failed
- **Unknown**: Pod state cannot be determined

## kubectl Commands Reference

### Essential Commands

```bash
# Cluster info
kubectl cluster-info
kubectl get nodes
kubectl top nodes  # Resource usage

# Namespace management
kubectl get namespaces
kubectl create namespace dev
kubectl config set-context --current --namespace=dev

# Get resources
kubectl get pods
kubectl get pods -n kube-system
kubectl get pods --all-namespaces
kubectl get pods -o wide  # More details
kubectl get pods -o yaml  # Full YAML
kubectl get pods -w       # Watch mode

# Describe resources (detailed info)
kubectl describe pod <pod-name>
kubectl describe deployment <deployment-name>
kubectl describe service <service-name>

# Logs
kubectl logs <pod-name>
kubectl logs <pod-name> -c <container-name>  # Multi-container pod
kubectl logs -f <pod-name>  # Follow/tail
kubectl logs --previous <pod-name>  # Previous crashed container

# Execute commands in pods
kubectl exec -it <pod-name> -- /bin/bash
kubectl exec <pod-name> -- env
kubectl exec <pod-name> -c <container-name> -- ls /app

# Port forwarding
kubectl port-forward pod/<pod-name> 8080:80
kubectl port-forward service/<service-name> 8080:80

# Apply/Create/Delete
kubectl apply -f deployment.yaml
kubectl apply -f ./manifests/  # All files in directory
kubectl create -f pod.yaml
kubectl delete -f deployment.yaml
kubectl delete pod <pod-name>
kubectl delete deployment <deployment-name>

# Edit resources
kubectl edit deployment <deployment-name>
kubectl scale deployment <name> --replicas=3
kubectl set image deployment/<name> <container>=<image>:<tag>

# Rollout management
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name>
kubectl rollout restart deployment/<name>

# Debug commands
kubectl get events --sort-by='.lastTimestamp'
kubectl top pods  # Resource usage
kubectl debug <pod-name> -it --image=busybox
```

### Advanced kubectl

```bash
# Label selection
kubectl get pods -l app=nginx
kubectl get pods -l 'env in (prod,staging)'
kubectl get pods -l app=nginx,version=v1

# Field selection
kubectl get pods --field-selector status.phase=Running
kubectl get pods --field-selector metadata.namespace!=default

# JSON path queries
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
kubectl get pods -o jsonpath='{.items[*].status.podIP}'

# Custom columns
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase

# Dry run
kubectl apply -f deployment.yaml --dry-run=client -o yaml
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml

# Resource management
kubectl api-resources  # List all resource types
kubectl explain pod  # Documentation for resource type
kubectl explain pod.spec.containers
```

## Deployment Patterns

### Basic Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: production
  labels:
    app: web-app
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
        version: v1
    spec:
      containers:
      - name: app
        image: myapp:1.0.0
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: ENV
          value: production
        - name: LOG_LEVEL
          value: info
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Multi-Container Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-sidecar
spec:
  containers:
  # Main application
  - name: app
    image: myapp:1.0.0
    ports:
    - containerPort: 8080
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/app

  # Sidecar for log shipping
  - name: log-shipper
    image: fluent/fluent-bit:latest
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/app
      readOnly: true
    - name: fluent-config
      mountPath: /fluent-bit/etc/

  volumes:
  - name: shared-logs
    emptyDir: {}
  - name: fluent-config
    configMap:
      name: fluent-bit-config
```

### StatefulSet (for databases)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

## Service Patterns

### ClusterIP (Internal Service)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  type: ClusterIP  # Default, internal only
  selector:
    app: web-app
  ports:
  - name: http
    port: 80
    targetPort: 8080
    protocol: TCP
```

### NodePort (External Access)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app-external
spec:
  type: NodePort
  selector:
    app: web-app
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080  # Must be 30000-32767
```

### LoadBalancer (Cloud Provider)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app-lb
spec:
  type: LoadBalancer
  selector:
    app: web-app
  ports:
  - port: 80
    targetPort: 8080
```

### Headless Service (StatefulSets)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  clusterIP: None  # Headless
  selector:
    app: postgres
  ports:
  - port: 5432
```

## Ingress Patterns

### Basic Ingress (nginx)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app
            port:
              number: 80
```

### TLS/SSL Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress-tls
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - app.example.com
    secretName: app-tls-secret
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app
            port:
              number: 80
```

### Multi-Service Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-service
spec:
  ingressClassName: nginx
  rules:
  - host: example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

## ConfigMaps and Secrets

### ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  # Key-value pairs
  LOG_LEVEL: "info"
  DATABASE_URL: "postgres://db:5432/mydb"

  # File content
  app.conf: |
    server {
      listen 80;
      server_name localhost;
    }
```

**Using ConfigMap:**

```yaml
# As environment variables
env:
- name: LOG_LEVEL
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: LOG_LEVEL

# All keys as env vars
envFrom:
- configMapRef:
    name: app-config

# As volume mount
volumes:
- name: config
  configMap:
    name: app-config
volumeMounts:
- name: config
  mountPath: /etc/config
  readOnly: true
```

### Secret

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  # Base64 encoded values
  username: YWRtaW4=
  password: cGFzc3dvcmQxMjM=
stringData:
  # Plain text (will be encoded)
  api-key: "sk-1234567890"
```

**Creating secrets from command line:**

```bash
# From literal values
kubectl create secret generic db-secret \
  --from-literal=username=admin \
  --from-literal=password=secret123

# From file
kubectl create secret generic tls-secret \
  --from-file=tls.crt=./tls.crt \
  --from-file=tls.key=./tls.key

# Docker registry secret
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass \
  --docker-email=user@example.com
```

**Using Secrets:**

```yaml
# As environment variables
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: app-secret
      key: password

# As volume
volumes:
- name: secret
  secret:
    secretName: app-secret
volumeMounts:
- name: secret
  mountPath: /etc/secrets
  readOnly: true
```

## Resource Management

### Resource Requests and Limits

```yaml
resources:
  requests:
    cpu: 100m        # 0.1 CPU core
    memory: 128Mi    # 128 mebibytes
  limits:
    cpu: 500m        # 0.5 CPU core
    memory: 512Mi    # 512 mebibytes
```

**Units:**
- CPU: `m` = millicore (1000m = 1 core)
- Memory: `Ki`, `Mi`, `Gi`, `Ti` (binary) or `K`, `M`, `G`, `T` (decimal)

**Best Practices:**
- Always set requests (for scheduling)
- Set limits to prevent resource hogging
- Requests ≤ Limits
- Monitor actual usage to tune values

### ResourceQuota (Namespace Limits)

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: production
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "10"
    pods: "50"
```

### LimitRange (Default Limits)

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: production
spec:
  limits:
  - default:
      cpu: 500m
      memory: 512Mi
    defaultRequest:
      cpu: 100m
      memory: 128Mi
    max:
      cpu: 2
      memory: 2Gi
    min:
      cpu: 50m
      memory: 64Mi
    type: Container
```

## Health Checks

### Liveness Probe

**Checks if container is alive. Restarts if fails.**

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
    httpHeaders:
    - name: Custom-Header
      value: Awesome
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
  successThreshold: 1

# Alternative: TCP probe
livenessProbe:
  tcpSocket:
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 20

# Alternative: Command probe
livenessProbe:
  exec:
    command:
    - cat
    - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Readiness Probe

**Checks if container is ready to serve traffic. Removes from service if fails.**

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
  successThreshold: 1
```

### Startup Probe

**For slow-starting containers. Delays liveness/readiness checks.**

```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
```

**Probe Parameters:**
- `initialDelaySeconds`: Wait before first probe
- `periodSeconds`: How often to probe
- `timeoutSeconds`: Probe timeout
- `failureThreshold`: Consecutive failures to mark unhealthy
- `successThreshold`: Consecutive successes to mark healthy

## Horizontal Pod Autoscaling

### Basic HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Custom Metrics HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-custom-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

**kubectl HPA commands:**

```bash
kubectl autoscale deployment web-app --min=2 --max=10 --cpu-percent=70
kubectl get hpa
kubectl describe hpa web-app-hpa
```

## Persistent Volumes

### PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
```

**Access Modes:**
- `ReadWriteOnce` (RWO): Single node read-write
- `ReadOnlyMany` (ROX): Many nodes read-only
- `ReadWriteMany` (RWX): Many nodes read-write

**Using PVC in Pod:**

```yaml
volumes:
- name: data
  persistentVolumeClaim:
    claimName: app-data
volumeMounts:
- name: data
  mountPath: /data
```

## GitOps Workflow

### ArgoCD Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo
    targetRevision: HEAD
    path: k8s/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

### Kustomize

```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml
- ingress.yaml

namespace: production

commonLabels:
  app: web-app
  env: production

images:
- name: myapp
  newTag: 1.0.0

configMapGenerator:
- name: app-config
  literals:
  - ENV=production
  - LOG_LEVEL=info
```

**Apply with kubectl:**

```bash
kubectl apply -k ./k8s/production/
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl get pods
kubectl describe pod <pod-name>

# Common issues:
# - ImagePullBackOff: Wrong image name or no access
# - CrashLoopBackOff: Container keeps crashing
# - Pending: Insufficient resources or scheduling issues

# Check logs
kubectl logs <pod-name>
kubectl logs <pod-name> --previous

# Check events
kubectl get events --sort-by='.lastTimestamp'
```

### Service Not Accessible

```bash
# Check service
kubectl get svc
kubectl describe svc <service-name>

# Check endpoints (should have pod IPs)
kubectl get endpoints <service-name>

# Test from another pod
kubectl run test --rm -it --image=busybox -- wget -O- http://<service-name>

# Check if pods match service selector
kubectl get pods -l app=web-app
```

### Resource Issues

```bash
# Check node resources
kubectl top nodes
kubectl describe node <node-name>

# Check pod resources
kubectl top pods
kubectl describe pod <pod-name> | grep -A 5 "Limits:"

# Check resource quotas
kubectl get resourcequota
kubectl describe resourcequota
```

### Network Debugging

```bash
# Run debug pod
kubectl run debug --rm -it --image=nicolaka/netshoot -- bash

# Inside debug pod:
ping <service-name>
nslookup <service-name>
curl http://<service-name>
traceroute <pod-ip>

# Check DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup kubernetes.default
```

## Quick Reference

### Common Patterns by Use Case

**Stateless Web App:**
- Deployment (multiple replicas)
- ClusterIP Service (internal)
- Ingress (external access)
- ConfigMap (configuration)
- Secret (credentials)
- HPA (autoscaling)

**Database:**
- StatefulSet (ordered pods)
- Headless Service (DNS)
- PersistentVolumeClaim (storage)
- Secret (passwords)

**Background Job:**
- Job (one-time task)
- CronJob (scheduled task)
- ConfigMap (job config)

**Logging/Monitoring:**
- DaemonSet (one per node)
- Service (metrics collection)

### Resource Definition Template

```yaml
apiVersion: <group>/<version>
kind: <resource-type>
metadata:
  name: <name>
  namespace: <namespace>
  labels:
    app: <app-name>
    version: <version>
  annotations:
    description: <description>
spec:
  # Resource-specific configuration
```

### Common Label Conventions

```yaml
labels:
  app.kubernetes.io/name: myapp
  app.kubernetes.io/instance: myapp-prod
  app.kubernetes.io/version: "1.0.0"
  app.kubernetes.io/component: frontend
  app.kubernetes.io/part-of: web-platform
  app.kubernetes.io/managed-by: helm
```

### Best Practices Summary

1. **Always set resource requests/limits**
2. **Use namespaces for isolation**
3. **Implement health checks**
4. **Use ConfigMaps/Secrets for configuration**
5. **Label everything consistently**
6. **Use Deployments, not bare Pods**
7. **Enable RBAC and network policies**
8. **Monitor resource usage**
9. **Use GitOps for deployment**
10. **Test in staging before production**
