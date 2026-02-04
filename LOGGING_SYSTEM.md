# Script Execution Logging System

## Overview

This system automatically logs every script execution attempt (both failures and successes) to build a knowledge base that helps improve AI-generated scripts over time.

## Features

### 1. **Automatic Logging**
- Every script execution is logged with full context
- Failures include error messages, stack traces, and stderr
- Successes include output files and execution time
- Sessions group related attempts (failures → eventual success)

### 2. **Intelligent Analysis**
- Identifies common error patterns
- Categorizes errors (import errors, attribute errors, etc.)
- Tracks library-specific issues
- Analyzes successful fix strategies
- Generates recommendations for improving the AI

### 3. **AI Learning**
- AI automatically learns from past failures
- System context is dynamically updated with common mistakes
- Reduces repeat failures over time
- Improves first-time success rate

## Directory Structure

```
logs/
├── failures/           # Failed execution attempts
│   └── YYYY-MM-DD/    # Organized by date
│       └── {log_id}.json
├── successes/         # Successful executions
│   └── YYYY-MM-DD/
│       └── {log_id}.json
├── sessions/          # Session metadata (groups related attempts)
│   └── {session_id}.json
└── analysis/          # Analysis results and patterns
    └── latest_analysis.json
```

## Log Entry Format

### Failure Log
```json
{
  "log_id": "uuid",
  "session_id": "uuid",
  "timestamp": "ISO-8601",
  "status": "failed",
  "code": "python code",
  "code_hash": "md5hash",
  "user_prompt": "what the user asked for",
  "ai_model": "gemini-2.5-flash-lite",
  "image_filename": "image.png",
  "error_message": "concise error",
  "error_type": "TypeError",
  "stderr": "full stderr output",
  "stdout": "stdout if any",
  "return_code": 2,
  "previous_attempt_id": "uuid or null",
  "fixed_by": "uuid or null",
  "error_category": "import_error",
  "tags": ["lib:MapsBridge", "error:import"]
}
```

### Success Log
```json
{
  "log_id": "uuid",
  "session_id": "uuid",
  "timestamp": "ISO-8601",
  "status": "success",
  "code": "python code",
  "code_hash": "md5hash",
  "user_prompt": "what the user asked for",
  "ai_model": "gemini-2.5-flash-lite",
  "image_filename": "image.png",
  "output_files": ["result.png"],
  "stdout": "execution output",
  "execution_time_seconds": 1.23,
  "previous_attempt_id": "uuid or null",
  "tags": ["lib:MapsBridge", "output:tile"]
}
```

## API Endpoints

### Get Summary Statistics
```
GET /api/logs/summary
```
Returns overview of success/failure rates.

### Get Full Analysis
```
GET /api/logs/analysis
```
Returns complete analysis including:
- Error patterns
- Common errors
- Fix strategies
- Library issues
- Recommendations

### Get Recent Failures
```
GET /api/logs/failures?limit=50&unfixed_only=false
```
Returns recent failure logs.

### Get Recent Successes
```
GET /api/logs/successes?limit=50
```
Returns recent success logs.

### Get Session Details
```
GET /api/logs/session/{session_id}
```
Returns all attempts in a session (failure → success journey).

### Get Specific Log
```
GET /api/logs/log/{log_id}
```
Returns a specific log entry.

### Get AI Context
```
GET /api/logs/ai-context?max_examples=10
```
Returns AI-readable context about common errors.

### Get Error Patterns
```
GET /api/logs/error-patterns
```
Returns analysis of common error patterns.

### Get Recommendations
```
GET /api/logs/recommendations
```
Returns recommendations for improving system_context.

## Using the Logs for AI Improvement

### 1. Review Common Errors
```bash
curl http://localhost:8000/api/logs/error-patterns
```

This shows you:
- Most common error categories
- Specific error messages
- Fix rates for each error type

### 2. Get AI Learning Summary
```bash
curl http://localhost:8000/api/logs/ai-context
```

This generates a summary that can be:
- Shared with AI assistants to improve script generation
- Used to update the system_context
- Analyzed to identify training gaps

### 3. Review Unfixed Failures
```bash
curl http://localhost:8000/api/logs/failures?unfixed_only=true
```

These represent issues the AI hasn't successfully resolved yet.

### 4. Analyze Fix Strategies
The analysis includes successful fix patterns:
- What imports were added/removed
- Code structure changes
- Common solutions for each error type

## Session Tracking

Sessions group related attempts. When the AI generates a script that fails, the frontend should:

1. Store the `session_id` and `log_id` from the error response
2. When retrying with a fixed script, pass:
   - `session_id`: Same as before (links attempts)
   - `previous_attempt_id`: The `log_id` of the failed attempt
3. When successful, the success is linked to all previous failures

This creates a complete "failure → fix" history.

## Example Usage Flow

### Initial Request
```python
# User asks: "Apply Gaussian blur"
# AI generates script, execution fails

response = {
    "error": "Execution failed",
    "log_id": "fail-123",
    "session_id": "session-abc"
}
```

### Retry with Fix
```python
# User says: "Fix the error"
# AI generates corrected script

POST /run
{
    "code": "fixed code",
    "session_id": "session-abc",
    "previous_attempt_id": "fail-123",
    "user_prompt": "Fix the error"
}

# Success!
response = {
    "job_id": "job-456",
    "log_id": "success-789",
    "session_id": "session-abc"
}
```

Now the system knows:
- `fail-123` was fixed by `success-789`
- Both are part of `session-abc`
- The fix can be analyzed to learn how to avoid this error

## Benefits

### For Users
- Scripts improve over time
- Fewer errors on first attempt
- Faster iteration cycles

### For Developers
- Clear visibility into failure patterns
- Data-driven improvements to system_context
- Quantifiable success rate metrics

### For AI
- Learns from past mistakes
- Avoids repeating common errors
- Generates better code on first try

## Maintenance

### Cleanup Old Logs
Logs accumulate over time. You can implement cleanup:

```python
# Delete logs older than 30 days
import shutil
from datetime import datetime, timedelta

cutoff = datetime.now() - timedelta(days=30)
for date_dir in logs_dir.glob("failures/*/"):
    if datetime.strptime(date_dir.name, "%Y-%m-%d") < cutoff:
        shutil.rmtree(date_dir)
```

### Export Analysis
```bash
# Get latest analysis
curl http://localhost:8000/api/logs/analysis > analysis.json

# Review recommendations
curl http://localhost:8000/api/logs/recommendations
```

### Monitor Success Rate
```bash
# Check current success rate
curl http://localhost:8000/api/logs/summary | jq '.summary.recent_success_rate_7d'
```

## Future Enhancements

- [ ] Web UI for browsing logs
- [ ] Automatic system_context updates based on analysis
- [ ] Export logs for external analysis
- [ ] A/B testing different prompts/models
- [ ] Trend analysis (is success rate improving?)
- [ ] Anomaly detection (unusual error spikes)

## Troubleshooting

### Logs not being created
- Check that `LOGS_DIR` exists and is writable
- Verify `script_logger` is initialized in `app.py`
- Check console for import errors

### Analysis fails
- Ensure logs directory structure exists
- Check that JSON log files are valid
- Verify sufficient disk space

### Session tracking not working
- Frontend must pass `session_id` and `previous_attempt_id`
- Check that these values are preserved between requests
- Verify session files are being created in `logs/sessions/`






