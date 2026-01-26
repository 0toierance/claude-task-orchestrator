# Context Bundles

How to define and use context bundles for intelligent document routing.

## What Are Context Bundles?

Context bundles are pre-computed mappings that connect keywords to relevant documentation. When you create a task, the orchestrator:

1. Extracts keywords from your task description
2. Matches keywords to bundle definitions
3. Loads the associated SOPs, system docs, and code references
4. Provides this context to the agent

## Bundle Structure

Bundles are defined in `.claude/context/templates/context-bundles.json`:

```json
{
  "bundle_name": {
    "description": "When this bundle applies",
    "sops": ["sop-file.md"],
    "system": ["system-doc.md"],
    "code_refs": ["/src/path/**/*.ts"]
  }
}
```

### Fields

| Field | Description |
|-------|-------------|
| `description` | Human-readable explanation of when this bundle applies |
| `sops` | Array of SOP filenames from `context/sops/` |
| `system` | Array of system doc filenames from `context/system/` |
| `code_refs` | Array of glob patterns for relevant code |

## Default Bundles

The orchestrator includes these default bundles:

### database_operations
```json
{
  "description": "Database schema design, migrations, query optimization",
  "sops": ["database-optimization.md", "security-protocols.md"],
  "system": ["architecture.md"],
  "code_refs": ["/src/db/**/*.sql", "/src/db/**/*.ts"]
}
```

**Keywords**: database, schema, query, postgres, table, migration, sql

### api_design
```json
{
  "description": "REST/GraphQL endpoints, API contracts",
  "sops": ["api-design-standards.md", "security-protocols.md"],
  "system": ["architecture.md"],
  "code_refs": ["/src/api/**/*.ts", "/src/routes/**/*.ts"]
}
```

**Keywords**: api, endpoint, route, request, response, rest, graphql

### ui_components
```json
{
  "description": "React/React Native components, styling, animations",
  "sops": ["ui-design-standards.md"],
  "system": ["component-library.md"],
  "code_refs": ["/src/components/**/*.tsx", "/src/screens/**/*.tsx"]
}
```

**Keywords**: component, ui, screen, design, style, animation, button, modal

### security_protocols
```json
{
  "description": "Auth, encryption, audit trails",
  "sops": ["security-protocols.md"],
  "system": ["architecture.md"],
  "code_refs": ["/src/auth/**/*.ts"]
}
```

**Keywords**: auth, security, permission, encrypt, session, token, jwt

### cicd_deployment
```json
{
  "description": "Build pipelines, deployments, monitoring",
  "sops": ["deployment-checklist.md"],
  "system": ["architecture.md"],
  "code_refs": ["/.github/workflows/**", "/eas.json"]
}
```

**Keywords**: deploy, build, cicd, pipeline, github, actions, release

## Creating Custom Bundles

### Step 1: Identify the Domain

What area of your codebase does this cover?
- Payment processing
- Machine learning
- Real-time features
- Third-party integrations

### Step 2: Define the Bundle

```json
{
  "payment_processing": {
    "description": "Stripe integration, transactions, PCI compliance",
    "sops": [
      "payment-handling.md",
      "security-protocols.md"
    ],
    "system": [
      "stripe-integration.md",
      "architecture.md"
    ],
    "code_refs": [
      "/src/payments/**/*.ts",
      "/src/billing/**/*.ts"
    ]
  }
}
```

### Step 3: Identify Keywords

What words would someone use when describing tasks in this domain?

For payment_processing:
- payment, stripe, transaction, billing
- checkout, cart, order, purchase
- refund, subscription, invoice

### Step 4: Update Agent Routing

In the `/task_create` command, add routing for your bundle:

```markdown
### Keyword Mapping
- "payment", "stripe", "checkout", "billing" → `payment_processing`
```

And agent selection:
```markdown
### Agent Selection
- `payment_processing` → **backend-engineer**
```

## Combining Bundles

Tasks often span multiple domains. The orchestrator can combine bundles:

```json
{
  "context_bundle": {
    "type": "database_operations + payment_processing",
    "sops": [
      "database-optimization.md",
      "security-protocols.md",
      "payment-handling.md"
    ],
    "system": [
      "architecture.md",
      "stripe-integration.md"
    ],
    "code_refs": [
      "/src/db/**/*.ts",
      "/src/payments/**/*.ts"
    ]
  }
}
```

## Best Practices

### 1. Keep Bundles Focused
Don't create one giant bundle. Smaller, focused bundles combine better.

### 2. Avoid Documentation Overlap
If multiple bundles include the same SOP, that's okay. But avoid redundancy in what the SOP covers.

### 3. Use Specific Code Refs
More specific globs = less irrelevant code loaded:
- Good: `/src/payments/stripe/**/*.ts`
- Less good: `/src/**/*.ts`

### 4. Document Bundle Purpose
The `description` field helps both you and the orchestrator understand when to use it.

### 5. Test Bundle Selection
Create test tasks and verify correct bundles are selected:
```
/task_create "Add Stripe webhook handler"
/task_status  # Check context_bundle.type
```

## Troubleshooting

### "Wrong bundle selected"
1. Check keywords in your task description
2. Review keyword mappings in /task_create command
3. Use explicit domain prefix: "Database: optimize user queries"

### "Missing documentation in context"
1. Verify file exists at specified path
2. Check filename spelling in bundle definition
3. Ensure path is relative to `context/sops/` or `context/system/`

### "Too much irrelevant code loaded"
1. Make code_refs more specific
2. Split into multiple focused bundles
3. Use file extensions: `**/*.ts` not `**/*`
