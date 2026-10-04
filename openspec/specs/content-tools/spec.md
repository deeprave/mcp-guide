## Purpose

Define requirements for content-oriented tools and related guidance exposed through the system.
## Requirements
### Requirement: Research Efficient Document Import Approaches

The project SHALL evaluate document import approaches based on measured user impact, operational reliability, and portability across the target client matrix before introducing new import-specific commands or tools.

The project SHALL treat agent-specific background execution as one candidate approach among several, not as the default outcome of this exploration.

The project SHALL distinguish between:

- clients that can complete delegated ingestion end-to-end, including `send_file_content`
- clients that can only offload preparation or background work
- and clients that require the universal inline fallback path

#### Scenario: Exploration evaluates multiple approach families
- **WHEN** the exploration is conducted
- **THEN** it compares multiple candidate approaches, including agent-agnostic and agent-specific options
- **AND** it does not assume that delegating work to a background agent is sufficient to solve the core import bottleneck

#### Scenario: Exploration covers the target client matrix
- **WHEN** the exploration evaluates portability
- **THEN** it considers the supported client and agent environments called out by the proposal
- **AND** it identifies the minimum broadly portable baseline and any product-specific optimisations separately

#### Scenario: Exploration defines viability before implementation
- **WHEN** the exploration recommends a follow-up implementation
- **THEN** it includes explicit viability criteria covering foreground wait time, total completion time, reliability, and user-visible feedback
- **AND** it defines how the recommendation remains agent-agnostic or what fallback exists for platform-specific optimisations

#### Scenario: Exploration treats prepared artifacts as the default model
- **WHEN** the exploration defines ingestion semantics
- **THEN** it treats prepared knowledge artifacts as the default outcome
- **AND** it treats raw preservation as an explicit alternate mode rather than the default path

#### Scenario: Exploration separates source tracks and execution modes
- **WHEN** the exploration describes the ingestion design space
- **THEN** it separates local-file acquisition/preparation from URL acquisition/preparation
- **AND** it separates delegated execution from inline fallback execution

#### Scenario: Exploration standardizes fallback wording
- **WHEN** optimized separate execution is unavailable or cannot actually be used
- **THEN** the exploration defines standardized fallback explanation wording for inline execution
- **AND** it treats that wording as part of the universal fallback contract rather than a client-specific detail

#### Scenario: Exploration defines a strict delegated-ingestion bar
- **WHEN** a client is considered for an optimized delegated path
- **THEN** the client must be able to complete ingestion end-to-end, including `send_file_content`
- **AND** cloud or background preparation alone does not qualify the client for that path

### Requirement: Stateless export delivery guidance

Export guidance SHALL instruct the client to write the complete returned payload
verbatim to the supplied, configured destination, respecting create-only or
overwrite instructions. Delivery frontmatter SHALL remain file data during that
write; its `type` and `instruction` retain the content's semantics for later use.
Guide SHALL NOT direct later content requests to an exported or indexed copy.

#### Scenario: Export delivers file data
- **WHEN** `export_content` returns a payload and write instruction
- **THEN** the client is instructed to preserve the entire payload verbatim
- **AND** embedded frontmatter is not executed as an export instruction
- **AND** create-only or overwrite behaviour applies to the supplied destination

#### Scenario: Later content retrieval remains ordinary
- **WHEN** a client requests the same content after exporting it
- **THEN** Guide returns its rendered content without a prior-file reference

### Requirement: Document Update Command Remains Inline by Default

The `:document/update` command SHALL remain an inline mutation command unless a concrete handoff-oriented benefit is established during implementation.

#### Scenario: Update remains inline
- **WHEN** `:document/update` is rendered
- **THEN** the template continues to instruct the agent to call the update tool inline
- **AND** it does not require a handoff branch merely for consistency with ingestion or export commands
