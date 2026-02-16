# Kubernetes Migration Guide

This guide explains how to migrate from Docker Compose to Kubernetes deployment.

## Overview

The main architectural change is replacing **Docker-in-Docker** with **Kubernetes Pod API**:

- **Before**: Backend container spawns Docker containers via Docker socket
- **After**: Backend pod creates Kubernetes pods via Kubernetes API

## Files Created

### Kubernetes Manifests (`k8s/` directory)

1. **namespace.yaml** - Dedicated namespace for isolation
2. **persistent-volumes.yaml** - 5 PVCs for data persistence
3. **configmap.yaml** - Environment configuration
4. **secret.yaml** - API keys (GOOGLE_API_KEY, OPENAI_API_KEY)
5. **rbac.yaml** - ServiceAccount + Role + RoleBinding for pod creation
6. **backend-deployment.yaml** - Main backend deployment
7. **backend-service.yaml** - LoadBalancer service (port 8000)
8. **runner-pod-template.yaml** - Template for runner pods (reference only)
9. **README.md** - Detailed deployment instructions

### Backend Code

1. **backend/k8s_runner.py** - New Kubernetes runner module
   - Replaces Docker subprocess calls
   - Creates pods via Kubernetes API
   - Manages ConfigMaps for script storage
   - Handles pod lifecycle and log retrieval

## Required Backend Changes

### 1. Add Kubernetes Dependency

Add to `backend/requirements.txt`:
```
kubernetes>=28.1.0
```

### 2. Update app.py

Add runtime detection at the top of `backend/app.py`:

```python
import os

# Determine execution runtime
EXECUTION_RUNTIME = os.getenv("EXECUTION_RUNTIME", "docker")  # "docker" or "kubernetes"

if EXECUTION_RUNTIME == "kubernetes":
    from backend.k8s_runner import get_runner
    print("✓ Using Kubernetes runtime for script execution")
else:
    print("✓ Using Docker runtime for script execution")
```

### 3. Modify Script Execution Logic

Find the function that runs scripts (likely in the `/api/run` endpoint). Replace Docker calls:

**Before (Docker)**:
```python
docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{input_path}:/input:ro",
    "-v", f"{output_path}:/output",
    "py-exec:latest",
    "python", "-u", "job_runner.py"
]
result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
```

**After (Kubernetes)**:
```python
if EXECUTION_RUNTIME == "kubernetes":
    runner = get_runner()
    result = runner.run_script(
        job_id=job_id,
        script_content=script_code,
        request_json=request_json,
        input_path=input_path,
        output_path=output_path,
        timeout=600
    )
    success = result["status"] == "success"
    logs_output = result["logs"]
else:
    # Existing Docker code
    docker_cmd = [...]
    result = subprocess.run(...)
```

### 4. Add Health Check Endpoint

Add to `backend/app.py` if not already present:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes."""
    return {"status": "healthy", "version": API_VERSION}
```

## Deployment Process

### Step 1: Build and Push Images

```bash
# Backend image
docker build -t your-registry.io/maps-python-backend:latest .
docker push your-registry.io/maps-python-backend:latest

# Runner image
cd backend/runner_image
docker build -t your-registry.io/py-exec:latest .
docker push your-registry.io/py-exec:latest
```

### Step 2: Update Image References

Edit the following files to use your registry:
- `k8s/backend-deployment.yaml` - line with `image: maps-python-backend:latest`
- `backend/k8s_runner.py` - line with `runner_image: str = "py-exec:latest"`

### Step 3: Configure Secrets

```bash
# Option 1: Edit k8s/secret.yaml directly
# Option 2: Create via kubectl
kubectl create secret generic maps-api-keys \
  --from-literal=GOOGLE_API_KEY=your-google-key \
  --from-literal=OPENAI_API_KEY=your-openai-key \
  -n maps-python
```

### Step 4: Apply Manifests

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/persistent-volumes.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml  # If using file
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
```

### Step 5: Verify Deployment

```bash
# Check pods
kubectl get pods -n maps-python

# Check logs
kubectl logs -f deployment/maps-backend -n maps-python

# Get service URL
kubectl get svc maps-backend -n maps-python
```

### Step 6: Access Application

```bash
# Option 1: Port forward for local testing
kubectl port-forward svc/maps-backend 8000:8000 -n maps-python

# Option 2: Use LoadBalancer external IP (if available)
kubectl get svc maps-backend -n maps-python
# Access via http://<EXTERNAL-IP>:8000
```

## Key Differences

| Aspect | Docker Compose | Kubernetes |
|--------|----------------|------------|
| **Container Creation** | Docker CLI via socket | Kubernetes API |
| **Data Sharing** | Volume mounts | PersistentVolumeClaims |
| **Script Passing** | Volume mount | ConfigMap |
| **Networking** | Docker network | ClusterIP services |
| **Permissions** | Docker socket access | ServiceAccount RBAC |
| **Lifecycle** | docker-compose up/down | kubectl apply/delete |

## Storage Considerations

### PVC Access Modes

Current setup uses **ReadWriteOnce** (RWO):
- Works for single-node clusters
- Backend and runner pods must be on same node

For multi-node clusters:
- Use **ReadWriteMany** (RWX)
- Requires storage class that supports RWX (NFS, CephFS, etc.)
- Edit `k8s/persistent-volumes.yaml` to change access mode

### Storage Classes

Check available storage classes:
```bash
kubectl get storageclass
```

Specify in PVC if needed:
```yaml
spec:
  storageClassName: your-storage-class
```

## Troubleshooting

### Backend can't create pods

Check RBAC permissions:
```bash
kubectl auth can-i create pods \
  --as=system:serviceaccount:maps-python:maps-backend-sa \
  -n maps-python
```

View role bindings:
```bash
kubectl describe role maps-backend-role -n maps-python
kubectl describe rolebinding maps-backend-rolebinding -n maps-python
```

### PVC not binding

Check PVC status:
```bash
kubectl get pvc -n maps-python
kubectl describe pvc maps-outputs -n maps-python
```

Possible issues:
- No available storage class
- Insufficient cluster storage
- Access mode not supported

### Runner pods failing

View pod events:
```bash
kubectl get pods -n maps-python
kubectl describe pod runner-<job-id> -n maps-python
```

Check runner logs:
```bash
kubectl logs runner-<job-id> -n maps-python
```

### Images not pulling

Verify image exists:
```bash
docker pull your-registry.io/maps-python-backend:latest
```

Check imagePullSecrets if using private registry:
```yaml
spec:
  imagePullSecrets:
  - name: registry-credentials
```

## Rollback to Docker Compose

If needed, revert by:
1. Remove Kubernetes resources: `kubectl delete namespace maps-python`
2. Revert backend code changes
3. Start Docker Compose: `docker-compose up -d`

## Production Recommendations

1. **Use Ingress** instead of LoadBalancer for better routing
2. **Add resource limits** appropriate for your workload
3. **Implement pod disruption budgets** for availability
4. **Use external secret management** (Vault, AWS Secrets Manager)
5. **Add horizontal pod autoscaling** for backend if needed
6. **Implement backup strategy** for PVCs
7. **Use network policies** for security
8. **Add monitoring** (Prometheus, Grafana)
9. **Implement CI/CD pipeline** for image builds

## Next Steps

After successful deployment:
1. Test script execution functionality
2. Verify log collection works
3. Check file persistence across pod restarts
4. Load test with multiple concurrent jobs
5. Set up monitoring and alerts
