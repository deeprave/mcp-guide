**Approval gate**: PENDING

## 1. Design Expression Parser
- [ ] 1.1 Define expression grammar and precedence rules
- [ ] 1.2 Design parser architecture
- [ ] 1.3 Define error handling for malformed expressions
- [ ] 1.4 Document expression syntax

## 2. Implement Expression Parser
- [ ] 2.1 Create expression parser module
- [ ] 2.2 Implement comma splitting (respecting escapes)
- [ ] 2.3 Implement category/document separation (first `/`)
- [ ] 2.4 Implement OR (`|`) parsing
- [ ] 2.5 Implement AND (`&`) parsing
- [ ] 2.6 Implement space removal
- [ ] 2.7 Add unit tests for parser

## 3. Enhance category_content Tool
- [ ] 3.1 Update to accept expression syntax
- [ ] 3.2 Integrate expression parser
- [ ] 3.3 Implement multi-category retrieval
- [ ] 3.4 Implement boolean logic evaluation
- [ ] 3.5 Handle `filename` parameter override
- [ ] 3.6 Add integration tests

## 4. Update Collection Model
- [ ] 4.1 Modify Collection model to store expressions
- [ ] 4.2 Update collection validation
- [ ] 4.3 Add migration path if needed
- [ ] 4.4 Update collection tests

## 5. Simplify collection_content Tool
- [ ] 5.1 Refactor to delegate to category_content
- [ ] 5.2 Concatenate collection expressions
- [ ] 5.3 Update tests
- [ ] 5.4 Verify backward compatibility

## 6. Update Documentation
- [ ] 6.1 Document expression syntax with examples
- [ ] 6.2 Update tool descriptions
- [ ] 6.3 Add usage guide for complex queries
- [ ] 6.4 Update README

## 7. Update Specifications
- [ ] 7.1 Create spec delta for tool-infrastructure
- [ ] 7.2 Create spec delta for models
- [ ] 7.3 Document expression grammar
- [ ] 7.4 Add scenarios for all expression types
