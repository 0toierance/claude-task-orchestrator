# Phase Lifecycle

Deep dive into the 4-phase task lifecycle.

## Overview

Every task progresses through four distinct phases:

```
Analysis → Design → Implementation → Finalization
```

Each phase has:
- **Entry criteria** - What must be true to enter
- **Objectives** - What the agent accomplishes
- **Exit criteria** - What must be true to advance
- **Outputs** - What gets produced

## Phase 1: Analysis

### Purpose
Understand the current state, identify patterns, and assess risks before designing.

### Agent Mode
`ANALYZE`

### Objectives
1. Map existing code patterns that can be reused
2. Identify dependencies (tables, APIs, services)
3. Assess risks (security, performance, technical)
4. Outline rough database requirements

### Finding Categories
- `existing_patterns` - Reusable code patterns
- `dependencies` - Services/tables/APIs needed
- `risks` - Security/performance/technical risks
- `database_requirements` - Rough schema needs

### Exit Criteria
- All findings have confidence > 0.8
- All decisions resolved
- No unresolved blockers

### Advancement
```
/advance_phase
```
Triggers compression: ~7,200 tokens → ~450 tokens

## Phase 2: Design

### Purpose
Create implementation-ready specifications based on analysis findings.

### Agent Mode
`PROPOSE`

### Context Received
- Compressed analysis brief (450 tokens)
- 3-5 critical findings from analysis
- Context bundle (SOPs, system docs)

### Objectives
1. Design complete database schemas with indexes, RLS policies
2. Design API endpoints with request/response contracts
3. Plan caching strategy (what, where, TTL, invalidation)
4. Define performance targets and scaling considerations

### Finding Categories
- `database_schema` - Complete table definitions
- `api_design` - Endpoint contracts
- `caching_strategy` - Cache architecture
- `performance_plan` - Latency/throughput targets

### Key Requirement
Every design finding must have `implementation_ready: true`

### Exit Criteria
- All findings have confidence > 0.8
- All decisions resolved
- At least one finding has `implementation_ready: true`
- No unresolved blockers

### Optional: Validation
Before advancing, you can request validation:
```
/validate_finding F-009 security-engineer
```

## Phase 3: Implementation

### Purpose
Execute the approved designs by writing code, tests, and documentation.

### Agent Mode
`IMPLEMENT`

### Context Received
- Implementation brief (compressed from design)
- 3-5 critical design findings
- Context bundle

### Objectives
1. Create database migrations
2. Implement code (services, APIs, components)
3. Write tests
4. Update documentation

### Outputs
Updates `implementation_artifacts[]` with:
```json
{
  "type": "migration|code|test|documentation",
  "file_path": "/src/...",
  "description": "Brief description"
}
```

### Exit Criteria
- All planned artifacts created
- Tests pass
- No critical errors

## Phase 4: Finalization

### Purpose
Commit changes, close issues, and complete tracking tasks.

### Triggered By
```
/finalize TASK-ID
```

### Agent Mode
CI/CD Engineer in `FINALIZE` mode

### Objectives
1. Read completion summary
2. Create git commit with conventional format
3. Close referenced GitHub issues
4. Complete referenced Todoist tasks
5. Move task to `completed/` directory

### Outputs
```json
{
  "commit_hash": "abc123",
  "commit_message": "feat(auth): Add JWT authentication",
  "github_issues_closed": ["#42"],
  "todoist_tasks_completed": ["task-id"]
}
```

## Phase Transitions

### Analysis → Design
```
You: /advance_phase

System:
1. Validates exit criteria
2. Compresses findings (7200 → 450 tokens)
3. Identifies 3-5 critical findings
4. Updates task phase to "design"
5. Dispatches agent in PROPOSE mode
```

### Design → Implementation
```
You: /advance_phase

System:
1. Validates exit criteria
2. Checks implementation_ready flags
3. Compresses design findings
4. Updates task phase to "implementation"
5. Dispatches agent in IMPLEMENT mode
```

### Implementation → Finalization
```
You: /finalize TASK-ID

System:
1. Validates artifacts exist
2. Dispatches CI/CD engineer
3. Creates commit, closes issues
4. Moves task to completed/
```

## Token Budget by Phase

| Phase | Context Budget | Output Budget | Compression |
|-------|---------------|---------------|-------------|
| Analysis | 35K | 7,200 | → 450 |
| Design | 36.8K | 4,800 | → 600 |
| Implementation | 37.6K | Variable | None |

## Handling Blockers

If an agent encounters a blocker:

1. Agent writes blocker to `knowledge_pool.blockers[]`
2. Orchestrator reports blocker to you
3. Resolve blocker (provide information, make decision)
4. Agent continues or re-runs phase

## Handling Decisions

If an agent needs user input:

1. Agent writes decision to `knowledge_pool.decisions[]`
2. Orchestrator reports decision to you
3. You resolve: `/resolve_decision D-001 "your answer"`
4. Agent incorporates answer in next run

## Skipping Phases

For simple tasks, you can skip design:

```json
{
  "execution_plan": {
    "phases": [
      {"name": "design", "status": "skipped", "reason": "Low complexity task"}
    ]
  }
}
```

But analysis should never be skipped - understanding before doing is core to the system.
