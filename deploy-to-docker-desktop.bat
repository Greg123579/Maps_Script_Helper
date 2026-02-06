@echo off
REM Deploy to Docker Desktop Kubernetes
echo ========================================
echo Deploying Maps Python Helper to Docker Desktop K8s
echo ========================================

echo.
echo Step 0: Deleting existing deployment...
REM Kill any existing port-forward processes first
taskkill /F /IM kubectl.exe >nul 2>&1
timeout /t 1 /nobreak >nul
kubectl delete deployment maps-backend -n maps-data-analysis --ignore-not-found=true
if %errorlevel% equ 0 (
    echo Existing deployment deleted
) else (
    echo No existing deployment found ^(this is OK^)
)
echo Waiting 2 seconds for cleanup...
timeout /t 2 /nobreak >nul

echo.
echo Step 1: Prune Docker build cache?
choice /C YN /M "Prune Docker build cache (recommended if builds fail)"
if %errorlevel% equ 1 (
    echo Pruning Docker build cache...
    docker builder prune -f
    echo Done.
) else (
    echo Skipping cache prune.
)

echo.
echo Step 2: Building Docker images...
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
echo Step 3: Creating namespace...
kubectl apply -f k8s-resources/namespace.yaml

echo.
echo Step 4: Checking secrets...
kubectl get secret maps-data-analysis-ai-api-keys -n maps-data-analysis >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Secret 'maps-data-analysis-ai-api-keys' not found!
    echo.
    echo To create the secret, run:
    echo   kubectl create secret generic maps-data-analysis-ai-api-keys --from-literal=GOOGLE_API_KEY=your-key --from-literal=OPENAI_API_KEY=your-key -n maps-data-analysis
    echo.
    echo Press any key to continue anyway ^(secret is optional^)...
    pause >nul
) else (
    echo Secret 'maps-data-analysis-ai-api-keys' exists - OK
)

echo.
echo Step 5: Creating RBAC ^(ServiceAccount, Role, RoleBinding^)...
kubectl apply -f k8s-resources/rbac.yaml

echo.
echo Step 6: Deploying backend...
kubectl apply -f k8s-resources/backend-deployment.yaml
if %errorlevel% neq 0 (
    echo ERROR: Failed to apply backend deployment
    exit /b 1
)
kubectl apply -f k8s-resources/backend-service.yaml
if %errorlevel% neq 0 (
    echo ERROR: Failed to apply backend service
    exit /b 1
)

echo.
echo Waiting for pod to be ready ^(this may take 20-30 seconds^)...
echo Checking pod status every 3 seconds...
:wait_loop
timeout /t 3 /nobreak >nul
kubectl get pods -n maps-data-analysis -l app=maps-backend -o jsonpath="{.items[0].status.phase}" >nul 2>&1
if %errorlevel% neq 0 (
    echo Waiting for pod to be created...
    goto wait_loop
)
kubectl get pods -n maps-data-analysis -l app=maps-backend -o jsonpath="{.items[0].status.containerStatuses[0].ready}" | findstr "true" >nul
if %errorlevel% neq 0 (
    echo Pod is starting... ^(still initializing^)
    goto wait_loop
)
echo.
echo ========================================
echo Deployment complete! Pod is ready.
echo ========================================
echo.
echo Pod status:
kubectl get pods -n maps-data-analysis -l app=maps-backend
echo.
echo Deployment status:
kubectl get deployment maps-backend -n maps-data-analysis

echo.
echo Step 7: Starting port-forward...
echo Starting port-forward on localhost:8000 -^> pod:8080...
start /B kubectl port-forward svc/maps-backend 8000:8000 -n maps-data-analysis
timeout /t 2 /nobreak >nul
echo.
echo ========================================
echo All done! App is available at: http://localhost:8000
echo ========================================
echo.
echo To view logs:
echo   kubectl logs -f deployment/maps-backend -n maps-data-analysis
echo.
echo NOTE: Port-forward is running in the background.
echo       Closing this window will stop the port-forward.
echo       Press any key to stop port-forward and exit.
echo ========================================
pause >nul
taskkill /F /IM kubectl.exe >nul 2>&1