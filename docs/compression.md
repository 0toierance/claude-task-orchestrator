# Compression System

How the orchestrator manages context across phases through intelligent compression.

## The Problem

Claude has a limited context window. Without compression:

| Phase | Context | Previous Findings | Total |
|-------|---------|-------------------|-------|
| Analysis | 35K | 0 | 35K ✓ |
| Design | 35K | 7.2K | 42.2K ⚠️ |
| Implementation | 35K | 12K | 47K ❌ |

By the implementation phase, we'd overflow the context.

## The Solution

Compress findings between phases, keeping only essential information:

| Phase | Context | Compressed | Critical | Total |
|-------|---------|------------|----------|-------|
| Analysis | 35K | 0 | 0 | 35K ✓ |
| Design | 35K | 450 | 1,350 | 36.8K ✓ |
| Implementation | 35K | 600 | 2,000 | 37.6K ✓ |

## How Compression Works

### Step 1: Identify Critical Findings

Not all findings are equally important. The system identifies critical findings based on:

- **Tags**: Findings tagged `["critical"]`
- **Dependencies**: Findings that other findings depend on
- **Confidence**: Findings with confidence > 0.9
- **Categories**: Design-related categories in analysis, implementation-ready in design

### Step 2: Generate Compressed Brief

The remaining findings are summarized into a brief:

**Before (7,200 tokens):**
```json
{
  "findings": [
    {
      "id": "F-001",
      "category": "existing_patterns",
      "content": {
        "pattern_name": "Service layer pattern",
        "location": "/src/services/[service_name].ts",
        "description": "Existing pattern for data access through service classes...",
        "reusability": "High - can extend for new features",
        "gaps": "Missing error handling standardization"
      }
    },
    // ... 15 more detailed findings
  ]
}
```

**After (450 tokens):**
```json
{
  "phase_compressions": {
    "analysis": {
      "brief": "Analysis identified service layer pattern at /src/services/ suitable for extension. Key dependencies: PostgreSQL [sessions_table] table, Redis cache layer. Primary risks: race condition in concurrent session updates (HIGH), missing rate limiting (MEDIUM). Database needs: sessions table with user_id foreign key, expires_at timestamp, device_info JSONB.",
      "critical_findings": ["F-003", "F-007", "F-012"],
      "token_count": 450
    }
  }
}
```

### Step 3: Pass to Next Phase

The next phase agent receives:
1. **Compressed brief** (~450 tokens)
2. **Critical findings in full** (3-5 findings, ~1,350 tokens)
3. **Context bundle** (SOPs, system docs)

## Compression Algorithm

```python
def compress_phase(task, phase_name):
    findings = get_findings_for_phase(task, phase_name)

    # 1. Identify critical findings (keep full detail)
    critical = identify_critical(findings)

    # 2. Generate brief from remaining findings
    non_critical = [f for f in findings if f not in critical]
    brief = generate_brief(non_critical)

    # 3. Store compression
    task["knowledge_pool"]["phase_compressions"][phase_name] = {
        "brief": brief,
        "critical_findings": [f["id"] for f in critical],
        "token_count": count_tokens(brief)
    }

    return task
```

## Token Budgets

### Analysis Phase
- **Input**: Context bundle + task definition
- **Budget**: ~35,000 tokens
- **Output**: Up to 7,200 tokens in findings

### Design Phase
- **Input**: Compressed analysis (450) + critical findings (1,350) + context bundle
- **Budget**: ~36,800 tokens
- **Output**: Up to 4,800 tokens in findings

### Implementation Phase
- **Input**: Compressed design (600) + critical design findings (2,000) + context bundle
- **Budget**: ~37,600 tokens
- **Output**: Variable (code artifacts tracked separately)

## What Gets Preserved

### Always Preserved (Critical Findings)
- Findings tagged `["critical"]`
- Findings with `implementation_ready: true`
- Findings referenced as dependencies by other critical findings
- High-confidence (>0.9) findings in key categories

### Summarized (In Brief)
- Pattern locations and reusability assessments
- Dependency lists (tables, APIs, services)
- Risk summaries with severity
- Database schema outlines

### Discarded
- Verbose explanations
- Alternative approaches not chosen
- Low-confidence speculative findings
- Redundant information

## Manual Compression

You can trigger compression manually:

```
/compress_phase analysis
```

This is rarely needed since `/advance_phase` handles it automatically.

## Viewing Compressions

Check what was compressed:

```
/task_status
```

Or read the task file directly:
```json
{
  "knowledge_pool": {
    "phase_compressions": {
      "analysis": {
        "brief": "...",
        "critical_findings": ["F-001", "F-003"],
        "token_count": 423
      }
    }
  }
}
```

## Best Practices

### For Agents
1. **Tag critical findings** - Use `["critical"]` tag for must-preserve information
2. **Be specific in content** - Vague findings compress poorly
3. **Link dependencies** - Critical finding chains are preserved together
4. **Set implementation_ready** - Design findings with this flag are always preserved

### For Users
1. **Review before advancing** - Check critical findings make sense
2. **Resolve decisions first** - Unresolved decisions can't be compressed properly
3. **Don't over-tag critical** - If everything is critical, compression fails

## Troubleshooting

### "Too many critical findings"
If compression results in >5 critical findings, consider:
- Were too many findings tagged critical?
- Can some be consolidated?
- Is the task scope too large?

### "Important information lost"
If design agent is missing context:
- Was the finding tagged critical?
- Was it linked as a dependency?
- Consider `/add_finding` to manually add missing information

### "Compression failed"
Check:
- Are all findings valid JSON?
- Are token counts calculated?
- Is tiktoken installed?
