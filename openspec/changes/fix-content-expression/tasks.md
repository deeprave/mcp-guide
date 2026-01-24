# Tasks for fix-content-expression

## 1. Update category_content to use parse_expression
- [x] Import `parse_expression` from `content_common.py`
- [x] Parse `args.category` using `parse_expression`
- [x] Handle multiple expressions and aggregate results
- [x] Deduplicate FileInfo results
- [x] Maintain backward compatibility

## 2. Add tests
- [x] Test `category_content("review/commit")` works
- [x] Test `category_content("review/commit+pr")` works
- [x] Test `category_content("review/commit,docs/guide")` works
- [x] Verify existing tests still pass
