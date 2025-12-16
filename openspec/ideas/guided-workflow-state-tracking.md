# Guided Workflow State Tracking

**Created**: 2025-12-16T21:52:24+11:00  
**Status**: Idea  
**Category**: Development Workflow

## Overview

A resumable state tracking system for guided workflows with five phases: discussion, planning, implementation, check, and review. The MCP server handles phase transitions and provides workflow update reminders to agents.

## Workflow Phases

1. **Discussion** - Alignment and requirements gathering (no code changes)
2. **Planning** - Create implementation plans (no code changes)  
3. **Implementation** - Update production code and tests
4. **Check** - Run tests and code quality tools
5. **Review** - Wait for and address user review

## File Structure

### Primary State File
`.todo/{feature-id}-workflow.md`
```markdown
# Workflow State: {feature-name}

## Current Phase: IMPLEMENTATION
- **Status**: In Progress  
- **Started**: 2025-12-16T20:30:00+11:00
- **OpenSpec Feature**: list-category-files
- **Description**: Implementing category file listing tool

## Phase Details
### Current Focus
- Writing integration tests for category_list_files
- Next: Tool registration verification

### Blockers/Issues
- None

## Recent Milestones
- 2025-12-16T20:30:00: PLANNING → IMPLEMENTATION (plan approved)
- 2025-12-16T20:00:00: DISCUSSION → PLANNING (requirements gathered)

## Key Conversation Points
- User requested minimal implementation approach
- TDD methodology confirmed as requirement
- Dict-based config compatibility issues discovered

## Todo Lists
- **Active**: 1765877138441 (Implementation tasks)
- **Completed**: []

## Checkpoints
- checkpoint-planning-complete-20251216T203000.md
```

### Checkpoint Files
`.todo/{feature-id}-checkpoint-{phase}-{timestamp}.md`
- Created at major phase transitions
- Snapshot of complete state at that moment
- Allows rollback to previous phases if needed

## MCP Tool Interface

New `workflow_state` tool with commands:

### Core Commands
- `init` - Start new workflow tracking for OpenSpec feature
- `update` - Update current phase details, focus, or conversation points
- `transition` - Move between phases with validation and automatic timestamping
- `checkpoint` - Create milestone snapshot at phase completion
- `resume` - Load and display current state for agent context
- `status` - Quick status check and next action reminder

### Transition Validation
- DISCUSSION → PLANNING (requirements gathered)
- PLANNING → IMPLEMENTATION (plan approved by user)
- IMPLEMENTATION → CHECK (code complete)
- CHECK → REVIEW (tests pass, quality checks complete)
- REVIEW → COMPLETE (user approval) or back to earlier phases

### Agent Reminders
MCP server provides periodic reminders to agents:
- Update workflow state after significant progress
- Transition phases when criteria met
- Create checkpoints at milestones
- Resume context from workflow state on restart

## Integration Points

- **Todo Lists**: References existing `todo_list` tool IDs
- **OpenSpec**: Tracks OpenSpec feature IDs and progress
- **Conversation Memory**: Preserves key discussion points across sessions
- **Resumability**: Agent reads workflow state on restart to continue context
- **User Editable**: Markdown format allows direct user modifications

## Benefits

1. **Resumable State**: Survives power outages and session restarts
2. **Context Preservation**: Maintains conversation history and key decisions
3. **Progress Tracking**: Clear milestones and phase transitions
4. **User Transparency**: Human-readable markdown format
5. **Tool Integration**: Works with existing todo and OpenSpec systems
6. **Automated Reminders**: MCP server prompts agents to maintain state

## Implementation Requirements

- New MCP tool for workflow state management
- Integration with existing `.todo` folder patterns
- Phase transition validation logic
- Automatic reminder system for agents
- Checkpoint creation and restoration
- Resume functionality for interrupted sessions

## Related Ideas and Dependencies

### Command-Based Prompt System Integration
**Reference**: `openspec/ideas/command_prompt_system_plan.md`

The command-based prompt system provides natural integration points for workflow management:

**Workflow Commands**:
- `:workflow/status` - Display current workflow state
- `:workflow/transition` - Move between phases with validation
- `:workflow/checkpoint` - Create milestone snapshots
- `:workflow/resume` - Load workflow context after interruption
- `:workflow/help` - Show available workflow commands

**Template Context**: Workflow commands can access full project context including:
- Current phase and status
- Recent milestones and conversation points
- Active todo lists and OpenSpec feature IDs
- Phase transition history

**Implementation Synergy**: The command system's `_commands` directory structure aligns perfectly with workflow management needs, providing a discoverable interface for workflow operations.

### User-Defined Workflows Integration
**Reference**: `openspec/ideas/user-defined-workflows.md`

The user-defined workflows idea provides the foundation for flexible phase management:

**Phase Definition**: Instead of hardcoded phases (discussion, planning, implementation, check, review), workflows can be defined per-project:
- Simple: `plan → implement → review`
- Standard: `discuss → plan → implement → check → review`  
- Complex: `research → design → prototype → implement → test → review → deploy`

**State File Coordination**: Both systems use state files but serve different purposes:
- **User-defined workflows**: `.guide` file tracks current phase name
- **Guided workflow tracking**: `.todo/{feature-id}-workflow.md` tracks detailed state

**Unified Approach**: These can work together where:
- User-defined workflows define the available phases and transitions
- Guided workflow tracking provides detailed state management within those phases
- Command system provides the interface for both

### Dependencies and Interactions

1. **Phase Validation**: Guided workflow state tracking should validate transitions against user-defined workflow rules
2. **Command Integration**: Workflow commands should respect user-defined phase definitions
3. **State Synchronization**: The `.guide` file and workflow state files should remain synchronized
4. **Template Context**: Workflow commands need access to both phase definitions and detailed tracking state

### Updated Architecture

**Layered Approach**:
1. **User-Defined Workflows** (Foundation) - Define available phases and rules
2. **Guided Workflow State Tracking** (Detail Layer) - Track progress within phases
3. **Command-Based Prompts** (Interface Layer) - Provide discoverable workflow operations

**File Structure Integration**:
```
docroot/
├── _commands/
│   └── workflow/
│       ├── status.mustache     # :workflow/status
│       ├── transition.mustache # :workflow/transition  
│       └── checkpoint.mustache # :workflow/checkpoint
├── .guide                      # Current phase (user-defined workflows)
└── .todo/
    └── {feature-id}-workflow.md # Detailed state tracking
```

## Future Enhancements

- Visual workflow status in development tools
- Integration with git commit messages
- Automated phase detection based on file changes
- Workflow analytics and time tracking
- Template workflows for common feature types
- Cross-project workflow pattern sharing
- Workflow validation and linting tools
