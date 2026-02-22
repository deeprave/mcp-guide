## 1. Prerequisites
- [ ] 1.1 Verify `refactor-combine-tools` is complete and merged
- [ ] 1.2 Verify unified `category` and `collection` tools are available
- [ ] 1.3 Review existing command template structure

## 2. Create Project Command Namespace
- [ ] 2.1 Create `src/mcp_guide/templates/_commands/project/` directory
- [ ] 2.2 Create subdirectories: `category/`, `collection/`, `perm/`

## 3. Implement Project Category Commands
- [ ] 3.1 Create `project/category.mustache` dispatcher template
- [ ] 3.2 Create action-specific templates: `category/list.mustache`, `category/add.mustache`, etc.
- [ ] 3.3 Wire templates to call unified `category` tool with appropriate Args
- [ ] 3.4 Test all category actions work correctly

## 4. Implement Project Collection Commands
- [ ] 4.1 Create `project/collection.mustache` dispatcher template
- [ ] 4.2 Create action-specific templates: `collection/list.mustache`, `collection/add.mustache`, etc.
- [ ] 4.3 Wire templates to call unified `collection` tool with appropriate Args
- [ ] 4.4 Test all collection actions work correctly

## 5. Move Project Info Command
- [ ] 5.1 Move `_commands/info/project.mustache` to `_commands/project/info.mustache`
- [ ] 5.2 Create alias: `info/project.mustache` redirects to `project/info`
- [ ] 5.3 Test both paths work correctly

## 6. Reorganize Permission Commands
- [ ] 6.1 Create `project/perm.mustache` dispatcher template
- [ ] 6.2 Consolidate `perm/write-add`, `perm/read-add`, `perm/write-del`, `perm/read-del` logic
- [ ] 6.3 Implement action-first syntax: `add [file] [read|write]`, `del [file] [read|write]`
- [ ] 6.4 Test permission management works correctly

## 7. Remove Old Commands
- [ ] 7.1 Remove `_commands/create/category.mustache`
- [ ] 7.2 Remove `_commands/create/collection.mustache`
- [ ] 7.3 Remove `_commands/create/` directory if empty
- [ ] 7.4 Remove `_commands/perm/write-add.mustache`
- [ ] 7.5 Remove `_commands/perm/read-add.mustache`
- [ ] 7.6 Remove `_commands/perm/write-del.mustache`
- [ ] 7.7 Remove `_commands/perm/read-del.mustache`
- [ ] 7.8 Remove `_commands/perm/` directory if empty

## 8. Update Help System
- [ ] 8.1 Update `_commands/help.mustache` to reflect new command structure
- [ ] 8.2 Document `project/*` namespace commands
- [ ] 8.3 Document command aliases (e.g., `info/project` → `project/info`)

## 9. Testing and Validation
- [ ] 9.1 Test all `project/category` actions
- [ ] 9.2 Test all `project/collection` actions
- [ ] 9.3 Test `project/info` and `info/project` alias
- [ ] 9.4 Test all `project/perm` actions
- [ ] 9.5 Verify old command paths are removed or aliased
- [ ] 9.6 Run full test suite
- [ ] 9.7 Test with actual MCP client

## 10. Documentation
- [ ] 10.1 Update any documentation referencing old command paths
- [ ] 10.2 Document new `project/*` namespace structure
- [ ] 10.3 Document migration path from old commands
