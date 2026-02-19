## 1. Implementation

- [x] 1.1 Add ConfigDirectoryError exception class to file_lock.py
- [x] 1.2 Add logger import to file_lock.py
- [x] 1.3 Wrap lock file creation in try/except for FileNotFoundError
- [x] 1.4 Check if parent directory exists when FileNotFoundError caught
- [x] 1.5 Create parent directory if missing (log with logger.exception and raise ConfigDirectoryError on failure)
- [x] 1.6 Retry lock creation (log with logger.exception and raise ConfigDirectoryError on failure)
- [x] 1.7 Find main entry point and add exception handler for ConfigDirectoryError with exit code 2

## 2. Testing

- [x] 2.1 Add test for lock_update with missing parent directory (success case)
- [x] 2.2 Add test for lock_update when parent creation fails (raises ConfigDirectoryError)
- [x] 2.3 Add test for lock_update when retry fails after parent creation (raises ConfigDirectoryError)
- [x] 2.4 Verify first-time startup works end-to-end with non-existent config directory
