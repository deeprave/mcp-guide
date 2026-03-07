# Change: Consolidate Category and Collection Tools

## Why
MCP server has a hard limit of 37 tools. Currently at 39 tools (37 original + 2 new permission tools). Need to consolidate similar category and collection operations to reduce tool count while maintaining all functionality. Additionally, remove low-value discovery tools and redundant flag getter tools.

## What Changes
**Category/Collection Consolidation:**
- Combine `category_list` + `collection_list` → `category_collection_list`
- Combine `category_remove` + `collection_remove` → `category_collection_remove`
- Combine `category_add` + `collection_add` → `category_collection_add`
- Combine `category_change` + `collection_change` → `category_collection_change`
- Combine `category_update` + `collection_update` → `category_collection_update`
- Add `type: Literal["category", "collection"]` discriminator to all combined tools
- Remove `@toolfunc` decorator from old tools (kept for internal use)
- Saves 5 tools

**Discovery Tools Removal:**
- Remove `list_tools`, `list_prompts`, `list_resources` from tool registration
- Keep functions for potential future use (may combine into single `list_server_info` tool later)
- Saves 3 tools

**Flag Tools Consolidation:**
- Remove `get_project_flag` and `get_feature_flag` (redundant with list operations)
- Add `feature_name: Optional[str]` filter to `list_project_flags` and `list_feature_flags`
- When `feature_name` provided, returns single flag value instead of dict
- Saves 2 tools

**Total Reduction:** 39 → 28 tools (saves 11 tools, well under 37 limit)

## Impact
- **BREAKING**: Tool names change for category/collection operations
- **BREAKING**: `get_project_flag` and `get_feature_flag` removed (use `list_*_flags` with `feature_name` parameter)
- **BREAKING**: `list_tools`, `list_prompts`, `list_resources` no longer available as tools
- Affected specs: `category-tools`, `collection-tools`, `feature-flags`, `discovery-tools`
- Affected code: `tool_category.py`, `tool_collection.py`, `tool_feature_flags.py`, `tool_discovery.py`
- Agent workflows must update to use new consolidated tool names and parameters
