#!/usr/bin/env python3
"""
Script Execution Log Analysis CLI

Command-line tool for analyzing script execution logs and identifying patterns.
Useful for:
- Reviewing common errors
- Getting recommendations for system_context improvements
- Tracking success rate over time
- Identifying problematic code patterns

Usage:
    python analyze_logs.py summary          # Show summary statistics
    python analyze_logs.py errors           # Show common error patterns
    python analyze_logs.py recommendations  # Get AI improvement recommendations
    python analyze_logs.py unfixed          # Show unfixed failures
    python analyze_logs.py session <id>     # Show session details
    python analyze_logs.py context          # Generate AI learning context
    python analyze_logs.py export           # Export full analysis to JSON
"""

import sys
import json
import pathlib
from datetime import datetime
from typing import Optional

# Ensure Windows consoles don't crash on unicode output (✓/✗ etc.)
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Add backend to path
sys.path.insert(0, str(pathlib.Path(__file__).parent / "backend"))

from log_analyzer import LogAnalyzer
from script_logger import ScriptLogger


def print_section(title: str, char: str = "="):
    """Print a section header"""
    print(f"\n{char * 70}")
    print(f"{title:^70}")
    print(f"{char * 70}\n")


def print_summary(analyzer: LogAnalyzer):
    """Print summary statistics"""
    print_section("SCRIPT EXECUTION SUMMARY")
    
    analysis = analyzer.analyze_all()
    summary = analysis["summary"]
    
    print(f"Total Failures:       {summary['total_failures']:>6}")
    print(f"Total Successes:      {summary['total_successes']:>6}")
    print(f"Unfixed Failures:     {summary['unfixed_failures']:>6}")
    print(f"Fixed Failures:       {summary['fixed_failures']:>6}")
    print()
    print(f"Overall Success Rate: {summary['overall_success_rate']:>5.1f}%")
    print(f"Recent Success (7d):  {summary['recent_success_rate_7d']:>5.1f}%")
    print(f"Recent Attempts (7d): {summary['recent_attempts_7d']:>6}")
    print()


def print_error_patterns(analyzer: LogAnalyzer):
    """Print common error patterns"""
    print_section("COMMON ERROR PATTERNS")
    
    analysis = analyzer.analyze_all()
    patterns = analysis["error_patterns"]
    
    if not patterns:
        print("No error patterns found.")
        return
    
    for i, pattern in enumerate(patterns[:10], 1):
        print(f"{i}. {pattern['category'].upper().replace('_', ' ')}")
        print(f"   Count: {pattern['count']}")
        print(f"   Examples:")
        for example in pattern['examples'][:2]:
            fixed_status = "FIXED" if example['fixed'] else "UNFIXED"
            print(f"     - {example['error_message'][:80]}... [{fixed_status}]")
        print()


def print_common_errors(analyzer: LogAnalyzer):
    """Print most common specific errors"""
    print_section("MOST COMMON SPECIFIC ERRORS")
    
    analysis = analyzer.analyze_all()
    common_errors = analysis["common_errors"]
    
    if not common_errors:
        print("No common errors found.")
        return
    
    for i, error in enumerate(common_errors[:10], 1):
        fix_rate = error['fix_rate']
        print(f"{i}. {error['error'][:80]}")
        print(f"   Occurrences: {error['count']}  |  Fix Rate: {fix_rate:.0f}%")
        print()


def print_library_issues(analyzer: LogAnalyzer):
    """Print library-specific issues"""
    print_section("LIBRARY-SPECIFIC ISSUES")
    
    analysis = analyzer.analyze_all()
    library_issues = analysis["library_issues"]["libraries_with_issues"]
    
    if not library_issues:
        print("No library issues found.")
        return
    
    for issue in library_issues[:10]:
        print(f"• {issue['library']}")
        print(f"  Errors: {issue['count']}")
        if issue['errors']:
            print(f"  Recent errors:")
            for err in issue['errors'][:2]:
                fixed = "✓" if err['fixed'] else "✗"
                print(f"    [{fixed}] {err['error'][:70]}")
        print()


def print_mapbridge_issues(analyzer: LogAnalyzer):
    """Print MapsBridge-specific issues"""
    print_section("MAPBRIDGE-SPECIFIC ISSUES")
    
    analysis = analyzer.analyze_all()
    mb_issues = analysis["mapbridge_issues"]
    
    print(f"Request Type Errors:    {mb_issues['request_type_errors']}")
    print(f"Stdin Parsing Errors:   {mb_issues['stdin_parsing_errors']}")
    print(f"Output Errors:          {mb_issues['output_errors']}")
    print(f"Channel Errors:         {mb_issues['channel_errors']}")
    print(f"Other Errors:           {mb_issues['other_errors']}")
    print()
    
    if mb_issues['examples']:
        print("Recent Examples:")
        for example in mb_issues['examples'][:5]:
            fixed = "✓" if example['fixed'] else "✗"
            print(f"  [{fixed}] [{example['category']}] {example['error'][:60]}")
        print()


def print_recommendations(analyzer: LogAnalyzer):
    """Print recommendations for improvement"""
    print_section("RECOMMENDATIONS FOR IMPROVEMENT")
    
    analysis = analyzer.analyze_all()
    recommendations = analysis["recommendations"]
    
    if not recommendations:
        print("No recommendations at this time. Great job!")
        return
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
        print()


