## REMOVED Requirements

### Requirement: TaskManager State Machine
**Reason**: FSM was never implemented. The actual coordination system is a pubsub/event model documented in `workflow-events`.
**Migration**: See `workflow-events` spec for the EventType/subscribe/TaskSubscriber pattern.

### Requirement: Task Protocol Interface
**Reason**: Replaced by `TaskSubscriber` protocol in the pubsub model.
**Migration**: See `workflow-events` spec.

### Requirement: MCP Result Enhancement
**Reason**: `instruction` field on Result is implemented but not FSM-specific.
**Migration**: See `tool-infrastructure` spec for Result pattern.

### Requirement: Agent Communication Tools
**Reason**: FSM-specific routing was never built.
**Migration**: N/A.

### Requirement: Generic Task Coordination
**Reason**: Superseded by pubsub model in `workflow-events`.
**Migration**: See `workflow-events` spec.
