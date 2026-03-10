# Implementation Tasks

## 1. Parser Enhancement
- [x] 1.1 Add `argrequired` parameter to `parse_command_arguments()` signature
- [x] 1.2 Implement logic to check if flag is in `argrequired` list when processing `--flag` (no `=`)
- [x] 1.3 Consume next argument as value when flag is in `argrequired`
- [x] 1.4 Add error when required flag has no value (missing or next token starts with `-`)
- [x] 1.5 Write unit tests for all scenarios (equals syntax, space syntax, missing value, multiple flags, edge cases)

## 2. Frontmatter Processing
- [x] 2.1 Update frontmatter parser to extract `argrequired` field from YAML
- [x] 2.2 Validate `argrequired` is a list, log warning if invalid format
- [x] 2.3 Pass `argrequired` list to command parser
- [x] 2.4 Write unit tests for frontmatter parsing with/without `argrequired`

## 3. Template Updates
- [x] 3.1 Add `argrequired` to `workflow/issue.mustache` for `tracking`, `issue`, `description`, `queue`
- [x] 3.2 Add `argrequired` to `project/category/add.mustache` for `dir`, `patterns`, `description`
- [x] 3.3 Add `argrequired` to `project/category/change.mustache` for `new_name`, `new_dir`, `new_patterns`, `new_description`
- [x] 3.4 Add `argrequired` to `project/category/update.mustache` for `add_patterns`, `remove_patterns`
- [x] 3.5 Add `argrequired` to `project/collection/add.mustache` for `categories`, `description`
- [x] 3.6 Add `argrequired` to `project/collection/change.mustache` for `new_name`, `new_categories`, `new_description`
- [x] 3.7 Add `argrequired` to `project/collection/update.mustache` for `add_categories`, `remove_categories`
- [x] 3.8 Add `argrequired` to `flags/project/set.mustache` for `value`
- [x] 3.9 Add `argrequired` to `flags/feature/set.mustache` for `value`

## 4. Integration Testing
- [x] 4.1 Test `:issue --tracking=GUIDE-177` (equals syntax still works)
- [x] 4.2 Test `:issue --tracking GUIDE-177` (space syntax now works)
- [x] 4.3 Test `:issue --tracking` (error message displayed)
- [x] 4.4 Test backward compatibility with commands without `argrequired`
- [x] 4.5 All 1550 tests pass

## 5. Documentation
- [x] 5.1 Update CHANGELOG.md with new feature
- [x] 5.2 Add `argrequired` documentation to `docs/developer/command-authoring.md`
- [x] 5.3 Update `docs/user/commands.md` with flag syntax examples
- [x] 5.4 Document dash-prefixed value handling (requires equals syntax)

## 6. Validation
- [x] 6.1 Run all existing tests - all 1550 tests pass
- [x] 6.2 Run `ruff check` and `mypy` - all checks pass
- [x] 6.3 Code review completed - 0 critical issues, 2 minor warnings addressed
- [x] 6.4 Error messages verified clear and helpful

## 7. Additional Work
- [x] 7.1 Address code review feedback: add logging for frontmatter failures
- [x] 7.2 Preserve INSTRUCTION_DISPLAY_ONLY flag for parse errors
- [x] 7.3 Create reusable `_client-info` partial for agent detection
- [x] 7.4 Update `:status` and `:review` commands to use client-info partial
