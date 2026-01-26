# Automation Hooks

Python scripts that power the orchestrator's automation.

## Overview

| Hook | Trigger | Purpose |
|------|---------|---------|
| `hook_enrich_findings.py` | SubagentStop | Add timestamps and token counts |
| `hook_compress_phase.py` | PostToolUse | Compress findings between phases |
| `hook_init_task.py` | PostToolUse | Initialize new task files |
| `hook_validate_task.py` | PreToolUse | Validate task structure |

## Requirements

```bash
pip install tiktoken
```

Or:
```bash
pip install -r requirements.txt
```

## Making Hooks Executable

```bash
chmod +x *.py
```

## How Hooks Work

### Input
Hooks receive JSON via stdin:
```json
{
  "transcript_path": "/path/to/transcript.jsonl",
  "tool_name": "Write",
  "arguments": {...}
}
```

### Output
- Logging to stderr (visible in Claude Code)
- Exit code 0 = success
- Exit code 1 = block action (PreToolUse only)

## Placeholder System

Agents write findings with placeholders:
```json
{
  "timestamp": "TIMESTAMP_PH",
  "token_count": "TOKEN_COUNT_PH"
}
```

`hook_enrich_findings.py` replaces these with actual values.

## Customization

See [docs/hooks.md](../docs/hooks.md) for detailed documentation on modifying or creating custom hooks.
