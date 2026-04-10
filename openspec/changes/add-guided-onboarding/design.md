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

## Onboarding State

A project flag `onboarded` tracks whether onboarding has been completed for a project.

- **Unset or `false`**: onboarding has not been completed
- **`true`**: onboarding has been completed at least once

The flag does not gate the `:onboard` command — users can invoke it at any time to reconfigure.

The flag is set to `true` atomically as part of the final configuration update when the user confirms onboarding choices. It is not set earlier.

## Startup Notification

When a project is loaded and `onboarded` is not `true`, the system surfaces a notification to the user.

This reuses the startup instruction pathway, conditioned on the `onboarded` flag:

```text
on project load:
  if onboarded != true:
    render _system/_onboard_prompt (user/information)
    surface to user
```

The notification is `user/information` — the agent displays it, does not act on it. It repeats on every session load until onboarding is completed.

The template lives in the `_system` category as `_onboard_prompt.mustache`. Initial content is placeholder text explaining that onboarding is available and how to invoke it:

> mcp-guide can be configured to match your project preferences. Run `{{@}}guide :onboard` (or use the `guide://_onboard` URI) to get started. This takes a few minutes and covers language, workflow, testing, git, and code style preferences.

## Atomic Configuration Application

Onboarding choices are not applied piecemeal. Instead:

1. The agent works through the onboarding flow, collecting user preferences in its working context
2. At the final step, the agent presents a summary of all pending configuration changes
3. The user confirms
4. All changes are applied in one update through existing mechanisms (profiles, flags, policy selections, etc.)
5. `onboarded` is set to `true` as part of that same update

This avoids leaving the project in a partially-configured state if the user exits onboarding early.

## The `:onboard` Command

The `:onboard` command template drives the onboarding flow. It contains the agent instructions for:

- inspecting the project
- identifying relevant configuration dimensions
- presenting choices to the user
- collecting preferences
- summarising and confirming

The startup notification is intentionally minimal — it explains onboarding exists and how to start it. The substantive agent guidance lives in the command template.

## Rationale

This design is preferable to expanding profiles alone because profiles are a storage mechanism, not a discovery mechanism.

Guided onboarding improves:

- discoverability
- usability
- user control
- and long-term reconfiguration

without forcing a new underlying config system.
