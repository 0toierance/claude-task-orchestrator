---
description: Answer pending decision to unblock agent progress
---

# resolve_decision

Marks a decision as resolved with user's answer, updates affected findings, and checks for unblocked work.

## Usage
```
/resolve_decision {decision_id} {answer}
```

**Parameters:**
- `{decision_id}` - Decision ID (e.g., D-001)
- `{answer}` - User's answer with rationale

**Smart Detection:**
If user provides answer without explicit decision_id and only one pending decision exists, automatically resolve that decision.

## Orchestrator Process

### 1. Load Task
- Find task with pending decision matching decision_id
- If multiple tasks have same decision_id, prompt user for task selection
- If decision not found, report error

### 2. Locate Decision
From task's `knowledge_pool.decisions[]`:
- Find decision where `id == decision_id` and `status == "pending"`
- If already resolved, inform user
- If not found, list all pending decisions

### 3. Update Decision
Modify decision object:
- Set `status: "resolved"`
- Set `resolved_by: "user"`
- Set `resolved_at: [ISO-8601 timestamp]`
- Set `answer: [user's answer]`
- Extract rationale from answer if provided

### 4. Update Impacted Findings
For each finding_id in `decision.impacts_findings[]`:
- Locate finding in `knowledge_pool.findings[]`
- Add note about decision resolution
- If finding has `implementation_ready: false` pending this decision, re-evaluate readiness

### 5. Check for Unblocked Blockers
For each blocker in `knowledge_pool.blockers[]`:
- If blocker was waiting on this decision, update blocker status
- Mark blocker as potentially resolved if decision was the blocker

### 6. Assess Phase Readiness
After resolution, check if current phase can now proceed:
- All decisions resolved? 
- Confidence scores >0.8?
- Ready to advance?

### 7. Write Updated Task File
Save changes to `.claude/tasks/active/TASK-{id}.json`

### 8. Report to User
```
EXAMPLE OUTPUT:
D-001 resolved: "Yes, configurable 24-72h"
Updated F-002 (database schema)
Ready to advance to design phase
```

If multiple findings impacted:
```
D-001 resolved: "Yes, configurable 24-72h"
Updated findings:
  F-002: Database schema
  F-007: API design
Ready to advance to design phase
```

## Error Handling
- Decision not found: List all pending decisions with IDs
- Decision already resolved: Show previous resolution
- Invalid decision_id format: Explain expected format (D-###)

## Related Commands
- `/task_status` - View pending decisions
- `/advance_phase` - Move forward after resolving decisions