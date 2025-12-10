# Content Retrieval Tools

## Tools

### get_category_content
Retrieve content from a specific category.
- `category` (required): Category name
- `pattern` (optional): Glob pattern to filter files

### get_collection_content
Retrieve content from a specific collection.
- `collection` (required): Collection name
- `pattern` (optional): Glob pattern to filter files

### get_content
Retrieve content from category or collection (unified access).
- `category_or_collection` (required): Category or collection name
- `pattern` (optional): Glob pattern to filter files

## Pattern Syntax

Glob patterns for file matching:
- `*` - matches any characters within filename
- `**` - matches any characters including directory separators
- `?` - matches single character
- `[abc]` - matches any character in set
- `intro` - matches all files named intro (any extension)
- `*.md` - matches all markdown files
- `**/*.py` - matches all Python files recursively

## Response Format

**Single file**: Plain markdown content
**Multiple files**: MIME multipart format with RFC 2046 structure, boundary "guide-boundary"

## Agent Instructions

### Success
No instruction provided - content returned directly as value.

### Errors

**not_found** (category/collection doesn't exist):
- Instruction: "Present this error to the user and take no further action."

**no_matches** (pattern matches no files):
- Instruction: "Present this error to the user so they can correct the pattern. Do NOT attempt corrective action."

**file_read_error** (file access issues):
- Instruction: "Present this error to the user. The file may have been deleted, moved, or has permission issues."

**no_project** (no active project session):
- Instruction: "To fix: Call set_current_project with the basename of the current working directory."
