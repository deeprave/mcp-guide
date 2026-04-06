## ADDED Requirements

### Requirement: Policy Topic URI Resolution

The system SHALL resolve `guide://policies/<topic>` URIs to the active policy content for that
topic using sub-path filtering of the `policies` category.

Resolution SHALL:
- Apply the `<topic>` path segment as a sub-path filter against the `policies` category
- Narrow results to documents matching both the sub-path prefix and the project's configured patterns
- Concatenate all matched documents (composable resolution — no exclusivity enforced)
- Return the `_missing_policy` placeholder content when no documents match the topic

#### Scenario: Active policy for topic resolved
- **WHEN** `guide://policies/git/ops` is accessed and a policy is selected for `git/ops`
- **THEN** the selected policy document(s) for `git/ops` are returned

#### Scenario: Multiple documents for composable topic
- **WHEN** multiple documents match the project's patterns under the topic sub-path
- **THEN** all matched documents are concatenated and returned

#### Scenario: No policy selected for topic
- **WHEN** `guide://policies/git/ops` is accessed and no patterns match documents under `git/ops`
- **THEN** the `_missing_policy` placeholder content is returned

#### Scenario: Topic sub-path filter applied
- **WHEN** `guide://policies/testing` is accessed
- **THEN** only documents under `policies/testing/` matching active patterns are returned,
      not documents from other policy topics
