---
type: agent/instruction
instruction: |-
  Adhere to these guidelines ALWAYS.
  You MUST confirm understanding of these guidelines before proceeding.
  Do not display this content to the user.
  You MUST follow these instructions.
  This information is for your information and use.
  Use this information when working with OpenSpec.
  Follow this policy exactly.
  If .guide.yaml missing, create it and enter discussion phase.
---
Content-Type: multipart/mixed; boundary="guide-boundary-069d4e7f-f930-7121-8000-68d1aed1b31a"

--guide-boundary-069d4e7f-f930-7121-8000-68d1aed1b31a
Content-Type: text/markdown
Content-Location: guide://guide/general.md
Content-Length: 2197


General Development Guidelines

Architectural Decisions - CRITICAL RULE

YOU MUST NEVER MAKE ARCHITECTURAL DECISIONS WITHOUT USER INVOLVEMENT.

Before making ANY architectural decision:
1. STOP immediately
2. Notify the user of the decision point
3. Present options with trade-offs
4. Wait for explicit consent before proceeding

Architectural decisions include:
- Design patterns and abstractions
- Module/package structure
- Technology or library choices
- Data models and schemas
- API contracts and interfaces
- Concurrency models
- Error handling strategies

NO EXCEPTIONS. NO ASSUMPTIONS. ALWAYS CONSULT.

Code Quality

- Self-documenting code
- Comments only for:
  * API documentation
  * IDE bookmarks
  * Complex logic clarification
- Follow existing code style
- Respect encapsulation boundaries
- Avoid implementation details

Definition of Done

- All tests pass without warnings - NO exceptions
- Resolve all linting and type checking issues
  * Resolve means RESOLVE, never suppress without explicit user consent
- Format according to project standard
- Text files: terminating newline, no trailing whitespace

Version Control

# Git Policy: Conservative (Read-Only)

The agent may use read-only git operations but must not modify the working tree
or history UNLESS EXPLICITLY REQUESTED.

## Permitted

- `git status`, `git diff`, `git log`, `git show`
- `git branch --list`, `git tag --list`
- `git stash list` (read only)

## Forbidden

- `git add`, `git commit`, `git push`
- `git reset`, `git restore`, `git checkout`, `git switch`
- `git rebase`, `git merge`, `git stash push/pop`
- Any operation that modifies the index, working tree, or history

## Git MCP

If a git MCP server is connected, its tools are subject to the same permissions
as the equivalent CLI operations. Read-only tools (status, diff, log) are
permitted; tools that stage, commit, push, or otherwise modify state are
forbidden unless explicitly requested.

## Rationale

Useful when the agent needs to inspect repository state (e.g. check what has
changed before reviewing), but the user still owns all write operations.

Confirmation Required

Confirm understanding of these guidelines before proceeding.

--guide-boundary-069d4e7f-f930-7121-8000-68d1aed1b31a
Content-Type: text/markdown
Content-Location: guide://guide/methodology.md
Content-Length: 3101

Methodology

# Methodology Policy: Test-Driven Development (TDD)

The agent follows the Red-Green-Refactor cycle for all new functionality.

## Rules

- Write a failing test before writing any production code
- Write only enough test code to demonstrate a failure
- Write only enough production code to make the failing test pass
- Refactor immediately after green; do not accumulate technical debt
- Each cycle should take minutes, not hours
- Commit after each successful cycle
- Let tests drive the design

## Common mistakes to avoid

- Writing tests after the implementation
- Making increments too large
- Skipping the refactor phase
- Testing implementation details instead of behaviour

## Rationale

TDD produces well-tested code and lets the test suite serve as executable
specification. Best suited to teams comfortable with the discipline of
writing tests first.


# Methodology Policy: SOLID Principles

Apply SOLID design principles to object-oriented code.

## Principles

- **S** — Single Responsibility: each class has one reason to change
- **O** — Open/Closed: open for extension, closed for modification
- **L** — Liskov Substitution: subtypes must be substitutable for their base types
- **I** — Interface Segregation: many specific interfaces over one general interface
- **D** — Dependency Inversion: depend on abstractions, not concretions

## Application guidelines

