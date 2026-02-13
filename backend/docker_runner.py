"""
Docker runner module for executing user scripts in Docker containers.
Used for local development with Docker Desktop.
"""

import os
import subprocess
import json
import time
from typing import Dict, Any, Optional


class DockerRunner:
    """Manages script execution using Docker containers."""
    
    def __init__(self, runner_image: str = "py-exec:latest", timeout: int = 600):
        """Initialize Docker runner."""
        self.runner_image = runner_image
        self.default_timeout = timeout
        
        # Verify Docker is available
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Docker is not available")
            print("✓ Docker runtime initialized")
        except Exception as e:
            raise RuntimeError(f"Docker is not available: {e}")
    
    def run_script(
        self,
        job_id: str,
        script_path: str,
        request_path: str,
        input_path: str,
        output_path: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a script in a Docker container.
        
        Args:
            job_id: Unique job identifier
            script_path: Path to script file on host
            request_path: Path to request JSON on host
            input_path: Path to input directory on host
            output_path: Path to output directory on host
            timeout: Execution timeout in seconds
        
        Returns:
            Dict with status, exit_code, stdout, stderr
        """
        timeout = timeout or self.default_timeout
        
        # Get host paths for volume mounting (for Docker-in-Docker)
        host_project_dir = os.getenv("HOST_PROJECT_DIR", "")
        
        # Build volume mount paths
        if host_project_dir and os.path.exists("/app"):
            # Running in Docker container - use host paths
            script_host = script_path.replace("/app", host_project_dir)
            request_host = request_path.replace("/app", host_project_dir)
            input_host = input_path.replace("/app", host_project_dir)
            output_host = output_path.replace("/app", host_project_dir)
            
            # Convert Windows paths to forward slashes for Docker
            script_host = script_host.replace("\\", "/")
            request_host = request_host.replace("\\", "/")
            input_host = input_host.replace("\\", "/")
            output_host = output_host.replace("\\", "/")
        else:
            # Running directly on host
            script_host = script_path
            request_host = request_path
            input_host = input_path
            output_host = output_path
        
        # Build Docker command
        # Note: job_runner.py expects the script at /code/main.py (not /code/script.py)
        docker_cmd = [
            "docker", "run",
            "--rm",
            "--name", f"runner-{job_id}",
            "-v", f"{script_host}:/code/main.py:ro",
            "-v", f"{request_host}:/code/request.json:ro",
            "-v", f"{input_host}:/input:ro",
            "-v", f"{output_host}:/output",
            "-e", f"JOB_ID={job_id}",
            self.runner_image
        ]
        
        print(f"Executing Docker command: {' '.join(docker_cmd)}")
        
        try:
            # Run the container
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "logs": result.stdout + result.stderr
            }
            
        except subprocess.TimeoutExpired:
            # Try to stop the container
            try:
                subprocess.run(
                    ["docker", "stop", f"runner-{job_id}"],
                    timeout=10,
                    capture_output=True
                )
            except:
                pass
            
            return {
                "status": "timeout",
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Script execution timed out after {timeout} seconds",
                "logs": f"Script execution timed out after {timeout} seconds"
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Docker execution error: {str(e)}",
                "logs": f"Docker execution error: {str(e)}"
            }
    
    def cleanup(self, job_id: str):
        """Clean up any remaining containers."""
        try:
            subprocess.run(
                ["docker", "rm", "-f", f"runner-{job_id}"],
                capture_output=True,
                timeout=10
            )
        except:
            pass


# Singleton instance
_runner: Optional[DockerRunner] = None


def get_runner() -> DockerRunner:
    """Get or create the Docker runner instance."""
    global _runner
    if _runner is None:
        runner_image = os.getenv("RUNNER_IMAGE", "py-exec:latest")
        timeout = int(os.getenv("SCRIPT_TIMEOUT", "600"))
        _runner = DockerRunner(runner_image, timeout)
    return _runner
