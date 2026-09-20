## MODIFIED Requirements

### Requirement: Async factory for no-project result

The system SHALL provide an async factory `make_no_project_result()` in
`result_constants.py`, taking no arguments, that produces a `Result` with a
rendered `_project-root` instruction when possible, falling back to the
static `INSTRUCTION_NO_PROJECT` string when not.

The factory SHALL:
1. Ask `GuideRuntime` for its cached no-project instruction via
   `get_runtime().get_no_project_instruction()`.
2. `GuideRuntime.get_no_project_instruction()` SHALL render `_system/_project-root`
   with `session=None` — no session is looked up or constructed for this render,
   since there genuinely is none to report at this point. `render_content`,
   `render_template`, and `get_template_contexts` SHALL accept `session=None`
   and render using system/agent context only, with project- and
   client-derived context omitted rather than raising.
3. The rendered instruction SHALL be cached for the lifetime of the process
   and reused on every subsequent call, since the template's only variable
   (`tool_prefix`) is fixed once the process starts.
4. If rendering raises `FileNotFoundError` (no `_system/_project-root`
   template available, e.g. an unconfigured docroot) or if no `GuideRuntime`
   is installed (`RuntimeError` from `get_runtime()`), the factory SHALL fall
   back to the static `INSTRUCTION_NO_PROJECT` string.

`_check_project_bound()` in `core/tool_decorator.py` SHALL delegate to the
factory on the unbound-project path, calling
`(await make_no_project_result()).to_json_str()` with no arguments — no
`ctx` or session is threaded through this call.

The static `INSTRUCTION_NO_PROJECT` constant SHALL be retained as the
factory's fallback string. The `RESULT_NO_PROJECT` object constant and its
`_make_no_project_result()` constructor SHALL NOT be retained: they were
removed once confirmed to have zero remaining callers, and the factory now
constructs a fresh `Result.failure(...)` on every call using whichever
instruction (rendered or fallback) applies.

#### Scenario: Unbound session returns rendered instruction
- **WHEN** a tool with `requires_project=True` is called
- **AND** the session is unbound
- **AND** a `GuideRuntime` is installed with a project-root template available
- **THEN** `_check_project_bound()` returns a `Result.failure` JSON string
  carrying the rendered `_project-root` template as its instruction
- **AND** the instruction contains guidance on git worktree detection and CWD
  fallback

#### Scenario: No session falls back to static instruction
- **WHEN** a tool with `requires_project=True` is called
- **AND** no `GuideRuntime` has been created for the process
- **THEN** `_check_project_bound()` returns a `Result.failure` JSON string
  using the static `INSTRUCTION_NO_PROJECT` string as its instruction

#### Scenario: Rendering failure falls back to static instruction
- **WHEN** a tool with `requires_project=True` is called
- **AND** the session is unbound
- **AND** rendering `_system/_project-root` raises `FileNotFoundError`
- **THEN** `_check_project_bound()` returns a `Result.failure` JSON string
  using the static `INSTRUCTION_NO_PROJECT` string as its instruction
- **AND** no exception propagates to the caller

#### Scenario: Bound session is unaffected
- **WHEN** a tool with `requires_project=True` is called
- **AND** a project is bound to the session
- **THEN** `_check_project_bound()` returns `None`
- **AND** no template rendering occurs
- **AND** the tool proceeds normally

#### Scenario: Rendered instruction is cached across calls
- **WHEN** `make_no_project_result()` is called more than once within the
  same process
- **AND** the first call successfully rendered `_system/_project-root`
- **THEN** subsequent calls reuse the cached rendered instruction rather than
  rendering the template again
