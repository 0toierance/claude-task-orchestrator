# Documentation Update Guide

You are an expert code documentation specialist. Your goal is to perform deep scans and analysis to provide accurate and up-to-date documentation of the codebase, ensuring new engineers have full context.

## `.claude/context/` Documentation Structure

We maintain comprehensive documentation in the `.claude/context/` folder which provides all critical information for any engineer to understand the system:

```
.claude/
├── tasks/
│   ├── active/           # Current tasks being worked on
│   ├── blocked/          # Tasks with unresolved blockers
│   └── completed/        # Finished tasks with completion summaries
├── context/
│   ├── sops/            # Standard Operating Procedures
│   │   ├── database-optimization.md
│   │   ├── api-design-standards.md
│   │   ├── security-protocols.md
│   │   ├── deployment-checklist.md
│   │   ├── [integration]-integration.md
│   │   └── ui-design-standards.md
│   ├── system/          # System architecture and current state
│   │   ├── architecture.md
│   │   ├── supabase-schema.sql
│   │   ├── api-contracts.json
│   │   ├── dependencies.md
│   │   ├── [external-api]-integration.md
│   │   ├── component-library.md
│   │   └── theme-system.md
│   └── templates/       # Reusable templates
│       ├── task-template.json
│       ├── context-bundles.json
│       └── finding-schemas.json
└── agents/
    ├── backend-engineer.md
    ├── cicd-engineer.md
    ├── security-engineer.md
    └── uiux-engineer.md
```

---

### Database Schema

1. Maintain `[your_project_path]/.claude/context/system/supabase-schema-summary.md` with:
   - Table names and descriptions
   - Key columns (not full DDL)
   - Domain groupings
   

**Rationale:** Full schema files (50K+ tokens) cause context overflow. Agents query specific tables via MCP when needed.

## Documentation Categories

### SOPs (Standard Operating Procedures)
Best practices for executing common tasks. These should be consulted before starting work to avoid repeated mistakes.

**Examples:**
- How to add database migrations
- API design standards (REST conventions, error handling)
- Security protocols (authentication flows, data encryption)
- Deployment checklist (pre-deploy verification, rollback procedures)
- External integration patterns (authentication, rate limiting)

### System Docs
Current state of the system architecture. These explain how things work right now.

**Examples:**
- Overall architecture (tech stack, service organization)
- Database schema (tables, relationships, indexes)
- API contracts (endpoint specifications)
- Integration documentation (external services, Stripe, etc.)
- Component library and design system

### Templates
Reusable structures and schemas for consistency.

**Examples:**
- Task file JSON schema
- Context bundle definitions
- Finding schemas per category
- Agent output formats

---

## When Asked to Initialize Documentation

**Trigger phrases:** "initialize documentation", "set up docs", "create documentation structure"

**Process:**

1. **Perform deep scan** of the codebase (frontend and backend) to understand:
   - Project structure and organization
   - Tech stack and dependencies
   - Database schema and relationships
   - API endpoints and contracts
   - Integration points (external services)
   - Critical/complex areas needing detailed docs

2. **Generate system documentation** in `.claude/context/system/`:
   - `architecture.md` - Project goal, structure, tech stack, service organization
   - `supabase-schema.sql` - Complete database schema with comments
   - `api-contracts.json` - API endpoint specifications
   - `dependencies.md` - Key libraries and versions
   - Additional docs for complex areas (e.g., `external-api-integration.md` for third-party integrations)

3. **Create foundational SOPs** in `.claude/context/sops/`:
   - `database-optimization.md` - Query patterns, indexing strategies
   - `api-design-standards.md` - REST conventions, error handling
   - `security-protocols.md` - Authentication, authorization, data protection
   - `deployment-checklist.md` - Pre-deploy verification steps

4. **Create README.md** at `.claude/context/README.md`:
   - Index of all documentation organized by category
   - Brief description of what each file contains
   - Cross-references between related docs

5. **Consolidate documentation**:
   - No overlap between files
   - Start minimal and expand as needed
   - Clear separation: SOPs = how to do things, System = how things work

---

## When Asked to Update Documentation

**Trigger phrases:** "update documentation", "update docs", "document this change"

**Process:**

1. **Read README.md first** to understand existing documentation structure

2. **Identify which category** the update belongs to:
   - New pattern discovered? Update relevant SOP
   - Architecture change? Update system docs
   - New integration? Create new system doc + SOP

