## 1. Specification
- [ ] 1.1 Define project-status capability spec with configurable state file
- [ ] 1.2 Define enhanced phase-tracking flag format (boolean/list with transition controls)
- [ ] 1.3 Define state file YAML format and validation rules
- [ ] 1.4 Define WorkflowManager FSM states and transitions
- [ ] 1.5 Define MCP tool interfaces for state management

## 2. Core Implementation
- [x] 2.1 Add phase-state-file feature flag with default '.guide.yaml' (implemented as workflow-file)
- [x] 2.2 Enhance phase-tracking flag parser for boolean/list values (implemented as workflow flag)
- [x] 2.3 Create TaskManager FSM with predefined state constants and task classification
- [x] 2.4 Implement Task protocol interface with async methods and timeout support
- [x] 2.5 Add asyncio timeout handling with weakref callbacks and automatic cleanup
- [x] 2.6 State file parser/validator implemented with configurable filename support
- [x] **NEW** 2.7 Implement flag validation registration system
- [x] **NEW** 2.8 Register workflow-specific semantic validators
- [x] **NEW** 2.9 Update flag setting operations to use registered validators

## 3. MCP Tools & Agent Data Interception
- [x] 3.1 Extend MCP Result structure with additional_instruction field
- [x] 3.2 Implement agent data interception system with bit-flag registration
- [x] 3.3 Create ephemeral interest registration with content-based callbacks
- [x] 3.4 Add conditional caching (only cache when tasks are interested)
- [x] 3.5 Implement response negotiation (tasks can modify/reject responses)
- [x] 3.6 State file reading via existing send_file_content tool (no additional tools needed)
- [x] 3.7 State file updating via existing filesystem tools (no additional tools needed)
- [x] 3.8 State change notification via additional_instruction field in tool responses
- [x] 3.9 Implement task classification (active vs scheduled) with proper coordination

## 4. Template Integration
- [x] 4.1 Add phase_state_file to template context (implemented as workflow configuration)
- [x] 4.2 Implement workflow state monitoring and caching system
- [x] 4.3 Create separate workflow context with independent lifecycle
- [x] 4.4 Add workflow template variables (workflow.phase, workflow.issue, etc.)
- [x] 4.5 Implement agent instruction system with _workflow directory
- [x] 4.6 Extend response processing for global additional_instruction injection
- [x] 4.7 Enhance partial support with frontmatter conditions
- [x] 4.8 Update status template to show workflow information conditionally
- [x] 4.9 Integrate workflow commands into existing command templates
- [x] 4.10 Make workflow commands configuration-aware and state-sensitive

## 5. Security & Validation
- [x] 5.1 Enforce state file location within allowed write paths (implemented in workflow flags)
- [x] 5.2 Add upfront validation before any agent requests (implemented via flag validators)
- [x] 5.3 Return clear error messages for invalid phase-state-file flag (implemented as ValidationError)
- [x] 5.4 Validate state file path resolution security (implemented in workflow file validation)
- [x] 5.5 Implement workflow state file change detection and monitoring
- [x] 5.6 Add proactive agent notification system for state changes
- [x] 5.7 Validate workflow instruction templates and frontmatter processing
- [x] 5.8 Ensure secure access to _workflow instruction directory
- [x] 5.9 Consolidate filesystem security policy implementations

## 6. Integration & Testing
- [x] 6.1 Update existing .guide.yaml to new format (already using current workflow state format)
- [x] 6.2 Test WorkflowManager FSM state transitions
- [x] 6.3 Test timeout handling and recovery
- [x] 6.4 Workflow context cache fully functional and operational
- [x] 6.5 Agent interactions with state management via existing filesystem tools
