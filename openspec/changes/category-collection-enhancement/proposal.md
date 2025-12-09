# Change: Enhanced Category and Collection Content Retrieval

## Why

Current content retrieval is limited to single categories or collections. Users need flexible, expressive syntax to retrieve specific documents from multiple categories with boolean logic (AND/OR operations) without creating numerous collections.

## What Changes

### 1. Multi-Category Document Selection
Allow comma-separated category/document specifications:
```
category_content(category="category1/docname1,category2/docname2,category3", filename="name")
```
- `filename` parameter overrides default patterns for plain categories

### 2. Boolean Expression Support
Add AND (`&`) and OR (`|`) operators for document selection within categories:
- AND (`&`) has highest precedence (binds more tightly)
- OR (`|`) has lower precedence
- Examples:
  - `category1/docname1|docname3` - fetch docname1 OR docname3
  - `category1/docname1&docname3` - fetch docname1 AND docname3
  - `category1/docname1&docname2|docname3&docname4` - (doc1 AND doc2) OR (doc3 AND doc4)

### 3. Collections as Expression Storage
- Collections store category/document expressions (not just plain category names)
- `collection_content` passes concatenated expressions to `category_content`
- Single unified content handler
- Expression parsing rules:
  - First `/` separates category from document expression
  - Unescaped commas separate expressions
  - Spaces automatically removed (expressions can be quoted)
  - Standard glob characters (`*`, `?`, `**`, `\`) have special meaning

### 4. Expression Parser
Implement lightweight expression parser:
- Split on commas (respecting escapes)
- Split on first `/` for category/document separation
- Parse OR (`|`) expressions left-to-right
- Parse AND (`&`) within OR sections
- Apply glob matching for document names

## Impact

- **Affected specs**: `tool-infrastructure`, `models`
- **Affected code**:
  - `src/mcp_guide/tools/tool_category.py` - Enhanced category_content
  - `src/mcp_guide/tools/tool_collection.py` - Simplified collection_content
  - `src/mcp_guide/models.py` - Collection model to store expressions
  - New expression parser module
- **Breaking change**: No - extends existing functionality
- **Benefits**:
  - Flexible document retrieval without creating collections
  - Boolean logic for complex queries
  - Collections become more powerful
  - Single unified content handler
  - Reduced code duplication

## Acceptance Criteria

- [ ] Multi-category comma-separated syntax works
- [ ] Boolean AND (`&`) operator works
- [ ] Boolean OR (`|`) operator works with correct precedence
- [ ] Complex expressions parse correctly
- [ ] Collections can store category/document expressions
- [ ] `collection_content` delegates to `category_content`
- [ ] Expression parser handles escapes and special characters
- [ ] All tests pass
- [ ] Documentation includes expression syntax guide
- [ ] Spec deltas added
