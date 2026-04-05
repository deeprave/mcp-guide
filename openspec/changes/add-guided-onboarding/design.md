# Design: Add Guided Onboarding

## Purpose

This change introduces a user-facing guided setup experience for project configuration.

The key design principle is:

```text
make configuration discoverable through conversation
without replacing the existing configuration model
```

## Core Model

The system already has configuration primitives:

- profiles
- categories
- collections
- feature flags
- project flags
- workflow settings
- policy selections

Guided onboarding should orchestrate those primitives, not replace them.

So the architecture is:

```text
guided onboarding
  = interaction layer

existing config mechanisms
  = storage and application layer
```

## Onboarding Responsibilities

The onboarding flow should:

1. inspect the project when possible
2. identify relevant setup dimensions
3. explain choices in plain language
4. ask the user for preferences
5. apply the resulting configuration

Relevant dimensions may include:

- language/framework profiles
- testing and type-checking posture
- workflow mode
- policy selections
- content or rendering preferences
- OpenSpec support
- update behavior

## Project Introspection

Project introspection should be pragmatic rather than exhaustive.

Examples of useful signals:

- Python, JavaScript, Rust, Java, etc.
- framework conventions like Django, React, FastAPI, Spring
- package manager or toolchain indicators
- testing configuration
- repo/workflow layout

If the current project is missing or ambiguous, the onboarding flow should ask the user directly.

## User-Facing Choice Presentation

The flow should present choices in terms the user can reason about easily.

It should avoid forcing users to think in internal flag names unless necessary.

Examples:

```text
Do you want:
- a simple workflow
- or full phased workflow support?

Do you want:
- AI to avoid commits and PR creation
- or to allow more automation?
```

This is preferable to asking users to choose raw configuration keys up front.

## Application Model

Once the user chooses preferences, onboarding should update the project using existing tools and configuration pathways.

This may include:

- applying profiles
- adding or updating categories and collections
- setting project flags
- setting feature flags
- applying selected policies

## Relationship to Policy Selection

Policy selection is one major onboarding domain, but not the entire onboarding experience.

This change assumes the policy-selection model exists and can be invoked as one part of onboarding.

## Rationale

This design is preferable to expanding profiles alone because profiles are a storage mechanism, not a discovery mechanism.

Guided onboarding improves:

- discoverability
- usability
- user control
- and long-term reconfiguration

without forcing a new underlying config system.
