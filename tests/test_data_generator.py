"""Generate test data files for integration tests."""

from pathlib import Path


def generate_test_files(docroot: Path) -> None:
    """Generate test files in docroot organized by categories.

    Args:
        docroot: Path to the document root directory
    """
    # Guide category
    guide_dir = docroot / "guide"
    guide_dir.mkdir(parents=True, exist_ok=True)

    (guide_dir / "guidelines.md").write_text(
        "# Project Guidelines\n\n"
        "## Code Standards\n"
        "- Follow PEP 8 for Python code\n"
        "- Use type hints\n"
        "- Write docstrings\n"
    )

    (guide_dir / "guidelines-feature1.md").write_text(
        "# Feature 1 Guidelines\n\n## Implementation\n- Use async/await patterns\n- Handle errors gracefully\n"
    )

    # Lang category
    lang_dir = docroot / "lang"
    lang_dir.mkdir(parents=True, exist_ok=True)

    (lang_dir / "python.md").write_text(
        "# Python Guide\n\n## Best Practices\n- Use virtual environments\n- Leverage type hints\n- Follow PEP 8\n"
    )

    (lang_dir / "java.md").write_text(
        "# Java Guide\n\n"
        "## Best Practices\n"
        "- Use Maven or Gradle\n"
        "- Follow Java naming conventions\n"
        "- Leverage streams API\n"
    )

    (lang_dir / "spring-boot.md").write_text(
        "# Spring Boot Guide\n\n"
        "## Configuration\n"
        "- Use application.yml\n"
        "- Leverage auto-configuration\n"
        "- Use dependency injection\n"
    )

    (lang_dir / "kotlin.md").write_text(
        "# Kotlin Guide\n\n## Best Practices\n- Use data classes\n- Leverage null safety\n- Use coroutines for async\n"
    )

    # Context category
    context_dir = docroot / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    (context_dir / "jira.md").write_text(
        "# Jira Integration\n\n## Setup\n- Configure API token\n- Set project key\n- Define issue types\n"
    )

    (context_dir / "jira-settings.yaml").write_text(
        "jira:\n  url: https://example.atlassian.net\n  project: PROJ\n  api_token: ${JIRA_API_TOKEN}\n"
    )

    (context_dir / "standards.md").write_text(
        "# Development Standards\n\n"
        "## Code Review\n"
        "- All PRs require review\n"
        "- Tests must pass\n"
        "- Coverage must be maintained\n"
    )
