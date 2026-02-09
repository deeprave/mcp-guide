# Categories and Collections

Organizing content with categories and collections in mcp-guide.

## Categories

Categories define which files to include based on directory paths and file patterns.

### Defining Categories

Categories are defined in project configuration (`~/.config/mcp-guide/projects/<project>/config.yaml`):

```yaml
categories:
  guidelines:
    dir: guidelines
    patterns:
      - "*.md"
    description: "Project guidelines and standards"

  python:
    dir: lang/python
    patterns:
      - "*.md"
      - "*.txt"
    description: "Python language guidelines"
```

### Category Properties

- **dir**: Directory path relative to docroot (required)
- **patterns**: List of glob patterns to match files (required)
- **description**: Human-readable description (optional)

### Pattern Syntax

Patterns use glob syntax:

- `*.md` - All Markdown files
- `**/*.py` - All Python files recursively
- `test_*.py` - Files starting with "test_"
- `{*.md,*.txt}` - Multiple extensions
- `[!_]*.md` - Files not starting with underscore

### Using Categories

Request content by category name:

```python
# Via MCP tool
get_content(expression="guidelines")
```

Categories can be combined:

```python
# Multiple categories
get_content(expression="guidelines+python")
```

## Collections

Collections group categories together. They act as "macros" to provide targeted context for specific tasks.

### Defining Collections

```yaml
collections:
  python-dev:
    categories:
      - guidelines
      - python
      - testing
    description: "Python development context"

  code-review:
    categories:
      - guidelines
      - code-quality
      - security
    description: "Code review checklist"
```

### Collection Properties

- **categories**: List of category names or expressions (required)
- **description**: Human-readable description (optional)

### Using Collections

Request content by collection name:

```python
get_content(expression="python-dev")
```

Collections expand to their categories automatically.

### Nested Collections

Collections can reference other collections:

```yaml
collections:
  base:
    categories:
      - guidelines

  python-dev:
    categories:
      - base  # References the 'base' collection
      - python
```

## Category Expressions

Category expressions allow flexible content selection:

### Basic Expressions

- `guidelines` - Single category
- `guidelines+python` - Multiple categories (union)
- `guidelines/security` - Subdirectory within category

### Subdirectory Selection

Use `/` to select subdirectories:

```python
# Only security guidelines
get_content(expression="guidelines/security")

# Multiple subdirectories
get_content(expression="guidelines/security+guidelines/testing")
```

## Pattern Overrides

Override category patterns at request time:

```python
# Only Python files from guidelines category
get_content(expression="guidelines", pattern="*.py")
```

This is useful for:
- Filtering by file type
- Selecting specific files
- Testing patterns

## Content Deduplication

When multiple categories include the same file, mcp-guide:

1. Includes the file once
2. Merges instructions from all occurrences
3. Deduplicates similar instruction sentences

This prevents redundant content while preserving unique information.

## Best Practices

### Category Design

- **Single responsibility** - One topic per category
- **Clear naming** - Use descriptive names
- **Logical grouping** - Group related content
- **Consistent structure** - Follow naming conventions

### Collection Design

- **Task-oriented** - Design for specific use cases
- **Composable** - Build from smaller categories
- **Documented** - Add clear descriptions
- **Tested** - Verify content is useful

### Pattern Design

- **Specific** - Match only intended files
- **Consistent** - Use consistent extensions
- **Documented** - Comment complex patterns
- **Tested** - Verify matches

## Examples

### Development Workflow

```yaml
categories:
  guidelines:
    dir: guidelines
    patterns: ["*.md"]

  tdd:
    dir: workflows/tdd
    patterns: ["*.md"]

  python:
    dir: lang/python
    patterns: ["*.md"]

collections:
  python-tdd:
    categories:
      - guidelines
      - tdd
      - python
    description: "Python TDD workflow"
```

### Code Review

```yaml
categories:
  code-quality:
    dir: standards/quality
    patterns: ["*.md"]

  security:
    dir: standards/security
    patterns: ["*.md"]

  testing:
    dir: standards/testing
    patterns: ["*.md"]

collections:
  code-review:
    categories:
      - code-quality
      - security
      - testing
    description: "Code review checklist"
```

### Documentation

```yaml
categories:
  api-docs:
    dir: docs/api
    patterns: ["*.md"]

  user-docs:
    dir: docs/user
    patterns: ["*.md"]

  dev-docs:
    dir: docs/developer
    patterns: ["*.md"]

collections:
  all-docs:
    categories:
      - api-docs
      - user-docs
      - dev-docs
    description: "Complete documentation"
```

## Troubleshooting

### No Files Found

Check:
1. Directory path is correct relative to docroot
2. Patterns match your file extensions
3. Files exist in the specified directory

### Duplicate Content

If seeing duplicate content:
1. Check for overlapping patterns
2. Verify category definitions don't conflict
3. Review collection composition

### Wrong Files Included

If wrong files are included:
1. Make patterns more specific
2. Use negative patterns (`[!_]*.md`)
3. Organize files into subdirectories

## Next Steps

- **[Content Documents](content-documents.md)** - Writing content with templates
- **[Feature Flags](feature-flags.md)** - Conditional content inclusion
- **[Profiles](profiles.md)** - Pre-configured category setups

