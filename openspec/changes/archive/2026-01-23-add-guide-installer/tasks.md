# Tasks: add-guide-installer

## Phase 1: Core Installer Module ✅ COMPLETED
- [x] Implement file hashing (SHA256)
- [x] Implement original file tracking (_installed.zip)
- [x] Implement diff computation and application
- [x] Implement smart update logic
- [x] Implement template discovery
- [x] Implement file installation
- [x] Implement installation orchestration

## Phase 2: Configuration Management ✅ COMPLETED
- [x] Implement config file operations
- [x] Implement path resolution
- [x] Implement path validation

## Phase 3: CLI Script ✅ COMPLETED
- [x] Implement argument parsing
- [x] Implement interactive prompts
- [x] Implement installation execution
- [x] Implement error handling

## Phase 4: Server Integration ✅ COMPLETED
- [x] Add CLI options to server
- [x] Implement first-run detection
- [x] Implement normal startup flow

## Phase 5: Package Configuration ✅ COMPLETED
- [x] Create template package structure
- [x] Add console script entry point
- [x] Add dependencies to pyproject.toml

## Phase 6: Profile Support ✅ COMPLETED
See: `specs/profile-support/` for detailed implementation
- [x] Implement profile model and loading
- [x] Implement use_project_profile tool
- [x] Track applied profiles in project metadata
- [x] Create initial profile templates (python, rust, jira, github, tdd)
- [x] Add profile listing and inspection tools
- [x] Unit and integration tests

## Testing ✅ COMPLETED
- [x] Unit tests for all modules
- [x] Integration tests for installation flow
- [x] Integration tests for update flow
- [x] Manual testing of mcp-install script
- [x] Manual testing of first-run installation

## Documentation ✅ COMPLETED
- [x] Update README with installation instructions
- [x] Document profile system (in OpenSpec)
- [x] Document update process
