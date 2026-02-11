# Implementation Tasks

## 1. Investigation

- [x] 1.1 Identify where frontmatter is parsed
- [x] 1.2 Identify where template rendering occurs
- [x] 1.3 Determine if frontmatter is rendered before or after extraction
- [x] 1.4 Find recent changes that broke variable expansion
- [x] 1.5 Identify where instruction text is aggregated/combined

## 2. Fix Variable Expansion

- [x] 2.1 Ensure frontmatter fields are rendered with template context
- [x] 2.2 Apply same context to frontmatter as template body
- [x] 2.3 Preserve frontmatter structure after rendering

## 3. Implement Instruction Deduplication

- [x] 3.1 Identify common repeated phrases in instructions
- [x] 3.2 Create deduplication logic for instruction text
- [x] 3.3 Combine repeated "Do not display" phrases into single statement
- [x] 3.4 Preserve unique instruction content while removing redundancy
- [x] 3.5 Apply deduplication after template rendering

## 4. Testing

- [x] 4.1 Add test for template variables in frontmatter instruction field
- [x] 4.2 Add test for instruction deduplication
- [x] 4.3 Add test for template variables in other frontmatter fields
- [x] 4.4 Verify existing templates still work correctly
- [x] 4.5 Test with workflow context variables

## 5. Verification

- [x] 5.1 Verify {{workflow.file}} expands correctly
- [x] 5.2 Verify other workflow variables expand correctly
- [x] 5.3 Verify repeated phrases are deduplicated
- [x] 5.4 Check all templates with instruction fields
- [x] 5.5 Ensure no regression in template rendering
