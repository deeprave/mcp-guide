## Context

Guide already serves package-shaped skills from `_skills/<skill-name>/SKILL.md`
and evaluates requirements and conditional template sections using the active
project context. The existing workflow skills demonstrate the package and
frontmatter conventions, but none gives Git operations a reusable hygiene
contract.

## Goals / Non-Goals

**Goals:**

- Add four self-contained, verb-named Git skill packages.
- Give agents clear safe defaults for branching, commit messages, pushing,
  pull requests, and restoring a primary worktree.
- Keep the packages usable without workflow or OpenSpec configuration.
- Make workflow/OpenSpec references conditional rather than making Git usage
  conditional.

**Non-Goals:**

- Implement or wrap Git commands, GitHub operations, or MCP tools.
- Change repository Git policy, branch protection, commit signing, or pull
  request templates.
- Create issues automatically or infer an issue identifier where none is
  available.
- Add brittle tests tied to the wording or continued presence of shipped skill
  templates.

## Decisions

### Use flat, package-shaped skill names

Ship `git-commit`, `git-push`, `git-pr`, and `git-worktree-reset` as flat
packages beneath `_skills`. This follows the portable `SKILL.md` package shape
already used by Guide and keeps each public identifier compatible with external
skill tooling. Nested `git/...` identifiers were considered, but flat names
avoid a non-standard identifier convention and make catalogue discovery
simpler.

### Keep Git hygiene instructions declarative

The skills instruct agents how to inspect state and which guarded operations
to perform; they do not contain executable scripts or call tools implicitly.
This keeps the user in control of state-changing actions and lets the same
skill work with standard Git, Git-facing MCPs, or a client terminal.

### Use contextual issue metadata without manufacturing it

`git-commit` uses a known, applicable issue identifier in branch and commit
naming. It does not create an issue or invent an identifier merely to satisfy
a naming pattern. If project policy or the user requires an issue first, the
agent follows that instruction explicitly.

### Make cleanup deliberately conservative

`git-worktree-reset` treats both uncommitted changes and unpushed commits as a
stop condition requiring user direction. It uses a normal branch switch and
fast-forward update only after these checks; it does not use destructive reset,
checkout, or stash commands as an automatic fallback.

### Verify delivery behaviour without template-text coupling

Use controlled temporary skill packages to test generic discovery, conditions,
and response behaviour where coverage is needed. Do not assert literal wording
or exact production package inventories. Manually review the bundled skill
content against this change's specification.

## Risks / Trade-offs

- [An agent can still disregard a declarative skill] → Keep the skills direct,
  self-contained, and explicit about preconditions; clients remain responsible
  for honouring retrieved instructions.
- [Repository branch conventions can differ] → Use the specified naming shape
  as the Guide default while preserving explicit project or user conventions
  when supplied.
- [A fetch cannot fast-forward a branch with unusual upstream configuration] →
  Inspect the configured upstream and report a missing or incompatible one
  rather than selecting another remote or changing history.

## Migration Plan

The change adds packaged documents only. Existing clients discover them through
the current Guide skill catalogue after the updated documentation is installed;
there is no configuration migration or compatibility break.
