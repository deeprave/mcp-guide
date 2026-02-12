# Categories and Collections

Organising content with categories and collections in mcp-guide.

## Categories

Categories define which files to include based on directory paths and file patterns.

### Defining Categories

Categories are defined in your project configuration:

```yaml
categories:
  guidelines:
    dir: guidelines
    patterns:
      - "readthis"
      - "guidelines"
    description: "Project guidelines and standards"

  python:
    dir: lang/python
    patterns:
      - "python-guide"
      - "style"
    description: "Python language guidelines"
```

### Category Properties

- **dir**: Directory path relative to docroot (required)
- **patterns**: List of glob patterns matching document basenames (required)
- **description**: Human-readable description (optional)

### Pattern Syntax

Patterns are globs matching document basenames (not extensions). Focus on text documents:

- `readthis` - Matches "readthis", "readthis.md", "readthis.txt"
- `guide*` - Matches "guidelines", "guide-python", etc.
- `python-*` - Matches "python-style", "python-testing"
- `{guide,readme}` - Matches either "guide" or "readme"

### Using Categories

Request content using the `@guide` prompt:

```
@guide guidelines
```

Categories can be combined with `+`:

```
@guide guidelines+python
```

Override patterns with `/`:

```
@guide guidelines/python
```

## Collections

Collections group category expressions together. They act as "macros" to provide targeted context for specific tasks.

Category expressions can be simple names (`guidelines`) or complex expressions (`guidelines+python`).

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

- **categories**: List of category expressions (required)
- **description**: Human-readable description (optional)

### Using Collections

Request content using the `@guide` prompt:

```
@guide python-dev
```

Collections expand to their category expressions automatically.

You can also override patterns:

```
@guide python-dev/testing
```

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

```
@guide guidelines/security
```

## Pattern Overrides

Override category patterns at request time using `/`:

```
@guide guidelines/python
```

This is useful for:
- Filtering by topic
- Selecting specific documents
- Testing patterns

## Next Steps

- **[Content Documents](content-documents.md)** - Writing content with templates
- **[Feature Flags](feature-flags.md)** - Conditional content inclusion
- **[Profiles](profiles.md)** - Pre-configured category setups

