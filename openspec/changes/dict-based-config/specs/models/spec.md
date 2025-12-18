# models Spec Delta

## MODIFIED Requirements

### Requirement: Project Configuration Structure

The system SHALL use dictionary-based storage for categories and collections instead of list-based storage.

**Data Models:**
- `Project.categories` SHALL be `dict[str, Category]` where keys are category names
- `Project.collections` SHALL be `dict[str, Collection]` where keys are collection names
- `Category` model SHALL NOT include `name` field (name becomes dict key)
- `Collection` model SHALL NOT include `name` field (name becomes dict key)

**Configuration Format:**
```yaml
categories:
  guide:
    dir: guide/
    patterns: [guidelines]
    description: "Project guidelines"
  lang:
    dir: lang/
    patterns: [python]
    description: "Language-specific rules"

collections:
  all:
    categories: [guide, lang]
    description: "All guidelines"
```

#### Scenario: Dictionary-based category access
- **WHEN** accessing category by name
- **THEN** use `project.categories[name]` for O(1) lookup

#### Scenario: Dictionary-based collection access
- **WHEN** accessing collection by name
- **THEN** use `project.collections[name]` for O(1) lookup

#### Scenario: Category iteration
- **WHEN** iterating over categories
- **THEN** use `project.categories.items()` to get (name, category) pairs

#### Scenario: Collection iteration
- **WHEN** iterating over collections
- **THEN** use `project.collections.items()` to get (name, collection) pairs

#### Scenario: Duplicate prevention
- **WHEN** checking if category/collection exists
- **THEN** use `name in project.categories` for O(1) existence check

### Requirement: Configuration Migration

The system SHALL automatically migrate list-based configurations to dictionary-based format.

**Migration Process:**
- Detect list-based format during configuration loading
- Convert categories list to dictionary with names as keys
- Convert collections list to dictionary with names as keys
- Remove `name` fields from category/collection objects
- Log migration warnings for user awareness

#### Scenario: Automatic migration on load
- **WHEN** loading configuration with list-based categories/collections
- **THEN** automatically convert to dictionary format and save

#### Scenario: Migration logging
- **WHEN** performing automatic migration
- **THEN** log warning about format conversion

#### Scenario: Invalid migration data
- **WHEN** list-based config has duplicate names
- **THEN** fail migration with clear error message

### Requirement: Template Context Name Injection

The system SHALL inject category and collection names into template contexts since names are no longer object fields.

**Name Injection:**
- Category contexts SHALL include `name` field from dictionary key
- Collection contexts SHALL include `name` field from dictionary key
- Template contexts SHALL maintain backward compatibility with existing templates

#### Scenario: Category name in template context
- **WHEN** building category template context
- **THEN** inject category name from dictionary key as `name` field

#### Scenario: Collection name in template context
- **WHEN** building collection template context
- **THEN** inject collection name from dictionary key as `name` field

#### Scenario: Template backward compatibility
- **WHEN** existing templates reference `{{category.name}}`
- **THEN** name is available from injected context data
