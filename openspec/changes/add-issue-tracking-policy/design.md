# Design

## Context

Selected issue-tracking providers currently share `_provider-common.md.mustache`, which tells agents that they may proceed without an issue. The onboarding template selects one provider policy under the mutually exclusive `issue-tracking/*` topic. The commit template does not currently consume issue-tracking policy content.

## Goals / Non-Goals

**Goals:**

- Make a selected non-`None` provider policy require issue tracking for eligible changes.
- Keep the requirement composable with the selected provider through the shared provider template.
- Deliver the guidance to the commit flow before its branching instructions.
- Default issue tracking from the change scope while requiring user clarification when that scope is uncertain.

**Non-Goals:**

- Change provider selection, tracker integrations, or issue schemas.
- Require issue tracking for projects that select `None`.
- Infer or create an issue after an explicit user waiver.

## Decisions

### Make selected providers enforce the requirement

Selecting a non-`None` provider already identifies the issue-tracking policy for a project. Its shared provider template will render the requirement directly; no project flag or onboarding opt-in is introduced.

Using another `issue-tracking/*` document was rejected because provider choices are mutually exclusive within that topic; replacing a provider selection would discard its integration-specific guidance. A separate configuration model was rejected because the selected provider already represents whether issue tracking is enabled.

### Keep enforcement guidance in the shared provider partial

The shared policy will first reuse an applicable issue. If none exists, it will direct the agent to create one with an available provider integration and allocate it to the active change or commit. It will allow proceeding without an identifier only when the user explicitly says that specific change need not be tracked. That waiver applies only to the current change and SHALL NOT alter project policy or create a persistent exception.

Small bug-fix changes, and changes not tracked in OpenSpec when OpenSpec is active, are untracked by default. Changes that are more than a bug fix and are tracked in OpenSpec when it is active are tracked by default. The user's instruction determines the outcome; if an agent cannot tell whether an issue should be linked or created, it SHALL ask the user rather than infer one.

Duplicating this text in every provider template was rejected because provider-specific files intentionally only supply the provider name and would make the policy drift-prone.

### Import issue-tracking guidance into the commit template before branching

The commit command will declare the `issue-tracking` policy topic and render its partial immediately before the branch-format guidance. This makes the check available at the decision point before branch creation and commit preparation.

Relying on the agent to retrieve the policy separately was rejected because it does not reliably place the requirement in the commit flow.

## Risks / Trade-offs

- [A project switches to `None`] → The `None` policy continues not to require identifiers.
- [No available tracker integration] → The policy directs the agent to ask the user how to provide or create the issue rather than inventing an identifier; a change-specific waiver remains available only through explicit user instruction.
- [Provider policy rendered outside the commit command] → The requirement also guides general change handling, which is consistent with allocating the issue before a commit.

## Migration Plan

Existing projects receive the requirement when their selected provider policy is updated. No configuration migration is needed.
