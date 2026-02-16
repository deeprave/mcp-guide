# Categories and Collections

Organising content with categories and collections in mcp-guide.

## Categories

Categories specify which files to include based on directory paths and file patterns.

### Viewing Categories

To see what categories exist in your project, ask your AI:

```
@guide :project -v
```

This shows all categories, their directories, patterns, and descriptions.

### Creating Categories

You can ask your AI to create categories for you:

```
Please create a category called 'api' for API documentation in the docs/api directory
```

```
Add a category 'testing' with patterns for pytest files
```

The AI will create the category with appropriate settings based on your description.

### Category Properties

Each category has:

- **Name**: Up to 30 characters, no leading underscore/hyphen, no whitespace
- **Directory**: Path relative to docroot where documents are stored
- **Patterns**: Glob patterns that match documents to include
- **Description**: Optional human-readable description

### Pattern Syntax

Patterns are globs that match documents that should be selected when the bare category is used.
This normally means using the basename, without the file extension.
Patterns are matched for basenames by default, and various extensions are tried in order: markdown, markdown template and finally text.
Beware of using glob patterns containing `*` too liberally. It is better to simply add multiple patterns than select everything.
Trailing `*` in any pattern is discouraged, the system takes care of that automatically.

Examples:

- `readthis` - Matches "readthis", "readthis.md", "readthis.txt"
- `{guide,readme}` - Matches both "guide" and "readme"

### Using Categories

The primary use of the prompt is to request content using an expression.

Request a single category:

```
@guide guide
```

Request multiple categories by separating them with commas:

```
@guide guide,lang,context
```

You can override the default patterns by using `/` to specify documents within the category:

```
@guide lang/python
```

Combine multiple patterns within a category using `+`:

```
@guide testing/python+pytest
```

## Collections

Collections group category expressions together. They act as "macros" to provide targeted context for specific tasks without remembering complex expressions.

### Viewing Collections

To see what collections exist in your project:

```
@guide :project -v
```

This shows all collections and the categories they include.

### Creating Collections

Ask your AI to create collections:

```
Please create a collection called 'python-dev' that includes guide, lang, and testing categories
```

```
Add a collection 'code-review' with guide, checks, and review categories
```

The AI will set up the collection with the categories you specify.

### Using Collections

Request a collection using the `@guide` prompt:

```
@guide python-dev
```

Collections expand to their category expressions automatically.

You can also override patterns when using a collection:

```
@guide python-dev/testing
```

### Nested Collections

Collections can reference other collections. For example, you might have a base collection that other collections build upon. Ask your AI to set this up:

```
Create a 'base' collection with just the guide category, then create 'python-dev' that includes base plus lang and testing
```

## Category Expressions

Category expressions provide flexible content selection.

### Basic Expressions

- `guide` - Single category
- `guide,lang` - Multiple categories (comma-separated)
- `lang/python` - Specific pattern within a category

### Subdirectory Selection

You can use `/` to select documents from subdirectories within a category:

```
@guide docs/api/authentication
```

This selects the "authentication" document from the `api/` subdirectory within the `docs` category.

## Next Steps

- **[Documents](documents.md)** - Writing content with templates
- **[Feature Flags](feature-flags.md)** - Conditional content inclusion
- **[Profiles](profiles.md)** - Pre-configured category setups

