"""
Unified runner interface that automatically selects Docker or Kubernetes.
Provides a consistent API for script execution regardless of runtime environment.
"""

import os
from typing import Dict, Any, Optional
from backend.runtime_config import detect_runtime, get_runtime_config


class UnifiedRunner:
    """
    Unified interface for script execution.
    Automatically selects Docker or Kubernetes based on environment.
    """
    
    def __init__(self):
        """Initialize the appropriate runner based on detected runtime."""
        self.runtime = detect_runtime()
        self.config = get_runtime_config()
        
        if self.runtime == "kubernetes":
            from backend.k8s_runner import get_runner
            self._runner = get_runner()
            print(f"✓ Using Kubernetes runtime (namespace: {self.config['namespace']})")
        else:
            from backend.docker_runner import get_runner
            self._runner = get_runner()
            print(f"✓ Using Docker runtime (image: {self.config['runner_image']})")
    
    def run_script(
        self,
        job_id: str,
        script_path: str = None,
        script_content: str = None,
        request_path: str = None,
        request_json: str = None,
        input_path: str = None,
        output_path: str = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a script using the appropriate runtime.
        
        Args:
            job_id: Unique job identifier
            script_path: Path to script file (Docker) - optional if script_content provided
            script_content: Script code as string (Kubernetes) - optional if script_path provided
            request_path: Path to request JSON file (Docker) - optional if request_json provided
            request_json: Request JSON as string (Kubernetes) - optional if request_path provided
            input_path: Path to input directory
            output_path: Path to output directory
            timeout: Execution timeout in seconds (optional)
        
        Returns:
            Dict with:
            - status: "success", "failed", or "timeout"
            - exit_code: int
            - logs: str (combined stdout/stderr)
            - stdout: str (Docker only)
            - stderr: str (Docker only)
        """
        if self.runtime == "kubernetes":
            # Kubernetes requires script content and request JSON
            if not script_content and script_path:
                with open(script_path, 'r') as f:
                    script_content = f.read()
            
            if not request_json and request_path:
                with open(request_path, 'r') as f:
                    request_json = f.read()
            
            return self._runner.run_script(
                job_id=job_id,
                script_content=script_content,
                request_json=request_json,
                input_path=input_path,
                output_path=output_path,
                timeout=timeout
            )
        else:
            # Docker requires file paths
            return self._runner.run_script(
                job_id=job_id,
                script_path=script_path,
                request_path=request_path,
                input_path=input_path,
                output_path=output_path,
                timeout=timeout
            )
    
    def get_runtime_info(self) -> Dict[str, Any]:
        """Get information about the current runtime."""
        return {
            "runtime": self.runtime,
            "config": self.config,
            "runner_type": type(self._runner).__name__
        }


# Singleton instance
_unified_runner: Optional[UnifiedRunner] = None


def get_runner() -> UnifiedRunner:
    """Get or create the unified runner instance."""
    global _unified_runner
    if _unified_runner is None:
        _unified_runner = UnifiedRunner()
    return _unified_runner
