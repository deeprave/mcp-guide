## 1. Specification
- [ ] 1.1 Define project-status capability spec with configurable state file
- [ ] 1.2 Define enhanced phase-tracking flag format (boolean/list with transition controls)
- [ ] 1.3 Define state file YAML format and validation rules
- [ ] 1.4 Define WorkflowManager FSM states and transitions
- [ ] 1.5 Define MCP tool interfaces for state management

## 2. Core Implementation
- [ ] 2.1 Add phase-state-file feature flag with default '.guide.yaml'
- [ ] 2.2 Enhance phase-tracking flag parser for boolean/list values
- [ ] 2.3 Create WorkflowManager FSM with predefined state constants
- [ ] 2.4 Implement callback-based task coordination (start_task, completed_task)
- [ ] 2.5 Add timeout handling and agent notification
- [ ] 2.6 Create state file parser/validator with configurable filename

## 3. MCP Tools
- [ ] 3.1 Add MCP tools for reading state file content
- [ ] 3.2 Add MCP tools for updating state file structure
- [ ] 3.3 Add state change notification handling
- [ ] 3.4 Implement single active task constraint

## 4. Template Integration
- [ ] 4.1 Add phase_state_file to template context
- [ ] 4.2 Update status template to show workflow information
- [ ] 4.3 Make status display conditional on phase-tracking configuration
- [ ] 4.4 Add phase-specific instruction inclusion
- [ ] 4.5 Implement frontmatter conditional rendering for feature flags
- [ ] 4.6 Add frontmatter phase requirement matching (requires-phase-tracking)
- [ ] 4.7 Add template suppression when requirements not met

## 5. Security & Validation
- [ ] 5.1 Enforce state file location within allowed write paths
- [ ] 5.2 Add upfront validation before any agent requests
- [ ] 5.3 Return clear error messages for invalid phase-state-file flag
- [ ] 5.4 Validate state file path resolution security
- [ ] 5.5 Implement automatic state file change detection
- [ ] 5.6 Add proactive agent notification for state changes
- [ ] 5.7 Handle state file monitoring without sampling support

## 6. Integration & Testing
- [ ] 6.1 Update existing .guide.yaml to new format
- [ ] 6.2 Test WorkflowManager FSM state transitions
- [ ] 6.3 Test timeout handling and recovery
- [ ] 6.4 Test status command with various phase-tracking configurations
- [ ] 6.5 Test agent interactions with state management tools
