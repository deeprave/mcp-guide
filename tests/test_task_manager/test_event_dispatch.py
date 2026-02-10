"""Tests for event dispatch refactoring."""

from mcp_guide.render.content import RenderedContent
from mcp_guide.render.frontmatter import Frontmatter
from mcp_guide.task_manager.manager import EventResult, aggregate_event_results


def _make_rendered_content(content: str, instruction: str) -> RenderedContent:
    """Helper to create RenderedContent with instruction."""
    from pathlib import Path

    fm = Frontmatter({"instruction": instruction})
    return RenderedContent(
        frontmatter=fm,
        frontmatter_length=0,
        content=content,
        content_length=len(content),
        template_path=Path("test.mustache"),
        template_name="test",
    )


class TestEventResult:
    """Test EventResult dataclass."""

    def test_event_result_with_message(self):
        """Test EventResult with simple message."""
        result = EventResult(result=True, message="Success")
        assert result.result is True
        assert result.message == "Success"
        assert result.rendered_content is None

    def test_event_result_with_rendered_content(self):
        """Test EventResult with rendered content."""
        rendered = _make_rendered_content("Test content", "Test instruction")
        result = EventResult(result=True, rendered_content=rendered)
        assert result.result is True
        assert result.message is None
        assert result.rendered_content == rendered

    def test_event_result_failure(self):
        """Test EventResult with failure."""
        result = EventResult(result=False, message="Failed")
        assert result.result is False
        assert result.message == "Failed"


class TestAggregateEventResults:
    """Test aggregate_event_results function."""

    def test_empty_list(self):
        """Test empty list returns Result.ok with blank instruction."""
        result = aggregate_event_results([])
        assert result.success is True
        assert result.value is None
        assert result.message is None
        assert result.instruction == ""

    def test_single_result_with_message(self):
        """Test single EventResult with message."""
        event_result = EventResult(result=True, message="Success")
        result = aggregate_event_results([event_result])
        assert result.success is True
        assert result.message == "Success"
        assert result.value is None

    def test_single_result_with_rendered_content(self):
        """Test single EventResult with rendered content."""
        rendered = _make_rendered_content("Test content", "Test instruction")
        event_result = EventResult(result=True, rendered_content=rendered)
        result = aggregate_event_results([event_result])
        assert result.success is True
        assert result.value == "Test content"
        assert result.instruction == "Test instruction"

    def test_single_result_failure(self):
        """Test single EventResult with failure."""
        event_result = EventResult(result=False, message="Failed")
        result = aggregate_event_results([event_result])
        assert result.success is False
        assert result.error == "Failed"

    def test_multiple_results_all_success(self):
        """Test multiple EventResults all successful."""
        results = [
            EventResult(result=True, message="First"),
            EventResult(result=True, message="Second"),
        ]
        result = aggregate_event_results(results)
        assert result.success is True
        assert "First" in result.message
        assert "Second" in result.message

    def test_multiple_results_with_failure(self):
        """Test multiple EventResults with one failure - success takes precedence."""
        results = [
            EventResult(result=True, message="Success"),
            EventResult(result=False, message="Failed"),
        ]
        result = aggregate_event_results(results)
        assert result.success is True  # At least one succeeded
        assert result.message == "Success"  # Only success messages aggregated

    def test_multiple_results_with_rendered_content(self):
        """Test multiple EventResults with rendered content."""
        results = [
            EventResult(result=True, rendered_content=_make_rendered_content("First", "Inst1")),
            EventResult(result=True, rendered_content=_make_rendered_content("Second", "Inst2")),
        ]
        result = aggregate_event_results(results)
        assert result.success is True
        assert "First" in result.value
        assert "Second" in result.value
        assert "Inst1" in result.instruction or "Inst2" in result.instruction

    def test_message_deduplication(self):
        """Test duplicate messages are deduplicated."""
        results = [
            EventResult(result=True, message="Same message"),
            EventResult(result=True, message="Same message"),
            EventResult(result=True, message="Different"),
        ]
        result = aggregate_event_results(results)
        assert result.success is True
        # Should only contain "Same message" once
        assert result.message.count("Same message") == 1
        assert "Different" in result.message

    def test_instruction_deduplication(self):
        """Test duplicate instructions are deduplicated."""
        results = [
            EventResult(result=True, rendered_content=_make_rendered_content("A", "Same")),
            EventResult(result=True, rendered_content=_make_rendered_content("B", "Same")),
            EventResult(result=True, rendered_content=_make_rendered_content("C", "Different")),
        ]
        result = aggregate_event_results(results)
        assert result.success is True
        # Should deduplicate instructions
        assert result.instruction.count("Same") == 1
        assert "Different" in result.instruction

    def test_mixed_rendered_and_non_rendered(self):
        """Test mix of rendered content and simple messages."""
        results = [
            EventResult(result=True, message="Simple"),
            EventResult(result=True, rendered_content=_make_rendered_content("Rendered", "Inst")),
        ]
        result = aggregate_event_results(results)
        assert result.success is True
        assert "Simple" in result.message
        assert "Rendered" in result.value
