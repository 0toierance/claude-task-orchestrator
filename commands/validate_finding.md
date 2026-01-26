---
description: Manually request validation of specific finding by appropriate agent (opt-in only)
---

# validate_finding

Manually dispatches an agent to validate a specific finding. Use when you want security review or technical verification.

**Note:** Validation is opt-in. The system does NOT automatically validate - you decide when it's needed.

## Usage
```
/validate_finding {finding_id} [agent] [task_id]
```

**Parameters:**
- `{finding_id}` - Finding to validate (e.g., F-009)
- `[agent]` (optional) - Specific agent to use. If omitted, auto-select based on finding category
- `[task_id]` (optional) - Task containing the finding. If omitted, search active tasks

## Orchestrator Process

### 1. Locate Finding
- Search for finding_id in specified or active tasks
- If found in multiple tasks, prompt user to select
- Verify finding exists

### 2. Validate Finding Readiness
Check if finding is ready for validation:
- Is finding from design phase?
- Does finding have `implementation_ready: true`?
- Has finding already been validated?

If not ready, report issue and stop.

### 3. Determine Validator Agent
If agent not specified, auto-select based on finding category:
- `database_schema`, `api_design`, `performance_plan` → security-engineer
- `security_review`, `threat_analysis` → backend-engineer or uiux-engineer
- `component_design`, `accessibility_implementation` → backend-engineer
- `workflow_design`, `deployment_strategy` → security-engineer

If specified agent name doesn't match available agents, report error.

### 4. Prepare Validation Context
Create validation brief for agent:
- Finding being validated (full content)
- Dependencies (load referenced findings)
- Related findings from same phase
- Relevant SOPs and system docs
- Compressed context from previous phases

### 5. Dispatch Agent in VALIDATE Mode
Invoke selected agent with:
- Mode: VALIDATE
- Task file path
- Specific finding_id to validate
- Validation context

### 6. Agent Creates Validation Finding
Agent writes new finding with category `technical_review`, `security_review`, or appropriate validation category.

Validation finding includes:
- Which finding is being validated
- Issues found (with severity and recommendations)
- Approval status (true/false)
- Findings that require changes

### 7. Report to User
```
EXAMPLE OUTPUT:
Dispatching security-engineer to validate F-009...
Validation F-015 added
Issues found: Missing timeout index
Approval: false (requires changes)

Options:
1. /advance_phase (re-dispatch to fix)
2. /query_findings id=F-015 (see details)
```

If approved:
```
EXAMPLE OUTPUT:
Dispatching security-engineer to validate F-009...
Validation F-015 added
Approval: true (design approved)

Ready to proceed with implementation.
```

## Error Handling
- Finding not found: List available findings with IDs
- Finding not ready for validation: Explain what's needed (e.g., "Finding must be from design phase")
- Agent not available: List available agents
- Validation fails: Report error and suggest manual review

## Related Commands
- `/query_findings` - Find findings to validate
- `/advance_phase` - Proceed after validation approval or fix issues