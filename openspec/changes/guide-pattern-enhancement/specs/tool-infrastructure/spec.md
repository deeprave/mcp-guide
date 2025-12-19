## ADDED Requirements

### Requirement: Document Expression Model
The system SHALL use a unified DocumentExpression model for parsing user input before resolution.

#### Scenario: Document expression parsing
- **WHEN** user provides input like "category/pattern+pattern2"
- **THEN** DocumentExpression SHALL parse raw input into structured components
- **AND** validation SHALL be deferred until resolution time

#### Scenario: Expression model structure
- **WHEN** DocumentExpression is created
- **THEN** it SHALL contain:
  - `raw_input`: Original user input string
  - `name`: Parsed category or collection name
  - `patterns`: Optional list of parsed patterns
- **AND** no strict validation SHALL be applied during parsing

#### Scenario: Category vs collection resolution
- **WHEN** DocumentExpression is resolved in get_content
- **THEN** system SHALL first check if name matches existing collection
- **AND** if no collection found, SHALL treat as category name
- **AND** validation SHALL occur during resolution, not parsing

### Requirement: Category Name Validation Rules
The system SHALL apply different validation rules for parsing vs user creation of categories.

#### Scenario: Parsing allows underscore prefix
- **WHEN** parsing user input containing category name with underscore prefix
- **THEN** parsing SHALL succeed and allow the underscore
- **AND** underscore-prefixed names SHALL be treated as valid for lookup

#### Scenario: User creation disallows underscore prefix
- **WHEN** user attempts to create category with underscore prefix via category_add
- **THEN** validation SHALL fail with clear error message
- **AND** error SHALL indicate underscore prefix is reserved for system categories

#### Scenario: System category access
- **WHEN** system or existing categories have underscore prefix
- **THEN** they SHALL be accessible through get_content and other tools
- **AND** underscore prefix SHALL be treated as reserved namespace

#### Scenario: Category name validation during creation
- **WHEN** user creates new category via category_add
- **THEN** name SHALL be validated with strict rules:
  - No underscore prefix
  - No special characters that conflict with expression syntax
  - Standard identifier rules apply

### Requirement: Slash Syntax Content Retrieval
The system SHALL support `category/pattern` syntax as shorthand for two-parameter content retrieval.

#### Scenario: Basic slash syntax
- **WHEN** `get_content("lang/python")` is called
- **THEN** it SHALL be equivalent to `get_content("lang", "python")`
- **AND** the category is "lang" and pattern is "python"

#### Scenario: Path-like patterns
- **WHEN** `get_content("docs/api/v1/auth")` is called
- **THEN** category SHALL be "docs" and pattern SHALL be "api/v1/auth"
- **AND** only the first `/` acts as the delimiter

#### Scenario: No slash present
- **WHEN** `get_content("guidelines")` is called
- **THEN** entire string SHALL be treated as category name
- **AND** pattern SHALL be None (use category defaults)

#### Scenario: Explicit pattern parameter override
- **WHEN** `get_content("lang/python", "java")` is called
- **THEN** explicit pattern parameter SHALL take precedence
- **AND** slash-parsed pattern SHALL be ignored

### Requirement: Multi-Pattern Category Support
The system SHALL support multiple patterns within a single category using `+` separator.

#### Scenario: Multiple patterns with plus separator
- **WHEN** `get_content("lang/python+java+rust")` is called
- **THEN** content matching ANY of the patterns SHALL be retrieved
- **AND** results from all matching patterns SHALL be aggregated

#### Scenario: Plus separator with slash syntax
- **WHEN** `get_content("docs/api+tutorial+reference")` is called
- **THEN** category SHALL be "docs"
- **AND** patterns SHALL be ["api", "tutorial", "reference"]
- **AND** content matching any pattern SHALL be included

#### Scenario: Plus separator validation
- **WHEN** pattern contains `+` separator
- **THEN** each individual pattern SHALL be validated
- **AND** invalid patterns SHALL be reported with clear error messages

### Requirement: Multi-Category Expression Support
The system SHALL support comma-separated expressions for retrieving content from multiple categories.

