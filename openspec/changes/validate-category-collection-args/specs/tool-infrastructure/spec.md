## ADDED Requirements

### Requirement: CategoryCollection Args Cross-Field Validation
`CategoryCollectionAddArgs`, `CategoryCollectionChangeArgs`, and `CategoryCollectionUpdateArgs` SHALL reject incompatible field combinations at model construction time with a descriptive `ValueError`.

Fields that are category-only (`dir`, `patterns`, `new_dir`, `new_patterns`, `add_patterns`, `remove_patterns`) MUST NOT be provided when `type='collection'`.

Fields that are collection-only (`categories`, `new_categories`, `add_categories`, `remove_categories`) MUST NOT be provided when `type='category'`.

#### Scenario: Category-only fields rejected for collection type
- **WHEN** `CategoryCollectionAddArgs(type='collection', name='all', dir='docs/')` is constructed
- **THEN** a `ValueError` is raised indicating `dir` is not valid for `type='collection'`

#### Scenario: Collection-only fields rejected for category type
- **WHEN** `CategoryCollectionAddArgs(type='category', name='docs', categories=['guidelines', 'specs'])` is constructed
- **THEN** a `ValueError` is raised indicating `categories` is not valid for `type='category'`

#### Scenario: Compatible fields accepted
- **WHEN** `CategoryCollectionAddArgs(type='category', name='docs', dir='docs/')` is constructed
- **THEN** no error is raised
