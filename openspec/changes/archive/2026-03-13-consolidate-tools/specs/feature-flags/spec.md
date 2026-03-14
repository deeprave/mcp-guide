## REMOVED Requirements

### Requirement: get_project_flag Tool
**Reason**: Redundant with `list_project_flags` which now supports filtering by `feature_name`
**Migration**: Use `list_project_flags(feature_name="flag-name")` instead

### Requirement: get_feature_flag Tool
**Reason**: Redundant with `list_feature_flags` which now supports filtering by `feature_name`
**Migration**: Use `list_feature_flags(feature_name="flag-name")` instead

## MODIFIED Requirements

### Requirement: list_project_flags Tool

The system SHALL provide a `list_project_flags` tool that lists or retrieves project feature flags with glob pattern filtering.

Arguments:
- `feature_name` (optional, string): Glob pattern to filter flags (e.g., 'workflow*', 'content-*'). Supports wildcards: `*` (any chars), `?` (single char), `[abc]` (char set).
- `active` (optional, boolean): Include resolved flags (True) or project-only (False). Defaults to true.

The tool SHALL:
- When `feature_name` is None: Return dict of all flags
- When `feature_name` contains wildcards (`*`, `?`, `[`): Return dict of matching flags using glob pattern
- When `feature_name` is exact match (no wildcards): Return single flag value (or None if not found)
- When `active` is True: Merge global and project flags (project overrides global)
- When `active` is False: Return project flags only
- Use `fnmatch` for pattern matching
- Return Result pattern response

#### Scenario: List all active flags
- **WHEN** called with no feature_name and active=True
- **THEN** return merged dict of global and project flags

#### Scenario: Get specific flag value (exact match)
- **WHEN** called with feature_name="workflow" (no wildcards)
- **THEN** return the single value of that flag (or None if not set)

#### Scenario: Filter flags by glob pattern
- **WHEN** called with feature_name="workflow*"
- **THEN** return dict of all flags matching pattern (e.g., {"workflow": true, "workflow-phase": "check"})

#### Scenario: Filter with multiple wildcards
- **WHEN** called with feature_name="content-*"
- **THEN** return dict of matching flags (e.g., {"content-styling": "mime", "content-format": "json"})

#### Scenario: Pattern with no matches
- **WHEN** called with feature_name="nonexistent*"
- **THEN** return empty dict {}

#### Scenario: List project-only flags
- **WHEN** called with active=False
- **THEN** return only project-level flags, excluding global flags

### Requirement: list_feature_flags Tool

The system SHALL provide a `list_feature_flags` tool that lists or retrieves global feature flags with glob pattern filtering.

Arguments:
- `feature_name` (optional, string): Glob pattern to filter flags (e.g., 'allow-*'). Supports wildcards: `*` (any chars), `?` (single char), `[abc]` (char set).
- `active` (optional, boolean): Unused for global flags (kept for consistency). Defaults to true.

The tool SHALL:
- When `feature_name` is None: Return dict of all global flags
- When `feature_name` contains wildcards (`*`, `?`, `[`): Return dict of matching flags using glob pattern
- When `feature_name` is exact match (no wildcards): Return single flag value (or None if not found)
- Use `fnmatch` for pattern matching
- Return Result pattern response

#### Scenario: List all global flags
- **WHEN** called with no feature_name
- **THEN** return dict of all global flags

#### Scenario: Get specific global flag value (exact match)
- **WHEN** called with feature_name="allow-client-info" (no wildcards)
- **THEN** return the single value of that flag (or None if not set)

#### Scenario: Filter global flags by pattern
- **WHEN** called with feature_name="allow-*"
- **THEN** return dict of all flags matching pattern
