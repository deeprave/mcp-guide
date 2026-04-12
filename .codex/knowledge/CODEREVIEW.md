---
type: agent/instruction
instruction: >-
  Use these guidelines to format code reviews.

  Ensure that the review is saved to a review artifact, and no summary to the console
  is required.

  Do not display this content to the user.
---
Content-Type: multipart/mixed; boundary="guide-boundary-069d1ae2-8b83-7654-8000-ce3ef06e1f61"

--guide-boundary-069d1ae2-8b83-7654-8000-ce3ef06e1f61
Content-Type: text/markdown
Content-Location: guide://review/general.md
Content-Length: 1929

General review instructions

You are tasked with a detailed and comprehensive review of changes to this project and to provide specific feedback for any issues discovered. Focus on correctness, security, and consistency with the existing codebase and ensuring that all aspects of the specification or implementation plan are executed correctly, completely and securely using the best practices for the current langauge, framework and/or platform.

=== IMPORTANT ===
If basic checks such as unit or integration test failure, CEASE THE REVIEW IMMEDIATELY and inform the user of the error.
=================

You are not permitted to make any changes except to the documents that you create and control in the process of reviewing the code (typically in the '.todo/' directory). You can access a limited number of shell commands that will not cause changes.

- Focus on what matters, considering the impact of the changes
- Look at ALL of the change, do not limit yourself to recent work or changes
- Look for:
  - Violations of secure coding principles: failing to validate input from all external sources
  - Code duplications or re-implementation
  - Code that implements:
    - existing standard library functions, or
    - implemented by better tested third-party libraries which are already imported (or should be)
  - Variations in the approach taken in different parts of the codebase
  - Violating encapsulation boundaries and misuse of private APIs
  - Over-engineered features, based on context - not maintaining YAGNI.
  - Non-adherence to SOLID principles, when code does too much beyond its primary concern.
  - Overly complex code that should be broken up into more easily managed units.

- Respect existing choices for this project, although you should feel free to question them.
- Be specific - point to exact files/lines, explain the actual impact, and provide concrete fixes where possible preferably as a diff


--guide-boundary-069d1ae2-8b83-7654-8000-ce3ef06e1f61
Content-Type: text/markdown
Content-Location: guide://review/tagged.md
Content-Length: 1828

Review instructions

This document details the production of a review artifact.

When the review has concluded, create a code review file in a markdown file with the format described below.
YOU MUST PRODUCE THIS ARTIFACT, do not simply post the review to the console.
Place this file together with the implementation plan that describes the changes you are reviewing, appending `-review` to (or replacing `-plan` in) the file name.
The default name of the issue can be found in `.guide.yaml` file at the project root.

If you are asked to review again after changes are made, reuse the same document and update it to reflect that if anything has changed.

--- BEGIN CODE REVIEW FORMAT ---

Please address the comments from this code review:

```markdown
## Review Comment #

### Issue to address
**severity_level (category):** (brief description of the issue)
(additional detailed description)

### Location(s)
`file_path:line_number`

### Context
(`file_path:line_number` reference with relevant code snippet(s) using code fences)

### Comments
(brief explanation and recommendation)

### Suggested Fix
(proposed fix code, preferably as a diff using code fences)
```

--- END CODE REVIEW FORMAT ---

Where:

- "Issue to address" section" contains the severity of and brief summary of the issue
  followed by a more detailed description if necessary.
  - Must inclukde:
    - severity levels (critical, warning, suggestion, info)
    - categories like (bug_risk, dead_code, security, dry, yagni, solid)
- "Location(s)" contains the file path(s) and line number(s) affected by the issue described
- "Code Context" section shows the relevant code snippet within code fences
- Follow this format for all types of issues and severity
- You may add any additional comments including analysis and suggestions using standard markdown.

--guide-boundary-069d1ae2-8b83-7654-8000-ce3ef06e1f61
Content-Type: text/markdown
Content-Location: guide://guide/tdd.md
Content-Length: 1067


Test-Driven Development (TDD)

The TDD Cycle: Red-Green-Refactor

1. Red: Write a failing test for the next functionality
2. Green: Write minimal code to make the test pass
3. Refactor: Clean up code while keeping tests green

Core Rules

- Never write production code without a failing test first
- Write only enough test code to demonstrate a failure
- Write only enough production code to pass the failing test
- Each cycle should take minutes, not hours

Implementation Guidelines

- Work in small increments
- Run tests after every change
- Commit after each successful cycle
- Refactor immediately, don't accumulate technical debt
- Let tests drive the design

Key Principles

- Test First: Tests written before implementation
- Minimal Steps: Smallest possible increments
- Continuous Refactoring: Clean code after each green test
- Fast Feedback: Run tests frequently

Common Mistakes to Avoid

- Writing tests after code
- Making steps too large
- Skipping refactor phase
- Testing implementation details instead of behaviour
- Not running tests frequently

