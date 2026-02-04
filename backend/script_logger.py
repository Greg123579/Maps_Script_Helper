"""
Script Execution Logger

Logs all script execution attempts (failures and successes) to build a knowledge base
for improving AI-generated scripts. Each execution is logged with:
- Script code
- Execution parameters
- Error details (if failed)
- Output details (if successful)
- Relationships between failed attempts and eventual success

This creates a library of examples that the AI can analyze to improve future scripts.
"""

import json
import uuid
import pathlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict


@dataclass
class ScriptExecutionLog:
    """Record of a single script execution attempt"""
    log_id: str  # Unique ID for this log entry
    session_id: str  # Groups related attempts (failures -> success)
    timestamp: str  # ISO format timestamp
    status: str  # "failed" or "success"
    
    # Script details
    code: str
    code_hash: str  # Simple hash to detect duplicate attempts
    
    # Execution context
    user_prompt: Optional[str] = None  # What the user asked for
    ai_model: Optional[str] = None  # Which AI model generated this
    image_filename: Optional[str] = None
    
    # Results
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    stderr: Optional[str] = None
    stdout: Optional[str] = None
    return_code: Optional[int] = None
    
    # For successful runs
    output_files: Optional[List[str]] = None
    execution_time_seconds: Optional[float] = None
    
    # Relationships
    previous_attempt_id: Optional[str] = None  # Link to previous failed attempt
    fixed_by: Optional[str] = None  # If this was a failure, ID of success that fixed it
    
    # Analysis metadata
    error_category: Optional[str] = None  # Categorized error type for analysis
    tags: Optional[List[str]] = None  # Keywords for searching/filtering


