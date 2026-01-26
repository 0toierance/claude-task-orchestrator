# Claude Task Orchestrator

A structured workflow system for Claude Code that coordinates AI agents on complex tasks with traceable context.

## The Problem This Solves

AI agents often build without clear direction, creating files that are sparsely located and disconnected. This system:

- **Aligns agents** to coordinate on structured tasks
- **Traces context** - every task references the documents used to solve it
- **Compresses knowledge** - 7200 tokens compressed to 450 tokens between phases
- **Self-documents** - learnings extracted to SOPs automatically

## How It Works

```
You → Orchestrator → Sub-Agent (autonomous) → Findings → Compression → Next Phase
```

### 4-Phase Workflow

1. **Analysis** - Agent maps existing patterns, identifies dependencies, assesses risks
2. **Design** - Agent creates implementation-ready specifications
3. **Implementation** - Agent writes code, migrations, tests
4. **Finalization** - Git commit, close issues, complete tasks

### Knowledge Pool

Every task maintains a structured knowledge pool:
- **Findings** - Discoveries with confidence scores (0.0-1.0)
- **Decisions** - Questions needing user input
- **Blockers** - Issues preventing progress
- **Compressions** - Token-efficient summaries for next phase

## Quick Start

### 1. Clone as `.claude` directory

```bash
# In your project root
git clone https://github.com/YOUR_USERNAME/claude-task-orchestrator.git .claude
```

### 2. Install Python dependency

```bash
pip install tiktoken
```

### 3. Make hooks executable

```bash
chmod +x .claude/hooks/*.py
```

### 4. Create your first task

```bash
# In Claude Code
/task_create "Implement user authentication with JWT tokens"
```

## Features

| Feature | Description |
|---------|-------------|
| Phase-based workflow | Analysis → Design → Implementation → Finalization |
| Automatic compression | ~7200 tokens → ~450 tokens between phases |
| Knowledge pool | Structured findings, decisions, blockers |
| Context bundles | Pre-computed document mappings |
| 4 specialized agents | Backend, Frontend, Security, DevOps |
| Self-documenting | Learnings extracted to SOPs |
| Hook automation | Timestamps, token counts, validation |

## Available Commands

| Command | Description |
|---------|-------------|
| `/task_create "description"` | Create new task, dispatch analysis agent |
| `/go [task_id]` | Resume work on active task |
| `/task_status` | Check current task progress |
| `/advance_phase` | Move to next phase after completion |
| `/resolve_decision D-ID "answer"` | Answer pending decision |
| `/finalize TASK-ID` | Git commit, close issues |
| `/document_learnings TASK-ID` | Extract patterns to documentation |

See [quick-reference.md](quick-reference.md) for complete command list.

## Core Agents

| Agent | Specialization |
|-------|----------------|
| **backend-engineer** | Database, APIs, real-time systems, performance |
| **frontend-engineer** | UI/UX, components, animations, accessibility |
| **security-engineer** | Threat analysis, compliance, vulnerability review |
| **devops-engineer** | CI/CD, deployments, monitoring, infrastructure |

## Directory Structure

```
.claude/
├── agents/           # Agent definitions (4 files)
├── commands/         # Orchestrator commands (13 files)
├── hooks/            # Python automation (4 files)
├── context/
│   ├── sops/         # Standard Operating Procedures
│   ├── system/       # Architecture documentation
│   └── templates/    # Task template, context bundles
├── tasks/
│   ├── active/       # Current tasks
│   ├── blocked/      # Tasks with blockers
│   └── completed/    # Finished tasks
├── settings.json     # Hook configuration
└── docs/             # Framework documentation
```

## Customization

This framework is designed to be customized for your project:

1. **Agents** - Modify agent competencies and infrastructure context
2. **Context Bundles** - Define keyword → docs mappings for your codebase
3. **SOPs** - Add project-specific standard operating procedures
4. **System Docs** - Document your architecture

See [CUSTOMIZATION.md](CUSTOMIZATION.md) for detailed guide.

## Documentation

- [Quick Reference](quick-reference.md) - Command cheat sheet
- [Workflow Diagram](workflow.mermaid) - Visual workflow
- [Concepts](docs/concepts.md) - Core concepts explained
- [Phases](docs/phases.md) - Phase lifecycle deep dive
- [Compression](docs/compression.md) - How compression works
- [Hooks](docs/hooks.md) - Hook system explained
- [Agents](docs/agents.md) - Creating custom agents
- [Context Bundles](docs/context-bundles.md) - Defining bundles
- [SOPs](docs/sops.md) - Writing effective SOPs

## Requirements

- Claude Code CLI
- Python 3.8+ with `tiktoken` package
- Git (for finalization)

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Contributions welcome! Please read the documentation first and ensure your changes maintain backward compatibility with existing task files.