#### Scenario: Multi-category comma separation
- **WHEN** `get_content("lang/python,docs/api,guidelines")` is called
- **THEN** content SHALL be retrieved from all three specifications
- **AND** results SHALL be aggregated in order

#### Scenario: Mixed expression syntax
- **WHEN** `get_content("lang/python+java,docs,context/openspec")` is called
- **THEN** "lang" category SHALL use patterns ["python", "java"]
- **AND** "docs" category SHALL use default patterns
- **AND** "context" category SHALL use pattern "openspec"

#### Scenario: Expression parsing errors
- **WHEN** expression contains malformed syntax
- **THEN** clear error message SHALL be returned
- **AND** error SHALL indicate location and nature of problem

#### Scenario: Whitespace handling
- **WHEN** expression contains spaces around separators
- **THEN** spaces SHALL be automatically trimmed
- **AND** expressions can be quoted to preserve internal spaces

### Requirement: Collection Pattern Overrides
The system SHALL support per-category pattern overrides in collections.

#### Scenario: Collection with pattern overrides
- **WHEN** collection is defined with pattern overrides:
```yaml
collections:
  quick-start:
    categories:
      - api-reference: ["overview*.md", "quickref*.md"]
      - user-guides: ["getting-started*.md"]
      - tutorials
```
- **THEN** "api-reference" SHALL use override patterns ["overview*.md", "quickref*.md"]
- **AND** "user-guides" SHALL use override patterns ["getting-started*.md"]
- **AND** "tutorials" SHALL use its default patterns

#### Scenario: Three-tier pattern resolution
- **WHEN** content is retrieved from collection with overrides
- **THEN** pattern resolution SHALL follow priority order:
  1. Tool call `pattern` parameter (highest priority)
  2. Collection pattern override (medium priority)
  3. Category default patterns (lowest priority)

#### Scenario: Backward compatible collections
- **WHEN** existing collection without pattern overrides is accessed
- **THEN** all categories SHALL use their default patterns
- **AND** behavior SHALL be identical to pre-enhancement behavior

### Requirement: Common FileInfo Gathering and Rendering
The system SHALL separate FileInfo gathering from content rendering with shared functions.

#### Scenario: Category FileInfo gathering function
- **WHEN** system needs FileInfo for a category
- **THEN** it SHALL call a common gather_category_fileinfos function
- **AND** function SHALL handle pattern resolution (overrides, defaults, multi-pattern)
- **AND** function SHALL return List[FileInfo] without rendering

#### Scenario: Common rendering function
- **WHEN** system has List[FileInfo] to render
- **THEN** it SHALL call a common render_fileinfos function
- **AND** function SHALL handle template context and formatting
- **AND** function SHALL return formatted content string

#### Scenario: internal_category_content refactored
- **WHEN** internal_category_content is called
- **THEN** it SHALL call gather_category_fileinfos for the category
- **AND** call render_fileinfos to format the results
- **AND** return Result[str] with rendered content

#### Scenario: gather_content uses common functions
- **WHEN** gather_content processes expressions
- **THEN** for categories it SHALL call gather_category_fileinfos
- **AND** for collections it SHALL recursively call gather_content
- **AND** aggregate all FileInfo objects across categories/collections
- **AND** final rendering SHALL use the same render_fileinfos function
The system SHALL implement a gather_content function that processes expressions and delegates to existing internal tools.

#### Scenario: Expression parsing and delegation
- **WHEN** get_content receives an expression
- **THEN** it SHALL call gather_content to process the expression
- **AND** gather_content SHALL split expression by commas
- **AND** for each sub-expression SHALL split by first `/` to separate name from patterns

#### Scenario: Collection resolution and recursion
- **WHEN** gather_content encounters a collection name
- **THEN** it SHALL retrieve the collection definition
- **AND** recursively call gather_content with the collection's stored expression
- **AND** aggregate results from the recursive call

#### Scenario: Category resolution via internal tool
- **WHEN** gather_content encounters a category name
- **THEN** it SHALL call internal_category_content with appropriate arguments
- **AND** use the existing category content logic without duplication

#### Scenario: FileInfo aggregation and rendering
- **WHEN** gather_content completes processing all sub-expressions
- **THEN** it SHALL return a unified set of FileInfo objects
- **AND** get_content SHALL render these FileInfo objects directly or via template
- **AND** de-duplication SHALL occur at the FileInfo level by absolute path

