---
description: Move task to next phase after completing current phase work
---

# What it does

Validates current phase completion, compresses findings, updates phase status, and dispatches next agent. Always delegate to an agent, never do the work.

## Usage
```
/advance_phase [task_id]
```

**Parameters:**
- `[task_id]` (optional) - Specific task to advance. If omitted, use current active task.

## Orchestrator Process

### 1. Load Task
- If task_id provided: Load that task
- If omitted: Use most recently updated active task
- Verify task is in active/ directory

### 2. Validate Phase Completion
Check current phase prerequisites:

**For ANALYZE → DESIGN:**
- All findings have confidence >0.8
- No pending decisions
- No unresolved blockers

**For DESIGN → IMPLEMENT:**
- All findings have confidence >0.8
- No pending decisions
- No unresolved blockers
- **PLUS:** At least one finding has `implementation_ready: true`

If validation fails, report specific issues and stop.

### 3. Compress Current Phase
Generate compressed brief from current phase findings.

## Eensure no duplicate JSON keys when writing! Specifically phase_compression key** 

## Don't create extra "phase_compressions": {} in the Task, be mindful

**Orchestrator writes the following to `task.knowledge_pool.phase_compressions[current_phase]`:**

```json
{
  "timestamp": "TIMESTAMP_COMPRESS",
  "summary": "[Write your 450-600 token compressed summary here - include key points, critical insights, and context needed for next phase]",
  "critical_findings": ["FIND-001", "FIND-003", "FIND-007"],
  "must_address": [
    "Key item that next phase must handle",
    "Another critical requirement",
    "Important constraint or consideration"
  ],
  "resolved_decisions": [
    "Brief summary of decisions made during this phase"
  ],
  "original_token_count": "TOKENS_CALCULATE",
  "compressed_token_count": "TOKENS_CALCULATE",
  "compression_ratio": "TOKENS_CALCULATE"
}
```

**Orchestrator responsibilities:**
- Write the compressed summary (your cognitive work - be thorough and precise)
- List 3-5 most critical finding IDs in `critical_findings` array
- List must-address items for next phase
- Summarize any decisions that were resolved
- Use exact placeholder strings: `"TIMESTAMP_COMPRESS"` and `"TOKENS_CALCULATE"`

**DO NOT attempt to calculate token counts yourself** - the hook will handle this automatically.

**Hook will automatically:**
- Replace `TIMESTAMP_COMPRESS` with current timestamp
- Sum token counts from the original findings listed in `critical_findings`
- Count tokens in your compressed summary
- Calculate compression ratio
- Replace all three `TOKENS_CALCULATE` placeholders with accurate values

### 4. Determine Next Phase
Based on current phase:
- `analysis` → `design`
- `design` → `implementation` (validation is opt-in only via /validate_finding)
- `implementation` → mark task complete, move to completed/

Update `task.current_phase` to next phase name (e.g., "design").

Use `"TIMESTAMP_COMPRESS"` placeholder for timestamps - the hook will replace them.

### 6. Dispatch Next Agent
Based on next phase and context bundle:
- `design` → Primary agent in PROPOSE mode
- `validation` → security-engineer in VALIDATE mode
- `implementation` → Primary agent in IMPLEMENT mode

**Include compressed context in dispatch:**
- Load the compressed summary from `phase_compressions[previous_phase]`
- Include critical findings IDs so agent can reference them
- Pass must-address items as requirements

### 7. Validate Task File Integrity
**IMPORTANT:** After writing the task file with phase compression, run the validation hook to remove any duplicate keys.

Execute this Bash command with 60-second timeout:

```bash
echo '{"tool_name": "Write", "tool_input": {"file_path": "[your_project_path]/.claude/tasks/active/TASK-XXX.json"}}' | python3 [your_project_path]/.claude/hooks/hook_validate_task.py
```

Replace `[your_project_path]` with your project directory and `TASK-XXX.json` with the actual task filename.

**Parameters for Bash tool:**
- `timeout`: 60000 (60 seconds)
- `run_in_background`: true
- `description`: "Validate task file and remove duplicate phase_compressions keys"

**Why this is necessary:**
- Removes any duplicate `phase_compressions` keys that may have been created during write
- Prevents Python's JSON parser from silently overwriting data with empty duplicates
- Ensures task file integrity before next phase begins
- Complements PreToolUse hook as defense-in-depth

### 8. Report to User
After advancing the phase, report the transition:

```
EXAMPLE OUTPUT:
✓ Analysis phase validated - all findings meet confidence threshold
✓ Compressed 5 findings into phase summary (token counts will be calculated)
✓ Phase advanced: analysis → design
✓ Task file integrity validated
→ Dispatching backend-engineer in PROPOSE mode...

Next phase requirements:
- Implement transaction workflow
- Design mediation interface
- Address transaction dispute edge cases
```

**Note:** Token count details will be available in the task file after the hook processes placeholders.

## Error Handling

### Validation Failures
**Unresolved decisions:**
```
❌ Cannot advance: 2 pending decisions require resolution
- DECISION-001: Choose between REST vs GraphQL
- DECISION-003: Determine transaction timeout duration
→ Use /resolve_decision to address these before advancing
```

**Low confidence findings:**
```
❌ Cannot advance: 3 findings below confidence threshold (0.8)
- FIND-002: confidence 0.6
- FIND-005: confidence 0.7
- FIND-008: confidence 0.5
→ Use /update_finding to increase confidence or remove uncertain findings
```

**Unresolved blockers:**
```
❌ Cannot advance: 1 active blocker
- BLOCKER-001: Stripe API key access required
→ Resolve blockers before advancing
```

### Other Errors
- **No next phase**: "Task complete! Use /finalize to commit changes"
- **Agent dispatch fails**: Report error and suggest manual agent invocation
- **File write fails**: Verify task file permissions and retry

## Implementation Notes

### Phase Compression Strategy
When writing your compressed summary:
1. **Focus on outcomes**: What was learned, decided, or designed?
2. **Preserve critical context**: What must the next agent know?
3. **Reference findings by ID**: Don't rewrite findings, just reference them
4. **Be concise but complete**: Aim for 450-600 tokens
5. **Include constraints**: Any limitations or requirements discovered

### Token Calculation Flow
The hook calculates accurate token counts by:
1. Reading the findings listed in `critical_findings[]`
2. Summing their existing `token_count` values (already accurate from earlier hooks)
3. Counting tokens in your new compressed summary
4. Computing compression ratio: `original_tokens / compressed_tokens`

This ensures precision without requiring the orchestrator to estimate.

### Placeholder Usage
**Always use these exact strings:**
- `"TIMESTAMP_COMPRESS"` - For any timestamp field during compression
- `"TOKENS_CALCULATE"` - For token-related calculations

The hook scans the JSON after Write completes and replaces these placeholders.

## Related Commands
- `/task_status` - Check if ready to advance
- `/resolve_decision` - Clear blockers before advancing
- `/compress_phase` - Manually trigger compression if needed
- `/validate_finding` - Request security validation before implementation