#!/usr/bin/env python3
"""
PostToolUse hook: Phase compression placeholder processing
Responsibility: Replace TIMESTAMP_COMPRESS and TOKENS_CALCULATE placeholders
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

def count_tokens(text):
    """
    Accurately count tokens using tiktoken.
    Falls back to rough estimate if tiktoken unavailable.
    """
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model("gpt-4")
        return len(encoding.encode(text))
    except ImportError:
        # Fallback: rough estimate (1 token ≈ 4 characters)
        return len(text) // 4

def get_current_timestamp():
    """Get current timestamp in Eastern Time"""
    return datetime.now(ZoneInfo('America/New_York')).isoformat()

def replace_timestamp_placeholders(obj, current_time):
    """Recursively replace TIMESTAMP_COMPRESS with actual timestamp"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if value == "TIMESTAMP_COMPRESS":
                obj[key] = current_time
            else:
                replace_timestamp_placeholders(value, current_time)
    elif isinstance(obj, list):
        for item in obj:
            replace_timestamp_placeholders(item, current_time)

def remove_duplicate_phase_compressions(task):
    """
    Remove duplicate empty phase_compressions keys outside of knowledge_pool.
    Returns count of duplicates removed.
    """
    duplicates_removed = 0

    # Check all top-level keys except knowledge_pool
    keys_to_check = [k for k in task.keys() if k != 'knowledge_pool']

    for key in keys_to_check:
        value = task[key]

        # If this is a dict, check if it has phase_compressions
        if isinstance(value, dict):
            if 'phase_compressions' in value:
                # Remove empty or duplicate phase_compressions
                if not value['phase_compressions'] or value['phase_compressions'] == {}:
                    del value['phase_compressions']
                    duplicates_removed += 1
                    print(f"  Removed empty phase_compressions from '{key}'", file=sys.stderr)

            # Recursively check nested dicts
            duplicates_removed += clean_nested_phase_compressions(value)

    return duplicates_removed

def clean_nested_phase_compressions(obj, parent_path=""):
    """Recursively clean phase_compressions from nested structures"""
    removed = 0

    if isinstance(obj, dict):
        # Check if this dict has phase_compressions key
        if 'phase_compressions' in obj:
            if not obj['phase_compressions'] or obj['phase_compressions'] == {}:
                del obj['phase_compressions']
                removed += 1
                print(f"  Removed nested empty phase_compressions at {parent_path}", file=sys.stderr)

        # Recurse into nested dicts
        for key, value in list(obj.items()):
            if isinstance(value, dict):
                removed += clean_nested_phase_compressions(value, f"{parent_path}.{key}")
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        removed += clean_nested_phase_compressions(item, f"{parent_path}.{key}[{i}]")

    return removed

def process_compression_placeholders(task):
    """
    Find phase compressions with TOKENS_CALCULATE placeholders.
    Calculate accurate token counts by:
    1. Summing token_count from findings listed in critical_findings
    2. Counting tokens in the compressed summary
    3. Computing compression ratio
    """
    phase_compressions = task.get('knowledge_pool', {}).get('phase_compressions', {})
    changes_made = False
    
    for phase_name, compression in phase_compressions.items():
        # Check if this compression needs calculation
        if compression.get('original_token_count') != "TOKENS_CALCULATE":
            continue
        
        print(f"[Compression] Processing {phase_name} phase...", file=sys.stderr)
        
        # Get the finding IDs that were compressed
        critical_finding_ids = compression.get('critical_findings', [])
        
        if not critical_finding_ids:
            print(f"  -> Warning: No critical_findings listed, cannot calculate original tokens", 
                  file=sys.stderr)
            compression['original_token_count'] = 0
            compression['compressed_token_count'] = 0
            compression['compression_ratio'] = 0
            changes_made = True
            continue
        
        # Sum up tokens from the ORIGINAL findings (already have accurate counts)
        original_tokens = 0
        findings = task.get('knowledge_pool', {}).get('findings', [])
        found_findings = 0
        
        for finding in findings:
            if finding.get('id') in critical_finding_ids:
                # These findings already have accurate token_count from earlier hook
                finding_tokens = finding.get('token_count', 0)
                original_tokens += finding_tokens
                found_findings += 1
                print(f"    Found {finding.get('id')}: {finding_tokens} tokens", file=sys.stderr)
        
        if found_findings != len(critical_finding_ids):
            print(f"  -> Warning: Found {found_findings}/{len(critical_finding_ids)} critical findings", 
                  file=sys.stderr)
        
        # Count tokens in the NEW compressed summary
        compressed_text = compression.get('summary', '')
        compressed_tokens = count_tokens(compressed_text)
        
        # Calculate ratio
        if compressed_tokens > 0:
            ratio = round(original_tokens / compressed_tokens, 1)
        else:
            ratio = 0
        
        # Replace ALL three TOKENS_CALCULATE placeholders with calculated values
        compression['original_token_count'] = original_tokens
        compression['compressed_token_count'] = compressed_tokens
        compression['compression_ratio'] = ratio
        
        print(f"  -> Calculated: {original_tokens} → {compressed_tokens} tokens ({ratio}x compression)", 
              file=sys.stderr)
        
        changes_made = True
    
    return changes_made

