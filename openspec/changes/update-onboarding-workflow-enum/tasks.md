## 1. Specification

- [x] 1.1 Add a `workflow-flags` delta defining the supported onboarding-facing
  workflow enumeration and its mapping to valid `workflow` flag values
- [x] 1.2 Ensure the spec covers `none` and `unstructured` as equivalent
  disabled-workflow choices
- [x] 1.3 Ensure the spec distinguishes `structured` as the boolean shorthand
  and `full` as the explicit full phase sequence
- [x] 1.4 Ensure the spec clarifies `exploration` as an available but non-linear
  exploratory mode, available across all workflow-enabled variants but not when
  workflow is disabled

## 2. Onboarding prompt implementation

- [x] 2.1 Update `src/mcp_guide/templates/_commands/onboard.mustache` so the
  workflow question presents only the supported workflow options
- [x] 2.2 Update the template so each user-facing option maps to a server-valid
  `workflow` flag value
- [x] 2.3 Ensure the prompt language distinguishes disabled workflow,
  boolean-enabled structured workflow, and explicit custom workflow sequences

## 3. Validation

- [x] 3.1 Validate the change with
  `openspec validate update-onboarding-workflow-enum --strict --no-interactive`
- [x] 3.2 Confirm the onboarding wording and the spec mapping stay aligned
