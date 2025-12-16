# Design: Collection Management Tools

## Context

Collections group related categories for organized content access. Currently, collections can only be managed by manually editing configuration files. We need tools to manage collections programmatically with proper validation and referential integrity checks.

## Goals

- Provide CRUD operations for collections
- Validate all inputs including category references
- Maintain configuration integrity
- Use Result pattern for consistent error handling
- Ensure referenced categories exist

## Non-Goals

- Managing collection content (delegated to categories)
- Validating category directories exist on disk
- Batch operations (multiple collections at once)
- Automatic category creation

## Decisions

### Four-Tool Design

**Decision:** Provide four separate tools: add, remove, change, update

**Rationale:**
- `add`: Create new collection (all fields)
- `remove`: Delete collection (simple, destructive)
- `change`: Replace entire configuration (rename, replace categories)
- `update`: Modify specific fields (add/remove categories incrementally)
- Mirrors category tools design for consistency
- Clear separation between replace (change) and modify (update)

**Alternatives considered:**
- Single tool with operation parameter - Less discoverable
- Only add/remove/update - No way to replace all categories at once

### Category Reference Validation

**Decision:** Validate that all referenced categories exist before creating/updating collection

**Rationale:**
- Maintains referential integrity
- Prevents broken references
- Fails fast with clear error
- Lists all missing categories in error message

**Behavior:**
```python
# Validate all categories exist
missing = [c for c in categories if c not in config.categories]
if missing:
    return Result.failure(
        error=f"Categories not found: {', '.join(missing)}",
        error_type="category_not_found"
    )
```

### Change vs Update Semantics

**Decision:** `change` replaces, `update` modifies (same as category tools)

**change:**
- Replaces entire configuration
- Can rename collection
- Replaces all categories (not additive)
- Use when you want to set exact state

**update:**
- Modifies specific fields
- Cannot rename (use change for that)
- Adds/removes categories incrementally
- Use when you want to adjust existing state

**Rationale:**
- Consistent with category tools
- Clear distinction between replace and modify
- Supports both use cases
- Prevents accidental data loss

### Validation Strategy

**Decision:** Validate all inputs before any configuration changes

**Rationale:**
- Fail fast on invalid input
- Prevent partial updates
- Clear error messages
- Referential integrity

**Validation layers:**
1. Type checking (schema validation)
2. Format validation (name, description)
3. Existence validation (collection exists/doesn't exist)
4. Reference validation (categories exist)

### No Auto-Creation of Categories

**Decision:** Do not automatically create categories that don't exist

**Rationale:**
- Explicit is better than implicit
- Categories require directory and pattern configuration
- User should create categories intentionally
- Clear error message guides user to create category first

### Configuration Persistence

**Decision:** Reuse file locking and validation from category tools

**Rationale:**
- Consistent behavior across tools
- Already implemented and tested
- Same concurrency concerns
- Same validation requirements

## Implementation Notes

### Validation Functions

```python
def validate_collection_name(name: str) -> Result[None]:
    """Validate collection name (reuse category validation)."""
    return validate_category_name(name)

def validate_category_references(
    categories: list[str],
    config: ProjectConfig
) -> Result[None]:
    """Validate all categories exist."""
    missing = [c for c in categories if c not in config.categories]
    if missing:
        return Result.failure(
            error=f"Categories not found: {', '.join(missing)}",
            error_type="category_not_found",
            instruction="Create missing categories first using category_add."
        )
    return Result.ok(None)
```

### Tool Structure

```python
async def collection_add(
    name: str,
    description: Optional[str] = None,
    categories: Optional[list[str]] = None
) -> str:
    """Add new collection."""
    session = get_current_session()
    if not session:
        return Result.failure(
            error="No active session",
            error_type="no_session"
        ).to_json_str()

    # Validate inputs
    result = validate_collection_name(name)
    if result.is_failure():
        return result.to_json_str()

    # Check doesn't exist
    config = await session.get_project()
    if name in config.collections:
        return Result.failure(
            error=f"Collection '{name}' already exists",
            error_type="already_exists"
        ).to_json_str()

    # Validate category references
    cats = categories or []
    result = validate_category_references(cats, config)
    if result.is_failure():
        return result.to_json_str()

    # Create collection
    collection = Collection(
        name=name,
        description=description,
        categories=cats
    )

    # Persist
    config.collections[name] = collection
    await session.save_project(config)

    return Result.ok(
        value=f"Collection '{name}' created"
    ).to_json_str()
```

### Update Logic

```python
async def collection_update(
    name: str,
    add_categories: Optional[list[str]] = None,
    remove_categories: Optional[list[str]] = None
) -> str:
    """Update collection categories."""
    # ... validation ...

    collection = config.collections[name]

    # Remove first
    if remove_categories:
        collection.categories = [
            c for c in collection.categories
            if c not in remove_categories
        ]

    # Then add
    if add_categories:
        # Validate new categories exist
        result = validate_category_references(add_categories, config)
        if result.is_failure():
            return result.to_json_str()

        # Add without duplicates
        for cat in add_categories:
            if cat not in collection.categories:
                collection.categories.append(cat)

    # Persist
    await session.save_project(config)

    return Result.ok(
        value=f"Collection '{name}' updated"
    ).to_json_str()
```

## Dependencies

- Result pattern (ADR-003)
- Tool conventions (ADR-008)
- Session management (existing)
- Configuration models (existing)
- File locking (from category tools)
- Validation functions (from category tools)

## Risks / Trade-offs

**Risk:** Category reference validation may be too strict
- **Mitigation:** Clear error message with missing categories
- **Mitigation:** Instruction to create categories first

**Trade-off:** No auto-creation of categories
- **Benefit:** Explicit, predictable behavior
- **Cost:** Extra step for users
- **Decision:** Explicitness is worth the cost

**Trade-off:** Four tools vs fewer parameterized tools
- **Benefit:** Clear intent and discoverability
- **Cost:** More code to maintain
- **Decision:** Consistency with category tools

## Migration Plan

No migration needed - new tools.

Deployment steps:
1. Reuse validation functions from category tools
2. Implement category reference validation
3. Implement each tool
4. Reuse configuration persistence from category tools
5. Register tools with MCP server
6. Test with various inputs
7. Document usage and validation rules

## Open Questions

None - design is complete.
