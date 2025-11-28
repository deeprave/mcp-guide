# Architecture Decision Records (ADR) Index

This index tracks all ADRs including historical decisions that have been superseded or removed.

## Active ADRs

### ADR-001: Tool Naming Convention
**Status:** Accepted
**Date:** 2025-11-25
**File:** [001-tool-naming-convention.md](001-tool-naming-convention.md)

### ADR-002: MCP Server Framework
**Status:** Accepted
**Date:** 2025-11-25
**File:** [002-mcp-server-framework.md](002-mcp-server-framework.md)

### ADR-003: Result Pattern for Tool and Prompt Responses
**Status:** Accepted
**Date:** 2025-11-25
**File:** [003-result-pattern-response.md](003-result-pattern-response.md)
**Note:** Renamed from "Result Pattern for Error Handling" on 2025-11-27 to reflect broader scope

### ADR-004: Logging Architecture
**Status:** Accepted
**Date:** 2025-11-25
**File:** [004-logging-architecture.md](004-logging-architecture.md)

### ADR-006: Session Management Architecture
**Status:** Accepted
**Date:** 2025-11-26
**File:** [006-session-management-architecture.md](006-session-management-architecture.md)

### ADR-007: MCP SDK Client-Based Integration Testing
**Status:** Accepted
**Date:** 2025-11-26
**File:** [007-mcp-sdk-client-testing.md](007-mcp-sdk-client-testing.md)
**Supersedes:** ADR-005
**Note:** Includes historical context from ADR-005

### ADR-008: MCP Tool Definition Conventions
**Status:** Accepted
**Date:** 2025-11-27
**File:** [008-tool-definition-conventions.md](008-tool-definition-conventions.md)
**Dependencies:** ADR-001, ADR-003, ADR-004

## Historical ADRs

### ADR-005: MCP Inspector for Integration Testing
**Status:** Superseded
**Date:** 2025-11-25
**Superseded By:** ADR-007 (2025-11-26)
**Reason:** Investigation revealed `mcp-inspector` package is a placeholder with no implementation. ADR-007 uses MCP SDK client testing utilities instead, which are officially maintained and fully implemented.
**Historical Content:** Preserved in ADR-007 under "Historical Context" section

## ADR Numbering

ADR numbers are assigned sequentially and are never reused. When an ADR is superseded or removed, its number remains reserved to maintain historical continuity. This explains gaps in the numbering sequence (e.g., missing ADR-005).

## Status Definitions

- **Accepted**: Active decision, currently in use
- **Superseded**: Replaced by a newer ADR
- **Deprecated**: No longer recommended but not yet replaced
- **Rejected**: Considered but not adopted

## Maintenance

When creating a new ADR:
1. Use the next available number (currently: 009)
2. Add entry to this index
3. Update "Supersedes" field if replacing an existing ADR
4. Move superseded ADR to "Historical ADRs" section
