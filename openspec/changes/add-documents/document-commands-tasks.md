# add-documents/document-commands Implementation Plan

Add prompt command templates for managing stored documents via the agent. Templates instruct the agent which tools to call with what arguments — no production code changes required.

## 1. Parent Command Summary

- [x] 1.1 Create `_commands/document.mustache` — type `user/information`, list subcommands (add, remove, list) with usage examples

## 2. Document Add Command

- [x] 2.1 Create `_commands/document/add.mustache` — base template with category, path, --as, --force

### 2a. Metadata and Type Extensions

- [x] 2a.1 Add `metadata` field to `SendFileContentArgs` and thread through `send_file_content` to event dispatch
- [x] 2a.2 Add `--metadata`, `--agent-info`, `--agent-instruction`, `--user-info` flags to `add.mustache`
  - argrequired for `--metadata`
  - Type flags are mutually exclusive; default is `agent/instruction`
  - Template instructs agent to parse metadata string into a dict

## 3. Document Remove Command

- [x] 3.1 Create `_commands/document/remove.mustache` — type `agent/instruction`, usage `:document/remove <category> <name>`
  - minargs: 2 (category, name)
  - Instruct agent to call `document_remove` with category and name

## 4. Document List Command

- [x] 4.1 Create `_commands/document/list.mustache` — type `agent/instruction`, usage `:document/list <category>`
  - minargs: 1 (category)
  - Instruct agent to call `category_list_files` with category and source=stored
