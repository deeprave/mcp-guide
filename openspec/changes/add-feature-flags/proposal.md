# Change: Add Feature Flags Support

## Why
Enable flexible feature configuration at global and project levels without code changes. Feature flags support gradual rollout, project-specific customization, and extensible configuration with multiple value types beyond simple boolean toggles.

## What Changes
- Add `feature_flags` to global configuration model (defaults to empty dict)
- Add `project_flags` to project configuration model (defaults to empty dict)
- Implement MCP tools: `list_flags`, `set_flag`, `get_flag`
- Add feature flag validation (names and values)
- Support resolution hierarchy: project-specific → global → None
- Restrict flag values to: bool, str, list[str], dict[str, str]

## Impact
- Affected specs: config-manager, mcp-server
- Affected code: Configuration models, MCP tools, validation
- **BREAKING**: None - additive changes with backward compatibility
- Dependencies: Session management, Result pattern, configuration persistence
