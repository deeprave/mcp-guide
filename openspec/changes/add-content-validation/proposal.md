# Change: Add Frontmatter Validation and Template Linting

## Why

Content authors currently receive no feedback on broken guide documents until an agent encounters them at runtime — at which point the failure manifests as a confusing agent error rather than a clear authoring problem. Common issues include invalid frontmatter fields, undefined Mustache variable references, broken `guide://` URIs, and `requires-*` flags referencing feature flags that don't exist. A validation command would catch these at authoring time and make content development significantly safer.

## What Changes

### 1. Add a `@guide :docs/validate` command

Add a new prompt command `:docs/validate` (and CLI flag `--validate`) that runs a suite of checks across all guide documents in the current project. Returns a structured report of issues grouped by document.

### 2. Frontmatter schema validation

Validate that frontmatter fields use known keys with correct value types. Flag unknown keys and type mismatches (e.g. `requires-workflow` set to a string instead of boolean).

### 3. Template variable linting

Parse Mustache templates and check that all referenced variables (e.g. `{{workflow.phase}}`, `{{project.name}}`) are present in the known template context for the document type and enabled feature flags. Flag undefined references as warnings.

### 4. `guide://` URI validation

Resolve all `guide://` URIs embedded in templates and verify they refer to an existing document, category, collection, or command. Flag broken URIs as errors.

### 5. `requires-*` flag reference validation

Validate that `requires-<flag>` frontmatter keys reference feature flags that are actually defined. Flag references to undefined or misspelled flags.

### 6. Severity levels: errors vs warnings

Issues are classified as:
- **error** — will cause runtime failure (broken URI, unknown frontmatter key with strict impact, missing required variable)
- **warning** — may cause unexpected behaviour (undefined template variable, unused document, unrecognised `requires-*` value)

The command exits with a non-zero status if any errors are found, enabling use in CI.

## Impact

- Affected specs: `frontmatter-processing`, `template-rendering`
- Affected code: new validation module, frontmatter parser extensions, Mustache variable extractor, `guide://` URI resolver, new command template
