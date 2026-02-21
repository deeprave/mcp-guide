# Change: Add Feature Documentation

**Status**: Proposed
**Priority**: Medium
**Complexity**: Low

## Why

Users need comprehensive documentation for workflow and OpenSpec features. Current documentation lacks detailed coverage of these capabilities.

## What Changes

- Add `docs/user/workflows.md` - Document workflow support, workflow-consent, configuration, and default prompt commands
- Add `docs/user/openspec.md` - Document OpenSpec support, available commands, and interactions
- Remove `docs/user/INDEX.md` - Consolidate with docs/index.md
- Update `docs/index.md` - Add links to new documentation and incorporate content from user INDEX

## Impact

- Affected files: `docs/user/workflows.md` (new), `docs/user/openspec.md` (new), `docs/user/INDEX.md` (removed), `docs/index.md` (updated)
- No changes to existing functionality
- Simplifies documentation structure by removing duplicate index
