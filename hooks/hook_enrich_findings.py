#!/usr/bin/env python3
"""
SubagentStop hook: Enriches task findings with timestamps and token counts
ENHANCED: Uses explicit placeholders (TIMESTAMP_PH, TOKEN_COUNT_PH)
Runs after subagent completes, before returning to orchestrator
"""

import sys
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import tiktoken

# Placeholder constants
TIMESTAMP_PLACEHOLDER = "TIMESTAMP_PH"
TOKEN_COUNT_PLACEHOLDER = "TOKEN_COUNT_PH"

def count_tokens(text, model="cl100k_base"):
    """Count tokens in text using tiktoken"""
    try:
        encoding = tiktoken.get_encoding(model)
        return len(encoding.encode(str(text)))
    except Exception as e:
        print(f"[Hook] Error counting tokens: {e}", file=sys.stderr)
        return 0

def has_placeholders(finding):
    """Check if finding has placeholder values that need replacement"""
    if not isinstance(finding, dict):
        return False
    
    timestamp = finding.get('timestamp')
    token_count = finding.get('token_count')
    
    # Check for placeholder strings
    has_timestamp_ph = timestamp == TIMESTAMP_PLACEHOLDER
    has_token_count_ph = token_count == TOKEN_COUNT_PLACEHOLDER
    
    return has_timestamp_ph or has_token_count_ph

def validate_finding_structure(finding, finding_id):
    """Check if finding has correct structure and placeholders"""
    issues = []
    
    # Check if it's a string instead of object
    if isinstance(finding, str):
        issues.append("Finding is a string, not an object - CRITICAL ERROR")
        return issues
    
    if not isinstance(finding, dict):
        issues.append(f"Finding is type {type(finding)}, not dict - CRITICAL ERROR")
        return issues
    
    # Check for required fields
    required = ['id', 'agent', 'phase', 'category', 'confidence', 'content']
    missing = [f for f in required if f not in finding]
    if missing:
        issues.append(f"Missing required fields: {missing}")
    
    # Check if agent used placeholders correctly
    timestamp = finding.get('timestamp')
    token_count = finding.get('token_count')
    
    # Warn if agent tried to add real values instead of placeholders
    if timestamp and timestamp != TIMESTAMP_PLACEHOLDER:
        # Check if it looks like a real timestamp (has microseconds)
        if re.search(r'\.\d{6}', str(timestamp)):
            issues.append(f"Agent added real timestamp instead of placeholder '{TIMESTAMP_PLACEHOLDER}'")
        elif timestamp not in [None, ""]:
            issues.append(f"Agent added invalid timestamp: {timestamp} (should use '{TIMESTAMP_PLACEHOLDER}')")
    
    if token_count and token_count != TOKEN_COUNT_PLACEHOLDER:
        if isinstance(token_count, (int, float)) and token_count == 0:
            issues.append(f"Agent added token_count=0 (should use '{TOKEN_COUNT_PLACEHOLDER}')")
        elif isinstance(token_count, (int, float)) and token_count > 0:
            issues.append(f"Agent calculated token_count={token_count} (should use '{TOKEN_COUNT_PLACEHOLDER}')")
    
    return issues

def repair_finding(finding, finding_index, current_time):
    """Repair malformed finding by adding missing fields"""
    if not isinstance(finding, dict):
        print(f"[Hook] Cannot repair finding #{finding_index}: not a dict", file=sys.stderr)
        return None
    
    repaired = False
    
    # Add missing required fields
    if 'id' not in finding:
        finding['id'] = f"F-{finding_index:03d}"
        print(f"[Hook] Added missing ID: F-{finding_index:03d}", file=sys.stderr)
        repaired = True
    
    if 'category' not in finding:
        finding['category'] = 'unknown'
        print(f"[Hook] Added missing category: unknown", file=sys.stderr)
        repaired = True
    
    if 'confidence' not in finding:
        finding['confidence'] = 0.5
        print(f"[Hook] Added missing confidence: 0.5", file=sys.stderr)
        repaired = True
    
    if 'content' not in finding:
        finding['content'] = {}
        print(f"[Hook] Added empty content object", file=sys.stderr)
        repaired = True
    
    # Ensure arrays exist
    if 'dependencies' not in finding:
        finding['dependencies'] = []
    if 'validates' not in finding:
        finding['validates'] = []
    if 'tags' not in finding:
        finding['tags'] = []
    
    # Add placeholders if missing (for backwards compatibility)
    if 'timestamp' not in finding:
        finding['timestamp'] = TIMESTAMP_PLACEHOLDER
        repaired = True
    
    if 'token_count' not in finding:
        finding['token_count'] = TOKEN_COUNT_PLACEHOLDER
        repaired = True
    
    return finding if repaired else finding

