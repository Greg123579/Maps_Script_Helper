import os, uuid, shutil, json, pathlib, subprocess, traceback, io, time
from datetime import datetime
from typing import Optional, List
import threading

_start_time = time.time()
def _log_import(module_name: str):
    elapsed = time.time() - _start_time
    print(f"[Startup] {elapsed:.2f}s - Importing {module_name}...")

_log_import("FastAPI")
from fastapi import FastAPI, UploadFile, File, Form, Response, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import re
_log_import("PIL")
from PIL import Image
from contextlib import asynccontextmanager
import asyncio
from pydantic import BaseModel
_log_import("google.generativeai")
import google.generativeai as genai
_log_import("SQLAlchemy")
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Import logging modules
try:
    from backend.script_logger import ScriptLogger
    from backend.log_analyzer import LogAnalyzer
    from backend.database import get_db, init_database
    from backend.models import User, UserScript, LibraryImage, UserImage, LibraryScript, ExecutionSession
except ImportError:
    # When running from backend/ directory
    from script_logger import ScriptLogger
    from log_analyzer import LogAnalyzer
    from database import get_db, init_database
    from models import User, UserScript, LibraryImage, UserImage, LibraryScript, ExecutionSession

# Initialize script execution runtime (auto-detects Docker or Kubernetes)
_log_import("Script execution runtime")
try:
    from backend.runtime_config import detect_runtime
except ImportError:
    from runtime_config import detect_runtime

_execution_runtime = detect_runtime()
script_runner = None

if _execution_runtime == "kubernetes":
    _log_import("Kubernetes client")
    try:
        from backend.k8s_runner import get_runner as get_k8s_runner
        script_runner = get_k8s_runner()
        print("✓ Using Kubernetes runtime for script execution")
    except Exception as e:
        print(f"⚠ WARNING: Failed to initialize Kubernetes runner: {e}")
        traceback.print_exc()
        print("  Falling back to Docker runtime...")
        _execution_runtime = "docker"

if _execution_runtime == "docker":
    try:
        from backend.docker_runner import get_runner as get_docker_runner
        script_runner = get_docker_runner()
        print("✓ Using Docker runtime for script execution")
    except Exception as e:
        print(f"✗ ERROR: Failed to initialize any script runner: {e}")
        traceback.print_exc()
        raise RuntimeError("No script execution runtime available. Cannot start backend.") from e

_import_time = time.time() - _start_time
print(f"[Startup] {_import_time:.2f}s - All imports complete")

# Version tracking
API_VERSION = "1.20.1"  # Fixed batch file syntax, added startup timing logs, improved deployment script

# Configure Gemini AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    # Show masked key for confirmation (first 3 and last 3 characters)
    masked_key = f"{GOOGLE_API_KEY[:3]}...{GOOGLE_API_KEY[-3:]}" if len(GOOGLE_API_KEY) > 6 else "***"
    print(f"✓ Gemini AI configured successfully (Key: {masked_key})")
else:
    print("⚠ Warning: GOOGLE_API_KEY not set. AI Assistant will not work.")

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = BASE_DIR / "assets"
OUTPUTS_DIR = BASE_DIR / "outputs"
LOGS_DIR = BASE_DIR / "logs"


_PY_EXEC_PIP_CACHE = {
    "generated_at": 0.0,
    "packages": None,  # dict[str, str] of name->version
}


def _get_py_exec_pip_packages(max_age_seconds: int = 600) -> dict[str, str]:
    """
    Return pip packages installed in the script execution sandbox image (py-exec:latest).

    Reads from requirements.txt file. Cached for max_age_seconds to avoid repeated file reads.
    """
    now = time.time()
    cached = _PY_EXEC_PIP_CACHE.get("packages")
    if cached and (now - float(_PY_EXEC_PIP_CACHE.get("generated_at", 0.0)) < max_age_seconds):
        return cached

    try:
        # Read from requirements file (more reliable than querying a pod)
        req_path = BASE_DIR / "backend" / "runner_image" / "requirements.txt"
        if req_path.exists():
            pkgs: dict[str, str] = {}
            for line in req_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Parse "package==version" or just "package"
                if "==" in line:
                    name, version = line.split("==", 1)
                    pkgs[name.strip()] = version.strip()
                else:
                    pkgs[line.strip()] = "installed"
            
            if pkgs:
                _PY_EXEC_PIP_CACHE["generated_at"] = now
                _PY_EXEC_PIP_CACHE["packages"] = pkgs
                return pkgs
    except Exception as e:
        print(f"Warning: Could not read requirements file: {e}")
    
    # Fallback to empty dict
    return {}


def _get_py_exec_requirements_summary() -> str:
    """
    Build a concise, AI-readable list of 3rd-party libs available in the execution sandbox (py-exec).

    Important: This is the environment that runs user scripts (job_runner.py), not the FastAPI backend.
    """
    pip_pkgs = _get_py_exec_pip_packages()
    pkg_names = sorted(pip_pkgs.keys(), key=str.lower) if pip_pkgs else []

    parts: list[str] = []
    parts.append("Third-party packages installed in the execution sandbox (py-exec):")
    if pkg_names:
        parts.append(", ".join(pkg_names))
    else:
        # Fallback: at least show what we *intend* to install (direct requirements)
        req_path = BASE_DIR / "backend" / "runner_image" / "requirements.txt"
        if req_path.exists():
            req_lines = []
            for raw in req_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "#" in line:
                    line = line.split("#", 1)[0].strip()
                req_lines.append(line)
            parts.append("Direct requirements include:")
            parts.append(", ".join(req_lines) if req_lines else "(none)")
        else:
            parts.append("Unknown (requirements file not found).")

    # Import cheat sheet: only include items that are actually present (best-effort)
    installed_lower = {n.lower() for n in pkg_names}
    cheat_sheet = [
        ("numpy", "import numpy as np"),
        ("pandas", "import pandas as pd"),
        ("matplotlib", "import matplotlib.pyplot as plt"),
        ("opencv-python-headless", "import cv2"),
        ("scikit-image", "from skimage import filters, morphology, measure"),
        ("scipy", "from scipy import ndimage"),
        ("pillow", "from PIL import Image"),
        ("imageio", "import imageio.v3 as iio"),
        ("tifffile", "import tifffile"),
        ("fpdf2", "from fpdf import FPDF"),
        ("reportlab", "from reportlab.pdfgen import canvas"),
        ("networkx", "import networkx as nx"),
    ]
    present = []
    for pkg, imp in cheat_sheet:
        # match either exact package name or common variants
        if pkg.lower() in installed_lower:
            present.append(imp)
        elif pkg.lower() == "opencv-python-headless" and ("opencv-python-headless" in installed_lower):
            present.append(imp)
        elif pkg.lower() == "scikit-image" and ("scikit-image" in installed_lower or "skimage" in installed_lower):
            present.append(imp)
        elif pkg.lower() == "pillow" and ("pillow" in installed_lower):
            present.append(imp)

    if present:
        parts.append("")
        parts.append("IMPORT CHEAT SHEET (use these exact imports):")
        parts.extend([f"- {imp}" for imp in present])

    parts.append("")
    parts.append("Do NOT assume other packages are installed unless listed above. If a library would help but is missing, recommend it as an optional install.")
    return "\n".join(parts)


def _get_py_exec_installed_packages() -> set[str]:
    """Return normalized package names installed in py-exec (best-effort)."""
    pkgs = _get_py_exec_pip_packages()
    if pkgs:
        return {k.strip().lower() for k in pkgs.keys()}

    # Fallback to requirements.txt parsing
    req_path = BASE_DIR / "backend" / "runner_image" / "requirements.txt"
    if not req_path.exists():
        return set()
    out: set[str] = set()
    for raw in req_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "#" in line:
            line = line.split("#", 1)[0].strip()
        m = re.match(r"^([A-Za-z0-9_.-]+)", line)
        if m:
            out.add(m.group(1).strip().lower())
    return out


