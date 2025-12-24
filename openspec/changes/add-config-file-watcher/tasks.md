## 1. Core Implementation
- [x] 1.1 Create PathWatcher generic file monitoring class
- [x] 1.2 Implement WatcherRegistry for instance management
- [x] 1.3 Create ConfigWatcher extending PathWatcher
- [x] 1.4 Add content caching with invalidation

## 2. Integration
- [x] 2.1 Integrate with session management
- [x] 2.2 Add multiple callback registration
- [x] 2.3 Implement error isolation between callbacks
- [x] 2.4 Add automatic config file monitoring to Session class
- [x] 2.5 Implement cache invalidation on external config changes
- [x] 2.6 Add WARN level logging for external config changes

## 3. Testing
- [x] 3.1 Write PathWatcher tests (25 tests, 97% coverage)
- [x] 3.2 Write ConfigWatcher tests (9 tests, 91% coverage)
- [x] 3.3 Write WatcherRegistry tests (9 tests, 100% coverage)
- [x] 3.4 Ensure cross-platform compatibility
- [x] 3.5 Add integration tests for config watcher functionality

## 4. Quality Assurance
- [x] 4.1 Pass all linting checks (ruff)
- [x] 4.2 Pass all type checking (mypy)
- [x] 4.3 Achieve >90% test coverage on new components
- [x] 4.4 Verify session cleanup and resource management
