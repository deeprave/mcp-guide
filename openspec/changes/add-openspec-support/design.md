# Design: OpenSpec CLI Integration

## Context
MCP-Guide provides category/collection-based content management through MCP. OpenSpec provides spec-driven development workflows through its CLI. This integration creates a bridge between MCP-Guide's agent interaction model and OpenSpec's CLI, accounting for the client-server filesystem separation inherent in MCP architecture.

## Goals / Non-Goals

### Goals
- Integrate with OpenSpec CLI without reimplementing its logic
- Provide guided command templates for OpenSpec workflows
- Handle client-server filesystem separation transparently
- Conditionally activate via `openspec` feature flag
- Integrate OpenSpec project state into template context
- Support all OpenSpec CLI commands through agent delegation
- Discover and adapt to OpenSpec schema configurations

### Non-Goals
- Reimplement OpenSpec validation or file parsing
- Create MCP tools or resources (delegate to CLI instead)
- Assume direct filesystem access to client
- Modify OpenSpec file formats or conventions
- Replace OpenSpec CLI functionality
- Initiate worktree changes without explicit user request

## Decisions

### Integration Strategy
- **Decision**: Delegate all OpenSpec operations to CLI via agent execution
- **Rationale**: Avoids reimplementation, maintains compatibility, respects client-server boundary
- **Alternatives**: Parsing OpenSpec files directly was rejected due to server-client separation

### Feature Flag
- **Decision**: Use `openspec` feature flag (not `openspec-support`)
- **Rationale**: Simple, clear naming that matches the tool being integrated
- **Alternatives**: More verbose names were considered but add no value

### OpenSpec Detection & Discovery
- **Decision**: Multi-phase discovery via OpenSpecTask:
  1. Request openspec command path (validates CLI availability)
  2. Check for openspec/ directory existence (validates project setup)
  3. Discover available schemas via `openspec schemas --json`
  4. Cache discovery results for session
- **Rationale**: Verifies CLI, project structure, and configuration without assuming filesystem access
- **Alternatives**: Direct filesystem checks rejected due to server-client separation

### Command Execution Protocol
- **Decision**: Smart Agent Pattern - specify outcome, not process
- **Rationale**:
  - Agents understand command execution on their OS
  - Minimal verbosity (2-3 lines per command)
  - OS-agnostic (agent handles platform differences)
  - Clear about required response data
- **Alternatives**: Verbose protocol templates rejected as unnecessarily complex

### Template Type System
- **Decision**: Use `type: agent/instruction` for command templates
- **Rationale**: Distinguishes instructions (agent acts) from information (agent/user receives)
- **Types**:
  - `agent/instruction` - Instruct agent to perform action
  - `agent/information` - Inform agent (not displayed to user)
  - `user/information` - Display to user
  - Combined: `user/information,agent/information`
- **Note**: Parser support deferred until needed (YAGNI)

### File Response Convention
- **Decision**: Standardized response paths:
  - JSON output: `.openspec-<command>.json`
  - Text output: `.openspec-<command>.txt`
  - Agent uses `guide_send_file_content` with appropriate path
- **Rationale**: Predictable, easy to parse, self-documenting
- **Alternatives**: Dynamic paths considered but add complexity

### Persistence Strategy
- **Decision**: Store OpenSpec metadata in existing configuration structures
- **Storage Locations**:
  - Global flag: `openspec` feature flag (truthy or object with schema config)
  - Project config: OpenSpec section in main project config (version, schemas)
  - Workflow file: Current change reference and metadata only
- **Rationale**:
  - No separate config files (less clutter)
  - Portable with project config
  - Change-specific data stays in workflow
  - Global schema cache in feature flag value
- **Paths**: All paths relative to project directory
- **Discovery**: On-demand for templates, cached for schemas/version
- **Alternatives**: Separate `.guide/openspec.yaml` rejected as unnecessary clutter

### Boundary Enforcement
- **Decision**: Never instruct agent to initialize or modify worktree
- **Rationale**: User must explicitly request worktree changes
- **Implementation**: Provide user-facing information on how to prompt agent
- **Example**: "To initialize OpenSpec, ask the agent to run `openspec init`"

## Architecture

