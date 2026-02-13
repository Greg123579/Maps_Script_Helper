import os, sys, json, pathlib
import traceback

print("=" * 60)
print("[DEBUG] job_runner.py starting...")
print(f"[DEBUG] Python version: {sys.version}")
print(f"[DEBUG] Working directory: {os.getcwd()}")
print(f"[DEBUG] PYTHONPATH: {os.environ.get('PYTHONPATH', 'not set')}")
print("=" * 60)

# CRITICAL: Create output and matplotlib config directory BEFORE importing matplotlib
# This must happen before any matplotlib import, as matplotlib tries to access
# its config directory during import. The MPLCONFIGDIR env var is set in Dockerfile,
# but we need to ensure the directory exists and is writable.

# Use current working directory (which is set to /outputs/{job-id} in K8s)
# or fall back to /output and /input for Docker compatibility
working_directory = pathlib.Path(os.getcwd())
# For K8s: use ./input and ./result when they exist. For Docker: /input and /output are mounted.
output_dir = (working_directory / "result") if (working_directory / "result").exists() else pathlib.Path("/output")
input_dir = (working_directory / "input") if (working_directory / "input").exists() else pathlib.Path("/input")
matplotlib_dir = output_dir / ".matplotlib"

print(f"[DEBUG] Checking output directory: {output_dir}...")

# Ensure output exists (it should be created by k8s_runner or Docker, but verify)
if not output_dir.exists():
    print(f"[DEBUG] {output_dir} does not exist, attempting to create...")
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"[DEBUG] Created {output_dir} directory")
    except Exception as e:
        print(f"Error: Could not create {output_dir}: {e}", file=sys.stderr)
        sys.exit(1)
else:
    print(f"[DEBUG] {output_dir} exists")

# List contents of output dir
print(f"[DEBUG] Contents of {output_dir} BEFORE script execution:")
try:
    for item in output_dir.iterdir():
        print(f"[DEBUG]   - {item.name} (is_file={item.is_file()})")
except Exception as e:
    print(f"[DEBUG]   Error listing {output_dir}: {e}")

# List contents of input dir (input_dir already set above)
# Set environment variable for MapsBridge to use
os.environ['INPUT_DIR'] = str(input_dir)
os.environ['OUTPUT_DIR'] = str(output_dir)
print(f"[DEBUG] Contents of {input_dir}:")
if input_dir.exists():
    try:
        for item in input_dir.iterdir():
            print(f"[DEBUG]   - {item.name} (is_file={item.is_file()})")
    except Exception as e:
        print(f"[DEBUG]   Error listing {input_dir}: {e}")
else:
    print(f"[DEBUG]   {input_dir} does not exist!")

# Handle matplotlib config directory
# The directory should be created by the host before mounting with world-writable permissions.
# If it doesn't exist, try to create it. If creation fails, that's OK if it exists and is writable.
if not matplotlib_dir.exists():
    try:
        matplotlib_dir.mkdir(parents=True, exist_ok=True)
        print(f"[DEBUG] Created {matplotlib_dir} directory")
    except (PermissionError, OSError) as e:
        # Directory creation failed - check if it exists now (might have been created by host)
        if not matplotlib_dir.exists():
            print(f"Warning: Could not create {matplotlib_dir}: {e}", file=sys.stderr)
            print(f"Attempting to continue - directory may be created by host...", file=sys.stderr)
        # If it exists now, continue - we'll verify writability below

# Verify the directory exists and is writable
if not matplotlib_dir.exists():
    print(f"Error: {matplotlib_dir} does not exist and could not be created", file=sys.stderr)
    sys.exit(1)

if not os.access(str(matplotlib_dir), os.W_OK):
    print(f"Error: {matplotlib_dir} exists but is not writable", file=sys.stderr)
    try:
        stat_info = matplotlib_dir.stat()
        print(f"Directory permissions: {oct(stat_info.st_mode)}", file=sys.stderr)
        print(f"Directory owner: UID={stat_info.st_uid}, GID={stat_info.st_gid}", file=sys.stderr)
        print(f"Current process UID={os.getuid()}, GID={os.getgid()}", file=sys.stderr)
    except Exception:
        pass
    sys.exit(1)

# Verify MPLCONFIGDIR is set (should be set in Dockerfile, but double-check)
if 'MPLCONFIGDIR' not in os.environ:
    os.environ['MPLCONFIGDIR'] = str(matplotlib_dir)

