# Fix Expression Handling in category_content and collection_content

## Problem
Both `category_content` and `collection_content` tools fail to handle expressions correctly:
- `category_content("review/commit")` fails - doesn't parse category/pattern syntax
- `collection_content` fails when collections contain expressions like "review/commit"

Currently only `get_content` handles expressions properly (parsing commas, +, category/pattern syntax).

## Solution
Make `category_content` and `collection_content` use the same expression parsing logic as `get_content`:
- Parse expressions on commas (multiple expressions)
- Parse category/pattern syntax (e.g., "review/commit")
- Handle multiple patterns with + (e.g., "review/commit+pr")
- Aggregate and deduplicate results

## Verification
After fix:
- `category_content("review/commit")` should return commit instructions
- `@guide commit` (which uses collection with "review/commit" expression) should work
- All existing tests should still pass

## Files to Change
- `src/mcp_guide/tools/tool_category.py` - `category_content` function
- `src/mcp_guide/tools/tool_collection.py` - `collection_content` function (if exists)
- `src/mcp_guide/utils/content_common.py` - shared expression parsing logic