```
Client (Agent + OpenSpec CLI)          Server (MCP-Guide)
├── OpenSpec CLI                       ├── Feature Flag: openspec
├── openspec/ directory                ├── OpenSpecTask (TaskManager)
├── File System Access                 │   ├── Discovery Phase
└── Command Execution                  │   │   ├── Verify CLI path
                                       │   │   ├── Check project structure
    ↕ MCP Protocol                     │   │   ├── Discover schemas
    (stdio/http/sse)                   │   │   └── Cache results
                                       │   └── Status Monitoring
    ↕ Agent Instructions               │       └── Track change progress
                                       ├── Command Templates
                                       │   ├── :openspec/init (user info)
                                       │   ├── :openspec/list
                                       │   ├── :openspec/view
                                       │   ├── :openspec/change/*
                                       │   ├── :openspec/archive
                                       │   ├── :openspec/spec/*
                                       │   ├── :openspec/validate
                                       │   ├── :openspec/show
                                       │   ├── :openspec/status
                                       │   ├── :openspec/instructions
                                       │   ├── :openspec/schemas
                                       │   └── :openspec/templates
                                       └── Template Context
                                           └── openspec.*
```

## OpenSpec Discovery Process

### Phase 1: CLI Verification
```
Server → Agent: "Send openspec command path using guide_send_file_content with path .openspec-cli-path.txt"
Agent → Server: Sends result of `which openspec` or equivalent
Server: Caches command path, marks CLI as available/unavailable
```

### Phase 2: Project Detection
```
Server → Agent: "Check if openspec/ directory exists and send listing"
Agent → Server: Sends directory structure or "not found"
Server: Caches project detection status
```

If no openspec/ directory:
- Set dormant state
- Provide user information: "To initialize OpenSpec in this project, ask the agent: 'Please run openspec init'"
- Do NOT instruct agent to initialize

### Phase 3: Schema Discovery
```
Server → Agent: "Run openspec schemas --json and send result to .openspec-schemas.json"
Agent → Server: Sends JSON with available schemas
Server: Caches schema list (e.g., ["spec-driven", "tdd"])
```

### Phase 4: Template Discovery (per schema)
```
Server → Agent: "Run openspec templates --schema spec-driven --json and send to .openspec-templates-spec-driven.json"
Agent → Server: Sends JSON with template list for schema
Server: Caches templates per schema
```

### Phase 5: Change Schema Detection (when change active)
```
Server → Agent: "Run openspec show <change-id> --json and send to .openspec-change-<id>.json"
Agent → Server: Sends change metadata including schema
Server: Caches current change schema
```

## Command Execution Pattern

### Pattern 1: JSON Response Required
```mustache
---
type: agent/instruction
---
Run `openspec list --json` and send the result using {{tool_prefix}}send_file_content with path `.openspec-changes.json`
```

### Pattern 2: Interactive Display Only
```mustache
---
type: agent/instruction
---
Run `openspec view` to display the interactive dashboard.
```

### Pattern 3: Text Response Required
```mustache
---
type: agent/instruction
---
Run `openspec validate {{change_id}}` and send the output using {{tool_prefix}}send_file_content with path `.openspec-validate.txt`
```

### Pattern 4: User Information (No Agent Action)
```mustache
---
type: user/information
---
To initialize OpenSpec in this project, ask the agent:

"Please run `openspec init` to set up the OpenSpec directory structure."

This will create the necessary files and directories for spec-driven development.
```

## OpenSpec Schema Support

### Schema Types
OpenSpec supports multiple workflow schemas:
- **spec-driven**: Traditional specification-first approach
- **tdd**: Test-driven development approach
- Others may be added by OpenSpec

### Schema-Specific Artifacts
Each schema defines different required artifacts:
- `proposal.md` - Change proposal (common to all)
- `tasks.md` - Implementation tasks (common to all)
- `design.md` - Design document (schema-specific)
- `spec.md` - Specification deltas (schema-specific)
- Others as defined by schema

### Artifact Instructions
OpenSpec provides instructions for creating each artifact:
```bash
openspec instructions --change <change-id> --schema <schema> --json <artifact-name>
```

Example:
```bash
openspec instructions --change add-feature --schema spec-driven --json proposal.md
```

Returns JSON with:
- Artifact purpose
- Required sections
- Validation rules
- Examples

### Template Integration
Templates for each schema can be discovered:
```bash
openspec templates --schema spec-driven --json
```

Returns list of available templates that can be used as starting points for new changes.

### Change Schema Detection
When a change is active, determine its schema:
```bash
openspec show <change-id> --json
```

Response includes `schema` field indicating which workflow is in use.

## Workflow Integration

