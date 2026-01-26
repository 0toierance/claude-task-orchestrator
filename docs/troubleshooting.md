# Troubleshooting Guide

Common issues and their solutions.

## Installation Issues

### "Hooks not executing"

**Symptoms**: Task files aren't being enriched, timestamps remain as placeholders.

**Solutions**:
1. Make hooks executable:
   ```bash
   chmod +x .claude/hooks/*.py
   ```

2. Verify Python is available:
   ```bash
   which python3
   ```

3. Check settings.json paths are correct:
   ```json
   {
     "hooks": {
       "SubagentStop": [{
         "hooks": [{
           "type": "command",
           "command": ".claude/hooks/hook_enrich_findings.py"
         }]
       }]
     }
   }
   ```

### "tiktoken not found"

**Symptoms**: Token counts aren't being calculated, hook errors mentioning tiktoken.

**Solution**:
```bash
pip install tiktoken
```

Or in a virtual environment:
```bash
pip install -r .claude/hooks/requirements.txt
```

### "Permission denied"

**Symptoms**: Hooks fail with permission errors.

**Solution**:
```bash
chmod +x .claude/hooks/*.py
```

## Task Issues

### "Task file corrupted"

**Symptoms**: JSON parse errors, task won't load.

**Solutions**:
1. Validate JSON syntax:
   ```bash
   python -m json.tool .claude/tasks/active/TASK-001.json
   ```

2. Check for common issues:
   - Missing commas between array elements
   - Trailing commas
   - Unescaped quotes in strings
   - Invalid range notation in arrays (use `[52, 115]` not `[52-115]`)

3. Restore from git if available:
   ```bash
   git checkout .claude/tasks/active/TASK-001.json
   ```

### "Can't advance phase"

**Symptoms**: `/advance_phase` fails or reports issues.

**Causes and solutions**:

1. **Unresolved decisions**:
   ```
   /task_status  # See pending decisions
   /resolve_decision D-001 "your answer"
   ```

2. **Low confidence findings**:
   - Review findings with confidence < 0.8
   - Agent may need to re-analyze with more context

3. **Missing implementation_ready** (design → implementation):
   - At least one design finding needs `implementation_ready: true`
   - Agent needs to complete design specifications

### "Agent selected wrong"

**Symptoms**: Backend task routed to frontend agent, etc.

**Solutions**:
1. Check task keywords match context bundles:
   ```
   /task_status  # See context_bundle
   ```

2. Update context-bundles.json with better keyword mappings

3. Manually specify in task creation:
   ```
   /task_create "Backend: Add user authentication API"
   ```

### "Context bundle missing docs"

**Symptoms**: Agent doesn't have access to relevant SOPs.

**Solutions**:
1. Check context-bundles.json mappings
2. Verify SOP files exist at specified paths
3. Update bundle to include missing docs

## Agent Issues

### "Agent not following compressed context"

**Symptoms**: Agent seems to start fresh, ignores previous analysis.

**Solutions**:
1. Verify compression happened:
   ```json
   {
     "knowledge_pool": {
       "phase_compressions": {
         "analysis": {...}  // Should exist
       }
     }
   }
   ```

2. Check agent is loading context:
   - Agent should read `phase_compressions` first
   - Check agent prompt includes context loading protocol

### "Findings have wrong structure"

**Symptoms**: Findings missing required fields, validation failures.

**Solutions**:
1. Review agent finding structure definition
2. Ensure placeholders are exact strings:
   - `"TIMESTAMP_PH"` (not `timestamp_ph` or `TBD`)
   - `"TOKEN_COUNT_PH"` (not numbers)

3. Validate content is an object, not a string

### "Agent creating too many findings"

**Symptoms**: Token overflow, >20 findings per phase.

**Solutions**:
1. Agent should consolidate related discoveries
2. Use categories effectively (one finding per pattern, not per file)
3. Focus on significant findings, not obvious observations

## Compression Issues

### "Too many critical findings"

**Symptoms**: Compression keeps >5 findings as critical.

**Solutions**:
1. Review `["critical"]` tag usage - reserve for truly critical
2. Consolidate findings where possible
3. Consider if task scope is too large

### "Important information lost in compression"

**Symptoms**: Design agent missing context from analysis.

**Solutions**:
1. Tag important findings as critical
2. Link findings via dependencies
3. Manually add missing info:
   ```
   /add_finding
   ```

### "Compression failed"

**Symptoms**: Error messages about compression, phase_compressions empty.

**Solutions**:
1. Check all findings are valid JSON
2. Verify tiktoken is installed
3. Check hook_compress_phase.py is executable

## Finalization Issues

### "Git commit failed"

**Symptoms**: `/finalize` doesn't create commit.

**Solutions**:
1. Check git is initialized:
   ```bash
   git status
   ```

2. Verify files are staged:
   ```bash
   git add .
   ```

3. Check for git hooks blocking commit

### "GitHub issues not closing"

**Symptoms**: Issues remain open after finalize.

**Solutions**:
1. Verify `gh` CLI is authenticated:
   ```bash
   gh auth status
   ```

2. Check issue numbers in task file are correct
3. Verify you have permissions to close issues

## Performance Issues

### "Tasks taking too long"

**Solutions**:
1. Break large tasks into smaller ones
2. Use more specific context bundles
3. Reduce SOP/system doc sizes

### "Context overflow"

**Symptoms**: Agent truncated, missing information.

**Solutions**:
1. Verify compression is working
2. Reduce context bundle size
3. Use more targeted code_refs globs

## Recovery Procedures

### Recovering from Failed Task

1. Use Claude Code rollback button to revert changes
2. Resume with:
   ```
   /go TASK-ID
   ```

### Manually Completing a Task

If automation fails:
```
/task_complete TASK-001 "Manually completed - describe what was done"
```

### Resetting a Task

To restart a task from analysis:
1. Edit task file
2. Set `current_phase: "analysis"`
3. Clear findings: `findings: []`
4. Resume: `/go TASK-ID`

## Getting Help

1. Check task status:
   ```
   /task_status
   ```

2. Review task file directly:
   ```bash
   cat .claude/tasks/active/TASK-001.json | python -m json.tool
   ```

3. Check hook output in Claude Code stderr

4. Review completed tasks for working examples:
   ```bash
   ls .claude/tasks/completed/
   ```