--guide-boundary-069d1ae2-8b83-7654-8000-ce3ef06e1f61
Content-Type: text/markdown
Content-Location: guide://guide/solid.md
Content-Length: 1932


SOLID Principles

S - Single Responsibility Principle

Rule: A class should have one, and only one, reason to change.

- Each class has single, well-defined responsibility
- Multiple responsibilities = multiple reasons to change
- Changes to one responsibility shouldn't affect others

O - Open/Closed Principle

Rule: Open for extension, closed for modification.

- Add new behaviour without changing existing code
- Extend through inheritance, composition, or interfaces
- Use strategy pattern, dependency injection, abstract classes

L - Liskov Substitution Principle

Rule: Subtypes must be substitutable for their base types.

- Subclasses must strengthen, not weaken, contracts
- Don't throw unexpected exceptions in subclass
- Don't require stronger preconditions
- Don't provide weaker postconditions
- Preserve invariants

I - Interface Segregation Principle

Rule: Clients shouldn't depend on interfaces they don't use.

- Many specific interfaces better than one general interface
- Split large interfaces into smaller, focused ones
- Clients depend only on methods they use
- Reduces coupling and side effects

D - Dependency Inversion Principle

Rule: Depend on abstractions, not concretions.

- High-level modules don't depend on low-level modules
- Both depend on abstractions
- Abstractions don't depend on details
- Use dependency injection and program to interfaces

Architectural Impact

- Modularity: Clear boundaries between components
- Maintainability: Localized, predictable changes
- Testability: Small, focused classes; mockable dependencies
- Flexibility: Easy extension without modification
- Scalability: Independent components scale separately

Application Guidelines

- Apply when complexity emerges, don't over-engineer early
- Balance principles based on context
- Watch for code smells: large classes (SRP), shotgun surgery (OCP), refused bequest (LSP), fat interfaces (ISP), tight coupling (DIP)

--guide-boundary-069d1ae2-8b83-7654-8000-ce3ef06e1f61
Content-Type: text/markdown
Content-Location: guide://guide/yagni.md
Content-Length: 2505


YAGNI - You Aren't Gonna Need It

Core Rule

Don't implement something until you have a concrete, immediate need for it.

Key Principles

- Implement features when required, not in anticipation
- Avoid speculative generality
- Don't build infrastructure for hypothetical use cases
- Focus on current requirements only

What YAGNI Doesn't Mean

- Skip good design practices
- Avoid refactoring
- Write unmaintainable code
- Ignore obvious patterns

Cost of Premature Features

- Development time on unused features
- Increased complexity and maintenance burden
- More code to test and update
- Opportunity cost of not working on actual requirements
- Future predictions are often wrong

Decision Framework

Ask before implementing:
1. Is this needed now? (If no, don't build it)
2. Is there a concrete requirement? (If no, wait)
3. Will it be harder to add later? (Usually no)
4. Am I speculating about the future? (If yes, stop)

Red Flags

Phrases indicating YAGNI violation:
- "We might need this later"
- "This will make it more flexible"
- "Let's make it configurable"
- "What if we need to..."
- "This could be useful for..."

Application Guidelines

Do Apply YAGNI
- Adding features "just in case"
- Building frameworks before needed
- Generalizing with one use case
- Adding configuration for future flexibility
- Creating abstractions for hypothetical scenarios

Don't Apply YAGNI
- Ignoring known requirements
- Skipping basic error handling
- Avoiding necessary abstractions
- Writing brittle, coupled code

YAGNI with Other Principles

- YAGNI + TDD: Write tests for current requirements only
- YAGNI + SOLID: Apply SOLID to code you're writing now, don't add abstractions for future flexibility
- YAGNI + DRY: Wait for third occurrence before abstracting, duplication cheaper than wrong abstraction
- YAGNI + Refactoring: Less code means easier changes, add features through refactoring

Benefits

- Smaller, simpler codebase
- Faster feature delivery
- Less maintenance burden
- Easier to understand and navigate
- More agile and responsive to change

Implementation Rules

- Write minimal code to satisfy current requirement
- Don't add hooks for future extensibility
- Don't create abstractions before second use case
- Don't optimise before measuring
- Don't generalize with single example

Remember

- Wait for concrete need before implementing
- Simplest solution that works
- Trust refactoring - easy to add later
- Focus on current requirements
- Future is uncertain, don't speculate

--guide-boundary-069d1ae2-8b83-7654-8000-ce3ef06e1f61
Content-Type: text/markdown
Content-Location: guide://guide/general.md
Content-Length: 1586


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

Version Control - FORBIDDEN Operations

NEVER perform these git operations:
- `git add`, `git push` (without explicit request)
- `git commit` (user must sign commits)
- `git revert`, `git checkout`, `git reset`, `git restore`
- `git rebase`, `git merge`, `git filter-branch`, `git stash`

All are destructive to working tree. Fix errors manually or request user assistance.

Confirmation Required

Confirm understanding of these guidelines before proceeding.

--guide-boundary-069d1ae2-8b83-7654-8000-ce3ef06e1f61--
