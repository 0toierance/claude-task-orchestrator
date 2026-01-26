# Core Concepts

Understanding the fundamental concepts behind Claude Task Orchestrator.

## The Problem

When AI agents work on complex software tasks, they often:

1. **Create scattered files** - Code ends up in random locations without clear organization
2. **Lose context** - Earlier decisions are forgotten as context windows fill up
3. **Work without direction** - No structured approach to analysis → design → implementation
4. **Don't learn** - Patterns aren't captured for future reference

## The Solution

Claude Task Orchestrator addresses these problems through:

### 1. Structured Phases

Every task moves through defined phases:

```
Analysis → Design → Implementation → Finalization
```

Each phase has clear objectives and outputs, preventing agents from jumping straight to code.

### 2. Knowledge Pool

All discoveries are stored in a structured knowledge pool:

```json
{
  "findings": [],      // Agent discoveries with confidence scores
  "decisions": [],     // Questions needing user input
  "blockers": [],      // Issues preventing progress
  "phase_compressions": {}  // Summaries for next phase
}
```

### 3. Context Compression

Between phases, findings are compressed:
- **Raw findings**: ~7,200 tokens
- **Compressed**: ~450 tokens + 3-5 critical findings

This preserves essential knowledge while staying within context limits.

### 4. Traceable Context

Every task references the documents that informed decisions:

```json
{
  "context_bundle": {
    "sops": ["api-design-standards.md"],
    "system": ["architecture.md"],
    "code_refs": ["/src/api/**/*.ts"]
  }
}
```

## Key Components

### Tasks

A task is a structured JSON file tracking:
- **Definition**: What needs to be done
- **Context Bundle**: Relevant documentation
- **Knowledge Pool**: Findings, decisions, blockers
- **Execution Plan**: Phase status and progress
- **Implementation Artifacts**: Created files
- **Completion Summary**: What was built, patterns learned

### Agents

Specialized AI agents with defined competencies:
- **Backend Engineer**: Database, APIs, performance
- **Frontend Engineer**: UI/UX, components, accessibility
- **Security Engineer**: Threats, compliance, vulnerabilities
- **DevOps Engineer**: CI/CD, deployment, monitoring

Each agent operates in modes:
- **ANALYZE**: Map patterns, identify dependencies, assess risks
- **PROPOSE**: Design implementation-ready specifications
- **VALIDATE**: Review another agent's work
- **IMPLEMENT**: Write code, tests, documentation

### Orchestrator

The orchestrator (you, using Claude Code) manages:
- Task creation and routing
- Phase advancement
- Decision resolution
- Compression between phases
- Finalization and documentation

### Hooks

Python automation that runs automatically:
- **hook_enrich_findings.py**: Adds timestamps
- **hook_compress_phase.py**: Compresses findings
- **hook_init_task.py**: Initializes new tasks
- **hook_validate_task.py**: Validates task structure

### Context Bundles

Pre-computed mappings of keywords to documentation:

```json
{
  "database_operations": {
    "sops": ["database-optimization.md"],
    "system": ["architecture.md"],
    "code_refs": ["/src/db/**/*.ts"]
  }
}
```

When you create a task mentioning "database", the orchestrator automatically loads relevant docs.

### SOPs (Standard Operating Procedures)

Documented procedures for common tasks:
- API design standards
- Security protocols
- Performance optimization
- Deployment checklists

Agents reference SOPs when making recommendations.

### System Docs

Architecture documentation describing:
- Current system design
- Service infrastructure
- Data flows
- Integration points

## The Workflow

```
1. /task_create "description"
   ↓
2. Orchestrator parses → generates context bundle → creates task file
   ↓
3. Dispatches agent in ANALYZE mode
   ↓
4. Agent writes findings to knowledge pool
   ↓
5. /advance_phase → compresses findings → dispatches PROPOSE mode
   ↓
6. Agent writes design findings
   ↓
7. /advance_phase → dispatches IMPLEMENT mode
   ↓
8. Agent writes code, tests, docs
   ↓
9. /finalize → git commit, close issues
   ↓
10. /document_learnings → extract patterns to SOPs
```

## Benefits

1. **Organized output** - Files go where they belong
2. **Preserved context** - Compression keeps knowledge across phases
3. **Structured approach** - Analysis before design before code
4. **Learning system** - Patterns extracted and documented
5. **Traceable decisions** - Know why choices were made
6. **Coordinated agents** - Clear handoffs between phases
