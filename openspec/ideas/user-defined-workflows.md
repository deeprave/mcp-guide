# Idea: User-Defined Workflows

**Status:** Incubating
**Date:** 2025-12-08
**Category:** Workflow Management

## Current State

mcp-server-guide currently uses a rigid 4-phase workflow:
- **Discussion** - Requirements gathering, analysis, architectural decisions
- **Planning** - Implementation planning, task breakdown
- **Implementation** - Code execution following the plan
- **Check** - Testing, code quality verification, self-review

### Current Mechanism

- Instruction files (or built-in instructions) introduce each phase
- Agent manages `.consent` and `.issue` files for phase transitions
- Enforcement pre-use tool attempted to prevent unauthorized file changes
  - Recently stopped working for unknown reasons
  - No longer deemed necessary due to excellent agent instruction adherence
- Phase transitions are explicit and controlled

### Limitations

- **Rigid structure** - All projects must follow the same 4-phase flow
- **Inflexible** - Cannot adapt to different project types or team preferences
- **One-size-fits-all** - Doesn't accommodate simpler or more complex workflows

## Proposed Approach

Replace the rigid 4-phase system with **user-defined workflows** that allow projects to define their own phase structure and rules.

### Core Concept

Workflows are defined through **category-based instructions** where users create their own workflow phases that suit their environment.

**Examples of possible workflows:**
- Simple: `plan → implement → review`
- Standard: `discuss → plan → implement → check → review`
- Complex: `research → design → prototype → implement → test → review → deploy`

### Key Principles

1. **No tool enforcement** - Agent self-regulates based on instructions
2. **Category-driven** - Workflow definitions stored in a designated category
3. **File-based state** - `.guide` file tracks current phase
4. **Instruction-based** - Each phase has detailed instructions for agent behavior
5. **User-controlled transitions** - Explicit phase changes (with optional auto-transitions)

## Design

### Feature Flag

A new configuration setting determines which category contains workflow definitions:

```yaml
feature-flags:
  workflow-category: "workflow"  # Default category name
```

This category is defined in the project configuration like any other category.

### Workflow Category Structure

The workflow category contains:

1. **General workflow instructions** (default pattern)
   - How phases are managed
   - State file location and format
   - Transition rules
   - Default phase behavior

2. **Phase-specific instructions** (per-phase files)
   - Detailed rules for what is/isn't allowed in each phase
   - Entry/exit criteria
   - Transition conditions
   - Agent behavior guidelines

### State Management

**`.guide` file** at project root:
- Contains current phase name
- Absence of file = default phase is active
- Agent-managed (created/updated during transitions)

**Example `.guide` file:**
```
implementation
```

### Phase Instructions

Each phase has an instruction document that defines:

- **Purpose** - What this phase is for
- **Allowed actions** - What the agent can do
- **Restricted actions** - What the agent cannot do
- **Entry criteria** - When to enter this phase
- **Exit criteria** - When this phase is complete
- **Transition rules** - How to move to next phase

### Default Workflow Definition

Initial implementation provides a 5-phase workflow:

1. **discussion** - Requirements gathering, analysis, architectural decisions
2. **planning** - Implementation planning, task breakdown, specifications
3. **execution** - Code implementation following the plan
4. **checks** - Testing, code quality verification, self-review
5. **review-feedback** - Incorporate review feedback, iterate

### Transition Control

**Explicit transitions (default):**
- User instructs agent to transition: "move to planning phase"
- Agent updates `.guide` file
- Agent presents new phase instructions

**Automatic transitions (optional):**
- Instructions can specify auto-transition conditions
- Example: "After all tests pass in checks phase, automatically transition to review-feedback"
- Agent still requires user confirmation before auto-transitioning

## Benefits

### Flexibility
- Projects can define workflows that match their needs
- Simple projects can use simple workflows
- Complex projects can add more phases

### Adaptability
- Different project types can have different workflows
- Teams can customize to their processes
- Workflows can evolve over time

### Simplicity
- No enforcement tools needed
- Agent self-regulates through instructions
- Clear state management via `.guide` file

### Portability
- Workflows are project-specific configuration
- Easy to share workflow definitions between projects
- Different AI agents can follow the same instructions

## Implementation Considerations

### Phase 1: Core Infrastructure
- Feature flag for workflow category
- `.guide` file state management
- Phase instruction loading mechanism
- Transition command handling

### Phase 2: Default Workflow
- Create default 5-phase workflow instructions
- General workflow management instructions
- Phase-specific instruction documents

### Phase 3: Customization
- Documentation for creating custom workflows
- Examples of different workflow types
- Validation of workflow definitions

### Phase 4: Migration
- Migrate existing 4-phase system to new approach
- Backward compatibility considerations
- Deprecation path for old system

## Open Questions

1. **Validation** - How to validate workflow definitions?
2. **Nested phases** - Should phases support sub-phases?
3. **Parallel phases** - Can multiple phases be active simultaneously?
4. **Phase history** - Should we track phase transition history?
5. **Rollback** - Can we rollback to a previous phase?
6. **Conditional transitions** - How complex should transition rules be?
7. **Multi-project workflows** - How do workflows interact across projects?

## Examples

### Simple Workflow

```yaml
# workflow/general.md
Workflow: Simple 3-Phase

Phases:
- plan: Create implementation plan
- implement: Execute the plan
- review: Verify and review changes

State file: .guide
Default phase: plan
```

### Complex Workflow

```yaml
# workflow/general.md
Workflow: Enterprise 7-Phase

Phases:
- research: Gather requirements and research solutions
- design: Create architectural design
- prototype: Build proof of concept
- implement: Full implementation
- test: Comprehensive testing
- review: Code review and feedback
- deploy: Deployment preparation

State file: .guide
Default phase: research
Auto-transitions: test → review (when all tests pass)
```

## Related

- Current 4-phase workflow system
- Category-based instruction system
- Agent instruction adherence
- Project configuration management

## Next Steps

When this moves to proposal:
- Define exact instruction format
- Specify state file format
- Design transition command syntax
- Create validation rules
- Plan migration strategy
- Discuss open questions
