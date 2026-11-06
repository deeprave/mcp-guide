# result Specification

## Purpose
Define the cross-surface Guide `Result` envelope and its optional disposition.

## Requirements

### Requirement: Result outcome envelope

A `Result` SHALL represent either success with an optional value or failure
with an error and error type. It MAY carry message, response-specific
instruction, arguments, cache policy, structured error data, additional agent
instructions, and disposition. Serialisation SHALL omit optional fields that
are unset.

#### Scenario: Successful result

- **WHEN** Guide produces a successful result
- **THEN** the envelope identifies success and includes its value when present

#### Scenario: Failed result

- **WHEN** Guide produces a failed result
- **THEN** the envelope identifies failure and includes its error and error type

### Requirement: Result disposition vocabulary

The system SHALL define these optional content dispositions: `user/information`,
`agent/information`, `agent/instruction`, `agent/error`, `user/error`, and
`unknown/error`.

#### Scenario: Disposition vocabulary is available
- **WHEN** a Result carries a disposition
- **THEN** it uses one of Guide's defined dispositions

### Requirement: Disposition semantics

Each disposition SHALL carry these semantics:

- `user/information`: content intended for user display.
- `agent/information`: content intended for the agent without unsolicited user display.
- `agent/instruction`: a response-specific agent action.
- `agent/error`: a correctable request or call error.
- `user/error` and `unknown/error`: failures that require user visibility rather
  than an inferred correction.

#### Scenario: Agent informational response
- **WHEN** a Guide response has disposition `agent/information`
- **THEN** the agent does not display it unprompted

### Requirement: Unset result disposition

A `Result` disposition SHALL NOT be fabricated when no call site has set one;
it MAY remain unset, per the tool-infrastructure result-disposition requirement.

#### Scenario: Call site leaves a disposition unset
- **WHEN** no call site sets a Result disposition
- **THEN** Guide leaves the disposition unset

### Requirement: Disposition and response-specific instruction
A `Result` whose meaning is fully carried by its disposition SHALL NOT also carry a prose `instruction` that only restates that disposition's standing meaning. A prose `instruction` SHALL be present only when it adds information the disposition alone does not convey (for example, a specific corrective value, a specific next tool call, or context specific to that response).

#### Scenario: Disposition alone is sufficient
- **WHEN** a `Result` sets disposition `agent/information` and the enclosed value needs no further handling guidance
- **THEN** the result carries no `instruction` field

#### Scenario: Disposition plus response-specific detail
- **WHEN** a `Result` sets disposition `agent/error` because two arguments were mutually exclusive
- **THEN** the result's `instruction`, if present, names the specific arguments in conflict rather than repeating generic error-handling guidance

