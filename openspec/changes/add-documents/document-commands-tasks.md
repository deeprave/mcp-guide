# add-documents/document-commands Implementation Plan

Add prompt command templates for managing stored documents via the agent. Templates instruct the agent which tools to call with what arguments — no production code changes required.

## 1. Parent Command Summary

- [x] 1.1 Create `_commands/document.mustache` — type `user/information`, list subcommands (add, remove, list) with usage examples

## 2. Document Add Command

- [x] 2.1 Create `_commands/document/add.mustache` — type `agent/instruction`, usage `:document/add <category> <path> [--as <name>] [--force]`
  - minargs: 2 (category, path)
  - argrequired for `--as`
  - Instruct agent to: read file content and mtime from `path`, call `send_file_content` with content, path, category, name (from `--as` or basename of path), mtime, and optional force

## 3. Document Remove Command

- [x] 3.1 Create `_commands/document/remove.mustache` — type `agent/instruction`, usage `:document/remove <category> <name>`
  - minargs: 2 (category, name)
  - Instruct agent to call `document_remove` with category and name

## 4. Document List Command

- [x] 4.1 Create `_commands/document/list.mustache` — type `agent/instruction`, usage `:document/list <name>`
  - minargs: 1 (category name)
  - Instruct agent to call `category_list_files` with name and source=stored
