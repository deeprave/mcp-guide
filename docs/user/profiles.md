# Profiles

Profiles give you quick project setup with pre-configured categories and collections.

## What are Profiles?

Think of profiles as templates for your project. Instead of manually creating categories and collections, you can apply a profile that sets everything up for you. There are profiles for common scenarios like Python development, TDD workflows, Jira integration, and various programming languages and frameworks.

## Discovering Profiles

Ask your AI agent what's available:

```
list all project profiles
What profiles are available?
```

The agent will show you available profiles and what they add to your project.

## Using Profiles

Just ask your AI agent to apply them:

```
Apply the python profile
Use the tdd profile for this project
Add the jira profile
```

## How Profiles Work

Profiles are **additive** - they add categories and collections without removing existing ones. You can apply multiple profiles to build up your project configuration:

```
Apply the python profile
Apply the tdd profile
Apply the jira profile
```

This gives you Python + TDD + Jira setup combined.

Applying the same profile multiple times has no effect - profiles are idempotent.

