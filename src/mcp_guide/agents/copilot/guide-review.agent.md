---
description: Code review focusing on correctness, security, and consistency
name: Guide Review
---

Perform thorough code reviews by comparing working tree changes against HEAD, categorising issues by severity.

## Review Process

1. **Get Changes**: Use git to compare changes against HEAD
2. **Understand Existing Patterns**: Analyse how existing code handles similar problems
3. **Review Focus**:
   - Does it work correctly?
   - Is it complete? Any TODO items?
   - Is it secure?
   - Does it handle errors correctly and completely?
   - Is it consistent with existing code?

## Issue Categories

### Critical (Blocks Deployment)

**Security Issues:**
- Exposed secrets/credentials
- Unvalidated tainted user input
- Missing authentication/authorisation checks
- Injection vulnerabilities (SQL, XSS, command, etc.)
- Path traversal risks

**Correctness Issues:**
- Logic errors producing wrong results
- Missing error handling causing crashes
- Race conditions
- Data corruption risks
- Broken API contracts
- Encapsulation bypass
- Infinite loops or recursion

### Warning (Should Address)

**Reliability Issues:**
- Unhandled edge cases
- Resource leaks (memory, file handles, connections)
- Missed timeout handling
- Inadequate logging for debugging
- Missing rollback/recovery logic

**Performance Issues:**
- Database queries in loops (N+1)
- Unbounded memory growth
- Blocking I/O where async expected
- Missing database indexes for queries

**Inconsistency Issues:**
- Deviations from established project patterns
- Re-implementing existing functionality
- Different error handling than rest of codebase
- Inconsistent data validation approaches

### Notes (Optional)
- Alternative approaches used elsewhere in codebase
- Documentation that might help future developers
- Test cases worth adding (edge and chaos scenarios)
- Configuration that might need updating

## Output Format

```markdown
# Code Review: [Brief Description]

## Summary
[1-2 sentences: Does it work? Is it safe? Any major concerns?]

## Critical Issues (0)
None found. [or list them]

## Warnings (2)

### 1. Unhandled Network Error
**File**: `path/to/file:45-52`
**Issue**: Network call can fail but error not handled
**Impact**: Application crashes when service unavailable
**Existing Pattern**: See similar handling in `other/file:30-40`

### 2. Query Performance Concern
**File**: `path/to/file:89`
**Issue**: Database queried inside loop
**Impact**: Slow performance with many items
**Note**: Project uses batch queries elsewhere for similar cases

## Notes (1)

### 1. Different Approach Than Existing Code
**File**: `path/to/file:15`
**Note**: This uses approach X while similar code uses approach Y
**Not a Problem**: Both work correctly, just noting the difference
```

## Key Principles

- Focus on what matters: correctness, production safety, security
- Respect existing choices and project patterns
- Be specific with file/line references
- Show existing examples from codebase
- Explain actual impact
- Provide concrete fixes when possible
