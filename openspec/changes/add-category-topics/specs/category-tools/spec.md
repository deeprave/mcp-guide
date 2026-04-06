## ADDED Requirements

### Requirement: Category Document Discovery

The system SHALL provide a `discover_category_documents(category, pattern)` function that returns
the set of document paths for a category without rendering their content.

The function SHALL:
- Query both the filesystem template corpus and stored project documents for the category
- Exclude files and directories with a `_` prefix from results
- Apply the given pattern as a filter (or return all documents if pattern is None/empty)
- Return results in a consistent, reproducible order

#### Scenario: Filesystem documents discovered
- **WHEN** the category has documents in the filesystem template corpus
- **THEN** those documents are included in the returned set

#### Scenario: Stored documents discovered
- **WHEN** the category has documents stored as project documents
- **THEN** those stored documents are included in the returned set

#### Scenario: Combined discovery
- **WHEN** the category has both filesystem and stored documents
- **THEN** both sources are included in the returned set without duplication

#### Scenario: Underscore prefix exclusion
- **WHEN** a document or directory has a `_` prefix
- **THEN** it is excluded from the returned set

#### Scenario: Empty category
- **WHEN** the category has no documents matching the pattern
- **THEN** an empty set is returned

### Requirement: Sub-path Category Filtering

The system SHALL support sub-path filtering in category content resolution when a document
pattern ends with a trailing slash.

Sub-path filtering SHALL use prefix-filter semantics: it narrows the documents matched by the
project's existing configured patterns to those under the specified sub-path prefix. It SHALL
NOT override the project's configured patterns.

#### Scenario: Trailing slash triggers sub-path filtering
- **WHEN** the document pattern ends with `/` (e.g. `"git/ops/"`)
- **THEN** only documents under that sub-path that also match the project's configured patterns
      are returned

#### Scenario: No trailing slash — unchanged behavior
- **WHEN** the document pattern does not end with `/`
- **THEN** existing pattern-matching behavior applies without sub-path filtering

#### Scenario: Configured pattern narrows sub-path results
- **WHEN** a project has configured pattern `git/ops/conservative*` and sub-path filter `git/ops/`
- **THEN** only documents matching `git/ops/conservative*` under `git/ops/` are returned
      (not all documents under `git/ops/`)

#### Scenario: Sub-path with no matching configured patterns
- **WHEN** sub-path filter is applied but no configured patterns match documents under that path
- **THEN** an empty result is returned
