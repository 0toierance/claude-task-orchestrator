# Customization Guide

How to adapt Claude Task Orchestrator for your specific project.

## Overview

The orchestrator is designed to be customized. While the core workflow (phases, compression, hooks) remains constant, you should tailor:

1. **Agent competencies** - What each agent knows about your stack
2. **Context bundles** - How keywords map to your documentation
3. **SOPs** - Your project-specific procedures
4. **System docs** - Your architecture documentation

## Customizing Agents

### Agent Structure

Each agent file in `.claude/agents/` follows this structure:

```markdown
---
name: backend-engineer
description: Brief description for agent selection
model: opus
---

# Identity
Who the agent is and what they specialize in.

# Infrastructure Context
Project-specific details (ports, services, IDs).

# Core Competencies
List of skills and knowledge areas.

# Context Loading Protocol
How to read compressed context from previous phases.

# Operating Modes
## Mode: ANALYZE
## Mode: PROPOSE
## Mode: VALIDATE
## Mode: IMPLEMENT

# Finding Structure
JSON schema for findings with placeholders.

# Critical Rules
DO and DON'T lists.
```

### Adding Infrastructure Context

Update the Infrastructure Context section with your specifics:

```markdown
# Infrastructure Context
- Supabase project: your-project-id
- API server: port 3000
- Database: PostgreSQL on port 5432
- Redis cache: port 6379
```

### Modifying Competencies

Add competencies relevant to your tech stack:

```markdown
# Core Competencies
- Database Architecture: PostgreSQL with Prisma ORM
- API Design: GraphQL with Apollo Server
- Caching: Redis with cache-aside pattern
- Authentication: Auth0 integration
```

### Creating New Agents

To add a new agent (e.g., `data-engineer`):

1. Create `.claude/agents/data-engineer.md`
2. Follow the structure template
3. Define modes appropriate for data work
4. Update context bundles to route data keywords to this agent

## Customizing Context Bundles

### Bundle Structure

Context bundles in `.claude/context/templates/context-bundles.json` map keywords to relevant documentation:

```json
{
  "bundle_name": {
    "description": "When this bundle applies",
    "sops": ["sop-file.md"],
    "system": ["system-doc.md"],
    "code_refs": ["/src/path/**/*.ts"]
  }
}
```

### Adding a New Bundle

Example: Adding a "machine_learning" bundle:

```json
{
  "machine_learning": {
    "description": "ML model training, inference, data pipelines",
    "sops": [
      "ml-training-guidelines.md",
      "data-preprocessing.md"
    ],
    "system": [
      "ml-architecture.md",
      "model-registry.md"
    ],
    "code_refs": [
      "/src/ml/**/*.py",
      "/notebooks/**/*.ipynb"
    ]
  }
}
```

### Keyword Routing

The orchestrator matches keywords in task descriptions to bundles:

- "model", "training", "inference" → `machine_learning`
- "database", "query", "migration" → `database_operations`
- "component", "ui", "style" → `ui_components`

Update `/task_create` command if you need custom keyword matching.

## Writing SOPs

### SOP Structure

SOPs in `.claude/context/sops/` should be actionable procedures:

```markdown
# [Topic] SOP

## When to Use
- Scenario 1
- Scenario 2

## Procedure

### Step 1: [Action]
Details and code examples.

### Step 2: [Action]
Details and code examples.

## Common Pitfalls
- Pitfall 1 and how to avoid
- Pitfall 2 and how to avoid

## Checklist
- [ ] Item 1
- [ ] Item 2

## Related Documents
- [Link to related doc]
```

### Example: Database Migration SOP

```markdown
# Database Migration SOP

## When to Use
- Adding new tables
- Modifying existing schema
- Adding indexes

## Procedure

### Step 1: Create Migration File
```bash
npx prisma migrate dev --name descriptive_name
```

### Step 2: Verify Migration
- Check generated SQL is correct
- Test on development database
- Verify rollback works

### Step 3: Deploy
- Run on staging first
- Monitor for errors
- Run on production during low-traffic

## Common Pitfalls
- **Large table migrations**: Use batching for data migrations
- **Index creation**: Use CONCURRENTLY on production

## Checklist
- [ ] Migration file reviewed
- [ ] Tested locally
- [ ] Tested on staging
- [ ] Rollback tested
- [ ] Production deployed
```

## Writing System Docs

### System Doc Structure

System docs in `.claude/context/system/` describe current architecture:

```markdown
# [System Component]

## Overview
What it does and why it exists.

## Architecture
How it's structured, with diagrams if helpful.

## Key Components
- Component 1: Description
- Component 2: Description

## Data Flow
How data moves through the system.

## Configuration
How to configure it.

## Related
- Link to related docs
```

### Example: Authentication System Doc

```markdown
# Authentication Architecture

## Overview
JWT-based authentication with refresh tokens.

## Architecture
```
Client → API Gateway → Auth Service → Database
           ↓
        JWT Validation
```

## Key Components
- **Auth Service**: Handles login, logout, token refresh
- **JWT Middleware**: Validates tokens on protected routes
- **Refresh Token Store**: Redis-backed token storage

## Data Flow
1. User submits credentials
2. Auth service validates against database
3. JWT + refresh token issued
4. Client stores tokens
5. Subsequent requests include JWT
6. Middleware validates before routing

## Configuration
Environment variables:
- `JWT_SECRET`: Token signing key
- `JWT_EXPIRY`: Token lifetime (default: 15m)
- `REFRESH_EXPIRY`: Refresh token lifetime (default: 7d)
```

## Updating the Context README

After adding documentation, update `.claude/context/README.md`:

1. Add new documents to the structure section
2. Add cross-references
3. Add to "Quick Start" scenarios

## Testing Customizations

### Verify Agent Loading

```
/task_create "test task for [your domain]"
/task_status
```

Check that:
- Correct agent was selected
- Context bundle includes your docs
- Agent has your infrastructure context

### Verify Context Bundles

Create tasks with keywords from your bundles and verify the correct documents are loaded.

### Verify SOPs Are Followed

Check agent findings reference your SOPs when making recommendations.

## Best Practices

1. **Keep agents focused** - Don't overload with too many competencies
2. **Update docs with code** - When code changes, update system docs
3. **Document learnings** - Use `/document_learnings` after tasks
4. **Version your customizations** - Commit `.claude/` with your project
5. **Review completed tasks** - Learn from what worked and what didn't
