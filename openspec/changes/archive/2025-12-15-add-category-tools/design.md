# Design: Category Management Tools

## Context

Categories define content organization in mcp-guide, specifying directories and patterns for content discovery. Currently, categories can only be managed by manually editing configuration files. We need tools to manage categories programmatically with proper validation and safety checks.

## Goals

- Provide CRUD operations for categories
- Validate all inputs for safety (traversal prevention, path safety)
- Maintain configuration integrity
- Auto-update collections when categories change
- Use Result pattern for consistent error handling

## Non-Goals

- Managing category content (files in directories)
- Validating that directories exist on disk
- Migrating or moving category content
- Batch operations (multiple categories at once)

## Decisions

### Four-Tool Design

**Decision:** Provide four separate tools: add, remove, change, update

**Rationale:**
- `add`: Create new category (all fields)
- `remove`: Delete category (simple, destructive)
- `change`: Replace entire configuration (rename, replace patterns)
- `update`: Modify specific fields (add/remove patterns incrementally)
- Clear separation between replace (change) and modify (update)
- Follows common CRUD patterns

**Alternatives considered:**
- Single tool with operation parameter - Less discoverable
- Only add/remove/update - No way to replace all patterns at once
- Add/remove/modify - "modify" is ambiguous

### Validation Strategy

**Decision:** Validate all inputs before any configuration changes

**Rationale:**
- Fail fast on invalid input
- Prevent partial updates
- Clear error messages
- Security (traversal prevention)

**Validation layers:**
1. Type checking (schema validation)
2. Format validation (regex, length)
3. Safety validation (traversal, absolute paths)
4. Existence validation (category exists/doesn't exist)

### Directory Path Safety

**Decision:** Strict validation with traversal prevention and component checks

**Rules:**
- Relative paths only
- No ".." components
- No leading/trailing "__" in components
- Valid filename characters only
- Defaults to category name

**Rationale:**
- Prevents directory traversal attacks
- Prevents access to system directories
- Ensures predictable directory structure
- Double underscore prefix/suffix reserved for system use

### Pattern Safety

**Decision:** Similar validation to directory paths but allow wildcards

**Rules:**
- Valid filename characters plus wildcards (*, ?, [])
- No ".." components
- No absolute paths
- No leading/trailing "__"
- Extension optional

**Rationale:**
- Patterns are used in glob operations
- Same security concerns as directory paths
- Wildcards are essential for pattern matching

### Auto-Update Collections

**Decision:** Automatically update collections when categories are removed or renamed

**Rationale:**
- Maintains referential integrity
- Prevents broken references
- User expectation (cascading updates)
- Simpler than requiring manual cleanup

**Behavior:**
- Remove: Remove category from all collections
- Rename: Update category name in all collections
- Change dir/patterns: No collection updates needed

### Change vs Update Semantics

**Decision:** `change` replaces, `update` modifies

**change:**
- Replaces entire configuration
- Can rename category
- Replaces all patterns (not additive)
- Use when you want to set exact state

**update:**
- Modifies specific fields
- Cannot rename (use change for that)
- Adds/removes patterns incrementally
- Use when you want to adjust existing state

**Rationale:**
- Clear distinction between replace and modify
- Supports both use cases
- Prevents accidental data loss

### Configuration Persistence

**Decision:** Use file locking and validation before write

**Rationale:**
- Prevents concurrent modification issues
- Ensures configuration is valid before writing
- Graceful error handling
- Atomic operations

**Implementation:**
```python
with file_lock(config_path):
    config = load_config()
    # Make changes
    validate_config(config)
    write_config(config)
```

## Implementation Notes

### Validation Functions

```python
def validate_category_name(name: str) -> Result[None]:
    """Validate category name."""
    if not re.match(r'^[a-zA-Z0-9_-]{1,30}$', name):
        return Result.failure(
            error="Invalid category name",
            error_type="invalid_name"
        )
    return Result.ok(None)

def validate_directory(dir: str) -> Result[None]:
    """Validate directory path."""
    if os.path.isabs(dir):
        return Result.failure(
            error="Absolute paths not allowed",
            error_type="absolute_path"
        )
    if '..' in dir.split(os.sep):
        return Result.failure(
            error="Path traversal not allowed",
            error_type="traversal_attempt"
        )
    for component in dir.split(os.sep):
        if component.startswith('__') or component.endswith('__'):
            return Result.failure(
                error="Component cannot start/end with __",
                error_type="invalid_component"
            )
    return Result.ok(None)
```

### Tool Structure

```python
async def category_add(
    name: str,
    dir: Optional[str] = None,
    description: Optional[str] = None,
    patterns: Optional[list[str]] = None
) -> str:
    """Add new category."""
    session = get_current_session()
    if not session:
        return Result.failure(
            error="No active session",
            error_type="no_session"
        ).to_json_str()

    # Validate inputs
    result = validate_category_name(name)
    if result.is_failure():
        return result.to_json_str()

    # Check doesn't exist
    config = await session.get_project()
    if name in config.categories:
        return Result.failure(
            error=f"Category '{name}' already exists",
            error_type="already_exists"
        ).to_json_str()

    # Create category
    category = Category(
        name=name,
        dir=dir or name,
        patterns=patterns or []
    )

    # Persist
    config.categories[name] = category
    await session.save_project(config)

    return Result.ok(
        value=f"Category '{name}' created"
    ).to_json_str()
```

### Collection Auto-Update

```python
def update_collections_on_remove(config, category_name):
    """Remove category from all collections."""
    for collection in config.collections.values():
        if category_name in collection.categories:
            collection.categories.remove(category_name)

def update_collections_on_rename(config, old_name, new_name):
    """Update category name in all collections."""
    for collection in config.collections.values():
        if old_name in collection.categories:
            idx = collection.categories.index(old_name)
            collection.categories[idx] = new_name
```

## Dependencies

- Result pattern (ADR-003)
- Tool conventions (ADR-008)
- Session management (existing)
- Configuration models (existing)
- File locking (existing)

## Risks / Trade-offs

**Risk:** Auto-update of collections may be unexpected
- **Mitigation:** Document behavior clearly
- **Mitigation:** Include in success message ("Updated 3 collections")

**Risk:** File locking may cause delays or failures
- **Mitigation:** Use timeout on lock acquisition
- **Mitigation:** Clear error message if lock fails

**Trade-off:** Four tools vs fewer parameterized tools
- **Benefit:** Clear intent and discoverability
- **Cost:** More code to maintain
- **Decision:** Benefits outweigh costs

**Trade-off:** Strict validation vs flexibility
- **Benefit:** Security and safety
- **Cost:** May reject some valid use cases
- **Decision:** Security is priority

## Migration Plan

No migration needed - new tools.

Deployment steps:
1. Implement validation functions
2. Implement each tool
3. Add file locking to configuration writes
4. Register tools with MCP server
5. Test with various inputs
6. Document usage and validation rules

## Open Questions

None - design is complete.
