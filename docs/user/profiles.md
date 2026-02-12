# Profiles

Using profiles for pre-configured project setups in mcp-guide.

## What are Profiles?

Profiles are pre-configured sets of categories and collections that can be applied to projects. They provide quick setup for common scenarios without manual configuration.

## Discovering Profiles

Ask your AI agent to list available profiles:

```
List available profiles
Show me what profiles exist
What profiles can I use?
```

## Using Profiles

Ask your AI agent to apply profiles:

```
Apply the python profile
Use the tdd profile for this project
Show me details about the jira profile
```

## Profile Behaviour

Profiles are **additive** - they add categories and collections without removing existing ones. Multiple profiles can be combined to build up complex project configurations.

## Next Steps

- **[Categories and Collections](categories-and-collections.md)** - Understanding content organisation
- **[Feature Flags](feature-flags.md)** - Configuring behaviour


Multiple profiles can be combined:

```python
use_project_profile(profile="python")
use_project_profile(profile="tdd")
use_project_profile(profile="jira")
```

Result: Python + TDD + Jira setup

### Idempotent

Applying the same profile multiple times has no additional effect:

```python
use_project_profile(profile="python")
use_project_profile(profile="python")  # No change
```

## Discovering Profiles

### List Available Profiles

```python
# List all profiles
list_profiles()

# List profiles for specific category
list_profiles(category="python")
```

### Show Profile Details

```python
# Show what a profile adds
show_profile(profile="python")
```

Output:

```
Profile: python

Categories:
- lang/python: Python language guidelines
- testing/pytest: pytest testing standards

Collections:
- python-dev: Python development context
```

## Profile Contents

### python Profile

```yaml
categories:
  lang/python:
    dir: lang/python
    patterns: ["*.md"]
    description: "Python language guidelines"

  testing/pytest:
    dir: testing/pytest
    patterns: ["*.md"]
    description: "pytest testing standards"

collections:
  python-dev:
    categories:
      - lang/python
      - testing/pytest
    description: "Python development context"
```

### tdd Profile

```yaml
categories:
  workflows/tdd:
    dir: workflows/tdd
    patterns: ["*.md"]
    description: "TDD workflow guidelines"

  testing:
    dir: testing
    patterns: ["*.md"]
    description: "Testing standards"

collections:
  tdd-workflow:
    categories:
      - workflows/tdd
      - testing
    description: "TDD workflow context"
```

### jira Profile

```yaml
categories:
  context/jira:
    dir: context/jira
    patterns: ["*.md"]
    description: "Jira workflow context"

collections:
  jira-workflow:
    categories:
      - context/jira
    description: "Jira integration context"
```

## Creating Custom Profiles

Custom profiles can be created by project administrators. See [Developer Documentation](../developer/) for details on profile creation.

## Best Practices

### When to Use Profiles

- **New projects** - Quick setup with standard categories
- **Consistent setup** - Same configuration across projects
- **Common patterns** - Established workflows and practices

### When Not to Use Profiles

- **Unique requirements** - Project needs custom categories
- **Learning** - Understanding category structure
- **Experimentation** - Testing different configurations

### Profile Selection

- **Start simple** - Apply one profile at a time
- **Verify content** - Check what profile adds before applying
- **Combine thoughtfully** - Ensure profiles complement each other
- **Document choices** - Note which profiles are used

## Examples

### Python Project Setup

```python
# Apply Python profile
use_project_profile(profile="python")

# Verify categories added
list_project(verbose=True)
```

### TDD Workflow

```python
# Apply TDD profile
use_project_profile(profile="tdd")

# Use TDD collection
get_content(expression="tdd-workflow")
```

### Combined Setup

```python
# Python project with TDD and Jira
use_project_profile(profile="python")
use_project_profile(profile="tdd")
use_project_profile(profile="jira")

# Access combined context
get_content(expression="python-dev+tdd-workflow+jira-workflow")
```

## Troubleshooting

### Profile Not Found

Check:
1. Profile name is correct (case-sensitive)
2. Profile is available (use `list_profiles()`)
3. Spelling is correct

### Profile Not Adding Categories

Verify:
1. Profile was applied successfully
2. Check project configuration
3. Verify docroot has profile content

### Unexpected Categories

If seeing unexpected categories:
1. Check which profiles were applied
2. Review profile contents
3. Verify no manual category additions

## Next Steps

- **[Categories and Collections](categories-and-collections.md)** - Understanding categories
- **[Content Management](content-management.md)** - Content organisation
- **[Getting Started](getting-started.md)** - Basic setup

