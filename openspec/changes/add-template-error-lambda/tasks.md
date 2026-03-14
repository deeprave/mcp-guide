## 1. Implementation
- [ ] 1.1 Add `error_message` attribute to `TemplateFunctions.__init__`
- [ ] 1.2 Add `_error` lambda method to `TemplateFunctions`
- [ ] 1.3 Register `_error` lambda in `render_template_content`
- [ ] 1.4 Add `error` field to `RenderedContent`
- [ ] 1.5 After rendering, check `functions.error_message` and set `rendered.error`
- [ ] 1.6 Update `_execute_command` to check `rendered.error` and return `Result.failure()`
- [ ] 1.7 Write tests for `_error` lambda
- [ ] 1.8 Migrate command templates to use `{{#_error}}` instead of inline error blocks
- [ ] 1.9 Run full test suite and verify all pass
