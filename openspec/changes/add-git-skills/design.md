## Context

Guide already serves packaged skills and injects selected policy partials into template rendering.

## Decisions

### Policy selection drives orchestration

`issue-tracking/<provider>` selects the tracker, including explicit `none`. `git/delivery/<mode>` selects direct, branch, or multi-branch delivery. These policies complement the existing commit, PR, and autonomy policies.

### Tracker use remains a user choice per change

The selected provider makes issue handling available; it does not manufacture an issue. A skill asks whether to create/link one or proceed without it. When the user chooses creation or linking, the skill uses an available MCP, CLI, or other integration; if none is available, it asks the user how to proceed.

### Compose skills at delivery boundaries

`git-pr` consumes commit and push guidance, then applies PR policy and any repository template. `git-push` distinguishes work for the current change from pre-existing unrelated edits. `git-sync` is post-merge worktree synchronisation rather than branch cleanup or deletion.

### Verify contracts, not prose

Tests exercise delivered recommendations and conditional policy behaviour with controlled templates. They do not assert wording from shipped skill templates.
