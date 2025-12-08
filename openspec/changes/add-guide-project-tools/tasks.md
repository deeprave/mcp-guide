# Implementation Tasks: Project Management Tools

## Overview

This change implements five project management tools for multi-project workflows:
1. `get_current_project` - Get current project information
2. `set_current_project` - Switch to a project by name
3. `clone_project` - Copy project configuration
4. `list_projects` - List all projects
5. `list_project` - Get specific project details

## Documentation

- **Specification:** `spec.md` - Complete tool specifications and requirements
- **Implementation Plan:** `implementation-plan.md` - Detailed TDD tasks broken into phases

## Implementation Phases

### Phase 1: Read-only Tools (14 tasks)
- [x] Add error constants
- [x] Implement `get_current_project` (verbose/non-verbose) - **COMPLETE (GUIDE-111)**
- [ ] Implement `list_projects` (verbose/non-verbose)
- [ ] Implement `list_project`
- [x] Register tools (get_current_project registered)

### Phase 2: Project Switching (5 tasks) - **COMPLETE (GUIDE-112)**
- [x] Implement `set_current_project` (verbose/non-verbose)
- [x] Test project creation
- [x] Reuse existing `switch_project` logic

### Phase 3: Clone Functionality (12 tasks)
- Implement `clone_project` with merge/replace logic
- Implement conflict detection
- Implement safeguards and force override
- Test 1-arg and 2-arg modes
- Test cache reload

### Phase 4: Integration (3 tasks)
- Multi-project workflow tests
- Documentation updates
- ROADMAP updates

## Total Tasks: 34

See `implementation-plan.md` for detailed task breakdown with test requirements.

## Key Design Decisions

1. **Reuse Existing Logic:** `set_current_project` uses existing `switch_project` internally
2. **Result Pattern:** All tools return `Result[T]` following ADR-003
3. **Tool Conventions:** All tools follow ADR-008 with ToolArguments schemas
4. **Safeguards:** `clone_project` has safeguards for destructive operations
5. **Cache Reload:** Automatic cache reload when current project modified

## Dependencies

- `mcp_guide.session` - Session and project management
- `mcp_guide.config` - ConfigManager for project configs
- `mcp_guide.models` - Project, Category, Collection models
- `mcp_core.result` - Result pattern
- `mcp_core.tool_arguments` - ToolArguments base class

## Testing Requirements

- Unit tests for all argument schemas
- Unit tests for error cases
- Integration tests for multi-project workflows
- Integration tests for clone operations
- Test coverage >90%
