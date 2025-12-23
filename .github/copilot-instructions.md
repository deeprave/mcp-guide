# GitHub Copilot Instructions for Code Reviews

## Code Review Formatting for AI Agents

When providing code reviews or feedback in this repository, format your responses to be AI-agent friendly rather than human-web-browser friendly.

### Principles

1. **Plain Text First**: Use plain text and markdown instead of HTML, CSS, or heavily formatted web content
2. **Copy-Paste Ready**: Format entire reviews so they can be copied and pasted directly into AI agents without reformatting
3. **Clear Structure**: Use markdown headings, lists, and code blocks for organization
4. **Minimal Formatting**: Avoid complex tables, purely decorative elements, or special characters that break when copied as plain text

### Format Guidelines

#### DO: Use Simple Markdown Code Blocks

```python
# Issue: Variable name is unclear
# Fix:
def process_user_data(user_id: str) -> dict:
    return fetch_user(user_id)
```

#### DO: Provide File Paths and Line References

**File**: `src/handlers.py`
**Lines**: 45-52
**Issue**: Missing error handling

```python
# Current code:
result = api.call()

# Suggested fix:
try:
    result = api.call()
except APIError as e:
    logger.error(f"API call failed: {e}")
    raise
```

#### DO: Use Plain Lists for Multiple Issues

**Issues Found**:

1. **src/utils.py:23** - Missing type hint for `process_data` function
2. **src/models.py:67** - Potential null pointer in `get_user_name()`
3. **tests/test_api.py:12** - Test should verify error message content

#### DON'T: Use HTML/CSS Formatting

```html
<!-- Avoid this -->
<div style="color: red; font-weight: bold;">
  <p>Issue found in line 45</p>
</div>
```

#### DON'T: Use Complex Tables or Formatting

Avoid:
- Decorative symbols that may not copy correctly (assume utf-8)
- Complex nested tables
- Inline HTML styling
- Rich text formatting that doesn't translate to plain text
- Special Unicode characters that break in plain text contexts
- Bold/italic markdown in excess (use sparingly only for headers)

### Review Comment Structure

When commenting on code, use this structure:

```markdown
**File**: path/to/file.py
**Line(s)**: 45-52

**Issue**: Brief description of the problem

**Current Code**:
```language
[exact code from the file]
```

**Suggested Fix**:
```language
[proposed corrected code]
```

**Rationale**: Why this change improves the code
```

### Batch Fixes Format

For multiple small fixes, group them by file:

```markdown
## Suggested Changes

### src/handlers.py

**Lines 23-25**: Add error handling
```python
try:
    data = fetch_data()
except DataError:
    return None
```

**Line 67**: Fix type hint
```python
def get_user(user_id: int) -> Optional[User]:
```

### src/utils.py

**Line 12**: Remove unused import
```python
# Remove: from typing import Dict
```
```

### AI Agent Integration

This format ensures that:
- Entire review documents can be copied and pasted into AI chat interfaces
- AI agents can easily parse file paths and line numbers
- Code blocks are ready to copy/paste into edit commands
- Context is clear without requiring rendered HTML
- Changes can be applied programmatically
- No information is lost when copying from rendered view to plain text

### Examples

**Good Review Comment**:

```markdown
**File**: src/api/handlers.py
**Lines**: 145-150

**Issue**: Missing validation for user input

**Fix**:
```python
def create_user(name: str, email: str) -> User:
    if not name or not email:
        raise ValueError("Name and email are required")
    if not is_valid_email(email):
        raise ValueError("Invalid email format")
    return User(name=name, email=email)
```

**Rationale**: Prevents creation of invalid user records
```

**Poor Review Comment**:
```
WARNING ALERT
Problem detected!
Check line ~145ish in the handlers file or something
You should probably add some validation maybe?
```
(Vague references, no file path, no code examples, excessive decoration)

### Summary

Keep reviews simple, structured, and copy-paste friendly. The entire review should be copyable as plain text and pasteable into any AI agent without loss of information or formatting issues. Optimize for AI agent consumption, not web browser rendering.

### Testing Your Review Format

Before posting, test by:
1. Copy your entire review comment
2. Paste into a plain text editor
3. Verify all information is intact and readable
4. Ensure code blocks are clearly delimited
5. Check that file paths and line numbers are preserved
