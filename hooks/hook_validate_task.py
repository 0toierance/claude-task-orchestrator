#!/usr/bin/env python3
"""
PreToolUse hook: Task JSON validation and cleanup
Responsibility: Validate and fix task structure BEFORE Write tool executes
Prevents duplicate keys and structural errors from being written to disk
"""

import sys
import json
import re

def find_duplicate_keys_in_object(obj, path="", duplicates=None):
    """
    Recursively find duplicate keys within the same object.
    Returns dict of {path: [duplicate_key_names]}
    """
    if duplicates is None:
        duplicates = {}

    if isinstance(obj, dict):
        # Check for duplicate keys by converting to/from JSON
        # Python's json.loads silently keeps last duplicate, so we need raw string check
        pass  # This is checked in the raw JSON string

        # Recurse into nested objects
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            find_duplicate_keys_in_object(value, new_path, duplicates)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{path}[{i}]"
            find_duplicate_keys_in_object(item, new_path, duplicates)

    return duplicates

def fix_duplicate_phase_compressions(content):
    """
    Remove duplicate phase_compressions keys within knowledge_pool.
    Keep the FIRST non-empty occurrence, remove all subsequent ones.
    """
    lines = content.split('\n')
    result_lines = []
    in_knowledge_pool = False
    knowledge_pool_indent = 0
    found_phase_compressions = False
    in_duplicate_block = False
    duplicate_block_indent = 0
    lines_removed = 0

    for i, line in enumerate(lines):
        # Detect entering knowledge_pool
        if '"knowledge_pool"' in line:
            in_knowledge_pool = True
            knowledge_pool_indent = len(line) - len(line.lstrip())
            result_lines.append(line)
            continue

        # Detect exiting knowledge_pool
        if in_knowledge_pool:
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= knowledge_pool_indent and '}' in line.strip():
                in_knowledge_pool = False
                found_phase_compressions = False
                result_lines.append(line)
                continue

        # If we're inside a duplicate block, skip until we exit it
        if in_duplicate_block:
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= duplicate_block_indent and '}' in line:
                in_duplicate_block = False
                lines_removed += 1
                print(f"[PreValidate] Removed duplicate phase_compressions closing brace at line {i+1}", file=sys.stderr)
                continue
            else:
                lines_removed += 1
                continue

        # Check for phase_compressions within knowledge_pool
        if in_knowledge_pool and '"phase_compressions"' in line:
            if not found_phase_compressions:
                # First occurrence
                if '{}' in line:
                    # Empty - skip it and keep looking
                    print(f"[PreValidate] Skipping empty phase_compressions at line {i+1}", file=sys.stderr)
                    lines_removed += 1
                    continue
                else:
                    # Non-empty first occurrence - keep it
                    found_phase_compressions = True
                    result_lines.append(line)
                    continue
            else:
                # Duplicate occurrence - remove it
                print(f"[PreValidate] Removing duplicate phase_compressions at line {i+1}", file=sys.stderr)
                current_indent = len(line) - len(line.lstrip())

                if '{}' in line:
                    # Inline empty object - just skip this line
                    lines_removed += 1
                    continue
                else:
                    # Block object - need to skip entire block
                    in_duplicate_block = True
                    duplicate_block_indent = current_indent
                    lines_removed += 1
                    continue

        # Keep all other lines
        result_lines.append(line)

    if lines_removed > 0:
        print(f"[PreValidate] Fixed {lines_removed} duplicate phase_compressions lines", file=sys.stderr)

    return '\n'.join(result_lines)

def validate_and_fix(content):
    """
    Validate and fix task JSON content before writing.
    Returns (fixed_content, was_modified)
    """
    modified = False

    # Check for empty or whitespace-only content
    if not content or not content.strip():
        print(f"[PreValidate] WARNING: Empty content provided, skipping validation", file=sys.stderr)
        return content, False

    # Fix duplicate phase_compressions keys
    fixed_content = fix_duplicate_phase_compressions(content)
    if fixed_content != content:
        modified = True
        content = fixed_content

    # Validate JSON is parseable
    try:
        task = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[PreValidate] ERROR: Invalid JSON - {e}", file=sys.stderr)
        print(f"[PreValidate] Content preview: {content[:200]}...", file=sys.stderr)
        # Return original content - let the Write tool fail with proper error
        return content, False

    # Validate required structure
    if 'knowledge_pool' in task:
        kp = task['knowledge_pool']

        # Ensure phase_compressions is a dict
        if 'phase_compressions' in kp:
            if not isinstance(kp['phase_compressions'], dict):
                print(f"[PreValidate] Fixing phase_compressions type: {type(kp['phase_compressions'])} -> dict", file=sys.stderr)
                kp['phase_compressions'] = {}
                modified = True
        else:
            # Add missing phase_compressions
            kp['phase_compressions'] = {}
            modified = True
            print(f"[PreValidate] Added missing phase_compressions", file=sys.stderr)

        # Ensure other required keys exist
        for key in ['findings', 'decisions', 'blockers']:
            if key not in kp:
                kp[key] = []
                modified = True
                print(f"[PreValidate] Added missing knowledge_pool.{key}", file=sys.stderr)

    if modified:
        # Re-serialize with proper formatting
        content = json.dumps(task, indent=2)
        print(f"[PreValidate] Task structure validated and fixed", file=sys.stderr)

    return content, modified

def main():
    """PreToolUse hook main execution"""
    try:
        # Read hook input from stdin
        hook_input = json.load(sys.stdin)

        tool_name = hook_input.get('tool_name', '')
        tool_input = hook_input.get('tool_input', {})

        print(f"[PreValidate] Hook triggered for tool: {tool_name}", file=sys.stderr)

        # Only process Write tool
        if tool_name != 'Write':
            print(f"[PreValidate] Skipped: Not a Write operation", file=sys.stderr)
            # Return original input unchanged
            print(json.dumps(hook_input))
            sys.exit(0)

        file_path = tool_input.get('file_path', '')
        content = tool_input.get('content', '')

        # Only process task files
        if '.claude/tasks/' not in file_path or not file_path.endswith('.json'):
            print(f"[PreValidate] Skipped: Not a task file", file=sys.stderr)
            print(json.dumps(hook_input))
            sys.exit(0)

        print(f"[PreValidate] Validating task file: {file_path}", file=sys.stderr)
        print(f"[PreValidate] Content length: {len(content)} bytes", file=sys.stderr)

        # Validate and fix content
        fixed_content, was_modified = validate_and_fix(content)

        if was_modified:
            # Update the content in tool_input
            tool_input['content'] = fixed_content
            hook_input['tool_input'] = tool_input
            print(f"[PreValidate] Content fixed and validated", file=sys.stderr)
        else:
            print(f"[PreValidate] No changes needed", file=sys.stderr)

        # Return modified input
        print(json.dumps(hook_input))
        sys.exit(0)

    except Exception as e:
        print(f"[PreValidate] ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Return original input on error
        try:
            print(json.dumps(hook_input))
        except:
            pass
        sys.exit(0)

if __name__ == '__main__':
    main()
