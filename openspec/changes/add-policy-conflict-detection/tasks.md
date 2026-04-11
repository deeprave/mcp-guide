## 0. Prerequisite
- [ ] 0.1 Confirm `add-policy-selection` is implemented and archived before beginning

## 1. Define conflict rule registry
- [ ] 1.1 Define `ConflictRule` data structure: `{policies: list[str], message: str, severity: "warning" | "info"}`
- [ ] 1.2 Implement `ConflictRegistry` as a simple dict/list with lookup by active policy set
- [ ] 1.3 Author initial rule set (minimum: tdd+minimal, tdd+relaxed, no-git-ops+agent-autonomous, no-prs+agent-autonomous)
- [ ] 1.4 Store rules in a data file or template (not hardcoded in Python) per architecture guidelines

## 2. Implement conflict detection
- [ ] 2.1 Implement async `detect_conflicts(active_policies: list[str]) -> list[ConflictMatch]`
- [ ] 2.2 Integrate conflict check into the policy selection handler: run after selection is applied
- [ ] 2.3 Surface conflict warnings in the response without blocking the selection

## 3. Add `:policies/check` command
- [ ] 3.1 Create `_commands/policies/check.mustache` command template
- [ ] 3.2 Expose conflict results in template context
- [ ] 3.3 Include: conflicting policy pair, human-readable explanation, suggested resolution

## 4. Tests and validation
- [ ] 4.1 Unit tests for `detect_conflicts` covering all initial rule combinations
- [ ] 4.2 Test that conflict detection does not block policy selection
- [ ] 4.3 Test `:policies/check` with clean and conflicting configurations
- [ ] 4.4 Validate change with `openspec validate add-policy-conflict-detection --strict --no-interactive`
