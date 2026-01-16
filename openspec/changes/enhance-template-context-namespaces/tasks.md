## 1. Investigation
- [x] 1.1 Analyze current TemplateContext implementation and extension points
- [x] 1.2 Design client-server context architecture
- [x] 1.3 Plan namespace structure and data models
- [x] 1.4 Research template-driven instruction generation

## 2. Core Implementation
- [x] 2.1 Rename system namespace to server namespace
- [x] 2.2 Add client_data parameter to build_template_context()
- [x] 2.3 Fix nested dictionary handling in template context
- [x] 2.4 Create _common system category for shared templates

## 3. ClientContextTask System
- [x] 3.1 Create ClientContextTask following workflow pattern
- [x] 3.2 Implement basic OS detection request method
- [x] 3.3 Create client-context-setup.md.mustache template
- [x] 3.4 Create client-context-detailed.md.mustache template
- [x] 3.5 Add ClientContextTask startup integration via @task_init
- [x] 3.6 Subscribe task to TaskManager with FS_FILE_CONTENT events
- [x] 3.7 Call request_basic_os_info() on startup via TIMER_ONCE

## 4. Testing
- [x] 4.1 Test system namespace rename functionality
- [x] 4.2 Test client_data parameter integration
- [x] 4.3 Test nested dictionary handling fixes
- [x] 4.4 Test ClientContextTask basic functionality
- [x] 4.5 Test template rendering with new namespaces

## 5. Integration Testing
- [x] 5.1 Test template context caching with client data
- [x] 5.2 Verify no regressions in existing functionality
- [x] 5.3 Test client-server data exchange architecture
- [x] 5.4 Test template instruction generation

## 7. Additional Improvements (Completed During Implementation)
- [x] 7.1 Implement #equals and #contains Mustache helpers
- [x] 7.2 Fix timer unique bit generation (counter-based instead of bit-shifting)
- [x] 7.3 Fix duplicate handle_event methods in ClientContextTask
- [x] 7.4 Fix task counting to count unique tasks not subscriptions
- [x] 7.5 Combine ClientContextTask subscriptions (TIMER_ONCE | FS_FILE_CONTENT)
- [x] 7.6 Fix task stats to change from "timer" to "regular" when TIMER_ONCE removed
- [x] 7.7 Remove all sampling-based code (response_processor, filesystem_bridge)
- [x] 7.8 Create system info template (templates/_commands/info/system.mustache)
