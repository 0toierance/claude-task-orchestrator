---
description: Creates new task from the request and dispatch first agent.
---

# task_create

Creates a new task file with simple sequential ID (TASK-001, TASK-002, etc.), generates context bundle, validates no duplicates exist, and dispatches appropriate agent for initial analysis phase. 
Here is the problem you need to create a task for: $ARGUMENTS 


## Critical Requirements

**YOU MUST:**
1. Scan ALL task directories (active/, blocked/, completed/) to determine next ID
2. Check for duplicate/overlapping tasks before creating
3. Create task file in `.claude/tasks/active/` directory
4. **IMMEDIATELY dispatch selected agent using Task tool after creation**
5. Report task ID, context bundle, and agent dispatched to user

**YOU MUST NOT:**
- Create tasks with overlapping scope (>70% similarity)
- Skip agent dispatch step
- Use date-based IDs (use sequential TASK-001 format)
- Proceed if templates or directories are missing

## Orchestrator Process

### Step 1: Find Next Task ID

**Scan all task directories:**
```bash
# Find all task files across directories
find .claude/tasks -name "TASK-*.json" -type f
```

**Extract highest task number:**
- Parse filenames: `TASK-001.json` → 1, `TASK-002.json` → 2, etc.
- Find maximum number across ALL directories (active/blocked/completed)
- Next ID = max + 1 (e.g., if max is 3, next is `TASK-004`)
- If no tasks exist, start with `TASK-001`

**Format:** Zero-pad to 3 digits (001, 002, ..., 999)

### Step 2: Check for Duplicate Tasks

**Load existing active and blocked tasks:**
```bash
# Read all non-completed tasks
cat .claude/tasks/active/*.json .claude/tasks/blocked/*.json
```

**Compare statement blocks:**
- Extract `definition.statement_block` from each task
- Calculate similarity with new statement_block
- If >70% similar content detected:
  - **STOP** and ask user: "Similar task exists: TASK-XXX. Merge or create new?"
  - Wait for user response before proceeding

**Similarity indicators:**
- Same file paths mentioned
- Same keywords (>50% overlap)
- Same acceptance criteria
- Same component/feature names

### Step 3: Parse Statement Block

Extract from user's statement:
- **Title**: Brief 5-10 word summary of the task
- **Problem description**: What needs to be solved
- **Requirements**: What needs to be done (bulleted list)
- **Constraints**: Limitations, requirements (bulleted list)
- **Context**: Existing code, related work
- **Acceptance criteria**: How to verify completion (bulleted list)

### Step 4: Generate Context Bundle

Analyze keywords in statement to determine relevant context:

**Keyword Mapping:**
- "database", "schema", "query", "postgres", "table", "migration" → `database_operations`
- "api", "endpoint", "route", "request", "response" → `api_design`
- "payment", "stripe", "transaction", "billing" → `payment_processing`
- "realtime", "websocket", "subscription", "live", "polling" → `real_time`
- "auth", "security", "permission", "rls", "session" → `security_protocols`
- "component", "ui", "screen", "design", "style", "animation" → `ui_components`
- "deploy", "build", "cicd", "pipeline", "eas" → `cicd_deployment`
- "integration", "external", "api", "sync", "webhook" → `external_integration`

**Load bundle definitions:**
Read `.claude/context/templates/context-bundles.json` and match to keywords.

**Multiple bundles:**
If task spans multiple areas, combine bundles (e.g., `database_operations + payment_processing`).

### Step 5: Create Task File

**File path:** `.claude/tasks/active/TASK-{id}.json`

**Use template:** `.claude/context/templates/task_template.json`

**CRITICAL: Keep the `_NEEDS_INITIALIZATION` marker!**

The template has `"_NEEDS_INITIALIZATION": true` at the top. **DO NOT remove this marker.** The PostToolUse hook needs it to know this is a new task that requires timestamp initialization.

**Populate fields:**
- `task_id`: `TASK-{zero-padded-id}`
- `created_at`: **Leave as "ISO-8601-TIMESTAMP"** (placeholder - hook will replace)
- `updated_at`: **Leave as "ISO-8601-TIMESTAMP"** (placeholder - hook will replace)
- `status`: `"active"`
- `current_phase`: `"analysis"`
- `definition.title`: Extracted title from statement
- `definition.statement_block`: Full user statement (unchanged)
- `definition.acceptance_criteria`: Extracted criteria array
- `context_bundle.type`: Bundle name(s) from keyword analysis
- `context_bundle.sops`: SOPs from matched bundle
- `context_bundle.system`: System docs from matched bundle
- `context_bundle.code_refs`: Code paths from matched bundle
- `context_bundle.keywords`: Extracted keywords array
- `knowledge_pool`: Initialize empty (findings[], decisions[], blockers[])
- `execution_plan.phases[0]`: Set "analysis" phase to "in_progress"

