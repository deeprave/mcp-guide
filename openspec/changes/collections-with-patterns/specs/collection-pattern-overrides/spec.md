# Capability: Collection Pattern Overrides

## Overview

Enable collections to specify per-category pattern overrides, allowing fine-grained control over which files are included from each category when accessing collection content.

## ADDED Requirements

### Requirement: Collection Model Extension (REQ-CPO-001)

The Collection data model MUST support optional per-category pattern overrides.

**Rationale:** Enables collections to filter content from categories without creating duplicate categories or requiring manual pattern overrides on every tool call.

#### Scenario: Collection with Pattern Overrides

**Given** a collection definition with pattern overrides:
```yaml
collections:
  getting-started:
    description: "Quick start documentation"
    categories:
      - api-reference: ["overview*.md", "quickref*.md"]
      - user-guides: ["getting-started*.md", "installation*.md"]
      - tutorials: ["intro*.md", "hello-world*.md"]
```

**When** the collection is loaded

**Then** each category MUST retain its pattern override specification

**And** categories without overrides MUST use their default patterns

---

### Requirement: Pattern Resolution Priority (REQ-CPO-002)

Pattern resolution MUST follow a three-tier priority system.

**Rationale:** Provides predictable behavior with clear override hierarchy.

#### Scenario: Tool Call Pattern Override

**Given** a collection with pattern overrides defined

**When** `get_collection_content` is called with an explicit `pattern` parameter

**Then** the tool call pattern MUST take precedence over collection overrides

**And** the tool call pattern MUST take precedence over category defaults

#### Scenario: Collection Pattern Override

**Given** a collection with pattern overrides defined

**And** no explicit `pattern` parameter in the tool call

**When** `get_collection_content` is called

**Then** the collection's pattern overrides MUST be used for specified categories

**And** category default patterns MUST be used for categories without overrides

#### Scenario: Category Default Patterns

**Given** a collection without pattern overrides

**And** no explicit `pattern` parameter in the tool call

**When** `get_collection_content` is called

**Then** each category's default patterns MUST be used

---

### Requirement: Backward Compatibility (REQ-CPO-003)

Existing collections without pattern overrides MUST continue to work unchanged.

**Rationale:** Ensures smooth migration and no breaking changes for existing configurations.

#### Scenario: Legacy Collection Format

**Given** an existing collection defined as:
```yaml
collections:
  all-docs:
    description: "All documentation"
    categories:
      - api-reference
      - user-guides
```

**When** the collection is loaded and accessed

**Then** all categories MUST use their default patterns

**And** behavior MUST be identical to pre-enhancement behavior

---

### Requirement: Pattern Override Validation (REQ-CPO-004)

Pattern overrides MUST be validated as valid glob patterns.

**Rationale:** Prevents configuration errors and provides clear feedback.

#### Scenario: Valid Pattern Override

**Given** a collection with pattern override `["*.md", "*.txt"]`

**When** the collection is validated

**Then** validation MUST succeed

#### Scenario: Invalid Pattern Override

**Given** a collection with invalid pattern override `["[invalid"]`

**When** the collection is validated

**Then** validation MUST fail with a clear error message

**And** the error MUST indicate which pattern is invalid

---

### Requirement: Collection Management Tool Updates (REQ-CPO-005)

Collection management tools MUST support pattern overrides.

**Rationale:** Enables users to create and modify collections with pattern overrides through tools.

#### Scenario: Add Collection with Pattern Overrides

**Given** a `collection_add` tool call with pattern overrides:
```json
{
  "name": "getting-started",
  "categories": [
    {"name": "api-reference", "patterns": ["overview*.md"]},
    {"name": "user-guides"}
  ]
}
```

**When** the collection is created

**Then** the collection MUST be saved with pattern overrides

**And** `api-reference` category MUST have pattern override `["overview*.md"]`

**And** `user-guides` category MUST use default patterns

#### Scenario: Update Collection Pattern Overrides

**Given** an existing collection

**When** `collection_change` is called to modify pattern overrides

**Then** the pattern overrides MUST be updated

**And** the updated collection MUST be persisted

#### Scenario: List Collections with Pattern Overrides

**Given** collections with pattern overrides

**When** `collection_list` is called with `verbose=True`

**Then** pattern overrides MUST be displayed for each category

**And** categories without overrides MUST be clearly indicated

---

### Requirement: Configuration Format (REQ-CPO-006)

The YAML configuration format MUST support both simple and override syntax.

**Rationale:** Provides flexibility while maintaining readability.

#### Scenario: Mixed Category Specifications

**Given** a collection configuration:
```yaml
collections:
  mixed:
    categories:
      - api-reference
      - user-guides: ["getting-started*.md"]
      - tutorials
```

**When** the configuration is parsed

**Then** `api-reference` MUST use default patterns

**And** `user-guides` MUST use `["getting-started*.md"]` patterns

**And** `tutorials` MUST use default patterns

---

## MODIFIED Requirements

### Requirement: Content Retrieval Pattern Resolution (REQ-CONTENT-001)

Content retrieval MUST use three-tier pattern resolution: tool call parameter > collection override > category default.

**Original:** Content retrieval uses category default patterns or tool call override.

**Rationale:** Extends existing pattern resolution to support collection-level overrides while maintaining backward compatibility.

#### Scenario: Three-Tier Pattern Resolution

**Given** a category with default patterns `["*.md", "*.txt"]`

**And** a collection with override patterns `["overview*.md"]` for that category

**When** `get_collection_content` is called without pattern parameter

**Then** the collection override `["overview*.md"]` MUST be used

**When** `get_collection_content` is called with pattern parameter `["*.pdf"]`

**Then** the tool call pattern `["*.pdf"]` MUST be used

---

## Implementation Notes

### Data Model Changes

```python
# Before
@dataclass
class Collection:
    name: str
    description: Optional[str]
    categories: list[str]

# After
@dataclass
class Collection:
    name: str
    description: Optional[str]
    categories: list[str | dict[str, list[str]]]
```

### Configuration Serialization

- Simple category: stored as string
- Category with override: stored as dict with single key-value pair
- Deserialization must handle both formats

### Validation Rules

1. Pattern overrides must be valid glob patterns
2. Category names must exist in project
3. Pattern overrides are optional (empty list not allowed)
4. At least one pattern required if override specified

## Testing Strategy

### Unit Tests
- Collection model serialization/deserialization
- Pattern resolution priority logic
- Validation of pattern overrides

### Integration Tests
- End-to-end collection creation with overrides
- Content retrieval with various pattern combinations
- Tool operations (add, change, update, list)

### Backward Compatibility Tests
- Legacy collections continue to work
- Mixed collections (some with overrides, some without)
