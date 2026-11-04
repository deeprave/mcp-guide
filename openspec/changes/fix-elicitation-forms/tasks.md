# Tasks

## 2. Fix server-side delivery

- [x] 2.1 Correct any fault found in the modern `input_required` / continuation handling
- [x] 2.2 Confirm rendering is identical across protocol generations when URI values satisfy all forms

## 5. Dynamic choice sources

- [x] 5.1 Move the command-only resolver to `mcp_guide/input_sources.py`, call it from the skill path, and add `project-categories` and `project-collections`
- [x] 5.2 Add `_choose-category` and `_choose-collection` partials and use them in the category and collection remove/files/update/change commands

## 6. Inherited-PWD startup sharing

- [x] 6.1 Add `inherited_pwd_is_server_cwd()` and `initial_filesystem_sharing()` and use them in `start_runtime`
- [x] 6.2 Document the conditions in `docs/user/protocol-and-sessions.md` and mention the opt-in briefly (stdio only) elsewhere

## 6a. Strict-client schema

- [x] 6a.1 Strip generated model and property titles from the legacy form schema (Codex rejects `title` and cancels)

## 7. Documentation

- [x] 7.1 Update `docs/developer/authoring-elicitation.md` with verified and unreliable patterns
