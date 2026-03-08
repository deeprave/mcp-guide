# Change: Remove dead and unreachable code

## Why
Vulture analysis identified ~942 lines (4.7% of codebase) of dead code across 22 files.
This increases maintenance burden, confuses contributors, and inflates test coverage gaps.

## What Changes
- Remove dead functions, methods, classes, and variables that are never called from production code
- Remove modules that exist only as test fixtures for unused functionality
- Fix duplicate `break` bug in `render/context.py`
- Prioritised by largest clusters first for maximum impact per task

## Impact
- Affected specs: session-management, workflow-context, template-context, logging, filesystem-security, template-rendering, mcp-server
- Affected code: 22 files across render/, workflow/, session.py, core/, openspec/, server.py, and others
- No breaking changes - all removed code is unreachable from production paths
- Tests that exercise dead-code-only modules may need removal