#### Scenario: Pattern handling in delegation
- **WHEN** sub-expression contains patterns (after `/`)
- **THEN** patterns SHALL be passed to internal_category_content
- **AND** multi-pattern syntax (`+` separator) SHALL be resolved before delegation
- **AND** pattern precedence rules SHALL be applied during resolution
The system SHALL provide unified content access through single `get_content` tool.

#### Scenario: Collection as expression macro
- **WHEN** `get_content("quick-start")` is called on a collection
- **THEN** collection's stored expression SHALL be resolved
- **AND** content SHALL be retrieved according to collection definition

#### Scenario: Mixed collections and categories
- **WHEN** `get_content("quick-start,lang/rust,context/openspec")` is called
- **THEN** "quick-start" SHALL be resolved as collection expression
- **AND** "lang/rust" SHALL be resolved as category with pattern
- **AND** "context/openspec" SHALL be resolved as category with pattern
- **AND** all results SHALL be aggregated

#### Scenario: Collection vs category name resolution
- **WHEN** name exists as both collection and category
- **THEN** collection SHALL take precedence
- **AND** category can be accessed by using explicit pattern syntax

### Requirement: Enhanced Collection Management
Collection management tools SHALL support pattern overrides.

#### Scenario: Add collection with pattern overrides
- **WHEN** `collection_add` is called with pattern overrides
- **THEN** pattern overrides SHALL be stored in collection definition
- **AND** overrides SHALL be validated as valid glob patterns

#### Scenario: Update collection pattern overrides
- **WHEN** `collection_change` is called to modify pattern overrides
- **THEN** pattern overrides SHALL be updated
- **AND** updated collection SHALL be persisted

#### Scenario: List collections with pattern overrides
- **WHEN** `collection_list` is called with verbose mode
- **THEN** pattern overrides SHALL be displayed for each category
- **AND** categories without overrides SHALL be clearly indicated

### Requirement: Pattern Override Validation
Pattern overrides SHALL be validated as valid glob patterns.

#### Scenario: Valid pattern override
- **WHEN** collection contains pattern override `["*.md", "*.txt"]`
- **THEN** validation SHALL succeed

#### Scenario: Invalid pattern override
- **WHEN** collection contains invalid pattern override `["[invalid"]`
- **THEN** validation SHALL fail with clear error message
- **AND** error SHALL indicate which pattern is invalid

## MODIFIED Requirements

### Requirement: Result.ok() Method Signature
The `Result.ok()` method SHALL accept optional value parameter to match class design.

#### Scenario: Optional value parameter
- **WHEN** `Result.ok()` is called without value parameter
- **THEN** result SHALL have `value=None`
- **AND** message and instruction parameters SHALL work normally

#### Scenario: Explicit value parameter
- **WHEN** `Result.ok(value="content")` is called
- **THEN** result SHALL have the specified value
- **AND** behavior SHALL be identical to current implementation

### Requirement: Content Retrieval Error Handling
Content retrieval SHALL treat "no content found" as successful operation with advisory message.

#### Scenario: No content found success
- **WHEN** content retrieval finds no matching files
- **THEN** `Result.ok()` SHALL be returned with empty content
- **AND** advisory message SHALL indicate "No content found"
- **AND** operation SHALL be considered successful, not failed

#### Scenario: Consistent no-content handling
- **WHEN** any content retrieval operation finds no matches
- **THEN** behavior SHALL be consistent across categories, collections, and expressions
- **AND** advisory messages SHALL be informative but not treated as errors

## DEPRECATED Requirements

### Requirement: Separate Collection Content Tool
The `get_collection_content` tool SHALL be deprecated in favor of unified `get_content`.

#### Scenario: Deprecation notice
- **WHEN** `get_collection_content` is called
- **THEN** functionality SHALL work as before
- **AND** deprecation warning SHALL be logged
- **AND** migration guidance SHALL be provided

#### Scenario: Migration path
- **WHEN** migrating from `get_collection_content(collection="name")`
- **THEN** equivalent call is `get_content("name")`
- **AND** all existing functionality SHALL be preserved
