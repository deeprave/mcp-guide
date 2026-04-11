# Change: Add Guided Onboarding

## Why

The current system exposes a lot of capability through:

- categories
- collections
- profiles
- feature flags
- project flags
- workflow options
- optional policy documents

Those mechanisms are powerful, but not especially approachable for a new user.

A user installing the MCP may not know:

- what capabilities exist
- what options are available
- how to configure those options
- how document collections can be composed into useful directed prompts

Profiles help, but they still assume the user knows what profile names mean and how to combine them. That is not a friendly onboarding experience.

This change adds a guided onboarding experience that uses the AI agent to:

- inspect the project when possible
- infer likely relevant configuration topics
- explain meaningful options
- ask the user for preferences
- and update project configuration accordingly

Policy selection is one important part of this flow, but not the only one.

## What Changes

### 1. Add guided onboarding support

Add an onboarding mechanism that guides the user through initial project setup and later reconfiguration.

The onboarding flow should help the user configure:

- profiles
- categories and collections where relevant
- feature flags
- project flags
- workflow preferences
- policy selections

### 2. Use project introspection where possible

The onboarding flow should inspect the current project to identify likely relevant choices, for example:

- language or framework
- toolchain and package manager
- testing and type-checking setup
- workflow and documentation expectations

If there is no project yet, or the environment is ambiguous, the agent should ask the user instead.

### 3. Present choices in user-facing terms

The onboarding flow should present configuration in terms of user goals and preferences rather than internal flag or profile names wherever possible.

Examples:

- simple workflow vs full phased workflow
- strict review posture vs lighter autonomy
- test-driven workflow vs minimal testing guidance
- explicit commit/PR restrictions vs more permissive git automation

### 4. Apply onboarding selections through existing configuration mechanisms

The onboarding flow should not create a separate configuration system.

Instead it should apply selections using existing mechanisms, including:

- profiles
- categories
- collections
- feature flags
- project flags
- policy selections defined by `add-policy-selection`

### 5. Support both initial setup and later modification

The same guided approach should be usable for:

- first-time onboarding
- updating an existing project's setup later

## Scope

In scope:

- guided onboarding interaction and documentation/instruction support
- project introspection for relevant setup choices
- user-friendly presentation of configuration choices
- applying onboarding choices using existing project configuration mechanisms

Out of scope:

- replacing profiles/categories/collections/flags with a new configuration model
- defining the full policy corpus itself (handled by `add-policy-selection`)
- implementing every possible project detection heuristic in one pass

## Success Criteria

- the system provides a guided onboarding experience for project setup
- onboarding can inspect the project or ask the user when inspection is insufficient
- onboarding presents configuration choices in user-facing terms
- onboarding can apply selected preferences using existing configuration mechanisms
- onboarding supports both first-time setup and later reconfiguration

## Impact

- Affected specs:
  - `project-config`
  - `help-template-system`
  - `workflow-flags`
- Related change:
  - `add-policy-selection`
