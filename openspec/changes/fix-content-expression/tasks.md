# Tasks for fix-content-expression

## 1. Extract expression parsing logic from get_content
- [ ] Create shared function `parse_content_expression(expression: str)` in `content_common.py`
- [ ] Function should return list of (category, pattern) tuples
- [ ] Handle comma-separated expressions
- [ ] Handle category/pattern syntax
- [ ] Handle multiple patterns with +

## 2. Update category_content to use expression parsing
- [ ] Modify `category_content` in `tool_category.py` to call `parse_content_expression`
- [ ] If expression contains `/`, parse as category/pattern
- [ ] If expression contains `,`, split and process each
- [ ] Aggregate and deduplicate results

## 3. Update collection_content to use expression parsing
- [ ] Modify collection content retrieval to parse expressions in collection.categories
- [ ] Each expression in collection should be parsed and resolved
- [ ] Aggregate and deduplicate results from all expressions

## 4. Add tests
- [ ] Test `category_content("review/commit")` works
- [ ] Test `category_content("review/commit+pr")` works
- [ ] Test collections with expressions work
- [ ] Verify existing tests still pass
