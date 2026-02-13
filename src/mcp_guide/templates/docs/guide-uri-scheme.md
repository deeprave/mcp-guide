{{h1}}Guide URI Scheme

The `guide://` URI scheme provides MCP resource access to guide content.

{{h2}}URI Pattern

```
guide://collection/document
```

- {{b}}collection{{b}}: Collection or category name
- {{b}}document{{b}}: Optional document pattern (omit for all content)

{{h2}}Examples

```
guide://lang              # All language guidelines
guide://lang/python       # Python-specific content
guide://docs              # All documentation
guide://docs/readme       # README-related docs
guide://_workflow          # Workflow documentation
```

{{h2}}Usage

Access via MCP resources protocol:
1. Discover available patterns via `resources/list`
2. Read content via `resources/read` with guide:// URI

{{h2}}Behaviour

- Maps to existing content retrieval system
- Returns plain text/markdown content
- Handles missing collections/documents gracefully
- Supports same patterns as content tools
