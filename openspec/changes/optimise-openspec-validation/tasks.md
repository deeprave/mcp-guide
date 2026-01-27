## 1. Project Configuration
- [x] 1.1 Add `openspec_validated` boolean field to Project dataclass
- [x] 1.2 Add `openspec_version` optional string field to Project dataclass
- [x] 1.3 Default to False for new projects
- [x] 1.4 Persist via project configuration

## 2. Version Comparison Utility
- [x] 2.1 Add `meets_minimum_version(minimum: str) -> bool` method to OpenSpecTask
- [x] 2.2 Use `packaging.version.Version` for semantic version comparison
- [x] 2.3 Handle version prefixes (v1.2.3 or 1.2.3)
- [x] 2.4 Return False if version is None
- [x] 2.5 Add unit tests for version comparison (1.10.2 > 1.9.6, etc.)

## 3. Template Changes
- [x] 3.1 Update `openspec-project-check.mustache` to check file existence only (not read content)
- [x] 3.2 Skip validation entirely if `openspec_validated` flag is true
- [x] 3.3 Request OpenSpec version during validation if not already validated

## 4. Validation Logic
- [x] 4.1 Check `openspec/project.md` exists
- [x] 4.2 Request OpenSpec changes list (validates `openspec/changes` directory and populates cache)
- [x] 4.3 Check OpenSpec CLI command exists
- [x] 4.4 Add session-level version cache (`_version_this_session`)
- [x] 4.5 On startup: compare project version with session cache
- [x] 4.6 Request version if cache empty or versions differ
- [x] 4.7 Capture and store OpenSpec version in project config
- [x] 4.8 Set `openspec_validated` to true after all checks pass (including version)
- [x] 4.9 Never re-validate while flag is true

## 5. Template Context Lambda
- [x] 5.1 Add `has_version` lambda to openspec template context
- [x] 5.2 Lambda accepts minimum version string as parameter
- [x] 5.3 Returns boolean using version comparison utility
- [x] 5.4 Usage: `{{#openspec.has_version}}1.2.0{{/openspec.has_version}}`
- [x] 5.5 Test lambda in template rendering

## 6. Testing
- [x] 6.1 Test file existence check works correctly
- [x] 6.2 Test changes directory validation via list command
- [x] 6.3 Test validation only runs once per project
- [x] 6.4 Test flag persists across sessions
- [x] 6.5 Test version capture and persistence
- [x] 6.6 Test version comparison utility
- [x] 6.7 Test template lambda functionality
- [x] 6.8 Test minimum version checking
- [x] 6.9 Test version detection on startup
- [x] 6.10 Test version detection on project switch
- [x] 6.11 Test version update when OpenSpec upgraded

## 7. Documentation
- [x] 7.1 Update comments explaining one-time validation
- [x] 7.2 Document openspec_validated field in Project dataclass
- [x] 7.3 Document openspec_version field in Project dataclass
- [x] 7.4 Document version comparison utility
- [x] 7.5 Document template lambda usage
