# Implementation Tasks

## 1. Parser Enhancement
- [ ] 1.1 Add `argrequired` parameter to `parse_command_arguments()` signature
- [ ] 1.2 Implement logic to check if flag is in `argrequired` list when processing `--flag` (no `=`)
- [ ] 1.3 Consume next argument as value when flag is in `argrequired`
- [ ] 1.4 Add error when required flag has no value (missing or next token starts with `-`)
- [ ] 1.5 Write unit tests for all scenarios (equals syntax, space syntax, missing value, multiple flags, edge cases)

## 2. Frontmatter Processing
- [ ] 2.1 Update frontmatter parser to extract `argrequired` field from YAML
- [ ] 2.2 Validate `argrequired` is a list, log warning if invalid format
- [ ] 2.3 Pass `argrequired` list to command parser
- [ ] 2.4 Write unit tests for frontmatter parsing with/without `argrequired`

## 3. Template Updates
- [ ] 3.1 Add `argrequired` to `workflow/issue.mustache` for `tracking`, `issue`, `description`, `queue`
- [ ] 3.2 Add `argrequired` to `create/category.mustache` for `dir`, `patterns`, `description`
- [ ] 3.3 Add `argrequired` to `create/collection.mustache` for `description`
- [ ] 3.4 Update usage examples in templates to show both syntaxes work

## 4. Integration Testing
- [ ] 4.1 Test `:issue --tracking=GUIDE-177` (equals syntax still works)
- [ ] 4.2 Test `:issue --tracking GUIDE-177` (space syntax now works)
- [ ] 4.3 Test `:issue --tracking` (error message displayed)
- [ ] 4.4 Test `:create/category --description "Test files" tests` (space syntax)
- [ ] 4.5 Test backward compatibility with commands without `argrequired`

## 5. Documentation
- [ ] 5.1 Update command help text to reflect both syntaxes are supported
- [ ] 5.2 Add note about `argrequired` frontmatter field in template documentation

## 6. Validation
- [ ] 6.1 Run all existing tests - ensure 100% pass
- [ ] 6.2 Run `ruff check` and `mypy` - resolve all issues
- [ ] 6.3 Manual testing of affected commands
- [ ] 6.4 Verify error messages are clear and helpful
