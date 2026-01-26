# Writing Effective SOPs

Guide to creating Standard Operating Procedures that agents can follow.

## What Are SOPs?

SOPs (Standard Operating Procedures) are documented procedures for common tasks. They:

- Capture institutional knowledge
- Prevent repeated mistakes
- Ensure consistency across implementations
- Guide agents toward proven patterns

## SOP Structure

Every SOP should follow this structure:

```markdown
# [Topic] Standard Operating Procedure

## When to Use
- Scenario 1
- Scenario 2

## Prerequisites
- What must be in place before starting

## Procedure

### Step 1: [Action]
Detailed explanation with code examples.

### Step 2: [Action]
Detailed explanation with code examples.

## Common Pitfalls
- Pitfall 1: Description and how to avoid
- Pitfall 2: Description and how to avoid

## Checklist
- [ ] Verification item 1
- [ ] Verification item 2

## Examples

### Example 1: [Scenario]
Complete worked example.

## Related Documents
- Link to related SOP
- Link to system doc
```

## Writing Guidelines

### Be Specific

Don't: "Use proper error handling"
Do: "Wrap database operations in try/catch, log errors with context, return typed error objects"

### Include Code Examples

```markdown
### Step 2: Implement Error Handling

```typescript
try {
  const result = await db.query(sql, params);
  return { success: true, data: result };
} catch (error) {
  logger.error('Query failed', { sql, params, error });
  return { success: false, error: new DatabaseError(error.message) };
}
```
```

### Document Pitfalls

Agents learn from mistakes. Document common issues:

```markdown
## Common Pitfalls

### N+1 Query Problem
**What happens**: Looping over results and making individual queries.
**Why it's bad**: 100 items = 100 queries = slow.
**How to avoid**: Use JOINs or batch queries.

```typescript
// BAD
for (const user of users) {
  const orders = await getOrders(user.id);
}

// GOOD
const orders = await getOrdersForUsers(users.map(u => u.id));
```
```

### Provide Checklists

Checklists ensure nothing is missed:

```markdown
## Pre-Deployment Checklist

- [ ] All tests pass locally
- [ ] No TypeScript errors
- [ ] Environment variables documented
- [ ] Database migrations tested
- [ ] Rollback procedure verified
- [ ] Monitoring alerts configured
```

## SOP Categories

### Technical SOPs
- Database optimization
- API design standards
- Performance optimization
- Security protocols

### Process SOPs
- Deployment procedures
- Code review guidelines
- Incident response
- Release management

### Integration SOPs
- Third-party API integration
- Authentication flows
- Data synchronization

## Example: API Design SOP

```markdown
# API Design Standard Operating Procedure

## When to Use
- Creating new API endpoints
- Modifying existing API contracts
- Designing request/response schemas

## Prerequisites
- API framework set up (Express, Fastify, etc.)
- Error handling middleware in place
- Authentication middleware configured

## Procedure

### Step 1: Define the Resource

Identify the resource and its relationships:
- Resource name (singular): `user`, `order`, `product`
- Related resources: `user has many orders`
- Operations needed: CRUD, custom actions

### Step 2: Design Endpoint Paths

Follow REST conventions:
```
GET    /users          # List users
POST   /users          # Create user
GET    /users/:id      # Get user
PATCH  /users/:id      # Update user
DELETE /users/:id      # Delete user

# Custom actions
POST   /users/:id/verify   # Verify user
```

### Step 3: Define Request Schema

```typescript
interface CreateUserRequest {
  email: string;
  name: string;
  role?: 'user' | 'admin';
}
```

### Step 4: Define Response Schema

```typescript
interface UserResponse {
  id: string;
  email: string;
  name: string;
  role: string;
  createdAt: string;
}

interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, string>;
  };
}
```

### Step 5: Implement with Validation

```typescript
router.post('/users', async (req, res) => {
  const validation = validateCreateUser(req.body);
  if (!validation.success) {
    return res.status(400).json({
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid request body',
        details: validation.errors
      }
    });
  }

  const user = await userService.create(req.body);
  return res.status(201).json(user);
});
```

## Common Pitfalls

### Inconsistent Naming
**Problem**: Mixing `/getUsers`, `/user/list`, `/users`
**Solution**: Always use plural nouns, no verbs in paths

### Missing Error Cases
**Problem**: Only handling happy path
**Solution**: Document all error responses:
- 400: Validation error
- 401: Unauthorized
- 403: Forbidden
- 404: Not found
- 409: Conflict
- 500: Internal error

### Breaking Changes Without Versioning
**Problem**: Changing response format breaks clients
**Solution**: Version APIs: `/v1/users`, `/v2/users`

## Checklist

- [ ] Endpoint follows REST conventions
- [ ] Request schema defined with validation
- [ ] Response schema defined
- [ ] All error cases documented
- [ ] Authentication/authorization considered
- [ ] Rate limiting considered
- [ ] Tests written for happy path and errors

## Related Documents
- [security-protocols.md](security-protocols.md) - Authentication patterns
- [system/architecture.md](../system/architecture.md) - Service layer patterns
```

## Maintaining SOPs

### When to Update
- After discovering a new pitfall
- When patterns evolve
- After post-mortems reveal gaps
- When onboarding surfaces unclear areas

### Versioning
Consider adding version info:
```markdown
---
Version: 2.1
Last Updated: 2025-01-15
Author: Team
---
```

### Cross-References
Link related SOPs and system docs to create a knowledge web.

## Using SOPs in Tasks

### Agent Reference
Agents automatically receive SOPs via context bundles. They should cite SOPs in findings:

```json
{
  "content": {
    "recommendation": "Use batch queries per database-optimization.md Section 3",
    "sop_reference": "sops/database-optimization.md#batch-queries"
  }
}
```

### User Reference
When resolving decisions, reference SOPs:
```
/resolve_decision D-001 "Use JWT per security-protocols.md - session tokens section"
```

## Extracting SOPs from Tasks

After completing tasks, extract reusable patterns:

```
/document_learnings TASK-001
```

This analyzes the completion summary and suggests SOP updates.
