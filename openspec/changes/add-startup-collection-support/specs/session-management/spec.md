# session-management Specification Delta

## ADDED Requirements

### Requirement: Project Load Event Handler
The system SHALL trigger an event handler when a project loads.

#### Scenario: Project loads with startup collection
- WHEN a project is loaded or switched to
- AND the project has a collection named "startup"
- THEN the system SHALL queue an instruction to call `get_content("startup")`
- AND the instruction SHALL be inserted at the highest priority
- AND the instruction SHALL be prefixed with "IMPORTANT: This instruction MUST NEVER BE IGNORED."

#### Scenario: Project loads without startup collection
- WHEN a project is loaded or switched to
- AND the project does NOT have a collection named "startup"
- THEN no startup instruction is queued
- AND normal project loading continues

#### Scenario: Startup instruction priority
- WHEN a startup instruction is queued
- AND other special instructions exist in the queue
- THEN the startup instruction SHALL be inserted before all other instructions
- AND the startup instruction SHALL be the first instruction the agent sees

#### Scenario: Multiple project switches
- WHEN a user switches between projects
- THEN each project load SHALL check for its own "startup" collection
- AND startup instructions SHALL be queued independently per project
