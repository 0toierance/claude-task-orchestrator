#!/usr/bin/env python3
"""
PostToolUse hook: Task initialization only
Responsibility: Initialize new tasks with _NEEDS_INITIALIZATION marker
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

def get_current_timestamp():
    """Get current timestamp in Eastern Time"""
    return datetime.now(ZoneInfo('America/New_York')).isoformat()

def init_task_file(task_path):
    """Initialize task file if it has the initialization marker"""
    try:
        with open(task_path) as f:
            task = json.load(f)
        
        task_id = task.get('task_id', 'UNKNOWN')
        
        # Check for explicit marker
        has_marker = task.get('_NEEDS_INITIALIZATION', False)
        print(f"[Task Init] Checking {task_id}", file=sys.stderr)
        print(f"  Has _NEEDS_INITIALIZATION marker: {has_marker}", file=sys.stderr)
        
        if not has_marker:
            print(f"  -> Skipped: No initialization marker found", file=sys.stderr)
            return
        
        # Remove marker first
        print(f"  -> Marker found - initializing task", file=sys.stderr)
        del task['_NEEDS_INITIALIZATION']

        current_time = get_current_timestamp()
        issues_fixed = []
        
        # Add timestamps
        task['created_at'] = current_time
        task['updated_at'] = current_time
        issues_fixed.append(f"Added timestamps: {current_time}")
        
        # Remove _INSTRUCTIONS if present
        if '_INSTRUCTIONS' in task:
            del task['_INSTRUCTIONS']
            issues_fixed.append("Removed _INSTRUCTIONS section")
        
        # Ensure knowledge_pool exists
        if 'knowledge_pool' not in task:
            task['knowledge_pool'] = {
                'findings': [],
                'phase_compressions': {},
                'decisions': [],
                'blockers': []
            }
            issues_fixed.append("Initialized knowledge_pool")
        
        # Save
        with open(task_path, 'w') as f:
            json.dump(task, f, indent=2)
        
        print(f"[Task Init] Successfully initialized {task_id}", file=sys.stderr)
        for issue in issues_fixed:
            print(f"  - {issue}", file=sys.stderr)
        
    except Exception as e:
        print(f"[Task Init] Error initializing {task_path}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

def main():
    """Main hook execution"""
    try:
        log_file = '/tmp/hook_init_task.log'
        with open(log_file, 'a') as log:
            log.write(f"\n{'='*60}\n")
            log.write(f"Hook invoked at: {get_current_timestamp()}\n")
            log.flush()

        hook_input = json.load(sys.stdin)
        tool_name = hook_input.get('tool_name', '')
        tool_input = hook_input.get('tool_input', {})
        file_path = tool_input.get('file_path', '')

        with open(log_file, 'a') as log:
            log.write(f"Tool: {tool_name}\n")
            log.write(f"File: {file_path}\n")
            log.flush()

        print(f"[Task Init] PostToolUse hook triggered", file=sys.stderr)
        print(f"  Tool: {tool_name}", file=sys.stderr)
        print(f"  File: {file_path}", file=sys.stderr)
        
        # Only Write tool
        if tool_name != 'Write':
            with open(log_file, 'a') as log:
                log.write(f"Skipped: Not a Write operation\n")
            print(f"  -> Skipped: Not a Write operation", file=sys.stderr)
            sys.exit(0)

        # Only task files
        if '.claude/tasks/' not in file_path or not file_path.endswith('.json'):
            with open(log_file, 'a') as log:
                log.write(f"Skipped: Not a task file\n")
            print(f"  -> Skipped: Not a task file", file=sys.stderr)
            sys.exit(0)

        import time

        with open(log_file, 'a') as log:
            log.write(f"Starting file verification...\n")
            log.flush()

        # Wait for file to be fully written
        max_attempts = 5
        for attempt in range(max_attempts):
            time.sleep(0.5)

            if not Path(file_path).exists():
                msg = f"Attempt {attempt + 1}/{max_attempts}: File not found yet"
                with open(log_file, 'a') as log:
                    log.write(f"{msg}\n")
                print(f"  -> {msg}", file=sys.stderr)
                continue

            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if len(content) > 50:
                        msg = f"File verified on attempt {attempt + 1}"
                        with open(log_file, 'a') as log:
                            log.write(f"{msg}\n")
                            log.flush()
                        print(f"  -> {msg}", file=sys.stderr)
                        break
                    else:
                        msg = f"Attempt {attempt + 1}/{max_attempts}: File too small ({len(content)} bytes)"
                        with open(log_file, 'a') as log:
                            log.write(f"{msg}\n")
                        print(f"  -> {msg}", file=sys.stderr)
            except Exception as e:
                msg = f"Attempt {attempt + 1}/{max_attempts}: Read error: {e}"
                with open(log_file, 'a') as log:
                    log.write(f"{msg}\n")
                print(f"  -> {msg}", file=sys.stderr)
        else:
            msg = f"ERROR: File not found or unreadable after {max_attempts} attempts"
            with open(log_file, 'a') as log:
                log.write(f"{msg}\n")
                log.flush()
            print(f"  -> {msg}", file=sys.stderr)
            sys.exit(0)

        with open(log_file, 'a') as log:
            log.write(f"Calling init_task_file()...\n")
            log.flush()

        init_task_file(file_path)

        with open(log_file, 'a') as log:
            log.write(f"Hook completed successfully\n")
            log.flush()
        
        sys.exit(0)
        
    except Exception as e:
        try:
            log_file = '/tmp/hook_init_task.log'
            with open(log_file, 'a') as log:
                log.write(f"ERROR: {e}\n")
                import traceback
                traceback.print_exc(file=log)
                log.flush()
        except:
            pass
        print(f"[Task Init] ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()