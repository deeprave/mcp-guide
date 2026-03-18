## 1. Command Cache → Session
- [x] 1.1 Add `command_cache` dict attribute to `Session.__init__`
- [x] 1.2 Update `discover_commands()` to use session's cache instead of module global
- [x] 1.3 Remove module-level `_command_cache` and `_cache_lock`

## 2. FileCache → ContextVar
- [x] 2.1 Replace `_file_cache = FileCache()` with `ContextVar[FileCache]`
- [x] 2.2 Add accessor that creates `FileCache` on first access per-task
- [x] 2.3 Update `send_file_content` to use the ContextVar accessor

## 3. TaskManager → ContextVar
- [x] 3.1 Replace singleton `_instance` pattern with `ContextVar[TaskManager]`
- [x] 3.2 Update `get_task_manager()` to create on demand per-task
- [x] 3.3 Verify timer tasks and event dispatch are per-client
- [x] 3.4 Update tests for per-task TaskManager
