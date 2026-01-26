# Creating Custom Agents

Guide to creating and customizing agents for your project.

## Agent Structure

Every agent file follows this structure:

```markdown
---
name: agent-name
description: Brief description for agent selection
model: opus
---

# Identity
[Who the agent is]

# Infrastructure Context
[Project-specific details]

# Core Competencies
[Skills and knowledge]

# Context Loading Protocol
[How to load compressed context]

# Operating Modes
[ANALYZE, PROPOSE, VALIDATE, IMPLEMENT]

# Finding Structure
[JSON schema for findings]

# Critical Rules
[DO and DON'T lists]
```

## Creating a New Agent

### Step 1: Define Identity

```markdown
# Identity
You are the Data Engineer for [project description]. You design and
optimize data pipelines, manage ETL processes, implement data quality
systems, and ensure reliable data flow across the organization.
```

### Step 2: Add Infrastructure Context

```markdown
# Infrastructure Context
- Data Warehouse: Snowflake (account: xxx)
- ETL Tool: Apache Airflow on port 8080
- Message Queue: Apache Kafka on port 9092
- Monitoring: Datadog dashboards
```

### Step 3: Define Competencies

```markdown
# Core Competencies
- Pipeline Design: Airflow DAGs, dependency management, scheduling
- Data Modeling: Star schema, slowly changing dimensions, data marts
- ETL Optimization: Incremental loads, parallelization, partitioning
- Data Quality: Great Expectations, anomaly detection, lineage tracking
- Performance: Query optimization, materialized views, caching
```

### Step 4: Define Operating Modes

Each mode has specific responsibilities:

```markdown
## Mode: ANALYZE
**When:** `task.current_phase = "analysis"`

### Your Job
Understand existing data flows, identify bottlenecks, assess data quality.

### Process
- Map existing pipelines and dependencies
- Identify data quality issues
- Assess performance bottlenecks
- Document data lineage

### Categories
- `pipeline_patterns` - Existing DAG patterns
- `data_quality_issues` - Quality problems found
- `performance_bottlenecks` - Slow queries, inefficient loads
- `lineage_gaps` - Missing documentation
```

### Step 5: Define Finding Structure

```markdown
# Finding Structure

## Required Fields
- `id`: F-{sequential} (F-001, F-002, etc.)
- `agent`: Your agent name
- `phase`: Current phase
- `category`: One of your defined categories
- `confidence`: 0.0-1.0
- `content`: Structured data for the category
- `timestamp`: "TIMESTAMP_PH" (hook replaces)
- `token_count`: "TOKEN_COUNT_PH" (hook replaces)

## Example Finding
```json
{
  "id": "F-001",
  "agent": "data-engineer",
  "phase": "analysis",
  "category": "pipeline_patterns",
  "confidence": 0.9,
  "content": {
    "pipeline_name": "user_events_daily",
    "schedule": "0 2 * * *",
    "dependencies": ["raw_events", "user_dim"],
    "issues": ["No retry logic", "Missing alerts"]
  },
  "timestamp": "TIMESTAMP_PH",
  "token_count": "TOKEN_COUNT_PH"
}
```

### Step 6: Add Critical Rules

```markdown
# Critical Rules

## DO
- Read compressed context from previous phases
- Use exact placeholders for timestamp and token_count
- Tag critical findings appropriately
- Reference specific file paths

## DON'T
- Start implementation without approved designs
- Exceed token budget without raising decision
- Skip validation of existing pipelines
- Create test data in production
```

## Agent Selection Logic

The orchestrator selects agents based on context bundle keywords:

```
Keywords → Context Bundle → Agent
```

To add your agent to selection, update the `/task_create` command:

```markdown
### Step 6: Select Primary Agent

Based on context bundle type, select agent:

- `database_operations` → **backend-engineer**
- `data_pipelines` → **data-engineer**  // Add your agent
- `ui_components` → **frontend-engineer**
```

## Category Definitions

Define categories for each phase:

### Analysis Categories
- Pattern recognition and existing implementations
- Dependencies and integration points
- Risks and potential issues
- Requirements gathering

### Design Categories
- Schema/architecture design
- API/interface contracts
- Performance planning
- Security considerations

### Implementation Categories
- Code artifacts
- Configuration changes
- Test implementations
- Documentation updates

## Best Practices

### 1. Be Specific About Competencies
Don't: "Good at databases"
Do: "PostgreSQL optimization, partitioning strategies, query plan analysis"

### 2. Define Clear Mode Boundaries
- ANALYZE: Never write code
- PROPOSE: Never implement
- IMPLEMENT: Follow approved designs

### 3. Use Consistent Finding Categories
Categories should be predictable. Other agents and the orchestrator depend on consistent naming.

### 4. Include Token Budget Awareness
Agents should know their context limits:
```markdown
# Token Budget
- Analysis input: ~35K tokens
- Analysis output: up to 7,200 tokens
- Design input: ~37K tokens (includes compression)
```

### 5. Reference SOPs
Agents should cite relevant SOPs:
```markdown
When designing pipelines, follow guidelines in:
- `sops/data-pipeline-standards.md`
- `sops/data-quality-checks.md`
```

## Testing Your Agent

1. Create a task that should route to your agent:
```
/task_create "Build daily ETL pipeline for user events"
```

2. Verify agent selection:
```
/task_status
```

3. Check finding structure:
- Are categories correct?
- Are placeholders being replaced?
- Is content structured properly?

4. Test phase advancement:
```
/advance_phase
```

5. Verify compression includes your findings appropriately.
