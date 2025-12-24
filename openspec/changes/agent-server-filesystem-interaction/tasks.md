# Implementation Tasks

## Planning Phase

- [ ] Review MCP sampling/completion request documentation
- [ ] Verify sampling support in target MCP clients (Claude Desktop, others)
- [ ] Validate spec formatting with `openspec validate agent-server-filesystem-interaction --strict`
- [ ] Resolve any validation errors before proceeding

## Implementation Phase

### 1. Core Filesystem Module

- [ ] Create `src/mcp_guide/filesystem/__init__.py` module structure
- [ ] Write tests for path validation logic
- [ ] Implement `PathValidator` class with security fencing
- [ ] Write tests for file operation primitives
- [ ] Implement `FilesystemBridge` class for sampling-based operations
- [ ] Write tests for directory listing functionality
- [ ] Implement directory discovery via sampling requests
- [ ] Write tests for file reading functionality
- [ ] Implement file content retrieval via sampling requests

### 2. Security System

- [ ] Create `src/mcp_guide/filesystem/security.py`
- [ ] Write tests for allowed path configuration
- [ ] Implement `SecurityPolicy` class with configurable allowed paths
- [ ] Write tests for path traversal prevention
- [ ] Implement path normalization and validation
- [ ] Write tests for symbolic link validation
- [ ] Implement symlink security checks
- [ ] Write tests for audit logging
- [ ] Implement security audit trail

### 3. Cache Manager

- [ ] Create `src/mcp_guide/filesystem/cache.py`
- [ ] Write tests for file content caching
- [ ] Implement `FileCache` class with LRU eviction
- [ ] Write tests for cache invalidation
- [ ] Implement modification-time-based invalidation
- [ ] Write tests for cache size limits
- [ ] Implement configurable cache size management
- [ ] Write tests for cache statistics
- [ ] Implement cache performance metrics

### 4. MCP Tools

- [ ] Write tests for `guide_cache_file` tool
- [ ] Implement `guide_cache_file` tool for agent-provided content
- [ ] Write tests for `guide_list_directory` tool
- [ ] Implement `guide_list_directory` tool using sampling requests
- [ ] Write tests for `guide_read_file` tool
- [ ] Implement `guide_read_file` tool using sampling requests
- [ ] Add tool documentation and examples

### 5. OpenSpec Integration

- [ ] Write tests for OpenSpec filesystem integration
- [ ] Update OpenSpec tools to use filesystem interaction
- [ ] Implement change discovery using directory listing
- [ ] Implement file content access for validation
- [ ] Write tests for interactive workflows
- [ ] Implement dynamic file-based operations

### 6. Configuration

- [ ] Write tests for configuration schema updates
- [ ] Add filesystem security configuration to project schema
- [ ] Implement default allowed paths configuration
- [ ] Write tests for per-project path customization
- [ ] Implement project-specific path overrides
- [ ] Update configuration documentation

### 7. Error Handling

- [ ] Write tests for file not found errors
- [ ] Implement clear error messages for missing files
- [ ] Write tests for permission denied errors
- [ ] Implement security violation error handling
- [ ] Write tests for sampling request failures
- [ ] Implement fallback behavior for unsupported clients
- [ ] Write tests for cache errors
- [ ] Implement cache failure recovery

### 8. Documentation

- [ ] Document filesystem interaction architecture
- [ ] Create security model documentation
- [ ] Write usage examples for new tools
- [ ] Document configuration options
- [ ] Create troubleshooting guide
- [ ] Update OpenSpec workflow documentation

## Check Phase

### Automated Checks

- [ ] Run test suite: `uv run pytest tests/`
- [ ] Verify all tests pass
- [ ] Run type checker: `uv run mypy src/`
- [ ] Resolve any type errors
- [ ] Run linter: `uv run ruff check src/`
- [ ] Fix any linting issues
- [ ] Verify code coverage meets threshold (>80%)

### Manual Testing

- [ ] Test directory listing with OpenSpec changes
- [ ] Test file reading with various file types
- [ ] Verify path traversal attacks are blocked
- [ ] Test cache performance with multiple files
- [ ] Verify cache invalidation works correctly
- [ ] Test error handling with missing/invalid files
- [ ] Verify sampling works with target MCP clients

### Review Checklist

- [ ] All specs validated with `openspec validate --strict`
- [ ] All tasks marked complete
- [ ] All automated checks passing
- [ ] Manual testing completed successfully
- [ ] Documentation updated
- [ ] Security review completed

### User Review

- [ ] **READY FOR REVIEW** - Request user review of implementation
- [ ] **Address review feedback** - Iterate on any concerns
- [ ] **USER APPROVAL RECEIVED** - Explicit consent required before archiving

## Archive Phase

- [ ] Verify user approval received
- [ ] Archive change: `openspec archive agent-server-filesystem-interaction --yes`
- [ ] Verify specs merged to source of truth
- [ ] Confirm change moved to archive