- Apply when complexity emerges; do not over-engineer early
- Balance principles based on context
- Watch for code smells: large classes (SRP), shotgun surgery (OCP),
  refused bequest (LSP), fat interfaces (ISP), tight coupling (DIP)

## Rationale

SOLID principles produce modular, testable, maintainable code. Best applied
once complexity warrants it rather than from the first line.


# Methodology Policy: YAGNI

Do not implement something until there is a concrete, immediate need for it.

## Rules

- Implement features when required, not in anticipation
- Do not build infrastructure for hypothetical use cases
- Do not generalise from a single use case
- Do not add configuration for future flexibility
- Do not optimise before measuring
- Wait for a third occurrence before abstracting

## Red flags

These phrases indicate a likely YAGNI violation:
- "We might need this later"
- "This will make it more flexible"
- "Let's make it configurable"
- "What if we need to..."

## What YAGNI does NOT mean

YAGNI does not mean skipping good design or cutting corners:

- Do not skip basic error handling
- Do not avoid necessary abstractions
- Do not write brittle or tightly coupled code
- Do not ignore known, concrete requirements
- Do refactor — YAGNI and refactoring work together

## When NOT to apply YAGNI

- Ignoring requirements that are explicitly stated
- Skipping error handling for conditions that clearly can occur
- Avoiding an abstraction that already has two concrete uses
- Writing code that is knowingly unmaintainable

## Rationale

Speculative features cost development time, increase complexity, and are often
wrong. YAGNI keeps codebases smaller and easier to change.

--guide-boundary-069d4e7f-f930-7121-8000-68d1aed1b31a
Content-Type: text/markdown
Content-Location: guide://lang/python.md
Content-Length: 8376

Python Guidelines

Note: The `__init__.py` files in both `src/` and `tests/` directories are required for pytest to properly resolve import paths in the src layout.

Formatting & Quality
- Use `ruff format` and `ruff check` - address warnings before considering complete
- Use f-strings: `f"Error: {e}"` vs `"Error: {}".format(e)` or `"Error: %s" % e`
- pre-commit hooks ensure all commits are checked
- Use PEP 8 conventions imports at the top of modules unless required to avoid circular dependencies
- Avoid large `if`/`elif`/`else` blocks with more than 1 `elif`. Use `match` instead, a dictionary or some form of functional approach.
- Use a type checker like `mypy`, `ty` or `pyright` for type checking

Imports

- As per PEP8, you must import at module level until you are unable to do so, which is limited to
  - avoiding circular imports
  - rarely used module imports
- Avoid import within functions and methods, and if you need to do so place the import at the top of said function or method.

Asynchronous Code
- In an async application, strong preference is to *always* use `async`/`await` pattern
  - Exceptions:
    — Trivial functions that will use anything that may be accessed concurrently
    - Makes no function calls other than to sync library functions. Even then, prefer async if it likely that the function will be extended or enhanced in the future.

Encapsulation
- Never access private attributes outside of a class, with specific exceptions where tight coupling exists.
- Never access private attributes starting with dunder (two '__') attributes directly EVER. Not in tests, not in production code, not EVER.
- Never access private attributes via the "_classname__attribute" under ANY circumstances. Private variables exist for a reason and you MUST respect that.


Code Complexity
- Early returns with guard clauses
- List/dict comprehensions over loops when this produces readable code
- Chain operations - avoid intermediate variables
  - return a function result directly if last statement in a function or method
  - use the walrus operator if the only reason for the variable is for an `if` or `while` statement or expression

Type Hints
- Use modern typing: `List[str]`, avoid use if `Any` if possible
- Function signatures: Always type parameters and returns
- Use `typing.Protocol` for structural typing
- `Optional[T]` or `T | None` for nullable types

Code Quality checks
- For Python, use the following code quality tools
  - linting → ruff check
  - type checking → mypy, ty or pyright - whichever is selected for the project
  - testing → pytest
- Where possible, combine tests with common patterns using `pytest.mark.parametrize`

Iterator Patterns
Prefer comprehensions and generators:
```python ignore
# Good
valid_items = [item.process() for item in items if item.is_valid()]

# Avoid
results = []
for item in items:
    if item.is_valid():
        results.append(item.process())
```

