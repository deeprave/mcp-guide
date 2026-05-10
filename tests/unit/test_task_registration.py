"""Tests for project-scoped task class registration."""

import tomllib
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def clear_task_registry() -> None:
    """Keep task registration tests isolated from imported runtime modules."""
    from mcp_guide.decorators import clear_registered_tasks_for_testing

    clear_registered_tasks_for_testing()


class TestTaskRegister:
    """The @task_register decorator records classes without instantiating them."""

    def test_registers_task_class_without_instantiating(self) -> None:
        """Registration records the class and does not construct an instance."""
        from mcp_guide.decorators import get_registered_task_classes, task_register

        instantiated = False

        @task_register
        class RegisteredTask:
            def __init__(self) -> None:
                nonlocal instantiated
                instantiated = True

        assert get_registered_task_classes() == (RegisteredTask,)
        assert instantiated is False

    def test_duplicate_registration_is_idempotent(self) -> None:
        """Registering the same class more than once keeps one registry entry."""
        from mcp_guide.decorators import get_registered_task_classes, task_register

        class RegisteredTask:
            pass

        task_register(RegisteredTask)
        task_register(RegisteredTask)

        assert get_registered_task_classes() == (RegisteredTask,)

    def test_registration_preserves_class_order(self) -> None:
        """Task classes start in import/registration order."""
        from mcp_guide.decorators import get_registered_task_classes, task_register

        @task_register
        class FirstTask:
            pass

        @task_register
        class SecondTask:
            pass

        assert get_registered_task_classes() == (FirstTask, SecondTask)

    def test_registration_decorator_does_not_accept_task_policy(self) -> None:
        """Activation policy belongs to the task class, not the decorator."""
        from mcp_guide.decorators import task_register

        with pytest.raises(TypeError):
            task_register(flag="workflow")

    def test_vulture_treats_task_register_as_usage_site(self) -> None:
        """Static analysis config tracks project-scoped task decorators."""
        pyproject = tomllib.loads(Path("pyproject.toml").read_text())

        assert "@task_register" in pyproject["tool"]["vulture"]["ignore_decorators"]


class TestTaskInitCompatibility:
    """Existing @task_init import-time semantics stay intact."""

    def test_task_init_still_instantiates_decorated_class(self) -> None:
        """Infrastructure tasks can continue using import-time initialization."""
        from mcp_guide.decorators import task_init

        instances: list[str] = []

        @task_init
        class ImportTimeTask:
            def __init__(self) -> None:
                instances.append("created")

        assert ImportTimeTask.__name__ == "ImportTimeTask"
        assert instances == ["created"]