def fix_duplicate_json_keys(json_text):
    """
    Fix duplicate phase_compressions keys in knowledge_pool.
    Python's JSON parser silently overwrites duplicates - the LAST one wins.
    We need to keep the FIRST non-empty one and remove all subsequent ones.

    Strategy: Use regex to remove duplicate phase_compressions within knowledge_pool.
    """
    import re

    # Find all occurrences of "phase_compressions" within knowledge_pool section
    # We'll do this by finding the knowledge_pool section and processing it

    lines = json_text.split('\n')
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

        # Detect exiting knowledge_pool (closing brace at knowledge_pool indent level)
        if in_knowledge_pool:
            current_indent = len(line) - len(line.lstrip())

            # Check if we've exited knowledge_pool
            if current_indent <= knowledge_pool_indent and ('}' in line.strip()):
                in_knowledge_pool = False
                found_phase_compressions = False
                result_lines.append(line)
                continue

        # If we're inside a duplicate block, skip until we exit it
        if in_duplicate_block:
            current_indent = len(line) - len(line.lstrip())

            # If this line is at or before the duplicate block indent and has a closing brace, we're done
            if current_indent <= duplicate_block_indent and '}' in line:
                in_duplicate_block = False
                lines_removed += 1
                # Skip the closing line and trailing comma
                continue
            else:
                # Still inside duplicate block
                lines_removed += 1
                continue

        # Check for phase_compressions within knowledge_pool
        if in_knowledge_pool and '"phase_compressions"' in line:
            if not found_phase_compressions:
                # First occurrence
                if '{}' in line:
                    # Empty - skip it and keep looking
                    print(f"  Skipping empty phase_compressions at line {i+1}", file=sys.stderr)
                    lines_removed += 1
                    continue
                else:
                    # Non-empty first occurrence - keep it
                    found_phase_compressions = True
                    result_lines.append(line)
                    continue
            else:
                # Duplicate occurrence - remove it
                print(f"  Removing duplicate phase_compressions at line {i+1}", file=sys.stderr)
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
        print(f"  Fixed {lines_removed} duplicate phase_compressions lines", file=sys.stderr)

    return '\n'.join(result_lines)

