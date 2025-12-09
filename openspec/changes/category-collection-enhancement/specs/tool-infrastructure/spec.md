## ADDED Requirements

### Requirement: Expression-Based Content Retrieval
The system SHALL support flexible expression syntax for retrieving content from multiple categories with boolean logic.

#### Scenario: Multi-category comma-separated syntax
- **WHEN** category parameter contains comma-separated values
- **THEN** content is retrieved from all specified categories
- **AND** results are aggregated

#### Scenario: Category with document specification
- **WHEN** category includes `/docname` suffix
- **THEN** only specified document is retrieved from that category
- **AND** category default patterns are ignored

#### Scenario: Boolean OR operator
- **WHEN** document expression contains `|` operator
- **THEN** documents matching any OR clause are retrieved
- **AND** OR has highest precedence

#### Scenario: Boolean AND operator
- **WHEN** document expression contains `&` operator
- **THEN** all documents matching AND clauses are retrieved
- **AND** AND is evaluated within OR sections

#### Scenario: Complex boolean expressions
- **WHEN** expression contains both `&` and `|` operators
- **THEN** OR sections are evaluated left-to-right
- **AND** AND clauses within each OR section are evaluated
- **AND** results are aggregated correctly

#### Scenario: Filename parameter override
- **WHEN** `filename` parameter is provided
- **THEN** it overrides default patterns for plain categories
- **AND** it does not affect categories with document specifications

#### Scenario: Space handling
- **WHEN** expression contains spaces
- **THEN** unescaped spaces are automatically removed
- **AND** expressions can be quoted to contain spaces

#### Scenario: Glob character support
- **WHEN** document names contain glob characters (`*`, `?`, `**`, `\`)
- **THEN** standard glob matching is applied
- **AND** backslash escapes special characters

#### Scenario: Expression parsing errors
- **WHEN** expression is malformed
- **THEN** clear error message is returned
- **AND** error indicates location and nature of problem

### Requirement: Collections Store Expressions
The system SHALL allow collections to store category/document expressions.

#### Scenario: Collection with expressions
- **WHEN** collection is defined with category/document expressions
- **THEN** expressions are stored in collection
- **AND** expressions can include boolean operators

#### Scenario: Collection content delegation
- **WHEN** `collection_content` is called
- **THEN** stored expressions are concatenated
- **AND** concatenated expression is passed to `category_content`
- **AND** single unified handler processes request

#### Scenario: Expression validation in collections
- **WHEN** collection is created or updated with expressions
- **THEN** expressions are validated
- **AND** invalid expressions are rejected with clear error
