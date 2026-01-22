# Tasks: add-guide-installer

## Phase 1: Core Installer Module
- [ ] Implement file hashing (SHA256)
- [ ] Implement original file tracking (_installed.zip)
- [ ] Implement diff computation and application
- [ ] Implement smart update logic
- [ ] Implement template discovery
- [ ] Implement file installation
- [ ] Implement installation orchestration

## Phase 2: Configuration Management
- [ ] Implement config file operations
- [ ] Implement path resolution
- [ ] Implement path validation

## Phase 3: CLI Script
- [ ] Implement argument parsing
- [ ] Implement interactive prompts
- [ ] Implement installation execution
- [ ] Implement error handling

## Phase 4: Server Integration
- [ ] Add CLI options to server
- [ ] Implement first-run detection
- [ ] Implement normal startup flow

## Phase 5: Package Configuration
- [ ] Create template package structure
- [ ] Add console script entry point
- [ ] Add dependencies to pyproject.toml

## Phase 6: Profile Support
- [ ] Implement profile detection
- [ ] Implement profile loading and merging
- [ ] Modify clone_project for profiles
- [ ] Modify set_current_project for default profile
- [ ] Create profile templates (_default, _python, _rust, _java, _typescript)

## Testing
- [ ] Unit tests for all modules
- [ ] Integration tests for installation flow
- [ ] Integration tests for update flow
- [ ] Manual testing of mcp-install script
- [ ] Manual testing of first-run installation

## Documentation
- [ ] Update README with installation instructions
- [ ] Document profile system
- [ ] Document update process
