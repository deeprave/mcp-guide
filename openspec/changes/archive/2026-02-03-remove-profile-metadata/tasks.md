## 1. Remove metadata field from Project model
- [x] Remove `metadata` field from Project dataclass
- [x] Remove unused `Any` import
- [x] Update docstring

## 2. Remove metadata tracking from Profile
- [x] Remove metadata tracking logic from Profile.apply_to_project()
- [x] Profile only adds categories and collections

## 3. Remove metadata display
- [x] Remove applied_profiles display from format_project_data()

## 4. Update tests
- [x] Remove metadata assertions from test_profile_application.py
- [x] Verify all tests pass (1273 passing)

## 5. Verification
- [x] All quality checks pass (ruff, mypy)
- [x] No references to metadata or applied_profiles remain
- [x] Profile functionality works correctly
