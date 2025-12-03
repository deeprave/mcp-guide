# Change: Add Collection Management Tools

**Status**: Selected for Development
**Jira**: GUIDE-101, GUIDE-102 (with subtasks GUIDE-103 to GUIDE-107), GUIDE-108

## Why

Collections group related categories for organized content access. Currently, there's no standardized way to manage collections through tools. We need:

- Tools to add, remove, change, and update collections
- Validation of collection names, descriptions, and category references
- Safe operations that maintain configuration integrity
- Result pattern responses with clear error handling
- Validation that referenced categories exist

## What Changes

### Validation Functions (GUIDE-101)
- Implement category reference validation
- Implement category existence checks
- Reuse existing name and description validation from category tools

### Collection Management Tools (GUIDE-102)
Five tools implemented with TDD methodology:

1. **collection_list** (GUIDE-103) - List all collections with categories
2. **collection_add** (GUIDE-104) - Create new collection
3. **collection_remove** (GUIDE-105) - Delete collection
4. **collection_change** (GUIDE-106) - Replace collection configuration
5. **collection_update** (GUIDE-107) - Modify specific fields (add/remove categories)

Each tool:
- Uses @tools.tool decorator
- Returns Result pattern responses with instructions
- Validates category references
- Persists changes to project configuration
- Includes integrated unit tests (TDD)

### Integration Testing (GUIDE-108)
- End-to-end CRUD workflow tests
- Category validation integration
- Configuration persistence verification
- Error case handling

### Configuration Persistence
- Reuses safe configuration write from category tools
- No separate implementation needed

## Impact

- **New capability**: collection-tools
- **Affected code**: New tools module, configuration management
- **Dependencies**: Result pattern (ADR-003), tool conventions (ADR-008), session management, category tools
- **Breaking changes**: None (new tools)
- **Validation**: Ensures referenced categories exist

## Implementation Approach

- **TDD methodology**: Tests integrated with implementation, not separate tasks
- **3 stories, 5 subtasks**: Total 8 Jira cards
- **No separate documentation**: Tools are self-documenting via schemas
