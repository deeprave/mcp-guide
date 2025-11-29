# Change: Add Collection Management Tools

## Why

Collections group related categories for organized content access. Currently, there's no standardized way to manage collections through tools. We need:

- Tools to add, remove, change, and update collections
- Validation of collection names, descriptions, and category references
- Safe operations that maintain configuration integrity
- Result pattern responses with clear error handling
- Validation that referenced categories exist

## What Changes

- Implement `collection_list` tool (list all collections with categories)
- Implement `collection_add` tool (create new collection)
- Implement `collection_remove` tool (delete collection)
- Implement `collection_change` tool (replace collection configuration)
- Implement `collection_update` tool (modify specific fields)
- Add validation for names, descriptions, and category references
- Return Result pattern responses
- Persist changes to project configuration

## Impact

- Affected specs: New capability `collection-tools`
- Affected code: New tools module, configuration management
- Dependencies: Result pattern (ADR-003), tool conventions (ADR-008), session management
- Breaking changes: None (new tools)
- Validation: Ensures referenced categories exist