print(f"[DEBUG] Importing skimage and matplotlib...")

# Now it's safe to import matplotlib
from skimage import io, img_as_ubyte

# Set matplotlib backend to non-interactive for headless Docker environment
import matplotlib
matplotlib.use('Agg')

print(f"[DEBUG] Imports complete")

# Check if MapsBridge is available
print(f"[DEBUG] Checking MapsBridge availability...")
try:
    import MapsBridge
    print(f"[DEBUG] MapsBridge imported successfully from: {MapsBridge.__file__ if hasattr(MapsBridge, '__file__') else 'unknown'}")
except ImportError as e:
    print(f"[DEBUG] WARNING: MapsBridge import failed: {e}")

"""
This runner expects the user code at /code/main.py (or /work/main.py in K8s).
It sets USER_PARAMS env var (JSON).
User code is free to import scikit-image, numpy, imageio, matplotlib as preinstalled.
The user code should read from input_dir and write to output_dir (defined above based on runtime)
"""

def main():
    print(f"[DEBUG] main() starting...")
    
    # Debug: List what's in /code and /work directories
    print(f"[DEBUG] Checking /code directory...")
    code_dir = pathlib.Path("/code")
    if code_dir.exists():
        print(f"[DEBUG] /code exists, contents:")
        for item in code_dir.iterdir():
            print(f"[DEBUG]   - {item.name} (is_file={item.is_file()})")
    else:
        print(f"[DEBUG] /code directory does NOT exist")
    
    print(f"[DEBUG] Checking /work directory...")
    work_dir = pathlib.Path("/work")
    if work_dir.exists():
        print(f"[DEBUG] /work exists, contents:")
        for item in work_dir.iterdir():
            print(f"[DEBUG]   - {item.name} (is_file={item.is_file()})")
    else:
        print(f"[DEBUG] /work directory does NOT exist")
    
    # Try both /code (Docker) and /work (K8s) paths
    code_path = pathlib.Path("/work/main.py") if pathlib.Path("/work/main.py").exists() else pathlib.Path("/code/main.py")
    if not code_path.exists():
        print("No /code/main.py or /work/main.py found", file=sys.stderr)
        sys.exit(1)
    
    print(f"[DEBUG] Found code file: {code_path}")
    
    # Print the code being executed
    src = code_path.read_text(encoding="utf-8")
    print(f"[DEBUG] Code to execute ({len(src)} chars):")
    print("-" * 40)
    for i, line in enumerate(src.split('\n')[:20], 1):
        print(f"[DEBUG] {i:3d}: {line}")
    if len(src.split('\n')) > 20:
        print(f"[DEBUG] ... ({len(src.split(chr(10))) - 20} more lines)")
    print("-" * 40)

    # Make sure output exists and matplotlib config directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    matplotlib_dir.mkdir(parents=True, exist_ok=True)

    # Execute user code in a restricted namespace (same process). In a real
    # system we'd exec a new interpreter; here it's OK for MVP since we are already
    # in an isolated container with no network and limited resources.
    # IMPORTANT: Set __name__ to "__main__" so that `if __name__ == "__main__":` blocks execute
    user_globals = {
        '__builtins__': __builtins__,
        '__name__': '__main__',
        '__file__': str(code_path),
    }
    
    print(f"[DEBUG] Executing user code...")
    print(f"[DEBUG] __name__ set to: {user_globals['__name__']}")
    try:
        exec(compile(src, str(code_path), "exec"), user_globals, user_globals)
        print(f"[DEBUG] User code execution completed successfully")
    except Exception as e:
        print(f"User code error: {e}", file=sys.stderr)
        print(f"[DEBUG] Full traceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(2)
    
    # List contents of output_dir AFTER execution
    print(f"[DEBUG] Contents of {output_dir} AFTER script execution:")
    try:
        output_files = list(output_dir.iterdir())
        if not output_files:
            print(f"[DEBUG]   (empty - no files!)")
        for item in output_files:
            if item.is_file():
                size = item.stat().st_size
                print(f"[DEBUG]   - {item.name} ({size} bytes)")
            else:
                print(f"[DEBUG]   - {item.name}/ (directory)")
    except Exception as e:
        print(f"[DEBUG]   Error listing {output_dir}: {e}")
    
    print(f"[DEBUG] job_runner.py finished")

if __name__ == "__main__":
    main()