def enrich_finding(finding, finding_id, current_time):
    """Replace placeholders with actual values"""
    modified = False
    
    # Replace timestamp placeholder
    if finding.get('timestamp') == TIMESTAMP_PLACEHOLDER:
        finding['timestamp'] = current_time
        modified = True
        print(f"[Hook] Replaced timestamp placeholder for {finding_id}", file=sys.stderr)
    
    # Replace token_count placeholder
    if finding.get('token_count') == TOKEN_COUNT_PLACEHOLDER:
        content_str = json.dumps(finding.get('content', {}))
        finding['token_count'] = count_tokens(content_str)
        modified = True
        print(f"[Hook] Calculated token_count={finding['token_count']} for {finding_id}", file=sys.stderr)
    
    return modified

def parse_transcript(transcript_path):
    """Parse transcript to find modified task files"""
    task_files = set()

    try:
        with open(transcript_path, 'r') as f:
            for line in f:
                entry = json.loads(line)
                tool_name = entry.get('name', '')
                if entry.get('type') == 'tool_use' and tool_name in ['Write', 'Edit', 'Read']:
                    arguments = entry.get('arguments', {})
                    path = arguments.get('file_path', '')
                    if '.claude/tasks/' in path and path.endswith('.json'):
                        task_files.add(path)
                        print(f"[Hook] Found task file via {tool_name}: {path}", file=sys.stderr)
    except Exception as e:
        print(f"[Hook] Error parsing transcript: {e}", file=sys.stderr)

    return task_files

