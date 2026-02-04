"""
Example integration of unified runner in backend/app.py

Add this code to your script execution endpoint to support both Docker and Kubernetes.
"""

# At the top of backend/app.py, add:
from backend.unified_runner import get_runner as get_unified_runner
from backend.runtime_config import detect_runtime, get_runtime_config

# Add a new endpoint to check runtime info:
@app.get("/api/system/runtime")
async def get_runtime_info():
    """Get current runtime configuration."""
    try:
        runner = get_unified_runner()
        return runner.get_runtime_info()
    except Exception as e:
        return {
            "error": str(e),
            "runtime": detect_runtime(),
            "config": get_runtime_config()
        }


# In your script execution endpoint (e.g., /api/run or /api/execute):
@app.post("/api/run")
async def run_script(
    script_id: str = Form(...),
    # ... other parameters
):
    """Execute a user script using unified runner."""
    
    try:
        # Your existing setup code...
        job_id = str(uuid.uuid4())
        
        # Prepare paths
        script_path = f"/app/scripts/{script_id}.py"
        request_path = f"/app/outputs/{job_id}/request.json"
        input_path = f"/app/library/images"
        output_path = f"/app/outputs/{job_id}"
        
        # Create directories
        os.makedirs(output_path, exist_ok=True)
        
        # Save script and request
        with open(script_path, 'w') as f:
            f.write(script_code)
        
        with open(request_path, 'w') as f:
            json.dump(request_data, f)
        
        # Get unified runner (auto-detects Docker or Kubernetes)
        runner = get_unified_runner()
        
        # Execute script - same API for both runtimes!
        result = runner.run_script(
            job_id=job_id,
            script_path=script_path,      # Used by Docker
            script_content=script_code,   # Used by Kubernetes
            request_path=request_path,    # Used by Docker
            request_json=json.dumps(request_data),  # Used by Kubernetes
            input_path=input_path,
            output_path=output_path,
            timeout=600  # Optional: override default timeout
        )
        
        # Process result (same structure for both runtimes)
        if result["status"] == "success":
            print(f"✓ Script executed successfully (exit code: {result['exit_code']})")
            print(f"Logs:\n{result['logs']}")
            
            # Return success response
            return {
                "status": "success",
                "job_id": job_id,
                "output_path": output_path,
                "logs": result["logs"]
            }
        else:
            print(f"✗ Script failed (exit code: {result['exit_code']})")
            print(f"Error logs:\n{result['logs']}")
            
            # Return error response
            return {
                "status": "error",
                "job_id": job_id,
                "error": result["logs"],
                "exit_code": result["exit_code"]
            }
            
    except Exception as e:
        print(f"✗ Execution error: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


# MIGRATION FROM EXISTING DOCKER CODE:
# 
# OLD CODE (Docker only):
# docker_cmd = [
#     "docker", "run", "--rm",
#     "-v", f"{script_path}:/code/script.py:ro",
#     "-v", f"{request_path}:/code/request.json:ro",
#     "-v", f"{input_path}:/input:ro",
#     "-v", f"{output_path}:/output",
#     "py-exec:latest"
# ]
# result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
# 
# NEW CODE (Docker + Kubernetes):
# runner = get_unified_runner()
# result = runner.run_script(
#     job_id=job_id,
#     script_path=script_path,
#     script_content=script_code,
#     request_path=request_path,
#     request_json=json.dumps(request_data),
#     input_path=input_path,
#     output_path=output_path,
#     timeout=600
# )
