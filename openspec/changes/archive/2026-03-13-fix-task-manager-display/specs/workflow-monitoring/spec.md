## MODIFIED Requirements

### Requirement: Workflow Context for Template Rendering
The system SHALL provide workflow context data for template rendering that includes both workflow state and task manager statistics.

#### Scenario: Task manager statistics included
- **WHEN** `WorkflowContextCache.get_workflow_context()` is called
- **THEN** the returned context includes a `tasks` key
- **AND** `tasks` contains `count`, `peak_count`, `total_timer_runs`, `running`, and `timers` from `task_manager.get_task_statistics()`
- **AND** numeric values default to `0` when no tasks are active

#### Scenario: Status command displays task statistics
- **WHEN** user invokes `:status` command
- **THEN** the Task Manager section displays `Active Tasks: N (peak: M)`
- **AND** displays `Timer Events: K total`
- **AND** shows `0` for counts when no tasks exist (not empty strings)