def print_ai_summary(analyzer: LogAnalyzer):
    """Print AI learning summary"""
    print_section("AI LEARNING SUMMARY")
    
    analysis = analyzer.analyze_all()
    ai_summary = analysis["ai_learning_summary"]
    
    print(ai_summary)
    print()


def print_unfixed_failures(logger: ScriptLogger):
    """Print unfixed failures"""
    print_section("UNFIXED FAILURES")
    
    unfixed = logger.get_unfixed_failures()
    
    if not unfixed:
        print("✓ No unfixed failures! All errors have been resolved.")
        return
    
    # Sort by timestamp (most recent first)
    unfixed.sort(key=lambda x: x["timestamp"], reverse=True)
    
    print(f"Found {len(unfixed)} unfixed failure(s):\n")
    
    for i, failure in enumerate(unfixed[:20], 1):
        timestamp = datetime.fromisoformat(failure["timestamp"])
        age = datetime.now() - timestamp
        
        print(f"{i}. [{failure['error_category']}] {failure.get('error_type', 'Unknown')}")
        print(f"   Log ID: {failure['log_id']}")
        print(f"   Session: {failure['session_id']}")
        print(f"   Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({age.days}d {age.seconds//3600}h ago)")
        print(f"   Error: {failure.get('error_message', 'No message')[:80]}")
        if failure.get('user_prompt'):
            print(f"   Prompt: {failure['user_prompt'][:60]}")
        print()


def print_session(logger: ScriptLogger, session_id: str):
    """Print session details"""
    print_section(f"SESSION: {session_id}")
    
    session = logger.get_session(session_id)
    
    if not session:
        print(f"Session {session_id} not found.")
        return
    
    print(f"Created: {session['created_at']}")
    print(f"Status: {session['status'].upper()}")
    if session.get('resolved_at'):
        print(f"Resolved: {session['resolved_at']}")
    print(f"Attempts: {len(session['attempts'])}")
    print()
    
    print("Attempt History:")
    print("-" * 70)
    
    for i, attempt in enumerate(session['attempts'], 1):
        log_entry = logger.get_log(attempt['log_id'])
        if not log_entry:
            continue
        
        status_symbol = "✓" if log_entry['status'] == 'success' else "✗"
        # Avoid unicode symbols in Windows console
        status_symbol = "OK" if log_entry['status'] == 'success' else "NO"
        timestamp = datetime.fromisoformat(log_entry['timestamp'])
        
        print(f"{i}. {status_symbol} {log_entry['status'].upper()}")
        print(f"   Log ID: {log_entry['log_id']}")
        print(f"   Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if log_entry['status'] == 'failed':
            print(f"   Error: {log_entry.get('error_message', 'No message')[:70]}")
        else:
            print(f"   Output: {', '.join(log_entry.get('output_files', []))}")
        
        print()


def print_context(analyzer: LogAnalyzer, max_examples: int = 10):
    """Print AI context"""
    print_section("AI CONTEXT (For Improving Script Generation)")
    
    context = analyzer.generate_context_for_ai(max_examples=max_examples)
    print(context)
    print()


def export_analysis(analyzer: LogAnalyzer, output_file: str = "analysis_export.json"):
    """Export full analysis to JSON file"""
    print_section("EXPORTING ANALYSIS")
    
    analysis = analyzer.analyze_all()
    
    output_path = pathlib.Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Analysis exported to: {output_path.absolute()}")
    print(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")
    print()


def main():
    """Main CLI entry point"""
    # Setup paths
    base_dir = pathlib.Path(__file__).parent
    logs_dir = base_dir / "logs"
    
    if not logs_dir.exists():
        print(f"Error: Logs directory not found at {logs_dir}")
        print("Have you run any scripts yet?")
        sys.exit(1)
    
    # Initialize analyzer and logger
    analyzer = LogAnalyzer(logs_dir)
    logger = ScriptLogger(logs_dir)
    
    # Parse command
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "summary":
            print_summary(analyzer)
            
        elif command == "errors":
            print_error_patterns(analyzer)
            print_common_errors(analyzer)
            print_library_issues(analyzer)
            print_mapbridge_issues(analyzer)
            
        elif command == "recommendations":
            print_recommendations(analyzer)
            print_ai_summary(analyzer)
            
        elif command == "unfixed":
            print_unfixed_failures(logger)
            
        elif command == "session":
            if len(sys.argv) < 3:
                print("Usage: python analyze_logs.py session <session_id>")
                sys.exit(1)
            session_id = sys.argv[2]
            print_session(logger, session_id)
            
        elif command == "context":
            max_examples = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            print_context(analyzer, max_examples)
            
        elif command == "export":
            output_file = sys.argv[2] if len(sys.argv) > 2 else "analysis_export.json"
            export_analysis(analyzer, output_file)
            
        elif command == "all":
            # Print everything
            print_summary(analyzer)
            print_error_patterns(analyzer)
            print_common_errors(analyzer)
            print_library_issues(analyzer)
            print_mapbridge_issues(analyzer)
            print_recommendations(analyzer)
            print_unfixed_failures(logger)
            
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

