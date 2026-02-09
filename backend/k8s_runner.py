"""
Kubernetes runner module for executing user scripts in pods instead of Docker containers.
This replaces the Docker-in-Docker pattern with Kubernetes Pod API.
"""

import os
import json
import time
from typing import Optional, Dict, Any
from kubernetes import client, config
from kubernetes.client.rest import ApiException


class KubernetesRunner:
    """Manages script execution using Kubernetes Pods instead of Docker containers."""
    
    def __init__(self, namespace: str = "maps-python", runner_image: str = "py-exec:latest", timeout: int = 600):
        """Initialize Kubernetes client."""
        self.namespace = namespace
        self.runner_image = runner_image
        self.default_timeout = timeout
        
        # Try in-cluster config first, fall back to kubeconfig
        try:
            config.load_incluster_config()
            print("✓ Loaded in-cluster Kubernetes config")
        except config.ConfigException:
            try:
                config.load_kube_config()
                print("✓ Loaded kubeconfig")
            except config.ConfigException as e:
                raise RuntimeError(f"Could not configure Kubernetes client: {e}")
        
        self.core_v1 = client.CoreV1Api()
        self.batch_v1 = client.BatchV1Api()
    
    def create_script_configmap(self, job_id: str, script_content: str, request_json: str) -> str:
        """Create a ConfigMap containing the script and request data."""
        configmap_name = f"job-code-{job_id}"
        
        configmap = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(name=configmap_name, namespace=self.namespace),
            data={
                "main.py": script_content,
                "request.json": request_json
            }
        )
        
        try:
            self.core_v1.create_namespaced_config_map(
                namespace=self.namespace,
                body=configmap
            )
            print(f"✓ Created ConfigMap: {configmap_name}")
            return configmap_name
        except ApiException as e:
            raise RuntimeError(f"Failed to create ConfigMap: {e}")
    
    def create_runner_pod(
        self,
        job_id: str,
        configmap_name: str,
        input_path: str,
        output_path: str
    ) -> str:
        """Create a pod to execute the user script."""
        pod_name = f"runner-{job_id}"
        
        # Extract job directory from paths
        # input_path is like /app/outputs/job-id/input
        # We need to extract just the job-id part
        import os
        job_dir = os.path.basename(os.path.dirname(input_path))  # Extract job-id from path
        
        # Define the pod specification
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(
                name=pod_name,
                namespace=self.namespace,
                labels={
                    "app": "maps-runner",
                    "job-id": job_id
                }
            ),
            spec=client.V1PodSpec(
                restart_policy="Never",
                service_account_name="tfstack-maps-data-analysis",
                containers=[
                    client.V1Container(
                        name="runner",
                        image=self.runner_image,
                        image_pull_policy="IfNotPresent",
                        command=["python", "-u", "/work/job_runner.py"],
                        env=[
                            client.V1EnvVar(name="MPLCONFIGDIR", value=f"/outputs/{job_dir}/result/.matplotlib"),
                            client.V1EnvVar(name="JOB_ID", value=job_id)
                        ],
                        volume_mounts=[
                            client.V1VolumeMount(
                                name="code",
                                mount_path="/code",
                                read_only=True
                            ),
                            client.V1VolumeMount(
                                name="outputs",
                                mount_path="/outputs"
                            )
                        ],
                        working_dir=f"/outputs/{job_dir}",
                        resources=client.V1ResourceRequirements(
                            requests={"memory": "256Mi", "cpu": "100m"},
                            limits={"memory": "1Gi", "cpu": "500m"}
                        )
                    )
                ],
                volumes=[
                    client.V1Volume(
                        name="code",
                        config_map=client.V1ConfigMapVolumeSource(
                            name=configmap_name,
                            items=[
                                client.V1KeyToPath(key="main.py", path="main.py"),
                                client.V1KeyToPath(key="request.json", path="request.json")
                            ]
                        )
                    ),
                    client.V1Volume(
                        name="outputs",
                        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                            claim_name="maps-outputs"
                        )
                    )
                ]
            )
        )
        
        try:
            self.core_v1.create_namespaced_pod(
                namespace=self.namespace,
                body=pod
            )
            print(f"✓ Created Pod: {pod_name}")
            return pod_name
        except ApiException as e:
            raise RuntimeError(f"Failed to create Pod: {e}")
    
    def wait_for_pod_completion(self, pod_name: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Wait for pod to complete and return status."""
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                pod = self.core_v1.read_namespaced_pod(
                    name=pod_name,
                    namespace=self.namespace
                )
                
                phase = pod.status.phase
                
                if phase == "Succeeded":
                    return {"status": "success", "exit_code": 0}
                elif phase == "Failed":
                    container_status = pod.status.container_statuses[0] if pod.status.container_statuses else None
                    exit_code = container_status.state.terminated.exit_code if container_status and container_status.state.terminated else 1
                    return {"status": "failed", "exit_code": exit_code}
                
                # Still running
                time.sleep(2)
                
            except ApiException as e:
                if e.status == 404:
                    return {"status": "failed", "exit_code": -1, "error": "Pod not found"}
                raise
        
        return {"status": "timeout", "exit_code": -1}
    
    def get_pod_logs(self, pod_name: str) -> str:
        """Retrieve logs from a pod."""
        try:
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=self.namespace,
                container="runner"
            )
            return logs
        except ApiException as e:
            return f"Error retrieving logs: {e}"
    
    def cleanup_pod(self, pod_name: str, configmap_name: str):
        """Delete pod and associated ConfigMap."""
        try:
            # Delete pod
            self.core_v1.delete_namespaced_pod(
                name=pod_name,
                namespace=self.namespace,
                body=client.V1DeleteOptions()
            )
            print(f"✓ Deleted Pod: {pod_name}")
        except ApiException as e:
            print(f"Warning: Failed to delete Pod {pod_name}: {e}")
        
        try:
            # Delete ConfigMap
            self.core_v1.delete_namespaced_config_map(
                name=configmap_name,
                namespace=self.namespace,
                body=client.V1DeleteOptions()
            )
            print(f"✓ Deleted ConfigMap: {configmap_name}")
        except ApiException as e:
            print(f"Warning: Failed to delete ConfigMap {configmap_name}: {e}")
    
    def run_script(
        self,
        job_id: str,
        script_content: str,
        request_json: str,
        input_path: str,
        output_path: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a script in a Kubernetes pod.
        
        Returns a dict with:
        - status: "success", "failed", or "timeout"
        - exit_code: int
        - logs: str
        """
        timeout = timeout or self.default_timeout
        configmap_name = None
        pod_name = None
        
        try:
            # Create directories in PVC for this job
            job_dir = os.path.basename(input_path.rstrip('/'))  # Extract job-id from path
            # Note: We rely on the backend creating these directories before calling run_script
            # The input_path and output_path are full paths like /app/outputs/{job-id}/input
            # We just need the job-id directory name
            if '/' in input_path:
                parts = input_path.rstrip('/').split('/')
                job_dir = parts[-2] if parts[-1] in ('input', 'result') else parts[-1]
            else:
                job_dir = input_path
                
            # Create ConfigMap with script
            configmap_name = self.create_script_configmap(job_id, script_content, request_json)
            
            # Create and run pod
            pod_name = self.create_runner_pod(job_id, configmap_name, input_path, output_path)
            
            # Wait for completion
            result = self.wait_for_pod_completion(pod_name, timeout)
            
            # Get logs
            result["logs"] = self.get_pod_logs(pod_name)
            
            return result
            
        finally:
            # Cleanup - TEMPORARILY DISABLED FOR DEBUGGING
            print(f"[DEBUG] Cleanup disabled. Pod: {pod_name}, ConfigMap: {configmap_name}")
            # if pod_name and configmap_name:
            #     self.cleanup_pod(pod_name, configmap_name)


# Singleton instance
_runner: Optional[KubernetesRunner] = None


def get_runner() -> KubernetesRunner:
    """Get or create the Kubernetes runner instance."""
    global _runner
    if _runner is None:
        namespace = os.getenv("KUBERNETES_NAMESPACE", "maps-data-analysis")
        runner_image = os.getenv("RUNNER_IMAGE", "py-exec:latest")
        timeout = int(os.getenv("SCRIPT_TIMEOUT", "600"))
        _runner = KubernetesRunner(namespace, runner_image, timeout)
    return _runner