def _get_recent_missing_modules_from_logs(max_modules: int = 8) -> list[tuple[str, int]]:
    """
    Extract ModuleNotFoundError names from recent failure logs.
    Returns list of (module_name, count) sorted by count desc.
    """
    failures_dir = LOGS_DIR / "failures"
    if not failures_dir.exists():
        return []

    counts: dict[str, int] = {}
    pattern = re.compile(r"No module named ['\"]([^'\"]+)['\"]", re.IGNORECASE)

    # Iterate newest date dirs first (lexicographic YYYY-MM-DD matches chronological)
    date_dirs = [d for d in failures_dir.iterdir() if d.is_dir()]
    for date_dir in sorted(date_dirs, reverse=True)[:7]:
        for log_file in date_dir.glob("*.json"):
            try:
                data = json.loads(log_file.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            text = " ".join([
                str(data.get("error_message", "")),
                str(data.get("stderr", "")),
            ])
            for m in pattern.finditer(text):
                mod = m.group(1).strip()
                if not mod:
                    continue
                counts[mod] = counts.get(mod, 0) + 1

    ranked = sorted(counts.items(), key=lambda x: (-x[1], x[0].lower()))
    return ranked[:max_modules]


def _get_optional_library_recommendations_summary() -> str:
    """
    Provide optional "nice-to-have" libraries that are NOT installed by default.
    This is a recommendation list for the user/operator (to update the py-exec image),
    NOT permission for the AI to import them unless the user confirms they are installed.
    """
    installed = _get_py_exec_installed_packages()

    # Curated list: (pip_package, import_hint, why)
    wishlist: list[tuple[str, str, str]] = [
        ("openpyxl", "import openpyxl", "Write Excel .xlsx reports (tables, summary stats)"),
        ("xlsxwriter", "import xlsxwriter", "Fast Excel writer for formatted reports"),
        ("PyYAML", "import yaml", "Read/write YAML configs for parameterized scripts"),
        ("numba", "from numba import njit", "Speed up heavy numeric loops (CPU JIT)"),
        ("zarr", "import zarr", "Chunked storage for large arrays / large image stacks"),
        ("dask", "import dask.array as da", "Out-of-core processing for very large images"),
        ("pywavelets", "import pywt", "Wavelet denoise / multiscale analysis"),
    ]

    missing = [(pkg, imp, why) for (pkg, imp, why) in wishlist if pkg.lower() not in installed]

    # Also include “missing imports seen in logs” (operator-focused)
    missing_from_logs = _get_recent_missing_modules_from_logs(max_modules=8)

    # Map "module name" -> "package name" suggestion (best-effort)
    module_to_pkg = {
        "fpdf": "fpdf2",
        "yaml": "PyYAML",
        "cv2": "opencv-python-headless",
        "skimage": "scikit-image",
        "pil": "Pillow",
    }

    provides_module = {
        # If fpdf2 is installed, "fpdf" import is valid
        "fpdf": ("fpdf2" in installed),
        "cv2": ("opencv-python-headless" in installed),
        "PIL": ("pillow" in installed),
    }

    parts: list[str] = []
    parts.append("Optional recommended libraries (NOT installed by default):")
    if not missing:
        parts.append("(none from the curated list)")
    else:
        for pkg, imp, why in missing:
            parts.append(f"- {pkg}: {why}  |  e.g. `{imp}`  |  pip: `{pkg}`")

    if missing_from_logs:
        parts.append("")
        parts.append("Modules that previously failed to import (from recent logs):")
        for mod, cnt in missing_from_logs:
            suggested_pkg = module_to_pkg.get(mod, mod)
            now_ok = provides_module.get(mod) is True
            status = "now available" if now_ok else "not installed"
            parts.append(f"- {mod} (x{cnt}): suggested pip package `{suggested_pkg}` ({status})")

    parts.append("")
    parts.append("IMPORTANT: Only suggest these to the user as install options; do NOT import them in code unless the user confirms they are installed.")
    return "\n".join(parts)

LIBRARY_DIR = BASE_DIR / "library"
LIBRARY_IMAGES_DIR = LIBRARY_DIR / "images"
LIBRARY_METADATA_FILE = LIBRARY_DIR / "metadata.json"
USER_JOBS_FILE = BASE_DIR / "user_jobs.json"  # Track user_id -> job_ids mapping
USERS_FILE = BASE_DIR / "users.json"  # Track user accounts

# User uploads directory - stored on PVC (maps-assets) for persistence across deploys
# Library images stay baked into the Docker image at /app/library/images/
USER_UPLOADS_DIR = ASSETS_DIR / "uploads"

# Ensure library directories exist
LIBRARY_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
USER_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
if not LIBRARY_METADATA_FILE.exists():
    LIBRARY_METADATA_FILE.write_text("{}", encoding="utf-8")

# Cleanup synchronization (prevents multiple concurrent cleanups)
CLEANUP_MUTEX = threading.Lock()
CLEANUP_LOCK_FILE = OUTPUTS_DIR / ".cleanup.lock"
ACTIVE_MARKER_NAME = ".active"

# Initialize users.json
try:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text("{}", encoding="utf-8")
except Exception as e:
    print(f"Warning: Failed to initialize users.json: {e}")

# Initialize logging system
script_logger = ScriptLogger(LOGS_DIR)
log_analyzer = LogAnalyzer(LOGS_DIR)

def auto_seed_database():
    """Automatically seed database with library scripts and images if empty"""
    import os
    from backend.database import get_db_session
    from backend.models import LibraryScript, LibraryImage
    
    # Skip auto-seeding if SKIP_AUTO_SEED is set (when using pre-populated DB)
    if os.getenv("SKIP_AUTO_SEED", "").lower() in ("true", "1", "yes"):
        print("[Init] SKIP_AUTO_SEED is set, skipping database seeding")
        return
    
    print("[Init] Checking if database needs seeding...")
    
    with get_db_session() as db:
        # Check if library scripts exist
        script_count = db.query(LibraryScript).count()
        image_count = db.query(LibraryImage).count()
        
        # Seed library scripts if empty
        if script_count == 0:
            print("[Init] No library scripts found, seeding...")
            try:
                # Import the seed data directly
                import importlib.util
                seed_script_path = BASE_DIR / "seed_library_scripts.py"
                
                if seed_script_path.exists():
                    # Read and execute the LIBRARY_SCRIPTS from seed file
                    spec = importlib.util.spec_from_file_location("seed_library_scripts", seed_script_path)
                    seed_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(seed_module)
                    LIBRARY_SCRIPTS = seed_module.LIBRARY_SCRIPTS
                    
                    added_count = 0
                    for script_data in LIBRARY_SCRIPTS:
                        # Check if already exists (idempotent)
                        existing = db.query(LibraryScript).filter(
                            LibraryScript.name == script_data["name"]
                        ).first()
                        if existing:
                            continue
                            
                        library_script = LibraryScript(
                            name=script_data["name"],
                            filename=f"{script_data['name'].lower().replace(' ', '_')}.py",
                            description=script_data["description"],
                            category=script_data["category"],
                            tags=script_data["tags"],
                            code=script_data["code"]
                        )
                        db.add(library_script)
                        added_count += 1
                    
                    db.commit()
                    print(f"[Init] ✓ Seeded {added_count} library scripts")
                else:
                    print(f"[Init] ⚠ Seed script not found at {seed_script_path}")
            except Exception as e:
                print(f"[Init] ⚠ Could not seed scripts: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[Init] ✓ Found {script_count} existing library scripts")
        
        # Migrate library images if metadata.json exists
        if image_count == 0 and LIBRARY_METADATA_FILE.exists():
            print("[Init] No library images found, migrating from metadata.json...")
            try:
                import json
                from PIL import Image
                from datetime import datetime
                
                with open(LIBRARY_METADATA_FILE, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                library_count = 0
                for image_id, image_data in metadata.items():
                    # Check if already exists
                    existing = db.query(LibraryImage).filter(
                        LibraryImage.id == image_id
                    ).first()
                    if existing:
                        continue
                    
                    filename = image_data.get("filename", "")
                    image_path = LIBRARY_IMAGES_DIR / filename
                    
                    # Get image dimensions if file exists
                    width, height, file_size = None, None, None
                    if image_path.exists():
                        try:
                            with Image.open(image_path) as img:
                                width, height = img.size
                            file_size = image_path.stat().st_size
                        except:
                            pass
                    
                    # Only migrate library images (no user_id)
                    user_id = image_data.get("user_id")
                    if not user_id:
                        library_image = LibraryImage(
                            id=image_id,
                            name=image_data.get("name", filename),
                            filename=filename,
                            description=image_data.get("description", ""),
                            image_type=image_data.get("type", "SEM"),
                            category=image_data.get("category", "default"),
                            width=width,
                            height=height,
                            file_size=file_size,
                            created_at=datetime.utcnow()
                        )
                        db.add(library_image)
                        library_count += 1
                
                db.commit()
                print(f"[Init] ✓ Migrated {library_count} library images")
            except Exception as e:
                print(f"[Init] ⚠ Could not migrate images: {e}")
                import traceback
                traceback.print_exc()
        elif image_count > 0:
            print(f"[Init] ✓ Found {image_count} existing library images")
        elif not LIBRARY_METADATA_FILE.exists():
            print(f"[Init] ⚠ No metadata.json found at {LIBRARY_METADATA_FILE}, skipping image migration")

# Initialize user_jobs.json - handle case where Docker might have created it as a directory
if USER_JOBS_FILE.exists():
    if USER_JOBS_FILE.is_dir():
        try:
            shutil.rmtree(USER_JOBS_FILE)
            USER_JOBS_FILE.write_text("{}", encoding="utf-8")
        except Exception as e:
            print(f"Warning: Failed to fix user_jobs.json directory: {e}")
    elif USER_JOBS_FILE.is_file():
        # File exists and is a file, nothing to do
        pass
else:
    # File doesn't exist, create it
    USER_JOBS_FILE.write_text("{}", encoding="utf-8")

# Cleanup functions
def load_user_jobs():
    """Load user-job mappings"""
    if USER_JOBS_FILE.exists():
        try:
            return json.loads(USER_JOBS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_user_jobs(user_jobs):
    """Save user-job mappings"""
    USER_JOBS_FILE.write_text(json.dumps(user_jobs, indent=2), encoding="utf-8")

def cleanup_user_previous_jobs(user_id: str):
    """Clean up all previous job folders for a specific user"""
    user_jobs = load_user_jobs()
    if user_id in user_jobs:
        job_ids = user_jobs[user_id].copy()
        for job_id in job_ids:
            job_dir = OUTPUTS_DIR / job_id
            if job_dir.exists():
                try:
                    shutil.rmtree(job_dir)
                except Exception as e:
                    # Log error but continue cleanup
                    print(f"Warning: Failed to delete {job_dir}: {e}")
        # Clear the user's job list
        del user_jobs[user_id]
        save_user_jobs(user_jobs)

def cleanup_old_outputs(max_age_minutes: int = 30):
    """Delete output folders older than max_age_minutes.

    This is a global cleanup mechanism intended to prevent the outputs/ folder
    from growing without bound. It is run by the periodic cleanup task.

    Safety:
    - Any job directory containing an ".active" marker is treated as "in use"
      and will not be deleted (unless the marker is stale).
    - A lock is used to ensure only one cleanup runs at a time per backend
      process/container.
    """
    if not OUTPUTS_DIR.exists():
        return

    with CLEANUP_MUTEX:
        # Best-effort cross-process lock (works in Linux containers).
        # If we can't acquire the lock, skip to avoid concurrent cleanups.
        lock_fh = None
        fcntl = None
        try:
            CLEANUP_LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
            lock_fh = open(CLEANUP_LOCK_FILE, "w", encoding="utf-8")
            try:
                import fcntl as _fcntl  # type: ignore
                fcntl = _fcntl
                fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except Exception:
                try:
                    lock_fh.close()
                except Exception:
                    pass
                return
        except Exception:
            lock_fh = None

        try:
            current_time = time.time()
            max_age_seconds = max_age_minutes * 60
            deleted_count = 0

            for job_dir in OUTPUTS_DIR.iterdir():
                if not job_dir.is_dir():
                    continue

                # Skip active jobs (unless marker is stale)
                active_marker = job_dir / ACTIVE_MARKER_NAME
                if active_marker.exists():
                    try:
                        active_age = current_time - active_marker.stat().st_mtime
                        # Treat marker as stale if it's older than 2x max age
                        if active_age < (max_age_seconds * 2):
                            continue
                    except Exception:
                        # If marker can't be stat'ed, err on the side of skipping
                        continue

                try:
                    # Get modification time of the directory
                    mtime = job_dir.stat().st_mtime
                    age_seconds = current_time - mtime

                    if age_seconds >= max_age_seconds:
                        shutil.rmtree(job_dir)
                        deleted_count += 1
                except Exception as e:
                    print(f"Warning: Failed to delete {job_dir}: {e}")

            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} old output folder(s)")
        finally:
            if lock_fh is not None and fcntl is not None:
                try:
                    fcntl.flock(lock_fh, fcntl.LOCK_UN)
                except Exception:
                    pass
                try:
                    lock_fh.close()
                except Exception:
                    pass

def clear_all_outputs():
    """Clear all output folders (for startup cleanup)"""
    if not OUTPUTS_DIR.exists():
        return
    
    deleted_count = 0
    for job_dir in OUTPUTS_DIR.iterdir():
        if job_dir.is_dir():
            try:
                shutil.rmtree(job_dir)
                deleted_count += 1
            except Exception as e:
                print(f"Warning: Failed to delete {job_dir}: {e}")
    
    # Clear user jobs tracking
    # Handle case where Docker might have created it as a directory
    if USER_JOBS_FILE.exists() and USER_JOBS_FILE.is_dir():
        try:
            shutil.rmtree(USER_JOBS_FILE)
        except Exception as e:
            print(f"Warning: Failed to remove user_jobs.json directory: {e}")
    
    # Create/overwrite the file
    try:
        USER_JOBS_FILE.write_text("{}", encoding="utf-8")
    except Exception as e:
        print(f"Warning: Failed to create user_jobs.json: {e}")
    
    if deleted_count > 0:
        print(f"Cleared {deleted_count} output folder(s) on startup")

# ═══════════════════════════════════════════════════════════════
#              AUTO-DEBUG LOGGING UTILITIES
# ═══════════════════════════════════════════════════════════════

def get_session_consecutive_failures(session_id: str) -> int:
    """Count consecutive failures in a session (from most recent backward)."""
    if not session_id:
        return 0
    
    try:
        session_file = LOGS_DIR / "sessions" / f"{session_id}.json"
        if not session_file.exists():
            return 0
        
        session_data = json.loads(session_file.read_text(encoding="utf-8"))
        attempts = session_data.get("attempts", [])
        
        # Count consecutive failures from the end
        consecutive_failures = 0
        for attempt in reversed(attempts):
            if attempt.get("status") == "failure":
                consecutive_failures += 1
            else:
                break
        
        return consecutive_failures
    except Exception as e:
        print(f"Warning: Failed to check session failures: {e}")
        return 0

def has_debug_logging(code: str) -> bool:
    """Check if code already has auto-injected debug logging."""
    return "[AUTO-DEBUG]" in code

def inject_debug_logging(code: str) -> str:
    """
    Inject debug logging into Python code at strategic locations.
    Uses pattern-based injection for common failure points.
    """
    if has_debug_logging(code):
        return code  # Already has debug logging
    
    lines = code.split('\n')
    result = []
    
    for i, line in enumerate(lines):
        result.append(line)
        
        # Get indentation of current line
        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent
        
        # After Image.open calls
        if 'Image.open' in line and '=' in line:
            var = line.split('=')[0].strip()
            result.append(f'{indent_str}print(f"[AUTO-DEBUG] Loaded image: {var}, mode={{{var}.mode}}, size={{{var}.size}}, dtype={{type({var})}}")')
        
        # After cv2.imread calls
        elif 'cv2.imread' in line and '=' in line:
            var = line.split('=')[0].strip()
            result.append(f'{indent_str}print(f"[AUTO-DEBUG] cv2.imread: {var}, shape={{{var}.shape if {var} is not None else \'None\'}}, dtype={{{var}.dtype if {var} is not None else \'None\'}}")')
        
        # After MapsBridge.FromStdIn calls
        elif 'MapsBridge.' in line and 'FromStdIn' in line and '=' in line:
            var = line.split('=')[0].strip()
            result.append(f'{indent_str}print(f"[AUTO-DEBUG] MapsBridge request loaded: {var}, type={{type({var})}}")')
        
        # After MapsBridge path resolution
        elif 'ResolveSingleTileAndPath' in line and '=' in line:
            # Extract variable names (usually: tile, tileInfo, input_path = ...)
            if ',' in line.split('=')[0]:
                vars_part = line.split('=')[0].strip()
                result.append(f'{indent_str}print(f"[AUTO-DEBUG] Tile resolved: tile={{tile.Column if hasattr(tile, \'Column\') else \'?\'}}x{{tile.Row if hasattr(tile, \'Row\') else \'?\'}}, path={{input_path if \'input_path\' in locals() else \'?\'}}")')
        
        # After GetPreparedImagePath calls
        elif 'GetPreparedImagePath' in line and '=' in line:
            var = line.split('=')[0].strip()
            result.append(f'{indent_str}print(f"[AUTO-DEBUG] Prepared image path: {var}={{os.path.basename({var}) if os.path.exists({var}) else \'NOT FOUND\'}}")')
        
        # Before try blocks - add context logging
        elif line.strip().startswith('try:'):
            result.append(f'{indent_str}    print("[AUTO-DEBUG] Entering try block (line {i+1})")')
        
        # In except blocks - add detailed error logging
        elif line.strip().startswith('except') and ':' in line:
            # Add logging at the start of the except block
            next_indent = ' ' * (indent + 4)
            # We'll insert after the except line, so add a placeholder
            result.append(f'{next_indent}print(f"[AUTO-DEBUG] Exception caught: {{type(e).__name__ if \'e\' in locals() else \'unknown\'}}: {{e if \'e\' in locals() else \'?\'}}")')
    
    debug_code = '\n'.join(result)
    
    # Add header comment to indicate debug mode
    header = "# " + "="*70 + "\n"
    header += "# AUTO-DEBUG MODE ACTIVE\n"
    header += "# Diagnostic logging has been automatically injected to help\n"
    header += "# identify the issue. This will be removed after successful execution.\n"
    header += "# " + "="*70 + "\n\n"
    
    return header + debug_code

def remove_debug_logging(code: str) -> str:
    """Remove auto-injected debug logging from code."""
    if not has_debug_logging(code):
        return code
    
    lines = code.split('\n')
    cleaned = []
    
    # Skip header if present
    skip_header = False
    if lines and "AUTO-DEBUG MODE ACTIVE" in '\n'.join(lines[:5]):
        # Find where header ends
        for i, line in enumerate(lines):
            if i < 10 and ("="*20 in line or "AUTO-DEBUG MODE" in line or "diagnostic logging" in line.lower()):
                continue
            else:
                lines = lines[i:]
                break
    
    # Remove [AUTO-DEBUG] print statements
    for line in lines:
        if "[AUTO-DEBUG]" not in line:
            cleaned.append(line)
    
    return '\n'.join(cleaned)

async def periodic_cleanup():
    """Background task that runs periodic cleanup every 5 minutes"""
    while True:
        await asyncio.sleep(5 * 60)  # Wait 5 minutes
        cleanup_old_outputs(max_age_minutes=30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database and seed if needed
    startup_start = time.time()
    try:
        from backend.database import init_database
        # init_database() only creates tables if they don't exist - safe to call with existing DB
        db_start = time.time()
        init_database()
        print(f"[Startup] {time.time() - db_start:.2f}s - Database initialized")
        # auto_seed_database() checks if data exists and respects SKIP_AUTO_SEED env var
        seed_start = time.time()
        auto_seed_database()
        print(f"[Startup] {time.time() - seed_start:.2f}s - Database seeding complete")
        print(f"[Startup] {time.time() - startup_start:.2f}s - Total startup time")
    except Exception as e:
        print(f"[Init] Warning: Database initialization/seeding failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Startup: Start periodic cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown: Cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Python Image Sandbox MVP", lifespan=lifespan)

# Global exception handler to ensure JSON errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": f"Internal server error: {str(exc)}", "detail": traceback.format_exc()}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "detail": str(exc)}
    )

# Optional CORS for local testing (comment out if not needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility for safe integers
def clamp(v, lo, hi, default):
    try:
        x = int(v)
        return max(lo, min(hi, x))
    except Exception:
        return default

@app.post("/run")
async def run_code(
    code: str = Form(...),
    image: Optional[UploadFile] = File(None),
    use_sample: Optional[str] = Form("false"),
    user_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    previous_attempt_id: Optional[str] = Form(None),
    user_prompt: Optional[str] = Form(None),
    ai_model: Optional[str] = Form(None),
    inject_debug: Optional[str] = Form("false"),  # NEW: Allow explicit debug injection
    db: Session = Depends(get_db),
):
    """
    Receives Python source code + optional image.
    Runs the code inside a sandbox container and returns the result URL.
    If user_id is provided, cleans up previous files for that user.
    
    Logging parameters:
    - session_id: Groups related attempts (failures -> success)
    - previous_attempt_id: Links to previous failed attempt
    - user_prompt: Original user request for context
    - ai_model: Which AI model generated the code
    """
    execution_start_time = time.time()
    print(f"\n{'='*80}")
    print(f"[RUN] Received /run request")
    print(f"[RUN] Code length: {len(code) if code else 0} characters")
    print(f"[RUN] First 200 chars of code: {code[:200] if code else 'NO CODE'}")
    print(f"[RUN] Image provided: {image is not None}")
    print(f"[RUN] Use sample: {use_sample}")
    print(f"[RUN] User ID: {user_id}")
    print(f"{'='*80}\n")
    active_marker_path = None
    execution_record = None
    original_code = code  # Store original code for cleanup detection
    debug_mode_activated = False
    debug_mode_deactivated = False

    try:
      # Check if user explicitly requested debug injection
      if inject_debug.lower() == "true" and not has_debug_logging(code):
          print(f"[RUN] 🔍 ACTIVATING DEBUG MODE (user requested)")
          code = inject_debug_logging(code)
          debug_mode_activated = True
          print(f"[RUN] ✓ Diagnostic logging injected")
      
      # Generate user_id if not provided
      if not user_id:
          user_id = str(uuid.uuid4())
      
      # Create execution session record in database (if user exists)
      if user_id:
          user_exists = db.query(User).filter(User.id == user_id).first()
          if user_exists:
              execution_record = ExecutionSession(
                  id=session_id or str(uuid.uuid4()),
                  user_id=user_id,
                  script_name=user_prompt[:100] if user_prompt else "Untitled",
                  status="running",
                  started_at=datetime.utcnow()
              )
              db.add(execution_record)
              db.commit()
              print(f"[RUN] Created execution session record: {execution_record.id}")
      
      job_id = str(uuid.uuid4())
      job_dir = OUTPUTS_DIR / job_id
      in_dir = job_dir / "input"
      out_dir = job_dir / "result"
      code_dir = job_dir / "code"
      matplotlib_dir = out_dir / ".matplotlib"
      for d in (in_dir, out_dir, code_dir):
          d.mkdir(parents=True, exist_ok=True)
      
      # Mark this job as active (cleanup will skip it)
      active_marker_path = job_dir / ACTIVE_MARKER_NAME
      try:
          active_marker_path.write_text(str(time.time()), encoding="utf-8")
      except Exception as e:
          print(f"Warning: Failed to write active marker in {job_dir}: {e}")
      
      # Create matplotlib config directory with world-writable permissions
      # This must exist before the container runs, as the runner user may not have
      # permission to create directories in the mounted volume. We make it world-writable
      # so the container user can write to it regardless of UID/GID mismatch.
      matplotlib_dir.mkdir(parents=True, exist_ok=True)
      try:
          # Set permissions to 777 (world-writable) so container user can write
          # This is safe because it's inside the job-specific output directory
          os.chmod(str(matplotlib_dir), 0o777)
          print(f"Created matplotlib directory: {matplotlib_dir} with permissions 777")
      except Exception as e:
          print(f"Warning: Could not set permissions on {matplotlib_dir}: {e}")
          pass  # If chmod fails, continue anyway - directory exists, container will handle permissions
      
      # Verify directory exists and is writable
      if not matplotlib_dir.exists():
          print(f"ERROR: matplotlib_dir does not exist after creation: {matplotlib_dir}")
      elif not os.access(str(matplotlib_dir), os.W_OK):
          print(f"WARNING: matplotlib_dir is not writable: {matplotlib_dir}")

      # Write code
      main_py_path = code_dir / "main.py"
      print(f"[RUN] Writing code to: {main_py_path}")
      print(f"[RUN] Code to write length: {len(code)} characters")
      
      if not code or len(code) == 0:
          print(f"[RUN] ✗ ERROR: Code is empty!")
          return JSONResponse({"error": "No code provided. Code parameter is empty."}, status_code=400)
      
      main_py_path.write_text(code, encoding="utf-8")
      
      # Verify file was created and has content
      if not main_py_path.exists():
          print(f"[RUN] ✗ ERROR: File does not exist after write: {main_py_path}")
          return JSONResponse({"error": f"Failed to create code file at {main_py_path}"}, status_code=500)
      
      file_size = main_py_path.stat().st_size
      print(f"[RUN] ✓ Created code file: {main_py_path} ({file_size} bytes)")
      
      if file_size == 0:
          print(f"[RUN] ✗ ERROR: File is empty after write!")
          return JSONResponse({"error": "Code file is empty after write"}, status_code=500)

      # Prepare input image
      # Determine file extension from uploaded file or default to PNG
      if use_sample.lower() == "true":
        input_image_path = in_dir / "image.png"
        sample = (ASSETS_DIR / "sample.png")
        if not sample.exists():
          return JSONResponse({"error": "Sample image not found"}, status_code=404)
        shutil.copyfile(sample, input_image_path)
      elif image is None:
        return JSONResponse({"error": "No image provided. Please select an image from the library or upload a new one."}, status_code=400)
      else:
        # Preserve original file extension (supports PNG, JPG, TIFF, etc.)
        # skimage.imageio can read various formats including TIFF
        file_extension = pathlib.Path(image.filename).suffix.lower() if image.filename else ".png"
        # Normalize common extensions
        if file_extension in [".jpg", ".jpeg"]:
          file_extension = ".jpg"
        elif file_extension in [".tiff", ".tif"]:
          file_extension = ".tif"
        elif not file_extension:
          file_extension = ".png"
        
        input_image_path = in_dir / f"image{file_extension}"
        try:
          content = await image.read()
          
          # Apply EXIF orientation to pixel data, then strip EXIF
          # This ensures both browser and script see the same orientation
          from PIL import ImageOps
          import io as img_io
          
          # Load image from bytes
          img = Image.open(img_io.BytesIO(content))
          
          # Apply EXIF orientation if present (rotates the actual pixels)
          img = ImageOps.exif_transpose(img)
          
          # Save with orientation applied and EXIF stripped
          with open(input_image_path, "wb") as f:
            if file_extension == ".png":
              img.save(f, format="PNG")
            elif file_extension == ".jpg":
              img.save(f, format="JPEG", quality=95, exif=b'')
            elif file_extension in [".tif", ".tiff"]:
              img.save(f, format="TIFF")
            else:
              # For other formats, save as PNG
              img.save(f, format="PNG")
          
          # Convert TIFF to PNG for browser display (browsers can't display TIFF natively)
          # Keep the original TIFF for processing, but also create a PNG version for display
          if file_extension in [".tiff", ".tif"]:
            png_path = in_dir / "image.png"
            try:
              import numpy as np
              
              print(f"Converting TIFF to PNG: {input_image_path} -> {png_path}")
              img = Image.open(input_image_path)
              img_array = np.array(img)
              print(f"  Original: mode={img.mode}, size={img.size}, dtype={img_array.dtype}")
              
              # Normalize different bit depths to 8-bit (0-255)
              needs_normalization = False
              
              # Check for 16-bit, 32-bit, or float images
              if img_array.dtype in [np.uint16, np.uint32, np.int16, np.int32]:
                needs_normalization = True
              elif img_array.dtype in [np.float32, np.float64]:
                needs_normalization = True
              elif img_array.dtype == np.uint8:
                # Check if it's a low-range image (like labeled data)
                max_val = img_array.max()
                if max_val < 100 and max_val > 1:
                  needs_normalization = True
              
              if needs_normalization and img_array.size > 0:
                # Normalize to 0-255 range
                min_val = img_array.min()
                max_val = img_array.max()
                
                print(f"  Normalizing: dtype={img_array.dtype}, min={min_val}, max={max_val}")
                
                if max_val > min_val:
                  # Scale to 0-255
                  normalized = ((img_array - min_val) / (max_val - min_val) * 255).astype(np.uint8)
                  img = Image.fromarray(normalized)
                else:
                  # All same value - create blank image
                  img = Image.fromarray(np.zeros_like(img_array, dtype=np.uint8))
              
              # Convert to appropriate mode for PNG
              if img.mode not in ('RGB', 'RGBA', 'L'):
                if img.mode in ('LA',):
                  img = img.convert('RGBA')
                elif img.mode in ('P', 'I', 'F'):
                  img = img.convert('RGB')
                elif len(img.getbands()) == 1:
                  img = img.convert('L')  # Keep as grayscale
                else:
                  img = img.convert('RGB')
              
              img.save(png_path, "PNG")
              
              # Verify the PNG was created
              if png_path.exists():
                file_size = png_path.stat().st_size
                print(f"✓ Converted TIFF to PNG: {png_path} ({file_size} bytes)")
              else:
                print(f"⚠ Warning: PNG conversion completed but file not found at {png_path}")
            except Exception as e:
              print(f"⚠ Warning: Failed to convert TIFF to PNG: {e}")
              traceback.print_exc()
              # Continue anyway - the TIFF file is still available for processing
        except Exception as e:
          return JSONResponse({"error": f"Failed to save image: {str(e)}"}, status_code=500)

      # Execute script using detected runtime
      print(f"Using {_execution_runtime} runtime for script execution")
      
      # Define ProcResult class outside try block so it's available in except block
      class ProcResult:
          def __init__(self, returncode, stdout, stderr):
              self.returncode = returncode
              self.stdout = stdout
              self.stderr = stderr
      
      try:
          # Prepare request JSON
          request_data = {
              "user_id": user_id,
              "session_id": session_id,
              "user_prompt": user_prompt
          }
          request_json = json.dumps(request_data)
          
          # Write request.json to code_dir (needed for Docker runner, harmless for K8s)
          request_json_path = code_dir / "request.json"
          request_json_path.write_text(request_json, encoding="utf-8")
          
          # Run script using the detected runtime
          if _execution_runtime == "kubernetes":
              result = script_runner.run_script(
                  job_id=job_id,
                  script_content=code,
                  request_json=request_json,
                  input_path=str(in_dir),
                  output_path=str(out_dir),
                  timeout=60
              )
          else:
              # Docker runner uses file paths
              result = script_runner.run_script(
                  job_id=job_id,
                  script_path=str(main_py_path),
                  request_path=str(request_json_path),
                  input_path=str(in_dir),
                  output_path=str(out_dir),
                  timeout=60
              )
          
          # Check for timeout status
          if result.get("status") == "timeout":
              # Log timeout failure
              log_id = script_logger.log_failure(
                  code=code,
                  error_message="Execution timed out",
                  stderr="Script execution exceeded the 60 second timeout limit",
                  return_code=-1,
                  session_id=session_id,
                  user_prompt=user_prompt,
                  ai_model=ai_model,
                  image_filename=input_image_path.name if 'input_image_path' in locals() else None,
                  previous_attempt_id=previous_attempt_id,
                  error_category="timeout"
              )
              
              # Update execution record
              if execution_record:
                  execution_record.status = "timeout"
                  execution_record.error_message = "Script execution exceeded the 60 second timeout limit"
                  execution_record.completed_at = datetime.utcnow()
                  db.commit()
              
              return JSONResponse({
                  "error": "Execution timed out",
                  "message": "Script execution exceeded the 60 second timeout limit",
                  "timeout": 60,
                  "log_id": log_id,
                  "session_id": session_id or log_id
              }, status_code=504)
          
          proc = ProcResult(
              returncode=0 if result["status"] == "success" else 1,
              stdout=result.get("logs", ""),
              stderr=result.get("error", "") if result["status"] == "error" else ""
          )
      except Exception as e:
          print(f"Script execution failed ({_execution_runtime}): {e}")
          traceback.print_exc()
          proc = ProcResult(returncode=1, stdout="", stderr=str(e))

      if proc.returncode != 0:
          # Provide detailed error information for debugging
          error_details = {
              "error": "Execution failed",
              "return_code": proc.returncode,
              "stdout": proc.stdout if proc.stdout else "(no output)",
              "stderr": proc.stderr if proc.stderr else "(no error output)",
              "message": f"Script exited with code {proc.returncode}"
          }
          # If stderr is empty but stdout has content, include it in the error message
          if not proc.stderr and proc.stdout:
              error_details["message"] = f"Script exited with code {proc.returncode}. Check stdout for details."
          elif proc.stderr:
              error_details["message"] = f"Script exited with code {proc.returncode}. Error: {proc.stderr[:200]}"
          
          # Log failure
          log_id = script_logger.log_failure(
              code=code,
              error_message=error_details["message"],
              stderr=proc.stderr or "",
              return_code=proc.returncode,
              session_id=session_id,
              user_prompt=user_prompt,
              ai_model=ai_model,
              image_filename=input_image_path.name if 'input_image_path' in locals() else None,
              stdout=proc.stdout,
              previous_attempt_id=previous_attempt_id
          )
          
          # Update execution record
          if execution_record:
              execution_record.status = "error"
              execution_record.error_message = error_details["message"]
              execution_record.completed_at = datetime.utcnow()
              db.commit()
          
          error_details["log_id"] = log_id
          error_details["session_id"] = session_id or log_id
          
          return JSONResponse(error_details, status_code=400)

      # Collect all output files
      output_files = []
      if out_dir.exists():
          for file_path in out_dir.iterdir():
              if file_path.is_file():
                  file_info = {
                      "name": file_path.name,
                      "url": f"/outputs/{job_id}/result/{file_path.name}",
                      "type": file_path.suffix.lower() if file_path.suffix else "unknown"
                  }
                  output_files.append(file_info)
      
      # Check if any output files were produced
      if not output_files:
          return JSONResponse({"error": "No output files produced"}, status_code=400)
      
      # Check if result.png exists (for backward compatibility)
      result_path = out_dir / "result.png"
      result_url = f"/outputs/{job_id}/result/result.png" if result_path.exists() else None
      
      # Find original image URL (check for common image extensions)
      # For TIFF files, prefer PNG version if it exists (for browser display)
      # Otherwise check all formats
      original_url = None
      # First check if PNG exists (might be converted from TIFF)
      png_path = job_dir / "input" / "image.png"
      if png_path.exists():
        original_url = f"/outputs/{job_id}/input/image.png"
        print(f"✓ Found original image (PNG): {original_url}")
      else:
        # Check other formats
        for ext in [".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff"]:
          image_path = job_dir / "input" / f"image{ext}"
          if image_path.exists():
            original_url = f"/outputs/{job_id}/input/image{ext}"
            print(f"✓ Found original image ({ext}): {original_url}")
            break
      
      if not original_url:
        print(f"⚠ Warning: No original image found in {job_dir / 'input'}")
        # List what files actually exist for debugging
        if (job_dir / "input").exists():
          existing_files = list((job_dir / "input").iterdir())
          print(f"  Files in input directory: {[f.name for f in existing_files]}")

      # Check if we should remove debug logging (successful execution with debug code)
      cleaned_code = None
      if has_debug_logging(code):
          print(f"[RUN] ✓ SUCCESS with debug logging - preparing cleanup")
          cleaned_code = remove_debug_logging(code)
          debug_mode_deactivated = True
          print(f"[RUN] 🧹 Debug logging removed from code")
      
      # Log successful execution
      execution_time = time.time() - execution_start_time
      log_id = script_logger.log_success(
          code=code,
          output_files=[f["name"] for f in output_files],
          session_id=session_id,
          user_prompt=user_prompt,
          ai_model=ai_model,
          image_filename=input_image_path.name if 'input_image_path' in locals() else None,
          stdout=proc.stdout,
          execution_time=execution_time,
          previous_attempt_id=previous_attempt_id
      )
      
      # Update execution record
      if execution_record:
          execution_record.status = "success"
          execution_record.completed_at = datetime.utcnow()
          db.commit()
      
      response_data = {
          "job_id": job_id,
          "user_id": user_id,  # Return user_id so frontend can store it
          "original_url": original_url,
          "result_url": result_url,
          "output_files": output_files,
          "stdout": proc.stdout,
          "log_id": log_id,
          "session_id": session_id or log_id
      }
      
      # Add diagnostic mode information
      if debug_mode_activated:
          response_data["diagnostic_mode"] = {
              "activated": True,
              "message": "🔍 Diagnostic mode activated: Verbose logging added to help identify the issue."
          }
      
      if debug_mode_deactivated and cleaned_code:
          response_data["diagnostic_mode"] = {
              "deactivated": True,
              "message": "✓ Issue resolved! Diagnostic logging has been removed.",
              "cleaned_code": cleaned_code
          }
      
      return response_data
    except Exception as e:
      return JSONResponse(
          {"error": f"Failed to execute code: {str(e)}", "detail": traceback.format_exc()},
          status_code=500
      )
    finally:
      if active_marker_path is not None:
        try:
          active_marker_path.unlink(missing_ok=True)
        except Exception:
          pass

# Health check (optional)
@app.get("/health")
def health():
    return {"ok": True, "version": API_VERSION}

# Version endpoint
@app.get("/version")
def version():
    return {
        "version": API_VERSION,
        "status": "running"
    }

# Image Library Endpoints
def load_metadata():
    """Load image library metadata"""
    if LIBRARY_METADATA_FILE.exists():
        return json.loads(LIBRARY_METADATA_FILE.read_text(encoding="utf-8"))
    return {}

def save_metadata(metadata):
    """Save image library metadata"""
    LIBRARY_METADATA_FILE.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

# AI Chat Models
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: Optional[str] = None  # Optional context about current code/image
    image_url: Optional[str] = None  # Optional URL to the selected image
    model: Optional[str] = None  # Optional Gemini model override

# AI Chat endpoint
@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest):
    """
    Chat with Gemini AI for image processing assistance.
    Provides context-aware help with scikit-image, numpy, and matplotlib.
    Uses server-configured API key from GOOGLE_API_KEY environment variable.
    """
    # Check if API key is configured on server
    if not GOOGLE_API_KEY:
        return JSONResponse(
            {"error": "AI Assistant is not configured. GOOGLE_API_KEY environment variable is not set."},
            status_code=503
        )
    
    try:
        # Use server's API key (already configured at startup via genai.configure)
        # No need to reconfigure - genai is already configured with GOOGLE_API_KEY
        
        # Check if user is approving debug injection or asking to analyze debug output
        last_user_message = request.messages[-1] if request.messages else None
        inject_debug_approved = False
        analyze_debug_approved = False
        
        if last_user_message and last_user_message.role == "user":
            user_text = last_user_message.content.lower()
            # Detect affirmative responses to debug injection prompt
            if ("yes" in user_text and "debug" in user_text and "add" in user_text) or \
               ("add debugging" in user_text) or \
               ("inject debug" in user_text):
                inject_debug_approved = True
                print(f"[CHAT] User approved debug injection")
            # Detect request to analyze existing debug output
            elif ("yes" in user_text and ("analyze" in user_text or "fix" in user_text)) or \
                 ("analyze the debug" in user_text) or \
                 ("analyze and fix" in user_text):
                analyze_debug_approved = True
                print(f"[CHAT] User requested debug analysis and fix")
        
        # Initialize Gemini model (default is flash-lite unless overridden per request)
        
        # Try to get AI learning context from logs
        ai_learning_context = ""
        try:
            # Get recent failure patterns to help AI avoid common mistakes
            context_response = log_analyzer.generate_context_for_ai(max_examples=5)
            if context_response:
                ai_learning_context = f"\n\n## LEARNING FROM RECENT FAILURES\n{context_response}\n"
        except Exception as e:
            print(f"Warning: Could not load AI learning context: {e}")
        
        # Build system context for MAPS Script Bridge
        system_context = """You are an expert Python assistant for MAPS Script Bridge (MapsBridge) scripts.

🚨🚨🚨 CRITICAL: ALL SCRIPTS MUST USE MAPBRIDGE API 🚨🚨🚨

EVERY script will be run in MAPS eventually. Scripts must use MapsBridge API to:
✅ Read input data (via FromStdIn())
✅ Process images
✅ Output results (via MapsBridge methods)

This ensures scripts work in BOTH the Helper App (for testing) AND real MAPS (for production).

═══════════════════════════════════════════════════════════════
          🔴 CODE UPDATE vs EXPLANATION QUESTIONS 🔴
═══════════════════════════════════════════════════════════════

CRITICAL: Distinguish between two types of user requests:

1️⃣ CODE MODIFICATION REQUESTS (Include code blocks):
   - "Create a script that..."
   - "Update/modify/change the code to..."
   - "Fix this error..."
   - "Add feature X to the script..."
   - "Write a function that..."
   → For these: Provide code in ```python code blocks

2️⃣ EXPLANATION/UNDERSTANDING QUESTIONS (NO code blocks):
   - "Where in the script is X happening?"
   - "Explain how Y works..."
   - "What does function Z do?"
   - "How is X being calculated?"
   - "Show me where the file is saved"
   → For these: Answer in plain text, reference line numbers, explain concepts
   → DO NOT include code blocks - just explain the existing code

Rule: If the user is asking about UNDERSTANDING existing code, answer with text only.
If they want to MODIFY/CREATE code, then provide code blocks.

═══════════════════════════════════════════════════════════════
              AVAILABLE PYTHON LIBRARIES (EXECUTION SANDBOX)
═══════════════════════════════════════════════════════════════

{py_exec_libs}

═══════════════════════════════════════════════════════════════
     OPTIONAL LIBS (NOT INSTALLED) — RECOMMENDATIONS TO INSTALL
═══════════════════════════════════════════════════════════════

{py_exec_optional_libs}

═══════════════════════════════════════════════════════════════
              STEP 1: CHOOSE THE RIGHT REQUEST TYPE
═══════════════════════════════════════════════════════════════

ASK THE USER:
"Will this run on a Tile Set or Image Layer/Stitched Image?"

FOR TILE SETS (most common - 60%):
  → Use MapsBridge.ScriptTileSetRequest.FromStdIn()
  → User says: "tile set", "tiles", "individual tiles", "grid"

FOR IMAGE LAYERS/STITCHED IMAGES (20%):
  → Use MapsBridge.ScriptImageLayerRequest.FromStdIn()
  → User says: "image layer", "stitched image", "single image", "full image"

═══════════════════════════════════════════════════════════════
        RECOMMENDED: USE MAPSBRIDGE HELPER FUNCTIONS
═══════════════════════════════════════════════════════════════

MapsBridge includes convenience helpers to reduce boilerplate and prevent common mistakes:

- Resolve a single tile + its path: MapsBridge.ResolveSingleTileAndPath(request, channelIndex="0")
- Iterate tiles to process + paths: MapsBridge.IterTilesToProcessWithPath(request, channelIndex="0")
- Resolve prepared image path: MapsBridge.GetPreparedImagePath(request, channelIndex="0")
- Temp output folder: MapsBridge.GetTempOutputFolder(subfolder="MapsScriptOutputs")
- Parse parameters: MapsBridge.ParseScriptParameters(request.ScriptParameters)
- Common output pattern: MapsBridge.GetDefaultOutputTileSetAndChannel(...)

═══════════════════════════════════════════════════════════════
         PATTERN 1: TILE SET PROCESSING (Most Common)
═══════════════════════════════════════════════════════════════

```python
import os
import MapsBridge
from PIL import Image
import cv2

def main():
    # 1. Read tile set request
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    
    # 2. Get tile + TileInfo + input path (single-tile mode)
    # 🚨 CRITICAL: Channel index keys are strings: "0", "1", ...
    tile, tileInfo, input_path = MapsBridge.ResolveSingleTileAndPath(request, "0")
    
    MapsBridge.LogInfo(f"Processing tile [{tile.Column}, {tile.Row}]")
    
    # 4. Process image
    img = cv2.imread(input_path)
    result = cv2.GaussianBlur(img, (5, 5), 0)
    
    # 5. Save to temp folder
    output_folder = MapsBridge.GetTempOutputFolder("output")
    output_path = os.path.join(output_folder, "result.tif")
    cv2.imwrite(output_path, result)
    
    # 6. Create/get output tile set and ensure channel exists
    outputInfo = MapsBridge.GetDefaultOutputTileSetAndChannel(
        sourceTileSet=sourceTileSet,
        channelName="Processed",
        channelColor=(255, 0, 0),
        isAdditive=True,
        targetLayerGroupName="Outputs",
    )
    
    # 7. Send output
    MapsBridge.SendSingleTileOutput(
        tileRow=tileInfo.Row,
        tileColumn=tileInfo.Column,
        targetChannelName="Processed",
        imageFilePath=output_path,
        keepFile=True,
        targetTileSetGuid=outputInfo.TileSet.Guid,
    )
    
    MapsBridge.LogInfo("Processing complete!")

if __name__ == "__main__":
    main()
```

═══════════════════════════════════════════════════════════════
       PATTERN 2: IMAGE LAYER PROCESSING (Stitched Images)
═══════════════════════════════════════════════════════════════

```python
import os
import MapsBridge
import cv2

def main():
    # 1. Read image layer request
    request = MapsBridge.ScriptImageLayerRequest.FromStdIn()
    sourceLayer = request.SourceImageLayer
    
    # 2. Get input image
    # 🚨 CRITICAL: Use STRING key "0" not integer 0
    input_path = MapsBridge.GetPreparedImagePath(request, "0")
    
    MapsBridge.LogInfo(f"Processing layer: {sourceLayer.Name}")
    
    # 3. Process image
    img = cv2.imread(input_path)
    result = cv2.GaussianBlur(img, (5, 5), 0)
    
    # 4. Save to temp folder
    output_folder = MapsBridge.GetTempOutputFolder("output")
    output_path = os.path.join(output_folder, "result.png")
    cv2.imwrite(output_path, result)
    
    # 5. Create output image layer
    MapsBridge.CreateImageLayer(
        "Processed " + sourceLayer.Name,
        output_path,
        targetLayerGroupName="Outputs",
        keepFile=True
    )
    
    MapsBridge.LogInfo("Processing complete!")

if __name__ == "__main__":
    main()
```

═══════════════════════════════════════════════════════════════

        PATTERN 3: BATCH PROCESSING (Process All Tiles)
═══════════════════════════════════════════════════════════════

```python
import os
import MapsBridge

def main():
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    MapsBridge.LogInfo(f"Processing {len(request.TilesToProcess)} tiles")
    
    # Iterate through tiles requested by MAPS (or helper app)
    for tile, tileInfo, input_path in MapsBridge.IterTilesToProcessWithPath(request, "0"):
        MapsBridge.LogInfo(f"Processing tile [{tile.Column}, {tile.Row}] from {os.path.basename(input_path)}")
        # ... process each tile and send outputs via MapsBridge ...

if __name__ == "__main__":
    main()
```

═══════════════════════════════════════════════════════════════
          PATTERN 4: ANNOTATIONS (Sites & Areas of Interest)
═══════════════════════════════════════════════════════════════

```python
# Site of Interest (point marker - no size)
MapsBridge.CreateAnnotation(
    "Feature_001",
    stagePosition=(0.001, 0.002, 0),
    targetLayerGroupName="Annotations"
)

# Area of Interest (rectangular region - with size)
MapsBridge.CreateAnnotation(
    "ROI_001",
    stagePosition=(0.001, 0.002, 0),
    rotation=30,
    size=("10um", "5um"),
    notes="Important region",
    color=(0, 255, 0),
    isEllipse=False,
    targetLayerGroupName="Annotations"
)

# Create annotation from detected feature in tile (pixel to stage coords)
detectedPixelX = 200
detectedPixelY = 300
stageCoords = MapsBridge.TilePixelToStage(
    detectedPixelX, detectedPixelY,
    tile.Column, tile.Row, sourceTileSet
)
MapsBridge.CreateAnnotation(
    f"Detected_{tile.Column}_{tile.Row}",
    stagePosition=(stageCoords.X, stageCoords.Y, 0),
    targetLayerGroupName="Detected Features"
)
```

═══════════════════════════════════════════════════════════════
         PATTERN 5: CREATE TILE SET (New Acquisition - 20%)
═══════════════════════════════════════════════════════════════

```python
# Create new tile set for acquisition at detected location
MapsBridge.CreateTileSet(
    "New Acquisition",
    stagePosition=(tile.StagePosition.X, tile.StagePosition.Y, sourceTileSet.Rotation),
    totalSize=("30um", "20um"),
    tileHfw="5um",
    pixelSize="4nm",
    scheduleAcquisition=True,
    targetLayerGroupName="New Acquisitions"
)
```

═══════════════════════════════════════════════════════════════
                    🚨 CRITICAL RULES 🚨
═══════════════════════════════════════════════════════════════

✅ ALWAYS use STRING channel indices: "0", "1", "2" NOT integers 0, 1, 2
✅ ALWAYS use MapsBridge.FromStdIn() to read request
✅ Prefer MapsBridge.GetTempOutputFolder(...) for temporary outputs
✅ ALWAYS use MapsBridge output methods (CreateImageLayer, SendSingleTileOutput)
✅ ALWAYS use try/except for error handling around file I/O
✅ ALWAYS call MapsBridge.LogInfo/LogWarning/LogError for debugging
✅ ALWAYS create channels BEFORE sending tile output to them
✅ ALWAYS use keepFile=True to preserve temporary files

❌ NEVER use cv2.imread('/input/...')
❌ NEVER use cv2.imwrite('/output/...')
❌ NEVER use integer channel indices: ImageFileNames[0] ← WRONG!
❌ NEVER forget to create output tile set before creating channels
❌ NEVER hardcode image filenames - always use provided paths

═══════════════════════════════════════════════════════════════
                    AVAILABLE LIBRARIES
═══════════════════════════════════════════════════════════════

✅ MapsBridge - MAPS integration (REQUIRED)
✅ cv2 (OpenCV) - Image processing
✅ PIL/Pillow - Image I/O
✅ numpy - Arrays and math
✅ scipy - Scientific computing
✅ scikit-image (skimage) - Image processing
✅ matplotlib - Colormaps and visualization
✅ pandas - Data handling
✅ imageio - Image reading/writing

❌ mahotas - NOT installed
❌ tensorflow, torch, keras - NOT installed

═══════════════════════════════════════════════════════════════
                    POSITIONING & UNITS
═══════════════════════════════════════════════════════════════

Stage positions: tuples (x, y, rotation)
  - x, y: float in meters OR string with units
  - rotation: float in degrees OR string with units
  
Sizes: tuples (width, height)
  - width, height: float in meters OR string with units

Units strings: "30um", "5um", "4nm", "1mm", "30 deg"

Examples:
  stagePosition=(0.001, 0.002, 0)           # meters, meters, degrees
  stagePosition=("1mm", "2mm", "30 deg")    # string units
  size=("10um", "5um")                      # micrometers

═══════════════════════════════════════════════════════════════
                 CODE FORMATTING & INDENTATION
═══════════════════════════════════════════════════════════════

🚨 CRITICAL:
- ALWAYS use 4 spaces for indentation (NO TABS)
- NEVER mix indentation levels
- EVERY line must be properly indented
- Double-check ALL code blocks before sending

Common error: "IndentationError: unindent does not match any outer indentation level"
FIX: Ensure all code at same level uses exactly the same indentation

═══════════════════════════════════════════════════════════════
               UNDERSTANDING MAPS DATA TYPES
═══════════════════════════════════════════════════════════════

MAPS has TWO data types for script processing:

1. TILE SET (Collection of tiles) - 60% of use cases:
   - Multiple image tiles in a grid (e.g., 5x5 = 25 tiles)
   - Each tile: row/column indices (1-based)
   - Large area imaging (microscope acquires many tiles)
   - Process tile-by-tile OR all tiles together
   - Example: 10mm × 10mm sample = 100 individual 1mm tiles
   - API: ScriptTileSetRequest

2. IMAGE LAYER / STITCHED IMAGE - 20% of use cases:
   - SINGLE large image (stitched from tiles)
   - No tile indices - one complete image
   - Process the full assembled result
   - Example: 100 tiles stitched → one 10mm × 10mm image
   - API: ScriptImageLayerRequest
   - User terminology: "image layer" OR "stitched image"

🚨 IMPORTANT: Ask Clarifying Questions!
If unclear, ASK: "Will this run on a Tile Set or Image Layer/Stitched Image?"

- "tile set", "tiles", "grid" → TileSetRequest
- "image layer", "stitched", "single image" → ImageLayerRequest

═══════════════════════════════════════════════════════════════
                    HELPER APP vs REAL MAPS
═══════════════════════════════════════════════════════════════

The Helper App SIMULATES the MAPS environment for testing:

IN HELPER APP (testing):
✅ Images in /input/ directory
✅ MapsBridge.FromStdIn() scans /input folder (simulated)
✅ MapsBridge functions are SIMULATED (stubs, logging)
✅ Outputs copied to /output/ for preview
✅ Annotations logged (not visually created)

IN REAL MAPS (production):
✅ Images from tile set data folder
✅ MapsBridge.FromStdIn() reads JSON from stdin (real data)
✅ MapsBridge functions create real MAPS objects
✅ Outputs create actual channels, layers, annotations
✅ Annotations appear in MAPS project

SAME SCRIPT works in BOTH! Test in Helper → Deploy to MAPS

═══════════════════════════════════════════════════════════════
                 OTHER MAPBRIDGE FUNCTIONS
═══════════════════════════════════════════════════════════════

Store Files:
```python
MapsBridge.StoreFile(
    "C:\\analysis\\report.pdf",
    overwrite=True,
    keepFile=True,
    targetLayerGuid=outputTileSet.Guid
)
```

Append Notes:
```python
MapsBridge.AppendNotes(
    f"Processed tile [{tile.Column}, {tile.Row}]\\n",
    targetLayerGuid=outputTileSet.Guid
)
```

═══════════════════════════════════════════════════════════════
               CODE UPDATE GUIDELINES
═══════════════════════════════════════════════════════════════

When you DO update code:
✅ MUST provide COMPLETE, FULLY FUNCTIONAL script
✅ Include all imports, error handling, complete logic
✅ Script ready to run immediately
✅ Include if __name__ == "__main__": main()

⚠️ NEVER LIE ABOUT CODE UPDATES:
❌ DON'T say "✅ Code updated" without including code block
❌ DON'T claim update is done when asking for confirmation
✅ ONLY claim update when code block is in SAME response

═══════════════════════════════════════════════════════════════
              COMPLETE WORKING EXAMPLE SCRIPT
═══════════════════════════════════════════════════════════════

```python
import os
import tempfile
import MapsBridge
import cv2

def main():
    # Get tile to process (single tile mode)
    tileInfo = request.TilesToProcess[0]
    tile = next((t for t in sourceTileSet.Tiles 
                 if t.Column == tileInfo.Column and t.Row == tileInfo.Row), None)
    
    # 🚨 CRITICAL: Use STRING key "0" not integer 0
    tileFilename = tile.ImageFileNames["0"]
    input_path = os.path.join(sourceTileSet.DataFolderPath, tileFilename)
    
    MapsBridge.LogInfo(f"Processing tile [{tile.Column}, {tile.Row}]")
    
    # Process image
    img = cv2.imread(input_path)
    result = cv2.GaussianBlur(img, (5, 5), 0)
    
    # Save to temp folder
    output_folder = os.path.join(tempfile.gettempdir(), "output")
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, "result.tif")
    cv2.imwrite(output_path, result)
    
    # Create output tile set
    outputInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Results for " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    
    # Create channel
    MapsBridge.CreateChannel("Processed", (255,0,0), True, outputInfo.TileSet.Guid)
    
    # Send output
    MapsBridge.SendSingleTileOutput(
        tile.Row, tile.Column, "Processed",
        output_path, True, outputInfo.TileSet.Guid
    )
    
    MapsBridge.LogInfo("Processing complete!")

if __name__ == "__main__":
    main()
```

═══════════════════════════════════════════════════════════════
                    QUICK REFERENCE
═══════════════════════════════════════════════════════════════

TILE SET vs IMAGE LAYER:
- TileSet: Individual tiles, use request.TilesToProcess[0] → tile.ImageFileNames["0"]
- ImageLayer: Stitched image, use request.PreparedImages.get("0")

OUTPUT METHODS:
- TileSet output: GetOrCreateOutputTileSet → CreateChannel → SendSingleTileOutput
- ImageLayer output: CreateImageLayer

CRITICAL:
✅ Use STRING keys: ImageFileNames["0"], PreparedImages.get("0")
✅ Save to tempfile.gettempdir()
✅ Use keepFile=True
✅ Call LogInfo/LogWarning/LogError for debugging

═══════════════════════════════════════════════════════════════
                    AI LEARNING FROM LOGS
═══════════════════════════════════════════════════════════════

This system tracks all script executions to improve code generation.
Learns from:
- Common error patterns (imports, attributes, data access)
- Library-specific issues
- MapsBridge API misuse
- Successful fix strategies

Your goal: Generate scripts that work on the first try using these proven patterns!"""
        
        # Inject runtime library lists into system context (avoid str.format because the prompt contains many `{}` braces)
        try:
            system_context = system_context.replace(
                "{py_exec_libs}",
                _get_py_exec_requirements_summary(),
            ).replace(
                "{py_exec_optional_libs}",
                _get_optional_library_recommendations_summary(),
            )
        except Exception:
            # If injection fails for any reason, keep system_context as-is
            pass

        # Add AI learning context (use string concatenation to avoid .format() issues with curly braces in examples)
        if ai_learning_context:
            system_context = system_context + "\n\n" + ai_learning_context
        
        # Determine requested model (default to flash-lite)
        requested_model = (request.model or "gemini-2.5-flash-lite").strip()
        # Basic validation
        allowed_models = {"gemini-2.5-flash-lite", "gemini-2.5-pro"}
        if requested_model not in allowed_models:
            requested_model = "gemini-2.5-flash-lite"
        
        # Build conversation history
        conversation = []
        for msg in request.messages[-10:]:  # Last 10 messages for context
            role = "user" if msg.role == "user" else "model"
            conversation.append({"role": role, "parts": [msg.content]})
        
        # Add system context to the first message
        if conversation:
            conversation[0]["parts"].insert(0, system_context)
        
        
        # Add AI learning context (use string concatenation to avoid .format() issues with curly braces in examples)
        if ai_learning_context:
            system_context = system_context + "\n\n" + ai_learning_context
        
        # Determine requested model (default to flash-lite)
        requested_model = (request.model or "gemini-2.5-flash-lite").strip()
        # Basic validation
        allowed_models = {"gemini-2.5-flash-lite", "gemini-2.5-pro"}
        if requested_model not in allowed_models:
            requested_model = "gemini-2.5-flash-lite"

        # Build conversation history
        conversation = []
        for msg in request.messages[-10:]:  # Last 10 messages for context
            role = "user" if msg.role == "user" else "model"
            conversation.append({"role": role, "parts": [msg.content]})
        
        # Add system context to the first message
        if conversation and conversation[0]["role"] == "user":
            conversation[0]["parts"][0] = f"{system_context}\n\nUser question: {conversation[0]['parts'][0]}"
        
        # Add current context if provided
        if request.context:
            # Check if context contains error information
            if "Last execution error" in request.context or "STDERR" in request.context:
                if analyze_debug_approved:
                    # User wants to analyze debug output and fix the issue
                    conversation[-1]["parts"][0] = f"{conversation[-1]['parts'][0]}\n\n{request.context}\n\nThe script has verbose debugging enabled and is still failing. Please carefully analyze the [AUTO-DEBUG] output in the error logs to identify the root cause, then provide a COMPLETE, FULLY FUNCTIONAL corrected script with the debug statements removed."
                else:
                    conversation[-1]["parts"][0] = f"{conversation[-1]['parts'][0]}\n\n{request.context}\n\nPlease help fix this error and provide a COMPLETE, FULLY FUNCTIONAL corrected script that reads from /input/ and saves to /output/."
            else:
                conversation[-1]["parts"][0] = f"{conversation[-1]['parts'][0]}\n\nCurrent context: {request.context}\n\n🔴 IMPORTANT: If the user is asking a QUESTION about the code (e.g., 'where is X', 'explain how Y works'), answer in plain text WITHOUT code blocks. Only provide code blocks if they explicitly ask to CREATE, MODIFY, UPDATE, or FIX code."
        
        # Handle debug injection approval - return special response with instruction
        if inject_debug_approved:
            print(f"[CHAT] Returning debug injection approval response")
            # Get current code to inject debug into
            current_code = ""
            if request.context and "Current code:" in request.context:
                # Extract code from context
                code_start = request.context.find("Current code:") + len("Current code:")
                code_section = request.context[code_start:].strip()
                # Take first part (before any error messages)
                if "\n\nLast execution error" in code_section:
                    current_code = code_section[:code_section.find("\n\nLast execution error")].strip()
                else:
                    current_code = code_section
            
            # Inject debug logging
            if current_code and not has_debug_logging(current_code):
                debug_code = inject_debug_logging(current_code)
                return {
                    "response": "✅ Debug logging injected! I've added diagnostic print statements to help identify the issue. Click 'Run' to execute with verbose debugging enabled.",
                    "suggested_code": debug_code,
                    "success": True
                }
            else:
                return {
                    "response": "⚠️ Debug logging could not be injected (code may already have debug statements or is not available). Please try running the script again.",
                    "success": True
                }
        
        # If user requested debug analysis, continue to AI (don't return early)
        # The AI will analyze the debug output and propose a fix
        
        # Handle image if provided
        image_parts = []
        if request.image_url:
            try:
                # Resolve the image path from the URL
                # URLs are like /outputs/job_id/result/image.png or /library/images/filename
                image_path_str = request.image_url.lstrip('/')
                
                # Handle outputs path: outputs/job_id/result/image.png -> outputs/job_id/result/image.png
                # Handle library path: library/images/filename -> library/images/filename
                if image_path_str.startswith('outputs/'):
                    image_path = OUTPUTS_DIR / image_path_str.replace('outputs/', '')
                elif image_path_str.startswith('uploads/images/'):
                    image_path = USER_UPLOADS_DIR / image_path_str.replace('uploads/images/', '')
                elif image_path_str.startswith('library/images/'):
                    image_path = LIBRARY_IMAGES_DIR / image_path_str.replace('library/images/', '')
                else:
                    # Try relative to BASE_DIR
                    image_path = BASE_DIR / image_path_str
                
                if image_path.exists() and image_path.is_file():
                    # Load image using PIL
                    img = Image.open(image_path)
                    image_parts.append(img)
                    # Add image context to the message
                    conversation[-1]["parts"][0] = f"{conversation[-1]['parts'][0]}\n\n[User has selected an image: {image_path.name}]"
            except Exception as e:
                print(f"Warning: Failed to load image {request.image_url}: {e}")
                # Continue without image if loading fails
        
        # Start chat and get response
        model = genai.GenerativeModel(requested_model)
        chat = model.start_chat(history=conversation[:-1] if len(conversation) > 1 else [])
        
        # Prepare message parts (text + image if available)
        message_parts = [conversation[-1]["parts"][0]]
        if image_parts:
            message_parts.extend(image_parts)
        
        try:
            response = chat.send_message(message_parts)
            response_text = response.text
            
            # Check if response is empty or None
            if not response_text:
                raise ValueError("AI returned an empty response")
        except Exception as api_error:
            # Handle specific Gemini API errors
            error_msg = str(api_error)
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                raise Exception("API rate limit exceeded. Please try again in a moment.")
            elif "401" in error_msg or "403" in error_msg or "invalid" in error_msg.lower() and "api" in error_msg.lower():
                raise Exception("Invalid API key. Please check your GOOGLE_API_KEY configuration.")
            elif "timeout" in error_msg.lower():
                raise Exception("Request timed out. The AI service may be slow. Please try again.")
            elif "safety" in error_msg.lower() or "blocked" in error_msg.lower():
                raise Exception("Request was blocked by content safety filters. Please rephrase your question.")
            else:
                # Re-raise with more context
                raise Exception(f"AI API error: {error_msg}")
        
        # Check if AI is asking about data type and add quick replies
        quick_replies = None
        if "Tile Set" in response_text and "Image Layer" in response_text and ("?" in response_text or "choose" in response_text.lower() or "clarify" in response_text.lower()):
            quick_replies = [
                {
                    "text": "Tile Set",
                    "icon": "grid_view",
                    "description": "Individual tiles"
                },
                {
                    "text": "Image Layer / Stitched Image", 
                    "icon": "image",
                    "description": "Full assembled image"
                },
                {
                    "text": "Universal (Both)",
                    "icon": "auto_awesome",
                    "description": "Works with both types"
                }
            ]
        
        # Try to extract code blocks from the response
        # Improved regex to handle various formats:
        # - ```python\ncode```
        # - ```pythoncode``` (no newline)
        # - ```\ncode```
        # - ```code``` (no newline, no language)
        import re
        
        # Try multiple patterns to catch different formats
        code_blocks = []
        
        # Pattern 1: Standard markdown code blocks with language
        pattern1 = r'```(?:python|py)?\s*\n(.*?)```'
        matches1 = re.findall(pattern1, response_text, re.DOTALL)
        code_blocks.extend(matches1)
        
        # Pattern 2: Code blocks without newline after language
        pattern2 = r'```(?:python|py)\s*(.*?)```'
        matches2 = re.findall(pattern2, response_text, re.DOTALL)
        code_blocks.extend(matches2)
        
        # Pattern 3: Generic code blocks (no language specified)
        pattern3 = r'```\s*\n(.*?)```'
        matches3 = re.findall(pattern3, response_text, re.DOTALL)
        code_blocks.extend(matches3)
        
        # Pattern 4: Code blocks without newline
        pattern4 = r'```\s*(.*?)```'
        matches4 = re.findall(pattern4, response_text, re.DOTALL)
        code_blocks.extend(matches4)
        
        # Remove duplicates and empty blocks
        code_blocks = [cb.strip() for cb in code_blocks if cb.strip()]
        code_blocks = list(dict.fromkeys(code_blocks))  # Remove duplicates while preserving order
        
        # Clean up code blocks - remove any leading language identifiers that might have been captured
        cleaned_blocks = []
        for block in code_blocks:
            # Remove leading "python" or "py" if they appear as standalone words at the start
            cleaned = block.strip()
            # Check if it starts with "python" or "py" followed by whitespace or newline
            if cleaned.lower().startswith('python'):
                # Check if it's just "python" or "python\n" or "python "
                if len(cleaned) == 6 or (len(cleaned) > 6 and cleaned[6] in ['\n', ' ', '\r', '\t']):
                    cleaned = cleaned[6:].lstrip()
            elif cleaned.lower().startswith('py'):
                # Check if it's just "py" or "py\n" or "py "
                if len(cleaned) == 2 or (len(cleaned) > 2 and cleaned[2] in ['\n', ' ', '\r', '\t']):
                    cleaned = cleaned[2:].lstrip()
            cleaned_blocks.append(cleaned)
        
        code_blocks = cleaned_blocks
        
        # If there's a code block, extract it as suggested code update
        suggested_code = None
        if code_blocks:
            # Use the longest code block (most likely to be the full code)
            suggested_code = max(code_blocks, key=len).strip()
            
            print(f"📝 Found code block: {len(suggested_code)} chars")
            print(f"  First 100 chars: {suggested_code[:100]}")
            
            # Additional cleanup: remove any leading "python" or "py" that might still be there
            if suggested_code.lower().startswith('python'):
                if len(suggested_code) == 6 or (len(suggested_code) > 6 and suggested_code[6] in ['\n', ' ', '\r', '\t']):
                    suggested_code = suggested_code[6:].lstrip()
                    print(f"  Removed leading 'python'")
            elif suggested_code.lower().startswith('py'):
                if len(suggested_code) == 2 or (len(suggested_code) > 2 and suggested_code[2] in ['\n', ' ', '\r', '\t']):
                    suggested_code = suggested_code[2:].lstrip()
                    print(f"  Removed leading 'py'")
            
            # Final verification: ensure first line doesn't start with "python" or "py"
            lines = suggested_code.split('\n')
            if lines and lines[0].strip().lower() in ['python', 'py']:
                suggested_code = '\n'.join(lines[1:]).strip()
                print(f"  Removed leading 'python'/'py' from first line")
                lines = suggested_code.split('\n')
            
            # Simple validation: reject only if extremely short or obviously not code
            # Be permissive - if AI included it in a code block, it's probably intentional
            is_too_short = len(suggested_code) < 10
            is_empty_or_whitespace = not suggested_code or suggested_code.isspace()
            
            if is_empty_or_whitespace or is_too_short:
                # Only reject if it's clearly not code
                print(f"⚠ Rejecting code block: too short ({len(suggested_code)} chars) or empty")
                suggested_code = None
            else:
                # Accept the code! Remove code blocks from response text for cleaner display
                print(f"✅ Accepting code block: {len(suggested_code)} chars")
                for pattern in [pattern1, pattern2, pattern3, pattern4]:
                    response_text = re.sub(pattern, '', response_text, flags=re.DOTALL)
                response_text = response_text.strip()
                print(f"  Removed code blocks from response text")
                print(f"  First line: {lines[0][:80] if lines and lines[0] else 'empty'}")
        
        # Add timestamp comment at the top of suggested_code if it exists
        if suggested_code:
            # Get local time (handles timezone conversion from UTC if needed)
            now = datetime.now()
            timestamp = now.strftime("%H:%M:%S")
            timestamp_comment = f"# Last Code Update - {timestamp}\n"
            suggested_code = timestamp_comment + suggested_code
        else:
            # If no code was extracted, rewrite any false claims from the response text
            # This prevents the AI from saying "I've updated..." when it didn't send code
            original_text = response_text
            
            # Pattern 1: Replace "I've updated X" with "I can update X"
            response_text = re.sub(
                r"I've updated (the )?(`[^`]+`|[\w_]+)",
                r"I can update \1\2",
                response_text,
                flags=re.IGNORECASE
            )
            
            # Pattern 2: Replace "I have updated X" with "I can update X"
            response_text = re.sub(
                r"I have updated (the )?(`[^`]+`|[\w_]+)",
                r"I can update \1\2",
                response_text,
                flags=re.IGNORECASE
            )
            
            # Pattern 3: Replace "I will update X" (without question) with "Would you like me to update X?"
            if "would you like" not in response_text.lower() and "?" not in response_text:
                response_text = re.sub(
                    r"I will update (the )?(`[^`]+`|[\w_]+[^.]*)\.",
                    r"Would you like me to update \1\2?",
                    response_text,
                    flags=re.IGNORECASE
                )
                response_text = re.sub(
                    r"I'll update (the )?(`[^`]+`|[\w_]+[^.]*)\.",
                    r"Would you like me to update \1\2?",
                    response_text,
                    flags=re.IGNORECASE
                )
            
            # Pattern 4: Remove explicit success claims
            false_claims = [
                "✅ Code has been updated!",
                "✅ Code has been updated in the editor!",
                "✅ Code updated!",
                "✅ Updated!",
                "Code has been updated!",
                "Code has been updated in the editor!",
                "The code has been updated",
                "Script has been updated",
                "✅",  # Remove any remaining checkmarks
            ]
            for claim in false_claims:
                response_text = response_text.replace(claim, "")
            
            # Clean up any double newlines or trailing whitespace from removals
            response_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', response_text).strip()
            
            if original_text != response_text:
                print(f"🧹 Rewrote false claims in response:")
                print(f"   Before: {original_text[:100]}")
                print(f"   After:  {response_text[:100]}")
        
        result = {
            "response": response_text,
            "suggested_code": suggested_code,  # Code to update in editor
            "quick_replies": quick_replies,  # Quick reply buttons
            "success": True
        }
        
        # Log for debugging
        if suggested_code:
            print(f"✓ Extracted code block ({len(suggested_code)} chars)")
            print(f"  First line: {suggested_code.split(chr(10))[0][:80]}")
        else:
            print(f"⚠ No code block extracted from response ({len(response_text)} chars)")
            print(f"  Response preview: {response_text[:300]}")
            # Check if there are any backticks in the response
            if '```' in response_text:
                print(f"  ⚠️ Found backticks but no valid code block pattern matched!")
                print(f"  Backtick count: {response_text.count('```')}")
            else:
                print(f"  ℹ️ No code blocks in response (text-only response)")
            # Log a sample of the response to help debug
            if len(response_text) > 0:
                print(f"  Response sample: {response_text[:200]}")
        
        return result
        
    except Exception as e:
        import traceback
        error_str = str(e)
        error_type = type(e).__name__
        
        error_details = {
            "error": f"AI request failed: {error_str}",
            "error_type": error_type,
            "success": False,
            "full_error": error_str  # Always include full error message
        }
        
        # Add more details for common error types
        if hasattr(e, 'prompt_feedback'):
            error_details["prompt_feedback"] = str(e.prompt_feedback)
        if hasattr(e, 'response'):
            error_details["api_response"] = str(e.response) if e.response else None
        
        # Check for specific Gemini API error attributes
        if hasattr(e, 'args') and e.args:
            error_details["error_args"] = str(e.args)
        
        # Always include a simplified traceback (last few lines)
        tb_lines = traceback.format_exc().split('\n')
        # Get the last meaningful lines (skip empty lines at end)
        meaningful_lines = [line for line in tb_lines if line.strip()][-5:]
        error_details["error_traceback"] = '\n'.join(meaningful_lines)
        
        # Include full traceback in development
        import os
        if os.getenv("DEBUG", "false").lower() == "true":
            error_details["traceback"] = traceback.format_exc()
        
        # Log full error for debugging
        print(f"AI Chat Error: {error_type}: {error_str}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        
        return JSONResponse(
            error_details,
            status_code=500
        )

@app.post("/library/upload")
async def upload_library_image(
    image: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    image_type: str = Form(...),  # SEM, SDB, TEM, or OPTICAL
    user_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload an image to the library with metadata (stored in database)"""
    if image_type not in ["SEM", "SDB", "TEM", "OPTICAL"]:
        return JSONResponse({"error": "Image type must be SEM, SDB, TEM, or OPTICAL"}, status_code=400)
    
    if not user_id:
        return JSONResponse({"error": "user_id is required"}, status_code=400)
    
    # Verify user exists
    print(f"[Upload] Received user_id: '{user_id}' (type: {type(user_id).__name__})")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        all_users = db.query(User).all()
        print(f"[Upload] User not found. Available users: {[f'{u.name} ({u.id})' for u in all_users]}")
        return JSONResponse({"error": "User not found"}, status_code=404)
    print(f"[Upload] User found: {user.name} (ID: {user.id})")
    
    # Generate unique ID
    image_id = str(uuid.uuid4())
    
    # Save image file to user uploads directory (PVC-backed, persistent)
    file_extension = pathlib.Path(image.filename).suffix.lower() or ".png"
    image_filename = f"{image_id}{file_extension}"
    image_path = USER_UPLOADS_DIR / image_filename
    
    content = await image.read()
    with open(image_path, "wb") as f:
        f.write(content)
    
    # Get image dimensions
    width, height, file_size = None, None, None
    try:
        from PIL import Image as PILImage
        with PILImage.open(image_path) as img:
            width, height = img.size
        file_size = image_path.stat().st_size
    except:
        pass
    
    # Create user image in database
    new_image = UserImage(
        id=image_id,
        user_id=user_id,
        name=name,
        filename=image_filename,
        description=description,
        image_type=image_type,
        width=width,
        height=height,
        file_size=file_size
    )
    db.add(new_image)
    db.commit()
    
    return {
        "id": image_id,
        "user_id": user_id,
        "name": name,
        "description": description,
        "type": image_type,
        "url": f"/uploads/images/{image_filename}",
        "width": width,
        "height": height,
        "file_size": file_size
    }

@app.get("/library/images")
def list_library_images(user_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List images in the library from database
    
    Returns:
    - If user_id is None: all library images only
    - If user_id is provided: library images + user's uploaded images
    """
    images = []
    
    # Always include shared library images
    library_images = db.query(LibraryImage).all()
    for img in library_images:
        images.append(img.to_dict())
    
    # If user_id provided, add their uploaded images
    if user_id:
        user_images = db.query(UserImage).filter(UserImage.user_id == user_id).all()
        for img in user_images:
            images.append(img.to_dict())
    
    # Sort by name
    images.sort(key=lambda x: x["name"].lower())
    return {"images": images}

def _serve_image_file(image_path: pathlib.Path, filename: str, raw: bool = False):
    """Shared helper to serve an image file, with TIFF-to-PNG conversion for browsers.
    
    Args:
        image_path: Full filesystem path to the image file
        filename: The filename (used for Content-Disposition and extension detection)
        raw: If True, serve raw TIFF files without conversion (for script execution)
    """
    # Check if it's a TIFF file and raw=False - convert to PNG for browser display
    file_ext = pathlib.Path(filename).suffix.lower()
    if file_ext in ['.tiff', '.tif'] and not raw:
        try:
            import numpy as np
            
            img = Image.open(image_path)
            img_array = np.array(img)
            
            needs_normalization = False
            if img_array.dtype in [np.uint16, np.uint32, np.int16, np.int32]:
                needs_normalization = True
            elif img_array.dtype in [np.float32, np.float64]:
                needs_normalization = True
            elif img_array.dtype == np.uint8:
                max_val = img_array.max()
                if max_val < 100 and max_val > 1:
                    needs_normalization = True
            
            if needs_normalization and img_array.size > 0:
                min_val = img_array.min()
                max_val = img_array.max()
                print(f"Normalizing TIFF: dtype={img_array.dtype}, min={min_val}, max={max_val}")
                if max_val > min_val:
                    normalized = ((img_array - min_val) / (max_val - min_val) * 255).astype(np.uint8)
                    img = Image.fromarray(normalized)
                else:
                    img = Image.fromarray(np.zeros_like(img_array, dtype=np.uint8))
            
            if img.mode not in ('RGB', 'RGBA', 'L'):
                if img.mode in ('LA',):
                    img = img.convert('RGBA')
                elif img.mode in ('P', 'I', 'F'):
                    img = img.convert('RGB')
                elif len(img.getbands()) == 1:
                    img = img.convert('L')
                else:
                    img = img.convert('RGB')
            
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG', optimize=True)
            img_buffer.seek(0)
            
            return StreamingResponse(
                img_buffer,
                media_type="image/png",
                headers={
                    "Content-Disposition": f"inline; filename={filename}",
                    "Cache-Control": "public, max-age=3600"
                }
            )
        except Exception as e:
            print(f"⚠ Failed to convert TIFF for display: {e}")
            import traceback
            traceback.print_exc()
            return FileResponse(image_path)
    
    # For other formats or raw=True, serve directly
    return FileResponse(image_path)

@app.get("/uploads/images/{filename:path}")
def get_uploaded_image(filename: str, raw: bool = False):
    """Get a user-uploaded image file by filename (from PVC-backed storage)
    
    Args:
        filename: The image filename
        raw: If True, serve raw TIFF files without conversion (for script execution)
    """
    image_path = USER_UPLOADS_DIR / filename
    if not image_path.exists():
        return JSONResponse({"error": "Uploaded image file not found"}, status_code=404)
    return _serve_image_file(image_path, filename, raw)

@app.get("/library/images/{filename:path}")
def get_library_image(filename: str, raw: bool = False):
    """Get a specific library image file by filename
    
    Args:
        filename: The image filename
        raw: If True, serve raw TIFF files without conversion (for script execution)
    """
    image_path = LIBRARY_IMAGES_DIR / filename
    # Also check user uploads directory for backward compatibility
    if not image_path.exists():
        image_path = USER_UPLOADS_DIR / filename
    if not image_path.exists():
        return JSONResponse({"error": "Image file not found"}, status_code=404)
    
    return _serve_image_file(image_path, filename, raw)

@app.delete("/library/images/{image_id}")
def delete_library_image(
    image_id: str, 
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Delete an image from the library (only user's own images, not shared library images)"""
    # Try to find the image as a user image first
    user_image = db.query(UserImage).filter(UserImage.id == image_id).first()
    
    if user_image:
        # Verify user_id matches (security check)
        if user_id and user_image.user_id != user_id:
            return JSONResponse(
                {"error": "Unauthorized: Image belongs to a different user"},
                status_code=403
            )
        
        # Delete image file (check user uploads first, then library dir for backward compat)
        image_path = USER_UPLOADS_DIR / user_image.filename
        if not image_path.exists():
            image_path = LIBRARY_IMAGES_DIR / user_image.filename
        if image_path.exists():
            image_path.unlink()
        
        # Delete from database
        db.delete(user_image)
        db.commit()
        
        return {"success": True}
    
    # Check if it's a library image (which cannot be deleted)
    library_image = db.query(LibraryImage).filter(LibraryImage.id == image_id).first()
    if library_image:
        return JSONResponse(
            {"error": "Cannot delete shared library images"},
            status_code=403
        )
    
    # Image not found
    return JSONResponse({"error": "Image not found"}, status_code=404)

# ============================================================================
# User Accounts API
# ============================================================================

def load_users():
    """Load user accounts"""
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_users(users):
    """Save user accounts"""
    try:
        # Ensure parent directory exists
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Error saving users: {e}")
        import traceback
        traceback.print_exc()
        raise

class CreateUserRequest(BaseModel):
    name: str

def get_default_scripts(db: Session = None):
    """Return the default/library scripts from database"""
    if db is None:
        from backend.database import get_db_session
        with get_db_session() as db:
            scripts = db.query(LibraryScript).order_by(LibraryScript.name).all()
            return [script.to_dict() for script in scripts]
    else:
        scripts = db.query(LibraryScript).order_by(LibraryScript.name).all()
        return [script.to_dict() for script in scripts]
    """Return the default scripts that all new users should have"""
    return [
        {
            "name": "Thermal Colormap",
            "description": "Applies a thermal/hot false-color visualization (black → red → yellow → white) using multi-channel output.",
            "code": """# MAPS Script Bridge Example - False Color (Multi-Channel)
# Outputs separate R/G/B intensity channels for thermal colormap

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np

def get_thermal_channels(gray_array):
    \"\"\"
    Generate thermal colormap as separate intensity channels.
    Black -> Red -> Yellow -> White
    Returns: (red_intensity, green_intensity, blue_intensity) as uint8 arrays
    \"\"\"
    normalized = gray_array.astype(np.float32) / 255.0
    
    # Each channel is a grayscale intensity map
    r = np.clip(3.0 * normalized, 0, 1)
    g = np.clip(3.0 * normalized - 1.0, 0, 1)
    b = np.clip(3.0 * normalized - 2.0, 0, 1)
    
    return (
        (r * 255).astype(np.uint8),
        (g * 255).astype(np.uint8),
        (b * 255).astype(np.uint8)
    )

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Load the input image
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    img = Image.open(input_path).convert("L")
    gray_array = np.array(img)
    
    MapsBridge.LogInfo(f"Loaded: {input_filename} ({img.size[0]}x{img.size[1]})")
    
    # 3. Generate thermal colormap channels
    red_intensity, green_intensity, blue_intensity = get_thermal_channels(gray_array)
    
    # 4. Save each channel to temp folder (use PNG for compatibility)
    output_folder = os.path.join(tempfile.gettempdir(), "thermal_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    
    red_path = os.path.join(output_folder, f"{base}_red.png")
    green_path = os.path.join(output_folder, f"{base}_green.png")
    blue_path = os.path.join(output_folder, f"{base}_blue.png")
    
    Image.fromarray(red_intensity, mode="L").save(red_path)
    Image.fromarray(green_intensity, mode="L").save(green_path)
    Image.fromarray(blue_intensity, mode="L").save(blue_path)
    
    # 5. Create output tile set
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Thermal " + sourceTileSet.Name, 
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    
    # 6. Create channels with their display colors (additive blending)
    MapsBridge.CreateChannel("Red", (255, 0, 0), True, outputTileSet.Guid)
    MapsBridge.CreateChannel("Green", (0, 255, 0), True, outputTileSet.Guid)
    MapsBridge.CreateChannel("Blue", (0, 0, 255), True, outputTileSet.Guid)
    
    # 7. Send each intensity map to its channel
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Red", red_path, True, outputTileSet.Guid
    )
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Green", green_path, True, outputTileSet.Guid
    )
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Blue", blue_path, True, outputTileSet.Guid
    )
    
    MapsBridge.AppendNotes(f"Tile [{tileInfo.Column}, {tileInfo.Row}] processed\\\\n", outputTileSet.Guid)
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()"""
        },
        {
            "name": "Brightness Threshold",
            "description": "Highlights pixels above a brightness threshold. Uses ScriptParameters for the threshold value.",
            "code": """# MAPS Script Bridge - Brightness Threshold
# Highlights pixels above a configurable threshold

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # Get threshold from script parameters (default: 128)
    try:
        threshold = float(request.ScriptParameters) if request.ScriptParameters else 128
    except ValueError:
        threshold = 128
    
    # 2. Load the input image
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    img = Image.open(input_path).convert("L")
    
    MapsBridge.LogInfo(f"Loaded: {input_filename}, Threshold: {threshold}")
    
    # 3. Apply threshold - pixels above threshold become white, below become black
    result = img.point(lambda p: 255 if p > threshold else 0)
    
    # 4. Save to temp folder (use PNG for compatibility)
    output_folder = os.path.join(tempfile.gettempdir(), "threshold_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    output_path = os.path.join(output_folder, f"{base}_threshold.png")
    result.save(output_path)
    
    # 5. Create output tile set and channel
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Threshold " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    MapsBridge.CreateChannel("Highlight", (255, 0, 0), True, outputTileSet.Guid)
    
    # 6. Send output
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Highlight", output_path, True, outputTileSet.Guid
    )
    
    MapsBridge.AppendNotes(f"Tile [{tileInfo.Column}, {tileInfo.Row}] threshold={threshold}\\\\n", outputTileSet.Guid)
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()"""
        },
        {
            "name": "Edge Detection",
            "description": "Detects edges in the image using Sobel operator for feature highlighting.",
            "code": """# MAPS Script Bridge - Edge Detection
# Detects edges using Sobel operator

import os
import tempfile
import MapsBridge
from PIL import Image, ImageFilter
import numpy as np

def sobel_edge_detection(img_array):
    \"\"\"Apply Sobel edge detection\"\"\"
    from scipy import ndimage
    
    # Sobel kernels
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
    
    # Apply convolution
    gx = ndimage.convolve(img_array.astype(float), sobel_x)
    gy = ndimage.convolve(img_array.astype(float), sobel_y)
    
    # Compute magnitude
    magnitude = np.sqrt(gx**2 + gy**2)
    
    # Normalize to 0-255
    magnitude = (magnitude / magnitude.max() * 255).astype(np.uint8)
    return magnitude

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Load the input image
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    img = Image.open(input_path).convert("L")
    img_array = np.array(img)
    
    MapsBridge.LogInfo(f"Loaded: {input_filename} ({img.size[0]}x{img.size[1]})")
    
    # 3. Apply edge detection
    edges = sobel_edge_detection(img_array)
    result = Image.fromarray(edges, mode="L")
    
    # 4. Save to temp folder (use PNG for compatibility)
    output_folder = os.path.join(tempfile.gettempdir(), "edge_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    output_path = os.path.join(output_folder, f"{base}_edges.png")
    result.save(output_path)
    
    # 5. Create output tile set and channel
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Edges " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    MapsBridge.CreateChannel("Edges", (0, 255, 255), True, outputTileSet.Guid)
    
    # 6. Send output
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Edges", output_path, True, outputTileSet.Guid
    )
    
    MapsBridge.AppendNotes(f"Tile [{tileInfo.Column}, {tileInfo.Row}] edge detection\\\\n", outputTileSet.Guid)
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()"""
        },
        {
            "name": "Copy Original",
            "description": "Simple script that copies the original image to output. Good starting template.",
            "code": """# MAPS Script Bridge - Copy Original
# Simple template that copies the input image to output

import os
import shutil
import tempfile
import MapsBridge

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Get input path
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    
    MapsBridge.LogInfo(f"Processing: {input_filename}")
    
    # 3. Copy to temp folder (save as PNG for compatibility)
    output_folder = os.path.join(tempfile.gettempdir(), "copy_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    
    # Use PNG extension for output (works in both helper app and MAPS)
    output_path = os.path.join(output_folder, f"{base}_copy.png")
    
    # Open and re-save as PNG to ensure compatibility
    from PIL import Image
    img = Image.open(input_path)
    img.save(output_path)
    
    # 4. Create output tile set and channel
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Copy " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    MapsBridge.CreateChannel("Original", (255, 255, 255), True, outputTileSet.Guid)
    
    # 5. Send output
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Original", output_path, True, outputTileSet.Guid
    )
    
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()"""
        },
        {
            "name": "Particle Categorization",
            "description": "Segments particles, measures shape (area, solidity, circularity), and categorizes as round/irregular/small with color-coded output.",
            "code": """# MAPS Script Bridge - Particle Categorization
# Segments particles in EM images, measures shape, and categorizes them.
# Outputs:
#   1) Grayscale mask (labels per particle)
#   2) RGB visualization colored by category (round / irregular / small)

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np
from scipy import ndimage
from skimage import filters, morphology, measure, exposure

# ============================================================================
# TUNABLE PARAMETERS - Adjust for your specific images
# ============================================================================

GAUSSIAN_SIGMA = 1.5          # Noise reduction blur
CLAHE_CLIP_LIMIT = 0.03       # Contrast enhancement
MIN_PARTICLE_SIZE = 50        # Minimum particle area in pixels
FILL_HOLES = True             # Fill holes inside particles

# In this image, particles are BRIGHT on a DARK background
PARTICLES_ARE_DARK = False

# ---- Categorization thresholds ---------------------------------------------

# Anything smaller than this (in pixels) is "small"
SMALL_AREA_THRESHOLD = 300

# Shape thresholds for "round" particles
MIN_SOLIDITY_ROUND = 0.95     # 0-1, higher = fewer concavities
MIN_CIRCULARITY_ROUND = 0.85  # 4*pi*A / P^2, 1 = perfect circle

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_image(img_array):
    \"\"\"Normalize image intensities to 0-1 range.\"\"\"
    img_float = img_array.astype(np.float64)
    img_min, img_max = img_float.min(), img_float.max()
    if img_max - img_min > 0:
        return (img_float - img_min) / (img_max - img_min)
    return img_float

def preprocess_image(img_array, sigma=GAUSSIAN_SIGMA, clip_limit=CLAHE_CLIP_LIMIT):
    \"\"\"Apply Gaussian blur and CLAHE contrast enhancement.\"\"\"
    blurred = ndimage.gaussian_filter(img_array, sigma=sigma)
    blurred_norm = normalize_image(blurred)
    enhanced = exposure.equalize_adapthist(blurred_norm, clip_limit=clip_limit)
    return (enhanced * 255).astype(np.uint8)

def segment_particles(
    img_array,
    min_size=MIN_PARTICLE_SIZE,
    fill_holes=FILL_HOLES,
    dark_particles=PARTICLES_ARE_DARK
):
    \"\"\"
    Segment particles using Otsu thresholding.
    Returns labeled image where each particle has a unique integer ID.
    \"\"\"
    threshold = filters.threshold_otsu(img_array)

    if dark_particles:
        binary = img_array < threshold
    else:
        binary = img_array > threshold

    if fill_holes:
        binary = ndimage.binary_fill_holes(binary)

    binary = morphology.remove_small_objects(binary, min_size=min_size)
    labeled, num_particles = ndimage.label(binary)
    return labeled, num_particles

def categorize_particles(labeled_array):
    \"\"\"
    For each labeled particle, compute region properties and assign a category:
      1 = round
      2 = irregular
      3 = small
    Returns:
      category_map: 2D array with category IDs
      stats: list of per-particle dictionaries with measurements & category
    \"\"\"
    props = measure.regionprops(labeled_array)
    category_map = np.zeros_like(labeled_array, dtype=np.uint8)
    stats = []

    for region in props:
        label = region.label
        area = region.area
        solidity = region.solidity

        perimeter = region.perimeter if region.perimeter > 0 else 1.0
        circularity = 4.0 * np.pi * area / (perimeter ** 2)

        # Decide category
        if area < SMALL_AREA_THRESHOLD:
            category = 3  # small
        elif (solidity >= MIN_SOLIDITY_ROUND) and (circularity >= MIN_CIRCULARITY_ROUND):
            category = 1  # round
        else:
            category = 2  # irregular

        category_map[labeled_array == label] = category

        stats.append({
            "label": label,
            "area": float(area),
            "solidity": float(solidity),
            "circularity": float(circularity),
            "category": int(category),
        })

    return category_map, stats

def make_category_rgb(category_map):
    \"\"\"
    Convert category map to RGB for visualization:
      0 = background (black)
      1 = round      (green)
      2 = irregular  (red)
      3 = small      (blue)
    \"\"\"
    h, w = category_map.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)

    color_round = (0, 255, 0)
    color_irregular = (255, 0, 0)
    color_small = (0, 0, 255)

    rgb[category_map == 1] = color_round
    rgb[category_map == 2] = color_irregular
    rgb[category_map == 3] = color_small

    return rgb

# ============================================================================
# MAIN
# ============================================================================

def main():
    # 1. Get input from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]

    # 2. Load the input image (grayscale)
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    img = Image.open(input_path).convert("L")
    img_array = np.array(img)

    MapsBridge.LogInfo(f"Loaded: {input_filename} ({img.size[0]}x{img.size[1]})")

    # 3. Preprocess: blur + CLAHE
    preprocessed = preprocess_image(img_array)
    MapsBridge.LogInfo("Preprocessing complete (Gaussian blur + CLAHE)")

    # 4. Segment particles
    labeled, num_particles = segment_particles(preprocessed)
    MapsBridge.LogInfo(f"Segmentation complete: {num_particles} particles found")

    # 5. Categorize particles
    category_map, stats = categorize_particles(labeled)

    # Count categories
    n_round = sum(s["category"] == 1 for s in stats)
    n_irregular = sum(s["category"] == 2 for s in stats)
    n_small = sum(s["category"] == 3 for s in stats)
    MapsBridge.LogInfo(
        f"Categories: {n_round} round, {n_irregular} irregular, {n_small} small"
    )

    # 6. Build visualization RGB
    category_rgb = make_category_rgb(category_map)

    # 7. Setup output folder
    output_folder = os.path.join(tempfile.gettempdir(), "segmentation_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)

    # Use PNG for outputs
    mask_path = os.path.join(output_folder, f"{base}_labels.png")
    cat_path = os.path.join(output_folder, f"{base}_categories.png")

    # 8. Save labeled mask (16-bit-style visualization)
    if labeled.max() > 0:
        mask_visual = (
            labeled.astype(np.float32) / labeled.max() * 255
        ).astype(np.uint8)
    else:
        mask_visual = labeled.astype(np.uint8)

    mask_img = Image.fromarray(mask_visual, mode="L")
    mask_img.save(mask_path)
    MapsBridge.LogInfo(f"Saved mask: {os.path.basename(mask_path)}")

    # 9. Save category RGB image
    cat_img = Image.fromarray(category_rgb, mode="RGB")
    cat_img.save(cat_path)
    MapsBridge.LogInfo(f"Saved categories: {os.path.basename(cat_path)}")

    # 10. Create output tile set in MAPS
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Particle Categories " + sourceTileSet.Name,
        targetLayerGroupName="Outputs",
    )
    outputTileSet = outputTileSetInfo.TileSet

    # 11. Create channels and send outputs
    MapsBridge.CreateChannel("Labels", (255, 255, 255), True, outputTileSet.Guid)
    MapsBridge.CreateChannel("Categories", (255, 255, 255), True, outputTileSet.Guid)

    MapsBridge.SendSingleTileOutput(
        tileInfo.Row,
        tileInfo.Column,
        "Labels",
        mask_path,
        True,
        outputTileSet.Guid,
    )
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row,
        tileInfo.Column,
        "Categories",
        cat_path,
        True,
        outputTileSet.Guid,
    )

    # 12. Append notes (summary counts)
    MapsBridge.AppendNotes(
        (
            f"Tile [{tileInfo.Column}, {tileInfo.Row}]: "
            f"{num_particles} particles "
            f"({n_round} round, {n_irregular} irregular, {n_small} small)\\\\n"
        ),
        outputTileSet.Guid,
    )
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()"""
        },
        {
            "name": "False Color - Single Image",
            "description": "Creates a single RGB false-color visualization using viridis colormap. Good for quick viewing, but no independent channel control in Maps.",
            "code": """# MAPS Script Bridge - False Color (Single Image)
# Creates a single RGB color visualization using the viridis colormap.
# Output: One color image (no independent channel control in Maps)
# Use when: You want a quick color visualization or final composite

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np
import matplotlib.cm as cm

def main():
    # 1. Get the script request from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Get input image filename for channel "0"
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    
    # 3. Load the image and convert to grayscale, then to NumPy array
    MapsBridge.LogInfo(f"Loading: {input_path}")
    img = Image.open(input_path).convert("L")  # Convert to grayscale
    gray_data = np.array(img)
    
    # 4. Apply the false color map
    # Normalize the grayscale data to the 0.0-1.0 range
    # This automatically handles both 8-bit and 16-bit images
    MapsBridge.LogInfo("Applying 'viridis' colormap...")
    min_val = gray_data.min()
    max_val = gray_data.max()
    
    if max_val > min_val:
        normalized_data = (gray_data - min_val) / (max_val - min_val)
    else:
        # Handle solid color images to avoid division by zero
        normalized_data = np.zeros_like(gray_data, dtype=float)

    # Apply the 'viridis' colormap. The result is an RGBA array with float values.
    colored_data = cm.viridis(normalized_data)
    
    # Convert from float RGBA (0.0-1.0) to uint8 RGB (0-255) for saving
    rgb_array = (colored_data[:, :, :3] * 255).astype(np.uint8)
    
    # Convert the NumPy array back to a PIL Image
    result_image = Image.fromarray(rgb_array)

    # 5. Save output to a temporary folder
    output_folder = os.path.join(tempfile.gettempdir(), "false_color_output")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    output_path = os.path.join(output_folder, f"{base}_color.png")
    result_image.save(output_path)
    MapsBridge.LogInfo(f"Saved false color image to: {output_path}")
    
    # 6. Create the output tile set
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "False Color " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    
    # 7. Create a channel for the colored output and send the result
    MapsBridge.CreateChannel("Viridis", (255, 255, 255), True, outputTileSet.Guid)
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Viridis", output_path, True, outputTileSet.Guid
    )
    
    MapsBridge.LogInfo("Done!")

if __name__ == "__main__":
    main()"""
        },
        {
            "name": "False Color - Multi-Channel",
            "description": "Creates separate R, G, B grayscale channels using viridis colormap. Enables independent threshold control, on/off toggle, and additive blending in Maps.",
            "code": """# MAPS Script Bridge - False Color (Multi-Channel)
# Creates separate grayscale channels (R, G, B) from viridis colormap.
# Output: Three intensity map channels with independent control
# Use when: You want thresholding, segmentation, or independent channel control in Maps

import os
import tempfile
import MapsBridge
from PIL import Image
import numpy as np
import matplotlib.cm as cm

def main():
    # 1. Get the script request from MAPS
    request = MapsBridge.ScriptTileSetRequest.FromStdIn()
    sourceTileSet = request.SourceTileSet
    tileInfo = sourceTileSet.Tiles[0]
    
    # 2. Get input image filename for channel "0"
    input_filename = tileInfo.ImageFileNames["0"]
    source_folder = sourceTileSet.DataFolderPath
    input_path = os.path.join(source_folder, input_filename)
    
    # 3. Load the image and convert to grayscale
    MapsBridge.LogInfo(f"Loading: {input_path}")
    img = Image.open(input_path).convert("L")
    gray_data = np.array(img)
    
    # 4. Apply viridis colormap
    MapsBridge.LogInfo("Applying 'viridis' colormap and separating channels...")
    min_val = gray_data.min()
    max_val = gray_data.max()
    
    if max_val > min_val:
        normalized_data = (gray_data - min_val) / (max_val - min_val)
    else:
        normalized_data = np.zeros_like(gray_data, dtype=float)
    
    # Apply colormap (returns RGBA float array)
    colored_data = cm.viridis(normalized_data)
    
    # 5. Separate into grayscale intensity channels (R, G, B)
    # Each channel is an intensity map (0-255) that Maps will display with the assigned color
    red_channel = (colored_data[:, :, 0] * 255).astype(np.uint8)
    green_channel = (colored_data[:, :, 1] * 255).astype(np.uint8)
    blue_channel = (colored_data[:, :, 2] * 255).astype(np.uint8)
    
    # 6. Save each channel as grayscale PNG
    output_folder = os.path.join(tempfile.gettempdir(), "false_color_multichannel")
    os.makedirs(output_folder, exist_ok=True)
    base, ext = os.path.splitext(input_filename)
    
    red_path = os.path.join(output_folder, f"{base}_red.png")
    green_path = os.path.join(output_folder, f"{base}_green.png")
    blue_path = os.path.join(output_folder, f"{base}_blue.png")
    
    Image.fromarray(red_channel, mode="L").save(red_path)
    Image.fromarray(green_channel, mode="L").save(green_path)
    Image.fromarray(blue_channel, mode="L").save(blue_path)
    
    MapsBridge.LogInfo("Saved R, G, B channels as grayscale intensity maps")
    
    # 7. Create output tile set
    outputTileSetInfo = MapsBridge.GetOrCreateOutputTileSet(
        "Viridis Multi-Channel " + sourceTileSet.Name,
        targetLayerGroupName="Outputs"
    )
    outputTileSet = outputTileSetInfo.TileSet
    
    # 8. Create three channels with additive blending
    # Each channel gets its corresponding display color
    MapsBridge.CreateChannel("Red Component", (255, 0, 0), True, outputTileSet.Guid)
    MapsBridge.CreateChannel("Green Component", (0, 255, 0), True, outputTileSet.Guid)
    MapsBridge.CreateChannel("Blue Component", (0, 0, 255), True, outputTileSet.Guid)
    
    # 9. Send each grayscale channel to Maps
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Red Component", red_path, True, outputTileSet.Guid
    )
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Green Component", green_path, True, outputTileSet.Guid
    )
    MapsBridge.SendSingleTileOutput(
        tileInfo.Row, tileInfo.Column,
        "Blue Component", blue_path, True, outputTileSet.Guid
    )
    
    MapsBridge.AppendNotes(
        f"Tile [{tileInfo.Column}, {tileInfo.Row}] - Viridis colormap as multi-channel.\\\\n"
        "Toggle R/G/B channels independently, adjust thresholds, or segment by intensity!\\\\n",
        outputTileSet.Guid
    )
    
    MapsBridge.LogInfo("Done! Three channels created with additive blending.")
    MapsBridge.LogInfo("In Maps: Toggle channels on/off, adjust thresholds independently!")

if __name__ == "__main__":
    main()"""
        }
    ]

def initialize_default_scripts(user_id: str):
    """Initialize a new user with default scripts"""
    try:
        print(f"[initialize_default_scripts] Starting initialization for user {user_id}")
        default_scripts = get_default_scripts()
        print(f"[initialize_default_scripts] Got {len(default_scripts)} default scripts")
        
        for idx, script_data in enumerate(default_scripts):
            script_id = str(uuid.uuid4())
            script_file = USER_SCRIPTS_DIR / f"{script_id}.json"
            
            script = {
                "id": script_id,
                "user_id": user_id,
                "name": script_data["name"],
                "description": script_data["description"],
                "code": script_data["code"],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(script, f, indent=2)
            
            print(f"[initialize_default_scripts] {idx+1}/{len(default_scripts)} Created script: {script['name']} (id={script_id})")
        
        print(f"✓ Initialized {len(default_scripts)} default scripts for user {user_id}")
    except Exception as e:
        print(f"Warning: Failed to initialize default scripts for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        # Don't fail user creation if default script initialization fails

@app.get("/api/users/test")
def test_users_endpoint():
    """Test endpoint to verify users API is accessible"""
    return {"message": "Users API is working", "timestamp": datetime.now().isoformat()}

@app.get("/api/users")
def list_users(db: Session = Depends(get_db)):
    """List all user accounts"""
    try:
        users = db.query(User).order_by(User.name).all()
        return {"users": [user.to_dict() for user in users]}
    except Exception as e:
        print(f"Error listing users: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Failed to list users: {str(e)}"},
            status_code=500
        )

@app.post("/api/users")
async def create_user(request: CreateUserRequest, db: Session = Depends(get_db)):
    """Create a new user account"""
    try:
        print(f"Received create user request: name='{request.name}'")
        
        # Validate name
        if not request.name or not request.name.strip():
            print("Validation failed: name is empty")
            return JSONResponse(
                {"error": "Name is required"},
                status_code=400
            )
        
        # Check if name already exists
        existing_user = db.query(User).filter(User.name == request.name.strip()).first()
        if existing_user:
            print(f"User name already exists: '{request.name}'")
            return JSONResponse(
                {"error": "A user with this name already exists"},
                status_code=400
            )
        
        # Create new user
        new_user = User(
            name=request.name.strip(),
            created_at=datetime.utcnow()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✓ Created user: {new_user.name} (ID: {new_user.id})")
        
        return {"success": True, "user": new_user.to_dict()}
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Failed to create user: {str(e)}"},
            status_code=500
        )

@app.get("/api/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get a specific user account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    return {"user": user.to_dict()}

@app.post("/api/admin/reset-user-data")
def reset_user_data(db: Session = Depends(get_db)):
    """
    Delete all user accounts, user scripts, and user-uploaded images.
    Keeps default scripts and default library images.
    """
    try:
        deleted_counts = {
            "users": 0,
            "scripts": 0,
            "images": 0
        }
        
        # 1. Delete all user-uploaded images from database and filesystem (before users to avoid FK issues)
        user_images = db.query(UserImage).all()
        deleted_counts["images"] = len(user_images)
        for image in user_images:
            # Check user uploads first, then library dir for backward compat
            image_path = USER_UPLOADS_DIR / image.filename
            if not image_path.exists():
                image_path = LIBRARY_IMAGES_DIR / image.filename
            if image_path.exists():
                image_path.unlink()
                print(f"[RESET] Deleted user image file: {image.filename}")
            db.delete(image)
        print(f"[RESET] Deleted {deleted_counts['images']} user images")
        
        # 2. Delete all user scripts
        scripts = db.query(UserScript).all()
        deleted_counts["scripts"] = len(scripts)
        for script in scripts:
            db.delete(script)
        print(f"[RESET] Deleted {deleted_counts['scripts']} user scripts")
        
        # 3. Delete all users (cascade will handle remaining relationships)
        users = db.query(User).all()
        deleted_counts["users"] = len(users)
        for user in users:
            db.delete(user)
        print(f"[RESET] Deleted {deleted_counts['users']} user accounts")
        
        db.commit()
        
        print(f"[RESET] ✓ Reset complete: {deleted_counts['users']} users, {deleted_counts['scripts']} scripts, {deleted_counts['images']} images deleted")
        
        return {
            "success": True,
            "deleted": deleted_counts,
            "message": f"Deleted {deleted_counts['users']} users, {deleted_counts['scripts']} user scripts, and {deleted_counts['images']} user images"
        }
    except Exception as e:
        db.rollback()
        print(f"[RESET] ✗ Error during reset: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Failed to reset user data: {str(e)}"},
            status_code=500
        )

# ============================================================================
# Library Scripts API
# ============================================================================

@app.get("/api/library-scripts")
def get_library_scripts(db: Session = Depends(get_db)):
    """Get all library/default scripts"""
    try:
        scripts = db.query(LibraryScript).order_by(LibraryScript.category, LibraryScript.name).all()
        return {"scripts": [script.to_dict() for script in scripts]}
    except Exception as e:
        print(f"[API] Error loading library scripts: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Failed to load library scripts: {str(e)}"},
            status_code=500
        )

# ============================================================================
# User Scripts API
# ============================================================================

USER_SCRIPTS_DIR = BASE_DIR / "user_scripts"
USER_SCRIPTS_DIR.mkdir(exist_ok=True)

class UserScriptRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    code: str
    user_id: str  # Required for associating script with user

@app.get("/api/user-scripts")
def get_user_scripts(user_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get user-saved scripts for a specific user"""
    print(f"[API] GET /api/user-scripts called with user_id={user_id}")
    try:
        query = db.query(UserScript)
        if user_id:
            query = query.filter(UserScript.user_id == user_id)
        
        scripts = query.order_by(desc(UserScript.created_at)).all()
        print(f"[API] Found {len(scripts)} scripts")
        
        return {"scripts": [script.to_dict() for script in scripts]}
    except Exception as e:
        print(f"[API] Error loading scripts: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Failed to load scripts: {str(e)}"},
            status_code=500
        )

@app.post("/api/user-scripts")
async def save_user_script(script: UserScriptRequest, db: Session = Depends(get_db)):
    """Save a new user script"""
    try:
        print(f"[API] POST /api/user-scripts - Saving script '{script.name}' for user {script.user_id}")
        
        # Verify user exists
        user = db.query(User).filter(User.id == script.user_id).first()
        if not user:
            return JSONResponse(
                {"error": "User not found"},
                status_code=404
            )
        
        new_script = UserScript(
            user_id=script.user_id,
            name=script.name,
            description=script.description or "",
            code=script.code,
            is_user_created=True
        )
        
        db.add(new_script)
        db.commit()
        db.refresh(new_script)
        
        print(f"[API] ✓ Script saved successfully: {new_script.id}")
        return {"success": True, "script": new_script.to_dict()}
    except Exception as e:
        db.rollback()
        print(f"[API] ✗ Failed to save script: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Failed to save script: {str(e)}"}, 
            status_code=500
        )

@app.put("/api/user-scripts/{script_id}")
async def update_user_script(script_id: str, script: UserScriptRequest, db: Session = Depends(get_db)):
    """Update an existing user script"""
    print(f"[API] PUT /api/user-scripts/{script_id} - Updating script for user {script.user_id}")
    
    try:
        existing_script = db.query(UserScript).filter(UserScript.id == script_id).first()
        if not existing_script:
            print(f"[API] ✗ Script not found: {script_id}")
            return JSONResponse({"error": "Script not found"}, status_code=404)
        
        # Verify user_id matches (security check)
        if existing_script.user_id != script.user_id:
            return JSONResponse(
                {"error": "Unauthorized: Script belongs to a different user"},
                status_code=403
            )
        
        # Update fields
        existing_script.name = script.name
        existing_script.description = script.description or ""
        existing_script.code = script.code
        existing_script.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(existing_script)
        
        print(f"[API] ✓ Script updated successfully: {script_id}")
        return {"success": True, "script": existing_script.to_dict()}
    except Exception as e:
        db.rollback()
        print(f"[API] ✗ Failed to update script: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Failed to update script: {str(e)}"}, 
            status_code=500
        )

@app.delete("/api/user-scripts/{script_id}")
def delete_user_script(script_id: str, db: Session = Depends(get_db)):
    """Delete a user script"""
    try:
        script = db.query(UserScript).filter(UserScript.id == script_id).first()
        if not script:
            return JSONResponse({"error": "Script not found"}, status_code=404)
        
        db.delete(script)
        db.commit()
        
        print(f"[API] ✓ Script deleted: {script_id}")
        return {"success": True}
    except Exception as e:
        db.rollback()
        print(f"[API] ✗ Failed to delete script: {e}")
        return JSONResponse(
            {"error": f"Failed to delete script: {str(e)}"}, 
            status_code=500
        )

# ============================================================================
# Script Logging and Analysis API
# ============================================================================

@app.get("/api/logs/summary")
def get_logs_summary(db: Session = Depends(get_db)):
    """Get summary statistics of script executions from database"""
    try:
        total = db.query(ExecutionSession).count()
        successes = db.query(ExecutionSession).filter(ExecutionSession.status == "success").count()
        errors = db.query(ExecutionSession).filter(ExecutionSession.status == "error").count()
        timeouts = db.query(ExecutionSession).filter(ExecutionSession.status == "timeout").count()
        
        success_rate = (successes / total * 100) if total > 0 else 0
        
        return {
            "success": True,
            "summary": {
                "total_executions": total,
                "successful_executions": successes,
                "failed_executions": errors,
                "timeout_executions": timeouts,
                "success_rate": round(success_rate, 2)
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to generate summary: {str(e)}"},
            status_code=500
        )

@app.get("/api/logs/analysis")
def get_full_analysis(db: Session = Depends(get_db)):
    """Get complete analysis of all logs from database"""
    try:
        total = db.query(ExecutionSession).count()
        successes = db.query(ExecutionSession).filter(ExecutionSession.status == "success").count()
        errors = db.query(ExecutionSession).filter(ExecutionSession.status == "error").count()
        timeouts = db.query(ExecutionSession).filter(ExecutionSession.status == "timeout").count()
        
        success_rate = (successes / total * 100) if total > 0 else 0
        
        # Get recent executions
        recent_sessions = db.query(ExecutionSession).order_by(ExecutionSession.started_at.desc()).limit(100).all()
        
        return {
            "success": True,
            "analysis": {
                "summary": {
                    "total_executions": total,
                    "successful_executions": successes,
                    "failed_executions": errors,
                    "timeout_executions": timeouts,
                    "success_rate": round(success_rate, 2)
                },
                "recent_executions": [session.to_dict() for session in recent_sessions],
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to generate analysis: {str(e)}"},
            status_code=500
        )

@app.get("/api/logs/failures")
def get_recent_failures(limit: int = 50, unfixed_only: bool = False, db: Session = Depends(get_db)):
    """Get recent failure logs from database"""
    try:
        query = db.query(ExecutionSession).filter(
            ExecutionSession.status.in_(["error", "timeout"])
        )
        
        # Order by most recent
        query = query.order_by(ExecutionSession.started_at.desc())
        
        # Apply limit
        failures = query.limit(limit).all()
        
        return {
            "success": True,
            "failures": [failure.to_dict() for failure in failures],
            "count": len(failures)
        }
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to retrieve failures: {str(e)}"},
            status_code=500
        )

@app.get("/api/logs/successes")
def get_recent_successes(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent success logs from database"""
    try:
        successes = db.query(ExecutionSession).filter(
            ExecutionSession.status == "success"
        ).order_by(ExecutionSession.started_at.desc()).limit(limit).all()
        
        return {
            "success": True,
            "successes": [success.to_dict() for success in successes],
            "count": len(successes)
        }
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to retrieve successes: {str(e)}"},
            status_code=500
        )

@app.get("/api/logs/session/{session_id}")
def get_session(session_id: str):
    """Get all attempts in a session (failure -> success journey)"""
    try:
        session = script_logger.get_session(session_id)
        if not session:
            return JSONResponse(
                {"error": "Session not found"},
                status_code=404
            )
        
        # Get full details for each attempt
        attempts_details = []
        for attempt in session.get("attempts", []):
            log_id = attempt["log_id"]
            log_details = script_logger.get_log(log_id)
            if log_details:
                attempts_details.append(log_details)
        
        return {
            "success": True,
            "session": session,
            "attempts": attempts_details
        }
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to retrieve session: {str(e)}"},
            status_code=500
        )

@app.get("/api/logs/log/{log_id}")
def get_log(log_id: str):
    """Get a specific log entry"""
    try:
        log_entry = script_logger.get_log(log_id)
        if not log_entry:
            return JSONResponse(
                {"error": "Log not found"},
                status_code=404
            )
        
        return {
            "success": True,
            "log": log_entry
        }
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to retrieve log: {str(e)}"},
            status_code=500
        )

@app.get("/api/logs/ai-context")
def get_ai_context(max_examples: int = 10):
    """Get AI-readable context about common errors"""
    try:
        context = log_analyzer.generate_context_for_ai(max_examples=max_examples)
        ai_summary = log_analyzer._generate_ai_summary()
        
        return {
            "success": True,
            "context": context,
            "summary": ai_summary
        }
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to generate AI context: {str(e)}"},
            status_code=500
        )

@app.get("/api/logs/error-patterns")
def get_error_patterns():
    """Get analysis of common error patterns"""
    try:
        analysis = log_analyzer.analyze_all()
        return {
            "success": True,
            "error_patterns": analysis["error_patterns"],
            "common_errors": analysis["common_errors"],
            "library_issues": analysis["library_issues"],
            "mapbridge_issues": analysis["mapbridge_issues"]
        }
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to analyze error patterns: {str(e)}"},
            status_code=500
        )

@app.get("/api/logs/recommendations")
def get_recommendations():
    """Get recommendations for improving system_context"""
    try:
        analysis = log_analyzer.analyze_all()
        return {
            "success": True,
            "recommendations": analysis["recommendations"],
            "ai_learning_summary": analysis["ai_learning_summary"]
        }
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to generate recommendations: {str(e)}"},
            status_code=500
        )

