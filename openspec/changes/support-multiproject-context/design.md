# Design

## Context

The default handoff target is resolved beneath the configured documents path. Users may deliberately make that directory common to several independent projects, such as a control-plane repository and its checked-out library and web repositories. The current structured format uses `worktrees.root` for every primary checkout, so the last writer overwrites unrelated project handoff state.

Guide does not receive or retain the handoff document. Its responsibility is therefore to render an unambiguous client-side update protocol from the current bound project and worktree identity.

## Goals / Non-Goals

**Goals:**

- Make every structured handoff entry unique across projects that share one document.
- Retain independently named linked worktrees within each project.
- Preserve top-level global data, other projects, and other worktrees during locked updates.
- Give agents a comprehensible, deterministic migration path from the legacy layout.
- Allow a worktree entry to contain any current, valid JSON needed for another agent or session to resume work.
- Keep review activity from replacing or appending handoff context.

**Non-Goals:**

- Use directory names, repository paths, or client filesystem inspection as handoff identity.
- Make Guide read, cache, validate, or automatically migrate client-owned handoff content.
- Change project configuration identity or Git worktree labels.

## Decisions

### Namespace handoff entries by Guide project name

The canonical structured shape becomes:

```json
{
  "todo": "Remember to update the release notes",
  "projects": {
    "wybra": {
      "worktrees": {
        "root": {"path": "/Users/davidn/Code/wybra-dev/wybra"},
        "calm-falcon": {"path": "/Users/davidn/Code/wybra-dev/wybra_calm-falcon"}
      }
    },
    "uniquode.io": {
      "worktrees": {
        "root": {"path": "/Users/davidn/Code/wybra-dev/uniquode.io"}
      }
    }
  }
}
```

The effective Guide project name is the namespace key. `root` remains the primary checkout's worktree label, but it no longer identifies the project that owns the entry. This directly preserves the existing nested worktree model and prevents primary checkouts from colliding.

Using a repository directory name was rejected: independently created worktrees can have arbitrary locations and names. Using a hash or path was rejected because the requested, human-readable project name is the intended shared-document identity.

Sharing a handoff document is supported only among Guide projects with distinct configured project names. A same-name pair has the same intended identity and therefore cannot safely use separate namespaces in one document; that configuration is unsupported.

### Merge one leaf while holding the shared lock

The rendered handoff instructions will acquire the existing adjacent lock, identify the holder as `<project-name>/<worktree-name>`, reread the JSON or YAML mapping, and replace only `projects.<project-name>.worktrees.<worktree-name>`. They preserve all other keys at every level before atomically replacing the file. The 90-second mtime stale-lock rule remains unchanged.

### Preserve legacy entries; do not infer ownership

Guide cannot safely associate another project's legacy `worktrees.root` entry with the current project. Guidance will therefore preserve the legacy `worktrees` mapping while merging only the relevant current-project entry into `projects.<project-name>.worktrees` before relying on it. When the legacy and namespaced entries overlap, the entry with the newer timestamp wins. Existing root-level handoff state belongs to the current project's `root` worktree and is moved into that entry, except for genuinely global data such as a shared todo list or instructions for all agents. New writes always use the canonical layout.

Migration guidance is temporary and must be one concise, complete paragraph, with no examples or embellishment.

### Keep handoff context complete and agent-agnostic

`timestamp` and `path` are bookkeeping fields. Beyond them, a worktree entry may use any valid JSON structure, including nested objects and lists, to describe the current focus, completed work, remaining work, decisions, blockers, and next action. OpenSpec may provide supporting detail when active, but it does not limit this context. Agents remove historical information when it is no longer relevant.

### Review does not update handoff context

Review is observational. A review request changes the workflow phase to `review` only when needed; it otherwise leaves the workflow file unchanged and never updates handoff context. This prevents a reviewer from replacing the implementer's resumable state.

## Risks / Trade-offs

- [Existing documents keep a legacy root entry until someone migrates it] → preserve it verbatim and give explicit, non-destructive migration guidance.
- [Two unrelated projects share the same configured Guide project name] → they remain indistinguishable in a deliberately shared document; users can assign distinct project names before sharing handoff state.
- [Concurrent migration and normal update] → the existing lock, reread, merge, and atomic replacement procedure serialises both operations.

## Migration Plan

1. Update the handoff template and worktree command guidance to use project namespaces for JSON and YAML, with distinct configured project names as the sharing requirement.
2. Preserve a legacy `worktrees` mapping while moving applicable current-project entries into `projects.<project-name>.worktrees` under the adjacent lock; move legacy root-level handoff state into the current project's `root` entry while retaining genuinely global root data.
3. Update worktree allocation and resume guidance to look only in the current project's namespace.
4. Permit complete, agent-agnostic, non-historical JSON handoff context beyond `timestamp` and `path`.
5. Update review guidance so review requests do not write handoff context.
6. Existing non-worktree handoff formats remain unchanged; worktree support continues to require JSON or YAML.
