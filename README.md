# Python Image Sandbox MVP

This is a minimal, **local** MVP that lets users write Python in the browser, send it to a FastAPI backend,
execute the code in a **sandboxed Docker container** (no network, limited CPU/RAM), and view the resulting image.

> ⚠️ **Prereqs**: You need Docker and Python 3.10+ installed locally.
> The API calls `docker run` to execute code in a hardened container.

## Quick start

### Option 1: Using Docker (Recommended for Development)

**Windows:**
1. Ensure Docker Desktop is running
2. Double-click `start-dev.bat` or run it from command prompt
3. The script will:
   - Build the execution sandbox image (`py-exec:latest`)
   - Build and start the backend container with auto-reload
   - Mount your project files for live code changes
4. Open your browser to http://localhost:8000

**Linux/Mac:**
```bash
# Build execution sandbox
docker build -t py-exec:latest backend/runner_image

# Start backend with docker-compose
docker-compose up --build
```

### Option 2: Local Python Development

1) Create and activate a virtual environment (optional but recommended)
```bash
python -m venv .venv && source .venv/bin/activate   # on Windows use .venv\Scripts\activate
```

2) Install API dependencies
```bash
pip install -r backend/requirements.txt
```

3) Build the execution sandbox image (this image runs user code)
```bash
docker build -t py-exec:latest backend/runner_image
```

4) Run the API
```bash
uvicorn backend.app:app --reload
```
The server starts on http://127.0.0.1:8000

### Using the UI

- Navigate to: http://127.0.0.1:8000/    (the API serves the frontend)
- Either upload your own image (PNG/JPG) **or** click "Use Sample Image".
- Edit the Python code, then click **Run**.
- The result appears below the editor.

**Note:** When using Docker, changes to `backend/` and `frontend/` files will automatically reload the server.

## How it works

- The browser sends your code + (optional) image via `POST /run` (multipart form).
- The API creates a job folder, writes your code to `/code/main.py` and image to `/input/image.png`.
- The API launches a **short-lived Docker container**:
  - No network, read-only filesystem, 1 CPU, 1 GiB RAM
  - Mounts `/input` read-only, `/output` writeable, `/code` read-only
  - Passes your parameters via `USER_PARAMS` env var
- Your code saves the processed image to `/output/result.png`.
- The API returns a URL to the result image served at `/outputs/<job_id>/result.png`.

## Script Execution Logging & AI Learning 🧠

**NEW:** This system automatically learns from script execution failures and successes!

Every script execution is logged with:
- ✅ **Successes** - What works well
- ❌ **Failures** - Error details and stack traces
- 🔗 **Sessions** - Groups related attempts (failure → fix → success)
- 📊 **Analysis** - Common error patterns and recommendations

The AI uses this data to **improve future script generation** and avoid repeating mistakes!

### Quick Commands

```bash
# View summary statistics
python analyze_logs.py summary

# See common error patterns
python analyze_logs.py errors

# Get AI improvement recommendations
python analyze_logs.py recommendations

# See unfixed failures
python analyze_logs.py unfixed

# Export full analysis
python analyze_logs.py export
```

### API Endpoints

- `GET /api/logs/summary` - Success/failure statistics
- `GET /api/logs/analysis` - Full analysis report
- `GET /api/logs/failures` - Recent failure logs
- `GET /api/logs/successes` - Recent success logs
- `GET /api/logs/recommendations` - AI improvement suggestions

### Learn More

- 📖 **Quick Start:** See `LOGGING_QUICKSTART.md` for examples
- 📚 **Full Documentation:** See `LOGGING_SYSTEM.md` for API details

### Benefits

- 📈 **Measurable Progress** - Track success rate over time
- 🎯 **Pattern Detection** - Automatically identifies common mistakes
- 🔄 **Self-Improving AI** - Learns from failures to generate better code
- 🔍 **Debugging Help** - Easily review what went wrong and how it was fixed

## Notes & next steps

- This MVP is synchronous: `/run` blocks until the container finishes. For production, add a queue (Celery/RQ) + WebSockets for logs.
- The runner only includes a **curated** set of imaging libs (see `backend/runner_image/requirements.txt`).
- The container blocks network and drops capabilities for safety, but this is still an MVP—harden further for multi-tenant use (AppArmor/seccomp/gVisor, timeouts, sandbox SDK, etc.).
- **NEW:** The logging system builds a knowledge base of script failures/successes for AI improvement.