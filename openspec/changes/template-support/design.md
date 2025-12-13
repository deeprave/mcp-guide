# Design: Template Context Management (Phase 2)

## Context

Template support Phase 1 implemented basic template rendering with lambda functions. Phase 2 requires a comprehensive context management system to provide rich template variables from multiple data sources (system, agent, project, collection, category, file).

**Constraints:**
- Must maintain backward compatibility with Phase 1 template renderer
- Security requirement: no docroot path exposure
- Type safety: all context values must be template-safe
- Performance: stateless approach (no caching complexity)
- Integration: seamless integration with existing content tools

**Stakeholders:**
- Template authors (need rich context variables)
- Content tool users (transparent template rendering)
- Security (path exposure prevention)
- Maintainers (clean architecture)

## Goals / Non-Goals

**Goals:**
- Type-safe context management with ChainMap-based scope chaining
- Rich context variables from all data sources
- Secure path handling (relative paths only)
- Seamless integration with existing template renderer
- Comprehensive test coverage with TDD approach

**Non-Goals:**
- Context caching (adds complexity, stateless preferred)
- Dynamic context modification during rendering
- Complex template inheritance or includes
- Performance optimization beyond basic efficiency

## Decisions

### Decision: TemplateContext extends ChainMap[str, Any]
**Rationale:** ChainMap provides natural scope chaining behavior where inner scopes override outer scopes. This matches template variable resolution expectations.

**Alternatives considered:**
- Custom dict-based implementation: More complex, reinvents ChainMap functionality
- Nested dict merging: Loses scope information, harder to debug
- Simple dict: No scope chaining, variables would conflict

### Decision: Context management in `src/mcp_guide/utils/template_context.py`
**Rationale:**
- Utility nature fits with existing template modules
- Avoids circular dependencies with content tools
- Consistent with Phase 1 architecture

**Alternatives considered:**
- Separate `context/` module: Overkill for single-purpose functionality
- In `models.py`: Wrong abstraction level, models are data structures
- In `session.py`: Too coupled to session management

### Decision: Stateless context building (no caching)
**Rationale:**
- Simpler implementation and testing
- Avoids cache invalidation complexity
- Template rendering is not performance-critical
- Fresh context ensures consistency

**Alternatives considered:**
- Context caching: Adds complexity, invalidation logic, potential bugs
- Lazy loading: Complicates type safety and error handling

**Future consideration:** Session-based caching with component-level invalidation could be added as Phase 2B optimization if performance measurement shows benefit. See `.todo/template-context-caching-discussion.md` for detailed caching strategy analysis.

### Decision: Type validation at TemplateContext creation
**Rationale:**
- Fail fast on invalid data
- Clear error messages for debugging
- Prevents template rendering errors

**Alternatives considered:**
- Validation at template render time: Too late, harder to debug
- No validation: Risk of runtime template errors

### Decision: Soft/hard deletion with sentinel masking
**Rationale:**
- Supports advanced template scenarios
- Maintains ChainMap semantics
- Allows fine-grained context control

**Alternatives considered:**
- No deletion support: Limits template flexibility
- Only hard deletion: Doesn't support masking scenarios

## Architecture

### Context Layer Ordering (highest to lowest priority)
1. **Transient context**: `now`, `timestamp` (added per-render, highest priority)
2. **File context**: `file.path`, `file.basename`, `file.size`, `file.mtime`, `file.ctime`
3. **Collection context**: `collection.name`, `collection.description`, `collection.categories` (when applicable)
4. **Category context**: `category.name`, `category.description`, `category.dir`
5. **Project context**: `project.name`, `project.created_at`, `project.categories`, `project.collections`
6. **Agent context**: `@`, `agent.name`, `agent.version`, `agent.prompt_prefix`
7. **System context**: Static program info (base layer, lowest priority)
8. **Lambda functions**: `format_date`, `truncate`, `highlight_code` (injected during rendering)

Note: Transient context (timestamps) is generated fresh per-render using `get_transient_context()` function to ensure current values.

### MCP Context Caching Strategy

**Problem:** Duplication between `_determine_project_name()` and `Session.cache_mcp_context()` both calling MCP `list_roots()` and extracting similar data.