**What to remove from template:**
- Delete the `_INSTRUCTIONS` section (the template has instructions for you - remove them)

**What to keep:**
- **KEEP** `_NEEDS_INITIALIZATION: true` (hook needs this marker!)
- **KEEP** placeholder timestamps (hook will replace them)

**Write file:**
```bash
# Example path
[your_project_path]/.claude/tasks/active/TASK-004.json

### Step 6: Select Primary Agent

Based on context bundle type, select agent:

**Agent Selection Logic:**
- `database_operations` → **backend-engineer**
- `api_design` → **backend-engineer**
- `payment_processing` → **backend-engineer**
- `real_time` → **backend-engineer**
- `security_protocols` → **security-engineer**
- `ui_components` → **uiux-engineer**
- `cicd_deployment` → **cicd-engineer**
- `external_integration` → **backend-engineer**

**If multiple bundles:**
Select agent matching PRIMARY concern from statement (first mentioned or most critical).

**Default:** If no clear match, use **backend-engineer**.

### Step 7: Dispatch Agent (CRITICAL)

**YOU MUST use the Task tool to invoke the selected agent.**

**Agent invocation template:**
```
Use the Task tool with:
- subagent_type: {selected_agent_type}
- description: "Analyze {task_id}"
- prompt: "Analyze the task at .claude/tasks/active/{TASK-ID}.json. You are in ANALYZE mode. Load the task definition, context bundle, and begin your analysis. Write findings to the knowledge_pool.findings[] array in the task file."
```

**Example Task tool invocation:**
```
Task tool:
  subagent_type: "backend-engineer"
  description: "Analyze TASK-004"
  prompt: "Analyze the task at .claude/tasks/active/TASK-004.json. You are in ANALYZE mode. Load the task definition, context bundle, and begin your analysis. Write findings to the knowledge_pool.findings[] array in the task file."
```

**DO NOT:**
- Skip this step (agent dispatch is MANDATORY)
- Manually summarize the task instead of dispatching
- Wait for user confirmation before dispatching (dispatch immediately after creation)

### Step 8: Report to User

**Output format:**
```
✓ Task {TASK-ID} created successfully

Title: {extracted_title}
Context: {bundle_type}
Priority: {estimated_priority}
Complexity: {estimated_complexity}

Dispatching {agent_name} for analysis phase...
```

**Example output:**
```
✓ Task TASK-004 created successfully

Title: Implement transaction history pagination
Context: database_operations + ui_components
Priority: medium
Complexity: MEDIUM

Dispatching backend-engineer for analysis phase...
```

## Error Handling

### Missing Statement Block
**If:** statement_block is empty or <50 characters
**Action:** Ask clarifying questions:
- What specific problem needs solving?
- What are the acceptance criteria?
- Which parts of the codebase are involved?

### No Context Bundle Match
**If:** No keywords match any bundle
**Action:**
- Use `database_operations` as default bundle
- Dispatch **backend-engineer** for general analysis
- Note in report: "Using general context (no specific keywords matched)"

### Template Files Missing
**If:** Cannot read task_template.json or context-bundles.json
**Action:**
- Report error: "Template files missing. Cannot create task."
- Suggest checking `.claude/context/templates/` directory
- **DO NOT** create task without template

### Task Directory Missing
**If:** `.claude/tasks/active/` doesn't exist
**Action:**
- Create directory: `mkdir -p .claude/tasks/active`
- Proceed with task creation
- Verify blocked/ and completed/ exist, create if needed

### Duplicate Task Detected
**If:** >70% similarity with existing task
**Action:**
- Show comparison:
  ```
  ⚠ Similar task found: TASK-XXX

  Existing: {existing_title}
  New: {new_title}

  Similarity: 85%

  Options:
  1. Merge with TASK-XXX
  2. Create new task anyway
  3. Cancel
  ```
- Wait for user choice before proceeding

### Agent Selection Ambiguous
**If:** Multiple context bundles with equal priority
**Action:**
- Ask user: "Multiple domains detected (database + ui). Which should take priority?"
- Wait for response
- Select agent based on user's priority

## Validation Checklist

Before dispatching agent, verify:
- ✓ Task ID is unique (not in active/blocked/completed)
- ✓ Task file created at correct path
- ✓ JSON is valid (parseable)
- ✓ Context bundle loaded successfully
- ✓ Agent type is valid (one of: backend-engineer, uiux-engineer, security-engineer, cicd-engineer)
- ✓ Task tool will be invoked (DO NOT skip)

## Related Commands

- `/task_status` - Check task progress after creation
- `/go` - Resume work on created task
- `/advance_phase` - Move task to next phase after analysis
- `/query_findings` - Search findings in task knowledge pool

## Examples

### Example 1: Database Task
```
User: /task_create I need to add pagination to the transaction history. Users should be able to load 20 transactions at a time. Need to update the transactions table query and add offset/limit support.

