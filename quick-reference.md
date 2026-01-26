## Phase Advancement Checks

**ANALYZE → DESIGN:**
- All findings confidence >0.8
- All decisions resolved
- No unresolved blockers

**DESIGN → IMPLEMENT:**
- All findings confidence >0.8
- All decisions resolved
- No unresolved blockers
- **At least one finding has `implementation_ready: true`**

The `implementation_ready` flag only matters when leaving design phase - it ensures designs are detailed enough to implement.# Agent System Quick Reference

## Control Flow
```
You → Orchestrator → Sub-Agent (autonomous) → Orchestrator → You
     ↑___________________________________________↑
           You steer between runs only
```

## File Structure
```
.claude/
├── agents
│   ├── backend-engineer.md
│   ├── cicd-engineer.md
│   ├── security-engineer.md
│   └── uiux-engineer.md
├── commands
│   ├── advance_phase.md
│   ├── document_learnings.md
│   ├── finalize.md
│   ├── go.md
│   ├── query_findings.md
│   ├── resolve_decision.md
│   ├── task_complete.md
│   ├── task_create.md
│   ├── task_status.md
│   ├── update_doc.md
│   └── validate_finding.md
├── context
│   ├── sops
│   ├── system
│   └── templates
├── settings.json
├── settings.local.json
└── tasks
    ├── active
    ├── blocked
    └── completed
```

## Task File Sections

| Section | Purpose | Who Writes |
|---------|---------|------------|
| `definition` | User's original request | Orchestrator (from user input) |
| `context_bundle` | Relevant docs/code | Orchestrator (auto-generated) |
| `knowledge_pool.findings[]` | All agent discoveries | Sub-agents + User (via /add_finding) |
| `knowledge_pool.phase_compressions` | Token-efficient summaries | Orchestrator (between phases) |
| `knowledge_pool.decisions[]` | Questions needing user input | Sub-agents (raise), User (resolve) |
| `knowledge_pool.blockers[]` | Blocking issues | Sub-agents |
| `execution_plan` | Phase tracking | Orchestrator |
| `implementation_artifacts[]` | Code/files created | Sub-agents (implement phase) |
| `completion_summary` | What was built, patterns learned | Orchestrator (on completion) |

## Agent Modes

| Mode | Phase | Input Context | Output | Token Budget |
|------|-------|---------------|--------|--------------|
| ANALYZE | analysis | Context bundle only | Findings (detailed) | ~35K |
| PROPOSE | design | Compressed analysis + critical findings | Findings (implementation-ready) | ~37K |
| VALIDATE | manual only | Compressed + design findings | Validation findings | ~37K |
| IMPLEMENT | implementation | Compressed + critical design | Code artifacts | ~38K |

## Compression Strategy

| Phase | Raw Tokens | Compressed | Critical Findings | Next Phase Total |
|-------|------------|------------|-------------------|------------------|
| Analysis | 7,200 | 450 | 3 findings (1,350) | 36,800 |
| Design | 4,800 | 600 | 3 findings (2,000) | 37,600 |

**Key:** Each phase receives compressed summary + 3-5 critical findings, not all findings.

## Finding Structure

Agents write minimal structure. System hook auto-adds timestamp and token_count after agent finishes.

**Agent writes:**
```json
{
  "id": "F-001",
  "agent": "backend-engineer",
  "phase": "analysis",
  "category": "existing_patterns",
  "confidence": 0.9,
  "content": { /* category-specific structure */ },
  "dependencies": ["F-002"],
  "tags": ["critical"]
}
```

**System enriches to:**
```json
{
  "id": "F-001",
  "agent": "backend-engineer",
  "phase": "analysis",
  "timestamp": "2025-10-12T10:15:00Z",  // Auto-added by SubagentStop hook
  "category": "existing_patterns",
  "confidence": 0.9,
  "content": { /* category-specific structure */ },
  "dependencies": ["F-002"],
  "tags": ["critical"],
  "token_count": 180  // Auto-calculated by SubagentStop hook
}
```

For design phase findings, agent also includes:
- `implementation_ready: true` - signals specs are complete enough to code

## Finding Categories by Agent

### Backend Engineer

**Analysis:**
- `existing_patterns` - Reusable code patterns
- `dependencies` - Services/tables/APIs needed
- `risks` - Security/performance/technical risks
- `database_requirements` - Rough schema needs

**Design:**
- `database_schema` - Complete SQL with indexes/RLS
- `api_design` - Endpoint contracts + error cases
- `caching_strategy` - What/where/TTL/invalidation
- `performance_plan` - Expected latency/throughput

**Validation:**
- `security_review` - Vulnerabilities found
- `technical_review` - Design issues
- `performance_review` - Bottlenecks

**Implementation:**
- `migration` - Database migrations
- `code` - API/service implementation
- `test` - Test files
- `documentation` - Updated docs

### UI/UX Engineer

**Analysis:**
- `ui_patterns` - Existing component patterns
- `user_flow_analysis` - Navigation/interaction patterns
- `accessibility_gaps` - WCAG violations, screen reader issues
- `performance_concerns` - Render bottlenecks, animations

**Design:**
- `component_design` - Component specs with props/states
- `interaction_design` - Animations, gestures, transitions
- `layout_design` - Screen layouts, responsive breakpoints
- `accessibility_implementation` - ARIA, semantic HTML, focus

**Validation:**
- `usability_review` - User experience issues
- `visual_review` - Design consistency, brand alignment
- `accessibility_audit` - Compliance verification

