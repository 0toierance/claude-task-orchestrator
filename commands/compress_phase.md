---
description: Manually trigger compression of findings from specified phase
---

# compress_phase

Manually compresses findings from a specified phase to reduce token usage. Normally done automatically by `/advance_phase`, but can be triggered manually for testing or troubleshooting.

## Usage
```
/compress_phase {phase_name} [task_id]
```

**Parameters:**
- `{phase_name}` - Phase to compress (analysis, design, validation, implementation)
- `[task_id]` (optional) - Specific task. If omitted, use current active task.

## Orchestrator Process

### 1. Load Task
- If task_id provided: Load that task
- If omitted: Load current active task
- Verify task exists

### 2. Validate Phase
- Check that specified phase exists in task
- Verify phase has findings to compress
- Check if already compressed (warn if re-compressing)

### 3. Collect Phase Findings
From `task.knowledge_pool.findings[]`:
- Filter findings where `phase == {phase_name}`
- Count total findings
- Calculate total token count

### 4. Generate Compressed Brief
Create compressed summary (450-600 tokens):

**Extract:**
- **Summary**: One-paragraph overview of phase work (100-150 tokens)
- **Critical Findings**: Identify 3-5 most important findings by:
  - Confidence score
  - Tags (critical, security, blocking)
  - Dependencies (findings many others depend on)
- **Must Address**: Key points for next phase (50-100 tokens)
- **Decisions Resolved**: Summary of resolved decisions affecting this phase

**Structure:**
```json
{
  "total_findings": 8,
  "total_tokens": 7200,
  "compressed_brief": {
    "tokens": 450,
    "summary": "Need 3 tables ([transactions_table], [releases_table], [audit_table]). Critical risks: race conditions in dual-approval. Reuse dual-signature pattern from /src/transactions/processing.ts.",
    "critical_findings": ["F-002", "F-003", "F-007"],
    "must_address": [
      "Race condition requires PostgreSQL advisory locks",
      "Timeout enforcement via DB triggers"
    ],
    "decisions_resolved": {
      "D-001": "Timeout configurable 24-72h"
    }
  },
  "compression_strategy": "extract_critical_only"
}
```

### 5. Calculate Savings
- Original tokens: [count]
- Compressed tokens: [count]
- Savings: [percentage]

### 6. Save to Task
Write to `task.knowledge_pool.phase_compressions[{phase_name}]`

### 7. Report to User
```
EXAMPLE OUTPUT:
Compressing analysis phase:
  8 findings, 7,200 tokens
  Compressed brief: 450 tokens
  Critical findings: F-002, F-003, F-007 (1,350 tokens)
  
Savings: 5,400 tokens (75%)
Updated task file
```

## When to Use Manually

**Troubleshooting:**
- Test compression before advancing phase
- Verify token counts are reasonable
- Check which findings marked as critical

**Re-compression:**
- After adding findings to already-compressed phase
- After updating finding confidence scores
- To change compression strategy

**Optimization:**
- Experiment with different compression strategies
- Verify critical findings selection is correct

## Error Handling
- Phase not found: List available phases
- No findings in phase: "Phase has no findings to compress"
- Task not found: List available tasks

## Related Commands
- `/advance_phase` - Automatically compresses when advancing
- `/query_findings` - See which findings will be compressed