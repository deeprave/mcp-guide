# Spec Delta

## REMOVED Requirements

### Requirement: Handoff Command Flexibility

**Reason**: Proactive handoff context is requested by the `handoff-context` feature flag. The separate read/write command is no longer a Guide entrypoint.
**Migration**: Use the `handoff-context` flag for startup handoff guidance. Direct agent instructions can still ask for handoff context while the flag is disabled. `agent.has_handoff` remains the separate-execution capability and is unchanged.
