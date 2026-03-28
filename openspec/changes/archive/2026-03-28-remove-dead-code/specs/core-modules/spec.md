## ADDED Requirements

### Requirement: Dead Code Prevention
The system SHALL maintain less than 2% dead code as measured by vulture at 80% confidence.

#### Scenario: Vulture check passes
- **WHEN** `vulture src/mcp_guide/ --min-confidence 80` is run
- **THEN** only false positives (framework callbacks, dynamic registration) SHALL be reported

## REMOVED Requirements

### Requirement: Unused Utility Functions
**Reason**: Multiple modules contain functions that were never integrated or were superseded by later implementations. These include `WorkflowContextCache`, `SecurityPolicy`, `handle_project_load`, `render_template_with_context_chain`, and ~40 other dead functions/methods totalling ~942 lines.
**Migration**: No migration needed - code is unreachable from all production paths.