def process_compress_phase(task_path):
    """
    Process compression placeholders in task file
    """
    try:
        # Read raw file content
        with open(task_path) as f:
            raw_content = f.read()

        # Fix duplicate JSON keys before parsing
        fixed_content = fix_duplicate_json_keys(raw_content)

        # Now parse the fixed JSON
        task = json.loads(fixed_content)

        task_id = task.get('task_id', 'UNKNOWN')

        # Quick check: does this file have placeholders?
        task_str = json.dumps(task)
        has_timestamp = "TIMESTAMP_COMPRESS" in task_str
        has_tokens = "TOKENS_CALCULATE" in task_str

        print(f"[Compress Phase] Checking {task_id}", file=sys.stderr)
        print(f"  File size: {len(task_str)} chars", file=sys.stderr)
        print(f"  Has TIMESTAMP_COMPRESS: {has_timestamp}", file=sys.stderr)
        print(f"  Has TOKENS_CALCULATE: {has_tokens}", file=sys.stderr)

        # Debug: Show phase_compressions structure
        phase_compressions = task.get('knowledge_pool', {}).get('phase_compressions', {})

        # Remove duplicate/empty phase_compressions if they exist
        if isinstance(phase_compressions, list):
            print(f"  Warning: phase_compressions is a list, converting to dict", file=sys.stderr)
            phase_compressions = {}
            task['knowledge_pool']['phase_compressions'] = phase_compressions

        # Clean up: Find and remove empty duplicate phase_compressions keys elsewhere in task
        cleaned_duplicates = remove_duplicate_phase_compressions(task)
        duplicates_removed = cleaned_duplicates > 0

        if cleaned_duplicates:
            print(f"  Cleaned {cleaned_duplicates} duplicate phase_compressions keys", file=sys.stderr)

        if phase_compressions:
            print(f"  Found {len(phase_compressions)} phase compressions:", file=sys.stderr)
            for phase_name, compression in phase_compressions.items():
                timestamp_val = compression.get('timestamp', 'N/A')
                token_val = compression.get('original_token_count', 'N/A')
                print(f"    {phase_name}: timestamp={timestamp_val}, tokens={token_val}", file=sys.stderr)
        else:
            print(f"  No phase_compressions found in knowledge_pool", file=sys.stderr)
        
        if not has_timestamp and not has_tokens:
            print(f"  -> Skipped: No compression placeholders found", file=sys.stderr)
            return
        
        current_time = get_current_timestamp()
        changes_made = []
        
        # === HANDLE TIMESTAMP_COMPRESS PLACEHOLDERS ===
        if has_timestamp:
            print(f"[Timestamp] Replacing TIMESTAMP_COMPRESS placeholders...", file=sys.stderr)
            replace_timestamp_placeholders(task, current_time)
            changes_made.append("Replaced TIMESTAMP_COMPRESS placeholders")
        
        # === HANDLE TOKENS_CALCULATE PLACEHOLDERS ===
        if has_tokens:
            print(f"[Compression] Detecting TOKENS_CALCULATE placeholders...", file=sys.stderr)
            if process_compression_placeholders(task):
                changes_made.append("Calculated compression token counts")

        # === CLEAN UP DUPLICATES ===
        if duplicates_removed:
            changes_made.append(f"Removed {cleaned_duplicates} duplicate phase_compressions keys")

        # Save if any changes were made
        if changes_made:
            # Always update the updated_at timestamp when making changes
            task['updated_at'] = current_time
            
            with open(task_path, 'w') as f:
                json.dump(task, f, indent=2)
            
            print(f"[Compress Phase] Successfully processed {task_id}", file=sys.stderr)
            for change in changes_made:
                print(f"  - {change}", file=sys.stderr)
        else:
            print(f"[Compress Phase] No changes needed for {task_id}", file=sys.stderr)
        
    except Exception as e:
        print(f"[Compress Phase] Error processing {task_path}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

def main():
    """Main hook execution"""
    try:
        log_file = '/tmp/hook_compress_phase.log'
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

        print(f"[Compress Phase] PostToolUse hook triggered", file=sys.stderr)
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
            log.write(f"Calling process_compress_phase()...\n")
            log.flush()

        process_compress_phase(file_path)

        with open(log_file, 'a') as log:
            log.write(f"Hook completed successfully\n")
            log.flush()
        
        sys.exit(0)
        
    except Exception as e:
        try:
            log_file = '/tmp/hook_compress_phase.log'
            with open(log_file, 'a') as log:
                log.write(f"ERROR: {e}\n")
                import traceback
                traceback.print_exc(file=log)
                log.flush()
        except:
            pass
        print(f"[Compress Phase] ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()