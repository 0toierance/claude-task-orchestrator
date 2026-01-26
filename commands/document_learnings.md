---
description: Extract task learnings to SOPs and System documentation
---

# document_learnings

Analyzes completed task and updates SOPs with reusable patterns and System docs with architectural changes.

## Usage
```
/document_learnings {task_id}
```

**Parameters:**
- `{task_id}` - Completed task to extract learnings from

## Orchestrator Process

### 1. Load Completed Task
- Load task from `.claude/tasks/completed/{task_id}.json`
- Verify task has `completion_summary`
- If task not completed, report error

### 2. Analyze Completion Summary
Extract from `completion_summary`:
- `what_was_built` - High-level achievement
- `key_implementations` - Specific files/features
- `challenges_solved` - Problems and solutions
- `new_patterns_discovered` - Reusable patterns
- Context bundle type (determines which docs to update)

### 3. Identify Documentation Updates

**Reusable Patterns → SOPs:**
Map patterns to SOP files based on pattern type:
- Authentication/security patterns → `sops/security-protocols.md`
- Database query improvements → `sops/database-optimization.md`
- API design patterns → `sops/api-design-standards.md`
- Deployment procedures → `sops/deployment-checklist.md`
- Integration patterns → `sops/[integration]-integration.md`
- UI/UX patterns → `sops/ui-design-standards.md`

**Architectural Changes → System Docs:**
- New services/components → `system/architecture.md`
- Database changes → `system/supabase-schema.sql`
- New integrations → Create `system/{name}-integration.md`
- API changes → `system/api-contracts.json`
- Component additions → `system/component-library.md`

### 4. Format for Documentation

**For SOPs (procedural knowledge):**
Write as actionable procedures with examples:
```markdown
## [Pattern Name]

**When to use:** [Scenario description]

**Implementation:**
1. [Step with specific guidance]
2. [Step with code reference]

**Example:**
[Concrete example from this task]

**Files:** [Specific file paths from task]
**Reference:** Task {task_id}, Commit {hash}
```

**For System Docs (architectural knowledge):**
Write as factual descriptions:
```markdown
## [Component/Integration Name]

**Purpose:** [What it does]

**Implementation:** [How it works]
Located in: [file paths]

**Key Details:**
- [Important technical detail]
- [Integration point]
- [Configuration]

**Added in:** Task {task_id}, Commit {hash}
```

### 5. Update Documentation Files
For each identified documentation update:
- Read existing file
- Append new section or update existing section
- Maintain consistent formatting
- Add cross-references to related docs

### 6. Update README.md
If new documentation files created:
- Add to appropriate category in README
- Include brief description
- Update cross-references section if applicable

### 7. Mark Task as Documented
Update task file:
- Set `completion_summary.documented: true`
- Set `completion_summary.docs_updated: [list of updated files]`

### 8. Report to User
```
EXAMPLE OUTPUT:
Documenting learnings from [TASK-ID]...

Updated SOPs:
  api-integration.md
    + Session authentication pattern
    + Token extraction method
    + Rate limiting strategy

Updated System docs:
  external-api-integration.md
    + Request flow diagram
    + Session management architecture
    + Error handling patterns

Knowledge captured for future integration tasks.
```

## Error Handling
- Task not completed: "Task must be completed first. Use /task_complete or /finalize"
- No completion_summary: "No learnings to document. Task has no completion summary."
- Documentation file not found: Create new file with appropriate structure

## Related Commands
- `/task_complete` - Complete task before documenting
- `/finalize` - Finalize task before documenting
- `update_doc` - General documentation updates