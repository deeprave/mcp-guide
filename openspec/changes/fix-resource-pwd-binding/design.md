# Design

## Context

Native resources check for a URI `session_id` before opening the shared request context. That bypasses the existing eligible-PWD bind used by tools and prompts.

## Goals / Non-Goals

**Goals:**

- Give unbound native resource reads the same PWD bootstrap and continuation behaviour as tools and prompts.

**Non-Goals:**

- Change PWD eligibility, non-stdio behaviour, explicit `set_project`, or resource routing.
- Add new session identifiers or persistence.

## Decisions

- Enter the existing request-context scope before checking a missing resource session ID, so resource reads use the same session resolution and eligible PWD-binding path as tools and prompts. A valid stateful legacy connection continues to use its retained session; a modern request without an explicit session ID or eligible PWD bind remains unbound.

## Risks / Trade-offs

- The resource must not infer a project when the shared PWD-bootstrap conditions are ineligible; it must retain the existing unbound guidance.
