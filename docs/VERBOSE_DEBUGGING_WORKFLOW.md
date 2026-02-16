# Verbose Debugging Workflow

## Overview

This system implements a **two-stage error handling workflow** that asks users for permission before injecting verbose debugging statements into their scripts.

## Workflow Stages

### Stage 1: First Failure
When a script fails for the **first time**, the user is prompted:

```
"My code failed with an error. Can you help me fix it?"
```

**Quick Reply Options:**
- ✅ **Yes** - Send error details (stderr/stdout) + current code to the AI
- ❌ **No** - Dismiss this prompt

### Stage 2: Second+ Failure (Verbose Debugging)
When a script fails for the **second consecutive time** (or more), the user is prompted:

```
"The script failed again. Can I add debugging statements to help me diagnose it? 
Once I figure out the problem, they will be removed."
```

**Quick Reply Options:**
- 🐛 **Yes, add debugging** - Inject verbose logging to identify the problem
- ❌ **No, I'll fix it** - Dismiss and fix manually

## Technical Implementation

### Frontend Changes (`frontend/app.jsx`)

1. **Added state tracking:**
   ```javascript
   const [consecutiveFailures, setConsecutiveFailures] = useState(0);
   ```

2. **Increments failure counter** on each execution error

3. **Resets counter** on successful execution

4. **Modified `sendErrorToAI()` function** to accept `failureCount` parameter:
   - If `failureCount >= 2`: Shows debug injection prompt
   - If `failureCount === 1`: Shows standard error help prompt

### Backend Changes (`backend/app.py`)

1. **Added `inject_debug` parameter** to `/run` endpoint:
   ```python
   inject_debug: Optional[str] = Form("false")
   ```

2. **Removed automatic debug injection** - now requires explicit user approval

3. **Modified `/api/chat` endpoint** to detect debug approval:
   - Checks for keywords like "yes" + "debug", "add debugging", etc.
   - When approved: Injects debug logging into code
   - Returns code with `[AUTO-DEBUG]` markers

4. **Debug injection functions:**
   - `has_debug_logging(code)` - Checks for existing debug markers
   - `inject_debug_logging(code)` - Adds verbose logging statements
   - `remove_debug_logging(code)` - Cleans up debug statements after success

## Debug Logging Features

When debug logging is injected, the system adds:

### Print Statements for Key Operations:
- After `Image.open()` calls: Shows image mode, size, dtype
- After `cv2.imread()` calls: Shows array shape, dtype
- After `MapsBridge.FromStdIn()`: Shows request type
- After `ResolveSingleTileAndPath()`: Shows tile coordinates, path
- Before `try` blocks: Entry markers
- In `except` blocks: Detailed exception info

### Debug Header:
```python
# ======================================================================
# AUTO-DEBUG MODE ACTIVE
# Diagnostic logging has been automatically injected to help
# identify the issue. This will be removed after successful execution.
# ======================================================================
```

## User Experience Flow

```
┌─────────────────────────────┐
│   1st Execution Fails       │
│                             │
│  "Can you help me fix it?"  │
│   [Yes] [No]                │
└──────────┬──────────────────┘
           │ User: Yes
           │ AI: Analyzes & suggests fix
           ▼
┌─────────────────────────────┐
│   2nd Execution Fails       │
│                             │
│  "Add debugging statements?"│
│   [Yes] [No]                │
└──────────┬──────────────────┘
           │ User: Yes
           │ System: Injects debug logging
           ▼
┌─────────────────────────────┐
│   3rd Execution (Verbose)   │
│                             │
│  [AUTO-DEBUG] Loaded image: │
│  [AUTO-DEBUG] Tile: 0x0     │
│  [AUTO-DEBUG] Exception...  │
└──────────┬──────────────────┘
           │ Detailed logs help AI diagnose
           │ AI: Fixes root cause
           ▼
┌─────────────────────────────┐
│   4th Execution Succeeds    │
│                             │
│  Debug statements removed   │
│  Failure counter reset      │
└─────────────────────────────┘
```

## Benefits

1. **User Control** - Users decide when to enable verbose debugging
2. **Transparency** - Users know what's happening at each stage
3. **Educational** - Users learn from the debugging approach
4. **Clean Code** - Debug statements are temporary and removed on success
5. **Progressive Escalation** - Start simple, add detail only when needed

## Configuration

No configuration needed - the system automatically:
- Tracks consecutive failures per user session
- Prompts at appropriate times
- Injects and removes debug code as needed

## Future Enhancements

Potential improvements:
- [ ] Allow users to customize debug verbosity level
- [ ] Add debug logging templates for specific error types
- [ ] Persist debug preferences per user
- [ ] Add option to keep debug statements permanently
