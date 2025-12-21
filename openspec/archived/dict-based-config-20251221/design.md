# dict-based-config Design Document

## Architecture Changes

### Data Model Transformation

**Before (List-based):**
```python
@dataclass
class Category:
    name: str  # Explicit field
    dir: str
    patterns: list[str]
    description: Optional[str] = None

@dataclass
class Project:
    categories: list[Category]  # Linear search required
    collections: list[Collection]
```

**After (Dict-based):**
```python
@dataclass
class Category:
    # name removed - becomes dict key
    dir: str
    patterns: list[str]
    description: Optional[str] = None

@dataclass
class Project:
    categories: dict[str, Category]  # O(1) lookup
    collections: dict[str, Collection]
```

### Template Context Name Injection

**Challenge**: Template contexts need category/collection names, but names are now dict keys.

**Solution**: Inject names during context building:

```python
def _build_category_context(category_name: str) -> TemplateContext:
    # OLD: category.name from object
    # NEW: category_name from dict key
    category_data = {
        "name": category_name,  # Inject from key
        "dir": category.dir,
        "patterns": category.patterns,
        "description": category.description,
    }
```

### Performance Improvements

| Operation | List-based | Dict-based |
|-----------|------------|------------|
| Lookup by name | O(n) | O(1) |
| Duplicate check | O(n) | O(1) |
| Add category | O(n) validation | O(1) |
| Remove category | O(n) find + remove | O(1) |

### Configuration Migration Strategy

**Automatic Migration**: Detect and convert on load:

```python
def load_project_config(data: dict) -> Project:
    # Detect old format
    if isinstance(data.get("categories"), list):
        data = migrate_list_to_dict_format(data)

    # Parse as new format
    return Project.from_dict(data)

def migrate_list_to_dict_format(data: dict) -> dict:
    # Convert categories list to dict
    if "categories" in data and isinstance(data["categories"], list):
        categories_dict = {}
        for cat in data["categories"]:
            name = cat.pop("name")  # Remove name field
            categories_dict[name] = cat  # Use as key
        data["categories"] = categories_dict

    # Same for collections
    # ...
```

### Backward Compatibility

**Template Contexts**: Names still available via injection
**Tool APIs**: No changes to arguments or responses
**Configuration**: Automatic migration on first load

## Implementation Considerations

### Error Handling
- Dict key errors become "category not found" errors
- Maintain same error messages and types for tools
- Migration errors should be clear and actionable

### Testing Strategy
- Test both old and new config formats during migration period
- Verify template context name injection works correctly
- Performance tests to validate O(1) improvements
- Integration tests with real configuration files

### Rollback Plan
If issues arise:
1. Keep migration logic to convert back to list format
2. Feature flag to disable dict-based format
3. Maintain list-based code paths temporarily
