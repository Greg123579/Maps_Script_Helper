# Dual Runtime Support: Docker Desktop + Kubernetes

This system supports both Docker Desktop (local development) and Kubernetes (production) with automatic runtime detection.

## Quick Start

### Local Development (Docker Desktop)
```bash
# Start with docker-compose (default)
docker-compose up -d

# Access at http://localhost:8000
```

### Production (Kubernetes)
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/

# Access via service
kubectl port-forward svc/maps-backend 8000:8000 -n maps-python
```

## How It Works

The system **automatically detects** the runtime environment:

1. **Checks `EXECUTION_RUNTIME` env var** - explicit override
2. **Detects Kubernetes** - checks for `KUBERNETES_SERVICE_HOST`
3. **Defaults to Docker** - for local development

## Runtime Configuration

### Docker Desktop (Local)

**Environment Variables**:
```bash
EXECUTION_RUNTIME=docker       # Optional: force Docker runtime
RUNNER_IMAGE=py-exec:latest    # Container image for script execution
SCRIPT_TIMEOUT=600             # Max execution time in seconds
HOST_PROJECT_DIR=/path/to/project  # For Docker-in-Docker volume mounts
```

**docker-compose.yml** (no changes needed):
```yaml
services:
  backend:
    environment:
      - EXECUTION_RUNTIME=docker  # Optional: explicitly use Docker
```

### Kubernetes (Production)

**Environment Variables**:
```bash
EXECUTION_RUNTIME=kubernetes   # Optional: force Kubernetes runtime
KUBERNETES_NAMESPACE=maps-python  # Namespace for runner pods
RUNNER_IMAGE=py-exec:latest    # Container image for runner pods
SCRIPT_TIMEOUT=600             # Max execution time in seconds
```

**k8s/backend-deployment.yaml**:
```yaml
env:
- name: EXECUTION_RUNTIME
  value: "kubernetes"  # Optional: explicitly use Kubernetes
- name: KUBERNETES_NAMESPACE
  value: "maps-python"
```

## Architecture Comparison

| Feature | Docker Desktop | Kubernetes |
|---------|---------------|------------|
| **Script Execution** | Docker containers | Kubernetes Pods |
| **Data Sharing** | Volume mounts | PersistentVolumeClaims |
| **Script Transfer** | File mount | ConfigMap |
| **Auto-detection** | Default | Via `KUBERNETES_SERVICE_HOST` |
| **Cleanup** | Automatic (`--rm`) | Explicit (pod deletion) |
| **Networking** | Docker network | Cluster networking |
| **Best For** | Local dev, rapid prototyping | Production, multi-node |

## Development Workflow

### 1. Local Development
```bash
# Use docker-compose for rapid development
docker-compose up -d

# Code changes auto-reload (volume mounts)
# Test scripts immediately
# View logs: docker-compose logs -f
```

### 2. Test Kubernetes Locally
```bash
# Optional: Use Minikube or Kind for local K8s testing
minikube start

# Build and load images
docker build -t py-exec:latest -f backend/runner_image/Dockerfile backend/runner_image/
minikube image load py-exec:latest

# Deploy
kubectl apply -f k8s/

# Force Kubernetes runtime
kubectl set env deployment/maps-backend EXECUTION_RUNTIME=kubernetes -n maps-python
```

### 3. Deploy to Production
```bash
# Push images to registry
docker tag maps-python-backend:latest your-registry/maps-python-backend:latest
docker push your-registry/maps-python-backend:latest

docker tag py-exec:latest your-registry/py-exec:latest
docker push your-registry/py-exec:latest

# Update manifests with registry URLs
# Deploy to cluster
kubectl apply -f k8s/
```

## Backend Code Integration

The backend uses a **unified runner interface** that automatically selects the appropriate runtime:

```python
from backend.unified_runner import get_runner

# Get unified runner (auto-detects runtime)
runner = get_runner()

# Execute script (same API for both runtimes)
result = runner.run_script(
    job_id=job_id,
    script_path=script_path,      # For Docker
    script_content=script_content, # For Kubernetes
    request_path=request_path,     # For Docker
    request_json=request_json,     # For Kubernetes
    input_path=input_path,
    output_path=output_path,
    timeout=600
)

# Check result
if result["status"] == "success":
    print(result["logs"])
else:
    print(f"Error: {result['logs']}")
```

## Runtime Detection Logic

```python
from backend.runtime_config import detect_runtime, get_runtime_config

# Detect runtime
runtime = detect_runtime()  # Returns "docker" or "kubernetes"

# Get configuration
config = get_runtime_config()
# Returns dict with runtime-specific settings
```

## Switching Runtimes

### Force Docker (even in Kubernetes)
```bash
export EXECUTION_RUNTIME=docker
# Or in docker-compose.yml / K8s deployment
```

### Force Kubernetes (if available)
```bash
export EXECUTION_RUNTIME=kubernetes
# Requires Kubernetes cluster access
```

### Auto-detection (Recommended)
```bash
# Don't set EXECUTION_RUNTIME
# System automatically detects:
# - Docker Desktop → uses Docker runtime
# - Kubernetes cluster → uses Kubernetes runtime
```

## Troubleshooting

### Check Current Runtime
```bash
curl http://localhost:8000/api/system/info

# Response includes:
# {
#   "runtime": "docker" | "kubernetes",
#   "runner_type": "DockerRunner" | "KubernetesRunner"
# }
```

### Docker Runtime Issues
- Verify Docker is running: `docker ps`
- Check image exists: `docker images | grep py-exec`
- View container logs: `docker logs runner-<job-id>`

### Kubernetes Runtime Issues
- Check pod status: `kubectl get pods -n maps-python`
- View pod logs: `kubectl logs runner-<job-id> -n maps-python`
- Verify RBAC: `kubectl auth can-i create pods --as=system:serviceaccount:maps-python:maps-backend-sa -n maps-python`

### Runtime Not Switching
- Check `EXECUTION_RUNTIME` environment variable
- Restart backend: `docker-compose restart` or `kubectl rollout restart deployment/maps-backend -n maps-python`
- Verify auto-detection: Check for `KUBERNETES_SERVICE_HOST` in environment

## Performance Considerations

### Docker Desktop
- **Faster startup** - containers start in <1s
- **Lower overhead** - direct host access
- **Better for iteration** - immediate feedback
- **Resource limits** - Docker Desktop memory/CPU limits

### Kubernetes
- **Slower startup** - pods take 2-5s to start
- **Higher overhead** - container runtime + K8s API
- **Better for scale** - multi-node, resource management
- **Production features** - health checks, auto-restart, etc.

## Migration Path

### Phase 1: Local Development
- Use Docker Compose
- Rapid prototyping
- Feature development

### Phase 2: Integration Testing
- Deploy to dev Kubernetes cluster
- Test with Kubernetes runtime
- Verify PVC, ConfigMap behavior

### Phase 3: Production
- Deploy to production Kubernetes
- Configure monitoring, alerts
- Set up CI/CD pipeline

## Best Practices

1. **Use Docker for development** - faster iteration
2. **Test on Kubernetes before production** - catch runtime differences
3. **Don't hardcode runtime** - use auto-detection
4. **Use same runner image** - build once, deploy everywhere
5. **Monitor both runtimes** - collect metrics and logs
6. **Version your images** - tag with git commit or version number

## Next Steps

- Add health check endpoint showing runtime info
- Implement metrics collection (execution time, success rate)
- Add runtime-specific optimizations
- Create CI/CD pipeline for both environments
- Set up monitoring dashboards (Grafana, etc.)
