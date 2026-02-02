# Help Template System Spec Delta

## ADDED Requirements

### Requirement: User Documentation

The system SHALL provide comprehensive user-facing documentation covering all major features and configuration options.

Documentation SHALL include:
- General usage and configuration guides
- Document management and frontmatter reference
- Template syntax and functions
- Feature flags reference
- Commands and guide prompt usage

#### Scenario: User needs configuration guidance

- **WHEN** user wants to configure categories and collections
- **THEN** documentation provides clear examples and explanations
- **AND** documentation explains feature flags that affect behavior

#### Scenario: User needs frontmatter reference

- **WHEN** user wants to add frontmatter to documents
- **THEN** documentation lists all supported keys and their formats
- **AND** documentation provides examples for common use cases

#### Scenario: User needs template help

- **WHEN** user wants to create or modify templates
- **THEN** documentation explains template syntax and conditionals
- **AND** documentation lists available functions and partials

#### Scenario: User needs feature flag reference

- **WHEN** user wants to enable or configure a feature
- **THEN** documentation explains each feature flag's purpose and format
- **AND** documentation provides configuration examples

#### Scenario: User needs command help

- **WHEN** user wants to use commands
- **THEN** documentation shows basic invocation format with one example
- **AND** documentation points to :help for discovering available commands
