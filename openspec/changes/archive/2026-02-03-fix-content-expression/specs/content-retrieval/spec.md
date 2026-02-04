# Spec: Content Expression Parsing

## MODIFIED Requirements

### Requirement: Category Content Retrieval

The system SHALL parse expressions in category_content to support category/pattern syntax.

#### Scenario: Retrieve content with category and pattern

GIVEN a category "review" exists
AND the category contains files matching pattern "commit"
WHEN category_content("review/commit") is called
THEN the system SHALL parse "review" as category
AND "commit" as pattern
AND return matching content from the review category

#### Scenario: Retrieve content with multiple patterns

GIVEN a category "review" exists
AND the category contains files matching "commit" and "pr"
WHEN category_content("review/commit+pr") is called
THEN the system SHALL parse "review" as category
AND "commit+pr" as multiple patterns
AND return aggregated content matching either pattern
AND deduplicate results

#### Scenario: Retrieve content with multiple expressions

GIVEN categories "review" and "docs" exist
WHEN category_content("review/commit,docs/guide") is called
THEN the system SHALL parse as two expressions
AND retrieve content from review category with commit pattern
AND retrieve content from docs category with guide pattern
AND return aggregated deduplicated results

#### Scenario: Backward compatibility with simple category name

GIVEN a category "review" exists
WHEN category_content("review") is called
THEN the system SHALL treat "review" as simple category name
AND return all content from the review category
AND maintain existing behavior
