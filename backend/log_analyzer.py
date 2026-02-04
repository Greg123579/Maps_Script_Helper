"""
Log Analysis Module

Analyzes script execution logs to identify patterns, common errors, and insights
for improving the AI's script generation. Provides:
- Error pattern detection
- Common failure reasons
- Successful fix strategies
- AI-readable summaries for improving system_context
"""

import json
import pathlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import re


class LogAnalyzer:
    """Analyzes script execution logs to identify patterns and insights"""
    
    def __init__(self, logs_dir: pathlib.Path):
        self.logs_dir = logs_dir
        self.failures_dir = logs_dir / "failures"
        self.successes_dir = logs_dir / "successes"
        self.sessions_dir = logs_dir / "sessions"
        self.analysis_dir = logs_dir / "analysis"
    
    def analyze_all(self) -> Dict[str, Any]:
        """
        Run complete analysis on all logs
        
        Returns comprehensive analysis including:
        - Error patterns
        - Success rates
        - Common fixes
        - Recommendations for system_context
        """
        analysis = {
            "generated_at": datetime.now().isoformat(),
            "summary": self._generate_summary(),
            "error_patterns": self._analyze_error_patterns(),
            "common_errors": self._find_common_errors(),
            "fix_strategies": self._analyze_fix_strategies(),
            "library_issues": self._analyze_library_issues(),
            "mapbridge_issues": self._analyze_mapbridge_issues(),
            "recommendations": self._generate_recommendations(),
            "ai_learning_summary": self._generate_ai_summary()
        }
        
        # Save analysis
        analysis_file = self.analysis_dir / "latest_analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        return analysis
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate high-level statistics"""
        total_failures = sum(1 for _ in self._iter_all_failures())
        total_successes = sum(1 for _ in self._iter_all_successes())
        unfixed_failures = sum(1 for f in self._iter_all_failures() if not f.get("fixed_by"))
        
        # Calculate success rate over last 7 days
        recent_failures = list(self._iter_failures_since(days=7))
        recent_successes = list(self._iter_successes_since(days=7))
        recent_total = len(recent_failures) + len(recent_successes)
        recent_success_rate = (
            len(recent_successes) / recent_total * 100 
            if recent_total > 0 else 0
        )
        
        return {
            "total_failures": total_failures,
            "total_successes": total_successes,
            "unfixed_failures": unfixed_failures,
            "fixed_failures": total_failures - unfixed_failures,
            "overall_success_rate": (
                total_successes / (total_failures + total_successes) * 100
                if (total_failures + total_successes) > 0 else 0
            ),
            "recent_success_rate_7d": recent_success_rate,
            "recent_attempts_7d": recent_total
        }
    
    def _analyze_error_patterns(self) -> List[Dict[str, Any]]:
        """Identify most common error patterns"""
        error_categories = Counter()
        error_types = Counter()
        error_examples = defaultdict(list)
        
        for failure in self._iter_all_failures():
            category = failure.get("error_category", "unknown")
            error_type = failure.get("error_type", "unknown")
            
            error_categories[category] += 1
            error_types[error_type] += 1
            
            # Store example for each category (up to 3)
            if len(error_examples[category]) < 3:
                error_examples[category].append({
                    "log_id": failure["log_id"],
                    "error_message": failure.get("error_message", "")[:200],
                    "timestamp": failure["timestamp"],
                    "fixed": bool(failure.get("fixed_by"))
                })
        
        patterns = []
        for category, count in error_categories.most_common(10):
            patterns.append({
                "category": category,
                "count": count,
                "examples": error_examples[category]
            })
        
        return patterns
    
    def _find_common_errors(self) -> List[Dict[str, Any]]:
        """Find most common specific error messages"""
        error_messages = Counter()
        error_details = {}
        
        for failure in self._iter_all_failures():
            # Extract first line of error message for grouping
            error_msg = failure.get("error_message", "")
            stderr = failure.get("stderr", "")
            
            # Try to extract the actual error line
            key_error = self._extract_key_error(error_msg, stderr)
            
            if key_error:
                error_messages[key_error] += 1
                
                if key_error not in error_details:
                    error_details[key_error] = {
                        "error": key_error,
                        "count": 0,
                        "fixed_count": 0,
                        "examples": []
                    }
                
                error_details[key_error]["count"] += 1
                if failure.get("fixed_by"):
                    error_details[key_error]["fixed_count"] += 1
                
                if len(error_details[key_error]["examples"]) < 2:
                    error_details[key_error]["examples"].append({
                        "log_id": failure["log_id"],
                        "session_id": failure["session_id"],
                        "fixed": bool(failure.get("fixed_by"))
                    })
        
        common_errors = []
        for error, count in error_messages.most_common(15):
            details = error_details[error]
            details["fix_rate"] = (
                details["fixed_count"] / details["count"] * 100
                if details["count"] > 0 else 0
            )
            common_errors.append(details)
        
        return common_errors
    
    def _analyze_fix_strategies(self) -> List[Dict[str, Any]]:
        """Analyze how failures were fixed"""
        fix_strategies = []
        
        # Find failures that were fixed
        for failure in self._iter_all_failures():
            if not failure.get("fixed_by"):
                continue
            
            success_id = failure["fixed_by"]
            success = self._get_log_by_id(success_id)
            
            if not success:
                continue
            
            # Analyze what changed
            changes = self._analyze_code_changes(
                failure["code"],
                success["code"]
            )
            
            fix_strategies.append({
                "failure_id": failure["log_id"],
                "success_id": success_id,
                "error_category": failure.get("error_category"),
                "error_type": failure.get("error_type"),
                "changes": changes,
                "timestamp": success["timestamp"]
            })
        
        # Group by error type to find common fixes
        fixes_by_error = defaultdict(list)
        for fix in fix_strategies:
            error_type = fix.get("error_category", "unknown")
            fixes_by_error[error_type].append(fix["changes"])
        
        common_fixes = []
        for error_type, fixes_list in fixes_by_error.items():
            # Find common patterns in fixes
            all_changes = []
            for fixes in fixes_list:
                all_changes.extend(fixes.get("added_imports", []))
                all_changes.extend(fixes.get("removed_imports", []))
            
            if all_changes:
                common_fixes.append({
                    "error_type": error_type,
                    "fix_count": len(fixes_list),
                    "common_changes": Counter(all_changes).most_common(5)
                })
        
        return common_fixes
    
    def _analyze_library_issues(self) -> Dict[str, Any]:
        """Analyze issues related to specific libraries"""
        library_errors = defaultdict(lambda: {"count": 0, "errors": []})
        
        for failure in self._iter_all_failures():
            code = failure.get("code", "")
            stderr = failure.get("stderr", "")
            error_msg = failure.get("error_message", "")
            
            # Check which libraries are involved
            libraries = ["matplotlib", "numpy", "scipy", "PIL", "skimage", 
                        "cv2", "pandas", "imageio", "MapsBridge"]
            
            for lib in libraries:
                if lib in code or lib in stderr or lib in error_msg:
                    library_errors[lib]["count"] += 1
                    if len(library_errors[lib]["errors"]) < 3:
                        library_errors[lib]["errors"].append({
                            "log_id": failure["log_id"],
                            "error": self._extract_key_error(error_msg, stderr)[:150],
                            "fixed": bool(failure.get("fixed_by"))
                        })
        
        # Sort by count
        sorted_issues = sorted(
            [{"library": lib, **data} for lib, data in library_errors.items()],
            key=lambda x: x["count"],
            reverse=True
        )
        
        return {
            "libraries_with_issues": sorted_issues
        }
    
    def _analyze_mapbridge_issues(self) -> Dict[str, Any]:
        """Analyze MapsBridge-specific issues"""
        mapbridge_errors = {
            "request_type_errors": 0,
            "stdin_parsing_errors": 0,
            "output_errors": 0,
            "channel_errors": 0,
            "other_errors": 0,
            "examples": []
        }
        
        for failure in self._iter_all_failures():
            if "MapsBridge" not in failure.get("code", ""):
                continue
            
            error_msg = failure.get("error_message", "").lower()
            stderr = failure.get("stderr", "").lower()
            error_text = error_msg + " " + stderr
            
            # Categorize MapsBridge errors
            if "stdin" in error_text or "json" in error_text:
                mapbridge_errors["stdin_parsing_errors"] += 1
                category = "stdin_parsing"
            elif "requesttype" in error_text or "tileset" in error_text or "imagelayer" in error_text:
                mapbridge_errors["request_type_errors"] += 1
                category = "request_type"
            elif "channel" in error_text or "createchannel" in error_text:
                mapbridge_errors["channel_errors"] += 1
                category = "channel"
            elif "output" in error_text or "sendsingletileoutput" in error_text:
                mapbridge_errors["output_errors"] += 1
                category = "output"
            else:
                mapbridge_errors["other_errors"] += 1
                category = "other"
            
            # Store examples
            if len(mapbridge_errors["examples"]) < 10:
                mapbridge_errors["examples"].append({
                    "log_id": failure["log_id"],
                    "category": category,
                    "error": self._extract_key_error(error_msg, stderr)[:150],
                    "fixed": bool(failure.get("fixed_by"))
                })
        
        return mapbridge_errors
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for improving system_context"""
        recommendations = []
        
        # Analyze error patterns
        error_patterns = self._analyze_error_patterns()
        common_errors = self._find_common_errors()
        
        # Top 3 error categories
        if error_patterns:
            top_errors = error_patterns[:3]
            for pattern in top_errors:
                category = pattern["category"]
                count = pattern["count"]
                
                if category == "import_error":
                    recommendations.append(
                        f"HIGH PRIORITY: {count} import errors detected. "
                        "Ensure system_context clearly lists ALL available libraries "
                        "and emphasizes NEVER importing unavailable libraries."
                    )
                elif category == "attribute_error":
                    recommendations.append(
                        f"MEDIUM PRIORITY: {count} attribute errors detected. "
                        "Review MapsBridge API documentation in system_context. "
                        "Ensure all examples use correct attribute names."
                    )
                elif category == "data_access_error":
                    recommendations.append(
                        f"MEDIUM PRIORITY: {count} data access errors. "
                        "Emphasize in system_context: use STRING keys for ImageFileNames "
                        "and PreparedImages (e.g., ['0'] not [0])."
                    )
        
        # Analyze library issues
        library_issues = self._analyze_library_issues()
        if library_issues["libraries_with_issues"]:
            top_lib = library_issues["libraries_with_issues"][0]
            recommendations.append(
                f"LIBRARY ISSUE: {top_lib['library']} has {top_lib['count']} errors. "
                f"Review usage patterns and add specific examples to system_context."
            )
        
        # MapsBridge issues
        mapbridge_issues = self._analyze_mapbridge_issues()
        if mapbridge_issues["stdin_parsing_errors"] > 5:
            recommendations.append(
                "CRITICAL: Multiple stdin parsing errors detected. "
                "Emphasize in system_context: ALWAYS use FromStdIn() or FromJson() "
                "methods, detect RequestType first, use STRING keys."
            )
        
        return recommendations
    
    def _generate_ai_summary(self) -> str:
        """
        Generate a concise summary for AI to understand common issues
        
        This summary can be included in the system_context or provided
        to the AI when generating scripts.
        """
        summary = []
        summary.append("=== SCRIPT GENERATION LEARNINGS FROM EXECUTION LOGS ===\n")
        
        # Top errors
        common_errors = self._find_common_errors()
        if common_errors:
            summary.append("MOST COMMON ERRORS TO AVOID:")
            for i, error in enumerate(common_errors[:5], 1):
                fix_rate = error["fix_rate"]
                summary.append(
                    f"{i}. {error['error']} "
                    f"({error['count']} occurrences, {fix_rate:.0f}% fixed)"
                )
            summary.append("")
        
        # Library issues
        library_issues = self._analyze_library_issues()
        if library_issues["libraries_with_issues"]:
            summary.append("LIBRARY-SPECIFIC ISSUES:")
            for lib_issue in library_issues["libraries_with_issues"][:5]:
                summary.append(
                    f"- {lib_issue['library']}: {lib_issue['count']} errors"
                )
            summary.append("")
        
        # Recommendations
        recommendations = self._generate_recommendations()
        if recommendations:
            summary.append("RECOMMENDATIONS FOR SYSTEM_CONTEXT:")
            for rec in recommendations[:5]:
                summary.append(f"- {rec}")
            summary.append("")
        
        # Success patterns
        fix_strategies = self._analyze_fix_strategies()
        if fix_strategies:
            summary.append("SUCCESSFUL FIX PATTERNS:")
            for i, fix in enumerate(fix_strategies[:3], 1):
                summary.append(
                    f"{i}. {fix['error_category']} errors fixed by: "
                    f"{', '.join(fix['changes'].get('summary', ['code revision']))}"
                )
            summary.append("")
        
        summary.append("=== END LEARNINGS ===")
        
        return "\n".join(summary)
    
    # Helper methods
    
    def _iter_all_failures(self):
        """Iterate over all failure logs"""
        if not self.failures_dir.exists():
            return
        for date_dir in self.failures_dir.iterdir():
            if not date_dir.is_dir():
                continue
            for log_file in date_dir.glob("*.json"):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        yield json.load(f)
                except Exception as e:
                    print(f"Warning: Could not load log file {log_file}: {e}")
    
    def _iter_all_successes(self):
        """Iterate over all success logs"""
        if not self.successes_dir.exists():
            return
        for date_dir in self.successes_dir.iterdir():
            if not date_dir.is_dir():
                continue
            for log_file in date_dir.glob("*.json"):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        yield json.load(f)
                except Exception as e:
                    print(f"Warning: Could not load log file {log_file}: {e}")
    
    def _iter_failures_since(self, days: int):
        """Iterate over failures from the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for failure in self._iter_all_failures():
            timestamp = datetime.fromisoformat(failure["timestamp"])
            if timestamp >= cutoff_date:
                yield failure
    
    def _iter_successes_since(self, days: int):
        """Iterate over successes from the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for success in self._iter_all_successes():
            timestamp = datetime.fromisoformat(success["timestamp"])
            if timestamp >= cutoff_date:
                yield success
    
    def _get_log_by_id(self, log_id: str) -> Optional[Dict[str, Any]]:
        """Get a log entry by ID"""
        for base_dir in [self.failures_dir, self.successes_dir]:
            for date_dir in base_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                log_file = date_dir / f"{log_id}.json"
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
        return None
    
    def _extract_key_error(self, error_message: str, stderr: str) -> str:
        """Extract the key error message for grouping"""
        # Try to find the actual error line in stderr
        if stderr:
            lines = stderr.strip().split('\n')
            for line in reversed(lines):
                # Look for Python exception lines
                if re.match(r'\w+Error:', line) or re.match(r'\w+Exception:', line):
                    return line.strip()[:200]
        
        # Fall back to error_message
        if error_message:
            return error_message.strip()[:200]
        
        return "Unknown error"
    
    def _analyze_code_changes(self, old_code: str, new_code: str) -> Dict[str, Any]:
        """Analyze what changed between failed and successful code"""
        changes = {
            "added_imports": [],
            "removed_imports": [],
            "added_functions": [],
            "summary": []
        }
        
        # Extract imports
        old_imports = set(re.findall(r'^(?:import|from)\s+(\S+)', old_code, re.MULTILINE))
        new_imports = set(re.findall(r'^(?:import|from)\s+(\S+)', new_code, re.MULTILINE))
        
        changes["added_imports"] = list(new_imports - old_imports)
        changes["removed_imports"] = list(old_imports - new_imports)
        
        # Generate summary
        if changes["added_imports"]:
            changes["summary"].append(f"Added imports: {', '.join(changes['added_imports'])}")
        if changes["removed_imports"]:
            changes["summary"].append(f"Removed imports: {', '.join(changes['removed_imports'])}")
        
        # Check for structural changes
        if "def " in new_code and "def " not in old_code:
            changes["summary"].append("Added function definitions")
        
        if len(new_code) > len(old_code) * 1.5:
            changes["summary"].append("Significant code expansion")
        elif len(new_code) < len(old_code) * 0.5:
            changes["summary"].append("Significant code reduction")
        
        return changes
    
    def generate_context_for_ai(self, max_examples: int = 10) -> str:
        """
        Generate a context string that can be included when prompting the AI
        
        This provides real-world examples of failures to help the AI avoid
        making the same mistakes.
        """
        try:
            context = []
            context.append("## Common Script Errors to Avoid\n")
            context.append("Based on recent script execution failures:\n")
            
            # Get unfixed failures
            unfixed = []
            for failure in self._iter_all_failures():
                if not failure.get("fixed_by"):
                    unfixed.append(failure)
            
            # If no failures yet, return empty string
            if not unfixed:
                return ""
            
            # Sort by timestamp (most recent first)
            unfixed.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Include examples
            for i, failure in enumerate(unfixed[:max_examples], 1):
                context.append(f"\n### Example {i}: {failure.get('error_category', 'unknown')}")
                context.append(f"Error: {failure.get('error_message', 'No message')[:150]}")
                if failure.get("stderr"):
                    stderr_preview = failure["stderr"][:200]
                    context.append(f"Details: {stderr_preview}")
                context.append("")
            
            return "\n".join(context)
        except Exception as e:
            print(f"Warning: Error generating AI context: {e}")
            import traceback
            traceback.print_exc()
            return ""






