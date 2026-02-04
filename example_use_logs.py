"""
Example: Using the Script Logging System Programmatically

This demonstrates how to interact with the logging system from Python code.
"""

import pathlib
import sys

# Add backend to path
sys.path.insert(0, str(pathlib.Path(__file__).parent / "backend"))

from script_logger import ScriptLogger
from log_analyzer import LogAnalyzer


def main():
    """Example usage of logging system"""
    
    # Initialize logger and analyzer
    logs_dir = pathlib.Path(__file__).parent / "logs"
    logger = ScriptLogger(logs_dir)
    analyzer = LogAnalyzer(logs_dir)
    
    print("=" * 70)
    print("SCRIPT LOGGING SYSTEM - EXAMPLE USAGE")
    print("=" * 70)
    print()
    
    # Example 1: Get summary statistics
    print("1. Getting Summary Statistics")
    print("-" * 70)
    analysis = analyzer.analyze_all()
    summary = analysis["summary"]
    
    print(f"Total Failures:       {summary['total_failures']}")
    print(f"Total Successes:      {summary['total_successes']}")
    print(f"Overall Success Rate: {summary['overall_success_rate']:.1f}%")
    print(f"Recent Success (7d):  {summary['recent_success_rate_7d']:.1f}%")
    print()
    
    # Example 2: Get recent failures
    print("2. Getting Recent Failures")
    print("-" * 70)
    recent_failures = logger.get_recent_failures(limit=5)
    
    if recent_failures:
        for i, failure in enumerate(recent_failures[:3], 1):
            print(f"{i}. {failure.get('error_category', 'unknown')}")
            print(f"   Error: {failure.get('error_message', 'No message')[:60]}")
            print(f"   Fixed: {'Yes' if failure.get('fixed_by') else 'No'}")
            print()
    else:
        print("No failures logged yet!")
        print()
    
    # Example 3: Get unfixed failures
    print("3. Getting Unfixed Failures")
    print("-" * 70)
    unfixed = logger.get_unfixed_failures()
    
    if unfixed:
        print(f"Found {len(unfixed)} unfixed failure(s):")
        for failure in unfixed[:3]:
            print(f"  - {failure['log_id']}: {failure.get('error_category', 'unknown')}")
    else:
        print("✓ No unfixed failures! All errors have been resolved.")
    print()
    
    # Example 4: Get error patterns
    print("4. Getting Error Patterns")
    print("-" * 70)
    error_patterns = analysis["error_patterns"]
    
    if error_patterns:
        for i, pattern in enumerate(error_patterns[:3], 1):
            print(f"{i}. {pattern['category']} - {pattern['count']} occurrences")
    else:
        print("No error patterns detected yet.")
    print()
    
    # Example 5: Get recommendations
    print("5. Getting Recommendations for AI Improvement")
    print("-" * 70)
    recommendations = analysis["recommendations"]
    
    if recommendations:
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"{i}. {rec[:100]}...")
            print()
    else:
        print("No recommendations at this time!")
        print()
    
    # Example 6: Generate AI context
    print("6. Generating AI Context (for improving script generation)")
    print("-" * 70)
    ai_context = analyzer.generate_context_for_ai(max_examples=3)
    
    if ai_context:
        # Show first 500 chars
        print(ai_context[:500])
        if len(ai_context) > 500:
            print(f"\n... (truncated, total length: {len(ai_context)} chars)")
    else:
        print("No context available yet.")
    print()
    
    # Example 7: Programmatic logging (if you want to log manually)
    print("7. Example: Manual Logging")
    print("-" * 70)
    print("You can also log manually:")
    print()
    print("# Log a failure:")
    print("log_id = logger.log_failure(")
    print("    code='import cv2\\nprint(cv2.__version__)',")
    print("    error_message='ModuleNotFoundError: No module named cv2',")
    print("    stderr='Traceback...\\nModuleNotFoundError...',")
    print("    return_code=1,")
    print("    user_prompt='Show OpenCV version'")
    print(")")
    print()
    print("# Log a success:")
    print("log_id = logger.log_success(")
    print("    code='import skimage\\nprint(skimage.__version__)',")
    print("    output_files=['result.png'],")
    print("    user_prompt='Show skimage version',")
    print("    previous_attempt_id=previous_failure_id")
    print(")")
    print()
    
    # Example 8: Session tracking
    print("8. Example: Session Tracking")
    print("-" * 70)
    print("Sessions group related attempts:")
    print()
    print("# First attempt (creates session)")
    print("session_id = None")
    print()
    print("# Failure 1")
    print("fail_1 = logger.log_failure(...)")
    print("session_id = fail_1  # Use first log_id as session_id")
    print()
    print("# Failure 2 (same session)")
    print("fail_2 = logger.log_failure(..., session_id=session_id,")
    print("                            previous_attempt_id=fail_1)")
    print()
    print("# Success! (same session)")
    print("success = logger.log_success(..., session_id=session_id,")
    print("                             previous_attempt_id=fail_2)")
    print()
    print("# Now you can view the complete journey:")
    print("session = logger.get_session(session_id)")
    print("# Shows: fail_1 -> fail_2 -> success")
    print()
    
    print("=" * 70)
    print("For more information:")
    print("  - Quick Start: LOGGING_QUICKSTART.md")
    print("  - Full Docs:   LOGGING_SYSTEM.md")
    print("  - CLI Tool:    python analyze_logs.py --help")
    print("=" * 70)


if __name__ == "__main__":
    main()






