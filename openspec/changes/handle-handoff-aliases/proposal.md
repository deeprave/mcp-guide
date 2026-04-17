# Change: handle-handoff-aliases

## Why

The current handoff command requires the caller to explicitly specify exactly
one of read or write mode. That is precise, but it is less ergonomic than it
needs to be for the two most common intent-specific entry points:

- save context to a file
- restore context from a file

The desired behavior is to support intent-revealing aliases that still require
an explicit path while implicitly selecting the correct handoff mode.

Specifically:

- `:save-context` and `guide://_save-context/...` should behave like handoff
  write mode
- `:restore-context` and `guide://_restore-context/...` should behave like
  handoff read mode

This should reduce friction for common usage without weakening validation. A
path is still required, and the underlying handoff implementation should still
enforce its normal path handling and execution behavior.

## What Changes

- Add `save-context` as a handoff alias that implies write mode
- Add `restore-context` as a handoff alias that implies read mode
- Preserve the requirement that a path must still be provided for both aliases
- Preserve the existing explicit handoff command for callers that want to pass
  `--read` / `--write` or the equivalent URI query parameters directly
- Keep validation strict so ambiguous calls still fail clearly

## Suggested Approach

This looks feasible and should be a relatively small change.

The preferred implementation is:

- resolve alias intent before normal handoff argument validation
- map:
  - `save-context` -> implied write
  - `restore-context` -> implied read
- reject any conflicting explicit mode flags if they disagree with the alias
- continue to require a target path even when the mode is implied by alias

The URI forms should follow the same behavior:

- `guide://_save-context/<path>` acts as write mode
- `guide://_restore-context/<path>` acts as read mode

If desired, the implementation may also support explicit query forms on the
alias URIs, but the alias meaning should remain canonical and conflict checks
should stay strict.

## Impact

- Affected specs:
  - likely command or handoff command behavior specs
- Likely affected implementation:
  - handoff command parsing
  - guide URI command routing for `_handoff`, `_save-context`, and
    `_restore-context`
  - validation and error messaging for handoff mode selection
- No broader workflow or document update behavior should be affected
