## 1. Prerequisites
- [x] 1.1 Review existing command template structure
- [x] 1.2 Review existing category/collection tools and their Args classes

## 2. Create Project Command Namespace
- [x] 2.1 Create `src/mcp_guide/templates/_commands/project/` directory
- [x] 2.2 Create subdirectories: `category/`, `collection/`, `perm/`

## 3. Implement Project Category Commands
- [x] 3.1 Create `project/category.mustache` overview template
- [x] 3.2 Create action-specific templates: `category/list.mustache`, `category/add.mustache`, etc.
- [x] 3.3 Wire templates to call existing tools: `category_list`, `category_add`, etc.
- [x] 3.4 Test all category actions work correctly

## 4. Implement Project Collection Commands
- [x] 4.1 Create `project/collection.mustache` overview template
- [x] 4.2 Create action-specific templates: `collection/list.mustache`, `collection/add.mustache`, etc.
- [x] 4.3 Wire templates to call existing tools: `collection_list`, `collection_add`, etc.
- [x] 4.4 Test all collection actions work correctly

## 5. Move Project Info Command
- [x] 5.1 Move `_commands/info/project.mustache` to `_commands/project/project.mustache` (changed to project.mustache for consistency)
- [x] 5.2 Create aliases: `info/project` and `project/info` for backward compatibility
- [x] 5.3 Test both paths work correctly

## 6. Implement Permission Management Tools
- [x] 6.1 Create `AddPermissionPathArgs` and `RemovePermissionPathArgs` classes in `tool_project.py`
- [x] 6.2 Implement `add_permission_path` tool using `@toolfunc` decorator
- [x] 6.3 Implement `remove_permission_path` tool using `@toolfunc` decorator
- [x] 6.4 Reuse existing validation from `models/project.py` validators
- [x] 6.5 Handle duplicates silently (no error if path already exists)
- [x] 6.6 Add parametrized tests for both tools
- [x] 6.7 Test edge cases: invalid paths, duplicates, removal

## 7. Update Permission Command Templates
- [x] 7.1 Update `project/perm/write/add.mustache` to call `add_permission_path` tool
- [x] 7.2 Update `project/perm/write/remove.mustache` to call `remove_permission_path` tool
- [x] 7.3 Update `project/perm/read/add.mustache` to call `add_permission_path` tool
- [x] 7.4 Update `project/perm/read/remove.mustache` to call `remove_permission_path` tool
- [x] 7.5 Remove all direct config file editing instructions
- [x] 7.6 Test all permission commands work correctly

## 8. Reorganize Permission Commands (COMPLETED - needs tool backing)
- [x] 8.1 Remove old perm commands (write-add, read-add, write-del, read-del)
- [x] 8.2 Create `project/perm.mustache` showing current permissions
- [x] 8.3 Create new permission command templates (need tool updates per sections 6-7)
- [x] 8.4 Update documentation to reflect tool-based approach

## 9. Implement Flag Commands
- [x] 7.1 Create `_commands/flags/` directory
- [x] 7.2 Create `flags/project.mustache` overview template
- [x] 7.3 Create action templates: `project/list.mustache`, `project/get.mustache`, `project/set.mustache`, `project/remove.mustache`
- [x] 7.4 Wire to existing tools: `list_project_flags`, `get_project_flag`, `set_project_flag`
- [x] 7.5 Create `flags/feature.mustache` overview template
- [x] 7.6 Create action templates: `feature/list.mustache`, `feature/get.mustache`, `feature/set.mustache`, `feature/remove.mustache`
- [x] 7.7 Wire to existing tools: `list_feature_flags`, `get_feature_flag`, `set_feature_flag`
- [x] 7.8 Create `flags.mustache` combined overview template
- [x] 7.9 Add flag descriptions and scope restrictions
- [x] 7.10 Fix terminology: use "Feature Flags" not "Global Flags"
- [x] 7.11 Test all flag commands work correctly

## 10. Remove Old Commands
- [x] 8.1 Remove `_commands/create/category.mustache`
- [x] 8.2 Remove `_commands/create/collection.mustache`
- [x] 8.3 Remove `_commands/create/` directory
- [x] 8.4 Remove `_commands/perm/` directory and old commands
- [x] 8.5 Create `project/perm.mustache` for viewing permissions
- [x] 8.9 Remove `_commands/info/flags.mustache`

## 11. Update Help System
- [x] 9.1 Help system auto-discovers commands - no manual updates needed
- [x] 9.2 New `project/*` namespace commands automatically discovered
- [x] 9.3 New `flags/*` namespace commands automatically discovered
- [x] 9.4 Command aliases automatically discovered from frontmatter

## 12. Testing and Validation
- [x] 10.1 Test all `project/category` actions
- [x] 10.2 Test all `project/collection` actions
- [x] 10.3 Test `project/info` and `info/project` alias
- [x] 10.4 Test `project/perm` command
- [x] 10.5 Test all `flags/project` actions
- [x] 10.6 Test all `flags/feature` actions
- [x] 10.7 Test `flags` combined list
- [x] 10.8 Test flag value as positional argument
- [x] 10.9 Test `flags/list` combined command
- [x] 10.10 Run full test suite - all 1502 tests passing
- [x] 10.11 Test with actual MCP client (interactive testing throughout)
- [x] 10.12 Fix client-context-detailed template (removed eq/contains lambdas)

## 13. Documentation
- [x] 11.1 Update `docs/user/commands.md` with new command structure
- [x] 11.2 Update `docs/user/content-management.md` with category/collection examples
- [x] 11.3 Update `docs/user/feature-flags.md` with new flags commands
- [x] 11.4 All commands use `{{@}}guide :command` format (not `{{tool_prefix}}guide`)
- [x] 11.5 All templates use guide markup variables ({{h1}}, {{h2}}, {{b}})
- [x] 11.6 Preserve existing style and formatting in all documentation updates

## 14. Additional Improvements (Beyond Original Spec)
- [x] 12.1 Add category field to all command templates for better help organization
- [x] 12.2 Create new categories: `project-and-feature-flags`, `project-categories`, `project-collections`, `project-permissions`
- [x] 12.3 Unified flag category: merge `feature-flags` and `project-flags` into `project-and-feature-flags`
- [x] 12.4 Add permission management commands: `perm/read/add`, `perm/read/remove`, `perm/write/add`, `perm/write/remove`
- [x] 12.5 Fix prompt prefix: use `{{@}}guide` instead of `{{tool_prefix}}guide` for command examples
- [x] 12.6 Rename `project/info.mustache` to `project/project.mustache` for consistency with other project commands