@app.post("/api/logs/clear")
def clear_logs(db: Session = Depends(get_db)):
    """Delete all script execution logs from database."""
    try:
        # Count records before deletion
        total_count = db.query(ExecutionSession).count()
        success_count = db.query(ExecutionSession).filter(ExecutionSession.status == "success").count()
        error_count = db.query(ExecutionSession).filter(ExecutionSession.status == "error").count()
        timeout_count = db.query(ExecutionSession).filter(ExecutionSession.status == "timeout").count()
        
        # Delete all execution sessions
        db.query(ExecutionSession).delete()
        db.commit()
        
        print(f"[CLEAR_LOGS] Deleted {total_count} execution session records")
        
        return {
            "success": True,
            "deleted": {
                "total": total_count,
                "successes": success_count,
                "failures": error_count,
                "timeouts": timeout_count
            }
        }
    except Exception as e:
        db.rollback()
        print(f"[CLEAR_LOGS] Error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"error": f"Failed to clear logs: {str(e)}"},
            status_code=500,
        )

DEPLOY_DIR = pathlib.Path("/deploy")

class DeployRequest(BaseModel):
    script_name: str
    code: str

@app.post("/api/deploy-script")
async def deploy_script(request: DeployRequest):
    """Deploy a script to C:\\project\\Python (mounted at /deploy in container)"""
    try:
        # Ensure deploy directory exists
        DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
        
        # Sanitize script name for filename
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in request.script_name)
        if not safe_name.endswith('.py'):
            safe_name += '.py'
        
        script_file_path = DEPLOY_DIR / safe_name
        
        # Write the script file
        with open(script_file_path, 'w', encoding='utf-8') as f:
            f.write(request.code)
        
        # Return the host path for display
        host_path = f"C:\\project\\Python\\{safe_name}"
        
        return {
            "success": True, 
            "path": host_path,
            "message": f"Script deployed to {host_path}"
        }
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to deploy script: {str(e)}"}, 
            status_code=500
        )

