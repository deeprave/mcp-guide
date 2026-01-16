# Change: Add Template Partials Support

## Why
Template systems need to reuse common content across multiple templates. Currently, there's no mechanism to include partial templates, leading to duplication of common elements like project information displays.

## What Changes
- Add frontmatter `includes:` keyword for specifying partial templates
- Implement Mustache partial registration from included files
- Create standard project display partial for reuse across templates

## Impact
- Affected specs: template-system
- Affected code: template rendering, frontmatter processing
- New files: templates/partials/ directory structure
