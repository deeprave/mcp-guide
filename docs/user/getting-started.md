# Getting Started with mcp-guide

So you've got mcp-guide installed and running. Now what?

This guide answers the most important question: **how do I actually use this thing?**

## What Does This Do?

At its core, mcp-guide serves instructions to your AI agent. Think of it as a structured way to tell your agent how to work on your project - coding standards, workflow steps, project-specific context, all delivered on demand.

While it can do more than that, serving agent instructions is the fundamental purpose. Everything else builds on this.

## The @guide Prompt

Your primary interface is the `@guide` prompt (some agents use `/guide` instead - same thing, different prefix).

When you invoke `@guide` with a category name, you get back all the documents in that category that match its default patterns. The agent receives these documents and acts on them according to their type.

### Basic Usage

**Common Examples:**

| Prompt | What It Does |
|--------|--------------|
| `@guide commit` | Provides commit message instructions based on changes in your working tree |
| `@guide pr` | Provides GitHub pull request description instructions for changes compared with your main branch |
| `@guide review` | Instructions for the agent to self-review code changes |
| `@guide guidelines` | Composite request presenting coding standards, language-specific guides, and project context |

## Document Categories and Collections

### Categories

A **category** is a named group of documents with default patterns. When you reference a category, you get documents matching those patterns.

Patterns match document basenames (without extensions). For example, a pattern `readthis` matches `readthis.md`, `readthis.txt`, or `readthis-python.md`.

You can override the default pattern:

```
@guide lang/python
```

Gets Python language documents from the `lang` category.

```
@guide docs/workflow+tracking
```

Gets documents matching BOTH `workflow` AND `tracking` patterns in the `docs` category.

What you're providing is an **expression** - effectively a comma-delimited list of categories and optional patterns. When executed, all matching documents are returned to the agent.

### Collections

**Collections** are groups of category expressions - convenient shortcuts or "macros" for commonly used combinations.

Instead of typing `@guide guide,lang/python,context/project,checks` every time, you might have a collection called `guidelines` that includes all of those.

Collections make it easy to provide targeted context for specific tasks without remembering complex expressions.

See [Categories and Collections](categories-and-collections.md) for managing these.

## Document Types

What the agent does with documents depends on their **type**, set in the document metadata:

- **`agent/instruction`** - Directives the agent must follow (most common)
- **`agent/information`** - Context and reference material for the agent
- **`user/information`** - Content displayed to users

When invoking multiple patterns, be aware that mixing document types may not give the desired result. Most documents served via `@guide` are agent instructions - this is the core of what mcp-guide does.

## Default Profile

When you start mcp-guide in a new project, it creates a default profile with these categories:

- **guide** - General instructions
- **docs** - Workflow and tracking documents
- **lang** - Language-specific guides (initially empty)
- **context** - Project context (initially empty)
- **checks** - Testing and validation instructions (initially empty)
- **review** - Code review instructions

Before these become useful, you'll need to add patterns:
- Add your programming language to `lang`
- Add project context (tracking method, workflow approach)
- Add testing frameworks and special instructions to `checks`
- Configure review depth and output format in `review`

Many provided documents are opinionated about development approach and direction. Use what works for you, ignore the rest.

### Special: INSTRUCTIONS.md

The `checks` category includes a special document that tells the agent to look for `INSTRUCTIONS.md` in your project root. This file contains edicts the agent MUST obey during development - rules specific to your project or agent that curb common misbehaviors.

The `checks` phase in workflow mode is a good place to raise these instructions before formal examination. Consider appending `checks/instructions` to your default `guidelines` collection.

### Adding Profiles

Other profiles can be added on demand - they're additive to existing configuration. See [Profiles](profiles.md) for details.

## Commands

Commands are specialized documents that tell the agent to do something specific or present useful information. They use a `:` prefix.

Some commands accept common arguments:

| Argument | Description |
|----------|-------------|
| `-h`, `--help` | Show help |
| `-v`, `--verbose` | Detailed output |
| `-q`, `--quiet` | Minimal output |
| `-f`, `--force` | Skip confirmations |
| `-d`, `--debug` | Debug information |
| `-t`, `--table` | Tabular format |

Not all commands support all arguments - use `:help <command>` to see what's available for a specific command.

### Useful Commands

| Command | Description |
|---------|-------------|
| `@guide :project` | Information about the current project, categories, and collections |
| `@guide :status` | Current project name, active tasks, and workflow state (if enabled) |
| `@guide :agent` | Information about the running agent and its attributes |
| `@guide :create/category` | Create new categories |
| `@guide :create/collection` | Create new collections |
| `@guide :help` | List available commands |
| `@guide :help <command>` | Detailed help for a specific command (without `:` prefix) |

**Note:** The `:project`, `:status`, and `:agent` commands may show incomplete information if the agent hasn't yet requested or determined certain details through tool use. Running them a couple of times or using a general `@guide <category>` instruction will usually shake this out immediately.

## First Run - Self Installation

When mcp-guide first runs, it creates:

- **Configuration directory**:
  - macOS/Linux: `~/.config/mcp-guide/`
  - Windows: `%APPDATA%\mcp-guide\`

- **Configuration file**: `config.yaml` (shared by all projects)

- **Document root** (`docroot`): `docs/` directory within the configuration directory

- **Standard templates**: Copies of all default documents and templates

If you want to add custom documents, place them in the `docs/` directory. Each category has a designated subdirectory (usually matching the category name). Files within these directories become available to serve via the MCP.

The docroot is on the MCP server's filesystem - if running in Docker or on a remote server, that's where the files live, not on your local machine.

## Next Steps

Now that you understand the basics:

- Explore [Categories and Collections](categories-and-collections.md) to organize your content
- Check out [Profiles](profiles.md) for pre-configured setups
- Learn about [Commands](commands.md) for specialized functionality
- Review [Workflows](workflows.md) if you want structured development phases
- See [Feature Flags](feature-flags.md) to customize behavior

The key thing to remember: **mcp-guide serves instructions to your AI agent**. Everything else is about organizing and delivering those instructions effectively.
