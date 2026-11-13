# Design

## Context

Selected issue-tracking providers currently share `_provider-common.md.mustache`, which tells agents that they may proceed without an issue. The onboarding template selects one provider policy under the mutually exclusive `issue-tracking/*` topic, so a second selected policy document cannot represent this optional behaviour independently. The commit template does not currently consume issue-tracking policy content.

## Goals / Non-Goals

**Goals:**

- Let onboarding stage the requirement only when a non-`None` tracker is selected.
- Keep the requirement composable with the selected provider through a project flag rendered by the shared provider template.
- Deliver the guidance to the commit flow before its branching instructions.

**Non-Goals:**

- Change provider selection, tracker integrations, or issue schemas.
- Require issue tracking for projects that select `None` or do not enable the option.
- Infer or create an issue after an explicit user waiver.

## Decisions

### Represent the optional requirement with a project flag

Onboarding will offer required issue tracking after a recognised tracker is selected and stage a boolean project flag, such as `require-issue-tracking`. The shared provider template will branch on that flag to render either the existing optional guidance or the stricter requirement.

Using another `issue-tracking/*` document was rejected because provider choices are mutually exclusive within that topic; replacing a provider selection would discard its integration-specific guidance. A separate configuration model was rejected because policy choices already use project configuration and flags.

### Keep enforcement guidance in the shared provider partial

The required branch will first reuse an applicable issue. If none exists, it will direct the agent to create one with an available provider integration and allocate it to the active change or commit. It will allow proceeding without an identifier only after an explicit user statement that no issue is required.

Duplicating this text in every provider template was rejected because provider-specific files intentionally only supply the provider name and would make the policy drift-prone.

### Import issue-tracking guidance into the commit template before branching

The commit command will declare the `issue-tracking` policy topic and render its partial immediately before the branch-format guidance. This makes the check available at the decision point before branch creation and commit preparation.

Relying on the agent to retrieve the policy separately was rejected because it does not reliably place the requirement in the commit flow.

## Risks / Trade-offs

- [A stale requirement flag after switching to `None`] → Onboarding will stage removal or disabling of the flag when the user selects no tracker, and the `None` policy will continue not to require identifiers.
- [No available tracker integration] → The policy directs the agent to ask the user how to provide or create the issue rather than inventing an identifier.
- [Provider policy rendered outside the commit command] → The requirement also guides general change handling, which is consistent with allocating the issue before a commit.

## Migration Plan

Existing projects retain their current optional issue handling because the new flag is unset by default. Re-running onboarding lets them opt in. Removing or disabling the flag restores the existing optional behaviour without data migration.
