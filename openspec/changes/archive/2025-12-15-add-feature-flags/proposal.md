# Add Feature Flags Support

**Status**: Proposed
**Priority**: Medium
**Complexity**: Medium

## Why

Enable flexible feature configuration at global and project levels without code changes. Feature flags support gradual rollout, project-specific customization, and extensible configuration with multiple value types beyond simple boolean toggles.

## What Changes

- Add `feature_flags` to global configuration model (SHALL default to empty dict)
- Add `project_flags` to project configuration model (SHALL default to empty dict)
- MCP tools SHALL be implemented: `list_project_flags`, `set_project_flag`, `get_project_flag`
- MCP tools SHALL be implemented: `list_feature_flags`, `set_feature_flag`, `get_feature_flag`
- Feature flag validation SHALL be added (names and values)
- Resolution hierarchy SHALL support: project-specific → global → None
- Feature flag values SHALL be restricted to: bool, str, list[str], dict[str, str]

## Impact

- Affected specs: config-manager, mcp-server
- Affected code: Configuration models, MCP tools, validation
- **BREAKING**: None - additive changes with backward compatibility
- Dependencies: Session management, Result pattern, configuration persistence
