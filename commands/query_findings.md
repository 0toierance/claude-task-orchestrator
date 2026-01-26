---
description: Filter and search findings in task knowledge pool
---

# query_findings

Searches and filters findings based on various criteria to help understand task details.

## Usage
```
/query_findings [filters] [task_id]
```

**Parameters:**
- `[filters]` - One or more filter criteria (see below)
- `[task_id]` (optional) - Specific task to search. If omitted, use current active task.

## Filter Options

**By Phase:**
```
phase=analysis
phase=design
phase=validation
phase=implementation
```

**By Agent:**
```
agent=backend-engineer
agent=security-engineer
agent=cicd-engineer
agent=uiux-engineer
```

**By Category:**
```
category=risks
category=database_schema
category=api_design
category=security_review
```

**By Confidence:**
```
confidence>0.8
confidence<0.7
confidence>=0.9
```

**By Tag:**
```
tag=critical
tag=security
tag=performance
tag=blocking
```

**By Status:**
```
implementation_ready=true
implementation_ready=false
```

**By Finding ID:**
```
id=F-001
depends_on=F-002
validates=F-005
```

## Orchestrator Process

### 1. Load Task
- If task_id provided: Load that task
- If omitted: Load current active task
- Verify task exists

### 2. Parse Filters
Extract filter criteria from command:
- Split on spaces or commas
- Parse each filter into field, operator, value
- Support: `=`, `>`, `<`, `>=`, `<=`, `!=`

### 3. Filter Findings
From `task.knowledge_pool.findings[]`:
- Apply each filter criterion
- Use AND logic (all filters must match)
- Return matching findings

### 4. Sort Results
Default sort: Most recent first (by timestamp)
Optional sorts:
- By confidence (highest first)
- By phase order
- By finding ID

### 5. Format Output
For each matching finding, display:
```
EXAMPLE OUTPUT:
F-003: Race condition in dual approval
  Agent: backend-engineer
  Phase: analysis
  Category: risks
  Confidence: 0.95
  Tags: critical, security
  
F-007: Stripe API rate limits
  Agent: backend-engineer
  Phase: analysis
  Category: dependencies
  Confidence: 0.85
  Tags: external, blocking

Found 2 findings matching filters
```

If requesting full details (verbose mode):
Include finding content, dependencies, validations.

## Common Query Patterns

**High-confidence risks:**
```
/query_findings category=risks confidence>0.9
```

**Design findings ready for implementation:**
```
/query_findings phase=design implementation_ready=true
```

**All critical security findings:**
```
/query_findings tag=security tag=critical
```

**Findings depending on F-002:**
```
/query_findings depends_on=F-002
```

**Backend engineer's analysis phase work:**
```
/query_findings agent=backend-engineer phase=analysis
```

## Error Handling
- No matches: "No findings match the specified filters"
- Invalid filter syntax: Show example of correct syntax
- Task not found: List available tasks

## Related Commands
- `/task_status` - Overview of all findings
- `/validate_finding` - Request validation of specific finding