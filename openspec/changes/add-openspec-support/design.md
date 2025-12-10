# Design: OpenSpec MCP Integration

## Context
MCP-Guide currently provides category/collection-based content management through MCP. OpenSpec provides spec-driven development workflows through YAML specifications and change management. This integration makes OpenSpec workflows available to any MCP-compatible AI assistant.

## Goals / Non-Goals

### Goals
- Expose OpenSpec workflows through MCP protocol
- Maintain compatibility with existing MCP-Guide architecture
- Provide conditional activation via feature flags
- Integrate OpenSpec data into template context hierarchy
- Support read-only OpenSpec operations initially

### Non-Goals
- Modify OpenSpec file formats or workflows
- Replace existing MCP-Guide functionality
- Implement OpenSpec validation logic (delegate to openspec CLI)
- Support write operations in initial implementation

## Decisions

### Feature Flag Integration
- **Decision**: Use feature flag "openspec-support" to conditionally enable functionality
- **Rationale**: Allows gradual rollout and dependency on feature-flags implementation
- **Alternatives**: Always-on detection was considered but creates hard dependency

### OpenSpec Detection Strategy
- **Decision**: Detect OpenSpec projects by checking for `openspec/` directory and `openspec/project.md`
- **Rationale**: Follows OpenSpec conventions and provides reliable detection
- **Alternatives**: Configuration-based detection was considered but adds complexity

### MCP Integration Architecture
- **Decision**: Extend existing MCP server with OpenSpec-specific tools and resources
- **Rationale**: Leverages existing infrastructure and maintains consistency
- **Alternatives**: Separate MCP server was considered but increases deployment complexity

### Template Context Integration
- **Decision**: Add OpenSpec data at project level in template context hierarchy
- **Rationale**: Aligns with existing hierarchy: file > category > collection > project > agent > system
- **Alternatives**: Separate OpenSpec context was considered but breaks consistency

### Resource vs Tool Prioritization
- **Decision**: Implement tools first, resources second, prompts third
- **Rationale**: Tools provide immediate workflow value, resources are queryable but less actionable
- **Alternatives**: Resources-first approach was considered but provides less user value

## Architecture

```
MCP Server (existing)
├── Category/Collection Tools (existing)
├── Template Context (existing)
└── OpenSpec Integration (new)
    ├── Detection Layer
    │   ├── Feature Flag Check
    │   ├── Directory Validation
    │   └── Project Metadata Parser
    ├── MCP Tools
    │   ├── list-specs
    │   ├── list-changes
    │   ├── get-change
    │   ├── validate-change
    │   ├── show-delta
    │   ├── compare-specs
    │   └── get-project-context
    ├── MCP Resources
    │   ├── openspec://project
    │   ├── openspec://specs/{domain}
    │   ├── openspec://changes/{change-id}
    │   └── openspec://agents
    └── Template Context Extension
        ├── OpenSpec Project Data
        ├── Active Changes List
        └── Spec Domains List
```

## Implementation Strategy

### Phase 1: Core Detection & Tools
1. Implement feature flag checking
2. Add OpenSpec directory detection
3. Implement core tools: list-specs, list-changes, get-change
4. Basic error handling

### Phase 2: Advanced Tools & Context
1. Add validation and comparison tools
2. Integrate with template context hierarchy
3. Enhanced error handling and edge cases

### Phase 3: Resources & Prompts
1. Implement MCP resources for queryable state
2. Add guided workflow prompts
3. Performance optimization

## Open Questions

### Dependency Resolution
- **Question**: How should we handle the dependency on feature-flags implementation?
- **Resolution Needed**: Define interface contract for feature flag checking
- **Timeline**: Must be resolved before implementation begins

### OpenSpec CLI Integration
- **Question**: Should we shell out to `openspec` CLI or implement parsing directly?
- **Options**:
  - Shell execution: Simple but requires CLI installation
  - Direct parsing: More complex but self-contained
- **Resolution Needed**: Performance and deployment requirements analysis

### Error Handling Strategy
- **Question**: How should we handle malformed or incomplete OpenSpec projects?
- **Options**:
  - Fail silently and disable OpenSpec features
  - Provide detailed error messages through MCP
  - Partial functionality with warnings
- **Resolution Needed**: User experience requirements

### Template Context Data Structure
- **Question**: What OpenSpec data should be available in template context?
- **Candidates**:
  - Project metadata (name, description, tech stack)
  - Active changes list with status
  - Spec domains and current requirements
  - Agent configuration from AGENTS.md
- **Resolution Needed**: Template use case analysis

### Security Considerations
- **Question**: What file system access restrictions should apply?
- **Constraints**:
  - Read-only access to openspec/ directory
  - No execution of arbitrary commands
  - Relative path restrictions for containerized environments
- **Resolution Needed**: Security review and sandboxing requirements

## Risks / Trade-offs

### Risk: Feature Flag Dependency
- **Impact**: Cannot implement until feature-flags is available
- **Mitigation**: Design interface contract now, implement when dependency ready

### Risk: OpenSpec CLI Dependency
- **Impact**: Requires openspec CLI installation in deployment environment
- **Mitigation**: Document installation requirements, consider bundling

### Risk: Performance Impact
- **Impact**: File system scanning on every OpenSpec operation
- **Mitigation**: Implement caching strategy, lazy loading

### Trade-off: Functionality vs Complexity
- **Decision**: Start with read-only operations
- **Rationale**: Reduces complexity and security concerns
- **Future**: Add write operations in subsequent iterations

## Migration Plan

### Activation
1. Deploy with feature flag disabled by default
2. Enable for test projects to validate functionality
3. Gradual rollout to production projects
4. Monitor performance and error rates

### Rollback
1. Disable feature flag to deactivate functionality
2. No data migration required (read-only operations)
3. Existing MCP-Guide functionality unaffected
