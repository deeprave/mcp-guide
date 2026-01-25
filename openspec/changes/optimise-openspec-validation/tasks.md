## 1. Template Changes
- [ ] 1.1 Update `openspec-project-check.mustache` to check file existence only (not read content)
- [ ] 1.2 Skip validation entirely if already validated

## 2. Validation Flag
- [ ] 2.1 Add boolean flag to track validation completion
- [ ] 2.2 Set flag true after first successful validation
- [ ] 2.3 Never re-validate while flag is true

## 3. Testing
- [ ] 3.1 Test file existence check works correctly
- [ ] 3.2 Test validation only runs once
- [ ] 3.3 Test flag persists for project lifetime

## 4. Documentation
- [ ] 4.1 Update comments explaining one-time validation
