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

### Merge one leaf while holding the shared lock

The rendered handoff instructions will acquire the existing adjacent lock, identify the holder as `<project-name>/<worktree-name>`, reread the JSON or YAML mapping, and replace only `projects.<project-name>.worktrees.<worktree-name>`. They preserve all other keys at every level before atomically replacing the file. The 90-second mtime stale-lock rule remains unchanged.

### Preserve legacy entries; do not infer ownership

Guide cannot safely associate a legacy `worktrees.root` entry with a project: it does not receive the document and the entry may have been written by any project. Guidance will therefore preserve legacy `worktrees` data and tell the agent to move the relevant entry into its `projects.<project-name>.worktrees` namespace before relying on it. New writes always use the canonical layout.

## Risks / Trade-offs

- [Existing documents keep a legacy root entry until someone migrates it] → preserve it verbatim and give explicit, non-destructive migration guidance.
- [Two unrelated projects share the same configured Guide project name] → they remain indistinguishable in a deliberately shared document; users can assign distinct project names before sharing handoff state.
- [Concurrent migration and normal update] → the existing lock, reread, merge, and atomic replacement procedure serialises both operations.

## Migration Plan

1. Update the handoff template and worktree command guidance to use project namespaces for JSON and YAML.
2. When a legacy `worktrees` mapping is encountered, preserve it and instruct the client to move the applicable entries into `projects.<project-name>.worktrees` under the adjacent lock.
3. Update worktree allocation and resume guidance to look only in the current project's namespace.
4. Existing non-worktree handoff formats remain unchanged; worktree support continues to require JSON or YAML.
