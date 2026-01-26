---
description: Manually add finding to task knowledge pool for the specifcied task, if no task was specificed assume it was the last 'active' task. 
---

# add_finding

Interactively prompts user to add a manual finding to task's knowledge pool. Useful for capturing manual discoveries or insights. We are documenting something new found (i.e. system behavior that we don't like) during the review process and because its associated with task it would need to be appended as a new fresh finding.

**Parameters:**
- `[task_id]` (optional) - Task to add finding to. If omitted, use current active task.

## Orchestrator Process

### 1. Load Task
- If task_id provided: Load that task
- If omitted: Load current active task
- Verify task exists and is active

### 2. Interactive Prompts

**Prompt 1: Category**
```
Category? (existing_patterns|dependencies|risks|database_schema|api_design|
           component_design|workflow_design|security_review|etc)
>
```

Show category options based on current phase and agent types.

**Prompt 2: Content**
```
Content (JSON format):
>
```

Show example structure for selected category. User provides structured content.

**Prompt 3: Confidence**
```
Confidence (0.0-1.0)?
>
```

User rates their confidence in this finding.

**Prompt 4: Dependencies**
```
Dependencies (F-IDs, comma-separated)?
>
```

User lists finding IDs this depends on (optional).

**Prompt 5: Tags**
```
Tags (comma-separated)?
>
```

User adds tags like "critical", "security", "performance" (optional).

### 3. Generate Finding ID
- Get next available F-ID from task
- Format: F-{next_number} (e.g., F-017)

### 4. Create Finding Object
Build complete finding:
```json
{
  "id": "F-017",
  "agent": "user",
  "phase": "[current task phase]",
  "timestamp": "[ISO-8601]",
  "category": "[user input]",
  "confidence": [user input],
  "content": {[user input]},
  "dependencies": ["F-002", "F-005"],
  "tags": ["critical", "manual"],
  "token_count": [estimated],
  "manual": true
}
```

Always add `"manual": true` tag to distinguish from agent findings.

### 5. Validate Finding
Check:
- Content is valid JSON
- Category matches known categories
- Confidence is 0.0-1.0
- Referenced dependencies exist

If validation fails, prompt user to correct.

### 6. Add to Task
Append to `task.knowledge_pool.findings[]`

### 7. Report to User
```
EXAMPLE OUTPUT:
Finding F-016 added
Category: risks
Confidence: 0.85
Tags: security, critical, manual
```

## Example Session
```
User: /add_finding

Orchestrator: Category? (risks|dependencies|database_schema|...)
User: risks

Orchestrator: Content (JSON):
User: {
  "threat": "SQL injection in search filters",
  "severity": "high",
  "mitigation": "Use parameterized queries"
}

Orchestrator: Confidence (0.0-1.0)?
User: 0.85

Orchestrator: Dependencies (F-IDs, comma-separated)?
User: F-002

Orchestrator: Tags (comma-separated)?
User: security, critical

Orchestrator: Finding F-016 added
Category: risks
Confidence: 0.85
Tags: security, critical, manual
```

## When to Use

**Manual Discoveries:**
- Found issue during manual testing
- Discovered pattern not caught by agents
- External feedback or requirements

**Quick Captures:**
- Capture insight before it's forgotten
- Document decision rationale
- Record constraint or limitation

**Corrections:**
- Add missing context agents overlooked
- Correct agent misunderstandings

## Error Handling
- Invalid JSON: Show error and prompt again
- Unknown category: List valid categories
- Invalid confidence: Must be 0.0-1.0
- Task not found: List available tasks

## Related Commands
- `/query_findings` - View all findings including manual ones
- `/task_status` - See finding count increase