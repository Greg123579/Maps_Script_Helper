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
kubectl apply -f k8s-resources/namespace.yaml

echo.
echo Step 3: Creating persistent volumes...
kubectl apply -f k8s-resources/pvc.yaml

echo.
echo Step 4: Creating secrets...
echo NOTE: Make sure you've created the secret with your API keys!
echo If not, run:
echo   kubectl create secret generic maps-data-analysis-ai-api-keys --from-literal=GOOGLE_API_KEY=your-key --from-literal=OPENAI_API_KEY=your-key -n maps-data-analysis
echo.
pause

echo.
echo Step 5: Creating RBAC (ServiceAccount, Role, RoleBinding)...
kubectl apply -f k8s-resources/rbac.yaml

echo.
echo Step 6: Deploying backend...
kubectl apply -f k8s-resources/backend-deployment.yaml
kubectl apply -f k8s-resources/backend-service.yaml

echo.
echo ========================================
echo Deployment complete!
echo ========================================
echo.
echo Checking pod status...
kubectl get pods -n maps-data-analysis

echo.
echo To access the application:
echo   1. Wait for pod to be Running: kubectl get pods -n maps-data-analysis -w
echo   2. Port-forward: kubectl port-forward svc/maps-backend 8000:8000 -n maps-data-analysis
echo   3. Open browser: http://localhost:8000
echo.
echo To view logs:
echo   kubectl logs -f deployment/maps-backend -n maps-data-analysis
echo.