### Current Change Tracking
When workflow is enabled and a change is active:
1. OpenSpecTask monitors current workflow issue
2. If issue matches OpenSpec change pattern, track it
3. Periodically request status: `openspec status <change-id> --json`
4. Update template context with completion percentage

### Status Monitoring
```bash
openspec status <change-id> --json
```

Returns:
- Artifact completion status
- Task completion percentage
- Validation status
- Next recommended actions

### Template Context Integration
```yaml
openspec:
  available: boolean              # CLI detected
  project_detected: boolean       # openspec/ exists
  version: string                 # CLI version (from project config)
  schemas:
    available: []                 # ["spec-driven", "tdd"] (from project config)
    current: string               # Schema for active change (from .guide.yaml)
  changes:
    active: []                    # Active changes (discovered on-demand)
    archived: []                  # Archived changes (discovered on-demand)
    current:
      id: string                  # Current change ID (from .guide.yaml)
      schema: string              # Schema in use (from .guide.yaml)
      status: number              # Completion 0-100 (from .guide.yaml)
```

## Persistence Structure

### Global Feature Flag
The `openspec` feature flag can be:
- **Boolean**: `true` (enabled with defaults)
- **Object**: Configuration data cache (extensible)

```yaml
# Simple enable
openspec: true

# With configuration data
openspec:
  # Schema cache (useful to avoid repeated discovery)
  schemas:
    - name: spec-driven
      artifacts: [proposal, specs, design, tasks]
    - name: tdd
      artifacts: [spec, tests, implementation, docs]
  # Future: Other global OpenSpec configuration as needed
  # e.g., default_schema, experimental_features, etc.
```

**Purpose**: Cache relatively static global OpenSpec data to avoid repeated CLI calls.

**When to Update:**
- Set to `true` on first enable
- Populate with discovered data as needed
- Update when global OpenSpec configuration changes

**Extensibility**: Object structure is open-ended for future OpenSpec configuration needs.

### Project Configuration
OpenSpec data stored in main project config (portable with project):

```yaml
# In project config
openspec:
  version: "1.2.3"              # CLI version (for feature compatibility)
  schemas: [spec-driven, tdd]   # Available schemas
  last_check: 2026-01-15T22:00:00Z
```

**All paths relative to project directory.**

**When to Update:**
- Initial discovery (first time OpenSpec detected in project)
- Manual refresh via `:openspec/refresh`
- When version check fails or changes

**What NOT to Store:**
- CLI path (only needed for availability check)
- Templates (discovered on-demand)
- Change-specific data (goes in workflow file)

### Workflow File (`.guide.yaml`)
Only current change reference and metadata:

```yaml
Phase: implementation
Issue: add-feature
OpenSpec:
  change: add-feature           # Change ID
  schema: spec-driven           # Schema in use (optional)
  status: 45                    # Completion percentage (optional)
```

**When to Update:**
- When issue is OpenSpec change
- After running `:openspec/status`
- On workflow phase transitions
- When change is archived (remove OpenSpec section)

### Discovery Flow

```
1. Check openspec feature flag
   FALSE/missing → Feature disabled, stop
   TRUE/object → Continue

2. Check project config for openspec.version
   EXISTS → Use cached data, skip to step 5
   MISSING → Continue to step 3

3. Request CLI version from agent
   → Save to project config

4. Discover available schemas
   → Save to project config
   → Optionally cache in feature flag

5. Check if current issue is OpenSpec change
   YES → Load/update .guide.yaml OpenSpec section
   NO → Skip OpenSpec-specific tracking

6. Provide template context from cached data
```

### Template Discovery
Templates are **not cached** - discovered on-demand:
- When creating new change: `openspec templates --schema <schema>`
- When requesting artifact instructions: `openspec instructions --change <id> --schema <schema> <artifact>`

**Rationale**: Templates may change, on-demand discovery ensures current data

### CLI Path Handling
CLI path is **not stored** - only used for:
- Availability check (can we run `openspec`?)
- Version discovery (`openspec --version`)

Agent handles path resolution (via PATH or explicit location).

### Benefits
- **No clutter**: No separate config files
- **Portable**: Project config travels with project
- **Minimal**: Only cache what's needed
- **Flexible**: Schema config in global flag or project
- **Clean workflow**: Only change-specific data in `.guide.yaml`

### Refresh Strategy
- **Automatic**: When version check fails
- **Manual**: `:openspec/refresh` command
- **Selective**: Version/schemas only (templates always fresh)

## Implementation Strategy

### Phase 1: Detection & Discovery
1. Add `openspec` feature flag
2. Implement OpenSpecTask:
   - CLI path verification
   - Project structure detection
   - Schema discovery
   - Result caching
