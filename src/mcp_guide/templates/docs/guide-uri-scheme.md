{{h1}}Guide URI Scheme

The `guide://` URI scheme provides MCP resource access to guide content.

{{h2}}URI Pattern

```
guide://expression[/pattern]
guide://_command[/args][?kwargs]
```

- {{b}}expression{{b}}: Content expression for content URIs, such as a category name, collection name, or combined expression like `docs,tasks`
- {{b}}pattern{{b}}: Optional document pattern for content URIs
- {{b}}_command{{b}}: Command name for command URIs
- {{b}}args{{b}}: Optional positional command arguments
- {{b}}kwargs{{b}}: Optional query parameters passed as command keyword arguments

{{h2}}Examples

```
guide://lang              # All language guidelines
guide://lang/python       # Python-specific content
guide://docs              # All documentation
guide://docs/readme       # README-related docs
guide://docs,tasks        # Combined content expression
guide://_project          # Run the project command
guide://_status?verbose=true
guide://_perm/write/add/docs/
```

{{h2}}Usage

Access via MCP resources protocol:
1. Discover available patterns via `resources/templates/list`
2. Read content via `resources/read` with guide:// URI
3. Use the `read_resource` tool as a fallback when the client does not expose MCP resource reads directly

{{h2}}Behaviour

- Maps to existing content retrieval system
- Returns plain text/markdown content for both content and command URIs
- Handles missing collections/documents gracefully
- Supports command discovery through advertised resource templates
