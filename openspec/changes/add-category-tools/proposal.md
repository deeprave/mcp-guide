# Change: Add Category Management Tools

## Why

Categories are the primary organizational unit in mcp-guide, defining content directories and patterns. Currently, there's no standardized way to manage categories through tools. We need:

- Tools to add, remove, change, and update categories
- Validation of category names, directories, and patterns
- Safe operations that maintain configuration integrity
- Result pattern responses with clear error handling
- Automatic cleanup when categories are removed from collections

## What Changes

- Implement `category_add` tool (create new category)
- Implement `category_remove` tool (delete category, auto-remove from collections)
- Implement `category_change` tool (replace category configuration)
- Implement `category_update` tool (modify specific fields)
- Add validation for names, directories, descriptions, and patterns
- Return Result pattern responses
- Persist changes to project configuration

## Impact

- Affected specs: New capability `category-tools`
- Affected code: New tools module, configuration management
- Dependencies: Result pattern (ADR-003), tool conventions (ADR-008), session management
- Breaking changes: None (new tools)
- Side effects: category_remove auto-removes category from all collections
