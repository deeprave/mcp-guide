# Design: fix-document-update

## Context

This change adjusts existing document update behavior rather than introducing a
new subsystem. The main design requirement is to keep the implementation small
and aligned with the current task manager and installer architecture.

The affected areas are:

- global feature flag semantics for `autoupdate`
- startup task behavior in `McpUpdateTask`
- bound-project enforcement for the `update_documents` tool
- installer reconciliation between the previous installed set and the new
  template set

## Decisions

### 1. Treat `autoupdate` as enabled by default

The current flag resolution stack returns `None` when a flag is unset and
`requires_flag()` converts that to `False`. That behavior is correct for most
feature flags, but it is the wrong default for `autoupdate`.

Rather than changing generic flag resolution semantics for all flags, the
special-case should live in the update workflow itself. `McpUpdateTask` should
interpret the resolved `autoupdate` value using the rule:

- explicit `false` disables prompting
- explicit `true` enables prompting
- unset enables prompting

This keeps the behavior tightly scoped to the only feature that needs this
default inversion.

`autoupdate` should also use the standard boolean normaliser so accepted values
like `"enabled"` and `"off"` are canonicalised to `True` and `False` before
storage and resolution. That keeps it aligned with the rule that pure boolean
flags use the shared boolean normaliser.

### 2. Use acknowledged instruction delivery for startup prompting

The current startup prompt is queued as a normal instruction. That makes the
prompt easy to miss and gives the server no way to re-send reminders if the
agent does not act.

The task should instead use `queue_instruction_with_ack(...)` so the task
manager can keep retrying until the agent runs `update_documents` or the prompt
is otherwise acknowledged.

This preserves the current agent-driven execution model:

- the MCP server does not run `update_documents` internally
- the agent receives an instruction to do so
- the instruction stays active until acknowledged

### 3. Keep `update_documents` project-free

`update_documents` operates on docroot and archive files only. Docroot is read
from global configuration and does not require `session.get_project()`.

The project requirement is therefore accidental rather than architectural. The
tool should be marked `requires_project=False` and its internal logic should use
an unbound session when necessary.

This is consistent with the tool’s global nature and with `autoupdate` being a
global feature flag.

### 4. Reconcile removed upstream files during update

The current installer update loop only iterates files that exist in the new
template set. Files that existed in the previous installed version but are now
absent are ignored and remain in docroot.

The update flow should add a reconciliation pass based on the previous
installed/original archive:

1. enumerate tracked installed files from the previous archive
2. compute which tracked files are absent from the new template set
3. for each removed file:
   - if the current local file is missing, do nothing
   - if the current local file matches the previous original, delete the file
   - if the current local file differs from the previous original, preserve it

This preserves user edits while removing stale unchanged documents.

### 5. Do not remove directories

Directory cleanup is explicitly out of scope. Category layout or user-created
files may make empty-directory cleanup ambiguous, and the user requested that
parent directories remain untouched.

The updater should therefore delete only files and leave directory state as-is.

## Consequences

Positive:

- startup prompting works by default without requiring explicit flag setup
- agents receive follow-up reminders until update instructions are acknowledged
- `update_documents` aligns with its global configuration model
- upgrades stop leaving behind unchanged stale documents that were removed
  upstream

Trade-offs:

- `autoupdate` becomes a special-case semantic rather than following the normal
  missing-flag behavior
- installer update logic becomes a two-pass reconciliation process instead of a
  pure “iterate new templates only” loop

## Validation

The change should be validated with tests covering:

- `autoupdate` unset, `true`, and `false`
- acknowledged instruction queueing and update acknowledgement behavior
- `update_documents` success without a bound project
- removed unchanged file deletion
- removed user-modified file preservation
- parent directories remaining intact after file deletion