Orchestrator actions:
1. Scan tasks: TASK-001, TASK-002, TASK-003 exist → Next ID: TASK-004
2. No duplicates found
3. Extract keywords: "pagination", "transaction", "query" → database_operations
4. Create TASK-004.json with context_bundle: database_operations
5. Select agent: backend-engineer
6. Dispatch: Task tool → backend-engineer analyzing TASK-004
7. Report: "✓ Task TASK-004 created. Context: database_operations. Dispatching backend-engineer..."
```

### Example 2: UI Component Task
```
User: /task_create Need to fix the overlapping skeleton loaders on the catalog screen. They're rendering on top of each other during initial load. Should show single clean loader then transition smoothly.

Orchestrator actions:
1. Scan tasks: Existing tasks 001-004 → Next ID: TASK-005
2. No duplicates (no similar "skeleton" or "catalog" tasks in active/blocked)
3. Extract keywords: "skeleton", "catalog", "screen", "loader", "ui" → ui_components
4. Create TASK-005.json with context_bundle: ui_components
5. Select agent: uiux-engineer
6. Dispatch: Task tool → uiux-engineer analyzing TASK-005
7. Report: "✓ Task TASK-005 created. Context: ui_components. Dispatching uiux-engineer..."
```

### Example 3: Multi-Domain Task
```
User: /task_create We need to implement real-time balance updates. When a payment comes through the payment provider, the balance should update immediately on the user's screen without refresh. This involves webhooks, database triggers, and real-time subscriptions.

Orchestrator actions:
1. Scan tasks: Existing tasks 001-005 → Next ID: TASK-006
2. No duplicates found
3. Extract keywords: "payment", "stripe", "webhook", "realtime", "subscription", "database" → payment_processing + real_time + database_operations
4. Primary concern: "real-time updates" (user's main focus)
5. Create TASK-006.json with context_bundle: real_time + payment_processing
6. Select agent: backend-engineer (covers both domains)
7. Dispatch: Task tool → backend-engineer analyzing TASK-006
8. Report: "✓ Task TASK-006 created. Context: real_time + payment_processing. Dispatching backend-engineer..."
```

### Example 4: Duplicate Detection
```
User: /task_create Add pagination to transactions list

Orchestrator actions:
1. Scan tasks: TASK-004 exists with title "Implement transaction history pagination"
2. Compare:
   - Existing: "pagination", "transactions", "history"
   - New: "pagination", "transactions", "list"
   - Similarity: 80% (4/5 keywords match)
3. STOP and ask:
   ```
   ⚠ Similar task found: TASK-004

   Existing: Implement transaction history pagination
   New: Add pagination to transactions list

   Similarity: 80%

   Options:
   1. Continue with TASK-004 (recommended)
   2. Create new task anyway
   3. Cancel
   ```
4. Wait for user response before proceeding
```

## Implementation Notes

### Task ID Generation Algorithm
```javascript
// Pseudocode for task ID generation
function findNextTaskId() {
  const taskFiles = glob('.claude/tasks/**/*.json')
  const taskNumbers = taskFiles
    .map(f => f.match(/TASK-(\d+)\.json/))
    .filter(m => m !== null)
    .map(m => parseInt(m[1], 10))

  const maxId = taskNumbers.length > 0 ? Math.max(...taskNumbers) : 0
  const nextId = maxId + 1

  return `TASK-${nextId.toString().padStart(3, '0')}`
}
```

### Similarity Calculation
Consider these factors when comparing tasks:
- **Keywords overlap**: Count matching words (>50% = similar)
- **File paths**: Same files mentioned = very likely duplicate
- **Acceptance criteria**: Similar goals = likely duplicate
- **Component names**: Same UI component/service = likely duplicate

### Context Bundle Selection Priority
When multiple bundles match:
1. **Security** takes precedence (always include security-engineer)
2. **Primary domain** from first-mentioned keyword
3. **Backend** as default for technical tasks
4. **UI/UX** for visual/component tasks

### Agent Dispatch Verification
After dispatching agent, verify:
- Task tool was invoked (not just mentioned)
- Agent receives correct task file path
- Agent mode is set to ANALYZE
- Agent has necessary context bundle access

## Success Criteria

Task creation is successful when:
1. ✓ Task file created at `.claude/tasks/active/TASK-{id}.json`
2. ✓ JSON is valid and matches template structure
3. ✓ No duplicate tasks exist with >70% similarity
4. ✓ Context bundle properly loaded and assigned
5. ✓ Agent dispatched via Task tool (not skipped)
6. ✓ User receives confirmation with task ID and agent name