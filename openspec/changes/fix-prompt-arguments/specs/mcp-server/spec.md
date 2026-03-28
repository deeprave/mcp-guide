## MODIFIED Requirements

### Requirement: Guide Prompt Argument Handling

The guide prompt SHALL receive all positional arguments passed by the client regardless of transport mode (stdio, TUI, HTTP).

#### Scenario: TUI mode argument delivery

- GIVEN the guide prompt is invoked from a TUI-mode client
- WHEN the client passes one or more arguments
- THEN all arguments are received by the prompt handler in order
