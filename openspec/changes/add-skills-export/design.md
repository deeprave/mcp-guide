## Context

Guide already serves package-shaped skills from the server document root and
renders each selected `SKILL.md` for the active project. The command system can
render instructions with parsed positional arguments, keyword arguments, current
agent information, and project context, but it does not itself write to the
client filesystem. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**

- Add one command that gives an agent a safe, explicit workflow for exporting
  current-project Guide skills as local `SKILL.md` packages
- Build the command help from the active skill catalogue, selected names,
  destination, and current agent
- Prefer a client-native destination picker, multi-select skill picker, and
  confirmation when the agent can provide them, with an equivalent textual path
  when it cannot

**Non-Goals:**

- A server-side file-writing tool, global skill installation, or exporting into
  another project's root
- Automatically choosing, executing, trusting, or exporting a skill without
  the user's explicit final confirmation
- Defining a universal mapping for every agent; only recognised current-agent
  skill locations are offered as optional destination choices

## Decisions

### Render a command rather than add a write API

Create `_commands/skills/export.mustache` and rely on the existing command URI
parser. The command is an agent instruction because only the connected agent
knows and is authorised to mutate its local project filesystem.

This preserves the client/server filesystem boundary and uses the standard
`guide://_skills/export/<destination>?skills=...` interface. A dedicated MCP
tool was rejected because it would imply the server can safely write the
client's project files.

### Treat destinations as project-relative skill roots

The optional first positional argument is a project-relative directory. It
defaults to `.agents`; every skill is exported below it as a directory named
for the selected public skill identifier and rooted at `SKILL.md`. The command
rejects absolute and escaping destination values in its rendered requirements.

The dynamically rendered destination choices contain `.agents` and, only when
the recognised current agent has a configured project-local skills directory,
that directory. An explicit destination remains available for an agent whose
location is not known. This avoids hard-coding a global home directory or
incorrectly assuming the server's filesystem is the client's filesystem.

### Derive selections from the current skill catalogue

At render time the command obtains the same eligible, project-aware skill
catalogue used by `list_skills`. The `skills` keyword is split on commas,
trimmed, de-duplicated, and compared against public skill names before the
agent writes anything. Unknown names terminate the operation rather than
producing a partial export.

When the keyword is absent, the command directs the agent to obtain a
multi-select choice from the user. If a client-native picker is unavailable,
it renders the complete available list and asks for a textual selection.

### Make all mutation decisions explicit

The command has three decision points: destination selection when omitted,
skill selection when omitted, and a final confirmation of the resolved output
paths. It directs the agent to use an `AskUserQuestion`-style picker or
confirmation UI when available; otherwise it asks in plain text and stops for
the answer. It does not perform an implied default export merely because the
default destination is known.

### Export package content by resource retrieval

After confirmation, the agent retrieves each selected skill's rendered
`SKILL.md` resource and writes it to the proposed local package. The entrypoint
can identify supporting `resources/`, `agents/`, or `scripts/` members; the
agent retrieves only required members and treats scripts as untrusted local
content. This maintains the existing package resource contract rather than
introducing a parallel export representation.

## Risks / Trade-offs

- [An agent lacks a native selection UI] → Render equivalent numbered or
  named textual choices and wait for a response
- [A recognised agent's local convention changes] → Keep the mapping limited
  to recognised current agents and retain explicit destination input
- [A skill changes while an export is in progress] → The agent retrieves the
  rendered resource after confirmation, so the written content is the current
  resource result rather than an unrendered server file
- [An export could overwrite local work] → Require final confirmation and
  include existing-target inspection in the command instructions

## Migration Plan

The command is additive. Existing local skills and existing Guide resource
usage remain unchanged; users invoke the export command only when they choose
to create or update local copies.
