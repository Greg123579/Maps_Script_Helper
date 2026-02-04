# Dual Runtime Support - Quick Reference

## For Docker Desktop (Local Development)

### Start the system
```bash
docker-compose up -d
```

**That's it!** The system automatically detects Docker runtime and uses it.

### View logs
```bash
docker-compose logs -f backend
docker logs runner-<job-id>  # For specific job
```

### Stop the system
```bash
docker-compose down
```

---

## For Kubernetes (Production)

### Prerequisites
```bash
# Build and push images
docker build -t your-registry/maps-python-backend:latest .
docker push your-registry/maps-python-backend:latest

docker build -t your-registry/py-exec:latest -f backend/runner_image/Dockerfile backend/runner_image/
docker push your-registry/py-exec:latest

# Update k8s/backend-deployment.yaml with your registry URLs
```

### Deploy
```bash
# Create all resources
kubectl apply -f k8s/

# Check status
kubectl get pods -n maps-python

# View logs
kubectl logs -f deployment/maps-backend -n maps-python
```

### Access
```bash
# Port forward (local access)
kubectl port-forward svc/maps-backend 8000:8000 -n maps-python

# Or get LoadBalancer IP
kubectl get svc maps-backend -n maps-python
```

### Cleanup
```bash
kubectl delete namespace maps-python
```

---

## Environment Variables

### Docker Desktop (docker-compose.yml)
```yaml
environment:
  - EXECUTION_RUNTIME=docker  # Optional: explicit
  - RUNNER_IMAGE=py-exec:latest
  - SCRIPT_TIMEOUT=600
```

### Kubernetes (k8s/backend-deployment.yaml)
```yaml
env:
- name: EXECUTION_RUNTIME
  value: "kubernetes"  # Optional: explicit
- name: KUBERNETES_NAMESPACE
  value: "maps-python"
- name: RUNNER_IMAGE
  value: "your-registry/py-exec:latest"
- name: SCRIPT_TIMEOUT
  value: "600"
```

---

## Check Current Runtime

```bash
# Via API
curl http://localhost:8000/api/system/runtime

# Response:
{
  "runtime": "docker",  # or "kubernetes"
  "config": {...},
  "runner_type": "DockerRunner"  # or "KubernetesRunner"
}
```

---

## Force Specific Runtime

### Force Docker
```bash
export EXECUTION_RUNTIME=docker
docker-compose restart
```

### Force Kubernetes
```bash
kubectl set env deployment/maps-backend EXECUTION_RUNTIME=kubernetes -n maps-python
```

### Auto-detect (Default)
Don't set `EXECUTION_RUNTIME` - system auto-detects based on environment.

---

## Typical Workflow

1. **Develop locally** with Docker Compose
   ```bash
   docker-compose up -d
   # Make changes, test immediately
   ```

2. **Test on local Kubernetes** (optional)
   ```bash
   minikube start
   kubectl apply -f k8s/
   ```

3. **Deploy to production**
   ```bash
   # Push images to registry
   docker push your-registry/...
   
   # Deploy to cluster
   kubectl apply -f k8s/
   ```

---

## Troubleshooting

### Script not executing?
- **Docker**: `docker ps -a | grep runner` - check for containers
- **Kubernetes**: `kubectl get pods -n maps-python` - check for runner pods

### Can't switch runtime?
- Check `EXECUTION_RUNTIME` env var
- Restart backend service
- Verify Docker/Kubernetes is accessible

### Image not found?
- **Docker**: `docker images | grep py-exec`
- **Kubernetes**: Check imagePullPolicy and registry access

---

## Performance Tips

- **Use Docker for development** - faster iteration (containers start in <1s)
- **Use Kubernetes for production** - better scaling and resource management
- **Same runner image** - build once, use in both environments
- **Monitor timeouts** - adjust `SCRIPT_TIMEOUT` based on workload

---

## Files Reference

- `backend/runtime_config.py` - Runtime detection logic
- `backend/docker_runner.py` - Docker execution
- `backend/k8s_runner.py` - Kubernetes execution
- `backend/unified_runner.py` - Unified interface
- `backend/integration_example.py` - Code examples
- `DUAL_RUNTIME.md` - Complete documentation
- `k8s/` - Kubernetes manifests
- `docker-compose.yml` - Docker Compose config
