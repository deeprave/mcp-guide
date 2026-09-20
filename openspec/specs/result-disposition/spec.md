# result-disposition Specification

## Purpose
Defines the disposition vocabulary a Guide `Result` carries to tell an agent how to treat the response, and the tone rules that let a well-taught disposition replace a repeated prose instruction.

## Requirements

### Requirement: Disposition vocabulary
The system SHALL define exactly these content dispositions, each identifying both the audience and the required agent behavior:
- `user/information`: content for display to the user; the agent MAY format it or pass it through verbatim per the content's own markdown.
- `agent/information`: content useful to the agent but not necessarily to the user; the agent SHALL NOT display it unprompted and MAY surface it if the user asks or it is otherwise relevant.
- `agent/instruction`: a one-off action the agent SHALL take now, tied to the enclosed information.
- `agent/error`: a failure the agent caused and SHALL be able to correct itself (for example, mutually exclusive arguments, a missing required value); the response SHALL describe what was wrong and what would fix it.
- `user/error`: a failure caused by the user's request or current state that the agent SHALL NOT attempt to interpret or correct on the user's behalf; the agent SHALL report the failure to the user and stop.
- `unknown/error`: a failure not yet classified as agent- or user-caused; the agent SHALL treat it as it would `user/error` (report and stop, do not guess a fix) until the failure is classified.

A `Result`'s disposition SHALL NOT be fabricated when no call site has set one; it MAY remain unset, per the `tool-infrastructure` capability's "Result disposition is never fabricated" requirement.

#### Scenario: Agent-correctable error names the fix
- **WHEN** a Guide response has disposition `agent/error`
- **THEN** the response identifies what was wrong and what value or call would succeed instead

#### Scenario: User-correctable error stops rather than corrects
- **WHEN** a Guide response has disposition `user/error`
- **THEN** the response does not instruct the agent to infer, guess, or silently substitute a corrected value on the user's behalf

### Requirement: Disposition may stand in place of a prose instruction
A `Result` whose meaning is fully carried by its disposition SHALL NOT also carry a prose `instruction` that only restates that disposition's standing meaning. A prose `instruction` SHALL be present only when it adds information the disposition alone does not convey (for example, a specific corrective value, a specific next tool call, or context specific to that response).

#### Scenario: Disposition alone is sufficient
- **WHEN** a `Result` sets disposition `agent/information` and the enclosed value needs no further handling guidance
- **THEN** the result carries no `instruction` field

#### Scenario: Disposition plus response-specific detail
- **WHEN** a `Result` sets disposition `agent/error` because two arguments were mutually exclusive
- **THEN** the result's `instruction`, if present, names the specific arguments in conflict rather than repeating generic error-handling guidance

### Requirement: Agent learns the disposition vocabulary once per session
The system SHALL make the disposition vocabulary and its required agent behavior available to the agent through a single reference the agent encounters once (or on first relevant use) rather than repeating the full explanation on every response that carries a disposition.

#### Scenario: First response of a session carrying a disposition
- **WHEN** an agent's session has not yet received the disposition vocabulary reference
- **AND** a Guide response sets a disposition
- **THEN** the agent has access to the vocabulary reference by the time it needs to act on that disposition

#### Scenario: Subsequent responses do not repeat the vocabulary
- **WHEN** an agent's session has already received the disposition vocabulary reference
- **THEN** later responses carrying a disposition do not re-explain what that disposition means

### Requirement: Cooperative tone for retained prose instructions
Any prose `instruction` or `additional_agent_instructions` text that remains after a disposition is set SHALL state, where applicable, why the action matters and what result it produces, rather than an unexplained imperative alone.

#### Scenario: Retained instruction gives rationale
- **WHEN** a `Result` carries a prose instruction alongside its disposition
- **THEN** the instruction explains the reason for the action or its outcome, not only the action itself
