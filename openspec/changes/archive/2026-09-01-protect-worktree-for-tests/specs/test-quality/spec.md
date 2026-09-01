## ADDED Requirements

### Requirement: Worktree Modification Guard During Tests
The test suite SHALL abort the session if a test modifies a path inside the
repository worktree that is not ignored by git. Production XDG configuration
and docroot paths SHALL remain guarded as they are today.

The guard SHALL ignore paths that git would ignore, including root and nested
`.gitignore` rules, so expected generated files such as virtual environments,
bytecode, and coverage output do not fail the suite. The guard SHALL NOT itself
write tracked files into the worktree.

#### Scenario: Test writes a tracked worktree path
- **WHEN** a test creates or modifies a non-gitignored file under the repository
  root
- **THEN** the test session SHALL terminate with a failure that names the path
- **AND** the production XDG guard SHALL still apply

#### Scenario: Test writes a gitignored path
- **WHEN** a test creates or modifies a path that git ignores
- **THEN** the test session SHALL continue
- **AND** the worktree guard SHALL not treat that write as a violation

#### Scenario: Production XDG path is modified
- **WHEN** a test modifies a captured production configuration or docroot path
- **THEN** the test session SHALL terminate as it does today
