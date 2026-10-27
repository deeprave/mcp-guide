# Tasks

## 1. Workflow-file validation boundary

- [x] 1.1 Add an explicit validation-error outcome for agent-submitted workflow-file content while preserving tolerant parsing for passive callers; verify malformed YAML, non-mapping content, missing `phase`, and invalid field types fail without replacing cached valid state or acknowledging queued workflow guidance.
- [x] 1.2 Preserve workflow-monitor validation failures through `send_file_content`; verify a structured `tracking` value returns its actionable failure instead of a generic successful receipt.

## 2. Workflow guidance contract

- [x] 2.1 Add the compact strict YAML schema to initial workflow startup guidance; verify an initial workflow-enabled session receives it before being asked to submit the file.
- [x] 2.2 Align state-format, shared tracking guidance, workflow-discussion, and user workflow documentation with the `issue`, `plan`, and external-string `tracking` semantics; instruct agents to read the exact configured workflow-file path rather than discover it through a glob or repository search; verify rendered guidance remains available for projects with and without OpenSpec support.
- [x] 2.3 Ensure the registered workflow normaliser and workflow-specific parser make the non-ordered `exploration` phase available for every enabled explicit phase list while preserving the supplied phase order.

## 3. Validation

- [x] 3.1 Run the affected workflow parser, monitoring, and instruction-delivery tests in the foreground; verify all pass without warnings.
- [x] 3.2 Run applicable Ruff and Ty checks plus `openspec validate fix-workflow-file-validation --strict`; verify all pass.

## 4. Review follow-up

- [x] 4.1 Reject unexpected strict-parser failures and unknown or disabled submitted phases without changing cached workflow state; provide clear valid-phase guidance.
- [x] 4.2 Render only the configured enabled phases in workflow bootstrap guidance.
- [x] 4.3 Run focused workflow parser, monitoring, and rendering tests plus applicable static checks and strict OpenSpec validation.
