## ADDED Requirements

### Requirement: Absolute Docroot When The Config Key Is Missing
When a configuration file exists but `docroot` is absent, blank, or not a
string, the configuration service SHALL persist an absolute default beside that
configuration file. It SHALL NOT persist a current-working-directory-relative
path, and it SHALL NOT unpack packaged templates into the repository worktree
as a side effect of filling that key.

#### Scenario: Config file lacks a docroot key
- **WHEN** the configuration file is present and `docroot` is missing or blank
- **THEN** the service SHALL store an absolute path in the same directory as the
  configuration file's default docs location
- **AND** it SHALL NOT write a CWD-relative value such as `tests/fixtures/docs`

#### Scenario: First-run install uses a relative config directory
- **WHEN** first-run installation creates configuration because the file is
  missing
- **THEN** both the configuration directory and the installed docroot SHALL be
  stored as absolute paths
- **AND** the install SHALL NOT unpack templates into a git-tracked worktree
  path as a default

### Requirement: GuideRuntime Is The Sole ConfigManager Constructor
The process runtime SHALL construct the configuration service from the config
directory and docroot it is given. Application entry points, Sessions, and
feature-flag handlers SHALL NOT import or instantiate that configuration-service
class. Tests SHALL obtain a configuration service only by constructing a
process runtime.

#### Scenario: Server starts
- **WHEN** the MCP server application is constructed
- **THEN** it SHALL construct a process runtime with a config directory
- **AND** it SHALL NOT import or construct the configuration-service class

#### Scenario: Session needs project configuration
- **WHEN** a Session performs project CRUD, clone lookup, or registration
- **THEN** it SHALL obtain the configuration service from its process runtime
- **AND** the Session module SHALL NOT import the configuration-service class