3. Add dormant state handling (no openspec/ directory)
4. Create user information template for initialization

### Phase 2: Basic Commands
1. Create command templates:
   - `:openspec/list` - List changes/specs
   - `:openspec/show` - Show change/spec details
   - `:openspec/validate` - Validate change/spec
   - `:openspec/schemas` - List available schemas
   - `:openspec/templates` - List templates for schema
2. Implement JSON response parsing
3. Add basic template context

### Phase 3: Change Management
1. Add change workflow commands:
   - `:openspec/change/new` - Create new change
   - `:openspec/change/edit` - Edit change files
   - `:openspec/change/delete` - Delete change
2. Add archive command:
   - `:openspec/archive` - Archive completed change
3. Implement schema detection for changes

### Phase 4: Advanced Features
1. Add artifact instruction commands:
   - `:openspec/instructions` - Get artifact creation instructions
2. Add status monitoring:
   - `:openspec/status` - Show change completion status
3. Integrate with workflow tracking
4. Full template context with schema support

### Phase 5: Workflow Integration
1. Integrate existing `.kiro/prompts`:
   - Convert `openspec-proposal.md` to `:openspec/proposal`
   - Convert `openspec-apply.md` to `:openspec/apply`
   - Convert `openspec-archive.md` to `:openspec/archive`
2. Add schema-aware workflow guidance
3. Progress indicators for multi-step operations

## Command Mapping

### Core Commands
- `:openspec/init` → User info: "Ask agent to run `openspec init`"
- `:openspec/update` → `openspec update`
- `:openspec/list` → `openspec list [--specs] --json`
- `:openspec/view` → `openspec view` (interactive, display only)
- `:openspec/schemas` → `openspec schemas --json`
- `:openspec/templates` → `openspec templates --schema <schema> --json`

### Change Management
- `:openspec/change/new` → `openspec change new`
- `:openspec/change/edit` → `openspec change edit`
- `:openspec/change/delete` → `openspec change delete`
- `:openspec/archive` → `openspec archive <change>`

### Spec Management
- `:openspec/spec/show` → `openspec spec show --json`
- `:openspec/spec/list` → `openspec spec list --json`
- `:openspec/spec/compare` → `openspec spec compare`

### Validation & Display
- `:openspec/validate` → `openspec validate <item> [--strict]`
- `:openspec/show` → `openspec show <item> --json`

### Advanced Features
- `:openspec/status` → `openspec status <change> --json`
- `:openspec/instructions` → `openspec instructions --change <id> --schema <schema> --json <artifact>`

### Workflow (from .kiro/prompts)
- `:openspec/proposal` → Guided change proposal creation (schema-aware)
- `:openspec/apply` → Guided change application
- `:openspec/archive` → Guided change archival

## Open Questions

### Schema Evolution
- **Question**: How to handle new schemas added by OpenSpec?
- **Recommendation**: Re-run schema discovery periodically or on-demand

### Artifact Instruction Caching
- **Question**: Should we cache artifact instructions or fetch on-demand?
- **Recommendation**: Cache per-session, refresh on schema change

### Status Polling Frequency
- **Question**: How often to poll change status when workflow active?
- **Recommendation**: On workflow phase transitions and user request

### Template Organization
- **Question**: How to organize schema-specific templates?
- **Recommendation**: `templates/_commands/openspec/<command>.mustache`

## Risks / Trade-offs

### Risk: CLI Availability
- **Impact**: Feature unusable if OpenSpec CLI not installed
- **Mitigation**: Clear detection and user-facing installation guidance

### Risk: Schema Changes
- **Impact**: New schemas may require template updates
- **Mitigation**: Schema discovery makes system adaptable

### Risk: Performance
- **Impact**: CLI execution and JSON parsing add latency
- **Mitigation**: Cache discovery results, async execution

### Trade-off: User Boundary Enforcement
- **Decision**: Never auto-initialize or modify worktree
- **Rationale**: Respects user control, prevents unexpected changes
- **Cost**: Requires user to explicitly request initialization

## Migration Plan

### Activation
1. Deploy with `openspec` feature flag disabled by default
2. Document OpenSpec CLI installation requirements
3. Enable flag for projects with OpenSpec CLI installed
4. Provide detection command to verify setup

### Rollback
1. Disable `openspec` feature flag
2. No data migration required (no server-side state)
3. Existing MCP-Guide functionality unaffected
