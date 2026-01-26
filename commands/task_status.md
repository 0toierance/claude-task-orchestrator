---
description: Display current task state with findings, decisions, and progress
---

# task_status

Shows comprehensive status of specified task including phase, findings, decisions, and blockers.

## Usage
```
/task_status [task_id]
```

**Parameters:**
- `[task_id]` (optional) - Specific task to check. If omitted, show most recent active task.

## Orchestrator Process

### 1. Load Task
- If task_id provided: Load that specific task
- If omitted: Load most recently updated task from `.claude/tasks/active/`
- If not found: Report error

### 2. Parse Task Data
Extract from task file:
- Task ID, title, status, priority
- Current phase and phase history
- Context bundle type and loaded docs
- All findings count by phase
- Compression status and token savings
- Pending decisions
- Active blockers
- Next phase readiness

### 3. Calculate Statistics
- Total findings count
- Findings by phase (analysis: X, design: Y, etc.)
- Average confidence score across findings
- Token compression savings (original → compressed)
- Completion percentage based on phases

### 4. Check Phase Status
For current phase:
- Which agents have completed work
- Which agents are in progress
- What's blocking progression

For next phase:
- Prerequisites met? (decisions resolved, confidence >0.8)
- Ready to advance? Yes/No

### 5. Format Output
```
EXAMPLE OUTPUT:
[TASK-ID]: Implement payment processing
Status: active | Phase: design | Priority: high

Context: database_operations + payment_processing
  3 SOPs, 2 system docs (35K tokens)

Knowledge Pool:
  14 findings (8 analysis, 6 design)
  Token compression: 7,200 -> 450 (analysis)
  1 decision pending user input
  0 blockers

Current Phase: design
  backend-engineer completed F-009 through F-014
  Awaiting security-engineer validation

Next Phase: implementation (ready when validation passes)
```

### 6. Display Pending Items
If decisions pending:
```
Decisions Requiring Input:
  D-001: Should transaction timeout be configurable?
    Asked by: backend-engineer
    Context: High-value transactions may need longer review
    Use: /resolve_decision D-001 [answer]
```

If blockers exist:
```
Active Blockers:
  B-001: Stripe API limits unclear
    Raised by: backend-engineer
    Status: investigating
    Assigned to: cicd-engineer
```

## Error Handling
- Task not found: List available tasks and suggest correct ID
- Task file corrupted: Report parsing error and suggest manual inspection
- No active tasks: "No active tasks. Create one with /task_create"

## Related Commands
- `/resolve_decision` - Answer pending decisions
- `/advance_phase` - Move to next phase if ready
- `/query_findings` - Deep dive into specific findings