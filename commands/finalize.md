---
description: Create git commit, close GitHub issues, and complete Todoist tasks
---

# finalize

Dispatches CI/CD engineer to create commit, close related issues, and complete tracking tasks.

## Usage
```
/finalize {task_id}
```

**Parameters:**
- `{task_id}` - Task to finalize (must be in implementation complete or completed state)

## Orchestrator Process

### 1. Load and Validate Task
- Load task from `.claude/tasks/active/{task_id}.json`
- Verify task has `completion_summary` populated
- Verify task has `implementation_artifacts[]` with files
- If missing, report error and suggest completing implementation first

### 2. Dispatch CI/CD Engineer
Invoke cicd-engineer in FINALIZE mode with instruction:
"Finalize task at .claude/tasks/active/{task_id}.json"

The CI/CD engineer will:
1. Read completion_summary for commit message content
2. Create git commit with conventional format
3. Extract GitHub issue numbers from task
4. Close GitHub issues with commit reference
5. Search Todoist for "GH-{issue_number}" tasks
6. Complete Todoist tasks with commit reference
7. Update task file with finalization details

### 3. CI/CD Engineer Output
The agent writes finalization finding with:
- Git commit hash
- Commit message used
- GitHub issues closed (with numbers)
- Todoist tasks completed (with IDs)
- Files committed count

### 4. Update Task Status
After CI/CD engineer completes:
- Set `completion_summary.finalized: true`
- Set `completion_summary.git_commit: [hash]`
- Set `completion_summary.issues_closed: [array]`
- Set `completion_summary.todoist_tasks_completed: [array]`

### 5. Move Task to Completed
Move task file from `active/` to `completed/`:
```
.claude/tasks/active/TASK-{id}.json 
  → .claude/tasks/completed/TASK-{id}.json
```

### 6. Report to User
```
EXAMPLE OUTPUT:
Finalizing [TASK-ID]...

Git commit created:
  Commit: abc123
  Message: "feat(auth): Implement session cookie auth for transactions
  
  - Cookie jar management
  - Session validation middleware
  - Transaction initiation with auth
  
  Closes #42"
  Files: 8 modified

GitHub issues closed:
  #42: Add session authentication

Todoist tasks completed:
  GH-42: Add session authentication (Project: Backend)

Task finalized and ready for push.
```

## Error Handling
- Task not found: Report error with available task IDs
- No completion_summary: "Implementation incomplete. Finish implementation first."
- No implementation_artifacts: "No files to commit. Nothing to finalize."
- GitHub/Todoist API errors: Report which step failed, suggest manual completion

## Related Commands
- `/task_complete` - If you solved manually and want to close task
- `/document_learnings` - Extract knowledge from finalized task to docs
- `git push` - Push the created commit to remote