## Context

OpenAI Codex CLI supports custom URI schemes but not direct MCP prompts. The existing `guide://collection/document` pattern works for content but doesn't support command execution. We need to extend the URI scheme to enable command access for Codex users.

## Goals / Non-Goals

**Goals:**
- Enable all commands via `guide://_command` URI pattern
- Maintain backward compatibility with `guide://collection/document`
- Use underscore prefix to distinguish commands from collections/categories
- Parse positional args from path segments and kwargs from query params
- Reuse existing command discovery and execution infrastructure

**Non-Goals:**
- Creating new command syntax or aliases
- Changing existing prompt-based command interface
- Supporting commands that require interactive input
- Custom response formatting for Codex (use standard MCP responses)

## Decisions

### URI Pattern: `guide://_command/arg1?kwarg=value`

**Decision:** Use underscore prefix to denote commands in URI netloc/path.

**Rationale:**
- Underscore prefix already reserved for system categories (`_commands`, `_workflow`, `_openspec`)
- Categories already validate against underscore prefix in `category_add`
- Collections need same validation (prerequisite)
- No collision with user-created collections/categories
- Clear visual distinction from content URIs

**Alternatives considered:**
- `guide://cmd/command` - Could collide with "cmd" collection
- `guide://:command` - Colon parsed as port separator, creates ambiguity
- `guide:///command` - Empty netloc is unusual and less clear

### Command Path Resolution

**Decision:** Use `discover_commands()` command cache to match longest command path, remaining segments become positional args.

**Example:**
- `guide://_perm/write-add/docs/` → command=`perm/write-add`, args=`["docs/"]`
- `guide://_project` → command=`project`, args=`[]`

**Rationale:**
- Commands can contain slashes (e.g., `openspec/list`, `perm/write-add`)
- Need command cache to disambiguate path segments
- Command cache provides fast lookup (frozen in production, invalidated on file changes in dev mode)
- Longest match ensures correct parsing

### Query Parameter Parsing

**Decision:** Parse query params as kwargs with boolean inference:
- `?verbose` → `{"verbose": True}`
- `?verbose=true` → `{"verbose": True}`
- `?verbose=false` → `{"verbose": False}`
- `?name=test` → `{"name": "test"}`

**Rationale:**
- Matches common URL query param conventions
- Boolean flags without values default to True
- Explicit true/false values supported
- String values passed as-is

### Response Format

**Decision:** Return command output as-is, including MCP instructions.

**Rationale:**
- MCP instructions are valid for all agents
- No special handling needed for Codex
- Consistent with existing resource behavior
- Agents can interpret instructions as needed

## Risks / Trade-offs

**Risk:** Command discovery adds latency to URI parsing
- **Mitigation:** Command list is cached, discovery only on cache miss or dev mode

**Risk:** Complex commands with many args may create unwieldy URIs
- **Mitigation:** This is inherent to URI-based interfaces, not unique to our design

**Trade-off:** Underscore prefix validation for collections is a prerequisite
- **Impact:** Minimal - collections with underscore prefix are system-only by convention
- **Benefit:** Prevents future collision with command URIs

## Migration Plan

**Phase 1: Prerequisite (collection validation)**
1. Add underscore prefix validation to `collection_add`
2. Add underscore prefix validation to `collection_change`
3. Add tests for validation
4. No migration needed (no existing collections with underscore prefix)

**Phase 2: Command URI support**
1. Extend `GuideUri` model to support command URIs
2. Update `parse_guide_uri()` to detect underscore prefix and parse command/args/kwargs
3. Update `guide_resource()` to route command URIs to command handler
4. Add integration tests for command URI execution
5. Update documentation

**Rollback:** Remove command URI handling from resource handler, revert to content-only behavior.

## Open Questions

None - design is complete and ready for implementation.
