---
description: Resume work from current task state
---

# go

Loads active task and resumes work by dispatching appropriate agent for current phase.

## Usage
```
/go [task_id]
```

**Parameters:**
- `[task_id]` (optional) - Specific task to resume. If omitted, auto-detect.

## Orchestrator Process

### 1. Find Active Task

**If task_id provided:**
- Load `.claude/tasks/active/{task_id}.json`
- If not found, report error

**If no task_id:**
- List all files in `.claude/tasks/active/`
- If one active task: Load it automatically
- If multiple: Prompt user to select

**Multiple tasks prompt:**
```
Multiple active tasks found:
1. TASK-001: Implement payment processing (Phase: design)
2. TASK-002: Add OAuth auth (Phase: implementation)

Which task? (1/2)
```

Wait for user selection, then load that task.

### 2. Read Task State
From loaded task file:
- Read `current_phase`
- Read `execution_plan.phases[]` to find current phase status
- Check for unresolved decisions or blockers

### 3. Determine Agent and Mode
Based on `current_phase`:
- `analysis` → Primary agent in ANALYZE mode
- `design` → Primary agent in PROPOSE mode
- `validation` → Security-engineer in VALIDATE mode
- `implementation` → Primary agent in IMPLEMENT mode

Primary agent determined from `context_bundle.type` (same logic as task_create).

### 4. Check Prerequisites
Before dispatching:
- If phase is "design" or "implementation": Verify previous phase is "complete"
- If unresolved decisions exist: Report and wait for `/resolve_decision`
- If blockers exist: Report and suggest resolution

### 5. Dispatch Agent
Invoke selected agent with appropriate mode and task file path.

### 6. Report to User
```
EXAMPLE OUTPUT:
Loading [TASK-ID]...
Current phase: design (complete)
Dispatching backend-engineer in IMPLEMENT mode...
```

## Error Handling
- No active tasks: "No active tasks found. Create one with /task_create"
- Task file corrupted: Report error, suggest checking file manually
- Prerequisites not met: Report specific issue (decision/blocker) and suggest resolution command

## Related Commands
- `/task_status` - Check what phase/state before resuming
- `/resolve_decision` - Resolve blockers before resuming
- `/advance_phase` - Move to next phase if current complete