# Change: Add Project Hash Disambiguation

## Why
Currently, multiple projects with the same basename (e.g., `~/Projects/my-project` and `~/Projects/other/my-project`) cause conflicts because the system uses only the project name as the unique identifier. This leads to configuration confusion and incorrect project resolution.

## What Changes
- Add SHA256 hash calculation based on full project path
- Modify project configuration structure to use `{name}-{short-hash}` as keys
- Add `name` and `hash` properties to project configuration
- Implement hash verification during project resolution
- Add migration logic to convert existing configurations

## Impact
- Affected specs: project-config
- Affected code: project resolution, configuration management, session handling
- **BREAKING**: Configuration file format changes (handled by migration)
- Users will see no difference in UI/commands (backward compatible interface)
