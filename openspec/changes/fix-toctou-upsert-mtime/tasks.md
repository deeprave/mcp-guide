## 1. Store layer — conditional upsert

- [x] 1.1 Add mtime comparison logic to `_add_document()` within the write transaction
- [x] 1.2 Return skip indicator when mtime is unchanged or newer
- [x] 1.3 Unit tests for mtime skip, mtime older, mtime absent, force override

## 2. Task layer — remove TOCTOU pattern

- [x] 2.1 Remove `get_document()` staleness check from `document_task.py`
- [x] 2.2 Pass mtime/force through to store layer
- [x] 2.3 Update integration tests

## 3. Check

- [x] 3.1 Full test suite, ruff, ty
