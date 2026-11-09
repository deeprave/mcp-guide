# Spec Delta

## ADDED Requirements

### Requirement: Worktree inventory template projection

When worktree support is active, template rendering SHALL expose a read-only
`worktree.inventory` projection for the bound session. It SHALL provide whether
the inventory is current, its observation time when current, and its reported
worktree paths.

#### Scenario: Current inventory is rendered
- **GIVEN** the bound session has a current client worktree inventory
- **WHEN** a worktree command template is rendered
- **THEN** `worktree.inventory.current` SHALL be true
- **AND** the projection SHALL expose the reported paths and observation time

#### Scenario: Missing or expired inventory is rendered
- **GIVEN** the bound session has no worktree inventory or its inventory has expired
- **WHEN** a worktree command template is rendered
- **THEN** `worktree.inventory.current` SHALL be false
- **AND** the projection SHALL not expose stale paths as current

### Requirement: Worktree inventory freshness

Guide SHALL retain a client-reported worktree inventory for no more than one
minute in its bound session. It SHALL invalidate the inventory when it issues
guidance that creates or removes a worktree.

#### Scenario: Worktree-changing guidance invalidates inventory
- **GIVEN** a session has a current worktree inventory
- **WHEN** Guide issues linked-worktree creation or removal guidance
- **THEN** the inventory SHALL no longer be current

#### Scenario: Worktree command needs a current inventory
- **GIVEN** a worktree command requires inventory and none is current
- **WHEN** the command is requested
- **THEN** its rendered guidance SHALL direct the agent to refresh the inventory
