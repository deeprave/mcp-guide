# Tasks

## 1. Project-namespaced handoff context

- [x] 1.1 Update handoff, worktree allocation/resume, and review instructions to read and merge `projects.<project-name>.worktrees.<worktree-name>` for uniquely named Guide projects; retain the 90-second atomic-lock protocol; preserve global data; use timestamps to retain the newer entry during legacy migration; provide one concise, complete migration paragraph without examples or embellishment; permit complete current agent-agnostic JSON handoff entries; and prohibit review-context writes. No tests are required because this change is instruction-template behaviour.