**Solution:** Consolidate MCP context extraction into global ContextVars:

#### Global ContextVars (persist across project switches)
- `_cached_roots: ContextVar[CachedRootsInfo]` (already exists)
- `_cached_agent_info: ContextVar[AgentInfo]` (new)
- `_cached_client_params: ContextVar[dict]` (new)

#### Session-Specific Cache (invalidated on project switch)
- `contexts["system"]`: Static system information
- `contexts["project"]`: Project-specific data (invalidated when roots change)

#### Implementation Changes
1. **Rename `_determine_project_name()`** → `_cache_mcp_globals(ctx)`
2. **Expand scope** to cache roots, agent info, and client params globally
3. **Call once** in `get_or_create_session()` before session creation
4. **Remove from SessionState**: `cached_agent_info`, `cached_client_params`
5. **Session methods** read from global ContextVars instead of re-querying MCP

#### Benefits
- **Agent info persists** across project switches (global, not per-session)
- **Roots persist** until they actually change (not lost on project switch)
- **No duplication** - single MCP context extraction point
- **Smaller session state** - only project-specific data cached per-session
- **Better performance** - no re-detection of stable data on project switches

### Type Conversion Strategy
- **datetime → ISO 8601 string**: Template-safe, human-readable
- **Path → string**: Security-validated relative paths only
- **None → omit**: Graceful handling of optional fields
- **Lists → template-safe**: Category/collection names as string lists

### Security Model
- **Category.dir**: Convert to relative path, validate no parent directory traversal
- **File paths**: Relative to category directory only
- **Input validation**: All context keys must be strings, values must be template-safe types

## Integration Points

### Enhanced Template Renderer
```python
# New function for full context integration
def render_file_with_context(
    file_info: FileInfo,
    session: Session,
    project: Project,
    category: Category,
    collection: Optional[Collection] = None
) -> Result[str]:
    context = build_template_context(session, project, category, collection, file_info)
    return render_template_content(file_info.content, context, str(file_info.path))

# Existing function remains unchanged for backward compatibility
def render_template_content(content: str, context: ChainMap[str, Any], file_path: str = "<template>") -> Result[str]:
    # Phase 1 implementation unchanged
```

### Content Tools Integration
Content tools will detect `.mustache` files and use enhanced rendering:
```python
if is_template_file(file_info):
    result = render_file_with_context(file_info, session, project, category, collection)
    if result.is_ok():
        file_info = file_info.with_content(result.value)  # Update with rendered content
```

## Risks / Trade-offs

### Risk: Performance impact from stateless context building
**Mitigation:** Template rendering is not performance-critical. If needed, can add caching later without API changes.

### Risk: Complex type validation logic
**Mitigation:** Comprehensive test coverage with TDD approach. Clear error messages for debugging.

### Risk: Security vulnerabilities in path handling
**Mitigation:** Strict validation, relative paths only, comprehensive security tests.

### Trade-off: ChainMap complexity vs. simple dict merging
**Chosen:** ChainMap for proper scope semantics
**Cost:** Slightly more complex implementation
**Benefit:** Correct template variable resolution behavior

## Implementation Approach

### Phase 2A: Core Infrastructure
1. Implement TemplateContext class with comprehensive tests
2. Create context extractors for each data source
3. Implement main context builder function

### Phase 2B: Integration
1. Add enhanced template renderer function (additive)
2. Update content tools to use enhanced renderer for template files
3. Maintain full backward compatibility with Phase 1

### Phase 2C: Validation
1. Comprehensive security testing
2. Integration testing with real templates
3. Performance validation

### Rollback Strategy
- Phase 1 template renderer remains completely unchanged
- New functionality is purely additive
- Can disable template context features without breaking existing functionality
- No data migration required (stateless system)

## Open Questions

- **Q:** Should context building be async to support future async data sources?
  **A:** Start with sync implementation. Can add async wrapper later if needed.

- **Q:** How to handle very large context data (e.g., large file lists)?
  **A:** Current scope doesn't include large data. Monitor and optimize if needed.

- **Q:** Should we support custom context extractors for extensions?
  **A:** Not in Phase 2. Keep simple, add extensibility later if needed.
