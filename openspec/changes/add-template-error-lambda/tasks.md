## 1. Implementation
- [x] 1.1 Add `errors: list[str]` to `TemplateFunctions.__init__`
- [x] 1.2 Add `_error` lambda method to `TemplateFunctions` (appends rendered text, returns `""`)
- [x] 1.3 Register `_error` lambda in `render_template_content`; inject `template_name` into context
- [x] 1.4 Add `errors: list[str] = []` field to `RenderedContent`
- [x] 1.5 After rendering, copy `functions.errors` → `rendered.errors`
- [x] 1.6 Update `_execute_command` to check `rendered.errors` and return `Result.failure(error="\n".join(errors), error_type="validation", error_data={"errors": errors})`
- [x] 1.7 Write tests for `_error` lambda (single error, multiple errors, partial propagation, template_name in message)
- [x] 1.8 Migrate 23 command templates: replace `{{b}}Error:{{b}} ...` with `{{#_error}}...{{/_error}}`
- [x] 1.9 Run full test suite, ruff, mypy
