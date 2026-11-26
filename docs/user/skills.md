# Skills

Guide provides native skills for common development work. Compatible MCP clients
discover them through the standard Skills extension and read their instructions
from `skill://<name>/SKILL.md`. Clients that use Guide resources directly can
read the same skill through `guide://$<name>` or select it with `use_skill`.

Guide-owned skills are prefixed so they are easy to distinguish from skills
installed by you or another tool. Workflow skills use `guide-`, Git skills use
`guide-git-`, and review collation and sequential decisions use
`guide-triage` and `guide-sequence`.

Some skills need project-aware information. Bind the session first with
`set_project`; then append the opaque session identifier to a `skill://` URI:

```
skill://guide-review/SKILL.md?session_id=<session_id>
```

Guide can export one rendered skill at a time with
`guide://_skills/export/<skill-name>`. The export is a user-owned snapshot in
`.agents/skills/<skill-name>`; it may be changed locally and does not update
when Guide changes. When `.claude` exists, Guide also links a missing matching
Claude skill to that exported snapshot.

See [Guide URIs](guide-uris.md#skill-uris) for URI details and
[Prompt Commands](commands.md#skill-export) for export behaviour.
