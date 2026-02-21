## 1. Implementation

- [x] 1.1 Add `_ensure_config_dir()` helper method to `Session._ConfigManager`
- [x] 1.2 Method checks if `self.config_file.parent` exists and creates with `makedirs(exist_ok=True)`
- [x] 1.3 Log any exception during directory creation and continue
- [x] 1.4 Call `_ensure_config_dir()` in `get_or_create_project_config()` before `lock_update()`
- [x] 1.5 Call `_ensure_config_dir()` in `save_project_config()` before `lock_update()`

## 2. Testing

- [x] 2.1 Verify first-time startup works with non-existent config directory
- [x] 2.2 Verify normal startup still works with existing directory
