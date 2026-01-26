# Setup Guide

Complete installation and setup instructions for Claude Task Orchestrator.

## Prerequisites

- **Claude Code CLI** - The Claude Code command-line interface
- **Python 3.8+** - For automation hooks
- **Git** - For finalization features

## Installation

### Step 1: Clone the Repository

Clone this repository as the `.claude` directory in your project:

```bash
cd /path/to/your/project
git clone https://github.com/YOUR_USERNAME/claude-task-orchestrator.git .claude
```

Or if you want to track it as a submodule:

```bash
git submodule add https://github.com/YOUR_USERNAME/claude-task-orchestrator.git .claude
```

### Step 2: Install Python Dependencies

The hooks use `tiktoken` for accurate token counting:

```bash
pip install tiktoken
```

Or if you prefer a virtual environment:

```bash
python -m venv .claude/.venv
source .claude/.venv/bin/activate  # On Windows: .claude\.venv\Scripts\activate
pip install -r .claude/hooks/requirements.txt
```

### Step 3: Make Hooks Executable

```bash
chmod +x .claude/hooks/*.py
```

### Step 4: Verify Installation

Check that all components are in place:

```bash
ls -la .claude/
# Should show: agents, commands, hooks, context, tasks, settings.json
```

Test hook execution:

```bash
python .claude/hooks/hook_enrich_findings.py --help 2>/dev/null || echo "Hook is ready"
```

## Configuration

### Update settings.json

Edit `.claude/settings.json` to customize for your project:

```json
{
  "project": {
    "type": "react-native",  // or "web", "backend", "fullstack"
    "name": "My Awesome Project",
    "description": "A brief description of your project"
  }
}
```

### Configure Context Bundles

Edit `.claude/context/templates/context-bundles.json` to map keywords to your documentation:

```json
{
  "database_operations": {
    "description": "Database schema, migrations, queries",
    "sops": ["database-optimization.md"],
    "system": ["architecture.md"],
    "code_refs": ["/src/db/**/*.ts"]
  }
}
```

### Add Project Documentation

1. Create architecture docs in `.claude/context/system/`
2. Add SOPs for your patterns in `.claude/context/sops/`
3. Update `.claude/context/README.md` with cross-references

## First Task Walkthrough

### 1. Start Claude Code in your project

```bash
cd /path/to/your/project
claude
```

### 2. Create your first task

```
/task_create "Add user authentication with JWT tokens. Users should be able to register, login, and logout. Store sessions in PostgreSQL."
```

### 3. Watch the Analysis Phase

The orchestrator will:
1. Parse your statement
2. Generate a context bundle based on keywords
3. Create a task file in `.claude/tasks/active/`
4. Dispatch the backend-engineer in ANALYZE mode

### 4. Check Status

```
/task_status
```

View findings, decisions, and blockers.

### 5. Resolve Decisions (if any)

If the agent needs clarification:

```
/resolve_decision D-001 "Use bcrypt for password hashing with 12 rounds"
```

### 6. Advance to Design

Once analysis is complete:

```
/advance_phase
```

This compresses findings and dispatches the agent in PROPOSE mode.

### 7. Continue Through Phases

Repeat `/advance_phase` to move through:
- Design → Implementation
- Implementation → Finalization

### 8. Finalize

When implementation is complete:

```
/finalize TASK-001
```

This creates a git commit and closes any referenced issues.

### 9. Document Learnings (Optional)

Extract patterns to documentation:

```
/document_learnings TASK-001
```

## Troubleshooting

### Hooks Not Firing

1. Check hooks are executable: `chmod +x .claude/hooks/*.py`
2. Verify Python is available: `which python3`
3. Check settings.json has correct paths

### Token Count Errors

1. Ensure tiktoken is installed: `pip install tiktoken`
2. Check Python path in hooks

### Task File Errors

1. Validate JSON syntax: `python -m json.tool .claude/tasks/active/TASK-001.json`
2. Check for placeholder values not replaced

See [docs/troubleshooting.md](docs/troubleshooting.md) for more solutions.

## Next Steps

1. Read [CUSTOMIZATION.md](CUSTOMIZATION.md) to adapt for your project
2. Review [quick-reference.md](quick-reference.md) for all commands
3. Explore [docs/](docs/) for deep dives on each concept
