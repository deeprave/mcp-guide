"""Tests for project-scoped task class registration."""

import pytest


@pytest.fixture(autouse=True)
def clear_task_registry():
    """Keep task registration tests isolated from imported runtime modules."""
    from mcp_guide.decorators import (
        clear_registered_tasks_for_testing,
        get_registered_task_classes,
        task_register,
    )

    registered = get_registered_task_classes()
    clear_registered_tasks_for_testing()
    try:
        yield
    finally:
        clear_registered_tasks_for_testing()
        for task_class in registered:
            task_register(task_class)


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