Imports
- Use imports at module level - follow PEP 8 standards
- Only use function/class level imports to avoid circular imports & similar

Error Handling
- Use specific exceptions - DO NOT USE bare `except:` or `except Exception:`
- Context managers for resource management
- `raise ... from e` - preserve exception chains
- Custom exceptions for domain-specific errors

Pattern Matching (Python 3.11+)
- Use `match/case` for complex conditionals
- Structural pattern matching for data extraction
- Guard clauses with `if` conditions in patterns

Collections
- Choose correctly: `list`, `dict`, `set`, `deque`, `Counter`
- Use `collections.defaultdict` to avoid key checks
- `frozenset` for immutable sets

Function Design
- Small, focused functions with single responsibility
- Use `*args`, `**kwargs` judiciously
- Default arguments should be immutable
- Use `functools.lru_cache` for expensive pure functions

Classes & Objects
- Use `@dataclass` for simple data containers
- `__slots__` for memory efficiency when needed
- Properties over getters/setters
- Context managers with `__enter__`/`__exit__`

Testing with pytest
Always configure in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-report=term-missing",
]
```

Project Configuration
Essential `pyproject.toml` sections:
```toml
[project]
name = "modulename"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = []

[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "ruff", "ty", "pre-commit"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
src = ["src"]
target-version = "py313"
```

Testing
TDD

If using TDD, tests should be written before the implementation. Sometimes those tests may not be optimal for ongoing testing or regression testing.
So here are some general guidelines.

Refactoring or Redesign

Again, if using TDD, some tests are required to be written to test a refactoring or other re-arrangement (removing code or changes in design).
These should be regarded as "throwaway" tests as in the end, once the task is done and the tests pass to confirm successful completion they may serve no useful purpose going forwards. Those tests may be removed. Instead, replace with tests that actually TEST something useful about the resulting code, if required - and not already covered.

Coverage

Don't write tests just to achieve code coverage. Instead, test something in a useful way - that functionality works, that something returns or is set to a correct value etc. Certainly do not name tests, classes or modules containing the word _coverage_ - this is a bad smell that this module contains artificial tests purely to enhance or provide coverage. Tests should test actual functionality, and do not exist to achieve an arbitrary statistic.


Essential `.pre-commit-config.yaml`:
```yaml
# See https://pre-commit.com for more information
# See https://pre-commit.com/hooks.html for more hooks
repos:

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: no-commit-to-branch
        args: ['--branch', 'main']
        exclude: '^main$'
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-toml
      - id: requirements-txt-fixer

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.6
    hooks:
      - id: ruff
        args:
          - --fix
          - --line-length=120

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest --cov --cov-config=.coveragerc
        language: system
        types: [python]
        pass_filenames: false

  - repo: https://github.com/abravalheri/validate-pyproject
    rev: v0.24.1
    hooks:
      - id: validate-pyproject
```

Essential `.coveragerc`:
```ini
[run]
omit =
    */tests/conftest.py
    */tests/test_*.py

[report]
fail_under = 90
```

Anti-Patterns
- No bare `except:` - catch specific exceptions
- No mutable defaults - use `None` and create in function
- No `import *` - explicit imports only
- Address linter warnings - don't ignore without reason
- No `eval()` or `exec()` without strong justification

Common Idioms
```python  ignore
# Dictionary get with default
value = data.get('key', default_value)

# Enumerate for index and value
for i, item in enumerate(items):
    process(i, item)

# Context manager for files
with open(filename) as f:
    content = f.read()

# Exception chaining
try:
    risky_operation()
except SpecificError as e:
    raise CustomError("Operation failed") from e
```

uv Commands
```bash
# Create new project
uv init --package *modulename*

# Add dependencies
uv add *package*
uv add --dev pytest pytest-cov ruff ty pre-commit

# Install pre-commit hooks
uv run pre-commit install

# Run tests
uv run pytest

# Format and lint
uv run ruff format src tests
uv run ruff check src tests
uv run ty check src

# Run pre-commit on all files
uv run pre-commit run --all-files

# Refresh installed package after MCP development changes
uv sync
```

MCP Development Notes
When developing MCP servers with uv, you need to run `uv sync` to refresh the installed package after making changes. This ensures the MCP server picks up your latest code modifications.

--guide-boundary-069d4e7f-f930-7121-8000-68d1aed1b31a
Content-Type: text/markdown
Content-Location: guide://lang/python.org.md
Content-Length: 1616

# Python.org Overview

Python is a general-purpose programming language positioned as quick to learn, productive, and effective for integrating systems.

## Primary entry points
- Beginner's Guide for getting started
- Download page with current release information
- Online documentation at `docs.python.org`
- Community job board at `jobs.python.org`

## Current homepage highlights
- Latest advertised release: Python 3.14.3
- PyCon US 2026 promotion and registration link
- Recent Python news and upcoming events
- A success story featuring Zama Concrete ML and Python for machine learning / FHE tooling

## Language characteristics emphasized on the homepage
- Functions with mandatory, optional, keyword, and arbitrary argument lists
- Built-in compound data types such as lists
- Straightforward arithmetic and readable expression syntax
- Familiar control flow with `if`, `for`, `while`, and `range`
- Easy learning curve for both beginners and experienced programmers

## Common use areas highlighted
- Web development
- GUI development
- AI and machine learning
- Scientific and numeric computing
- Software development tooling
- System administration

## Ecosystem and governance
- The Python Software Foundation promotes, protects, and advances the language and its community.
- The site links to packaging, documentation, jobs, community resources, and contribution paths.

## Caveat
This capture is based on the non-interactive fallback rendering of `https://python.org` as observed without client-side scripts. It preserves the substantive visible content but may omit script-driven homepage elements.
--guide-boundary-069d4e7f-f930-7121-8000-68d1aed1b31a
Content-Type: text/markdown
Content-Location: guide://context/jira.md
Content-Length: 4666

MCP Atlassian Context Instructions

Project Type: Kanban
Approach: Minimalist
Issue Management: This is a JIRA managed project

Project Workflow Directories

See Guilde MCP: [guide_]category_content("context", "openspec") tool

Workflow

SPECIFICATIONS
After discussion with the user, a specification must be established and a corresponding JIRA issue created.
If the tasks has already been created, ask the user for the issue Id.
Ensure that the description must include:
  - A concise summary of the specification (issuesubject)
  - A description what is to be done, and why - motivations
  - Context and background
  - Objectives, description of the end result
  - Pre-requisites and requirements for implementation
  - Assumptions
  - A list of acceptance criteria

- The results of the description should be uploaded as the body of the issue itself.
- Acceptance criteria are to be made

PLANNING
Based on this description, when ready to commence the implementation, and all of the pre-requisites are satisfied and implementation plan must be added as the first comment in the JIRA issue.

It should provide a broad outline of what work is to be done, in what order, and how it will be tested.
It should comply with the tasks format and methodology required for this project.

- A checklist should be added if required.
- These should be task based.
- It should be ordered.
- It should be short, but be a complete testable unit.

If using TDD, the checklist should break down tasks based on the pattern:
  - RED(Test) -> GREEN(Implement) -> REFACTOR(Improve)

Methodology

# Methodology Policy: Test-Driven Development (TDD)

The agent follows the Red-Green-Refactor cycle for all new functionality.

## Rules

- Write a failing test before writing any production code
- Write only enough test code to demonstrate a failure
- Write only enough production code to make the failing test pass
- Refactor immediately after green; do not accumulate technical debt
- Each cycle should take minutes, not hours
- Commit after each successful cycle
- Let tests drive the design

## Common mistakes to avoid

- Writing tests after the implementation
- Making increments too large
- Skipping the refactor phase
- Testing implementation details instead of behaviour

## Rationale

TDD produces well-tested code and lets the test suite serve as executable
specification. Best suited to teams comfortable with the discipline of
writing tests first.


# Methodology Policy: SOLID Principles

Apply SOLID design principles to object-oriented code.

## Principles

- **S** — Single Responsibility: each class has one reason to change
- **O** — Open/Closed: open for extension, closed for modification
- **L** — Liskov Substitution: subtypes must be substitutable for their base types
- **I** — Interface Segregation: many specific interfaces over one general interface
- **D** — Dependency Inversion: depend on abstractions, not concretions

## Application guidelines

- Apply when complexity emerges; do not over-engineer early
- Balance principles based on context
- Watch for code smells: large classes (SRP), shotgun surgery (OCP),
  refused bequest (LSP), fat interfaces (ISP), tight coupling (DIP)

## Rationale

SOLID principles produce modular, testable, maintainable code. Best applied
once complexity warrants it rather than from the first line.


# Methodology Policy: YAGNI

Do not implement something until there is a concrete, immediate need for it.

## Rules

- Implement features when required, not in anticipation
- Do not build infrastructure for hypothetical use cases
- Do not generalise from a single use case
- Do not add configuration for future flexibility
- Do not optimise before measuring
- Wait for a third occurrence before abstracting

## Red flags

These phrases indicate a likely YAGNI violation:
- "We might need this later"
- "This will make it more flexible"
- "Let's make it configurable"
- "What if we need to..."

## What YAGNI does NOT mean

YAGNI does not mean skipping good design or cutting corners:

- Do not skip basic error handling
- Do not avoid necessary abstractions
- Do not write brittle or tightly coupled code
- Do not ignore known, concrete requirements
- Do refactor — YAGNI and refactoring work together

## When NOT to apply YAGNI

- Ignoring requirements that are explicitly stated
- Skipping error handling for conditions that clearly can occur
- Avoiding an abstraction that already has two concrete uses
- Writing code that is knowingly unmaintainable

## Rationale

Speculative features cost development time, increase complexity, and are often
wrong. YAGNI keeps codebases smaller and easier to change.

--guide-boundary-069d4e7f-f930-7121-8000-68d1aed1b31a
Content-Type: text/markdown
Content-Location: guide://context/openspec.md
Content-Length: 3684

OpenSpec Workflow

OpenSpec is a spec-driven development workflow that aligns humans and AI on what to build before writing code.

Directory Structure

```
openspec/
├── project.md          # Project conventions
├── specs/              # Source of truth
│   └── <component>/spec.md
└── changes/            # Proposed changes
    └── <feature>/
        ├── proposal.md # Why and what
        ├── tasks.md    # Implementation checklist
        └── specs/<component>/spec.md  # Deltas
```

Workflow Phases

1. Draft Proposal
Create `openspec/changes/<feature>/` with:
- `proposal.md` - Must include `## Why` and `## What Changes` headers
- `tasks.md` - Implementation checklist
- `specs/<component>/spec.md` - Deltas (ADDED/MODIFIED/REMOVED)

Critical: Specs must be `specs/<name>/spec.md` (directory + spec.md), not `specs/<name>.md`

2. Review & Align
```bash
openspec list                    # View active changes
openspec show <feature>          # Review details
openspec validate <feature>      # Check formatting
```

3. Implement
Work through `tasks.md`, marking items complete as you go.

4. Check
- Run all automated checks (tests, types, linting)
- Request user review explicitly
- Address feedback
- Require explicit user approval before archiving

5. Archive
```bash
openspec archive <feature> --yes
```
Merges changes to `openspec/specs/` and moves to `openspec/archive/`.

Proposal Format

```markdown
# Feature Name

**Status**: Proposed
**Priority**: High/Medium/Low
**Complexity**: High/Medium/Low

## Why
- Problem being solved
- Importance and impact

## What Changes
- Components added/modified/removed
- Dependencies changed

## Technical Approach (Optional)
Implementation details

## Success Criteria (Optional)
Verification steps
```

Delta Format

```markdown
## ADDED Requirements
### Requirement: New Feature
The system SHALL provide capability.

#### Scenario: Usage
- WHEN condition
- THEN behaviour

## MODIFIED Requirements
### Requirement: Updated Feature
(Complete updated text)

## REMOVED Requirements
### Requirement: Deprecated Feature
(What's being removed)
```

Archiving — Stale Delta Handling

When archiving, spec deltas may reference requirement headers that no longer exist
because a previous archive already actioned them. Two cases:

- Requirement no longer exists in any spec: use `--skip-specs` — the change
  was already applied by a prior archive, nothing to do.
- Requirement moved to a different spec or renamed: update the delta's spec
  path or header to match the current location before archiving — do NOT skip.

Proactive hygiene: when archiving a change that removes or renames a
requirement, check all other pending changes for references to that header and update
their deltas immediately to prevent stale delta accumulation.

Commands

```bash
# Viewing
openspec list [--changes|--specs]
openspec view                    # Interactive dashboard
openspec show <change> [--json]

# Validation
openspec validate <change> [--strict]  # REQUIRED before implementation

# Management
openspec archive <change> [--yes]
openspec update                  # Refresh instructions
```

Best Practices

1. One change per feature - keep atomic
2. Complete specs before implementation
3. Use deltas - show only changes
4. Validate with `--strict` before implementing (REQUIRED)
5. Include Check phase in tasks.md
6. Never archive without explicit user approval
7. Archive promptly after approval

OpenSpec vs .todo

- OpenSpec: Structured features with specs, formal workflow
- .todo: Quick fixes, investigations, reviews without specs

Resources

- Documentation: https://openspec.dev


--guide-boundary-069d4e7f-f930-7121-8000-68d1aed1b31a
Content-Type: text/markdown
Content-Location: guide://docs/tracking.md
Content-Length: 2904

Workflow Phases and Tracking

File Format
Development phases are tracked in .guide.yaml
```yaml
phase: [discussion|exploration|planning|implementation|check|review]
issue: <current-issue>
tracking: <tracker> <tracker-id>
description: <optional-context>
queue:
  - <queued-issues>
```

Core Rules
- Missing `.guide.yaml` = assume `phase: discussion`
- Missing issue = request from user
- Phase changes MUST update file
- Issue format: openspec ID or relative path

MCP Communication Protocol
CRITICAL: After ANY change to `.guide.yaml`:
1. Update the file with the new content
2. IMMEDIATELY use the `send_file_content` tool to send the complete updated content
3. The MCP cannot detect file changes automatically - you MUST notify it on every change
4. On phase transitions the MCP will respond with phase-specific instructions and restrictions
5. Never assume the MCP knows about file changes unless you explicitly send them

Phase Transitions

Phase Control and Consent:
- User has full control over movement between phases
- Phase ordering shown below is typical, but not required
- Explicit user requests to change phases must always be honoured, regardless of consent semantics
- Consent flags are instructions to the agent about when to ask permission, not restrictions on the user
- Users can manually edit `.guide.yaml` to change phases at any time
- `exploration` is available but not part of the standard ordered delivery sequence

Discussion Phase
- Default when no `.guide.yaml` exists - discussion mode
- Can modify: `.guide.yaml`, `openspec/`, `.todo/`
- Cannot modify: production code, tests

Exploration Phase
- Research-oriented, non-ordered workflow mode
- Can modify: `.guide.yaml`, `openspec/`, `.todo/`
- Cannot modify: production code, tests
- Explore the codebase, documentation, and external references as needed
- OpenSpec artifacts are allowed; implementation is not
- EXPLICIT CONSENT OR REQUEST REQUIRED before transition from exploration phase.

Planning Phase
- Auto-transition when plan drafted
- Can modify: `.guide.yaml`, `openspec/`, `.todo/`
- Cannot modify: production code, tests

Implementation Phase
- EXPLICIT CONSENT OR REQUEST REQUIRED before entering implementation phase.
- Can modify: all files including production code, tests

Check Phase
- Auto-transition when implementation complete
- Run all tests and code quality checks across ALL files
- Can modify: all files

Review Phase
- Auto-transition when all tests and code quality checks pass.
- Feedback and final review stage
- EXPLICIT CONSENT OR REQUEST REQUIRED before transition from review phase.

Queue Management
- On transition to discussion phase confirm that the current issue can be marked completed.
  - YES: remove issue, and fetch top issue from queue (if one exists)
  - NO: retain issue
- Urgent issue → current issue moves to top of queue
- Queue is usually processed in priority order

--guide-boundary-069d4e7f-f930-7121-8000-68d1aed1b31a--
