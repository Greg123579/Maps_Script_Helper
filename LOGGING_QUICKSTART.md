# Logging System Quick Start Guide

## What is this?

This system automatically learns from script execution failures and successes to help the AI generate better code over time.

## Quick Overview

Every time you run a script:
- ✅ **Success** → Logged with execution details
- ❌ **Failure** → Logged with error details and stack trace
- 🔗 **Session Tracking** → Groups related attempts (failure → fix → success)

The AI uses this data to **avoid making the same mistakes** in future scripts!

## View Logs (3 ways)

### 1. Command Line (Fastest)

```bash
# See summary
python analyze_logs.py summary

# See common errors
python analyze_logs.py errors

# Get recommendations for AI improvement
python analyze_logs.py recommendations

# See unfixed failures
python analyze_logs.py unfixed

# Export everything to JSON
python analyze_logs.py export
```

### 2. REST API

```bash
# Get summary
curl http://localhost:8000/api/logs/summary

# Get error patterns
curl http://localhost:8000/api/logs/error-patterns

# Get recommendations
curl http://localhost:8000/api/logs/recommendations

# Get recent failures
curl http://localhost:8000/api/logs/failures?limit=10

# Get AI learning context
curl http://localhost:8000/api/logs/ai-context
```

### 3. Python API

```python
from backend.script_logger import ScriptLogger
from backend.log_analyzer import LogAnalyzer
import pathlib

logs_dir = pathlib.Path("logs")
logger = ScriptLogger(logs_dir)
analyzer = LogAnalyzer(logs_dir)

# Get summary
analysis = analyzer.analyze_all()
print(analysis["summary"])

# Get unfixed failures
unfixed = logger.get_unfixed_failures()
print(f"Found {len(unfixed)} unfixed failures")

# Get AI context for improving scripts
context = analyzer.generate_context_for_ai(max_examples=5)
print(context)
```

## Example Workflow

### Initial Script Fails

```
User: "Apply Gaussian blur to the image"
AI: <generates script>
Result: ERROR - ImportError: No module named 'cv2'

System automatically logs:
  - log_id: "fail-abc-123"
  - session_id: "session-xyz"
  - error_category: "import_error"
  - error_message: "No module named 'cv2'"
  - code: <the failing script>
```

### User Requests Fix

```
User: "Fix the error"
AI: <generates corrected script using skimage instead>
Result: SUCCESS!

System automatically logs:
  - log_id: "success-def-456"
  - session_id: "session-xyz" (same session!)
  - previous_attempt_id: "fail-abc-123"
  - Marks fail-abc-123 as fixed_by: "success-def-456"
```

### AI Learns

Next time someone asks for blur:
- AI sees that `cv2` caused import errors
- System context includes: "DON'T use cv2, use skimage instead"
- Script works on first try! ✅

## Check Your Success Rate

```bash
python analyze_logs.py summary
```

Output:
```
======================================================================
                  SCRIPT EXECUTION SUMMARY
======================================================================

Total Failures:            42
Total Successes:           38
Unfixed Failures:           3
Fixed Failures:            39

Overall Success Rate:    47.5%
Recent Success (7d):     85.0%  ← Improving!
Recent Attempts (7d):      20
```

## What Gets Logged?

### For Failures
- Python code
- Error message
- Full stderr
- Return code
- User's original request
- Which AI model generated it
- Session/attempt linking

### For Successes
- Python code
- Output files created
- Execution time
- Session/attempt linking
- Links to previous failures it fixed

## Viewing Specific Sessions

A "session" is a group of related attempts. Example:

```bash
python analyze_logs.py session session-xyz-123
```

Shows:
```
======================================================================
                   SESSION: session-xyz-123
======================================================================

Created: 2025-12-16T10:30:00
Status: RESOLVED
Resolved: 2025-12-16T10:32:15
Attempts: 3

Attempt History:
----------------------------------------------------------------------
1. ✗ FAILED
   Log ID: fail-abc-123
   Time: 2025-12-16 10:30:00
   Error: ModuleNotFoundError: No module named 'cv2'

2. ✗ FAILED
   Log ID: fail-abc-124
   Time: 2025-12-16 10:31:00
   Error: NameError: name 'gaussian_filter' is not defined

3. ✓ SUCCESS
   Log ID: success-def-456
   Time: 2025-12-16 10:32:15
   Output: result.png, blurred_image.png
```

## Get AI Recommendations

```bash
python analyze_logs.py recommendations
```

Output:
```
======================================================================
              RECOMMENDATIONS FOR IMPROVEMENT
======================================================================

1. HIGH PRIORITY: 15 import errors detected. Ensure system_context 
   clearly lists ALL available libraries and emphasizes NEVER 
   importing unavailable libraries.

2. MEDIUM PRIORITY: 8 data access errors. Emphasize in system_context: 
   use STRING keys for ImageFileNames and PreparedImages 
   (e.g., ['0'] not [0]).

3. CRITICAL: Multiple stdin parsing errors detected. Emphasize in 
   system_context: ALWAYS use FromStdIn() or FromJson() methods, 
   detect RequestType first, use STRING keys.
```

These recommendations help you:
- Update the AI's system context
- Add examples to documentation
- Train the AI better

## Log File Locations

```
logs/
├── failures/2025-12-16/
│   ├── fail-abc-123.json
│   └── fail-abc-124.json
├── successes/2025-12-16/
│   └── success-def-456.json
├── sessions/
│   └── session-xyz-123.json
└── analysis/
    └── latest_analysis.json
```

## Tips

1. **Check logs regularly** to see if success rate is improving
2. **Review unfixed failures** to identify stubborn issues
3. **Export analysis** before making system_context changes
4. **Track sessions** to understand how failures get fixed
5. **Use recommendations** to guide AI training improvements

## Common Commands

```bash
# Daily check
python analyze_logs.py summary

# Weekly review
python analyze_logs.py all > weekly_report.txt

# Before updating system_context
python analyze_logs.py export system_context_analysis.json
python analyze_logs.py recommendations

# Debugging specific issue
python analyze_logs.py unfixed
python analyze_logs.py session <session-id>
```

## What Makes This Powerful?

1. **Automatic Learning** - No manual tracking needed
2. **Pattern Detection** - Identifies common mistakes automatically
3. **Fix Tracking** - Knows what solutions worked
4. **AI Integration** - Feeds learnings back to the AI
5. **Measurable Progress** - Track success rate over time

## Next Steps

1. Run some scripts and let failures happen (they're logged!)
2. Check `python analyze_logs.py summary` after a few runs
3. Review `python analyze_logs.py errors` to see patterns
4. Use `python analyze_logs.py recommendations` to improve the AI
5. Watch your success rate go up! 📈

For full documentation, see `LOGGING_SYSTEM.md`.