class ScriptLogger:
    """Handles logging of script execution attempts"""
    
    def __init__(self, logs_dir: pathlib.Path):
        """
        Initialize logger with base logs directory
        
        Directory structure:
        logs/
            failures/           # Failed execution attempts
                YYYY-MM-DD/     # Organized by date
                    {log_id}.json
            successes/          # Successful executions
                YYYY-MM-DD/
                    {log_id}.json
            sessions/           # Session metadata (groups related attempts)
                {session_id}.json
            analysis/           # Analysis results and patterns
                patterns.json
                common_errors.json
        """
        self.logs_dir = logs_dir
        self.failures_dir = logs_dir / "failures"
        self.successes_dir = logs_dir / "successes"
        self.sessions_dir = logs_dir / "sessions"
        self.analysis_dir = logs_dir / "analysis"
        
        # Create directory structure
        for dir_path in [self.failures_dir, self.successes_dir, 
                        self.sessions_dir, self.analysis_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _get_code_hash(self, code: str) -> str:
        """Generate a simple hash of the code for duplicate detection"""
        import hashlib
        # Normalize whitespace for better matching
        normalized = '\n'.join(line.strip() for line in code.split('\n') if line.strip())
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def _get_date_dir(self, base_dir: pathlib.Path) -> pathlib.Path:
        """Get today's date subdirectory"""
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = base_dir / today
        date_dir.mkdir(parents=True, exist_ok=True)
        return date_dir
    
    def log_failure(
        self,
        code: str,
        error_message: str,
        stderr: str,
        return_code: int,
        session_id: Optional[str] = None,
        user_prompt: Optional[str] = None,
        ai_model: Optional[str] = None,
        image_filename: Optional[str] = None,
        stdout: Optional[str] = None,
        previous_attempt_id: Optional[str] = None,
        error_category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Log a failed script execution
        
        Returns the log_id for linking to future attempts
        """
        log_id = str(uuid.uuid4())
        if not session_id:
            session_id = log_id  # Start new session
        
        # Categorize error if not provided
        if not error_category:
            error_category = self._categorize_error(error_message, stderr)
        
        # Auto-generate tags if not provided
        if not tags:
            tags = self._extract_tags(code, error_message, stderr)
        
        log_entry = ScriptExecutionLog(
            log_id=log_id,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            status="failed",
            code=code,
            code_hash=self._get_code_hash(code),
            user_prompt=user_prompt,
            ai_model=ai_model,
            image_filename=image_filename,
            error_message=error_message,
            error_type=self._extract_error_type(stderr),
            stderr=stderr,
            stdout=stdout,
            return_code=return_code,
            previous_attempt_id=previous_attempt_id,
            error_category=error_category,
            tags=tags
        )
        
        # Save to date-organized directory
        date_dir = self._get_date_dir(self.failures_dir)
        log_file = date_dir / f"{log_id}.json"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(log_entry), f, indent=2, ensure_ascii=False)
        
        # Update session metadata
        self._update_session(session_id, log_id, "failed")
        
        return log_id
    
    def log_success(
        self,
        code: str,
        output_files: List[str],
        session_id: Optional[str] = None,
        user_prompt: Optional[str] = None,
        ai_model: Optional[str] = None,
        image_filename: Optional[str] = None,
        stdout: Optional[str] = None,
        execution_time: Optional[float] = None,
        previous_attempt_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Log a successful script execution
        
        If previous_attempt_id is provided, links this success to the failed attempt(s)
        """
        log_id = str(uuid.uuid4())
        if not session_id:
            session_id = log_id
        
        if not tags:
            tags = self._extract_tags(code, "", "")
        
        log_entry = ScriptExecutionLog(
            log_id=log_id,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            status="success",
            code=code,
            code_hash=self._get_code_hash(code),
            user_prompt=user_prompt,
            ai_model=ai_model,
            image_filename=image_filename,
            output_files=output_files,
            stdout=stdout,
            execution_time_seconds=execution_time,
            previous_attempt_id=previous_attempt_id,
            tags=tags
        )
        
        # Save to date-organized directory
        date_dir = self._get_date_dir(self.successes_dir)
        log_file = date_dir / f"{log_id}.json"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(log_entry), f, indent=2, ensure_ascii=False)
        
        # Update session metadata
        self._update_session(session_id, log_id, "success")
        
        # Mark previous failures as fixed
        if previous_attempt_id:
            self._mark_failure_as_fixed(previous_attempt_id, log_id)
        
        return log_id
    
    def _update_session(self, session_id: str, log_id: str, status: str):
        """Update session metadata with new attempt"""
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
        else:
            session_data = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "attempts": [],
                "status": "in_progress"
            }
        
        session_data["attempts"].append({
            "log_id": log_id,
            "timestamp": datetime.now().isoformat(),
            "status": status
        })
        
        if status == "success":
            session_data["status"] = "resolved"
            session_data["resolved_at"] = datetime.now().isoformat()
        
        session_data["updated_at"] = datetime.now().isoformat()
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    def _mark_failure_as_fixed(self, failure_log_id: str, success_log_id: str):
        """Mark a failure log as fixed by a successful attempt"""
        # Find the failure log file
        for date_dir in self.failures_dir.iterdir():
            if not date_dir.is_dir():
                continue
            failure_file = date_dir / f"{failure_log_id}.json"
            if failure_file.exists():
                with open(failure_file, 'r', encoding='utf-8') as f:
                    failure_data = json.load(f)
                
                failure_data["fixed_by"] = success_log_id
                
                with open(failure_file, 'w', encoding='utf-8') as f:
                    json.dump(failure_data, f, indent=2, ensure_ascii=False)
                break
    
    def _categorize_error(self, error_message: str, stderr: str) -> str:
        """Categorize error type for analysis"""
        error_text = (error_message + " " + stderr).lower()
        
        if "import" in error_text or "modulenotfounderror" in error_text:
            return "import_error"
        elif "attributeerror" in error_text:
            return "attribute_error"
        elif "keyerror" in error_text or "indexerror" in error_text:
            return "data_access_error"
        elif "typeerror" in error_text:
            return "type_error"
        elif "valueerror" in error_text:
            return "value_error"
        elif "filenotfounderror" in error_text or "no such file" in error_text:
            return "file_not_found"
        elif "permission" in error_text or "access" in error_text:
            return "permission_error"
        elif "timeout" in error_text:
            return "timeout"
        elif "memory" in error_text:
            return "memory_error"
        elif "syntax" in error_text:
            return "syntax_error"
        else:
            return "unknown"
    
    def _extract_error_type(self, stderr: str) -> Optional[str]:
        """Extract the Python exception type from stderr"""
        if not stderr:
            return None
        
        # Look for pattern like "ExceptionType: message"
        import re
        match = re.search(r'(\w+Error|\w+Exception):', stderr)
        if match:
            return match.group(1)
        return None
    
    def _extract_tags(self, code: str, error_message: str, stderr: str) -> List[str]:
        """Extract relevant tags from code and errors"""
        tags = []
        
        # Extract library usage
        libraries = [
            "MapsBridge", "numpy", "scipy", "matplotlib", "PIL", 
            "skimage", "cv2", "pandas", "imageio"
        ]
        for lib in libraries:
            if f"import {lib}" in code or f"from {lib}" in code:
                tags.append(f"lib:{lib}")
        
        # Extract MapsBridge patterns
        if "TileSetRequest" in code:
            tags.append("request_type:tileset")
        if "ImageLayerRequest" in code:
            tags.append("request_type:imagelayer")
        if "SendSingleTileOutput" in code:
            tags.append("output:tile")
        if "CreateImageLayer" in code:
            tags.append("output:imagelayer")
        if "CreateChannel" in code:
            tags.append("output:channel")
        
        # Extract error patterns
        if error_message or stderr:
            error_text = (error_message + " " + stderr).lower()
            if "import" in error_text:
                tags.append("error:import")
            if "matplotlib" in error_text:
                tags.append("error:matplotlib")
            if "stdin" in error_text or "json" in error_text:
                tags.append("error:input_parsing")
        
        return tags
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata including all attempts"""
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def get_log(self, log_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific log entry by ID"""
        # Search in both failures and successes
        for base_dir in [self.failures_dir, self.successes_dir]:
            for date_dir in base_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                log_file = date_dir / f"{log_id}.json"
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
        return None
    
    def get_recent_failures(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get most recent failures"""
        failures = []
        
        # Get all failure files sorted by date (newest first)
        for date_dir in sorted(self.failures_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            
            for log_file in sorted(date_dir.glob("*.json"), 
                                  key=lambda f: f.stat().st_mtime, 
                                  reverse=True):
                with open(log_file, 'r', encoding='utf-8') as f:
                    failures.append(json.load(f))
                
                if len(failures) >= limit:
                    return failures
        
        return failures
    
    def get_recent_successes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get most recent successes"""
        successes = []
        
        for date_dir in sorted(self.successes_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            
            for log_file in sorted(date_dir.glob("*.json"),
                                  key=lambda f: f.stat().st_mtime,
                                  reverse=True):
                with open(log_file, 'r', encoding='utf-8') as f:
                    successes.append(json.load(f))
                
                if len(successes) >= limit:
                    return successes
        
        return successes
    
    def get_unfixed_failures(self) -> List[Dict[str, Any]]:
        """Get all failures that haven't been fixed yet"""
        unfixed = []
        
        for date_dir in self.failures_dir.iterdir():
            if not date_dir.is_dir():
                continue
            
            for log_file in date_dir.glob("*.json"):
                with open(log_file, 'r', encoding='utf-8') as f:
                    failure = json.load(f)
                    if not failure.get("fixed_by"):
                        unfixed.append(failure)
        
        return unfixed






