# Implementation Tasks

## 1. Investigation

- [ ] 1.1 Identify where frontmatter is parsed
- [ ] 1.2 Identify where template rendering occurs
- [ ] 1.3 Determine if frontmatter is rendered before or after extraction
- [ ] 1.4 Find recent changes that broke variable expansion
- [ ] 1.5 Identify where instruction text is aggregated/combined

## 2. Fix Variable Expansion

- [ ] 2.1 Ensure frontmatter fields are rendered with template context
- [ ] 2.2 Apply same context to frontmatter as template body
- [ ] 2.3 Preserve frontmatter structure after rendering

## 3. Implement Instruction Deduplication

- [ ] 3.1 Identify common repeated phrases in instructions
- [ ] 3.2 Create deduplication logic for instruction text
- [ ] 3.3 Combine repeated "Do not display" phrases into single statement
- [ ] 3.4 Preserve unique instruction content while removing redundancy
- [ ] 3.5 Apply deduplication after template rendering

## 4. Testing

- [ ] 4.1 Add test for template variables in frontmatter instruction field
- [ ] 4.2 Add test for instruction deduplication
- [ ] 4.3 Add test for template variables in other frontmatter fields
- [ ] 4.4 Verify existing templates still work correctly
- [ ] 4.5 Test with workflow context variables

## 5. Verification

- [ ] 5.1 Verify {{workflow.file}} expands correctly
- [ ] 5.2 Verify other workflow variables expand correctly
- [ ] 5.3 Verify repeated phrases are deduplicated
- [ ] 5.4 Check all templates with instruction fields
- [ ] 5.5 Ensure no regression in template rendering
