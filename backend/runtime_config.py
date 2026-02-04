"""
Runtime detection and configuration for script execution.
Auto-detects whether to use Docker or Kubernetes based on environment.
"""

import os
from typing import Literal

RuntimeType = Literal["docker", "kubernetes"]


def detect_runtime() -> RuntimeType:
    """
    Auto-detect the execution runtime.
    
    Priority:
    1. EXECUTION_RUNTIME env var (explicit override)
    2. Check for Kubernetes environment (KUBERNETES_SERVICE_HOST)
    3. Default to Docker
    """
    # Explicit override
    runtime = os.getenv("EXECUTION_RUNTIME", "").lower()
    if runtime in ["docker", "kubernetes"]:
        return runtime
    
    # Auto-detect Kubernetes
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        return "kubernetes"
    
    # Default to Docker (for local development)
    return "docker"


def is_kubernetes() -> bool:
    """Check if running in Kubernetes environment."""
    return detect_runtime() == "kubernetes"


def is_docker() -> bool:
    """Check if running in Docker environment."""
    return detect_runtime() == "docker"


def get_runtime_config() -> dict:
    """Get runtime-specific configuration."""
    runtime = detect_runtime()
    
    if runtime == "kubernetes":
        return {
            "runtime": "kubernetes",
            "namespace": os.getenv("KUBERNETES_NAMESPACE", "maps-python"),
            "runner_image": os.getenv("RUNNER_IMAGE", "py-exec:latest"),
            "timeout": int(os.getenv("SCRIPT_TIMEOUT", "600")),
        }
    else:
        return {
            "runtime": "docker",
            "runner_image": os.getenv("RUNNER_IMAGE", "py-exec:latest"),
            "timeout": int(os.getenv("SCRIPT_TIMEOUT", "600")),
            "docker_socket": os.getenv("DOCKER_SOCKET", "/var/run/docker.sock"),
        }
