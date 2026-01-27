# Change: Optimise OpenSpec Validation

## Why
Current implementation reads entire `openspec/project.md` file content and requests OpenSpec command location every session. These are one-time validation checks that should never repeat once confirmed.

## What Changes
- Check `openspec/project.md` exists (not read content) - once only
- Check `openspec/changes` directory exists by requesting changes list - once only
- Check OpenSpec command exists - once only
- Store validation result as boolean flag in project configuration
- Never re-validate while flag is true

## Impact
- Affected specs: openspec-integration
- Affected code:
  - `src/mcp_guide/templates/_common/openspec-project-check.mustache`
  - `src/mcp_guide/client_context/openspec_task.py`
  - `src/mcp_guide/models/project.py` (add openspec_validated field)
  - Project configuration persistence
