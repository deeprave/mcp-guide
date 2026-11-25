## Context

Guide already serves package-shaped skills from the server document root and
renders a selected `SKILL.md` for the active project. The command system can
render instructions with parsed positional arguments, keyword arguments, current
agent information, and project context, but it does not itself write to the
client filesystem. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**

- Add one command that gives an agent a safe, explicit workflow for exporting
  current-project Guide skills as local `SKILL.md` packages
- Build execution guidance from the active skill catalogue, selected name, and
  overwrite state while keeping command help generic
- Prefer a client-native single-select skill picker when the agent can provide
  one, with an equivalent textual path when it cannot

**Non-Goals:**

- A server-side file-writing tool, global skill installation, or exporting into
  another project's root
- Automatically choosing, executing, trusting, or exporting a skill without
  a supplied or selected skill name
- Exporting to an alternative skill directory or maintaining links for clients
  other than Claude Code
- Synchronising, refreshing, or reconciling an exported local skill with its
  Guide source

## Decisions

### Render a command rather than add a write API

Create `_commands/skills/export.mustache` and rely on the existing command URI
parser. The command is an agent instruction because only the connected agent
knows and is authorised to mutate its local project filesystem.

This preserves the client/server filesystem boundary and uses the standard
`guide://_skills/export/<skill-name>?force=true` interface. The command obtains
the rendered package through the bound `export_skill` tool, while the connected
agent remains responsible for writing it to the client's project files.

### Use one canonical project-local export root

Every export is rooted at `.agents/skills/<skill-name>`, where the named public
skill is a directory rooted at `SKILL.md`. The name is the command's sole
positional argument; there is no list-valued query argument, destination
argument, or alternate export path. This is both project-local and directly
discovered by the supported Agent Skills clients.

### Add Claude Code compatibility without replacing its content

After an export, if the project has a `.claude` directory, create
`.claude/skills` if necessary. For the exported skill, if its entry is absent
from that directory, create a relative symlink to `.agents/skills/<skill-name>`.
If an entry already exists, leave it unchanged. When it is not that canonical
symlink, warn that Claude Code will use the existing `.claude/skills/<skill-name>`
entry rather than the exported skill, and tell the user to move, delete, or
rename it if they want the export to be visible. Do not create `.claude` solely
for this compatibility path.

### Derive selections from the current skill catalogue

At render time the command obtains the same eligible, project-aware skill
catalogue used by `list_skills`. Its sole positional skill name is compared
against public skill names before the agent writes anything. Unknown names
terminate the operation.

When the name is absent, the command directs the agent to obtain one choice
from the user. If a client-native picker is unavailable, it renders the
complete available list and asks for one textual selection.

### Require explicit forced replacement

The command selects one skill when its positional argument is omitted. An existing
canonical export is never replaced by default: the agent reports it and stops.
After the user explicitly requests replacement, `force=true` permits it. To
replace safely, rename the old entry to `<skill-name>.tmp-<suffix>`, create the
new export, then remove the backup. On an intervening failure, report it and
restore the backup where possible.

### Export complete package content through the MIME formatter

A bound `export_skill` tool returns the complete rendered package through the
existing MIME content formatter. Each MIME part identifies a package-relative
member and its permissions; the `SKILL.md` part includes only portable
frontmatter (`name`, `description`, and `usage`) before its rendered body.
Guide-only eligibility remains an export-time check. The command directs the
agent to write the returned package locally without executing scripts.

### Treat exports as user-owned snapshots

An export is a one-way copy for clients that do not consume MCP skills directly,
or for users who want to customise a local skill. Guide does not track, refresh,
or reconcile exported files. A later export replaces an existing target only
when the user has explicitly requested `force=true`.

The copied content is the skill rendered for the current bound session, including
its project, worktree, workflow, and other session-dependent context. Exports of
the same named skill in different sessions may legitimately differ; Guide does
not promise a stable raw-template representation.

## Risks / Trade-offs

- [An agent lacks a native selection UI] → Render the same named textual
  choices and wait for a response
- [A client does not discover `.agents/skills`] → Retain only the documented
  Claude Code compatibility link; do not multiply export locations
- [An exported skill diverges from Guide] → The local copy is intentionally
  user-owned; a later export can replace it only with `force=true`
- [The same skill renders differently on a later export] → Each export is an
  intentional snapshot of its current session context, not a deterministic
  source-template copy
- [An export could overwrite local work] → Refuse it unless `force=true`, then
  use a temporary rename and restoration path
- [Claude has its own same-named skill] → Preserve it and warn that it shadows
  the canonical export

## Migration Plan

The command is additive. Existing local skills and existing Guide resource
usage remain unchanged; users invoke the export command only when they choose
to create or update local copies.