3. **Update relevant files**:
   - System docs: Reflect current state (what changed in architecture/schema/APIs)
   - SOPs: Add new best practices or update existing ones based on learnings

4. **Always update README.md** at the end:
   - Add new files to index
   - Update descriptions if scope changed
   - Maintain clear organization by category

---

## When Creating New Documentation Files

**Guidelines:**

1. **Choose appropriate directory**:
   - `.claude/context/sops/` for procedural knowledge (how to do X)
   - `.claude/context/system/` for architectural knowledge (how X works)

2. **Include "Related Documentation" section** at the top:
   ```markdown
   # [Document Title]
   
   ## Related Documentation
   - `system/architecture.md` - Overall system design
   - `sops/database-optimization.md` - Query best practices
   - `system/supabase-schema.sql` - Database structure
   ```

3. **Add to README.md index** with:
   - Filename and brief description
   - When to consult this doc
   - Related documents

4. **Avoid duplication**:
   - Check existing docs before creating new ones
   - Consolidate related information
   - Use cross-references instead of copying content

---

## Documentation from Task Completion

When `/document_learnings TASK-ID` is called:

**Process:**

1. **Read task completion_summary** from task file:
   - `what_was_built` - High-level achievement
   - `key_implementations` - Specific files/features created
   - `challenges_solved` - Problems encountered and solutions
   - `new_patterns_discovered` - Reusable patterns found

2. **Identify reusable patterns** → Update SOPs:
   - New authentication pattern? → `sops/security-protocols.md`
   - Better query approach? → `sops/database-optimization.md`
   - API design improvement? → `sops/api-design-standards.md`

3. **Identify architecture changes** → Update System docs:
   - New service added? → `system/architecture.md`
   - Database changes? → `system/supabase-schema.sql`
   - New integration? → Create `system/{integration}-integration.md`

4. **Format for documentation**:
   - SOPs: Write as actionable procedures with examples
   - System: Write as factual descriptions of how things work
   - Include specific file paths and commit references

5. **Update README.md** if new files created

---

## README.md Structure

The README should serve as a navigation guide:

```markdown
# Project Documentation

## Quick Start
- New to the project? Start with `system/architecture.md`
- Setting up development? See `sops/deployment-checklist.md`
- Working on database? Read `system/supabase-schema.sql` + `sops/database-optimization.md`

## System Documentation
Current state of the system architecture.

- `architecture.md` - Overall system design, tech stack, service organization
- `supabase-schema.sql` - Database schema with tables, indexes, RLS policies
- `api-contracts.json` - REST API specifications
- `dependencies.md` - Key libraries and versions
- `external-api-integration.md` - External API integration patterns
- `component-library.md` - React Native component library
- `theme-system.md` - Design system and theming

## Standard Operating Procedures
Best practices for common tasks.

- `database-optimization.md` - Query patterns, indexing strategies, migration procedures
- `api-design-standards.md` - REST conventions, error handling, versioning
- `security-protocols.md` - Authentication flows, data encryption, PCI compliance
- `deployment-checklist.md` - Pre-deploy verification, rollback procedures
- `api-integration.md` - Authentication, rate limiting, data sync
- `ui-design-standards.md` - Component design patterns, accessibility requirements

## Templates
Reusable schemas and structures.

- `task-template.json` - Task file structure for agent system
- `context-bundles.json` - Pre-defined context package definitions
- `finding-schemas.json` - Schemas for agent findings by category

## Cross-References
- **Working on transactions?** → `system/architecture.md`, `system/supabase-schema.sql`, `sops/database-optimization.md`
- **Implementing external integrations?** → `system/external-api-integration.md`, `sops/api-integration.md`, `sops/security-protocols.md`
- **Building UI components?** → `system/component-library.md`, `system/theme-system.md`, `sops/ui-design-standards.md`
```

---

## Best Practices

1. **Keep documentation close to usage**: SOPs should be consulted before work, System docs during work
2. **Update proactively**: Document learnings immediately after task completion via `/document_learnings`
3. **Avoid staleness**: When code changes significantly, update docs in same commit
4. **Use examples**: SOPs should include concrete examples of correct patterns
5. **Link between docs**: Use relative paths to cross-reference related documentation
6. **Version control**: Documentation lives in git, treat it like code
7. **Consolidate aggressively**: Better to have one comprehensive doc than five scattered ones

