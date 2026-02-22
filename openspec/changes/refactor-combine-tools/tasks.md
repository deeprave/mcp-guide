## Phase 1: Category Tool Consolidation
- [ ] 1.1 Add `action` field to all `Category*Args` classes (Literal type with valid actions)
- [ ] 1.2 Create `CategoryArgs` discriminated union type using `action` as discriminator
- [ ] 1.3 Create new `category` tool function with `@toolfunc(CategoryArgs)` decorator
- [ ] 1.4 Implement dispatcher that routes to existing `internal_category_*` functions based on action
- [ ] 1.5 Remove old `category_list`, `category_add`, `category_remove`, `category_change`, `category_update`, `category_list_files` tool functions
- [ ] 1.6 Update tests to use new unified tool interface
- [ ] 1.7 Verify all 1453 tests pass

## Phase 2: Collection Tool Consolidation
- [ ] 2.1 Add `action` field to all `Collection*Args` classes (Literal type with valid actions)
- [ ] 2.2 Create `CollectionArgs` discriminated union type using `action` as discriminator
- [ ] 2.3 Create new `collection` tool function with `@toolfunc(CollectionArgs)` decorator
- [ ] 2.4 Implement dispatcher that routes to existing `internal_collection_*` functions based on action
- [ ] 2.5 Remove old `collection_list`, `collection_add`, `collection_remove`, `collection_change`, `collection_update` tool functions
- [ ] 2.6 Update tests to use new unified tool interface
- [ ] 2.7 Verify all tests pass

## Phase 3: Flag Tool Consolidation
- [ ] 3.1 Add `action` field to flag Args classes (Literal type: "list", "get", "set")
- [ ] 3.2 Add `type` field to flag Args classes (Literal["project"] | None for project vs global)
- [ ] 3.3 Create `FlagArgs` discriminated union type using `action` as discriminator
- [ ] 3.4 Create new `flag` tool function with `@toolfunc(FlagArgs)` decorator
- [ ] 3.5 Implement dispatcher that routes based on action and type to existing internal functions
- [ ] 3.6 Remove old flag tool functions (6 tools: list/get/set for both project and feature)
- [ ] 3.7 Update tests to use new unified tool interface
- [ ] 3.8 Verify all tests pass

## Phase 4: Profile Tool Consolidation
- [ ] 4.1 Add `action` field to profile Args classes (Literal type: "list", "show", "use")
- [ ] 4.2 Create `ProfileArgs` discriminated union type using `action` as discriminator
- [ ] 4.3 Create new `profile` tool function with `@toolfunc(ProfileArgs)` decorator
- [ ] 4.4 Implement dispatcher that routes to existing `internal_*_profile*` functions based on action
- [ ] 4.5 Remove old `list_profiles`, `show_profile`, `use_project_profile` tool functions
- [ ] 4.6 Update tests to use new unified tool interface
- [ ] 4.7 Verify all tests pass

## Phase 5: Project Tool Consolidation
- [ ] 5.1 Add `action` field to project Args classes (Literal type: "get", "set", "list", "all", "clone")
- [ ] 5.2 Create `ProjectArgs` discriminated union type using `action` as discriminator
- [ ] 5.3 Create new `project` tool function with `@toolfunc(ProjectArgs)` decorator
- [ ] 5.4 Implement dispatcher that routes to existing `internal_*_project*` functions based on action
- [ ] 5.5 Remove old `get_project`, `set_project`, `list_projects`, `list_project`, `clone_project` tool functions
- [ ] 5.6 Update tests to use new unified tool interface
- [ ] 5.7 Verify all tests pass

## Phase 6: Validation and Documentation
- [ ] 6.1 Run full test suite - verify all 1453 tests pass
- [ ] 6.2 Run linting checks (`ruff check`)
- [ ] 6.3 Run type checks (`mypy`)
- [ ] 6.4 Verify tool count reduced from 35 to 23 tools
- [ ] 6.5 Test tool discovery with MCP client
- [ ] 6.6 Update any documentation referencing old tool names