# Serve output files with TIFF conversion support
@app.get("/outputs/{job_id}/{folder}/{filename:path}")
async def get_output_file(job_id: str, folder: str, filename: str):
    """Get output files with automatic TIFF to PNG conversion for browser display"""
    file_path = OUTPUTS_DIR / job_id / folder / filename
    
    if not file_path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)
    
    # Check if it's a TIFF file - convert to PNG for browser display
    file_ext = pathlib.Path(filename).suffix.lower()
    if file_ext in ['.tiff', '.tif']:
        try:
            # Open TIFF - DO NOT apply EXIF orientation
            # Script outputs should be displayed exactly as created
            img = Image.open(file_path)
            
            # Import numpy for advanced handling
            import numpy as np
            
            # Convert to numpy array to check data type and range
            img_array = np.array(img)
            
            # Determine if we need to normalize the pixel values
            needs_normalization = False
            
            # Check for 16-bit, 32-bit, or float images
            if img_array.dtype in [np.uint16, np.uint32, np.int16, np.int32]:
                needs_normalization = True
            elif img_array.dtype in [np.float32, np.float64]:
                needs_normalization = True
            elif img_array.dtype == np.uint8:
                # Check if it's a labeled image (values are small integers like 0, 1, 2, 3...)
                max_val = img_array.max()
                if max_val < 100 and max_val > 1:
                    # Likely a labeled image - normalize to full range
                    needs_normalization = True
            
            if needs_normalization and img_array.size > 0:
                # Normalize to 0-255 range
                min_val = img_array.min()
                max_val = img_array.max()
                
                if max_val > min_val:
                    # Scale to 0-255
                    normalized = ((img_array - min_val) / (max_val - min_val) * 255).astype(np.uint8)
                    img = Image.fromarray(normalized)
                else:
                    # All same value - just convert to uint8
                    img = Image.fromarray((img_array * 0).astype(np.uint8))
            
            # Handle different image modes
            if img.mode == 'RGBA':
                # Keep RGBA for PNG (supports transparency)
                pass
            elif img.mode == 'LA':
                # Convert LA (grayscale + alpha) to RGBA
                img = img.convert('RGBA')
            elif img.mode == 'P':
                # Convert palette mode to RGBA
                img = img.convert('RGBA')
            elif img.mode in ('L', '1'):
                # Convert grayscale to RGB
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                # Convert any other mode to RGB
                img = img.convert('RGB')
            
            # Save to bytes buffer as PNG
            # PNG format doesn't preserve EXIF by default, which is what we want
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG', optimize=True)
            img_buffer.seek(0)
            
            return StreamingResponse(
                img_buffer,
                media_type="image/png",
                headers={
                    "Content-Disposition": f"inline; filename={filename.rsplit('.', 1)[0]}.png",
                    "Cache-Control": "public, max-age=3600"
                }
            )
        except Exception as e:
            # If conversion fails, return error with details
            return JSONResponse(
                {"error": f"Failed to convert TIFF image: {str(e)}", "detail": traceback.format_exc()},
                status_code=500
            )
    
    # For PNG/JPG output images, strip EXIF orientation to prevent unwanted rotation
    if file_ext in ['.png', '.jpg', '.jpeg'] and '/result/' in str(file_path):
        try:
            # Read and re-save without EXIF orientation
            img = Image.open(file_path)
            
            # Convert to bytes without EXIF
            img_buffer = io.BytesIO()
            if file_ext == '.png':
                img.save(img_buffer, format='PNG', optimize=True)
                media_type = "image/png"
            else:
                # Save JPEG without EXIF
                img.save(img_buffer, format='JPEG', quality=95, exif=b'')
                media_type = "image/jpeg"
            
            img_buffer.seek(0)
            return StreamingResponse(
                img_buffer,
                media_type=media_type,
                headers={
                    "Content-Disposition": f"inline; filename={filename}",
                    "Cache-Control": "public, max-age=3600"
                }
            )
        except Exception:
            # If stripping EXIF fails, serve file directly
            pass
    
    # For other formats, serve directly
    return FileResponse(file_path)

# Middleware to disable caching for development
@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    # Disable caching for HTML and JS files in development
    if request.url.path.endswith(('.html', '.jsx', '.js')):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Serve the frontend as static content
# Note: Static mounts must come AFTER API routes to avoid intercepting them
# Outputs are served via the custom endpoint above for TIFF conversion support
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
