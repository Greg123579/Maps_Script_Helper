@echo off
REM Deploy to Docker Desktop Kubernetes
echo ========================================
echo Deploying Maps Python Helper to Docker Desktop K8s
echo ========================================

echo.
echo Step 1: Building Docker images...
docker build -t maps-python-backend:latest -f Dockerfile .
if %errorlevel% neq 0 (
    echo ERROR: Backend image build failed
    exit /b 1
)

docker build -t py-exec:latest -f backend/runner_image/Dockerfile backend/runner_image/
if %errorlevel% neq 0 (
    echo ERROR: Runner image build failed
    exit /b 1
)

echo.
echo Step 2: Creating namespace...
kubectl apply -f k8s/namespace.yaml

echo.
echo Step 3: Creating persistent volumes...
kubectl apply -f k8s/persistent-volumes.yaml

echo.
echo Step 4: Creating secrets and config...
echo NOTE: You may need to edit k8s/secret.yaml with your API keys first!
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml

echo.
echo Step 5: Creating RBAC (ServiceAccount, Role, RoleBinding)...
kubectl apply -f k8s/rbac.yaml

echo.
echo Step 6: Deploying backend...
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml

echo.
echo ========================================
echo Deployment complete!
echo ========================================
echo.
echo Checking pod status...
kubectl get pods -n maps-python

echo.
echo To access the application:
echo   1. Wait for pod to be Running: kubectl get pods -n maps-python -w
echo   2. Port-forward: kubectl port-forward svc/maps-backend 8000:8000 -n maps-python
echo   3. Open browser: http://localhost:8000
echo.
echo To view logs:
echo   kubectl logs -f deployment/maps-backend -n maps-python
echo.
