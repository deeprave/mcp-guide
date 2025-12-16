# Change: Add Category Management Tools

**Jira ID:** GUIDE-25
**Epic:** GUIDE-24

## Why

Categories are the primary organizational unit in mcp-guide, defining content directories and patterns. Currently, there's no standardized way to manage categories through tools. We need:

- Tools to add, remove, change, and update categories
- Validation of category names, directories, and patterns
- Safe operations that maintain configuration integrity
- Result pattern responses with clear error handling
- Automatic cleanup when categories are removed from collections

## What Changes

- Implement `category_list` tool (list all categories with patterns)
- Implement `category_add` tool (create new category)
- Implement `category_remove` tool (delete category, auto-remove from collections)
- Implement `category_change` tool (replace category configuration)
- Implement `category_update` tool (modify specific fields)
- Add validation for names, directories, descriptions, and patterns
- Return Result pattern responses
- Persist changes to project configuration

## Impact

- Affected specs: New capability `category-tools`, tool-infrastructure (registration refactor)
- Affected code: New tools module, configuration management, tool registration infrastructure
- Dependencies: Result pattern (ADR-003), tool conventions (ADR-008 - needs revision), session management
- Breaking changes: None (new tools, internal infrastructure refactor)
- Side effects: category_remove auto-removes category from all collections

## Prerequisites

**CRITICAL:** Tool registration infrastructure must be refactored before implementing category tools.

**Current Issue:** Lazy constructor registration pattern is broken - tools don't register with FastMCP.

**Solution:** Implement decorator-based registration with ContextVar test mode control (Phase 0).

**See:** `REGISTRATION_REFACTOR.md` and `PHASE_0_PLAN.md` for details.
