# Project Documentation

Welcome to your project's documentation hub. This directory contains documentation that guides AI agents and developers.

## Quick Start

**New to the project?**
1. Start with `system/architecture.md` to understand the overall system design
2. Check relevant SOPs before starting work on specific features

## Documentation Types

### Standard Operating Procedures (SOPs)
Location: `sops/`

Best practices for executing common tasks. **Consult these before starting work** to avoid repeated mistakes.

| SOP | Purpose |
|-----|---------|
| `api-design-standards.md` | REST API conventions, error handling |
| `security-protocols.md` | Auth, encryption, session management |
| `performance-optimization.md` | Memory, caching, query optimization |
| `deployment-checklist.md` | Pre-deployment verification, rollback |
| `ui-design-standards.md` | Component patterns, styling |
| `react-native-best-practices.md` | React Native patterns |

### System Documentation
Location: `system/`

Current state of system architecture. These explain **how things work**.

| Document | Purpose |
|----------|---------|
| `architecture.md` | Overall system design (create this for your project) |
| `dependencies.md` | Key libraries and versions (create this for your project) |

### Templates
Location: `templates/`

| Template | Purpose |
|----------|---------|
| `task_template.json` | Task file structure |
| `context-bundles.json` | Keyword → docs mappings |

## Adding Documentation

### When to Add SOPs
- You discover a better way to do something
- You solve a difficult problem others might face
- You identify a common pitfall
- You establish a new pattern

### When to Add System Docs
- Architecture changes
- Database schema changes
- New integrations added
- API contracts change

### How to Add

1. Create file in appropriate directory (`sops/` or `system/`)
2. Follow existing document structure
3. Update this README
4. Add to `context-bundles.json` if it should be auto-loaded

## Cross-References

Create links between related documents:
```markdown
## Related Documents
- [security-protocols.md](sops/security-protocols.md)
- [architecture.md](system/architecture.md)
```

## Template: New SOP

```markdown
# [Topic] SOP

## When to Use
- Scenario 1
- Scenario 2

## Procedure

### Step 1: [Action]
Details...

## Common Pitfalls
- Pitfall 1: How to avoid

## Checklist
- [ ] Item 1

## Related Documents
- [Link]
```

## Template: New System Doc

```markdown
# [System Component]

## Overview
What it does and why.

## Architecture
How it's structured.

## Key Components
- Component 1: Description

## Configuration
How to configure it.
```

---

*Customize this README for your project. Add specific documentation relevant to your codebase.*