def enrich_task_file(task_file_path):
    """Process task file and replace placeholders with actual values"""
    try:
        # Security: Prevent path traversal
        if '..' in task_file_path:
            print(f"[Hook] SECURITY: Blocked path traversal: {task_file_path}", file=sys.stderr)
            return

        # Security: Only allow .claude/tasks/ files
        if '.claude/tasks/' not in task_file_path or not task_file_path.endswith('.json'):
            print(f"[Hook] SECURITY: Blocked non-task file: {task_file_path}", file=sys.stderr)
            return

        # Read task file
        with open(task_file_path, 'r') as f:
            task = json.load(f)
        
        modified = False
        current_time = datetime.now(ZoneInfo('America/New_York')).isoformat()
        task_id = task.get('task_id', 'UNKNOWN')
        
        print(f"[Hook] Processing {task_id}", file=sys.stderr)

        # Process findings in knowledge_pool
        if 'knowledge_pool' in task and 'findings' in task['knowledge_pool']:
            findings = task['knowledge_pool']['findings']
            valid_findings = []
            findings_with_placeholders = 0
            
            for i, finding in enumerate(findings):
                finding_id = finding.get('id', f'F-{i+1}') if isinstance(finding, dict) else f'F-{i+1}'
                
                # Check if this finding has placeholders
                if not has_placeholders(finding):
                    # No placeholders - already processed or old format
                    # Validate structure but skip enrichment
                    validation_issues = validate_finding_structure(finding, finding_id)
                    if validation_issues:
                        print(f"[Hook] WARNING: {finding_id} has issues but no placeholders:", file=sys.stderr)
                        for issue in validation_issues:
                            print(f"  - {issue}", file=sys.stderr)
                    
                    valid_findings.append(finding)
                    continue
                
                findings_with_placeholders += 1
                
                # Validate structure
                validation_issues = validate_finding_structure(finding, finding_id)
                if validation_issues:
                    print(f"[Hook] VALIDATION WARNING: {task_id} / {finding_id}:", file=sys.stderr)
                    for issue in validation_issues:
                        print(f"  - {issue}", file=sys.stderr)
                    
                    # Attempt repair
                    if isinstance(finding, dict):
                        repaired_finding = repair_finding(finding, i+1, current_time)
                        if repaired_finding:
                            finding = repaired_finding
                            modified = True
                        else:
                            print(f"[Hook] Skipping finding #{i+1} - cannot repair", file=sys.stderr)
                            continue
                    else:
                        print(f"[Hook] Skipping finding #{i+1} - not a dict", file=sys.stderr)
                        continue
                
                # Enrich finding by replacing placeholders
                if enrich_finding(finding, finding_id, current_time):
                    modified = True
                
                valid_findings.append(finding)
            
            # Update findings list
            if len(valid_findings) != len(findings):
                task['knowledge_pool']['findings'] = valid_findings
                modified = True
                print(f"[Hook] Removed {len(findings) - len(valid_findings)} invalid findings", file=sys.stderr)
            
            if findings_with_placeholders > 0:
                print(f"[Hook] Processed {findings_with_placeholders} findings with placeholders in knowledge_pool", file=sys.stderr)
            else:
                print(f"[Hook] No findings with placeholders found in knowledge_pool", file=sys.stderr)

        # Process design_findings (top-level array created by some agents)
        if 'design_findings' in task:
            design_findings = task['design_findings']
            valid_design_findings = []
            design_findings_with_placeholders = 0

            print(f"[Hook] Found design_findings array with {len(design_findings)} items", file=sys.stderr)

            for i, finding in enumerate(design_findings):
                finding_id = finding.get('id', f'D-{i+1}') if isinstance(finding, dict) else f'D-{i+1}'

                # Check if this finding has placeholders
                if not has_placeholders(finding):
                    valid_design_findings.append(finding)
                    continue

                design_findings_with_placeholders += 1

                # Validate structure
                validation_issues = validate_finding_structure(finding, finding_id)
                if validation_issues:
                    print(f"[Hook] VALIDATION WARNING: {task_id} / {finding_id}:", file=sys.stderr)
                    for issue in validation_issues:
                        print(f"  - {issue}", file=sys.stderr)

                    # Attempt repair
                    if isinstance(finding, dict):
                        repaired_finding = repair_finding(finding, i+1, current_time)
                        if repaired_finding:
                            finding = repaired_finding
                            modified = True
                        else:
                            print(f"[Hook] Skipping design_finding #{i+1} - cannot repair", file=sys.stderr)
                            continue
                    else:
                        print(f"[Hook] Skipping design_finding #{i+1} - not a dict", file=sys.stderr)
                        continue

                # Enrich finding by replacing placeholders
                if enrich_finding(finding, finding_id, current_time):
                    modified = True

                valid_design_findings.append(finding)

            # Update design_findings list
            if len(valid_design_findings) != len(design_findings):
                task['design_findings'] = valid_design_findings
                modified = True
                print(f"[Hook] Removed {len(design_findings) - len(valid_design_findings)} invalid design_findings", file=sys.stderr)

            if design_findings_with_placeholders > 0:
                print(f"[Hook] Processed {design_findings_with_placeholders} design_findings with placeholders", file=sys.stderr)

        # Process decisions
        if 'knowledge_pool' in task and 'decisions' in task['knowledge_pool']:
            for decision in task['knowledge_pool']['decisions']:
                if decision.get('timestamp') == TIMESTAMP_PLACEHOLDER:
                    decision['timestamp'] = current_time
                    modified = True
                
                if decision.get('resolved_at') == TIMESTAMP_PLACEHOLDER:
                    decision['resolved_at'] = current_time
                    modified = True
        
        # Process blockers
        if 'knowledge_pool' in task and 'blockers' in task['knowledge_pool']:
            for blocker in task['knowledge_pool']['blockers']:
                if blocker.get('timestamp') == TIMESTAMP_PLACEHOLDER:
                    blocker['timestamp'] = current_time
                    modified = True

        # Process implementation_artifacts
        if 'implementation_artifacts' in task:
            artifacts_processed = 0
            for i, artifact in enumerate(task['implementation_artifacts']):
                # Handle both dict and string artifacts
                if isinstance(artifact, dict):
                    # Process dict-style artifacts with placeholders
                    if artifact.get('timestamp') == TIMESTAMP_PLACEHOLDER:
                        artifact['timestamp'] = current_time
                        modified = True
                        artifacts_processed += 1
                        print(f"[Hook] Replaced timestamp in artifact: {artifact.get('path', f'#{i}')}", file=sys.stderr)

                    if artifact.get('token_count') == TOKEN_COUNT_PLACEHOLDER:
                        # Calculate token count from artifact content
                        content_str = json.dumps(artifact.get('content', artifact))
                        artifact['token_count'] = count_tokens(content_str)
                        modified = True
                        artifacts_processed += 1
                        print(f"[Hook] Calculated token_count={artifact['token_count']} for artifact: {artifact.get('path', f'#{i}')}", file=sys.stderr)
                elif isinstance(artifact, str):
                    # String artifacts don't need processing
                    continue
                else:
                    print(f"[Hook] WARNING: Artifact #{i} is type {type(artifact).__name__}, skipping", file=sys.stderr)

            if artifacts_processed > 0:
                print(f"[Hook] Processed {artifacts_processed} implementation_artifacts", file=sys.stderr)

        # Process execution_plan phases - calculate output_tokens from findings
        if 'execution_plan' in task and 'phases' in task['execution_plan']:
            for phase in task['execution_plan']['phases']:
                phase_name = phase.get('name', 'unknown')

                # Check if this phase has TOKEN_COUNT_PH placeholder
                if phase.get('output_tokens') == TOKEN_COUNT_PLACEHOLDER:
                    # Sum token_count from all findings in this phase
                    phase_tokens = 0
                    findings_counted = 0

                    if 'knowledge_pool' in task and 'findings' in task['knowledge_pool']:
                        for finding in task['knowledge_pool']['findings']:
                            if isinstance(finding, dict) and finding.get('phase') == phase_name:
                                token_count = finding.get('token_count', 0)
                                # Only count if token_count is an actual number (not placeholder)
                                if isinstance(token_count, (int, float)):
                                    phase_tokens += token_count
                                    findings_counted += 1

                    phase['output_tokens'] = phase_tokens
                    modified = True
                    print(f"[Hook] Calculated output_tokens={phase_tokens} for {phase_name} phase ({findings_counted} findings)", file=sys.stderr)

        # Update task's updated_at if anything changed
        if modified:
            task['updated_at'] = current_time
            
            # Write back to file
            with open(task_file_path, 'w') as f:
                json.dump(task, f, indent=2)
            
            print(f"[Hook] ✓ Enriched: {task_file_path}", file=sys.stderr)
        else:
            print(f"[Hook] No changes needed for {task_id}", file=sys.stderr)
        
    except Exception as e:
        print(f"[Hook] Error processing {task_file_path}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

def main():
    """Main hook execution"""
    try:
        # Read hook input
        hook_input = json.load(sys.stdin)
        
        print(f"[Hook] SubagentStop triggered", file=sys.stderr)
        
        transcript_path = hook_input.get('transcript_path')
        if not transcript_path:
            print("[Hook] No transcript path provided", file=sys.stderr)
            sys.exit(0)
        
        # Find task files modified in this session
        task_files = parse_transcript(transcript_path)
        
        # Fallback: Check active tasks if none found in transcript
        if not task_files:
            print("[Hook] No task files in transcript, checking active tasks...", file=sys.stderr)
            active_dir = Path(__file__).parent.parent / 'tasks' / 'active'
            if active_dir.exists():
                task_files = {str(p) for p in active_dir.glob('*.json')}
                print(f"[Hook] Found {len(task_files)} active task files", file=sys.stderr)
        
        # Process each task file
        for task_file in task_files:
            if Path(task_file).exists():
                enrich_task_file(task_file)
        
        print(f"[Hook] Processing complete, checked {len(task_files)} files", file=sys.stderr)
        sys.exit(0)
        
    except Exception as e:
        print(f"[Hook] ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(0)  # Don't block on errors

if __name__ == "__main__":
    main()