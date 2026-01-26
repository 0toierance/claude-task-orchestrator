---
description: Manually mark task as complete when solved outside agent workflow
---

# task_complete

Marks task as manually completed when user solved the problem themselves without full agent pipeline.

## Usage
```
/task_complete {task_id} "{reason}"
```

**Parameters:**
- `{task_id}` - Task to mark complete
- `{reason}` - Why/how it was manually completed

## Orchestrator Process

### 1. Load Task
- Load task from `.claude/tasks/active/{task_id}.json`
- Verify task exists and is in active state

### 2. Generate Completion Summary
Create or update `completion_summary` with:
- `completed_at`: Current timestamp
- `completed_by`: "user"
- `manual_completion`: true
- `reason`: User's provided reason
- `what_was_built`: Extract from reason if possible
- `final_phase`: Current phase when manually completed

### 3. Update Task Status
- Set `status`: "complete"
- Add note: "Manually completed by user"
- Preserve all findings and work done so far

### 4. Move to Completed
Move task file:
```
.claude/tasks/active/{task_id}.json 
  → .claude/tasks/completed/{task_id}.json
```

### 5. Report to User
```
EXAMPLE OUTPUT:
Task [TASK-ID] marked complete
Reason: Manually implemented payment flow with different approach
Moved to .claude/tasks/completed/

Run /document_learnings to capture knowledge for future tasks
```

Remind about `/document_learnings` to preserve knowledge.

## Error Handling
- Task not found: List available active tasks
- Task already completed: "Task already in completed/. Nothing to do."
- Missing reason: Prompt user to provide reason

## Use Cases
- You solved the problem faster than agents could
- You took a different approach than agents were pursuing
- External change made task unnecessary
- Third-party resolved the issue

## Related Commands
- `/document_learnings` - Extract patterns from manual work
- `/finalize` - If there are commits/issues to close