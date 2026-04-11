## 1. Implement frontmatter schema validator
- [ ] 1.1 Define the set of known frontmatter keys and their expected value types
- [ ] 1.2 Implement async `validate_frontmatter(content)` returning a list of `ValidationIssue`
- [ ] 1.3 Flag unknown top-level keys as warnings
- [ ] 1.4 Flag known keys with wrong value type as errors
- [ ] 1.5 Validate `requires-*` keys reference known feature flags; flag unknown as warnings

## 2. Implement Mustache variable linter
- [ ] 2.1 Implement a Mustache AST parser (or reuse Chevron internals) to extract referenced variable paths
- [ ] 2.2 Define the known template context per content type and feature flag combination
- [ ] 2.3 Flag variable references not present in any known context as warnings
- [ ] 2.4 Exclude section variables (e.g. `{{#workflow}}`) from strict checking — treat as conditional guards

## 3. Implement `guide://` URI validator
- [ ] 3.1 Extract all `guide://` URI references from template content (including partials)
- [ ] 3.2 Resolve each URI against the current project's categories, collections, commands, and stored documents
- [ ] 3.3 Flag unresolvable URIs as errors

## 4. Add `:docs/validate` command
- [ ] 4.1 Create `_commands/docs/validate.mustache` command template
- [ ] 4.2 Implement validation runner: iterate all project documents, run all validators, aggregate results
- [ ] 4.3 Group output by document path with severity indicators
- [ ] 4.4 Support `--strict` flag to treat warnings as errors
- [ ] 4.5 Add `--validate` CLI flag as an alternative entry point for CI use

## 5. Tests and validation
- [ ] 5.1 Unit tests for frontmatter schema validator with valid and invalid fixtures
- [ ] 5.2 Unit tests for Mustache variable extractor
- [ ] 5.3 Unit tests for `guide://` URI resolver against mock project content
- [ ] 5.4 Validate change with `openspec validate add-content-validation --strict --no-interactive`