**Implementation:**
- `component` - React/React Native components
- `styles` - Theme system, CSS/styling
- `assets` - Images, icons, animations

### CI/CD Engineer

**Analysis:**
- `pipeline_patterns` - Existing workflow patterns
- `deployment_dependencies` - Services/secrets/infra
- `build_risks` - Version conflicts, breaking changes

**Design:**
- `workflow_design` - GitHub Actions/EAS configs
- `deployment_strategy` - Progressive rollout plans
- `monitoring_plan` - Sentry, logs, alerts

**Implementation:**
- `workflow` - CI/CD pipeline files
- `infrastructure` - Terraform, configs
- `deployment_config` - EAS.json, app store configs

### Security Engineer

**Analysis:**
- `threat_analysis` - Attack vectors, vulnerabilities
- `compliance_gaps` - PCI, GDPR, CCPA issues
- `authentication_risks` - Auth flow vulnerabilities

**Validation:**
- `security_review` - Code/design vulnerabilities
- `penetration_test` - Attack simulation results
- `compliance_audit` - Regulatory compliance check

## Commands You Use

| Command | When | Effect |
|---------|------|--------|
| `/task_create {statement}` | Start new work | Creates task, dispatches ANALYZE |
| `/go [TASK-ID]` | Resume work | Loads task, dispatches agent for current phase |
| `/task_status [ID]` | Check progress | Shows phase, findings, decisions |
| `/resolve_decision D-ID {answer}` | Agent asked question | Unblocks agent, enables advance |
| `/advance_phase` | Phase complete | Compresses, dispatches next |
| `/finalize TASK-ID` | Commit & close | Git commit, close issues, complete Todoist |
| `/task_complete TASK-ID "reason"` | Manually solved | Closes task, suggests documenting |
| `/document_learnings TASK-ID` | Extract knowledge | Updates SOPs + System docs |
| `/query_findings [filters]` | Find specific info | Filters knowledge pool |
| `/validate_finding F-ID` | Need review | Dispatches validator |
| `/compress_phase [phase]` | Manual compression | Forces compression (rare) |
| `/add_finding` | Manual finding | Interactive prompt |

## Orchestrator Auto-Actions

**After ANALYZE completes:**
1. Compress findings (7K -> 450 tokens)
2. Report to you, await `/advance_phase`

**After PROPOSE completes:**
1. Check implementation_ready flags
2. Compress, await advance
3. If you want validation, use `/validate_finding` manually

**After IMPLEMENT completes:**
1. Move task to completed/
2. Report summary

## Rollback with Claude Code

**Built-in Rollback:**
Claude Code tracks all file changes including `.claude/tasks/*.json`. Use rollback button to revert both code and task state together.

**After Rollback:**
```bash
You: "/go"
Orchestrator: Loads task, reads current_phase, resumes work
```

## Token Limits & Why Compression

**Without compression:**
- Analysis: 35K context + 0 findings = 35K (OK)
- Design: 35K context + 7.2K analysis = 42.2K (risk overflow)
- Implement: 35K context + 12K findings = 47K (overflow)

**With compression:**
- Analysis: 35K (OK)
- Design: 35K + 0.45K compressed + 1.35K critical = 36.8K (OK)
- Implement: 35K + 0.6K compressed + 2K critical = 37.6K (OK)

## Decision Flow

```
Sub-agent: "D-001: Should timeout be configurable?"
  (returns to orchestrator)
Orchestrator: "Decision needed: D-001"
  (reports to you)
You: "/resolve_decision D-001 Yes, 24-72h range"
  (orchestrator processes)
Orchestrator: Updates task, informs agents in next phase
```

## Blocker Flow

```
Sub-agent: "B-001: Stripe API limits unclear"
  (returns to orchestrator)
Orchestrator: "Blocker detected: B-001"
  (assigns to appropriate agent)
CICD-Engineer: Investigates, resolves blocker
Orchestrator: "B-001 resolved, ready to advance"
```

## Validation (Opt-In Only)

```
You: "/validate_finding F-009 security-engineer"
Security-engineer (VALIDATE): Reviews F-009
  (approved=false)
Orchestrator: "Validation failed, needs fixes"
You: "Fix it" or provide guidance
Backend-engineer (PROPOSE): Revises F-009
Security-engineer (VALIDATE): approved=true
Orchestrator: "Ready for implementation"
```

## Key Differences from Original Proposal

| Original | Optimized |
|----------|-----------|
| Sequential phase lock | Phase-agnostic modes |
| agent_outputs nested by phase | Flat findings[] with IDs |
| No compression | Auto-compression between phases |
| No rollback | Checkpoints + rollback |
| Manual coordination | Orchestrator auto-routes |
| Context: load all SOPs | Context: pre-computed bundles |
| No confidence scoring | 0.0-1.0 confidence per finding |
| No validation layer | Any agent validates any finding |

## Common Patterns

**Starting work:**
```bash
You: "/task_create [detailed requirements]"
→ Task created, analysis started
→ Wait for completion, check status
You: "/task_status"
→ Review findings, resolve decisions
You: "/resolve_decision D-001 [answer]"
You: "/advance_phase"
```

**Mid-phase review:**
```bash
You: "/query_findings phase=design implementation_ready=true"
→ See what's designed
You: "/validate_finding F-009 security-engineer"
→ Get security review
```

**Something went wrong:**
```bash
[Use Claude Code rollback button]
Code + task file both revert
You: "/task_sync [TASK-ID]"
Verifies sync
You: "Resume from design phase"
Orchestrator: Reads task state, continues
```