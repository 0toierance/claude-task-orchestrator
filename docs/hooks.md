# Hook System

Understanding the Python automation hooks that power the orchestrator.

## Overview

Hooks are Python scripts that run automatically at specific points in the Claude Code lifecycle:

| Hook | Trigger | Purpose |
|------|---------|---------|
| `hook_enrich_findings.py` | SubagentStop | Add timestamps, calculate token counts |
| `hook_compress_phase.py` | PostToolUse (Write/Edit) | Compress findings between phases |
| `hook_init_task.py` | PostToolUse (Write/Edit) | Initialize new task files |
| `hook_validate_task.py` | PreToolUse (Write) | Validate task file structure |

## Hook Configuration

Hooks are configured in `settings.json`:

```json
{
  "hooks": {
    "SubagentStop": [{
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/hook_enrich_findings.py"
      }]
    }],
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [
        {"type": "command", "command": ".claude/hooks/hook_init_task.py"},
        {"type": "command", "command": ".claude/hooks/hook_compress_phase.py"}
      ]
    }],
    "PreToolUse": [{
      "matcher": "Write",
      "hooks": [{
        "type": "command", "command": ".claude/hooks/hook_validate_task.py"
      }]
    }]
  }
}
```

## Hook Details

### hook_enrich_findings.py

**Trigger**: `SubagentStop` - After any sub-agent completes

**Purpose**: Replace placeholder values with actual data

**What it does**:
1. Reads task file from transcript
2. Finds findings with placeholder values
3. Replaces `"TIMESTAMP_PH"` with actual ISO timestamp
4. Replaces `"TOKEN_COUNT_PH"` with calculated token count (using tiktoken)
5. Saves updated task file

**Placeholder System**:
Agents write findings with placeholders:
```json
{
  "id": "F-001",
  "timestamp": "TIMESTAMP_PH",
  "token_count": "TOKEN_COUNT_PH",
  "content": {...}
}
```

Hook replaces with:
```json
{
  "id": "F-001",
  "timestamp": "2025-01-18T10:30:00.123456-05:00",
  "token_count": 245,
  "content": {...}
}
```

### hook_compress_phase.py

**Trigger**: `PostToolUse` with Write or Edit

**Purpose**: Automatically compress findings when phase advances

**What it does**:
1. Detects phase changes in task file
2. Identifies critical findings (tagged, high-confidence)
3. Generates compressed brief from non-critical findings
4. Stores compression in `phase_compressions`
5. Updates task file

**Compression Logic**:
```python
def compress_findings(findings):
    critical = [f for f in findings if "critical" in f.get("tags", [])]
    non_critical = [f for f in findings if f not in critical]

    brief = summarize(non_critical)  # ~450 tokens

    return {
        "brief": brief,
        "critical_findings": [f["id"] for f in critical[:5]],
        "token_count": count_tokens(brief)
    }
```

### hook_init_task.py

**Trigger**: `PostToolUse` with Write or Edit

**Purpose**: Initialize newly created task files

**What it does**:
1. Detects `_NEEDS_INITIALIZATION` marker in task file
2. Adds `created_at` and `updated_at` timestamps
3. Removes the initialization marker
4. Validates required fields exist

**Marker System**:
New tasks are created with:
```json
{
  "_NEEDS_INITIALIZATION": true,
  "task_id": "TASK-001",
  "created_at": "ISO-8601-TIMESTAMP",
  ...
}
```

Hook transforms to:
```json
{
  "task_id": "TASK-001",
  "created_at": "2025-01-18T10:00:00.000000-05:00",
  "updated_at": "2025-01-18T10:00:00.000000-05:00",
  ...
}
```

### hook_validate_task.py

**Trigger**: `PreToolUse` with Write

**Purpose**: Validate task file structure before writes

**What it does**:
1. Reads the content about to be written
2. If it's a task file, validates JSON structure
3. Checks required fields exist
4. Validates finding structure
5. Blocks write if validation fails

**Validation Checks**:
- Valid JSON syntax
- Required fields: `task_id`, `status`, `current_phase`
- Findings have required structure
- Timestamps are valid format

## Dependencies

All hooks require:
```
tiktoken>=0.5.0
```

Install with:
```bash
pip install -r .claude/hooks/requirements.txt
```

## Hook Input/Output

Hooks receive input via stdin as JSON:

```json
{
  "transcript_path": "/path/to/transcript.jsonl",
  "tool_name": "Write",
  "arguments": {
    "file_path": "/path/to/task.json",
    "content": "..."
  }
}
```

Hooks output to stderr (for logging) and exit with:
- `0` - Success, continue
- `1` - Block the action (for PreToolUse)

## Writing Custom Hooks

### Basic Structure

```python
#!/usr/bin/env python3
import sys
import json

def main():
    # Read hook input
    hook_input = json.load(sys.stdin)

    # Get relevant data
    transcript_path = hook_input.get('transcript_path')

    # Do your processing
    # ...

    # Log to stderr (visible in Claude Code)
    print("[Hook] Processing complete", file=sys.stderr)

    # Exit successfully
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Adding a Custom Hook

1. Create your hook in `.claude/hooks/`:
```bash
touch .claude/hooks/hook_my_custom.py
chmod +x .claude/hooks/hook_my_custom.py
```

2. Add to `settings.json`:
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write",
      "hooks": [
        {"type": "command", "command": ".claude/hooks/hook_my_custom.py"}
      ]
    }]
  }
}
```

## Troubleshooting

### "Hook not executing"
1. Check hook is executable: `chmod +x hooks/*.py`
2. Verify path in settings.json
3. Check Python is available

### "Permission denied"
```bash
chmod +x .claude/hooks/*.py
```

### "tiktoken not found"
```bash
pip install tiktoken
```

### "Hook blocking writes"
Check stderr output in Claude Code for validation errors. Fix the issues or temporarily disable the hook.

### Viewing Hook Output
Hook output goes to stderr. In Claude Code, you'll see messages like:
```
[Hook] Processing TASK-001
[Hook] Replaced timestamp placeholder for F-001
[Hook] Calculated token_count=245 for F-001
[Hook] ✓ Enriched: .claude/tasks/active/TASK-001.json
```

## Security Considerations

Hooks run with your user permissions. They can:
- Read/write files
- Execute commands
- Access network

Only use hooks from trusted sources. Review hook code before enabling.
