# list-category-files Change Proposal

## Summary
Add a `list-category-files` tool to allow discovery of files available in a category directory.

## Problem
Users currently have no way to discover what files are available in a category without knowing the exact patterns or file names. This creates a poor user experience where users must guess file names or have prior knowledge of the category structure.

## Solution
Implement a `list-category-files` tool that:
- Lists all files in a category directory using the existing file discovery mechanism
- Returns results in a brief 2-column format (path and size)
- Uses pattern `**/*` to discover all files (ignoring category-specific patterns)
- Removes `.mustache` extension from basenames in output
- Respects existing scan limits (MAX_DOCUMENTS_PER_GLOB=100, MAX_GLOB_DEPTH=8)

## Scope
This change adds a single new tool to the category-tools capability without modifying existing functionality.

## Dependencies
- Existing `discover_category_files` function in `file_discovery.py`
- Existing category validation and session management
- Existing Result pattern for tool responses

## Non-Goals
- Modifying existing file discovery behavior
- Adding file content preview
- Changing scan limits or depth restrictions
- Supporting custom patterns (always uses `**/*`)
