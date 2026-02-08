# Implementation Tasks: Add User Documentation

## 1. General Usage Documentation

- [ ] 1.1 Create overview of content delivery system
- [ ] 1.2 Document categories configuration and usage
- [ ] 1.3 Document collections configuration and usage
- [ ] 1.4 Document feature flags system overview
- [ ] 1.5 Add examples for common use cases

## 2. Pattern Syntax Documentation

- [ ] 2.1 Create comprehensive pattern syntax guide (docs/patterns.md)
- [ ] 2.2 Document glob pattern basics (*, **, ?, [])
- [ ] 2.3 Document recursive directory matching
- [ ] 2.4 Document file extension patterns (*.md, *.{py,js})
- [ ] 2.5 Document directory-specific patterns (src/**/*.py)
- [ ] 2.6 Add common use cases with examples
- [ ] 2.7 Document integration with categories and collections

## 3. Output Format Documentation

- [ ] 3.1 Create output formats guide (docs/output-formats.md)
- [ ] 3.2 Document MIME-multipart format
- [ ] 3.3 Document when to use vs plain format
- [ ] 3.4 Document how to enable in tools
- [ ] 3.5 Document output structure and boundaries
- [ ] 3.6 Add use cases and integration scenarios
- [ ] 3.7 Add practical examples

## 4. Document Management Documentation

- [ ] 4.1 Create frontmatter reference guide
  - [ ] 4.1.1 Document standard frontmatter keys
  - [ ] 4.1.2 Document requires-* directives
  - [ ] 4.1.3 Document includes directive
  - [ ] 4.1.4 Add frontmatter examples
- [ ] 4.2 Document commands system
  - [ ] 4.2.1 Explain command discovery
  - [ ] 4.2.2 Document command frontmatter keys
  - [ ] 4.2.3 Add command examples
- [ ] 4.3 Document client information exchange
  - [ ] 4.3.1 Explain send_* tools purpose
  - [ ] 4.3.2 Document send_file_content
  - [ ] 4.3.3 Document send_directory_listing
  - [ ] 4.3.4 Document send_working_directory
  - [ ] 4.3.5 Document send_command_location

## 5. Templates Documentation

- [ ] 5.1 Create template syntax guide (docs/templates.md)
- [ ] 5.2 Document Chevron/Mustache syntax basics
- [ ] 5.3 Document MCP Guide specific features
- [ ] 5.4 Document file detection (.mustache, .hbs extensions)
- [ ] 5.5 Document conditionals ({{#variable}}, {{^variable}})
- [ ] 5.6 Document loops and iteration
- [ ] 5.7 Add links to authoritative resources
- [ ] 5.8 Document special functions
  - [ ] 5.8.1 Document template functions
  - [ ] 5.8.2 Document partials system
- [ ] 5.9 Add practical template examples

## 6. Template Context Reference

- [ ] 6.1 Create template context reference (docs/template-context.md)
- [ ] 6.2 Document system context (timestamp, formatting)
- [ ] 6.3 Document agent context (name, version, prefix)
- [ ] 6.4 Document project context (name, flags, config)
- [ ] 6.5 Document category context (metadata, files)
- [ ] 6.6 Document file context (path, metadata)
- [ ] 6.7 Document template functions (format_date, truncate, highlight_code)
- [ ] 6.8 Document context hierarchy and precedence
- [ ] 6.9 Document all template variables and lambdas

## 7. Feature Flags Documentation

- [ ] 7.1 Create workflow flag documentation
  - [ ] 7.1.1 Document workflow flag format
  - [ ] 7.1.2 Document workflow-consent flag format
  - [ ] 7.1.3 Document phase names and requirements
  - [ ] 7.1.4 Document consent types (entry/exit)
  - [ ] 7.1.5 Add workflow configuration examples
- [ ] 7.2 Create openspec flag documentation
  - [ ] 7.2.1 Document openspec flag purpose
  - [ ] 7.2.2 Document openspec configuration
  - [ ] 7.2.3 Add openspec examples
- [ ] 7.3 Create client context flags documentation
  - [ ] 7.3.1 Document allow-client-info flag
  - [ ] 7.3.2 Document client information usage
  - [ ] 7.3.3 Add client context examples

## 8. Commands and Guide Prompt Documentation

- [ ] 8.1 Document @guide prompt basics
  - [ ] 8.1.1 Explain command invocation format
  - [ ] 8.1.2 Add one simple example with arguments
  - [ ] 8.1.3 Document :help command for discovery

## 9. Organization & Review

- [ ] 9.1 Organize documentation in appropriate directory structure
- [ ] 9.2 Create table of contents / index
- [ ] 9.3 Add cross-references between documents
- [ ] 9.4 Update README with links to new documentation
- [ ] 9.5 Update feature overview in README
- [ ] 9.6 Review for completeness and clarity
- [ ] 9.7 Add navigation aids
- [ ] 9.8 Ensure consistent terminology
