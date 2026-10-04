---
cache: long
---

{{h1}}Guide URI Scheme

The `guide://` URI scheme provides MCP resource access to guide content.

{{h2}}URI Pattern

```
guide://expression[/pattern]?session_id=<session_id>
guide://_command[/args][?kwargs]
guide://$
guide://$?table
guide://$skill-name[/member-path][?kwargs]
```

- {{b}}expression{{b}}: Content expression for content URIs, such as a category name, collection name, or combined expression like `docs,tasks`
- {{b}}pattern{{b}}: Optional document pattern for content URIs
- {{b}}session_id{{b}}: Required query parameter for native content resource reads; pass the identifier returned by `set_project` unchanged
- {{b}}_command{{b}}: Command name for command URIs
- {{b}}args{{b}}: Optional positional command arguments
- {{b}}kwargs{{b}}: Optional query parameters passed as command keyword arguments
- {{b}}${{b}}: Server-provided skill catalogue; `$` is reserved and cannot begin a category or collection name
- {{b}}table{{b}}: Optional catalogue query value that returns a user-facing Markdown table
- {{b}}skill-name{{b}}: Flat, explicitly selected skill package name
- {{b}}member-path{{b}}: Optional package member below the selected skill, such as `resources/checklist.md`

{{h2}}Examples

```
guide://lang?session_id=<session_id>          # All language guidelines
guide://lang/python?session_id=<session_id>   # Python-specific content
guide://docs?session_id=<session_id>          # All documentation
guide://docs/readme?session_id=<session_id>   # README-related docs
guide://docs,tasks?session_id=<session_id>    # Combined content expression
guide://_project          # Run the project command
guide://_status?verbose=true
guide://_perm/write/add/docs%2F
guide://$
guide://$?table          # User-facing skill catalogue table
guide://$workflow-status
guide://$workflow-status/resources/checklist.md
```

{{h2}}Usage

Access via MCP resources protocol:
1. Discover available patterns via `resources/templates/list`
2. Read content via `resources/read` with guide:// URI
3. Use the `read_resource` tool as a fallback when the client does not expose MCP resource reads directly

Native content resources require an explicit `session_id` even on legacy MCP.
Without it, Guide returns unbound-session guidance rather than content. When using
the fallback `read_resource` tool, provide `session_id` as a tool argument instead
of adding it to the URI.

{{h2}}Behaviour

- Maps to existing content retrieval system
- Returns plain text/markdown content for both content and command URIs
- Handles missing collections/documents gracefully
- Supports command discovery through advertised resource templates
- Serves bundled skills from private, optionally nested packages below `{docroot}/_skills/`; the required frontmatter `name` is the public skill identity and the catalogue exposes selected frontmatter rather than raw YAML
- Returns the rendered entrypoint for `guide://$<skill-name>` and a named rendered member for `guide://$<skill-name>/<member-path>`
- Lets a skill entrypoint declare primitive `elicitation` forms in frontmatter. Guide requests a form only when its required values are absent from the URI, then makes accepted values available as template keyword arguments
- Makes `resources/`, `scripts/`, and `agents/` package members available on demand. Scripts are returned as content only: clients must download, inspect, establish trust, and obtain authority before local execution
