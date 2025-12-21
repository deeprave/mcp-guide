# dict-based-config Change Proposal

## Summary
Convert categories and collections from list-based to dictionary-based configuration for better duplicate prevention and performance.

## Problem
Current list-based configuration requires:
- Manual duplicate detection with linear traversal (O(n) lookups)
- Explicit validation logic in every tool
- More complex "already exists" checking

Dictionary-based configuration would provide:
- Automatic duplicate prevention at YAML parsing level
- O(1) lookups by name
- Simpler validation logic
- Preserved insertion order (Python 3.7+ guarantee)

## Solution
Convert configuration structure from:
```yaml
categories:
- name: guide
  dir: guide/
  patterns: [guidelines]
```

To:
```yaml
categories:
  guide:
    dir: guide/
    patterns: [guidelines]
```

**Key Changes:**
1. **Models**: Update `Project` model to use `dict[str, Category]` and `dict[str, Collection]`
2. **Template Context**: Ensure category/collection names are injected into template contexts
3. **Tool Logic**: Simplify duplicate detection (dict key existence vs linear search)
4. **Validation**: Remove manual duplicate checking, rely on dict key uniqueness
5. **Serialization**: Update YAML serialization/deserialization

## Scope
- Configuration models (`Project`, `Category`, `Collection`)
- All category and collection tools
- Template context building
- Configuration serialization/deserialization
- All tests and validation logic

## Dependencies
- Breaking change requiring configuration migration
- All existing tools that access categories/collections
- Template rendering system

## Non-Goals
- Changing tool APIs (arguments/responses remain the same)
- Modifying MCP tool registration
- Altering file discovery or content tools
