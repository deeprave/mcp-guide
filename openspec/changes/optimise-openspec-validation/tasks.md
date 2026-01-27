## 1. Project Configuration
- [x] 1.1 Add `openspec_validated` boolean field to Project dataclass
- [x] 1.2 Default to False for new projects
- [x] 1.3 Persist via project configuration

## 2. Template Changes
- [x] 2.1 Update `openspec-project-check.mustache` to check file existence only (not read content)
- [x] 2.2 Skip validation entirely if `openspec_validated` flag is true

## 3. Validation Logic
- [x] 3.1 Check `openspec/project.md` exists
- [x] 3.2 Request OpenSpec changes list (validates `openspec/changes` directory and populates cache)
- [x] 3.3 Check OpenSpec CLI command exists
- [x] 3.4 Set `openspec_validated` to true after all checks pass
- [x] 3.5 Never re-validate while flag is true

## 4. Testing
- [x] 4.1 Test file existence check works correctly
- [x] 4.2 Test changes directory validation via list command
- [x] 4.3 Test validation only runs once per project
- [x] 4.4 Test flag persists across sessions

## 5. Documentation
- [x] 5.1 Update comments explaining one-time validation
- [x] 5.2 Document openspec_validated field in Project dataclass
